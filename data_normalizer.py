# data_normalizer.py — Goldkey AI Masters 2026
"""
[내보험다보여 데이터 파서 & 트리니티 정규화 엔진]
한국신용정보원 '내보험다보여' API/스크래핑 결과를 트리니티 엔진 표준 형식으로 변환.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
exports:
  MAPPING_MAP               — 마스터 키워드 매핑 사전
  CONSENT_VERSION           — 내보험다보여 안내문 버전 (동의 이력 기록용)
  normalize_coverage_name() — 특약명 → 표준 카테고리
  normalize_amount()        — 다양한 금액 표기 → 원(int) 단위 통일
  transform_to_trinity_format() — 외부 데이터 리스트 → current_coverage dict
  log_unmapped_item()       — 매핑 실패 항목 로그 기록 (사전 업데이트용)

보안 규칙 (GP-SEC §1):
  - 연락처/주민번호 등 PII는 이 모듈에서 처리하지 않음
  - 인증 정보(ID/PW/세션) 메모리 즉시 파기 — del 명령어 사용
  - 변환 결과를 DB 저장 시 반드시 trinity_engine.save_analysis_to_db() 경유
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
from __future__ import annotations

import re
import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ══════════════════════════════════════════════════════════════════════════════
# [0] 버전 관리 — 동의 이력 테이블(user_consent_log)에 함께 기록
# ══════════════════════════════════════════════════════════════════════════════
CONSENT_VERSION = "2026-03-16-v1"   # 안내문 개정 시 이 값을 변경
POLICY_VERSION  = "2026-03-16-v1"   # 개인정보 처리방침 버전

# ══════════════════════════════════════════════════════════════════════════════
# [1] 마스터 키워드 매핑 사전 — 수천 개 특약명 → 표준 카테고리
# ══════════════════════════════════════════════════════════════════════════════
MAPPING_MAP: dict[str, list[str]] = {
    # ── 암 관련 ───────────────────────────────────────────────────────────────
    "암진단비": [
        "암진단", "일반암", "특정암", "암확정", "암보장", "암진단금",
        "암급여금", "암발생", "소액암", "갑상선암", "유방암", "전립선암",
        "대장암", "폐암", "위암", "간암", "췌장암", "혈액암", "뇌종양",
        "양성종양", "신생물", "악성",
    ],
    # ── 뇌혈관 관련 (trinity_engine 표준: "뇌졸중진단비") ────────────────────
    "뇌졸중진단비": [
        "뇌혈관", "뇌졸중", "뇌출혈", "뇌경색", "뇌혈전", "뇌색전",
        "뇌혈관질환", "뇌졸중진단", "뇌혈관질환진단", "뇌졸증",
        "중풍", "뇌동맥류", "뇌막염",
    ],
    # ── 심장·허혈성 관련 (trinity_engine 표준: "심근경색진단비") ────────────────
    "심근경색진단비": [
        "허혈성", "심근경색", "심장질환", "급성심근", "심장마비",
        "협심증", "심부전", "심혈관", "심장수술", "관상동맥", "심장발작",
        "심정지", "허혈심장",
    ],
    # ── 상해 후유장해 ─────────────────────────────────────────────────────────
    "상해후유장해": [
        "상해후유", "상해장해", "상해외상", "후유장해", "영구장해",
        "부분장해", "장해급여", "신체장해", "후유증", "상해장애",
        "상해지급", "골절장해",
    ],
    # ── 실손의료비 ────────────────────────────────────────────────────────────
    "실손의료비": [
        "실손", "실비", "의료비", "통원의료비", "입원의료비",
        "의료실비", "실손보장", "실비보장", "의료비실손", "급여의료비",
        "비급여의료비",
    ],
    # ── 수술비 ───────────────────────────────────────────────────────────────
    "수술비": [
        "수술비", "수술급여", "질병수술", "상해수술", "종수술",
        "외래수술", "수술보장", "수술치료", "수술급부",
    ],
    # ── 입원일당 ──────────────────────────────────────────────────────────────
    "입원일당": [
        "입원일당", "입원급여", "입원보장", "입원일비", "일당",
        "입원치료비", "병원일당", "입원비", "재원일당",
    ],
    # ── 사망 ─────────────────────────────────────────────────────────────────
    "사망보험금": [
        "사망", "사망보험금", "사망급여", "일반사망", "재해사망",
        "상해사망", "질병사망", "사망시", "순수사망",
    ],
    # ── 치매 ─────────────────────────────────────────────────────────────────
    "치매진단비": [
        "치매", "치매진단", "치매보장", "중증치매", "경증치매",
        "알츠하이머", "인지장애",
    ],
}

# 역매핑 캐시 (초기화 시 자동 생성)
_REVERSE_MAP: dict[str, str] = {}
for _std, _kws in MAPPING_MAP.items():
    for _kw in _kws:
        _REVERSE_MAP[_kw] = _std

# ══════════════════════════════════════════════════════════════════════════════
# [2] 미매핑 항목 로그 — 사전 업데이트 피드백 루프
# ══════════════════════════════════════════════════════════════════════════════
_LOG_DIR = Path(os.environ.get("NORMALIZER_LOG_DIR", "."))
_UNMAPPED_LOG = _LOG_DIR / "unmapped_coverage.log"

_logger = logging.getLogger("data_normalizer")
if not _logger.handlers:
    _logger.setLevel(logging.INFO)
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    _logger.addHandler(_handler)


def log_unmapped_item(raw_name: str, source: str = "") -> None:
    """
    매핑 실패 특약명을 파일 로그에 기록.
    정기적으로 검토하여 MAPPING_MAP 사전을 업데이트하는 데 사용.
    """
    _entry = {
        "ts":     datetime.now(timezone.utc).isoformat(),
        "raw":    raw_name,
        "source": source or "unknown",
    }
    _logger.warning(f"[UNMAPPED] {raw_name!r} (source={source})")
    try:
        with open(_UNMAPPED_LOG, "a", encoding="utf-8") as _f:
            _f.write(json.dumps(_entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# [3] 명칭 정규화 — 지저분한 특약명 → 표준 카테고리
# ══════════════════════════════════════════════════════════════════════════════
def normalize_coverage_name(
    raw_name: str,
    source: str = "",
    log_unmapped: bool = True,
) -> str:
    """
    외부 특약명을 표준 카테고리로 매핑.
    예: "(무)뉴-하이콜 암진단비(갱신형)" → "암진단비"
        "급성심근경색진단특약" → "허혈성심장진단비"

    Args:
        raw_name:     원본 특약/담보명
        source:       데이터 출처 (로그용)
        log_unmapped: True이면 매핑 실패 시 로그 기록

    Returns:
        표준 카테고리 키 또는 "기타담보"
    """
    if not raw_name:
        return "기타담보"

    # 특수문자·괄호 제거 후 검사
    _clean = re.sub(r"[\(\)\[\]{}\-_\.]", " ", str(raw_name))

    # 1차: 직접 키워드 매핑
    for _std, _kws in MAPPING_MAP.items():
        if any(_kw in _clean for _kw in _kws):
            return _std

    # 2차: 역매핑 캐시 (부분 문자열)
    for _kw, _std in _REVERSE_MAP.items():
        if _kw in raw_name:
            return _std

    # 매핑 실패 → 로그
    if log_unmapped:
        log_unmapped_item(raw_name, source)
    return "기타담보"


# ══════════════════════════════════════════════════════════════════════════════
# [4] 금액 정규화 — 다양한 표기 → 원(int) 단위
# ══════════════════════════════════════════════════════════════════════════════
_RE_FLOAT  = re.compile(r"[\d,]+\.?\d*")
_RE_DIGITS = re.compile(r"[^0-9]")


def normalize_amount(amount_str, source_unit: str = "auto") -> int:
    """
    다양한 금액 표기를 원(int) 단위로 통일.

    처리 가능 형식:
      - "1,000만원"  → 10_000_000
      - "1.5억"      → 150_000_000
      - "10,000,000" → 10_000_000
      - "1천만원"    → 10_000_000
      - 3000         → 3_000 (int 그대로, 단위 판별 후 보정)
      - "3000만"     → 30_000_000

    Args:
        amount_str:  원본 금액 문자열 또는 숫자
        source_unit: "auto"(자동 감지) | "원" | "만원" | "억"
    """
    if isinstance(amount_str, (int, float)):
        val = int(amount_str)
        if source_unit == "만원":
            return val * 10_000
        if source_unit == "억":
            return val * 100_000_000
        # auto: 100만 미만이면 만원 단위로 가정
        if source_unit == "auto" and 0 < val < 100_000:
            return val * 10_000
        return val

    s = str(amount_str).strip()
    if not s:
        return 0

    # 억 단위 처리 (예: "1.5억", "2억")
    _eok = re.search(r"([\d,]+\.?\d*)\s*억", s)
    if _eok:
        _num = float(_eok.group(1).replace(",", ""))
        return int(_num * 100_000_000)

    # 천만 단위 (예: "1천만원")
    _cheon_man = re.search(r"([\d]+)\s*천\s*만", s)
    if _cheon_man:
        return int(_cheon_man.group(1)) * 10_000_000

    # 천 단위 (예: "1천원")
    _cheon = re.search(r"([\d]+)\s*천(?!\s*만)", s)
    if _cheon:
        return int(_cheon.group(1)) * 1_000

    # 만원 단위 (예: "3,000만원", "500만")
    _man = re.search(r"([\d,]+)\s*만", s)
    if _man:
        _num = int(_man.group(1).replace(",", ""))
        return _num * 10_000

    # 순수 숫자 (쉼표 제거)
    _digits = _RE_DIGITS.sub("", s)
    if not _digits:
        return 0
    val = int(_digits)

    # auto 단위 감지: 100_000 미만이면 만원 단위로 추정
    if source_unit == "auto" and 0 < val < 100_000:
        return val * 10_000

    return val


# ══════════════════════════════════════════════════════════════════════════════
# [5] 통합 변환 파이프라인 — 외부 API JSON → current_coverage dict
# ══════════════════════════════════════════════════════════════════════════════
def transform_to_trinity_format(
    external_api_data: list,
    duplicate_policy: str = "sum",
    source: str = "내보험다보여",
) -> tuple[dict, list]:
    """
    외부 API 데이터(List[Dict]) → 트리니티 엔진 current_coverage Dict.

    Args:
        external_api_data: 내보험다보여 API 응답 리스트.
            각 항목은 다음 중 하나 이상의 키를 가져야 함:
            prodName / traitName / coverageName → 담보명
            amt / amount / coverageAmt          → 가입금액
            status / contStatus                 → 계약 상태 (유효 필터)

        duplicate_policy: 동일 카테고리 중복 처리 정책
            "sum"  — 합산 (기본, 다중 보험 합산 가입)
            "max"  — 최댓값만 취함 (중복 집계 오류 방지 모드)

        source: 데이터 출처 (로그용)

    Returns:
        (current_coverage dict, unmapped_items list)
        current_coverage: {"암진단비": 50_000_000, ...}
        unmapped_items:   매핑 실패 원본 항목 리스트 (감사·업데이트용)
    """
    # 모든 표준 카테고리 0으로 초기화
    standard_coverage: dict[str, int] = {k: 0 for k in MAPPING_MAP}

    unmapped: list[dict] = []

    for _item in (external_api_data or []):
        # ── 계약 상태 필터 (실효·해지 제외) ─────────────────────────────────
        _status = str(
            _item.get("status") or _item.get("contStatus") or "유효"
        ).strip()
        if _status in {"실효", "해지", "만기", "소멸", "expired", "terminated"}:
            continue

        # ── 담보명 추출 ────────────────────────────────────────────────────
        _raw_name = (
            _item.get("coverageName") or
            _item.get("traitName")    or
            _item.get("prodName")     or
            _item.get("name")         or ""
        ).strip()

        # ── 금액 추출 ─────────────────────────────────────────────────────
        _raw_amt = (
            _item.get("coverageAmt") or
            _item.get("amt")         or
            _item.get("amount")      or
            _item.get("insureAmt")   or 0
        )

        _std_key = normalize_coverage_name(_raw_name, source=source)
        _amount  = normalize_amount(_raw_amt)

        if _std_key == "기타담보":
            unmapped.append({"raw": _raw_name, "amt": _amount, "item": _item})
            continue

        if _std_key in standard_coverage:
            if duplicate_policy == "max":
                standard_coverage[_std_key] = max(
                    standard_coverage[_std_key], _amount
                )
            else:
                # "sum" — 합산 (다중 보험 중복 가입 총합)
                standard_coverage[_std_key] += _amount

    return standard_coverage, unmapped


# ══════════════════════════════════════════════════════════════════════════════
# [6] 인증 정보 제로 트러스트 파기 헬퍼 — GP-SEC §1
# ══════════════════════════════════════════════════════════════════════════════
def purge_auth_credentials(credential_dict: dict) -> None:
    """
    [GP-SEC §1 / Zero Trust] 내보험다보여 인증 정보를 메모리에서 즉시 파기.
    단순 None 할당이 아닌 del + 덮어쓰기로 GC 이전 메모리 노출 최소화.

    Usage:
        _auth = {"id": user_id, "pw": user_pw, "session": token}
        # ... 데이터 추출 완료 후 ...
        purge_auth_credentials(_auth)
    """
    if not isinstance(credential_dict, dict):
        return
    for _k in list(credential_dict.keys()):
        try:
            credential_dict[_k] = ""  # 덮어쓰기
            del credential_dict[_k]   # 즉시 삭제
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
# [7] 동의 이력 DB 저장 헬퍼 — user_consent_log 테이블
# ══════════════════════════════════════════════════════════════════════════════
def save_nibo_consent_log(
    agent_id: str,
    person_id: str,
    consented: bool,
    consent_version: str = CONSENT_VERSION,
    policy_version: str  = POLICY_VERSION,
) -> bool:
    """
    내보험다보여 연동 동의 이력을 Supabase user_consent_log 테이블에 저장.
    동의 시점의 약관 버전도 함께 기록 (개정 대응).

    테이블 스키마 (Supabase SQL Editor에서 생성):
        CREATE TABLE IF NOT EXISTS user_consent_log (
            id             UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            agent_id       TEXT NOT NULL,
            person_id      TEXT DEFAULT '',
            consent_type   TEXT NOT NULL,        -- 'nibo' | 'privacy' | 'terms'
            consented      BOOLEAN NOT NULL,
            consent_version TEXT,                -- 약관 버전
            policy_version  TEXT,                -- 개인정보처리방침 버전
            consented_at   TIMESTAMPTZ DEFAULT NOW(),
            ip_hash        TEXT DEFAULT ''       -- IP SHA-256 (GP-SEC §1)
        );
    """
    try:
        from trinity_engine import get_trinity_db
        _db = get_trinity_db()
        if not _db:
            return False
        _db.table("user_consent_log").insert({
            "agent_id":       agent_id,
            "person_id":      person_id or "",
            "consent_type":   "nibo",
            "consented":      consented,
            "consent_version": consent_version,
            "policy_version":  policy_version,
            "consented_at":   datetime.now(timezone.utc).isoformat(),
        }).execute()
        return True
    except Exception as _e:
        _logger.error(f"consent_log 저장 실패: {_e}")
        return False
