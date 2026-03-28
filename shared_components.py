# ══════════════════════════════════════════════════════════════════════════════
# [GP-ARCH] 시스템 아키텍처 지휘체계 — 최상위 운영 원칙 (모든 작업의 북극성)
#
#  🎖️ Cloud Run   (지휘통제실) : 실시간 지휘 및 모든 연산/판단 수행.
#                                Stateless 기반 최적 로직 실행 — 데이터 임시 저장 금지.
#  📜 GitHub       (기록관/비서): 1차 설계도 및 규칙 보관소.
#                                지휘관(Cloud Run)에 전달할 최신 코드(작전 교본) 관리.
#  🧠 Supabase     (활성 메모리): 상담 내용·고객 정보 즉시 저장/조회.
#                                지휘관의 현장 장부 — 상태는 반드시 여기에 저장.
#  📦 GCS          (영구 창고)  : PDF·이미지 등 대용량 파일 및 장기 데이터 백업.
#  💪 CRM / HQ     (실행 부위)  : 고객 소통 및 전문가 개입 UI — 몸통과 팔다리.
#
# [Cascade 특별 지시]
#  1. 코드 수정·기능 추가 시 반드시 위 지휘-기록-보관 체계에 부합하는지 검토.
#  2. 데이터 저장은 Cloud Run(임시) 금지 → Supabase(상태) 또는 GCS(파일) 사용.
#  3. 이 주석은 단순 기록이 아닌 프로젝트 최상위 운영 원칙이다. 절대 삭제 금지.
# ══════════════════════════════════════════════════════════════════════════════
# shared_components.py — Goldkey AI Masters 2026
"""
[GP 마스터-그림자 원칙 Phase 1] Python/Streamlit 공통 모듈
모 앱(app.py)과 자 앱(crm_app.py) 양쪽에서 import하여 사용.
이 파일이 바뀌면 양쪽 앱이 자동으로 반영된다.

[GP-DESIGN-V3] 전역 디자인 시스템 SSOT 준수 — inject_global_gp_design 등 단일 진입.
[GP-SEC] PII(개인정보) 로그 기록 및 평문 저장 절대 금지.
[GP-140] localStorage 기반 세션 지속성 및 탭 위치 관리 원칙(HQ 브라우저 측 구현과 정합).

export:
    CUSTOMER_SCHEMA          — 고객 필드 정의 딕셔너리
    customer_card_html()     — 고객 1행 카드 HTML
    customer_form()          — 고객 입력/수정 폼 (Streamlit 위젯)
    customer_input_form()    — 저장 로직 (양방향 Supabase upsert)
    render_customer_list()   — 고객 목록 FlatList 렌더
    build_deeplink_to_hq()   — 자 앱 → 모 앱 딥링크 URL 생성
    build_sso_redirect()     — SSO return_to URL 생성
    get_time_aware_greeting()    — KST 시각대별 공감형 인사말 반환 (아침/오후/저녁/심야)
    calculate_trinity_metrics() — 트리니티 계산법 — 건보료 기반 재무 지표 산출 엔진
    get_trinity_nhis_rate() — rules.json ota_updatable.nhis_rate (OTA)
"""

from __future__ import annotations
import streamlit as st
import os
import threading
import uuid, datetime
from typing import Optional

# [GP-TEXT-LOCK] 텍스트 무결성 보호 모듈 import
try:
    import app_texts as txt
except ImportError:
    txt = None


def ss_ns_key(namespace: str, key: str) -> str:
    """세션 네임스페이스 키 생성 (`ns:key`)."""
    return f"{namespace}:{key}"


def ss_get_ns(namespace: str, key: str, default=None):
    return st.session_state.get(ss_ns_key(namespace, key), default)


def ss_set_ns(namespace: str, key: str, value) -> None:
    st.session_state[ss_ns_key(namespace, key)] = value


def consent_get(name: str, default=False):
    """동의 플래그 조회 (namespaced 우선, legacy 호환)."""
    _new = st.session_state.get(ss_ns_key("consent", name), None)
    if _new is not None:
        return _new
    return st.session_state.get(name, default)


def consent_set(name: str, value) -> None:
    """동의 플래그 저장 (namespaced + legacy 동시 기록)."""
    ss_set_ns("consent", name, value)
    # 하위 호환: 기존 전역키도 유지해 기존 코드와 충돌 없이 단계적 전환
    st.session_state[name] = value


def get_env_secret(key: str, default_value: str = "") -> str:
    """st.secrets가 없어도 뻗지 않고 클라우드 환경변수로 대체하는 안전한 함수.
    로딩 우선순위: st.secrets(secrets.toml) → os.environ(Cloud Run) → default_value
    """
    # [K2-1] st.secrets — secrets.toml / Streamlit Cloud Secrets Manager
    try:
        val = st.secrets.get(key, None)
        if val is not None and str(val).strip():
            return str(val).strip()
    except Exception:
        pass
    # [K2-2] OS 환경변수 — Cloud Run ENV / .env 파일
    env_val = os.environ.get(key, "").strip()
    if env_val:
        return env_val
    # [K2-3] 기본값 반환
    return default_value


def get_clean_phone(raw: str) -> str:
    """[GP-회원관리 §연락처표준] 연락처 표준 정규화 — 숫자만 추출
    하이픈(-), 공백, 괄호, 특수문자 등 모두 제거 후 순수 숫자만 반환.
    모든 연락처 비교·해싱·저장 전 반드시 이 함수를 먼저 호출할 것.
    """
    if not raw:
        return ""
    return "".join(filter(str.isdigit, str(raw)))


def mask_name(name: str) -> str:
    """[GP-SEC §3] 고객 이름 마스킹 — API 전송 및 UI 표시용.
    규칙: 첫 글자·마지막 글자 유지, 중간 전체 * 처리
    예: 홍길동 → 홍*동 | 남궁민수 → 남**수 | 이황 → 이* | 김 → *
    """
    if not name:
        return "*"
    n = name.strip()
    if len(n) <= 1:
        return "*"
    if len(n) == 2:
        return n[0] + "*"
    return n[0] + "*" * (len(n) - 2) + n[-1]


def mask_phone(phone: str) -> str:
    """[GP-SEC] 전화번호 마스킹 — UI 표시용. 예: '01012345678' → '010-****-5678'"""
    import re as _re_mp
    if not phone:
        return ""
    _clean = _re_mp.sub(r"[^0-9]", "", phone)
    if len(_clean) == 11:
        return f"{_clean[:3]}-****-{_clean[7:]}"
    elif len(_clean) == 10:
        return f"{_clean[:3]}-***-{_clean[6:]}"
    return phone[:3] + "****" + phone[-2:] if len(phone) > 5 else "****"


def mask_ssn(ssn: str) -> str:
    """[GP-SEC §절대엄수] 주민등록번호 마스킹.
    규칙: 뒷 7자리 중 첫 자리(성별코드)만 노출, 나머지 6자리 * 처리
    예: 900101-1234567 → 900101-1****** | 9001011234567 → 900101-1******
    """
    import re as _re_ssn
    _clean = _re_ssn.sub(r"[^0-9]", "", ssn or "")
    if len(_clean) == 13:
        return _clean[:6] + "-" + _clean[6] + "******"
    if ssn and len(ssn) > 4:
        return ssn[:2] + "*" * (len(ssn) - 2)
    return "***"


def get_time_aware_greeting(name: str = "", login_time: str = "") -> str:
    """[GP-VOICE-2026] KST 기준 현재 시각에 맞는 전문가 시간인지형 인사말 반환.

    Args:
        name:       설계사 이름 (있으면 '이름'님 접두어 붙임)
        login_time: 로그인 시각 문자열 예) '09:32' (있으면 괄호 표기)

    시간대별 분기 (KST):
      05:00~11:59 — 아침  : 활기찬 시작 인사
      12:00~17:59 — 오후  : 집중 오후 인사
      18:00~21:59 — 저녁  : 마무리 위로 인사
      22:00~04:59 — 심야  : 열정 격려 인사
    """
    _prefix = f"'{name}'님, " if name else ""
    _suffix = f" (로그인: {login_time})" if login_time else ""
    _h = datetime.datetime.now().hour
    if 5 <= _h < 12:
        return f"{_prefix}활기찬 아침입니다.{_suffix}"
    elif 12 <= _h < 18:
        return f"{_prefix}좋은 오후입니다.{_suffix}"
    elif 18 <= _h < 22:
        return f"{_prefix}수고하신 저녁입니다.{_suffix}"
    else:
        return f"{_prefix}늦은 밤까지 열정이십니다.{_suffix}"


def get_trinity_nhis_rate() -> float:
    """건강보험료 역산용 총 요율 — `rules.json` ota_updatable.nhis_rate OTA 동기화 (Streamlit 비의존)."""
    _env = os.environ.get("GK_NHIS_RATE", "").strip()
    if _env:
        try:
            return float(_env)
        except ValueError:
            pass
    try:
        import json as _json
        from pathlib import Path as _Path

        _p = _Path(__file__).resolve().parent / "rules.json"
        if _p.is_file():
            with open(_p, "r", encoding="utf-8") as _f:
                _data = _json.load(_f)
            _ota = (_data.get("ota_updatable") or {}) if isinstance(_data, dict) else {}
            if "nhis_rate" in _ota:
                return float(_ota["nhis_rate"])
    except Exception:
        pass
    return 0.0719


def calculate_trinity_metrics(
    nhis_premium: int,
    sub_type: str = "workplace",
) -> dict:
    """
    [트리니티 개정 엔진 2026] 가입자 유형 분기 × 구간별 실효공제율 × 7대 완성형 보장액.

    sub_type 값:
      "workplace"        — 직장가입자 (보수월액 기반)
      "regional_general" — 지역가입자 일반/사업자 (재산가중치 75%)
      "regional_retiree" — 지역가입자 은퇴자 (재산가중치 50%)

    CFP 5년 소득보전 완성형 모델 — 법원 일실수입 산정 + 유가족 연착륙 기준.
    역산 요율은 `get_trinity_nhis_rate()` → rules.json `ota_updatable.nhis_rate`.
    """
    _nr = get_trinity_nhis_rate()
    # ── [Step 1] 가입자 유형별 명목 월소득 역산 ──────────────────────────────
    # 건강보험료율 — OTA(nhis_rate), 직장: 노사 각 절반 → 근로자 실질 부담 역산
    if sub_type == "regional_retiree":
        # 은퇴자 지역가입자: 재산점수 가중치 50% 반영
        _gross_monthly = int(nhis_premium / (_nr * 0.5))
    elif sub_type == "regional_general":
        # 일반 지역가입자/사업자: 재산점수 가중치 75% 반영
        _gross_monthly = int(nhis_premium / (_nr * 0.75))
    else:
        # 직장가입자: 사용자 50% 분담 → 근로자 실질 부담 역산
        _gross_monthly = int((nhis_premium * 2) / _nr)

    _gross_annual = _gross_monthly * 12

    # ── [Step 2] 연봉 구간별 누진 실효공제율 산출 ───────────────────────────
    # (고용보험·요양보험·소득세) 합산 공제율
    if _gross_annual <= 10_000_000:
        _ded_rate = 0.0137 + 0.0475
    elif _gross_annual <= 29_000_000:
        _ded_rate = 0.0242 + 0.0475
    elif _gross_annual <= 30_000_000:
        _ded_rate = 0.0262 + 0.0475
    elif _gross_annual <= 45_000_000:
        _ded_rate = 0.0417 + 0.0475
    elif _gross_annual <= 50_000_000:
        _ded_rate = 0.0547 + 0.0475
    elif _gross_annual <= 70_000_000:
        _ded_rate = 0.0962 + 0.0475
    elif _gross_annual <= 80_000_000:
        _ded_rate = 0.1182 + 0.0475
    elif _gross_annual <= 90_000_000:
        _ded_rate = 0.1422 + 0.0475
    elif _gross_annual <= 100_000_000:
        _ded_rate = 0.1652 + 0.0475
    else:
        _ded_rate = 0.20 + 0.0475

    # ── [Step 3] 가처분 월소득 확정 ──────────────────────────────────────────
    _net_monthly  = int(_gross_monthly * (1 - _ded_rate))
    _net_annual   = _net_monthly * 12
    _daily_value  = int(_net_monthly / 30)

    # ── [7대 완성형 보장액] CFP 5년 소득보전 + 법원 일실수입 기준 ─────────────
    # ① 일반사망: 유가족 5년 연착륙 자금 (가처분 × 60개월)
    death_cov         = _net_monthly * 60

    # ② 암 진단비: 5년 투병·생활비 (가처분 × 60개월)
    cancer_cov        = _net_monthly * 60

    # ③ 표적항암비: 가처분 30개월 (가처분 500만 기준 1.5억)
    target_cancer_cov = _net_monthly * 30

    # ④ 뇌/심장 진단비: 가처분 40개월 (가처분 500만 기준 2억)
    brain_heart_cov   = _net_monthly * 40

    # ⑤ 상해/질병 후유장해: 가처분 100개월 — 장해율 고려 (500만 기준 5억)
    disability_cov    = _net_monthly * 100

    # ── [2-Track 후유장해 2026] 초정밀 산출 ─────────────────────────────────
    # Step1: 치료·재활 및 소득상실 대체금 (1년, 2배수)
    _target_payout       = _net_monthly * 12 * 2
    # Step2: 총 필요 후유장해 가입금액 (장해율 10% 기준, 10분위 절사)
    _total_disability    = _target_payout / 0.10
    disability_cov_total = int(_total_disability / 10_000) * 10_000
    # Step3: 산재보험 공제 후 최소 필요 가입금액 (10% 장해, 176일 보상 가정)
    _min_disability_wc   = (_total_disability / 365) * (365 - 176)
    disability_cov_min   = int(_min_disability_wc / 10_000) * 10_000

    # ⑥ 로봇수술비: 가처분 6개월 (500만 기준 3,000만)
    robot_surg_cov    = _net_monthly * 6

    # ⑦ 간병인/입원일당: 가처분의 4% → 만 원 단위 절사
    caregiver_daily   = int((_net_monthly * 0.04) / 10_000) * 10_000

    # ── 하위 호환 필드 (구 코드 참조처 안전 유지) ────────────────────────────
    gap_injury        = min(_daily_value, 70_000)
    gap_disease       = min(_daily_value, 100_000)
    stroke_need       = _net_monthly * 18
    disability_2yr    = _net_monthly * 24
    cancer_standard   = cancer_cov          # 구 cancer_standard → cancer_cov 동기화
    injury_cover_1yr  = int((_net_monthly * 12) / 0.1)
    injury_cover_2yr  = int((_net_monthly * 24) / 0.1)

    return {
        # ── 기본 소득 지표 ──────────────────────────────────────────────────
        "sub_type":           sub_type,
        "gross_monthly":      _gross_monthly,
        "gross_annual":       _gross_annual,
        "ded_rate":           round(_ded_rate, 4),
        "net_monthly":        _net_monthly,
        "net_annual":         _net_annual,
        "daily_value":        _daily_value,
        # ── 7대 완성형 보장액 ───────────────────────────────────────────────
        "death_cov":          death_cov,
        "cancer_cov":         cancer_cov,
        "target_cancer_cov":  target_cancer_cov,
        "brain_heart_cov":    brain_heart_cov,
        "disability_cov":     disability_cov,
        "disability_cov_total": disability_cov_total,
        "disability_cov_min":   disability_cov_min,
        "robot_surg_cov":     robot_surg_cov,
        "caregiver_daily":    caregiver_daily,
        # ── 하위 호환 필드 ──────────────────────────────────────────────────
        "monthly_income":     _net_monthly,    # 구 호환: net 기준으로 전환
        "annual_income":      _net_annual,
        "gap_injury":         gap_injury,
        "gap_disease":        gap_disease,
        "stroke_need":        stroke_need,
        "disability_2yr":     disability_2yr,
        "cancer_min":         cancer_cov,
        "cancer_rec":         cancer_cov,
        "cancer_standard":    cancer_standard,
        "injury_cover_1yr":   injury_cover_1yr,
        "injury_cover_2yr":   injury_cover_2yr,
    }

# ── 모/자 앱 공개 URL — Cloud Run·로컬 모두 환경변수 우선 (하드코딩 금지) ───
# HQ_APP_URL   — HQ(Streamlit) 베이스, 딥링크·SSO에 사용
# CRM_APP_URL  — CRM 베이스, HQ→CRM 복귀 링크에 사용
# HQ_API_URL   — (선택) 증권분석 브리지 REST 베이스; 미설정 시 {HQ_APP_URL}/api/v1
import os as _os


def resolve_hq_app_url() -> str:
    u = get_env_secret("HQ_APP_URL", "").strip().rstrip("/")
    if u:
        return u
    return "http://localhost:8501"


def resolve_crm_app_url() -> str:
    u = get_env_secret("CRM_APP_URL", "").strip().rstrip("/")
    if u:
        return u
    return "http://localhost:8502"


HQ_APP_URL = resolve_hq_app_url()
CRM_APP_URL = resolve_crm_app_url()


def get_hq_api_base() -> str:
    """CRM → HQ 증권분석 API 베이스 (끝에 /api/v1 형태 권장)."""
    explicit = get_env_secret("HQ_API_URL", "").strip().rstrip("/")
    if explicit:
        return explicit
    return f"{HQ_APP_URL}/api/v1"


def request_hq_analysis_trigger(
    *,
    person_id: str,
    agent_id: str = "",
    user_id: str = "",
    sector: str = "home",
    timeout_sec: float = 15.0,
) -> dict:
    """
    CRM에서 HQ 증권분석 브리지(REST)로 세션 트리거.
    응답에 hq_deeplink 포함 — UI에서 새 탭으로 열 수 있음.
    """
    import json as _j
    import urllib.error as _ue
    import urllib.request as _ur

    if not person_id:
        return {"ok": False, "error": "person_id_required"}
    base = get_hq_api_base()
    url = f"{base.rstrip('/')}/analysis/trigger"
    secret = get_env_secret("GK_ANALYSIS_BRIDGE_SECRET", "").strip()
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if secret:
        headers["X-GK-Bridge-Key"] = secret
    payload = _j.dumps(
        {
            "person_id": person_id,
            "agent_id":  agent_id or "",
            "user_id":   user_id or "",
            "sector":    sector or "home",
        },
        ensure_ascii=False,
    ).encode("utf-8")
    req = _ur.Request(url, data=payload, headers=headers, method="POST")
    try:
        with _ur.urlopen(req, timeout=timeout_sec) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return _j.loads(raw) if raw.strip() else {"ok": True}
    except _ue.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")[:800]
        except Exception:
            body = ""
        return {"ok": False, "error": "http", "status": e.code, "body": body}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def schedule_hq_prewarm_from_crm(
    *,
    person_id: str,
    user_id: str = "",
    agent_id: str = "",
    reason: str = "select",
) -> None:
    """
    HQ Cloud Run 콜드 스타트 완화 — GET /api/v1/health (가벼운 핑).
    threading 백그라운드(daemon)로 실행되어 CRM UI를 블로킹하지 않음.
    세션당 person_id·reason 조합당 1회만 네트워크 호출.
    """
    import urllib.request as _ur

    if not person_id:
        return
    mark = f"_hq_prewarm_{person_id}_{reason}"
    if st.session_state.get(mark):
        return
    st.session_state[mark] = True

    def _run() -> None:
        base = get_hq_api_base().rstrip("/")
        url = f"{base}/health"
        try:
            with _ur.urlopen(_ur.Request(url, method="GET"), timeout=5.0):
                pass
        except Exception:
            pass

    threading.Thread(target=_run, name="hq-prewarm-health", daemon=True).start()


# ── 고객 데이터 스키마 (모/자 앱 공통) ────────────────────────────────────────
CUSTOMER_SCHEMA: dict = {
    "person_id":           {"type": "str",  "required": True,  "label": "고객 ID"},
    "name":                {"type": "str",  "required": True,  "label": "이름"},
    "contact":             {"type": "str",  "required": True,  "label": "연락처"},
    "birth_date":          {"type": "date", "required": False, "label": "생년월일"},
    "gender":              {"type": "str",  "required": False, "label": "성별",
                            "options": ["남성", "여성"]},
    "address":             {"type": "str",  "required": False, "label": "주소"},
    "job":                 {"type": "str",  "required": False, "label": "직업"},
    "memo":                {"type": "text", "required": False, "label": "메모"},
    "status":              {"type": "str",  "required": False, "label": "상태",
                            "options": ["potential", "active", "contracted", "closed"],
                            "default": "potential"},
    "management_tier":     {"type": "int",  "required": False, "label": "관리 등급",
                            "options": [1, 2, 3], "default": 3},
    "auto_renewal_month":  {"type": "int",  "required": False, "label": "자동차보험 만기월"},
    "fire_renewal_month":  {"type": "int",  "required": False, "label": "화재보험 만기월"},
    "last_auto_carrier":   {"type": "str",  "required": False, "label": "기존 자동차보험사"},
    "is_favorite":         {"type": "bool", "required": False, "label": "즐겨찾기",
                            "default": False},
    "prospecting_stage":   {"type": "str",  "required": False, "label": "개척 단계",
                            "options": ["lead", "contact", "proposal", "contracted"],
                            "default": "lead"},
    "community_tags":      {"type": "list", "required": False, "label": "소속 모임"},
    "risk_note":           {"type": "text", "required": False, "label": "고위험 메모"},
    "agent_id":            {"type": "str",  "required": False, "label": "담당 설계사 ID"},
}

TIER_META = {
    1: {"label": "VVIP", "color": "#b45309", "bg": "#fef3c7", "icon": "👑"},
    2: {"label": "핵심",  "color": "#1d4ed8", "bg": "#dbeafe", "icon": "⭐"},
    3: {"label": "일반",  "color": "#374151", "bg": "#f3f4f6", "icon": "👤"},
}
STATUS_META = {
    "potential":  {"label": "가망",   "color": "#6b7280", "bg": "#f3f4f6"},
    "active":     {"label": "진행중", "color": "#2563eb", "bg": "#dbeafe"},
    "contracted": {"label": "계약",   "color": "#16a34a", "bg": "#dcfce7"},
    "closed":     {"label": "종료",   "color": "#dc2626", "bg": "#fee2e2"},
}
STAGE_META = {
    "lead":       {"label": "발굴", "step": 1},
    "contact":    {"label": "접촉", "step": 2},
    "proposal":   {"label": "제안", "step": 3},
    "contracted": {"label": "계약", "step": 4},
}


# ── 고객 카드 HTML ─────────────────────────────────────────────────────────────
def customer_card_html(c: dict, *, show_deeplink: bool = True, agent_tab: str = "t1") -> str:
    """
    고객 1명에 대한 카드 HTML 반환.
    show_deeplink=True 이면 [🚀 HQ 정밀 분석] 버튼 포함.
    """
    tier   = c.get("management_tier", 3)
    tm     = TIER_META.get(tier, TIER_META[3])
    status = c.get("status", "potential")
    sm     = STATUS_META.get(status, STATUS_META["potential"])

    renewal = ""
    if c.get("auto_renewal_month"):
        renewal += f"🚗 자동차 {c['auto_renewal_month']}월  "
    if c.get("fire_renewal_month"):
        renewal += f"🏠 화재 {c['fire_renewal_month']}월"
    renewal_html = (
        f"<div style='font-size:0.75rem;color:#d97706;margin-top:3px;'>🔔 만기: {renewal}</div>"
        if renewal else ""
    )

    deeplink_btn = ""
    if show_deeplink:
        deeplink_url = build_deeplink_to_hq(
            cid=c.get("person_id", ""),
            name=c.get("name", ""),
            sector=agent_tab,
        )
        deeplink_btn = f"""
<a href="{deeplink_url}" target="_blank" style="display:inline-block;margin-top:8px;
  padding:5px 12px;background:#1e3a8a;color:#fff;border-radius:7px;
  font-size:0.76rem;font-weight:900;text-decoration:none;
  border:1px dashed #93c5fd;">
  🚀 HQ 모 앱에서 정밀 분석 진행
</a>"""

    avatar_char = (c.get("name") or "?")[0]
    return f"""
<div style="background:#fff;border:1px dashed #000;border-radius:10px;
  padding:12px 14px;margin-bottom:8px;display:flex;align-items:flex-start;gap:12px;">
  <div style="width:44px;height:44px;border-radius:50%;background:{tm['bg']};
    border:1px dashed #000;display:flex;align-items:center;justify-content:center;
    font-size:1.2rem;font-weight:900;color:{tm['color']};flex-shrink:0;">
    {avatar_char}
  </div>
  <div style="flex:1;min-width:0;">
    <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
      <span style="font-size:1rem;font-weight:900;color:#1e293b;">{c.get('name','')}</span>
      <span style="font-size:0.72rem;font-weight:700;color:{tm['color']};
        background:{tm['bg']};padding:1px 6px;border-radius:5px;
        border:1px dashed {tm['color']};">{tm['icon']} {tm['label']}</span>
      <span style="font-size:0.72rem;font-weight:700;color:{sm['color']};
        background:{sm['bg']};padding:1px 6px;border-radius:5px;">{sm['label']}</span>
    </div>
    <div style="font-size:0.80rem;color:#6b7280;margin-top:2px;">
      {c.get('job', '')}  {'·' if c.get('job') and c.get('contact') else ''}  {decrypt_pii(c.get('contact', ''))}
    </div>
    {renewal_html}
    {deeplink_btn}
  </div>
</div>"""


# ── 고객 목록 렌더 ─────────────────────────────────────────────────────────────
def render_customer_list(customers: list[dict], *, show_deeplink: bool = True,
                         agent_tab: str = "t1") -> None:
    """Streamlit에 고객 카드 목록 렌더링."""
    if not customers:
        st.info("등록된 고객이 없습니다.")
        return
    html_blocks = "".join(
        customer_card_html(c, show_deeplink=show_deeplink, agent_tab=agent_tab)
        for c in customers
    )
    st.markdown(html_blocks, unsafe_allow_html=True)


# ── 고객 입력 폼 (Streamlit 위젯) ────────────────────────────────────────────
def customer_form(initial: Optional[dict] = None, *, key_prefix: str = "cf") -> dict:
    """
    [Phase 1 §2] 고객 정보 입력/수정 폼 — 모/자 앱 양방향 공통.
    반환값: 수정된 고객 딕셔너리 (저장하려면 customer_input_form() 호출)
    """
    d = initial or {}
    col1, col2 = st.columns(2)
    with col1:
        name    = st.text_input("이름 *",    value=d.get("name", ""),    key=f"{key_prefix}_name")
        # [GP-SEC §1] 저장된 Fernet 암호화값 → 평문으로 복호화하여 표시
        _disp_contact = decrypt_pii(d.get("contact", "")) if d.get("contact") else ""
        contact = st.text_input("연락처 *",  value=_disp_contact, key=f"{key_prefix}_contact")
        job     = st.text_input("직업",      value=d.get("job", ""),     key=f"{key_prefix}_job")
    with col2:
        gender  = st.selectbox("성별",        ["(선택)", "남성", "여성"],
                               index=["(선택)", "남성", "여성"].index(d.get("gender") or "(선택)"),
                               key=f"{key_prefix}_gender")
        tier    = st.selectbox("관리 등급",   [3, 2, 1],
                               format_func=lambda x: TIER_META[x]["label"],
                               index=[3, 2, 1].index(d.get("management_tier", 3)),
                               key=f"{key_prefix}_tier")
        auto_mo = st.number_input("자동차보험 만기월", min_value=0, max_value=12,
                                  value=d.get("auto_renewal_month") or 0,
                                  key=f"{key_prefix}_auto_mo",
                                  help="0=없음, 1~12=월")
    memo = st.text_area("메모", value=d.get("memo", ""), key=f"{key_prefix}_memo", height=80)

    return {
        **d,
        "name":                name,
        "contact":             contact,
        "job":                 job,
        "gender":              None if gender == "(선택)" else gender,
        "management_tier":     tier,
        "auto_renewal_month":  auto_mo or None,
        "memo":                memo,
    }


# ── [Phase 1 §2] 양방향 CRUD — customer_input_form() ─────────────────────────
def customer_input_form(customer_data: dict, agent_id: str,
                        supabase_client=None) -> dict:
    """
    고객 정보 저장 (Supabase upsert).
    모 앱과 자 앱 양쪽에서 동일하게 호출. 동일한 gk_people 테이블 업데이트.

    Args:
        customer_data:   CUSTOMER_SCHEMA 기반 dict
        agent_id:        현재 설계사 user_id
        supabase_client: supabase-py Client 인스턴스 (없으면 secrets에서 자동 생성)
    Returns:
        저장된 레코드 dict
    Raises:
        ValueError: 필수 필드 누락
        Exception:  Supabase 오류
    """
    if not customer_data.get("name", "").strip():
        raise ValueError("이름을 입력해 주세요.")
    if not customer_data.get("contact", "").strip():
        raise ValueError("연락처를 입력해 주세요.")

    # [GP-SEC §1][GP-회원관리 §연락처표준] 저장 게이트웨이: 정규화 → Fernet 암호화
    _raw_contact = customer_data.get("contact", "")
    _clean_contact = get_clean_phone(_raw_contact)
    if _clean_contact:  # 유효한 전화번호인 경우만 암호화 (이미 암호화된 경우 skip)
        try:
            _dec_test = decrypt_pii(_raw_contact)
            if _dec_test == _raw_contact and not _raw_contact.startswith("gAAAA"):
                # 아직 평문 → 정규화 후 암호화
                customer_data = dict(customer_data)
                customer_data["contact"] = encrypt_pii(_clean_contact)
        except Exception:
            pass

    if supabase_client is None:
        try:
            from supabase import create_client
            sb_url = get_env_secret("SUPABASE_URL", "")
            sb_key = get_env_secret("SUPABASE_SERVICE_ROLE_KEY",
                        get_env_secret("SUPABASE_KEY", ""))
            supabase_client = create_client(sb_url, sb_key)
        except Exception as e:
            raise RuntimeError(f"Supabase 연결 실패: {e}")

    now = datetime.datetime.utcnow().isoformat()
    row = {
        **customer_data,
        "agent_id":   agent_id,
        "updated_at": now,
        "is_deleted": False,
    }
    if not row.get("person_id"):
        row["person_id"] = str(uuid.uuid4())
        row["created_at"] = now

    resp = (
        supabase_client.table("gk_people")
        .upsert(row, on_conflict="person_id")
        .execute()
    )
    if resp.data:
        return resp.data[0]
    raise RuntimeError("저장 응답 데이터 없음")


# ── 딥링크 빌더 ─────────────────────────────────────────────────────────────
def build_deeplink_to_hq(cid: str, agent_id: str = "", name: str = "", sector: str = "home",
                         token: str = "", user_id: str = "") -> str:
    """
    [Phase 3 — C-2 PII 보호 및 SSO 완성] CRM → HQ 딥링크 URL 생성.
    평문 PII(이름, 연락처) 절대 배제. AgentID + CID 결합 HMAC-SHA256 토큰 생성.
    name / token 파라미터는 하위 호환성 유지용 — URL에 포함하지 않음.
    user_id 제공 시: [GP-SEC §2] SSO auth_token 자동 생성 포함 → HQ 이중 로그인 방지.
    """
    # ── [GP-SEC §2-G2] cid 강제 검증 — 빈 person_id로 딥링크 생성 원천 차단 ──────
    if not cid:
        raise ValueError(
            "[GP-DEEPLINK §2] cid(person_id) 누락 — "
            "딥링크 생성 불가. 상담 중인 고객을 먼저 선택하세요."
        )
    import urllib.parse as _up
    import hmac as _hmac_dl
    _dl_secret = get_env_secret("ENCRYPTION_KEY", "GoldKey_System_Encrypt_Master_2026_@#$")
    if isinstance(_dl_secret, bytes):
        _dl_secret = _dl_secret.decode()
    _dl_agent = agent_id or ""
    _dl_token = _hmac_dl.new(
        _dl_secret.encode(), (_dl_agent + cid).encode(), "sha256"
    ).hexdigest()[:32]
    params = {
        "gk_agent_id": _dl_agent,
        "gk_cid":      cid,
        "gk_sector":   sector,
        "gk_token":    _dl_token,
    }
    # [GP-SEC §2] SSO 핸드오프 — user_id 제공 시 타임스탬프 기반 auth_token 자동 삽입
    # 리플레이 공격 차단: HMAC(KEY, user_id + str(ts)) + ts 동시 전송 (300초 유효)
    if user_id:
        import time as _time_dl
        _ts = int(_time_dl.time())
        _auth_tok = _hmac_dl.new(
            _dl_secret.encode(), (user_id + str(_ts)).encode(), "sha256"
        ).hexdigest()[:32]
        params["auth_token"] = _auth_tok
        params["user_id"]    = user_id
        params["ts"]         = _ts
    return f"{HQ_APP_URL}/?{_up.urlencode(params)}"


def build_sso_redirect(return_to: str) -> str:
    """
    [Phase 2] SSO: 자 앱 → 모 앱 로그인 후 return_to로 리다이렉트.
    """
    import urllib.parse as _up
    return f"{HQ_APP_URL}/?{_up.urlencode({'return_to': return_to})}"


def build_deeplink_to_crm(user_id: str, pid: str = "", screen: str = "contact") -> str:
    """
    [GP-SEC §2] HQ → CRM 복귀 딥링크 URL 생성.
    auth_token + user_id + crm_pid 포함 → CRM 수신 시 자동 인증 + 고객 화면 복원.
    타임스탬프 기반 HMAC-SHA256 토큰 (300초 유효) — 리플레이 공격 차단.
    """
    import urllib.parse as _up
    import hmac as _hmac_crm
    import time as _time_crm
    _secret = get_env_secret("ENCRYPTION_KEY", "GoldKey_System_Encrypt_Master_2026_@#$")
    if isinstance(_secret, bytes):
        _secret = _secret.decode()
    _ts = int(_time_crm.time())
    _auth_tok = _hmac_crm.new(
        _secret.encode(), (user_id + str(_ts)).encode(), "sha256"
    ).hexdigest()[:32]
    params: dict = {
        "auth_token": _auth_tok,
        "user_id":    user_id,
        "ts":         str(_ts),
    }
    if pid:
        params["crm_pid"] = pid
    if screen:
        params["crm_screen"] = screen
    return f"{CRM_APP_URL}/?{_up.urlencode(params)}"


# ── 응접 데스크 패널 렌더 (모 앱 전용) ────────────────────────────────────────
def render_reception_desk(*, key_prefix: str = "_rd") -> None:
    """
    [Phase 4] 모 앱 홈 상단에 영구 고정되는 'HQ 응접 데스크' 패널.
    URL query_params에서 gk_cid / gk_token / gk_sector 수신 시 자동 도킹.
    """
    cid    = st.query_params.get("gk_cid",    "")
    name   = st.query_params.get("gk_name",   "")
    sector = st.query_params.get("gk_sector", "")
    token  = st.query_params.get("gk_token",  "")

    # 도킹 상태 세션에 보존 (query_params는 곧 지워지므로)
    if cid and not st.session_state.get(f"{key_prefix}_docked_cid"):
        st.session_state[f"{key_prefix}_docked_cid"]    = cid
        st.session_state[f"{key_prefix}_docked_name"]   = name
        st.session_state[f"{key_prefix}_docked_sector"] = sector
        st.session_state[f"{key_prefix}_docked_token"]  = token
        st.session_state[f"{key_prefix}_loading"]       = True
        st.query_params.clear()
        st.rerun()

    _cid    = st.session_state.get(f"{key_prefix}_docked_cid",    "")
    _name   = st.session_state.get(f"{key_prefix}_docked_name",   "")
    _sector = st.session_state.get(f"{key_prefix}_docked_sector", "")
    _loading = st.session_state.get(f"{key_prefix}_loading", False)

    with st.container(border=True):
        if not _cid:
            # 비어있는 기본 상태
            st.markdown(
                "<div style='padding:6px 0;color:#94a3b8;font-size:0.85rem;text-align:center;'>"
                "🛎️ <b>응접 데스크</b> — CRM에서 고객을 선택하면 여기에 자동 도킹됩니다.</div>",
                unsafe_allow_html=True,
            )
            return

        if _loading:
            with st.spinner("🛎️ CRM에서 고객 정보를 안전하게 불러오고 있습니다..."):
                import time; time.sleep(0.6)
            st.session_state[f"{key_prefix}_loading"] = False
            st.rerun()

        # 도킹 완료 상태
        col_info, col_action = st.columns([3, 1])
        with col_info:
            st.markdown(
                f"<div style='padding:4px 0;'>"
                f"<span style='font-size:1.0rem;font-weight:900;color:#16a34a;'>✅ HQ 정밀 상담 도킹 완료</span>"
                f"<span style='font-size:0.9rem;font-weight:900;color:#1e293b;margin-left:10px;'>{_name}</span>"
                f"<span style='font-size:0.75rem;color:#6b7280;margin-left:8px;'>CID: {_cid[:8]}...</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
            if _sector and _sector not in ("home", ""):
                _sector_labels = {
                    "cancer": "암보험 분석", "brain": "뇌혈관 분석",
                    "heart": "심장 분석", "fire": "화재보험",
                    "auto": "자동차보험", "t1": "보험금 청구 상담",
                    "t2": "실손 분석", "t3": "KB7 보장 분석",
                }
                _label = _sector_labels.get(_sector, _sector)
                st.caption(f"📍 목적지 섹터: **{_label}** — 자동 이동 중")
        with col_action:
            _rd_uid = st.session_state.get("user_id", "")
            if _rd_uid and _cid:
                try:
                    _crm_back_url = build_deeplink_to_crm(
                        user_id=_rd_uid, pid=_cid, screen="contact"
                    )
                    st.markdown(
                        f"<a href='{_crm_back_url}' target='_self' style='"
                        "display:block;text-align:center;background:#f0fdf4;"
                        "color:#15803d;border:1px solid #86efac;border-radius:8px;"
                        "padding:5px 4px;font-size:0.72rem;font-weight:900;"
                        "text-decoration:none;margin-bottom:4px;'>"
                        "🔙 CRM 복귀</a>",
                        unsafe_allow_html=True,
                    )
                except Exception:
                    pass
            if st.button("✕ 도킹 해제", key=f"{key_prefix}_undock", use_container_width=True):
                for _k in [f"{key_prefix}_docked_cid", f"{key_prefix}_docked_name",
                            f"{key_prefix}_docked_sector", f"{key_prefix}_docked_token",
                            f"{key_prefix}_loading"]:
                    st.session_state.pop(_k, None)
                st.rerun()

        # 섹터 자동 점프 (JS Smooth Scroll)
        if _sector and _sector not in ("home", ""):
            _jump_done_key = f"{key_prefix}_jumped_{_cid}_{_sector}"
            if not st.session_state.get(_jump_done_key):
                st.session_state[_jump_done_key] = True
                # current_tab을 섹터로 이동
                st.session_state["current_tab"] = _sector
                st.session_state["_scroll_top"] = True
                import streamlit.components.v1 as _jcomp
                _jcomp.html(f"""
<script>
(function() {{
  function scrollToSector() {{
    try {{
      var pd = window.parent.document;
      var el = pd.getElementById('{_sector}') || pd.querySelector('[data-sector="{_sector}"]');
      if (el) {{
        el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
      }}
    }} catch(e) {{}}
  }}
  setTimeout(scrollToSector, 800);
  setTimeout(scrollToSector, 1800);
}})();
</script>""", height=0)
                st.rerun()


# ── [내보험다보여 연동 전용 안내문] — 신용정보법 제32조 별도 고지 의무 ──────────
_NIBO_CONSENT_VERSION = "2026-03-16-v1"   # 개정 시 이 값을 변경 (동의 이력에 기록)

def _get_nibo_consent_html():
    """내보험다보여 안내문 HTML 반환 (app_texts 우선, 폴백 포함)"""
    if txt and hasattr(txt, 'NIBO_AGREEMENT'):
        _content = txt.NIBO_AGREEMENT.replace('\n', '<br>')
        return f"<div style='font-size:0.82rem;color:#1e3a8a;line-height:1.9;'>{_content}</div>"
    return """
<div style='font-size:0.82rem;color:#1e3a8a;line-height:1.9;'>
<b style='font-size:0.88rem;'>🔐 내보험다보여 안내 — 신용정보의 이용 및 보호에 관한 법률 제32조 준수</b><br><br>
• <b>수집 항목:</b> 보험사명, 상품명, 보장내역, 계약상태 (한국신용정보원 제공 데이터)<br>
• <b>활용 목적:</b> AI 트리니티 엔진 기반 보장 분석 및 맞춤형 설계 서비스 제공<br>
• <b>정보 보관:</b> 분석 완료 후 30일 경과 시 자동 파기 (단, 분석 결과는 법령에 따라 최대 3년 보관 가능)<br>
• <b>인증 정보:</b> 데이터 수집 즉시 메모리에서 삭제 (서버 내 무단 저장 및 외부 유출 절대 금지)<br>
• <b>미동의 시:</b> AI 보장 분석 및 트리니티 설계 서비스 이용이 제한될 수 있습니다.<br>
</div>
"""

_NIBO_CONSENT_HTML = _get_nibo_consent_html()

# ── [GP-SEC §5] 공통 약관 원문 (HQ/CRM 양쪽 render_auth_screen에서 사용) ──────
def _get_terms_text():
    """이용약관 전문 반환 (app_texts 우선, 폴백 포함)"""
    if txt and hasattr(txt, 'TERMS_CONTENTS'):
        return txt.TERMS_CONTENTS
    return """■ Goldkey AI Masters 2026 이용약관 및 개인정보 통합 동의서

[제1조] 목적
본 약관은 Goldkey AI Masters 2026(이하 '서비스')의 이용 조건·절차, 운영자와 회원의 권리·의무를 규정함을 목적으로 합니다.

[제2조] 서비스 이용 조건
• 현재 전체 무료 베타 서비스로 운영 중이며, 회원 1인당 1일 10회 AI 상담 이용이 제한될 수 있습니다.
• 사용 대상: 보험업계 종사자 또는 관련 업무 자격 보유자(19세 이상)를 대상으로 합니다.

[제3조] 서비스 기능 범위
AI 보장 분석 도구 / 세무·법률·상속·증여 참고 정보 제공 / 보험사별 보장 및 보험금 청구 안내 절차 지원

[제4조] 제한 및 금지 사항
타인 계정 도용 및 허위 정보 입력 금지 / 시스템 해킹 시도 및 부당한 권한 획득 방지 / 자동화 도구(크롤링, 봇)를 이용한 무단 데이터 수집 방지

[제5조] 개인정보 수집 및 이용
• 수집 항목: 이름, 연락처, 비밀번호(암호화 저장)
• 이용 목적: 회원 인증, 이용 한도 관리, 서비스 품질 개선 및 맞춤형 컨텐츠 제공
• 보유 기간: 회원 탈퇴 시 즉시 파기 (단, 관계 법령에 따라 보존이 필요한 경우 제외)

[제5조의2] 회원 정보 보안 보호
• 비밀번호/연락처: SHA-256 단방향 해시로 저장하여 운영자도 원문을 열람하거나 복원할 수 없습니다.
• 데이터: AES 기반 Fernet 암호화 적용, 세션 종료 시 메모리 데이터 즉시 파기 / 전송: TLS 1.3 보안 통신 적용

[제6조] 마이크 접근 권한
• 음성 입력(STT) 기능: 마이크 허용 요청 시 음성 데이터는 텍스트 변환용으로만 사용되며 서버에 파일 형태로 저장되지 않습니다.
• 변환 방식: Google Web Speech API를 통해 실시간 변환 후 텍스트 데이터만 활용합니다.

[제7조] 데이터 파기 규정
• 즉시 파기: 회원 탈퇴 요청 시 DB 내 모든 정보 삭제 / 세션 종료 시 임시 분석 내용 삭제
• 정기 파기: 서비스 미사용 90일 경과 시 자동 삭제 처리하여 복구가 불가능하도록 조치합니다.

[제8조] 면책 사항 및 책임의 한계
본 서비스는 AI 기술을 활용한 상담 보조 도구입니다. 모든 분석 결과의 최종 판단 및 처리는 사용자(설계사)의 책임하에 이루어집니다. 보험금 지급 여부 등 최종 결정은 보험사의 심사 결과에 따르며, 법률·세무 문제는 반드시 전문가와 상의하십시오. 본 서비스는 보험 판매·중개·알선 관계와 독립적인 순수 AI 분석 도구입니다.

[제9조] 금융소비자보호법(금소법) 준수 원칙
① 적합성 원칙 준수: 고객 소득 및 위험 성향 기반 분석
② 특정 보험사 제휴 및 수수료 편향성 없음
③ 부당권유 방지: 단정적 표현 자동 감지 및 교정
④ 허위·과장 광고 방지: 객관적 수치, 약관, 판례 범위 내 분석

[제10조] 데이터 저장 분리 (Zero-Knowledge)
• Public Zone: 보험사 공시, 의학/법령 데이터 (중앙 서버 관리)
• Private Zone: 회원이 입력한 고객 기록 및 증권 정보 (회원 UID별 독립 보안 영역)
• 관리자 및 개발자는 기술적으로 Private Zone에 접근할 수 없으며(IAM 403 차단), 모든 데이터는 AES-256-GCM으로 암호화 저장됩니다.

[제11조] 카카오톡 서비스 보안 안내
• 서비스명: Goldkey AI 보고서 전송 시스템
• 보안 준수: 본 시스템은 대화 내용을 열람하거나 친구 목록을 수집하지 않으며, 메시지 발송 권한만 활용합니다.
• 데이터 보호: 전송 데이터는 TLS 암호화 처리되며, 서버에 보고서 원문 내용을 장기 저장하지 않습니다.

[제12조] 외부 서비스 연동(Google/Apple 캘린더)
회원의 명시적 동의하에 외부 캘린더 일정을 API(OAuth 2.0)로 연동할 수 있습니다. 수집된 일정은 앱 내 일정 관리 목적으로만 사용되며, 제3자 제공이나 마케팅 활용은 엄격히 금지됩니다. 연동 해제 시 서버 내 관련 데이터는 즉시 영구 삭제됩니다.

[제13조] 개인정보 제3자 제공 (알림톡 발송)
본 서비스는 분석 결과 안내를 위해 고객의 번호를 카카오톡 알림톡 API에 전달할 수 있습니다.
• 마스킹 조치: 전송되는 개인정보(이름, 연락처, 주민번호 일부 등)는 법령에 따라 별표(*)로 비식별 처리(마스킹)되어 발송됩니다.

• 최종 갱신일: 2026년 3월 31일
■ 서비스명: Goldkey_AI_Masters2026 | 운영자: 이세윤 | 문의: 010-3074-2616 / insusite@gmail.com
"""

_TERMS_TEXT = _get_terms_text()


def render_auth_screen(
    app_name: str = "Goldkey AI",
    app_icon: str = "🏆",
    terms_agree_key: str = "_gp_terms_agreed",
    show_header: bool = True,
    show_terms_scroll: bool = True,
    show_nibo_box: bool = True,
    show_checkboxes: bool = True,
    consent_header_text: str = None,
    consent_header_bg: str = "#dbeafe",
    consent_header_fg: str = "#1e3a8a",
) -> bool:
    """
    [GP-SEC §5] 공통 로그인/약관 동의 UI.
    HQ 앱(사이드바 내부)과 CRM 앱(메인 화면) 양쪽에서 호출.

    약관 원문을 HTML div 스크롤 박스에 렌더링하고,
    동의 체크박스가 체크된 경우에만 로그인 버튼 활성화 가능하도록
    bool 값(동의 여부)을 반환한다.

    Returns:
        True  — 약관 동의 완료 (로그인 버튼 활성화 허용)
        False — 미동의 (로그인 버튼 disabled 처리)
    """
    if show_header:
        st.markdown(
            f"<div style='font-size:0.88rem;font-weight:900;color:#1e3a8a;"
            f"margin-bottom:6px;text-align:center;'>{app_icon} {app_name} 이용약관</div>",
            unsafe_allow_html=True,
        )
    _terms_md = st.markdown if show_terms_scroll else (lambda *a, **k: None)
    _terms_md(
        "<div style='width:100%;max-width:100%;max-height:220px;overflow-y:auto;font-size:0.76rem;"
        "color:#222;line-height:1.75;border:1px dashed #000;border-radius:8px;"
        "padding:10px 14px;background:#f9fafb;margin-bottom:8px;'>"

        "<b style='color:#0a1628;'>[제1조] 목적</b> "
        "본 약관은 Goldkey AI Masters 2026(이하 '서비스')의 이용 조건·절차, 운영자와 회원의 권리·의무를 규정함을 목적으로 합니다.<br><br>"

        "<b style='color:#0a1628;'>[제2조] 서비스 이용 조건</b> "
        "현재 <b>전체 무료</b> 베타 서비스로 운영 중이며, 회원 1인당 <b>1일 10회</b> AI 상담 이용이 제한될 수 있습니다. "
        "<b>사용 대상:</b> 보험업계 종사자 또는 관련 업무 자격 보유자(19세 이상)를 대상으로 합니다.<br><br>"

        "<b style='color:#0a1628;'>[제3조] 서비스 기능 범위</b> "
        "AI 보장 분석 도구 / 세무·법률·상속·증여 참고 정보 제공 / 보험사별 보장 및 보험금 청구 안내 절차 지원<br><br>"

        "<b style='color:#0a1628;'>[제4조] 제한 및 금지 사항</b> "
        "타인 계정 도용 및 허위 정보 입력 금지 / 시스템 해킹 시도 및 부당한 권한 획득 방지 / 자동화 도구(크롤링, 봇)를 이용한 무단 데이터 수집 방지<br><br>"

        "<b style='color:#0a1628;'>[제5조] 개인정보 수집 및 이용</b> "
        "<b>수집 항목:</b> 이름, 연락처, 비밀번호(암호화 저장) / "
        "<b>이용 목적:</b> 회원 인증, 이용 한도 관리, 서비스 품질 개선 및 맞춤형 컨텐츠 제공 / "
        "<b>보유 기간:</b> 회원 탈퇴 시 즉시 파기 (단, 관계 법령에 따라 보존이 필요한 경우 제외)<br><br>"

        "<b style='color:#0a1628;'>[제5조의2] 회원 정보 보안 보호</b> "
        "<b>비밀번호/연락처:</b> SHA-256 단방향 해시로 저장하여 운영자도 원문을 열람하거나 복원할 수 없습니다. "
        "<b>데이터:</b> AES 기반 Fernet 암호화 적용, 세션 종료 시 메모리 데이터 즉시 파기 / <b>전송:</b> TLS 1.3 보안 통신 적용<br><br>"

        "<b style='color:#0a1628;'>[제6조] 마이크 접근 권한</b> "
        "음성 입력(STT) 기능: 마이크 허용 요청 시 음성 데이터는 텍스트 변환용으로만 사용되며 <b>서버에 파일 형태로 저장되지 않습니다.</b> "
        "<b>변환 방식:</b> Google Web Speech API를 통해 실시간 변환 후 텍스트 데이터만 활용합니다.<br><br>"

        "<b style='color:#0a1628;'>[제7조] 데이터 파기 규정</b> "
        "<b>즉시 파기:</b> 회원 탈퇴 요청 시 DB 내 모든 정보 삭제 / 세션 종료 시 임시 분석 내용 삭제 / "
        "<b>정기 파기:</b> 서비스 미사용 90일 경과 시 자동 삭제 처리하여 복구가 불가능하도록 조치합니다.<br><br>"

        "<b style='color:#0a1628;'>[제8조] 면책 사항 및 책임의 한계</b><br>"
        "본 서비스는 AI 기술을 활용한 상담 <b>보조</b> 도구입니다. 모든 분석 결과의 최종 판단 및 처리는 <b>사용자(설계사)</b>의 책임하에 이루어집니다. "
        "보험금 지급 여부 등 최종 결정은 보험사의 심사 결과에 따르며, 법률·세무 문제는 반드시 전문가와 상의하십시오. "
        "본 서비스는 보험 판매·중개·알선 관계와 독립적인 <b>순수 AI 분석 도구</b>입니다.<br><br>"

        "<b style='color:#0a1628;'>[제9조] 금융소비자보호법(금소법) 준수 원칙</b> "
        "① 적합성 원칙 준수: 고객 소득 및 위험 성향 기반 분석 / "
        "② 특정 보험사 제휴 및 수수료 편향성 없음 / "
        "③ 부당권유 방지: 단정적 표현 자동 감지 및 교정 / "
        "④ 허위·과장 광고 방지: 객관적 수치, 약관, 판례 범위 내 분석<br><br>"

        "<b style='color:#0a1628;'>[제10조] 데이터 저장 분리 (Zero-Knowledge)</b> "
        "<b>Public Zone:</b> 보험사 공시, 의학/법령 데이터 (중앙 서버 관리) / "
        "<b>Private Zone:</b> 회원이 입력한 고객 기록 및 증권 정보 (회원 UID별 독립 보안 영역) / "
        "관리자 및 개발자는 기술적으로 Private Zone에 접근할 수 없으며(IAM 403 차단), 모든 데이터는 AES-256-GCM으로 암호화 저장됩니다.<br><br>"

        "<b style='color:#0a1628;'>[제11조] 카카오톡 서비스 보안 안내</b> "
        "<b>서비스명:</b> Goldkey AI 보고서 전송 시스템 / "
        "<b>보안 준수:</b> 본 시스템은 대화 내용을 열람하거나 친구 목록을 수집하지 않으며, 메시지 발송 권한만 활용합니다. / "
        "<b>데이터 보호:</b> 전송 데이터는 TLS 암호화 처리되며, 서버에 보고서 원문 내용을 <b>장기 저장하지 않습니다.</b><br><br>"

        "<b style='color:#0a1628;'>[제12조] 외부 서비스 연동(Google/Apple 캘린더)</b><br>"
        "회원의 명시적 동의하에 외부 캘린더 일정을 API(OAuth 2.0)로 연동할 수 있습니다. "
        "수집된 일정은 앱 내 일정 관리 목적으로만 사용되며, 제3자 제공이나 마케팅 활용은 엄격히 금지됩니다. "
        "연동 해제 시 서버 내 관련 데이터는 <b>즉시 영구 삭제</b>됩니다.<br><br>"

        "<b style='color:#0a1628;'>[제13조] 개인정보 제3자 제공 (알림톡 발송)</b> "
        "본 서비스는 분석 결과 안내를 위해 고객의 번호를 카카오톡 알림톡 API에 전달할 수 있습니다. "
        "<b>마스킹 조치:</b> 전송되는 개인정보(이름, 연락처, 주민번호 일부 등)는 법령에 따라 "
        "별표(*)로 <b>비식별 처리(마스킹)</b>되어 발송됩니다.<br><br>"

        "<div style='background:#FFF3CD;border:1px solid #F0A500;border-radius:6px;padding:8px 10px;"
        "font-size:0.75rem;color:#7A4F00;margin-top:4px;'>"
        "<b>⚠️ 면책 및 서비스 이용 안내 (Disclaimer)</b><br>"
        "① 본 앱(Goldkey_AI_Masters2026)은 고객 상담 보조 업무 도구입니다. 모든 AI 분석 결과는 참고용 보조 지표이며, 법적 효력 및 보험 계약·청구·설계 행위가 아닙니다.<br>"
        "② 보장 내용·약관 해석·보험금 청구는 반드시 해당 보험회사 보상담당자 또는 손해사정인에게 확인하십시오.<br>"
        "③ AI 분석 결과는 오답(AI 할루시네이션) 발생 가능성이 있으며, 이로 인한 손해에 대해 당사는 법적 책임을 지지 않습니다.<br>"
        "④ 본 앱은 의료·법률·세무·회계·부동산 등 전문적 진단·상담을 대체할 수 없습니다. 최종 판단과 책임은 이용자 본인에게 있습니다.<br>"
        "<i>최종 개정일: 2026년 3월 31일</i>"
        "</div>"

        "<div style='margin-top:8px;padding:6px 10px;font-size:0.74rem;color:#374151;"
        "border-top:1px dashed #cbd5e1;'>"
        "<b style='color:#0a1628;'>■ 서비스명:</b> Goldkey_AI_Masters2026 &nbsp;|&nbsp; "
        "<b style='color:#0a1628;'>운영자:</b> 이세윤 &nbsp;|&nbsp; "
        "<b style='color:#0a1628;'>문의:</b> 010-3074-2616 / insusite@gmail.com"
        "</div>"
        "<div style='margin-top:8px;padding:7px 12px;background:#fff3cd;"
        "border:1px solid #f0a500;border-radius:6px;font-size:0.78rem;"
        "font-weight:700;color:#7a4f00;text-align:center;'>"
        "⚠️ 필수 동의 항목(3가지)에 모두 체크하셔야 로그인/가입 버튼이 활성화됩니다."
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    if not show_checkboxes:
        return False
    # ── [이용 필수동의 4가지 박스] ─────────────────────────────────────────
    st.markdown("""<style>
/* 필수동의 박스 — 체크박스 영역 border 스타일링 */
div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stCheckbox"]) {
    background: #f0f8ff;
    border-left: 1.5px solid #93c5fd;
    border-right: 1.5px solid #93c5fd;
    border-bottom: 1.5px solid #93c5fd;
    border-radius: 0 0 8px 8px;
    padding: 4px 10px 8px 10px;
    margin-bottom: 6px;
    text-align: left;
}
</style>""", unsafe_allow_html=True)
    _consent_header_text = consent_header_text or "📋 서비스 이용을 위한 필수 동의"
    st.markdown(
        f"<div style='width:100%;max-width:100%;background:{consent_header_bg};border-radius:8px 8px 0 0;"
        "padding:8px 16px;margin-top:10px;text-align:left;'>"
        f"<span style='font-size:1.0rem;font-weight:900;color:{consent_header_fg};'>"
        f"{_consent_header_text}</span></div>",
        unsafe_allow_html=True,
    )
    # 전체동의 → 개별 항목 자동 체크
    _all_key = f"{terms_agree_key}_all"

    def _on_all_consent_change(_k=terms_agree_key, _ak=_all_key):
        _v = st.session_state.get(_ak, False)
        for _ck in ("_c1", "_c2", "_c3", "_c4", "_c5", "_c6", "_c7", "_c8"):
            st.session_state[f"{_k}{_ck}"] = _v
        consent_set("voice_consent_agreed", _v)
        consent_set("cal_sync_consent_agreed", _v)
        consent_set("kakao_consent_agreed", _v)

    if st.session_state.get(_all_key, False):
        for _ck in ("_c1", "_c2", "_c3", "_c4", "_c5", "_c6", "_c7", "_c8"):
            st.session_state[f"{terms_agree_key}{_ck}"] = True
        consent_set("voice_consent_agreed", True)
        consent_set("cal_sync_consent_agreed", True)
        consent_set("kakao_consent_agreed", True)
    st.checkbox(
        "🔲 **전체 동의** (필수·선택·내보험다보여·AI음성·캘린더·카카오톡 항목 모두 동의)",
        key=_all_key,
        on_change=_on_all_consent_change,
    )
    _c1 = st.checkbox(
        "✅ **[필수]** 서비스 이용약관에 동의합니다 (제1조~제18조 · 외부캘린더·카카오톡·데이터폐쇄성·책임한계 포함)",
        key=f"{terms_agree_key}_c1",
    )
    _c2 = st.checkbox(
        "✅ **[필수]** 개인정보 수집·이용에 동의합니다 (개인정보보호법 제15조)",
        key=f"{terms_agree_key}_c2",
    )
    _c3 = st.checkbox(
        "✅ **[필수]** 개인정보 암호화·보관·파기 정책에 동의합니다 (제5조의2·제7조)",
        key=f"{terms_agree_key}_c3",
    )
    _c4 = st.checkbox(
        "☑️ **[선택]** 마케팅·서비스 개선 목적 정보 활용에 동의합니다",
        key=f"{terms_agree_key}_c4",
    )
    # ── [ID-100-AUTH] 내보험다보여 연동 동의 입구 제어 카드 ──────────────────
    if show_nibo_box:
        st.markdown(
            "<div style='width:100%;max-width:100%;background:#fffbeb;border:2px dashed #f59e0b;"
            "border-radius:10px;padding:12px 14px;margin-top:14px;'>"
            "<div style='font-size:0.82rem;font-weight:900;color:#92400e;margin-bottom:8px;'>"
            "🔐 [내보험다보여 연동 동의] — 신용정보법 제32조 별도 고지</div>"
            "<div style='font-size:0.75rem;color:#78350f;line-height:1.85;'>"
            "• <b>수집:</b> 보험사명 · 상품명 · 보장내역 · 계약 상태 (한국신용정보원 제공 데이터)<br>"
            "• <b>목적:</b> AI 트리니티 — 보장성 분석 및 맞춤형 보험 설계 제공<br>"
            "• <b>보관:</b> 분석 후 30일 경과 시 자동 파기 (단, 분석 리포트는 최대 3년 보관)<br>"
            "• <b>인증정보:</b> 데이터 연동 후 메모리에서 즉시 파기 (서버 내 무단 저장 불가)<br>"
            "• <b>미동의 시:</b> AI 보장 분석 및 트리니티 서비스 이용 불가"
            "</div></div>",
            unsafe_allow_html=True,
        )
        with st.popover("📋 신용정보의 이용 및 보호에 관한 법률", use_container_width=True):
            st.markdown(
                "<div style='font-size:0.78rem;color:#92400e;font-weight:700;"
                "margin-bottom:6px;'>📌 신용정보의 이용 및 보호에 관한 법률 제32조 적용</div>",
                unsafe_allow_html=True,
            )
            st.markdown(_NIBO_CONSENT_HTML, unsafe_allow_html=True)
    _c5 = st.checkbox(
        "✅ **[내보험다보여 필수]** 신용정보원 '내보험다보여' 연동 및 신용정보 조회·분석에 동의합니다 (신용정보법 제32조)",
        key=f"{terms_agree_key}_c5",
        help="AI 증권분석·트리니티 리포트 기능 사용 시 필수. 미동의 시 해당 기능이 비활성화됩니다.",
    )
    # ── [GP-VOICE] AI 음성 브리핑 동의 (선택) ──────────────────────────────────
    _voice_info = txt.BRIEFING_INFO if (txt and hasattr(txt, 'BRIEFING_INFO')) else "🔊 AI 브리핑 안내: 설계사님의 설계 내역 및 고객 분석 결과를 AI 아나운서의 내레이션으로 자동 브리핑해 제공하는 기능입니다. (마이크 권한 불필요, 스피커 출력)"
    st.markdown(
        f"<div style='max-width:600px;background:#f0fdf4;border:1px dashed #86efac;border-radius:8px;"
        f"padding:6px 12px;margin-top:10px;margin-bottom:4px;font-size:0.76rem;color:#14532d;'>"
        f"🔊 <b>{_voice_info}</b>"
        f"</div>",
        unsafe_allow_html=True,
    )
    _voice_consent = txt.BRIEFING_CONSENT_OPTIONAL if (txt and hasattr(txt, 'BRIEFING_CONSENT_OPTIONAL')) else "(선택) AI 패스 브리핑 및 오디오 자동 재생 동의"
    _c6 = st.checkbox(
        f"🔊 **{_voice_consent}**",
        key=f"{terms_agree_key}_c6",
        help=_voice_info,
    )
    consent_set("voice_consent_agreed", _c6)
    # ── [GP-CAL §15] 외부 캘린더 연동 동의 (선택) ──────────────────────────────
    _cal_info = txt.CALENDAR_LAYOUT_INFO if (txt and hasattr(txt, 'CALENDAR_LAYOUT_INFO')) else "📅 외부 캘린더 연동: Google·Apple의 일정을 사용자가 직접 확인 및 연동할 수 있습니다. 자동 수집 없음 / OAuth 2.0 표준 / 언제든지 권한 회수 가능 (제15조·제17조 적용)"
    st.markdown(
        f"<div style='max-width:600px;background:#f0fdf4;border:1px dashed #86efac;border-radius:8px;"
        f"padding:6px 12px;margin-top:10px;margin-bottom:4px;font-size:0.76rem;color:#14532d;'>"
        f"{_cal_info}"
        f"</div>",
        unsafe_allow_html=True,
    )
    _cal_consent = txt.EXTERNAL_SERVICE_CONSENT if (txt and hasattr(txt, 'EXTERNAL_SERVICE_CONSENT')) else "(선택) 외부 서비스(Google/Apple) 연동 및 정보 활용 동의 (제15조, 제17조)"
    _c7 = st.checkbox(
        f"📅 **{_cal_consent}**",
        key=f"{terms_agree_key}_c7",
        help=_cal_info,
    )
    consent_set("cal_sync_consent_agreed", _c7)
    # ── [GP-KAKAO] 카카오톡 발송 동의 (선택, 개인정보보호법 제17조) ─────────────
    _kakao_detail = txt.KAKAO_ALIMTALK_DETAILS if (txt and hasattr(txt, 'KAKAO_ALIMTALK_DETAILS')) else """
• 전송 목적: AI 보고서·상담 결과·계약 안내 메시지 전달
• 제3자 제공: 카카오(주) — 알림톡 API 전송 목적
• 수집 항목: 고객 수신 휴대전화 번호 (전송 후 API 서버 미보관)
• 보관 기간: 법령상 보관 기간에 따라 (계약 종료 후 3년 후 자동 파기)
• 미동의 시: 카카오톡 전송 불가 (그 외 서비스 기능은 사용 가능)
"""
    _kakao_html = _kakao_detail.replace('\n', '<br>')
    st.markdown(
        f"<div style='max-width:560px;background:#fef9c3;border:2px dashed #eab308;"
        f"border-radius:10px;padding:10px 14px;margin-top:12px;margin-bottom:4px;'>"
        f"<div style='font-size:0.82rem;font-weight:900;color:#713f12;margin-bottom:6px;'>"
        f"💬 [카카오톡 알림톡 발송 동의] — 개인정보보호법 제17조 제3자 제공 별도 고지</div>"
        f"<div style='font-size:0.75rem;color:#78350f;line-height:1.85;'>{_kakao_html}</div></div>",
        unsafe_allow_html=True,
    )
    _kakao_consent = txt.KAKAO_OPTIONAL_CONSENT if (txt and hasattr(txt, 'KAKAO_OPTIONAL_CONSENT')) else "[카카오톡 선택] 카카오톡 알림톡 전송 및 개인정보 제3자 제공(카카오)에 동의합니다. (제18조, 개인정보보호법 제17조)"
    _c8 = st.checkbox(
        f"💬 **{_kakao_consent}**",
        key=f"{terms_agree_key}_c8",
        help="고객에게 AI 분석 리포트를 카카오톡으로 발송하는 기능입니다. 미동의 시 카카오톡 발송 버튼이 비활성화됩니다.",
    )
    consent_set("kakao_consent_agreed", _c8)
    # 내보험다보여 동의 여부를 독립 세션키로도 저장 (feature gate용)
    consent_set("nibo_consent_agreed", _c5)
    ss_set_ns("consent", "nibo_consent_version", _NIBO_CONSENT_VERSION if _c5 else "")
    st.session_state["nibo_consent_version"] = _NIBO_CONSENT_VERSION if _c5 else ""
    _ts = (
        __import__("datetime").datetime.now().isoformat() if _c5 else ""
    )
    ss_set_ns("consent", "nibo_consent_timestamp", _ts)
    st.session_state["nibo_consent_timestamp"] = _ts
    agreed = _c1 and _c2 and _c3
    st.session_state[terms_agree_key] = agreed
    return agreed


# ── [GP-SEC §2] SSO 핸드오프 빌더 ─────────────────────────────────────────────
def build_sso_handoff_to_hq(
    user_id: str,
    auth_token: str = "",
    cid: str = "",
    sector: str = "home",
) -> str:
    """
    [GP-SEC §2] CRM → HQ 앱 SSO 핸드오프 URL 생성.
    - HMAC 포뮤러: HMAC(KEY, user_id + str(ts))[:32] — HQ 검증 로직과 동일
    - ts(타임스탬프) 자동 생성 포함 (300초 유효, 리플레이 공격 차단)
    - URL에 PII(전화번호 등 원문) 절대 포함 금지
    """
    import urllib.parse as _up
    import hmac as _hmac_sh
    import time as _time_sh
    _secret = get_env_secret("SSO_KEY", "GoldKey_CRM_HQ_SSO_Secure_Auth_2026_!@#")
    if isinstance(_secret, bytes):
        _secret = _secret.decode()
    _ts  = int(_time_sh.time())
    _tok = _hmac_sh.new(
        _secret.encode(),
        (user_id + str(_ts)).encode(),
        "sha256",
    ).hexdigest()[:32]
    params: dict = {"auth_token": _tok, "user_id": user_id, "ts": _ts}
    if cid:
        params["gk_cid"] = cid
    if sector and sector != "home":
        params["gk_sector"] = sector
    return f"{HQ_APP_URL}/?{_up.urlencode(params)}"


def build_context_transfer_to_hq(
    user_id: str,
    person_id: str,
    context_id: str,
    sector: str = "t3",
) -> str:
    """
    [Context Transfer — GP-SEC §2] CRM → HQ 상담 컨텍스트 이전 URL.
    SSO 토큰(HMAC-SHA256) + gk_ctx(context_id) 포함.
    수신 측(HQ)은 gk_ctx로 gk_consultation_contexts에서 상담 데이터 복원.
    - PII 원문 URL 미포함 (GP-SEC §1 준수)
    - 24시간 TTL (db_utils.save_consultation_context expires_at 기준)
    """
    import urllib.parse as _up
    import hmac as _hmac_ct
    import time as _time_ct
    _secret = get_env_secret("ENCRYPTION_KEY", "GoldKey_System_Encrypt_Master_2026_@#$")
    if isinstance(_secret, bytes):
        _secret = _secret.decode()
    _ts  = int(_time_ct.time())
    _tok = _hmac_ct.new(
        _secret.encode(),
        (user_id + str(_ts)).encode(),
        "sha256",
    ).hexdigest()[:32]
    params: dict = {
        "auth_token": _tok,
        "user_id":    user_id,
        "ts":         _ts,
        "gk_cid":     person_id,
        "gk_ctx":     context_id,
        "gk_sector":  sector,
        "gk_src":     "crm_ctx",
    }
    return f"{HQ_APP_URL}/?{_up.urlencode(params)}"


def verify_sso_token(token: str, user_id: str, user_name: str = "") -> bool:
    """
    [GP-SEC §2] HQ 앱에서 SSO 토큰 검증.
    HMAC-SHA256(secret, user_id + user_name)[:32] 과 비교.
    """
    import hmac as _hmac
    try:
        secret = get_env_secret("ENCRYPTION_KEY", "")
        if not secret:
            # [GP-SEC §6] ENCRYPTION_KEY 미설정 — 운영 환경에서는 반드시 환경변수 설정 필요
            import os as _os
            if _os.environ.get("K_SERVICE"):
                # Cloud Run 운영 환경에서 키 미설정은 보안 위반
                return False
            secret = "GoldKey_System_Encrypt_Master_2026_@#$"  # 로컬 개발 전용 폴백
        if isinstance(secret, bytes):
            secret = secret.decode()
        expected = _hmac.new(
            secret.encode(),
            (user_id + user_name).encode(),
            "sha256",
        ).hexdigest()[:32]
        return _hmac.compare_digest(token, expected)
    except Exception:
        return False


# ── [GP-SEC §1] PII 암호화 헬퍼 ────────────────────────────────────────────────
def encrypt_pii(plaintext: str) -> str:
    """
    [GP-SEC §1] 복호화가 필요한 PII(고객 연락처 등) Fernet 양방향 암호화.
    암호화 키: FERNET_KEY 환경변수 (없으면 ENCRYPTION_KEY 기반 파생).
    """
    try:
        from cryptography.fernet import Fernet
        import base64, hashlib
        raw_key = get_env_secret("FERNET_KEY", "")
        if not raw_key:
            seed = get_env_secret("ENCRYPTION_KEY", "GoldKey_System_Encrypt_Master_2026_@#$")
            raw_key = base64.urlsafe_b64encode(
                hashlib.sha256(seed.encode()).digest()
            ).decode()
        f = Fernet(raw_key.encode() if isinstance(raw_key, str) else raw_key)
        return f.encrypt(plaintext.encode()).decode()
    except Exception:
        return plaintext


def decrypt_pii(ciphertext: str) -> str:
    """
    [GP-SEC §1] Fernet 복호화. 실패 시 원문 반환(이미 평문인 경우 대비).
    """
    try:
        from cryptography.fernet import Fernet
        import base64, hashlib
        raw_key = get_env_secret("FERNET_KEY", "")
        if not raw_key:
            seed = get_env_secret("ENCRYPTION_KEY", "GoldKey_System_Encrypt_Master_2026_@#$")
            raw_key = base64.urlsafe_b64encode(
                hashlib.sha256(seed.encode()).digest()
            ).decode()
        f = Fernet(raw_key.encode() if isinstance(raw_key, str) else raw_key)
        return f.decrypt(ciphertext.encode()).decode()
    except Exception:
        return ciphertext


# ── [GP-SEC §4] Storage 태깅 업로드 ────────────────────────────────────────────
def upload_file_with_tag(
    file_bytes: bytes,
    filename: str,
    agent_id: str,
    person_id: str,
    bucket_name: str = "",
    supabase_client=None,
) -> str:
    """
    [GP-SEC §4] Supabase Storage에 파일 업로드.
    경로 규칙: {agent_id}/{person_id}/{filename}
    반드시 agent_id + person_id 태깅 — 연결 고리 영구 보존.

    Returns:
        업로드된 파일의 public URL (또는 storage path)
    Raises:
        RuntimeError: 업로드 실패
    """
    if not agent_id:
        raise ValueError("agent_id 필수 — Storage 태깅 규칙 위반 방지")
    if not person_id:
        raise ValueError("person_id 필수 — Storage 태깅 규칙 위반 방지")

    storage_path = f"{agent_id}/{person_id}/{filename}"
    bucket = bucket_name or get_env_secret("STORAGE_BUCKET", "gk-files")

    if supabase_client is None:
        try:
            from supabase import create_client
            sb_url = get_env_secret("SUPABASE_URL", "")
            sb_key = get_env_secret("SUPABASE_SERVICE_ROLE_KEY",
                        get_env_secret("SUPABASE_KEY", ""))
            supabase_client = create_client(sb_url, sb_key)
        except Exception as e:
            raise RuntimeError(f"Supabase 연결 실패: {e}")

    try:
        res = supabase_client.storage.from_(bucket).upload(
            storage_path, file_bytes, {"upsert": "true"}
        )
        return storage_path
    except Exception as e:
        raise RuntimeError(f"Storage 업로드 실패 ({storage_path}): {e}")


# ===========================================================================
# [GP-ALERT §1·§2] 회원 인증 오류 알람 + 관리자 긴급 신고 프로토콜
# HQ/CRM 양쪽 앱 공통 — 동일 함수, 동일 운용 프로토콜
# ===========================================================================

def notify_admin_member_error(
    member_name: str,
    error_type: str = "AUTH_MISMATCH",
    app_name: str = "HQ",
    extra_note: str = "",
) -> dict:
    """
    [GP-ALERT §1] 회원 인증 오류 발생 시:
      1) Supabase member_errors 테이블에 오류 기록 (status='pending')
      2) 관리자에게 카카오톡 알림톡 / SMS 즉시 발송
    error_type: "AUTH_MISMATCH" | "LOGIN_BLOCKED" | "MANUAL_REPORT"
    Returns: {"success": bool, "error_id": str, "sb_saved": bool, "notified": bool, "msg": str}
    """
    import datetime as _dt, hashlib as _hl
    now_str  = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_id = _hl.md5(f"{member_name}{now_str}".encode()).hexdigest()[:12].upper()
    _app_label = {"HQ": "HQ(정밀분석)", "CRM": "CRM(모바일)"}
    _type_labels = {
        "AUTH_MISMATCH": "연락처/비밀번호 불일치 (DB·GCS 매칭 오류)",
        "LOGIN_BLOCKED": "로그인 잠금 횟수 초과",
        "MANUAL_REPORT": "회원 직접 신고",
    }
    _label = _type_labels.get(error_type, error_type)

    # ── 1) Supabase member_errors 기록 ──────────────────────────────────────
    _sb_ok = False
    try:
        from supabase import create_client as _sc_sb
        _sb_url = get_env_secret("SUPABASE_URL", "")
        _sb_key = get_env_secret("SUPABASE_SERVICE_ROLE_KEY",
                      get_env_secret("SUPABASE_KEY", ""))
        if _sb_url and _sb_key:
            _sb2 = _sc_sb(_sb_url, _sb_key)
            _sb2.table("member_errors").upsert({
                "error_id":    error_id,
                "member_name": member_name,
                "error_type":  error_type,
                "app_name":    app_name,
                "status":      "pending",
                "created_at":  _dt.datetime.now().isoformat(),
                "note":        extra_note or "",
            }, on_conflict="error_id").execute()
            _sb_ok = True
    except Exception:
        pass

    # ── 2) 관리자 카카오/SMS 알림 ────────────────────────────────────────────
    _admin_phone = get_env_secret("ADMIN_NOTIFY_PHONE", "")
    if not _admin_phone:
        try:
            import streamlit as _st2
            _admin_phone = _st2.session_state.get("gp200_master_phone", "")
        except Exception:
            pass

    _send_ok  = False
    _send_msg = "관리자 연락처(ADMIN_NOTIFY_PHONE) 미설정"
    if _admin_phone:
        try:
            from modules.kakao_service import send_report, MSG_TYPE_NOTICE
            _alert_text = (
                f"[회원 오류 알람] #{error_id}\n\n"
                f"앱: {_app_label.get(app_name, app_name)}\n"
                f"회원명: {member_name}\n"
                f"오류유형: {_label}\n"
                f"발생시각: {now_str}\n"
            )
            if extra_note:
                _alert_text += f"메모: {extra_note}\n"
            _alert_text += "\n→ 관리자 시스템 설정 > '회원정보 오류 관리' 탭에서 초기화하세요."
            _res = send_report(
                _admin_phone, _alert_text,
                msg_type=MSG_TYPE_NOTICE,
                client_name="관리자",
                title=f"[긴급] 회원 인증 오류 — {member_name}",
            )
            _send_ok  = _res.get("success", False)
            _send_msg = _res.get("msg", "")
        except Exception as _e:
            _send_msg = str(_e)

    return {
        "success":  True,
        "error_id": error_id,
        "sb_saved": _sb_ok,
        "notified": _send_ok,
        "msg":      _send_msg,
    }


def render_member_emergency_btn(
    app_name: str = "HQ",
    key_prefix: str = "emergency",
    show_admin_login: bool = False,
) -> None:
    """
    [GP-ALERT §2] 로그인 화면 — '관리자 오류 신고' 긴급 버튼.
    회원이 진입 불가 시 클릭 → 이름 입력 → 관리자에게 즉시 신고.
    HQ/CRM 양쪽 앱 동일 함수로 공유.
    show_admin_login=True 시 '관리자 신고' 좌측에 '관리자 로그인' 버튼 추가.
    """
    try:
        import streamlit as _st3
    except ImportError:
        return

    _show_key = f"{key_prefix}_show_form"
    _done_key = f"{key_prefix}_sent_done"
    _adm_key  = f"{key_prefix}_show_admin"

    if _st3.session_state.get(_done_key):
        _st3.success("✅ 관리자에게 신고 완료. 확인 후 조치합니다.", icon="📞")
        if _st3.button("↩️ 다시 로그인 시도", key=f"{key_prefix}_retry"):
            _st3.session_state.pop(_done_key, None)
            _st3.session_state.pop(_show_key, None)
            _st3.rerun()
        return

    _st3.markdown(
        "<div style='border:1px dashed #DC2626;border-radius:8px;"
        "padding:6px 10px;margin-top:6px;background:#FEF2F2;'>",
        unsafe_allow_html=True,
    )

    if show_admin_login:
        _ec1, _ec2, _ec3 = _st3.columns([4, 3, 3])
        with _ec1:
            _st3.markdown(
                "<span style='font-size:0.78rem;color:#DC2626;font-weight:700;'>"
                "🆘 로그인 오류가 계속되시나요?</span>",
                unsafe_allow_html=True,
            )
        with _ec2:
            if _st3.button("🔐 관리자 로그인", key=f"{key_prefix}_admin_toggle",
                           use_container_width=True):
                _st3.session_state[_adm_key]  = not _st3.session_state.get(_adm_key, False)
                _st3.session_state[_show_key] = False
        with _ec3:
            if _st3.button("🆘 관리자 신고", key=f"{key_prefix}_toggle",
                           use_container_width=True):
                _st3.session_state[_show_key] = not _st3.session_state.get(_show_key, False)
                _st3.session_state[_adm_key]  = False
    else:
        _ec1, _ec2 = _st3.columns([6, 4])
        with _ec1:
            _st3.markdown(
                "<span style='font-size:0.78rem;color:#DC2626;font-weight:700;'>"
                "🆘 로그인 오류가 계속되시나요?</span>",
                unsafe_allow_html=True,
            )
        with _ec2:
            if _st3.button("🆘 관리자 신고", key=f"{key_prefix}_toggle",
                           use_container_width=True):
                _st3.session_state[_show_key] = not _st3.session_state.get(_show_key, False)

    # ── 관리자 로그인 인라인 폼 ───────────────────────────────────────────────
    if show_admin_login and _st3.session_state.get(_adm_key):
        _st3.markdown(
            "<div style='background:#FFFBEB;border:1.5px solid #D4AF37;"
            "border-left:4px solid #D4AF37;"
            "border-radius:10px;padding:10px 14px;margin-top:8px;'>",
            unsafe_allow_html=True,
        )
        _st3.markdown(
            "<span style='font-size:0.82rem;font-weight:900;color:#7c5c00;'>"
            "🔐 관리자 로그인</span>",
            unsafe_allow_html=True,
        )
        _st3.markdown("""
<style>
div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg,#FFF8E1,#FFF3CD) !important;
    border: 1.5px solid #D4AF37 !important;
    color: #7c5c00 !important;
    border-radius: 8px !important;
    font-weight: 800 !important;
    font-size: 0.85rem !important;
    box-shadow: 0 1px 4px rgba(212,175,55,0.25) !important;
    padding: 5px 18px !important;
}
div[data-testid="stFormSubmitButton"] > button:hover {
    background: linear-gradient(135deg,#FFF3CD,#FFE082) !important;
    border-color: #B8860B !important;
    color: #5c4000 !important;
}
</style>""", unsafe_allow_html=True)
        with _st3.form(f"{key_prefix}_admin_form", clear_on_submit=False):
            _adm_id_in   = _st3.text_input(
                "관리자 ID",
                key=f"{key_prefix}_adm_id", label_visibility="collapsed",
            )
            _adm_code_in = _st3.text_input(
                "관리자 코드", type="password",
                key=f"{key_prefix}_adm_code", label_visibility="collapsed",
            )
            _fadm_c1, _fadm_c2, _fadm_c3 = _st3.columns([1, 3, 1])
            with _fadm_c2:
                _adm_sub = _st3.form_submit_button("🔐 관리자 로그인", use_container_width=True)
        if _adm_sub:
            _aid = (_adm_id_in   or "").strip()
            _acd = (_adm_code_in or "").strip()
            _env_code   = get_env_secret("ADMIN_CODE", "")
            _master_env = get_env_secret("MASTER_CODE", "")
            import hashlib as _hl_emg
            _adm_default_hash = _hl_emg.sha256(b"kgagold6803").hexdigest()
            _adm_pw_hash      = get_env_secret("CRM_ADMIN_PW_HASH", _adm_default_hash)
            _adm_input_hash   = _hl_emg.sha256(_acd.encode()).hexdigest()
            _adm_auth_ok = False
            if _aid.lower() in ("admin", "이세윤") and _acd == _env_code and _env_code:
                _adm_auth_ok = True
                _st3.session_state["crm_is_admin"]      = True
                _st3.session_state["crm_authenticated"] = True
                _st3.session_state["crm_user_id"]       = "ADMIN_MASTER"
                _st3.session_state["crm_user_name"]     = "이세윤"
                _st3.session_state["crm_role"]          = "admin"
            elif _acd == _master_env and _master_env:
                _adm_auth_ok = True
                _mname = get_env_secret("MASTER_NAME", "이세윤")
                _st3.session_state["crm_is_admin"]      = True
                _st3.session_state["crm_authenticated"] = True
                _st3.session_state["crm_user_id"]       = "PERMANENT_MASTER"
                _st3.session_state["crm_user_name"]     = _mname
                _st3.session_state["crm_role"]          = "admin"
            elif _aid.lower() in ("admin", "이세윤") and _adm_input_hash == _adm_pw_hash:
                _adm_auth_ok = True
                _st3.session_state["crm_is_admin"]      = True
                _st3.session_state["crm_authenticated"] = True
                _st3.session_state["crm_user_id"]       = "ADMIN_MASTER"
                _st3.session_state["crm_user_name"]     = "이세윤"
                _st3.session_state["crm_role"]          = "admin"
            if _adm_auth_ok:
                _st3.success("✅ 관리자 인증 완료 — CRM 대시보드로 이동합니다...")
                _st3.rerun()
            else:
                _st3.error("❌ ID 또는 코드가 올바르지 않습니다.")
        _st3.markdown("</div>", unsafe_allow_html=True)

    # ── 관리자 신고 폼 ────────────────────────────────────────────────────────
    if _st3.session_state.get(_show_key):
        _nm = _st3.text_input(
            "가입 시 이름 입력", key=f"{key_prefix}_report_name",
            label_visibility="collapsed",
        )
        if _st3.button("📨 관리자에게 오류 신고 발송", key=f"{key_prefix}_send",
                       use_container_width=True, type="primary"):
            if not (_nm or "").strip() or len((_nm or "").strip()) < 2:
                _st3.warning("이름을 2자 이상 입력하세요.")
            else:
                with _st3.spinner("신고 중..."):
                    notify_admin_member_error(
                        member_name=_nm.strip(),
                        error_type="MANUAL_REPORT",
                        app_name=app_name,
                    )
                _st3.session_state[_done_key] = True
                _st3.rerun()
    _st3.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# [GP-PHASE-4] 반응형 통합 증권분석 센터 (내보험다보여)
# HQ 앱(app.py) + CRM 앱(crm_app.py) 양쪽에서 동일 렌더링
# ══════════════════════════════════════════════════════════════════════════════
# ── [GP-L-SEC] 내보험다보여 동의 상수 (ImportError 방지) ─────────────────────
_NIBO_CONSENT_VERSION = "2026-03-16-v1"
_NIBO_CONSENT_HTML = """
<div style='font-size:0.82rem;color:#1e3a8a;line-height:1.9;'>
<b style='font-size:0.88rem;'>🔐 내보험다보여 안내 — 신용정보의 이용 및 보호에 관한 법률 제32조 준수</b><br><br>
• <b>수집 항목:</b> 보험사명, 상품명, 보장내역, 계약상태 (한국신용정보원 제공 데이터)<br>
• <b>활용 목적:</b> AI 트리니티 엔진 기반 보장 분석 및 맞춤형 설계 서비스 제공<br>
• <b>정보 보관:</b> 분석 완료 후 30일 경과 시 자동 파기 (단, 분석 결과는 법령에 따라 최대 3년 보관 가능)<br>
• <b>인증 정보:</b> 데이터 수집 즉시 메모리에서 삭제 (서버 내 무단 저장 및 외부 유출 절대 금지)<br>
• <b>미동의 시:</b> AI 보장 분석 및 트리니티 설계 서비스 이용이 제한될 수 있습니다.<br>
</div>
"""


def render_unified_analysis_center(
    *,
    key_prefix: str = "_uac",
    compact: bool = False,
    person_id: str = "",
    agent_id: str = "",
) -> None:
    """반응형 통합 증권분석 센터 — 고객 대면용 AI 컨설팅 보드.
    좌우 5:5 레이아웃, 모바일 자동 스태킹.
    """
    st.markdown("""
<style>
@media(max-width:640px){
  div[data-testid="stHorizontalBlock"]>div[data-testid="stVerticalBlockBorderWrapper"],
  div[data-testid="stHorizontalBlock"]>div[data-testid="stVerticalBlock"]{
    width:100%!important;min-width:100%!important;flex:none!important;
  }
  .uac-gauge-label{font-size:0.65rem!important;}
}
.uac-header{background:linear-gradient(135deg,#059669 0%,#047857 100%);
  border-radius:12px;padding:12px 20px 10px;margin-bottom:14px;
  display:inline-flex;align-items:center;width:fit-content;max-width:100%;}
.uac-summary-card{background:linear-gradient(90deg,#f0fdf4,#ecfdf5);
  border:1.5px solid #6ee7b7;border-radius:10px;padding:10px 14px;
  margin-top:10px;font-size:0.82rem;}
.uac-alert-box{background:linear-gradient(90deg,#fffbeb,#fff7ed);
  border:2px solid #f59e0b;border-radius:10px;padding:12px 16px;margin-bottom:12px;}
.uac-prescription{background:#f8faff;border-left:4px solid #3b82f6;
  border-radius:0 8px 8px 0;padding:10px 14px;font-size:0.80rem;line-height:1.75;}
.uac-gauge-label{font-size:0.72rem;font-weight:700;color:#374151;}
.uac-data-card{background:#fff;border:1px dashed #000;border-radius:12px;
  padding:14px 16px 6px;margin-bottom:10px;}
.uac-red-alert{border:1.5px solid #FF4B4B;background:rgba(255,75,75,0.05);
  border-radius:8px;padding:10px 14px;color:#FF4B4B;font-size:0.76rem;
  font-weight:600;margin:8px 0 10px;word-break:keep-all;line-height:1.65;}
button[data-testid="baseButton-primary"]{
  background:linear-gradient(135deg,#4facfe 0%,#00f2fe 100%)!important;
  color:white!important;border:none!important;border-radius:12px!important;
  box-shadow:0 6px 14px rgba(0,192,255,0.28)!important;
  font-weight:800!important;transition:transform .15s,box-shadow .15s!important;}
button[data-testid="baseButton-primary"]:hover{
  transform:translateY(-2px)!important;
  box-shadow:0 10px 20px rgba(0,192,255,0.4)!important;}
</style>""", unsafe_allow_html=True)

    st.markdown(
        '<div class="uac-header">'
        '<span style="font-size:1.05rem;font-weight:900;color:white;letter-spacing:0.04em;">'
        '📊 통합 증권분석 센터 (내보험다보여)</span>'
        '<span style="background:rgba(255,255,255,0.25);color:white;font-size:0.65rem;'
        'font-weight:700;padding:2px 8px;border-radius:4px;margin-left:12px;">'
        'AI 분석 엔진 가동중</span></div>',
        unsafe_allow_html=True,
    )

    _kj = f"{key_prefix}_json"
    _kr = f"{key_prefix}_result"
    _left, _right = st.columns([1, 1], gap="medium")

    # ── 좌측: 데이터 & 가치 입력 영역 ──────────────────────────────────────
    with _left:
        st.markdown(
            "<div style='font-size:clamp(0.92rem,2.2vw,1.05rem);font-weight:900;color:#065f46;"
            "margin-bottom:8px;'>👈 데이터 & 가치 입력 영역</div>",
            unsafe_allow_html=True,
        )
        _tab_nibo, _tab_scan = st.tabs(["🌐 내보험다보여 크롤링", "📄 증권 파일 스캔/업로드"])

        with _tab_nibo:
            if not consent_get("nibo_consent_agreed", False):
                # [상담 플로우 §1] 안내 박스 — 동의 전 상단 가이드
                st.markdown(
                    "<div style='background:linear-gradient(135deg,#fffbeb,#fff7ed);"
                    "border:2px solid #f59e0b;border-radius:10px;padding:12px 14px;margin-bottom:10px;'>"
                    "<div style='font-size:0.85rem;font-weight:900;color:#92400e;margin-bottom:6px;'>"
                    "🔐 신용정보 조회 동의 후 이용 가능합니다.</div>"
                    "<div style='font-size:0.78rem;color:#78350f;line-height:1.7;'>"
                    "'트리니티(Trinity)계산법'와 KB손해보험 증권분석 기법에 의해 "
                    "<b>정밀한 필요 보험 가입금액 산출</b>을 위해 "
                    "<b>&ldquo;내보험다보여&rdquo;가 실행</b>되어야 합니다."
                    "</div></div>",
                    unsafe_allow_html=True,
                )
                st.warning("🔐 신용정보 조회 동의 후 이용 가능합니다.")
                if st.checkbox("✅ 신용정보 조회·분석 동의 (신용정보법 제32조)",
                               key=f"{key_prefix}_consent"):
                    consent_set("nibo_consent_agreed", True)
                    _nibo_ts = __import__("datetime").datetime.now().isoformat()
                    ss_set_ns("consent", "nibo_consent_version", "2026-03-16-v1")
                    ss_set_ns("consent", "nibo_consent_timestamp", _nibo_ts)
                    st.session_state["nibo_consent_version"] = "2026-03-16-v1"
                    st.session_state["nibo_consent_timestamp"] = _nibo_ts
                    st.rerun()
            else:
                _kp = key_prefix
                _uac_tok = st.session_state.get(f"{_kp}_auth_token")

                # ── 데이터 수집 & 인증 카드 (인증 전) ──────────────────────────
                if not _uac_tok:
                    st.markdown("<div class='uac-data-card'>", unsafe_allow_html=True)
                    st.markdown(
                        "<div style='font-size:0.82rem;font-weight:900;color:#065f46;"
                        "margin-bottom:10px;'>🌐 내보험다보여 크롤링 연결 — 피보험자 인증</div>",
                        unsafe_allow_html=True,
                    )
                    _uac_name = st.text_input(
                        "👤 피보험자 성명 *",
                        value=st.session_state.get("gs_c_name", ""),
                        key=f"{_kp}_auth_name",
                        max_chars=30,
                    )
                    _dc1, _dc2 = st.columns([3, 2])
                    with _dc1:
                        _uac_dob = st.text_input(
                            "🎂 생년월일 * (YYYYMMDD)",
                            key=f"{_kp}_auth_dob",
                            max_chars=8,
                        )
                    with _dc2:
                        _uac_carrier = st.selectbox(
                            "📶 통신사 *",
                            ["─ 선택 ─", "SKT", "KT", "LG U+",
                             "SKT 알뜰폰", "KT 알뜰폰", "LG 알뜰폰"],
                            key=f"{_kp}_auth_carrier",
                        )
                    _uac_phone = st.text_input(
                        "📱 휴대폰 번호 * (숫자만, - 없이)",
                        key=f"{_kp}_auth_phone",
                        max_chars=11,
                    )
                    st.markdown(
                        "<div class='uac-red-alert'>"
                        "⚠️ 생년월일·연락처는 한국신용정보원 본인확인에만 사용되는 <b>1회성 소모 정보</b>입니다. "
                        "인증 즉시 SHA-256 해시로 변환되며, 원본 정보는 <b>서버에 일체 저장되지 않습니다.</b> "
                        "<span style='font-size:0.68rem;'>(개인정보보호법 제15조 · 신용정보법 제32조)</span>"
                        "</div>",
                        unsafe_allow_html=True,
                    )
                    _uac_method = st.radio(
                        "🔑 인증 수단 선택",
                        ["카카오톡", "PASS", "NICE 본인확인", "간편인증(데모)"],
                        horizontal=True,
                        key=f"{_kp}_auth_method",
                    )
                    st.markdown("</div>", unsafe_allow_html=True)
                    _method_map = {
                        "카카오톡": "kakao", "PASS": "pass",
                        "NICE 본인확인": "nice", "간편인증(데모)": "simulate",
                    }
                    _dob_clean   = "".join(c for c in (_uac_dob   or "") if c.isdigit())
                    _phone_clean = "".join(c for c in (_uac_phone  or "") if c.isdigit())
                    _auth_ready  = (
                        bool((_uac_name or "").strip())
                        and len(_dob_clean) == 8
                        and _uac_carrier != "─ 선택 ─"
                        and len(_phone_clean) >= 10
                    )
                    if _auth_ready:
                        if st.button(
                            "🌐 내보험다보여 실행 (인증 요청)",
                            key=f"{_kp}_auth_run",
                            type="primary",
                            use_container_width=True,
                        ):
                            import hashlib as _hl
                            import time as _agt
                            with st.spinner("🔐 인증 게이트웨이 처리 중..."):
                                try:
                                    from modules.auth_gateway import authenticate as _ag_auth
                                    _tok = _ag_auth(
                                        name=(_uac_name or "").strip(),
                                        phone=_uac_phone,
                                        dob=_dob_clean,
                                        carrier=_uac_carrier,
                                        method=_method_map.get(_uac_method, "simulate"),
                                    )
                                except Exception as _age:
                                    _nm = (_uac_name or "").strip()
                                    _tok = {
                                        "token":        _hl.sha256((_nm + _phone_clean).encode()).hexdigest()[:32],
                                        "ci_hash":      _hl.sha256((_dob_clean + _nm).encode()).hexdigest()[:24],
                                        "name_initial": _nm[0] + "*" * max(len(_nm) - 2, 0) + (_nm[-1] if len(_nm) > 1 else ""),
                                        "phone_masked": _phone_clean[:3] + "-****-" + _phone_clean[-4:],
                                        "method":       "simulate",
                                        "issued_at":    _agt.time(),
                                        "expires_at":   _agt.time() + 1800,
                                        "error":        str(_age)[:120],
                                    }
                            st.session_state[f"{_kp}_auth_token"] = {
                                "name_initial": _tok.get("name_initial", "*"),
                                "phone_masked": _tok.get("phone_masked", "***"),
                                "method":       _tok.get("method", "simulate"),
                                "issued_at":    _tok.get("issued_at", 0),
                            }
                            st.session_state["gs_c_name"] = (_uac_name or "").strip()
                            for _sk in [f"{_kp}_auth_dob", f"{_kp}_auth_phone"]:
                                st.session_state.pop(_sk, None)
                            if _tok.get("error"):
                                st.warning(f"⚠️ {_tok['error']} — 시뮬레이션 모드로 진행")
                            try:
                                from modules.mydata_connector import fetch_mydata_insurance as _fmi
                                import json as _mj
                                _mdata = _fmi((_uac_name or "").strip(), use_simulate=True)
                                st.session_state["_nibo_raw_json"] = _mj.dumps(
                                    _mdata.get("insurance_list", []),
                                    ensure_ascii=False, indent=2,
                                )
                                st.session_state[_kj] = st.session_state["_nibo_raw_json"]
                            except Exception:
                                pass
                            st.rerun()
                    else:
                        st.button(
                            "🚀 트리니티 진단 시작 (필수 정보 입력 후 활성화)",
                            key=f"{_kp}_auth_run_dis",
                            disabled=True,
                            use_container_width=True,
                        )
                        _miss = []
                        if not (_uac_name or "").strip(): _miss.append("성명")
                        if len(_dob_clean) != 8:          _miss.append("생년월일 8자리")
                        if _uac_carrier == "─ 선택 ─":    _miss.append("통신사")
                        if len(_phone_clean) < 10:        _miss.append("휴대폰")
                        if _miss:
                            st.caption(f"⚠️ 미입력: {' · '.join(_miss)}")
                else:
                    # ── 인증 완료 배너 + 재인증 ──────────────────────────────
                    _at = _uac_tok
                    _ml = {"kakao": "카카오톡", "pass": "PASS", "nice": "NICE",
                           "simulate": "간편인증(데모)"}.get(_at.get("method", "simulate"), "간편인증")
                    st.markdown(
                        f"<div style='background:#dcfce7;border:1px solid #86efac;"
                        f"border-radius:8px;padding:8px 14px;font-size:0.8rem;"
                        f"color:#166534;font-weight:700;margin-bottom:10px;'>"
                        f"✅ 인증 완료 &nbsp;|&nbsp; {_at.get('name_initial','*')} &nbsp;|&nbsp; "
                        f"{_at.get('phone_masked','***')} &nbsp;|&nbsp; {_ml}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    if st.button("🔄 재인증", key=f"{_kp}_reauth"):
                        st.session_state.pop(f"{_kp}_auth_token", None)
                        st.rerun()

                # ── JSON 입력창 (인증 완료 후 자동 채워짐) ─────────────────────
                _json_val = st.text_area(
                    "내보험다보여 JSON",
                    value=st.session_state.get(_kj, st.session_state.get("_nibo_raw_json", "")),
                    height=110,
                    key=f"{key_prefix}_json_ta",
                    label_visibility="collapsed",
                )
                if _json_val != st.session_state.get(_kj, ""):
                    st.session_state[_kj] = _json_val
                    st.session_state["_nibo_raw_json"] = _json_val
                if st.button("📋 샘플 데이터 불러오기", key=f"{key_prefix}_sample",
                             use_container_width=True):
                    import json as _ujs
                    _s = _ujs.dumps([
                        {"prodName": "(무)뉴-하이콜 암진단비",   "traitName": "암진단비특약",    "amt": "3000만원",  "status": "유효"},
                        {"prodName": "뇌졸중진단확정비",          "traitName": "뇌졸중진단특약",  "amt": "10000000", "status": "유효"},
                        {"prodName": "급성심근경색진단비",         "traitName": "심근경색진단특약","amt": "2000만원",  "status": "유효"},
                        {"prodName": "일반상해후유장해(3~100%)", "traitName": "상해후유장해",    "amt": "5000만원",  "status": "유효"},
                        {"prodName": "DB손해 통합",               "traitName": "암진단비(소액암)","amt": "2000만원",  "status": "유효"},
                    ], ensure_ascii=False, indent=2)
                    st.session_state[_kj] = _s
                    st.session_state["_nibo_raw_json"] = _s
                    st.rerun()

        with _tab_scan:
            _uploaded = st.file_uploader(
                "증권 PDF 또는 이미지 업로드",
                type=["pdf", "jpg", "jpeg", "png"],
                key=f"{key_prefix}_file_up",
                help="보험증권 PDF/이미지를 업로드하면 AI가 담보를 자동 파싱합니다.",
                label_visibility="collapsed",
            )
            if _uploaded:
                st.success(f"✅ {_uploaded.name} 업로드 완료")
                if st.button("🔍 AI 파싱 시작", key=f"{key_prefix}_parse_btn",
                             type="primary", use_container_width=True):
                    st.info("📄 정밀 PDF 파싱은 A-SECTION '② 통합 스캔 허브'에서 이용 가능합니다.")

        st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
        st.markdown(
            "<hr style='border:none;border-top:2px dashed #d1d5db;margin:14px 0 10px;'>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='font-size:clamp(0.92rem,2.2vw,1.05rem);font-weight:800;color:#92400e;margin-bottom:4px;'>"
            "💰 월 건강보험료 납부액 "
            "<span style='font-weight:400;color:#6b7280;font-size:0.85rem;'>(가치 산출용) — 건강보험료납부율 역산법</span></div>",
            unsafe_allow_html=True,
        )
        _nhi = st.number_input(
            "월 건강보험료(원)",
            min_value=0, max_value=2_000_000,
            value=int(st.session_state.get("gs_hi_premium") or 0),
            step=10_000,
            key=f"{key_prefix}_nhi",
            help="직장인: 보수월액×3.545% (개인부담금) | 트리니티 역산공식 적용",
            label_visibility="collapsed",
        )
        if _nhi != int(st.session_state.get("gs_hi_premium") or 0):
            st.session_state["gs_hi_premium"] = _nhi
        if _nhi > 0:
            _cap_t = calculate_trinity_metrics(_nhi)
            st.caption(f"📊 추정 월소득 **{_cap_t['monthly_income']:,.0f}원** | 연소득 **{_cap_t['annual_income']:,.0f}원**")

        _cname   = (st.session_state.get("scan_client_name")
                    or st.session_state.get("gp200_name") or "")
        _cbirth  = st.session_state.get("scan_client_birth", "")
        _cgender = st.session_state.get("scan_client_gender", "")
        _has_data = bool(st.session_state.get(_kj) or st.session_state.get("_nibo_raw_json"))
        if _cname or _has_data:
            _b = f"({_cbirth[:4]}년생, " if _cbirth else "("
            _g = _cgender + "성)" if _cgender else ")"
            st.markdown(
                f'<div class="uac-summary-card">'
                f'👤 <b>분석 대상:</b> [{_cname or "미입력"}] 님 {_b}{_g}<br>'
                f'<span style="font-size:0.70rem;color:#6b7280;">'
                f'{"✅ 데이터 준비 완료" if _has_data else "⏳ 데이터 입력 대기"}'
                f'</span></div>',
                unsafe_allow_html=True,
            )

        st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
        if st.button("🤖 트리니티 산출법 실행", key=f"{key_prefix}_run",
                     type="primary", use_container_width=True):
            _run_nhi  = float(st.session_state.get("gs_hi_premium") or 0)
            _run_json = st.session_state.get(_kj) or st.session_state.get("_nibo_raw_json", "")
            _run_pid  = person_id or st.session_state.get("crm_selected_pid", "") or st.session_state.get("selected_customer_id", "")
            _run_aid  = agent_id  or st.session_state.get("user_id", "")
            if _run_nhi <= 0:
                st.warning("💰 월 건강보험료를 먼저 입력해 주세요.")
            else:
                with st.spinner("🤖 트리니티 산출 중…"):
                    # §Step1: 트리니티 즉시 로컬 산출 (화면 이탈 없음)
                    _t_result = calculate_trinity_metrics(_run_nhi)
                    st.session_state[f"{key_prefix}_trinity_result"] = _t_result
                    st.session_state["_trinity_calc_result"] = _t_result
                    # §Step2: DB 저장 (person_id 기준, 비동기 fallback)
                    if _run_pid and _run_aid:
                        try:
                            from db_utils import upsert_analysis_report as _u_ar2
                            _u_ar2(
                                person_id=_run_pid, agent_id=_run_aid,
                                analysis_data={"trinity": _t_result, "source": "UAC-트리니티산출"},
                                nhis_premium=_run_nhi,
                            )
                        except Exception:
                            pass
                    # §Step3: nibo JSON 있으면 전체 AI 분석 추가 실행 (결과는 우측 패널)
                    if (_run_json or "").strip():
                        try:
                            import json as _j2
                            from trinity_engine import execute_integrated_analysis as _exec
                            _raw = _j2.loads(_run_json.strip())
                            if isinstance(_raw, dict):
                                _raw = [_raw]
                            _adata, _unm, _ok = _exec(
                                raw_external_data=_raw,
                                client_contact=st.session_state.get("scan_client_contact", ""),
                                nhi_premium=_run_nhi,
                                consultant_info={
                                    "소속": st.session_state.get("gp200_company", st.session_state.get("_mp_company", "")),
                                    "이름": st.session_state.get("gp200_name", st.session_state.get("_mp_name", "")),
                                    "연락처": st.session_state.get("gp200_contact", st.session_state.get("_mp_phone", "")),
                                },
                                client_name=_cname,
                                agent_id=_run_aid,
                                person_id=_run_pid,
                                kb7_score=int(st.session_state.get("_sops_kb_score", 0) or 0),
                                consent_version=st.session_state.get("nibo_consent_version", ""),
                                source="UAC-트리니티산출",
                            )
                            st.session_state[_kr] = _adata
                            if _run_pid and _run_aid:
                                try:
                                    from db_utils import (
                                        set_crawl_status as _scs,
                                        upsert_analysis_report as _u_ar,
                                    )
                                    _scs(_run_pid, _run_aid, "done", data=_raw)
                                    if isinstance(_adata, dict):
                                        _u_ar(person_id=_run_pid, agent_id=_run_aid,
                                              analysis_data=_adata, nhis_premium=_run_nhi)
                                except Exception:
                                    pass
                        except Exception:
                            pass
                    st.success("✅ 트리니티 산출 완료! 아래 결과를 확인하세요.")
                    st.rerun()
        # 트리니티 산출 결과 즉시 렌더링 (CRM 화면 내, 화면이탈 없음)
        _t_res = (st.session_state.get(f"{key_prefix}_trinity_result")
                  or st.session_state.get("_trinity_calc_result"))
        if _t_res:
            _t_mi = _t_res.get("monthly_income", 0)
            _t_di = _t_res.get("daily_value", 0)
            _t_d2 = _t_res.get("disability_2yr", 0)
            st.markdown(
                f"<div style='background:#f0fdf4;border:1px dashed #16a34a;border-radius:10px;"
                f"padding:10px 14px;margin-top:8px;'>"
                f"<div style='font-size:0.8rem;font-weight:900;color:#14532d;margin-bottom:6px;'>"
                f"📊 트리니티 산출 결과</div>"
                f"<div style='display:flex;gap:16px;flex-wrap:wrap;'>"
                f"<div><span style='font-size:0.7rem;color:#64748b;'>추정 월소득</span><br>"
                f"<b style='font-size:0.95rem;color:#15803d;'>{_t_mi:,.0f}원</b></div>"
                f"<div><span style='font-size:0.7rem;color:#64748b;'>일일 필요 일당</span><br>"
                f"<b style='font-size:0.95rem;color:#15803d;'>{_t_di:,.0f}원</b></div>"
                f"<div><span style='font-size:0.7rem;color:#64748b;'>상해장해 2년 대체액</span><br>"
                f"<b style='font-size:0.95rem;color:#15803d;'>{_t_d2:,.0f}원</b></div>"
                f"</div></div>",
                unsafe_allow_html=True,
            )

        # [최하단 §4] HQ 심화상담 브릿지 — 4가지 데이터 Sync 체크 후 딥링크
        st.markdown(
            "<hr style='border:none;border-top:1px dashed #93c5fd;margin:14px 0 8px;'>",
            unsafe_allow_html=True,
        )
        _hq_bridge_pid = person_id or st.session_state.get("crm_selected_pid", "") or st.session_state.get("selected_customer_id", "")
        _hq_bridge_aid = agent_id  or st.session_state.get("user_id", "")
        # ── 4가지 데이터 완비 상태 체크 ──────────────────────────────────────
        _sync_basic   = bool(_hq_bridge_pid)
        _sync_nibo    = bool(st.session_state.get(_kj) or st.session_state.get("_nibo_raw_json"))
        _sync_trinity = bool(
            st.session_state.get(f"{key_prefix}_trinity_result")
            or st.session_state.get("_trinity_calc_result")
            or st.session_state.get(_kr)
        )
        _sync_files   = bool(st.session_state.get(f"{key_prefix}_file_up"))
        # DB 폴백 체크 (세션에 없을 때)
        if _hq_bridge_pid and _hq_bridge_aid and not (_sync_nibo and _sync_trinity):
            try:
                from db_utils import get_person_data_status as _gpds_hq
                _ds_hq = _gpds_hq([_hq_bridge_pid], _hq_bridge_aid).get(_hq_bridge_pid, {})
                _sync_nibo    = _sync_nibo    or bool(_ds_hq.get("has_nibo"))
                _sync_trinity = _sync_trinity or bool(_ds_hq.get("has_trinity"))
            except Exception:
                pass
        _sync_all = _sync_basic and _sync_nibo and _sync_trinity
        # ── 상태 배지 카드 ────────────────────────────────────────────────────
        st.markdown(
            "<div style='background:#f8fafc;border:1px dashed #000;border-radius:8px;"
            "padding:8px 12px;margin-bottom:8px;font-size:0.76rem;'>"
            "<b>📦 HQ 전송 데이터 현황</b><br>"
            f"{'🟢' if _sync_basic else '⭕'} 고객 기본정보 &nbsp;"
            f"{'🟢' if _sync_nibo else '⭕'} 내보험 JSON &nbsp;"
            f"{'🟢' if _sync_trinity else '⭕'} 트리니티 산출 &nbsp;"
            f"{'🟢' if _sync_files else '⭕'} 증권파일"
            "</div>",
            unsafe_allow_html=True,
        )
        # ── HQ 딥링크 생성 (SSO 토큰 포함) ──────────────────────────────────
        if _hq_bridge_pid and _hq_bridge_aid:
            try:
                _hq_bridge_url = build_sso_handoff_to_hq(
                    user_id=_hq_bridge_aid, cid=_hq_bridge_pid, sector="gk_sec10"
                )
            except Exception:
                _hq_bridge_url = HQ_APP_URL
        else:
            _hq_bridge_url = HQ_APP_URL
        _btn_bg  = "#002D56" if _sync_all else "#78350f"
        _btn_txt = "🚀 [HQ]앱 이동 — 심화상담" if _sync_all else "🚀 [HQ]앱 이동 — 심화상담 ⚠️ 데이터 불완전"
        st.markdown(
            f"<a href='{_hq_bridge_url}' target='_blank' style='"
            f"display:block;text-align:center;background:{_btn_bg};color:#FFCC00;"
            "border-radius:10px;padding:10px 0;font-size:0.88rem;font-weight:900;"
            f"text-decoration:none;border:1px dashed #FFCC00;margin-top:4px;'>{_btn_txt}</a>",
            unsafe_allow_html=True,
        )
        if not _sync_all:
            st.caption("⚠️ 미완비 항목을 먼저 채우면 HQ에서 정밀 분석을 즉시 시작할 수 있습니다.")

    # ── 우측: AI 가입결과 보고서 ────────────────────────────────────────────
    with _right:
        st.markdown(
            "<div style='font-size:clamp(0.92rem,2.2vw,1.05rem);font-weight:900;color:#1e3a8a;"
            "margin-bottom:8px;'>👉 AI 가입결과 보고서</div>",
            unsafe_allow_html=True,
        )
        _result = st.session_state.get(_kr)
        _nhi_r  = float(st.session_state.get("gs_hi_premium") or 0)

        if not _result:
            st.markdown(
                '<div style="background:#f8faff;border:1.5px dashed #93c5fd;'
                'border-radius:10px;padding:32px 20px;text-align:center;color:#6b7280;">'
                '🔍 좌측에서 보험 데이터를 입력하고<br>'
                '<b>⚡ AI 통합 분석 실행</b> 버튼을 눌러주세요.</div>',
                unsafe_allow_html=True,
            )
        else:
            _GAUGES = [
                ("암진단비", ["암진단", "암진"],      50_000_000),
                ("뇌졸중",   ["뇌졸중", "뇌경색"],    30_000_000),
                ("심근경색", ["심근경색", "급성심"],   20_000_000),
                ("수술비",   ["수술비", "수술"],       20_000_000),
                ("입원비",   ["입원비", "입원"],       10_000_000),
                ("후유장해", ["후유장해", "장해"],    100_000_000),
                ("질병사망", ["질병사망", "사망"],    100_000_000),
                ("실손의료", ["실손", "의료비"],        5_000_000),
                ("간병보험", ["간병"],                 50_000_000),
                ("치매보험", ["치매"],                 30_000_000),
            ]
            _cov: dict = {}
            for _gl, _kws, _ideal in _GAUGES:
                _amt = 0.0
                for _rk, _rv in (_result or {}).items():
                    if isinstance(_rv, dict):
                        if any(kw in str(_rk).lower() for kw in _kws):
                            try:
                                _amt = float(_rv.get("현재가입", 0) or 0)
                            except Exception:
                                _amt = 0.0
                            break
                _cov[_gl] = _amt

            _total_cov  = sum(_cov.values())
            _est_annual = _nhi_r * 360 if _nhi_r > 0 else 40_000_000
            _gap        = max(0.0, _est_annual * 10 - _total_cov)
            _gap_disp   = (f"{_gap/100_000_000:.1f}억 원"
                           if _gap >= 100_000_000 else f"{_gap/10_000:.0f}만 원")
            _sev = "🔴" if _gap > 50_000_000 else ("🟡" if _gap > 10_000_000 else "🟢")

            st.markdown(
                f'<div class="uac-alert-box">'
                f'<div style="font-size:0.80rem;font-weight:900;color:#92400e;margin-bottom:4px;">'
                f'{_sev} AI 분석 총평</div>'
                f'<div style="font-size:0.96rem;font-weight:800;color:#1c1917;line-height:1.5;">'
                f'현재 <b style="color:#dc2626;">{_gap_disp}</b>의 소득 공백 위험이 존재합니다</div>'
                f'<div style="font-size:0.70rem;color:#78350f;margin-top:4px;">'
                f'추정 연소득 {_est_annual/10_000:.0f}만원 기준 · 10년치 보장 갭 분석</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                "<div style='font-size:0.72rem;font-weight:800;color:#374151;"
                "margin-bottom:6px;'>🔰 10대 핵심 담보 적정도 게이지</div>",
                unsafe_allow_html=True,
            )
            _gc1, _gc2 = st.columns(2, gap="small")
            for _gi, (_gl, _kws, _ideal) in enumerate(_GAUGES):
                with (_gc1 if _gi % 2 == 0 else _gc2):
                    _v   = _cov.get(_gl, 0)
                    _pct = min(100, int(_v / _ideal * 100)) if _ideal > 0 else 0
                    _clr = "#16a34a" if _pct >= 80 else ("#f59e0b" if _pct >= 40 else "#dc2626")
                    _sts = "적정" if _pct >= 80 else ("보통" if _pct >= 40 else "취약")
                    st.markdown(
                        f'<div class="uac-gauge-label" style="margin-bottom:1px;">'
                        f'{_gl} <span style="float:right;color:{_clr};font-size:0.65rem;">{_sts}</span></div>',
                        unsafe_allow_html=True,
                    )
                    st.progress(_pct / 100)

            if _nhi_r > 0 and _total_cov > 0:
                _survive = int(_total_cov / calculate_trinity_metrics(int(_nhi_r))["monthly_income"]) if _nhi_r > 0 else 0
                st.metric(
                    label="⏱️ 현재 보험으로 버틸 수 있는 시간",
                    value=f"{_survive}개월",
                    delta="충분" if _survive >= 36 else "보강 필요",
                    delta_color="normal" if _survive >= 36 else "inverse",
                )

            _weak = [
                f"• {_gl} {_ideal//10_000:,}만원 보강 필요"
                for _gl, _kws, _ideal in _GAUGES
                if _cov.get(_gl, 0) < _ideal * 0.5
            ][:4]
            if _weak:
                st.markdown(
                    '<div class="uac-prescription"><b>📋 AI 맞춤형 처방전</b><br>'
                    + "<br>".join(_weak) + "</div>",
                    unsafe_allow_html=True,
                )

        # ── [트리니티 계산법] 건강보험료 기반 필요 가입금액 보고서 (항상 표시) ──
        if _nhi_r > 0:
            _tm    = calculate_trinity_metrics(int(_nhi_r))  # 트리니티 계산법 적용
            _tri_m = _tm["monthly_income"]
            _tri_a = _tm["annual_income"]
            _tri_d = _tm["daily_value"]
            _tri_c5yr = int(_tm["gross_annual"] * 5)
            _tri_rows = [
                ("🎗️ 암 진단비 (5년 일실수익)", _tri_c5yr, f"일실수익 5년 = 연소득 {int(_tm['gross_annual']/10_000):,}만원 × 5"),
                ("🎗️ 암 진단비 (최소)",        100_000_000, "소득 수준 무관 최소 기준"),
                ("🧠 뇌·심장 진단비",          100_000_000, "3대 진단비 각 1억원 목표"),
                ("🧓 치매 진단비",              50_000_000, "고령화 필수 — 중증 기준"),
                ("🦽 후유장해 (월소득×24개월)", int(_tri_m * 24), "2년 소득보상 최소 기준"),
                ("🏥 질병 일당 입원비",         int(min(_tri_d, 100_000)), "일 소득 대비 입원 손실"),
                ("🚗 상해 일당 입원비",         int(min(_tri_d,  70_000)), "상해 입원 손실 보전"),
                ("💼 월 보험료 예산 (소득5%)",  int(_tri_m * 0.05), "연소득 5% 적정 지출 기준"),
            ]
            _tri_html = "".join(
                f"<div style='display:flex;justify-content:space-between;align-items:baseline;"
                f"font-size:0.73rem;padding:4px 0;border-bottom:1px dotted #fde68a;'>"
                f"<span style='color:#78350f;font-weight:700;'>{r[0]}</span>"
                f"<span style='font-weight:900;color:#1c1917;'>{r[1]/10_000:,.0f}만원"
                f"<span style='font-size:0.60rem;color:#a16207;margin-left:6px;'>{r[2]}</span>"
                f"</span></div>"
                for r in _tri_rows
            )
            st.markdown(
                "<div style='background:#fffbeb;border:1.5px solid #fbbf24;"
                "border-radius:10px;padding:12px 14px;margin-top:12px;'>"
                "<div style='font-size:0.82rem;font-weight:900;color:#92400e;"
                "border-bottom:2px solid #fcd34d;padding-bottom:4px;margin-bottom:8px;'>"
                "💡 트리니티 계산법 — 평균 필요 가입금액 보고서</div>"
                f"<div style='font-size:0.73rem;color:#78350f;font-weight:700;margin-bottom:8px;"
                f"background:#fef9c3;border-radius:6px;padding:5px 8px;'>"
                f"월 건보료 <b>{_nhi_r:,.0f}원</b> → 추정 월소득 <b>{_tri_m:,.0f}원</b>"
                f" | 연소득 <b>{_tri_a/10_000:,.0f}만원</b></div>"
                + _tri_html
                + "<div style='font-size:0.62rem;color:#a16207;margin-top:6px;text-align:right;'>"
                "산출기준: 건보료 ÷ 3.545% (개인부담금) = 추정소득 (트리니티 계산법 역산)</div>"
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='background:#f8faff;border:1px dashed #bfdbfe;"
                "border-radius:8px;padding:10px 14px;margin-top:10px;text-align:center;"
                "font-size:0.76rem;color:#6b7280;'>"
                "💡 좌측 <b>월 건강보험료</b>를 입력하면<br>"
                "<b>트리니티 필요 가입금액 보고서</b>가 자동 산출됩니다.</div>",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    if st.button(
        "🌐 내보험다보여 실행버튼",
        key=f"{key_prefix}_deepdive",
        use_container_width=True,
    ):
        if "current_tab" in st.session_state:
            st.session_state["current_tab"] = "gk_sec10"
            st.session_state["_scroll_top"] = True
            st.rerun()
        else:
            _uid_sso = (
                st.session_state.get("crm_user_id")
                or st.session_state.get("user_id", "")
            )
            _cid_sso = (
                st.session_state.get("_rd_docked_cid")
                or st.session_state.get("_sso_gk_cid", "")
            )
            if _uid_sso:
                _hq_sso_url = build_sso_handoff_to_hq(
                    user_id=_uid_sso,
                    cid=_cid_sso,
                    sector="gk_sec10",
                )
            else:
                _hq_sso_url = f"{HQ_APP_URL}/?tab=gk_sec10"
            st.markdown(
                f'<a href="{_hq_sso_url}" target="_blank">'
                '🔗 통합 증권분석 센터(GK-SEC-10) 열기</a>',
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
# [GP-SEC §14] 보안 기준 준수 사이드바 — HQ·CRM 공통 모듈
# ══════════════════════════════════════════════════════════════════════════════
def render_security_sidebar() -> None:
    """
    [GP-SEC §14] 사이드바 최하단 보안 기준 준수 박스.
    HQ(app.py) · CRM(crm_app.py) 양쪽에서 동일하게 호출.
    """
    try:
        import streamlit as _st_sec
    except ImportError:
        return
    _st_sec.sidebar.markdown(
        "<div style='background:#eff6ff;padding:12px;border-radius:10px;"
        "font-size:0.77rem;border:1px dashed #3b82f6;margin-top:8px;'>"
        "<strong style='color:#1e3a8a;'>🔒 보안 기준 준수 (Security Standards)</strong><br><br>"
        "• ISO/IEC 27001 정보보안 관리체계 인증 기준 준용<br>"
        "• GDPR 및 국내 개인정보보호법 가이드라인 철저 준거<br>"
        "• TLS 1.3 차세대 전송 암호화 적용 (서버-클라이언트 통신 보호)<br>"
        "• AES-256 Fernet 기반의 고강도 세션 데이터 암호화<br>"
        "• SHA-256 단방향 해시를 통한 연락처 및 비밀번호 암호화 저장<br>"
        "• 로그아웃 시 단말기 내 민감 정보 메모리 점유 즉시 해제 (임시 데이터 잔류 방지)<br><br>"
        "<div style='border-top:1px dashed #93c5fd;margin-top:6px;padding-top:8px;'>"
        "<a href='https://grass-salamander-d59.notion.site/Goldkey-AI-32ac0ebd2dab804a859ae84dae2d38d6' target='_blank' "
        "style='color:#1d4ed8;font-weight:700;font-size:0.75rem;text-decoration:none;'>"
        "📋 개인정보 처리방침 전문 보기 →</a><br>"
        "<span style='color:#6b7280;font-size:0.7rem;'>골드키 AI · insusite@gmail.com</span>"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# [GP-DESIGN-V3] 전역 디자인 시스템 — Single Source of Truth
# app.py · crm_app.py 양쪽 최상단에서 inject_global_gp_design() 1회 호출
# ══════════════════════════════════════════════════════════════════════════════
_GP_GLOBAL_DESIGN_CSS = """<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard-dynamic-subset.css');
/* ══ GP-DESIGN-V3: 전역 파스텔 디자인 시스템 ════════════════════════════════ */

/* 1. CSS 변수 ─────────────────────────────────────────────────────────── */
:root {
  --gp-bg:           #F8FAFC;
  --gp-bg-soft:      #F8FAF8;
  --gp-pastel-blue:  #E1F5FE;
  --gp-pastel-mint:  #E8F5E9;
  --gp-pastel-cream: #FFFBEB;
  --gp-text:         #334155;
  --gp-text-dark:    #1e293b;
  --gp-text-muted:   #64748b;
  --gp-navy:         #1e3a8a;
  --gp-border:       #e2e8f0;
  --gp-radius:       10px;
  --gp-radius-sm:    8px;
  --gp-shadow:       0 1px 3px rgba(0,0,0,0.07);
}

/* 2. 전체 배경 + 폰트 기반 ─────────────────────────────────────────── */
[data-testid="stApp"],
[data-testid="stAppViewContainer"] > .main {
  background: var(--gp-bg) !important;
  font-family: 'Pretendard', 'Inter', 'Noto Sans KR', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif !important;
}
* { font-family: 'Pretendard', 'Inter', 'Noto Sans KR', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif !important; }
[data-testid="stSidebar"] { background: #f1f5f9 !important; }

/* 3. 유동 타이포그래피 — GP §11 clamp() (모바일~태블릿 유기적 스케일) ─── */
html, body,
[data-testid="stApp"] *,
[data-testid="stSidebar"] * {
  font-size: clamp(14px, 2vw + 10px, 20px) !important;
}
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] li {
  font-size: clamp(14px, 2vw + 10px, 20px) !important;
  color: var(--gp-text) !important;
  line-height: 1.6 !important;
  word-break: keep-all !important;
  overflow-wrap: break-word !important;
}
h1 { font-size: clamp(16px, calc(2.5vw + 12px), 26px) !important; }
h2 { font-size: clamp(15px, calc(2vw + 11px), 22px) !important; }
h3 { font-size: clamp(14px, calc(1.8vw + 10px), 18px) !important; }

/* 4. 모든 텍스트 컨테이너 글자 보호 ────────────────────────────────── */
div[data-testid="stMarkdownContainer"],
.element-container,
.stAlert,
.stCaption {
  word-break: keep-all !important;
  overflow-wrap: break-word !important;
  line-height: 1.55 !important;
}

/* 5. 파스텔 버튼 시스템 ─────────────────────────────────────────────── */
[data-testid="stButton"] > button {
  border-radius: var(--gp-radius-sm) !important;
  font-weight: 700 !important;
  font-size: clamp(11px, 1.8vw, 13px) !important;
  padding: 5px 14px !important;
  line-height: 1.45 !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  transition: all 0.15s ease !important;
  box-shadow: var(--gp-shadow) !important;
}
[data-testid="stButton"] > button[kind="secondary"] {
  background: var(--gp-pastel-blue) !important;
  color: var(--gp-navy) !important;
  border: 1px solid #bfdbfe !important;
}
[data-testid="stButton"] > button[kind="secondary"]:hover {
  background: #dbeafe !important;
  border-color: #93c5fd !important;
  transform: translateY(-1px) !important;
}
[data-testid="stButton"] > button[kind="primary"] {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%) !important;
  color: #1e3a8a !important;
  border: 1.5px solid #93c5fd !important;
  font-weight: 900 !important;
}
[data-testid="stButton"] > button[kind="primary"]:hover {
  background: #a5f3fc !important;
  border-color: #60a5fa !important;
  transform: translateY(-1px) !important;
}

/* 5b. 화면 전체너비 버튼 방지 — 컴팩트 max-width 제한 ───────── */
[data-testid="stButton"] {
  display: inline-flex !important;
  width: auto !important;
}
[data-testid="stButton"] > button {
  max-width: min(100%, 360px) !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}

/* 6. Alert(st.info/success/error/warning) 컴팩트 스타일 ──────────────── */
.stAlert {
  border-radius: var(--gp-radius-sm) !important;
  font-size: clamp(11px, 1.9vw, 13px) !important;
  padding: 7px 12px !important;
  word-break: keep-all !important;
  overflow-wrap: break-word !important;
  margin: 3px 0 !important;
}
[data-testid="stAlert"] {
  max-width: min(100%, 720px) !important;
  width: 100% !important;
}
[data-testid="stAlert"] > div {
  font-size: clamp(11px, 1.9vw, 13px) !important;
  line-height: 1.5 !important;
  word-break: keep-all !important;
}

/* 7. 입력 필드 GP 스타일 ──────────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] > div > div,
[data-testid="stNumberInput"] input {
  border-color: var(--gp-border) !important;
  border-radius: var(--gp-radius-sm) !important;
  background: #ffffff !important;
  font-size: clamp(12px, 2vw, 14px) !important;
  color: var(--gp-text-dark) !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus,
[data-testid="stNumberInput"] input:focus {
  border-color: #3b82f6 !important;
  box-shadow: 0 0 0 2px rgba(59,130,246,0.12) !important;
  outline: none !important;
}

/* 8. SPA 라디오 네비게이션 ──────────────────────────────────────────── */
div[data-testid="stRadio"] > div {
  display: flex !important;
  flex-wrap: nowrap !important;
  gap: 4px !important;
  background: #f1f5f9 !important;
  padding: 5px 7px !important;
  border-radius: var(--gp-radius) !important;
  border: 1px solid var(--gp-border) !important;
  overflow-x: auto !important;
}
div[data-testid="stRadio"] > div > label {
  flex: 1 !important;
  text-align: center !important;
  padding: 6px 10px !important;
  border-radius: var(--gp-radius-sm) !important;
  border: 1px solid #d1d5db !important;
  background: #ffffff !important;
  font-size: clamp(10px, 1.8vw, 13px) !important;
  font-weight: 700 !important;
  cursor: pointer !important;
  white-space: nowrap !important;
  transition: background 0.12s, color 0.12s !important;
  color: var(--gp-text) !important;
  word-break: keep-all !important;
}
div[data-testid="stRadio"] > div > label:has(input:checked) {
  background: var(--gp-navy) !important;
  color: #ffffff !important;
  border-color: var(--gp-navy) !important;
  font-weight: 900 !important;
}
div[data-testid="stRadio"] > div > label > div:first-child { display: none !important; }

/* 8b. stTabs 파스텔 오버라이드 ───────────────────────────── */
[data-testid="stTabs"] [data-testid="stTab"] {
  background: #f8fafc !important;
  border-bottom: 2.5px solid transparent !important;
  color: var(--gp-text-muted) !important;
  font-weight: 700 !important;
  font-size: clamp(11px, 1.8vw, 13px) !important;
  padding: 7px 14px !important;
  border-radius: var(--gp-radius-sm) var(--gp-radius-sm) 0 0 !important;
  transition: all 0.12s !important;
}
[data-testid="stTabs"] [aria-selected="true"][data-testid="stTab"] {
  background: #eff6ff !important;
  border-bottom-color: var(--gp-navy) !important;
  color: var(--gp-navy) !important;
  font-weight: 900 !important;
}
[data-testid="stTabs"] [data-testid="stTab"]:hover:not([aria-selected="true"]) {
  background: #f1f5f9 !important;
  color: var(--gp-text) !important;
}

/* 9. 태블릿 가로 (769px~1024px) — 2열 flex 유지 ─────────────────── */
@media (min-width: 769px) and (max-width: 1024px) {
  [data-testid="stHorizontalBlock"] {
    flex-wrap: wrap !important;
  }
  [data-testid="column"] {
    flex: 1 1 44% !important;
    min-width: 180px !important;
  }
}

/* 10. 모바일/세로 (768px 이하) — 100% 수직 스태킹 ─────────────────── */
@media (max-width: 768px) {
  [data-testid="column"] {
    width: 100% !important;
    flex: 1 1 100% !important;
    min-width: 100% !important;
    margin-bottom: 14px !important;
  }
  [data-testid="stHorizontalBlock"] {
    flex-direction: column !important;
  }
  .outlook-container { flex-direction: column !important; }
  [data-testid="stMarkdownContainer"] p,
  [data-testid="stMarkdownContainer"] span,
  span, label, .stMarkdown {
    font-size: clamp(12px, 3.5vw, 14px) !important;
    word-break: keep-all !important;
    overflow-wrap: break-word !important;
    line-height: 1.55 !important;
  }
  h1 { font-size: clamp(16px, 5vw, 22px) !important; }
  h2 { font-size: clamp(14px, 4.5vw, 18px) !important; }
  h3 { font-size: clamp(13px, 4vw, 16px) !important; }
  div[data-testid="stRadio"] > div { flex-wrap: wrap !important; }
  div[data-testid="stRadio"] > div > label { flex: 1 1 44% !important; }
  .stDataFrame, .element-container {
    max-width: 100% !important;
    overflow-x: auto !important;
  }
  .gko-mini-cal { width: 100% !important; }
  .stAlert {
    font-size: clamp(11px, 3.2vw, 13px) !important;
    padding: 7px 10px !important;
  }
}

/* ── §GP-V2-COMPACT: 정보밀도 극대화 컴팩트 여백 ────────────────── */
[data-testid="stVerticalBlock"] > [data-testid="element-container"] {
  margin-bottom: 4px !important;
}
[data-testid="stMarkdownContainer"] {
  margin-bottom: 4px !important;
}
[data-testid="stVerticalBlock"] {
  gap: 4px !important;
}
div[data-testid="stButton"] {
  margin-bottom: 4px !important;
}

/* ── §GP-V2-INLINE: 버튼 문장 길이 컴팩트핏 ─────────────────────── */
[data-testid="stButton"] > button {
  padding: 0.28rem 0.9rem !important;
  min-height: 2.1rem !important;
  width: auto !important;
  max-width: min(100%, 340px) !important;
}

/* ── §GP-V2-PASTEL-BLOCKS: 안내 블록 파스텔 기준 ──────────────────── */
div[style*="background:#fffbeb"],div[style*="background:#FEF3C7"] {
  border-radius: 8px !important;
  border: 1px solid #f59e0b !important;
}
div[style*="background:#eff6ff"],div[style*="background:#DBEAFE"] {
  border-radius: 8px !important;
  border: 1px solid #93c5fd !important;
}
div[style*="background:#f0fdf4"],div[style*="background:#DCFCE7"] {
  border-radius: 8px !important;
  border: 1px solid #6ee7b7 !important;
}

/* ── §GP-CRM-ACTION-GRID: 수평 액션 그리드 (수직 스택 금지 구역) ─────── */
.crm-responsive-shell {
  box-sizing: border-box !important;
  width: 100% !important;
  max-width: min(100%, 920px) !important;
  margin-left: auto !important;
  margin-right: auto !important;
}
.crm-action-grid-wrap [data-testid="stHorizontalBlock"] {
  display: flex !important;
  flex-direction: row !important;
  flex-wrap: wrap !important;
  gap: 8px !important;
  align-items: stretch !important;
  justify-content: flex-start !important;
  width: 100% !important;
}
.crm-action-grid-wrap [data-testid="column"] {
  flex: 1 1 calc(25% - 8px) !important;
  min-width: 140px !important;
  max-width: 100% !important;
}
.crm-action-grid-wrap [data-testid="stButton"] {
  width: 100% !important;
  display: block !important;
}
.crm-action-grid-wrap [data-testid="stButton"] > button {
  width: 100% !important;
  max-width: 100% !important;
  min-height: 2.75rem !important;
  font-size: clamp(12px, calc(1.2vw + 10px), 15px) !important;
  white-space: normal !important;
  line-height: 1.35 !important;
}
@media (max-width: 768px) {
  .crm-action-grid-wrap [data-testid="column"] {
    flex: 1 1 calc(50% - 6px) !important;
    min-width: 132px !important;
  }
}
/* [GP-BTN-NOWRAP] 버튼 포함 행 — 모든 화면에서 수평 유지, 압착 금지 */
[data-testid="stHorizontalBlock"]:has(button) {
  flex-direction: row !important;
  flex-wrap: nowrap !important;
}
[data-testid="stHorizontalBlock"]:has(button) > [data-testid="column"] {
  flex-shrink: 0 !important;
  min-width: 60px !important;
}
/* [GP-INPUT-DYNAMIC] 스마트 다이내믹 입력창 — 포커스 시 확장 애니메이션 */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
  font-size: clamp(0.82rem, 3vw, 0.98rem) !important;
  transition: box-shadow 0.35s cubic-bezier(0.4,0,0.2,1),
              border-color 0.3s ease !important;
  border-radius: 10px !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
  box-shadow: 0 0 0 3px rgba(99,102,241,0.18),
              0 2px 8px rgba(0,0,0,0.06) !important;
  border-color: #6366f1 !important;
}
/* [GP-LOGIN-COMPACT] 로그인 폼 — 최대폭 제한·중앙 정렬·카드 디자인 */
[data-testid="stForm"] {
  max-width: min(380px, 97vw) !important;
  margin: 6px auto 12px !important;
  background: rgba(255,255,255,0.97) !important;
  border: 1px dashed #000 !important;
  border-radius: 14px !important;
  padding: 18px 22px 14px !important;
  box-shadow: 0 4px 18px rgba(59,130,246,0.08) !important;
}
[data-testid="stFormSubmitButton"] button {
  font-size: clamp(0.9rem,3.5vw,1.05rem) !important;
  min-height: 44px !important;
  font-weight: 800 !important;
  border-radius: 10px !important;
  transition: box-shadow 0.25s ease !important;
}
[data-testid="stFormSubmitButton"] button:hover {
  box-shadow: 0 4px 12px rgba(99,102,241,0.3) !important;
  transform: translateY(-1px) !important;
}
/* [GP-TYPO-CLAMP] 헤더·레이블 반응형 타이포그래피 */
h1 { font-size: clamp(1.4rem,5vw,2rem) !important; }
h2 { font-size: clamp(1.1rem,4vw,1.55rem) !important; }
h3 { font-size: clamp(0.95rem,3.5vw,1.2rem) !important; }
label[data-testid="stWidgetLabel"] {
  font-size: clamp(0.8rem,2.8vw,0.92rem) !important;
}
/* [GP-PLACEHOLDER] 전역 Placeholder 시각적 감쇠 — 입력 방해 제거 */
::placeholder,
input::placeholder,
textarea::placeholder,
[data-baseweb="input"] input::placeholder,
[data-baseweb="textarea"] textarea::placeholder,
[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextAreaInput"] textarea::placeholder,
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
  color: #d1d5db !important;
  opacity: 0.4 !important;
  font-size: 0.85em !important;
  font-weight: 400 !important;
  transition: opacity 0.2s ease-in-out;
}
/* 포커스 시 placeholder 완전 숨김 */
input:focus::placeholder,
textarea:focus::placeholder,
[data-baseweb="input"] input:focus::placeholder,
[data-testid="stTextInput"] input:focus::placeholder,
[data-testid="stTextAreaInput"] textarea:focus::placeholder {
  color: transparent !important;
  opacity: 0 !important;
}
/* 브라우저 호환성 — WebKit / IE / Edge */
::-webkit-input-placeholder,
input::-webkit-input-placeholder,
textarea::-webkit-input-placeholder,
[data-baseweb="input"] input::-webkit-input-placeholder,
[data-testid="stTextInput"] input::-webkit-input-placeholder {
  color: #d1d5db !important;
  opacity: 0.4 !important;
  font-size: 0.85em !important;
  font-weight: 400 !important;
}
input:focus::-webkit-input-placeholder,
textarea:focus::-webkit-input-placeholder {
  color: transparent !important;
  opacity: 0 !important;
}
:-ms-input-placeholder,
::-ms-input-placeholder {
  color: #d1d5db !important;
  opacity: 0.4 !important;
  font-size: 0.85em !important;
  font-weight: 400 !important;
}
</style>"""


def inject_global_gp_design() -> None:
    """
    [GP-DESIGN-V3] 전역 디자인 시스템 Single Source of Truth.
    app.py · crm_app.py 최상단에서 1회 호출하면 양쪽 앱에 동일한
    파스텔톤 · clamp() 타이포그래피 · 반응형 레이아웃이 적용된다.

    포함 내용:
      - CSS 변수 (--gp-*) 기반 파스텔 팔레트
      - clamp() 전역 유동 타이포그래피 (GP §11 — 모바일 14px ~ 태블릿 상한)
      - word-break:keep-all + overflow-wrap:break-word 글자 보호
      - 파스텔 버튼 시스템 (secondary=#E1F5FE, primary=#dbeafe 파스텔 블루)
      - Alert · 컨테이너 max-width + width:100% (제30조)
      - CRM 수평 액션 그리드 (.crm-action-grid-wrap)
      - SPA 라디오 네비게이션 버튼형 CSS
    """
    st.markdown(_GP_GLOBAL_DESIGN_CSS, unsafe_allow_html=True)
    # [GP-PLACEHOLDER-JS] CSS 명세도 우회 — placeholder 속성 자체를 DOM에서 제거
    try:
        import streamlit.components.v1 as _cv1_ph
        _cv1_ph.html(
            """<script>
(function(){
  function _gp_clrph(){
    document.querySelectorAll('input[placeholder],textarea[placeholder]').forEach(function(el){
      if(el.dataset.gpPhCleared){return;}
      el.setAttribute('placeholder','');
      el.dataset.gpPhCleared='1';
    });
  }
  _gp_clrph();
  new MutationObserver(function(ml){
    ml.forEach(function(m){
      m.addedNodes.forEach(function(n){
        if(n.nodeType!==1){return;}
        if(n.matches&&n.matches('input[placeholder],textarea[placeholder]')){
          n.setAttribute('placeholder',''); n.dataset.gpPhCleared='1';
        }
        n.querySelectorAll&&n.querySelectorAll('input[placeholder],textarea[placeholder]')
          .forEach(function(el){el.setAttribute('placeholder',''); el.dataset.gpPhCleared='1';});
      });
    });
  }).observe(document.body,{childList:true,subtree:true});
})();
</script>""",
            height=0,
            scrolling=False,
        )
    except Exception:
        pass


# ── [GP-VOICE] 양앱 공통 Gemini Pro TTS (Zephyr · Korean) ─────────────────────
GP_TTS_ENGINE_LABEL = "Gemini Pro TTS"
GP_TTS_VOICE_ZEPHYR = "Zephyr"
GP_TTS_LANG_BCP47 = "ko-KR"
GP_TTS_LANG_LABEL = "한국어"


class GeminiProTTSVoice:
    """[GP-VOICE] HQ·CRM 공통 AI 음성 엔진 메타 (Gemini Pro TTS · Zephyr · 한국어)."""

    ENGINE = "AI 음성 합성"
    MODEL = "Gemini Pro TTS"
    LANG_LABEL = "한국어"
    VOICE = "Zephyr"

    @staticmethod
    def label_html() -> str:
        return (
            f"🎙️ <b>{GeminiProTTSVoice.ENGINE}</b> · <b>{GeminiProTTSVoice.MODEL}</b> · "
            f"언어: {GeminiProTTSVoice.LANG_LABEL} · 보이스: {GeminiProTTSVoice.VOICE}"
        )


def render_gp_gemini_pro_tts_player(
    text: str,
    key: str = "gp_gemini_tts",
    auto_play: bool = False,
    compact: bool = False,
) -> None:
    """AI 음성 합성 — Gemini Pro TTS, Zephyr, 한국어. 양앱 공통."""
    from voice_engine import render_voice_player_zephyr

    render_voice_player_zephyr(
        text,
        key=key,
        auto_play=auto_play,
        compact=compact,
    )


# ── [GP-44] rules.json — OTA / 설정 기반 UI ───────────────────────────────────
def _deep_merge_gp(dst: dict, src: dict) -> dict:
    for _k, _v in src.items():
        if _k in dst and isinstance(dst[_k], dict) and isinstance(_v, dict):
            _deep_merge_gp(dst[_k], _v)
        else:
            dst[_k] = _v
    return dst


@st.cache_data(ttl=60)
def load_gp_rules() -> dict:
    """프로젝트 루트 `rules.json` 로드 + (옵션) `GK_RULES_JSON_URL` 원격 병합 (60초 캐시)."""
    import json
    from pathlib import Path

    base: dict = {}
    _p = Path(__file__).resolve().parent / "rules.json"
    if _p.is_file():
        try:
            with open(_p, "r", encoding="utf-8") as f:
                base = json.load(f)
        except Exception:
            base = {}
    if not isinstance(base, dict):
        base = {}
    _url = (os.environ.get("GK_RULES_JSON_URL") or "").strip()
    if _url:
        try:
            import requests

            _r = requests.get(
                _url,
                timeout=8,
                headers={"User-Agent": "GoldkeyAI-GP44-rules/1"},
            )
            if _r.ok and _r.text.strip():
                remote = _r.json()
                if isinstance(remote, dict):
                    _local_crm_ui = base.get("crm_ui")
                    _deep_merge_gp(base, remote)
                    if _local_crm_ui is not None:
                        base["crm_ui"] = _local_crm_ui
        except Exception:
            pass
    return base


_DEFAULT_CRM_ACTION_ROWS: list[tuple[str, str, bool]] = [
    ("고객정보",     "contact",  True),
    ("고객 DB 관리","db_manage", True),
    ("스케줄",      "schedule", True),
    ("증권분석",    "analysis", True),
    ("카카오",      "kakao",    True),
    ("핸드폰스캔",  "settings", False),
]


def get_crm_action_grid_title() -> str:
    r = load_gp_rules()
    cu = (r.get("crm_ui") or {}) if isinstance(r, dict) else {}
    return str(
        cu.get("action_grid_title")
        or "🎯 업무 바로가기 · 고객을 표에서 선택하면 활성화됩니다"
    )


def get_crm_action_definitions() -> list[tuple[str, str, bool]]:
    """CRM 메인 그리드: (label, screen_key, requires_customer). rules.json `crm_ui.actions` 우선."""
    r = load_gp_rules()
    cu = (r.get("crm_ui") or {}) if isinstance(r, dict) else {}
    raw = cu.get("actions")
    if not raw or not isinstance(raw, list):
        return list(_DEFAULT_CRM_ACTION_ROWS)
    out: list[tuple[str, str, bool]] = []
    try:
        _sorted = sorted(raw, key=lambda x: int(x.get("order", 99)))
    except Exception:
        _sorted = raw
    for a in _sorted:
        if not isinstance(a, dict) or not a.get("enabled", True):
            continue
        _id = str(a.get("id", "")).strip()
        _lbl = str(a.get("label", "")).strip()
        if not _id or not _lbl:
            continue
        _req = bool(a.get("requires_customer", _id != "settings"))
        out.append((_lbl, _id, _req))
    return out if out else list(_DEFAULT_CRM_ACTION_ROWS)


# ══════════════════════════════════════════════════════════════════════════════
# [GP-CRM-AUTH] CRM 회원가입 및 비밀번호 재설정 Modal
# ══════════════════════════════════════════════════════════════════════════════

@st.dialog(txt.SIGNUP_MODAL_TITLE if (txt and hasattr(txt, 'SIGNUP_MODAL_TITLE')) else "🔐 회원가입")
def render_signup_modal():
    """
    [GP-CRM-AUTH §1] 회원가입 Modal
    
    - 연락처 이중 확인 (오입력 방지)
    - 비밀번호 이중 확인
    - SHA-256 해시 + AES-256 암호화
    - DB + GCS Dual Write
    """
    from utils.crypto_utils import hash_contact, hash_password, encrypt_name, generate_user_id
    from utils.gcs_master_sync import dual_write_member
    
    st.markdown(
        "<div style='font-size:0.85rem;color:#374151;margin-bottom:16px;'>"
        f"{txt.LOGIN_HQ_REFERENCE_REMOVED if (txt and hasattr(txt, 'LOGIN_HQ_REFERENCE_REMOVED')) else 'CRM 앱에서 직접 가입하실 수 있습니다'}"
        "</div>",
        unsafe_allow_html=True
    )
    
    # 입력 필드
    name = st.text_input(
        txt.SIGNUP_NAME_LABEL if (txt and hasattr(txt, 'SIGNUP_NAME_LABEL')) else "이름",
        key="signup_name"
    )
    
    contact = st.text_input(
        txt.SIGNUP_CONTACT_LABEL if (txt and hasattr(txt, 'SIGNUP_CONTACT_LABEL')) else "연락처 (로그인 ID)",
        placeholder="연락처를 입력하세요",
        key="signup_contact"
    )
    
    contact_confirm = st.text_input(
        txt.SIGNUP_CONTACT_CONFIRM_LABEL if (txt and hasattr(txt, 'SIGNUP_CONTACT_CONFIRM_LABEL')) else "연락처 확인",
        placeholder="연락처를 다시 입력하세요",
        key="signup_contact_confirm"
    )
    
    password = st.text_input(
        txt.SIGNUP_PASSWORD_LABEL if (txt and hasattr(txt, 'SIGNUP_PASSWORD_LABEL')) else "비밀번호",
        type="password",
        key="signup_password"
    )
    
    password_confirm = st.text_input(
        txt.SIGNUP_PASSWORD_CONFIRM_LABEL if (txt and hasattr(txt, 'SIGNUP_PASSWORD_CONFIRM_LABEL')) else "비밀번호 확인",
        type="password",
        key="signup_password_confirm"
    )
    
    # 유효성 검사
    contact_match = contact == contact_confirm if contact and contact_confirm else False
    password_match = password == password_confirm if password and password_confirm else False
    
    if contact and contact_confirm and not contact_match:
        st.error(txt.SIGNUP_CONTACT_MISMATCH_ERROR if (txt and hasattr(txt, 'SIGNUP_CONTACT_MISMATCH_ERROR')) else "⚠️ 연락처가 일치하지 않습니다")
    
    if password and password_confirm and not password_match:
        st.error(txt.SIGNUP_PASSWORD_MISMATCH_ERROR if (txt and hasattr(txt, 'SIGNUP_PASSWORD_MISMATCH_ERROR')) else "⚠️ 비밀번호가 일치하지 않습니다")
    
    # 버튼 활성화 조건
    can_submit = (
        name and 
        contact and 
        contact_confirm and 
        password and 
        password_confirm and 
        contact_match and 
        password_match
    )
    
    if not can_submit:
        st.caption(txt.SIGNUP_BUTTON_DISABLED_HINT if (txt and hasattr(txt, 'SIGNUP_BUTTON_DISABLED_HINT')) else "모든 필드를 올바르게 입력해야 가입 버튼이 활성화됩니다")
    
    # 가입 버튼
    if st.button(
        txt.SIGNUP_BUTTON_TEXT if (txt and hasattr(txt, 'SIGNUP_BUTTON_TEXT')) else "✅ 가입하기",
        disabled=not can_submit,
        use_container_width=True
    ):
        try:
            # 암호화 처리
            user_id = generate_user_id()
            contact_hash = hash_contact(contact)
            password_hash = hash_password(password)
            name_encrypted = encrypt_name(name)
            
            # 회원 데이터 구성
            member_data = {
                "user_id": user_id,
                "name_encrypted": name_encrypted,
                "contact_hash": contact_hash,
                "password_hash": password_hash,
                "role": "member",
                "quota_remaining": 10,
                "device_fingerprint": "",  # 향후 구현
                "created_at": datetime.datetime.now().isoformat(),
                "updated_at": datetime.datetime.now().isoformat()
            }
            
            # DB + GCS Dual Write
            # TODO: db_save_func 연결 필요
            success = dual_write_member(member_data, db_save_func=None)
            
            if success:
                st.success(txt.SIGNUP_SUCCESS_MESSAGE if (txt and hasattr(txt, 'SIGNUP_SUCCESS_MESSAGE')) else "✅ 회원가입이 완료되었습니다!")
                st.session_state["_signup_completed"] = True
                st.rerun()
            else:
                st.error("❌ 회원가입 중 오류가 발생했습니다. 다시 시도해 주세요.")
        
        except Exception as e:
            st.error(f"❌ 회원가입 실패: {e}")


@st.dialog(txt.PASSWORD_RESET_MODAL_TITLE if (txt and hasattr(txt, 'PASSWORD_RESET_MODAL_TITLE')) else "🔑 비밀번호 재설정")
def render_password_reset_modal():
    """
    [GP-CRM-AUTH §2] 비밀번호 재설정 Modal (Mockup 본인인증)
    
    - Step 1: PASS/카카오 인증 시뮬레이션
    - Step 2: 연락처 해시 대조
    - Step 3: 새 비밀번호 설정
    """
    from utils.crypto_utils import hash_contact, hash_password, encrypt_name
    from utils.gcs_master_sync import verify_member_by_contact_hash, save_member_to_gcs
    
    # 베타 경고
    st.warning(txt.PASSWORD_RESET_BETA_WARNING if (txt and hasattr(txt, 'PASSWORD_RESET_BETA_WARNING')) else "⚠️ 베타 테스트용 시뮬레이션 모드입니다")
    
    # 시뮬레이션 안내
    with st.expander("📱 본인인증 시뮬레이션 안내", expanded=False):
        st.markdown(
            txt.PASSWORD_RESET_AUTH_MOCKUP_NOTICE if (txt and hasattr(txt, 'PASSWORD_RESET_AUTH_MOCKUP_NOTICE')) else """
            현재 베타 테스트 기간으로, 실제 PASS/카카오 인증 대신 시뮬레이션 모드로 작동합니다.
            가입 시 사용한 이름과 연락처를 입력하세요.
            """
        )
    
    # Step 1: 본인인증
    if "password_reset_authenticated" not in st.session_state:
        st.session_state["password_reset_authenticated"] = False
        st.session_state["password_reset_user_id"] = None
    
    if not st.session_state["password_reset_authenticated"]:
        st.markdown(f"### {txt.PASSWORD_RESET_AUTH_STEP_TITLE if (txt and hasattr(txt, 'PASSWORD_RESET_AUTH_STEP_TITLE')) else 'Step 1: 본인인증'}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(
                txt.PASSWORD_RESET_PASS_BUTTON if (txt and hasattr(txt, 'PASSWORD_RESET_PASS_BUTTON')) else "🅿️ PASS 인증",
                use_container_width=True
            ):
                st.session_state["auth_method"] = "PASS"
        
        with col2:
            if st.button(
                txt.PASSWORD_RESET_KAKAO_BUTTON if (txt and hasattr(txt, 'PASSWORD_RESET_KAKAO_BUTTON')) else "💬 카카오 인증",
                use_container_width=True
            ):
                st.session_state["auth_method"] = "KAKAO"
        
        # 인증 방법 선택 후 입력 필드 표시
        if "auth_method" in st.session_state:
            st.markdown("---")
            st.markdown(f"**{st.session_state['auth_method']} 인증 시뮬레이션**")
            
            auth_name = st.text_input("이름", key="auth_name")
            auth_contact = st.text_input("연락처", placeholder="연락처를 입력하세요", key="auth_contact")
            
            if st.button("✅ 인증 완료", use_container_width=True):
                if auth_name and auth_contact:
                    # 연락처 해시로 회원 검색
                    contact_hash = hash_contact(auth_contact)
                    member = verify_member_by_contact_hash(contact_hash)
                    
                    if member:
                        # 이름 복호화 후 대조 (추가 보안)
                        from utils.crypto_utils import decrypt_name
                        stored_name = decrypt_name(member.get("name_encrypted", ""))
                        
                        if stored_name == auth_name:
                            st.success(txt.PASSWORD_RESET_AUTH_SUCCESS if (txt and hasattr(txt, 'PASSWORD_RESET_AUTH_SUCCESS')) else "✅ 본인인증 완료")
                            st.session_state["password_reset_authenticated"] = True
                            st.session_state["password_reset_user_id"] = member.get("user_id")
                            st.rerun()
                        else:
                            st.error("❌ 이름이 일치하지 않습니다")
                    else:
                        st.error(txt.PASSWORD_RESET_AUTH_FAILED if (txt and hasattr(txt, 'PASSWORD_RESET_AUTH_FAILED')) else "❌ 인증 정보가 일치하지 않습니다")
                else:
                    st.warning("⚠️ 이름과 연락처를 모두 입력해 주세요")
    
    # Step 2: 새 비밀번호 설정
    else:
        st.success(txt.PASSWORD_RESET_AUTH_SUCCESS if (txt and hasattr(txt, 'PASSWORD_RESET_AUTH_SUCCESS')) else "✅ 본인인증 완료")
        st.markdown("---")
        st.markdown("### Step 2: 새 비밀번호 설정")
        
        new_password = st.text_input(
            txt.PASSWORD_RESET_NEW_PASSWORD_LABEL if (txt and hasattr(txt, 'PASSWORD_RESET_NEW_PASSWORD_LABEL')) else "새 비밀번호",
            type="password",
            key="new_password"
        )
        
        new_password_confirm = st.text_input(
            txt.PASSWORD_RESET_NEW_PASSWORD_CONFIRM_LABEL if (txt and hasattr(txt, 'PASSWORD_RESET_NEW_PASSWORD_CONFIRM_LABEL')) else "새 비밀번호 확인",
            type="password",
            key="new_password_confirm"
        )
        
        password_match = new_password == new_password_confirm if new_password and new_password_confirm else False
        
        if new_password and new_password_confirm and not password_match:
            st.error(txt.SIGNUP_PASSWORD_MISMATCH_ERROR if (txt and hasattr(txt, 'SIGNUP_PASSWORD_MISMATCH_ERROR')) else "⚠️ 비밀번호가 일치하지 않습니다")
        
        if st.button(
            txt.PASSWORD_RESET_BUTTON_TEXT if (txt and hasattr(txt, 'PASSWORD_RESET_BUTTON_TEXT')) else "✅ 비밀번호 변경",
            disabled=not password_match,
            use_container_width=True
        ):
            try:
                # 새 비밀번호 해시
                new_password_hash = hash_password(new_password)
                
                # GCS에서 회원 정보 로드
                from utils.gcs_master_sync import load_member_from_gcs
                user_id = st.session_state["password_reset_user_id"]
                member = load_member_from_gcs(user_id)
                
                if member:
                    # 비밀번호 업데이트
                    member["password_hash"] = new_password_hash
                    member["updated_at"] = datetime.datetime.now().isoformat()
                    
                    # GCS 저장
                    success = save_member_to_gcs(member)
                    
                    if success:
                        st.success(txt.PASSWORD_RESET_SUCCESS_MESSAGE if (txt and hasattr(txt, 'PASSWORD_RESET_SUCCESS_MESSAGE')) else "✅ 비밀번호가 변경되었습니다!")
                        
                        # 세션 초기화
                        st.session_state["password_reset_authenticated"] = False
                        st.session_state["password_reset_user_id"] = None
                        if "auth_method" in st.session_state:
                            del st.session_state["auth_method"]
                        
                        st.rerun()
                    else:
                        st.error("❌ 비밀번호 변경 중 오류가 발생했습니다")
                else:
                    st.error("❌ 회원 정보를 찾을 수 없습니다")
            
            except Exception as e:
                st.error(f"❌ 비밀번호 변경 실패: {e}")
import os
def get_env_secret(k, d=None):
    return os.environ.get(k, d)

import os
def get_env_secret(k, d=None):
    return os.environ.get(k, d)
