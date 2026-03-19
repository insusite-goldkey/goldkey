# trinity_engine.py — Goldkey AI Masters 2026
"""
[트리니티 통합 엔진] HQ(app.py) × CRM(crm_app.py) 공유 데이터 레이어
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

exports:
  get_trinity_db()          — Supabase 공유 싱글톤 (HQ/CRM 공통)
  hash_contact(contact)     — SHA-256 단방향 해시  [GP-SEC §1]
  run_trinity_analysis()    — 건보료 역산 × KB표준 트리니티 분석 코어
  save_analysis_to_db()     — analysis_reports Upsert  (CRM→DB Push)
  get_analysis_from_db()    — 최신 분석 결과 Pull       (HQ 도킹 시)
  render_trinity_report()          — 통합 리포트 UI + 카카오톡 전송 버튼
  render_trinity_pull_box()         — HQ 도킹 스테이션 전용 Pull UI 위젯
  execute_integrated_analysis()     — 파서↔엔진 완전 통합 원-스텝 파이프라인

보안 원칙 (GP-SEC §1):
  - 연락처 원문은 절대 DB·로그·세션에 저장 금지
  - DB 조회 키 = SHA-256(clean_contact)  — 복호화 불가
  - 복호화 필요 PII는 shared_components.encrypt_pii() 사용
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
from __future__ import annotations

import hashlib
import json
import os
import urllib.parse
from datetime import datetime
from typing import Optional

import streamlit as st


# ══════════════════════════════════════════════════════════════════════════════
# [0] 환경변수 헬퍼 — secrets.toml 없어도 os.environ 폴백 (Cloud Run 대응)
# ══════════════════════════════════════════════════════════════════════════════
def _env(key: str, default: str = "") -> str:
    try:
        return st.secrets.get(key, os.environ.get(key, default))
    except Exception:
        return os.environ.get(key, default)


# ══════════════════════════════════════════════════════════════════════════════
# [1] Supabase 공유 DB 싱글톤 — HQ · CRM 공통 단일 인스턴스
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner=False)
def get_trinity_db():
    """
    Supabase 중앙 DB 연결 (CRM · HQ 공통).
    SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY 환경변수 또는 secrets.toml 자동 감지.
    """
    try:
        from supabase import create_client
        url = (_env("SUPABASE_URL") or "").strip()
        key = (_env("SUPABASE_SERVICE_ROLE_KEY") or _env("SUPABASE_KEY") or "").strip()
        if not url or not key:
            return None
        return create_client(url, key)
    except Exception as _e:
        try:
            st.warning(f"⚠️ trinity_engine: Supabase 연결 실패 — {_e}")
        except Exception:
            pass
        return None


# ══════════════════════════════════════════════════════════════════════════════
# [2] PII 보호 헬퍼 — GP-SEC §1 준수
# ══════════════════════════════════════════════════════════════════════════════
def hash_contact(contact: str) -> str:
    """
    [GP-SEC §1] 연락처 → SHA-256 단방향 해시.
    analysis_reports 테이블의 조회 키(contact_hash)로 사용.
    원문 복원 불가 — 운영자·관리자 포함 누구도 열람 불가.
    """
    clean = "".join(filter(str.isdigit, str(contact or "")))
    if not clean:
        return ""
    return hashlib.sha256(clean.encode()).hexdigest()


# ══════════════════════════════════════════════════════════════════════════════
# [2-B] 소득 역산 초정밀 엔진 — 8단계 세율 + 4대보험 공제 파이프라인
# ══════════════════════════════════════════════════════════════════════════════

# 2024년 기준 소득세 누진세율표 (과세표준 상한, 세율, 누진공제액)
_TAX_BRACKETS: list = [
    (14_000_000,    0.06,         0),
    (50_000_000,    0.15,   1_260_000),
    (88_000_000,    0.24,   5_760_000),
    (150_000_000,   0.35,  15_440_000),
    (300_000_000,   0.38,  19_940_000),
    (500_000_000,   0.40,  25_940_000),
    (1_000_000_000, 0.42,  35_940_000),
    (float("inf"),  0.45,  65_940_000),
]

_NHIS_EMP_RATE = 0.03545   # 건강보험료 근로자 부담율 (2026 기준)
_LTCI_EMP_RATE = 0.004591  # 장기요양보험료 근로자 부담율
_NPS_EMP_RATE  = 0.045     # 국민연금 근로자 부담율
_EI_EMP_RATE   = 0.009     # 고용보험 근로자 부담율


def get_tax_rate(gross_annual: float) -> float:
    """
    [2026 트리니티 표준] 명목 연봉 구간 기반 한계세율 반환.
    소득 구간에 따라 8단계 과세표준 표 자동 매핑.

    사용 예:
        rate  = get_tax_rate(gross_annual)          # 구간별 소득세율
        m_req = gross_annual * (1 - (rate + 0.045)) / 12  # 가처분 월소득
    """
    for ceiling, rate, _ in _TAX_BRACKETS:
        if gross_annual <= ceiling:
            return rate
    return 0.45


def compute_income_tax(gross_annual: float) -> float:
    """8단계 누진세율표 종합소득세 산출 (근로소득공제 미적용 건보료 역산 전용)."""
    for ceiling, rate, deduction in _TAX_BRACKETS:
        if gross_annual <= ceiling:
            return max(0.0, gross_annual * rate - deduction)
    return max(0.0, gross_annual * 0.45 - 65_940_000)


def compute_net_income(gross_annual: float) -> tuple:
    """
    8단계 세율 + 4대보험 → 가처분 연소득(I_net) 산출.

    공제 파이프라인:
      ① 종합소득세  (8단계 누진세율)
      ② 지방소득세  = 소득세 × 10%
      ③ 건강보험료  = 연소득 × 3.545%
      ④ 장기요양    = 연소득 × 0.4591%
      ⑤ 국민연금    = 연소득 × 4.5%
      ⑥ 고용보험    = 연소득 × 0.9%

    Returns:
        (net_annual: float, deduction_rate: float, breakdown: dict)
    """
    _it   = compute_income_tax(gross_annual)
    _lt   = _it * 0.1
    _nhis = gross_annual * _NHIS_EMP_RATE
    _ltci = gross_annual * _LTCI_EMP_RATE
    _nps  = gross_annual * _NPS_EMP_RATE
    _ei   = gross_annual * _EI_EMP_RATE
    _ded  = _it + _lt + _nhis + _ltci + _nps + _ei
    _net  = max(0.0, gross_annual - _ded)
    _rate = _ded / gross_annual if gross_annual > 0 else 0.0
    return _net, _rate, {
        "종합소득세":   _it,
        "지방소득세":   _lt,
        "건강보험료":   _nhis,
        "장기요양":     _ltci,
        "국민연금":     _nps,
        "고용보험":     _ei,
        "총공제액":     _ded,
        "합산공제율":   _rate,
        "가처분연소득": _net,
    }


def compute_coverage_needs(m_req: float) -> dict:
    """
    필요 월소득(M_req = I_net / 12) 기반 보장 자산 자동 산출.

    Args:
        m_req: 가처분 연소득 / 12 (순 월 필요 소득)

    Returns:
        {
          "암진단비": {"2년(기본치료)": float, "3년(집중재활)": float, "5년(완치판정)": float},
          "후유장해": {"12개월": float, "18개월": float, "24개월": float},
          "입원일당": float,
        }
    """
    return {
        "암진단비": {
            "2년(기본치료)": m_req * 24,
            "3년(집중재활)": m_req * 36,
            "5년(완치판정)": m_req * 60,
        },
        "후유장해": {
            "12개월": m_req * 12,
            "18개월": m_req * 18,
            "24개월": m_req * 24,
        },
        "입원일당": m_req / 30,
    }


# ══════════════════════════════════════════════════════════════════════════════
# [3] 트리니티 분석 코어 — 건보료 역산 × KB 표준 교차 분석
# ══════════════════════════════════════════════════════════════════════════════
_TRINITY_STANDARD: dict = {
    "암진단비":      {"표준_KB": 50_000_000,  "치료기간": "최소 2년",          "income_mult": 24},
    "뇌졸중진단비":  {"표준_KB": 30_000_000,  "치료기간": "1년 6개월 ~ 2년",   "income_mult": 24},
    "심근경색진단비":{"표준_KB": 30_000_000,  "치료기간": "1년 ~ 1년 6개월",   "income_mult": 18},
    "상해후유장해":  {"표준_KB": 100_000_000, "치료기간": "영구 장해 보정",     "income_mult": 0},
    "실손의료비":    {"표준_KB": 0,            "치료기간": "실비 청구 필수",     "income_mult": 0},
    "수술비":        {"표준_KB": 3_000_000,   "치료기간": "1회 수술 기준",       "income_mult": 3},
    "입원일당":      {"표준_KB": 50_000,      "치료기간": "일당 기준",           "income_mult": 0},
}


def run_trinity_analysis(
    current_coverage: dict,
    nhi_premium: float,
    kb7_result: Optional[list] = None,
) -> tuple:
    """
    트리니티 초정밀 분석 = 건보료 역산 × 8단계 세율 × KB 표준 교차 분석.

    ┌─ Step 1: 건보료 역산 → 명목 연봉 (I_gross)
    │   I_gross = (nhi_premium × 2 / 0.0719) × 12
    │
    ├─ Step 2: 8단계 세율 + 4대보험 공제 → 가처분 연소득 (I_net)
    │   I_net = I_gross × (1 - 합산공제율)
    │
    ├─ Step 3: 필요 월소득 (M_req) = I_net / 12
    │
    └─ Step 4: 보장 자산 필요 자금 산출 + KB 표준 교차 Gap 분석

    Args:
        current_coverage: {담보명: 가입금액(원)} dict
        nhi_premium:      월 건강보험료(원) — 본인 부담분
        kb7_result:       HQ _kb_standard_analysis() 결과 list (있으면 메타 병합)

    Returns:
        (analysis_data dict, m_req float)
        ※ m_req = 가처분 연소득 / 12 (순 필요 월소득)
    """
    # ── Step 1: 건보료 역산 → 명목 연봉 ──────────────────────────────────────
    monthly_gross = float(nhi_premium) * 2 / 0.0719
    gross_annual  = monthly_gross * 12

    # ── Step 2: 8단계 세율 + 4대보험 → 가처분 연소득 ─────────────────────────
    net_annual, ded_rate, breakdown = compute_net_income(gross_annual)

    # ── Step 3: 필요 월소득 (M_req) ────────────────────────────────────────────
    m_req = net_annual / 12

    # ── Step 4-A: 보장 자산 필요 자금 산출 ────────────────────────────────────
    coverage_needs = compute_coverage_needs(m_req)

    analysis_data: dict = {
        "_income_meta": {
            "gross_monthly":  monthly_gross,
            "gross_annual":   gross_annual,
            "net_annual":     net_annual,
            "m_req":          m_req,
            "deduction_rate": ded_rate,
            "breakdown":      breakdown,
            "coverage_needs": coverage_needs,
        }
    }

    # ── Step 4-B: KB 표준 Gap 분석 ────────────────────────────────────────────
    for item, cfg in _TRINITY_STANDARD.items():
        current_val = float(current_coverage.get(item, 0) or 0)

        if cfg["income_mult"] > 0:
            adequate = m_req * cfg["income_mult"]
        else:
            adequate = float(cfg["표준_KB"]) if cfg["표준_KB"] > 0 else 0.0

        gap = max(0.0, adequate - current_val)

        if gap == 0:
            status = "충족"
        elif adequate > 0 and gap > adequate * 0.5:
            status = "위험"
        else:
            status = "부족"

        analysis_data[item] = {
            "현재가입":  current_val,
            "표준_KB":   float(cfg["표준_KB"]),
            "적정_역산": adequate,
            "부족분":    gap,
            "치료기간":  cfg["치료기간"],
            "충족여부":  status,
        }

    if kb7_result:
        analysis_data["_kb7_meta"] = [
            {
                "id":    r.get("id"),
                "label": r.get("label"),
                "badge": r.get("badge"),
                "score": r.get("score"),
            }
            for r in kb7_result
        ]

    return analysis_data, m_req


# ══════════════════════════════════════════════════════════════════════════════
# [4] DB 저장 — CRM/HQ 현장 분석 결과 → 중앙 DB Push  [GP-SEC §1]
# ══════════════════════════════════════════════════════════════════════════════
def save_analysis_to_db(
    client_contact: str,
    analysis_data: dict,
    estimated_income: float,
    agent_id: str = "",
    kb7_score: int = 0,
    report_text: str = "",
    person_id: str = "",
) -> bool:
    """
    분석 결과를 중앙 Supabase DB에 Upsert.
    contact_hash + agent_id 복합 UNIQUE → 동일 고객/설계사 조합은 최신으로 덮어씀.

    [GP-SEC §1] 연락처 원문 저장 절대 금지 — contact_hash(SHA-256)만 저장.
    """
    db = get_trinity_db()
    if not db:
        return False

    c_hash = hash_contact(client_contact)
    if not c_hash:
        return False

    now_iso = datetime.now().isoformat()
    payload = {
        "contact_hash":     c_hash,
        "agent_id":         agent_id or "",
        "person_id":        person_id or "",
        "analyzed_at":      now_iso,
        "estimated_income": float(estimated_income) if estimated_income else 0.0,
        "kb7_score":        int(kb7_score) if kb7_score else 0,
        "analysis_data":    analysis_data,
        "report_text":      report_text or "",
        "updated_at":       now_iso,
    }

    try:
        db.table("analysis_reports").upsert(
            payload,
            on_conflict="contact_hash,agent_id",
        ).execute()
        return True
    except Exception as _e:
        try:
            st.error(f"📛 DB 저장 실패: {_e}")
        except Exception:
            pass
        return False


# ══════════════════════════════════════════════════════════════════════════════
# [5] DB 조회 — HQ 도킹 시 최신 분석 결과 Pull
# ══════════════════════════════════════════════════════════════════════════════
def get_analysis_from_db(
    client_contact: str = "",
    agent_id: str = "",
    person_id: str = "",
) -> Optional[dict]:
    """
    고객의 최신 분석 결과 Pull.
    client_contact 또는 person_id 중 하나 이상 제공 필요.
    agent_id 지정 시 해당 설계사 분석만, 미지정 시 전체 최신 1건.

    Returns:
        dict: analyzed_at, estimated_income, kb7_score, analysis_data, report_text
        None: 데이터 없음
    """
    db = get_trinity_db()
    if not db:
        return None

    try:
        if client_contact:
            c_hash = hash_contact(client_contact)
            if not c_hash:
                return None
            q = db.table("analysis_reports").select("*").eq("contact_hash", c_hash)
        elif person_id:
            q = db.table("analysis_reports").select("*").eq("person_id", person_id)
        else:
            return None

        if agent_id:
            q = q.eq("agent_id", agent_id)

        resp = q.order("analyzed_at", desc=True).limit(1).execute()

        if resp.data:
            row = resp.data[0]
            if isinstance(row.get("analysis_data"), str):
                try:
                    row["analysis_data"] = json.loads(row["analysis_data"])
                except Exception:
                    pass
            return row
        return None
    except Exception as _e:
        try:
            st.error(f"📛 DB 조회 실패: {_e}")
        except Exception:
            pass
        return None


# ══════════════════════════════════════════════════════════════════════════════
# [6] 통합 리포트 렌더러 + 카카오톡 전송 버튼 — HQ/CRM 공통 UI
# ══════════════════════════════════════════════════════════════════════════════
def render_trinity_report(
    analysis_data: dict,
    estimated_income: float,
    consultant_info: dict,
    client_name: str = "",
    show_kakao: bool = True,
) -> str:
    """
    트리니티 분석 결과 UI 렌더링 + 카카오톡 전송 버튼.

    Args:
        analysis_data:    run_trinity_analysis() 반환값
        estimated_income: 추정 월소득(원)
        consultant_info:  {"소속": "", "이름": "", "연락처": ""}
        client_name:      고객명
        show_kakao:       카카오톡 전송 버튼 표시 여부

    Returns:
        report_text (str) — save_analysis_to_db() report_text 파라미터용
    """
    _today = datetime.now().strftime("%Y년 %m월 %d일")
    _name    = consultant_info.get("이름", "")
    _company = consultant_info.get("소속", "")
    _phone   = consultant_info.get("연락처", "")

    # ── 리포트 헤더 ───────────────────────────────────────────────────────────
    html = (
        "<div style='border:1px dashed #000;border-radius:12px;"
        "background:#ffffff;padding:16px 20px;margin-bottom:12px;'>"
        "<div style='font-size:0.96rem;font-weight:900;color:#1a3a5c;"
        "border-bottom:2px solid #1a3a5c;padding-bottom:6px;margin-bottom:12px;'>"
        "📄 Goldkey AI Masters — 트리니티 맞춤형 보장 분석</div>"
        f"<div style='font-size:0.80rem;color:#374151;margin-bottom:10px;'>"
        f"고객: <b>{client_name or '소중한 고객'}님</b> &nbsp;|&nbsp; "
        f"필요 월소득(M_req): <b>{estimated_income:,.0f}원</b> &nbsp;|&nbsp; {_today}</div>"
    )

    # ── 보장 공백 테이블 ──────────────────────────────────────────────────────
    html += (
        "<table style='width:100%;border-collapse:collapse;font-size:0.78rem;margin-bottom:10px;'>"
        "<tr>"
        "<th style='background:#1a3a5c;color:#fff;padding:6px 8px;text-align:left;'>보장항목</th>"
        "<th style='background:#1a3a5c;color:#fff;padding:6px 8px;text-align:center;'>치료기간</th>"
        "<th style='background:#1a3a5c;color:#fff;padding:6px 8px;text-align:right;'>현재가입</th>"
        "<th style='background:#1a3a5c;color:#fff;padding:6px 8px;text-align:right;'>적정(역산)</th>"
        "<th style='background:#1a3a5c;color:#fff;padding:6px 8px;text-align:right;'>부족분</th>"
        "</tr>"
    )

    report_lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "📊 Goldkey AI 트리니티 보장 분석",
        f"고객: {client_name or '소중한 고객'}  |  {_today}",
        f"필요 월소득(M_req): {estimated_income:,.0f}원",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]

    for item, v in analysis_data.items():
        if str(item).startswith("_"):
            continue
        cur    = float(v.get("현재가입",  0) or 0)
        ade    = float(v.get("적정_역산", 0) or 0)
        gap    = float(v.get("부족분",    0) or 0)
        period = v.get("치료기간", "")
        badge  = v.get("충족여부", "")

        badge_color = "#dc2626" if badge == "위험" else ("#f59e0b" if badge == "부족" else "#059669")
        bg = "#fff5f5" if badge == "위험" else ("#fffbeb" if badge == "부족" else "#f0fdf4")

        gap_str = (
            f"<span style='color:{badge_color};font-weight:900;'>-{gap:,.0f}원</span>"
            if gap > 0 else
            "<span style='color:#059669;font-weight:700;'>✓ 충족</span>"
        )
        html += (
            f"<tr style='background:{bg};'>"
            f"<td style='border:1px solid #e5e7eb;padding:5px 8px;font-weight:700;'>{item}</td>"
            f"<td style='border:1px solid #e5e7eb;padding:5px 8px;text-align:center;"
            f"color:#6b7280;font-size:0.74rem;'>{period}</td>"
            f"<td style='border:1px solid #e5e7eb;padding:5px 8px;text-align:right;'>"
            f"{cur:,.0f}</td>"
            f"<td style='border:1px solid #e5e7eb;padding:5px 8px;text-align:right;'>"
            f"{ade:,.0f}</td>"
            f"<td style='border:1px solid #e5e7eb;padding:5px 8px;text-align:right;'>"
            f"{gap_str}</td>"
            f"</tr>"
        )
        report_lines.append(
            f"  {item}: 현재 {cur:,.0f} / 적정 {ade:,.0f} / 부족 {gap:,.0f} ({badge})"
        )

    html += "</table>"

    # ── [트리니티 소득 대체 리포트] 신설 섹션 ────────────────────────────────
    _imeta = analysis_data.get("_income_meta", {})
    if _imeta:
        _cn       = _imeta.get("coverage_needs", {})
        _bd       = _imeta.get("breakdown", {})
        _mreq     = float(_imeta.get("m_req", estimated_income))
        _gann     = float(_imeta.get("gross_annual", 0))
        _nann     = float(_imeta.get("net_annual", 0))
        _drate    = float(_imeta.get("deduction_rate", 0))
        _cancer_c = _cn.get("암진단비", {})
        _cancer_2y = float(_cancer_c.get("2년(기본치료)", 0))
        _cancer_3y = float(_cancer_c.get("3년(집중재활)", 0))
        _cancer_5y = float(_cancer_c.get("5년(완치판정)", 0))
        _disab_c  = _cn.get("후유장해", {})
        _disab_12 = float(_disab_c.get("12개월", 0))
        _disab_18 = float(_disab_c.get("18개월", 0))
        _disab_24 = float(_disab_c.get("24개월", 0))
        _daily    = float(_cn.get("입원일당", 0))
        _cancer_current = float((analysis_data.get("암진단비") or {}).get("현재가입", 0))
        _cancer_gap_5y  = max(0.0, _cancer_5y - _cancer_current)

        html += (
            "<div style='background:#eff6ff;border:1px dashed #000;border-radius:10px;"
            "padding:14px 16px;margin:10px 0 12px 0;'>"
            "<div style='font-size:0.88rem;font-weight:900;color:#1a3a5c;"
            "border-bottom:1px dashed #93c5fd;padding-bottom:6px;margin-bottom:10px;'>"
            "🔬 트리니티 초정밀 — 소득 대체 리포트</div>"
            "<div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:10px;'>"
            f"<div style='background:#fff;border:1px solid #bfdbfe;border-radius:6px;padding:8px;text-align:center;'>"
            f"<div style='font-size:0.68rem;color:#6b7280;'>명목 연봉 (I_gross)</div>"
            f"<div style='font-size:0.85rem;font-weight:900;color:#1e3a8a;'>{_gann:,.0f}원</div></div>"
            f"<div style='background:#fff;border:1px solid #bbf7d0;border-radius:6px;padding:8px;text-align:center;'>"
            f"<div style='font-size:0.68rem;color:#6b7280;'>합산공제율 (세율+4대보험)</div>"
            f"<div style='font-size:0.85rem;font-weight:900;color:#059669;'>{_drate*100:.1f}%</div></div>"
            f"<div style='background:#fff;border:1px solid #fde68a;border-radius:6px;padding:8px;text-align:center;'>"
            f"<div style='font-size:0.68rem;color:#6b7280;'>필요 월소득 (M_req)</div>"
            f"<div style='font-size:0.85rem;font-weight:900;color:#92400e;'>{_mreq:,.0f}원</div></div>"
            "</div>"
            f"<div style='background:#fff5f5;border-left:4px solid #ef4444;"
            f"border-radius:0 6px 6px 0;padding:10px 12px;margin-bottom:8px;'>"
            f"<div style='font-size:0.80rem;font-weight:900;color:#dc2626;margin-bottom:4px;'>🎗️ 암 진단비 필요 자금</div>"
            f"<div style='font-size:0.78rem;color:#374151;margin-bottom:4px;'>"
            f"선생님의 가처분 소득을 지키기 위해 암 진단 시 최소 "
            f"<b>{_cancer_2y:,.0f}원</b>(2년)에서 최대 <b>{_cancer_5y:,.0f}원</b>(5년)이 준비되어야 합니다.</div>"
            f"<div style='font-size:0.74rem;color:#6b7280;'>"
            f"2년(기본치료) {_cancer_2y:,.0f} &nbsp;|&nbsp; "
            f"3년(집중재활) {_cancer_3y:,.0f} &nbsp;|&nbsp; "
            f"5년(완치판정) {_cancer_5y:,.0f}</div>"
        )
        if _cancer_gap_5y > 0:
            html += (
                f"<div style='font-size:0.76rem;font-weight:900;color:#b91c1c;margin-top:4px;'>"
                f"⚠️ 현재 준비금({_cancer_current:,.0f}원) 기준 5년 공백: {_cancer_gap_5y:,.0f}원</div>"
            )
        html += "</div>"
        html += (
            f"<div style='background:#fefce8;border-left:4px solid #f59e0b;"
            f"border-radius:0 6px 6px 0;padding:10px 12px;margin-bottom:8px;'>"
            f"<div style='font-size:0.80rem;font-weight:900;color:#92400e;margin-bottom:4px;'>🦽 후유장해 필요 생활비</div>"
            f"<div style='font-size:0.74rem;color:#6b7280;'>"
            f"12개월 {_disab_12:,.0f} &nbsp;|&nbsp; "
            f"18개월 {_disab_18:,.0f} &nbsp;|&nbsp; "
            f"24개월 {_disab_24:,.0f}</div></div>"
            f"<div style='background:#f0fdf4;border-left:4px solid #22c55e;"
            f"border-radius:0 6px 6px 0;padding:10px 12px;'>"
            f"<div style='font-size:0.80rem;font-weight:900;color:#15803d;margin-bottom:4px;'>🏥 입원 일당 기준</div>"
            f"<div style='font-size:0.78rem;color:#374151;'>"
            f"하루 입원 시 최소 <b>{_daily:,.0f}원</b>이 지급되어야 소득 상실을 막을 수 있습니다.</div></div>"
            "</div>"
        )

        _ai_context = (
            "\n━━━ [트리니티 소득 역산 컨텍스트 — AI 인수심사 보조 데이터] ━━━\n"
            f"명목 연봉(I_gross): {_gann:,.0f}원\n"
            f"가처분 연소득(I_net): {_nann:,.0f}원 (합산공제율 {_drate*100:.1f}%)\n"
            f"필요 월소득(M_req): {_mreq:,.0f}원\n"
            f"암 진단비 필요액 — 2년: {_cancer_2y:,.0f}원 / 3년: {_cancer_3y:,.0f}원 / 5년: {_cancer_5y:,.0f}원\n"
            f"현재 암진단비 준비: {_cancer_current:,.0f}원"
        )
        if _cancer_gap_5y > 0:
            _ai_context += (
                f"\n→ [AI 분석 필수 반영] 5년 기준 암진단비 보장 공백 {_cancer_gap_5y:,.0f}원 — "
                f"고객님의 암 진단비 필요액은 5년 기준 {_cancer_5y:,.0f}원이나, "
                f"현재 {_cancer_current:,.0f}원만 준비되어 있어 {_cancer_gap_5y:,.0f}원의 심각한 보장 공백이 확인됩니다.\n"
            )
        _ai_context += f"입원 일당 기준: {_daily:,.0f}원/일\n━━━\n"
        try:
            st.session_state["trinity_ai_context"] = _ai_context
        except Exception:
            pass

        report_lines += [
            "",
            "━━━ 소득 대체 리포트 ━━━",
            f"명목 연봉: {_gann:,.0f}원  /  가처분 연소득: {_nann:,.0f}원  /  합산공제율: {_drate*100:.1f}%",
            f"필요 월소득(M_req): {_mreq:,.0f}원",
            f"암 진단비 필요액: 2년 {_cancer_2y:,.0f} / 3년 {_cancer_3y:,.0f} / 5년 {_cancer_5y:,.0f}",
            f"후유장해 필요액: 12개월 {_disab_12:,.0f} / 18개월 {_disab_18:,.0f} / 24개월 {_disab_24:,.0f}",
            f"입원 일당 기준: {_daily:,.0f}원/일",
        ]

    # ── 담당 전문가 정보 ──────────────────────────────────────────────────────
    if _name or _company:
        html += (
            "<div style='background:#f8fafc;border-left:4px solid #1a3a5c;"
            "border-radius:0 6px 6px 0;padding:8px 12px;font-size:0.78rem;margin-top:8px;'>"
            f"<b>👨‍💼 담당 전문가</b> &nbsp; 소속: {_company} &nbsp;|&nbsp; "
            f"성명: {_name} &nbsp;|&nbsp; 연락처: {_phone}</div>"
        )
        report_lines += ["", f"담당: {_company} {_name} ({_phone})"]

    html += (
        "<div style='font-size:0.70rem;color:#9ca3af;margin-top:8px;'>"
        "출처: 국가통계포털(KOSIS) · 한국신용정보원 · 통계청 2023</div></div>"
    )

    report_lines.append("출처: 국가통계포털(KOSIS) · 한국신용정보원 · 통계청 2023")
    st.markdown(html, unsafe_allow_html=True)

    report_text = "\n".join(report_lines)

    # ── 카카오톡 전송 버튼 ────────────────────────────────────────────────────
    if show_kakao:
        _gap_lines = "\n".join(
            f"• {k}: 부족 {float(v.get('부족분', 0)):,.0f}원"
            for k, v in analysis_data.items()
            if not str(k).startswith("_") and float(v.get("부족분", 0) or 0) > 0
        )
        _imeta_k = analysis_data.get("_income_meta", {})
        _mreq_k  = float(_imeta_k.get("m_req", estimated_income))
        _gann_k  = float(_imeta_k.get("gross_annual", 0))
        share_text = (
            f"[내 소득 대비 보장 부족액]\n"
            f"{_name or 'Goldkey'} 설계사 | 2026 트리니티 초정밀 역산 기준\n"
            f"명목 연봉: {_gann_k:,.0f}원 → 필요 월소득(M_req): {_mreq_k:,.0f}원\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "▼ 소득 대비 보장 부족액 ▼\n"
            + _gap_lines
            + "\n━━━━━━━━━━━━━━━━━━━━━\n"
            "※ 2026년 개정 요율 7.19% + 8단계 소득세 구간 + 국민연금 4.5% 반영"
        )
        kakao_url = f"kakaotalk://send?text={urllib.parse.quote(share_text)}"
        st.markdown(
            f'<a href="{kakao_url}" target="_blank" style="text-decoration:none;">'
            f'<div style="background:#FEE500;color:#000;padding:12px;border-radius:8px;'
            f'text-align:center;font-weight:900;font-size:0.92rem;margin-top:8px;'
            f'border:1px dashed #000;">💬 카카오톡으로 보고서 전송하기</div></a>',
            unsafe_allow_html=True,
        )

    # ── AI 필살 클로징 생성기 ──────────────────────────────────────────────────
    _closing_key = f"_trinity_closing_{hash(client_name or 'x') % 99999}"
    st.markdown(
        "<div style='margin-top:10px;border-top:1px dashed #000;padding-top:10px;'>",
        unsafe_allow_html=True,
    )
    if st.button(
        "🪄 AI 필살 클로징 멘트 생성",
        key=_closing_key,
        use_container_width=True,
        help="트리니티 분석 결과 기반 FCS(Fact-Crisis-Solution) 3단계 설득 스크립트 생성",
    ):
        with st.status("고객 맞춤형 심리 설득 스크립트 구성 중...", expanded=True) as _cls_status:
            try:
                from closing_engine import generate_killer_closing as _gkc
                _script = _gkc(
                    analysis_result  = analysis_data,
                    estimated_income = estimated_income,
                    client_name      = client_name or "고객",
                )
                _cls_status.update(label="✅ 클로징 스크립트 완성!", state="complete")
                st.markdown(_script)
                st.info(
                    "💡 위 멘트를 복사하여 상담 시 활용하거나, 카카오톡 메시지에 포함하여 발송하세요."
                )
            except Exception as _ce:
                _cls_status.update(label="⚠️ 오류 발생", state="error")
                st.error("클로징 생성 오류: " + str(_ce))
    st.markdown("</div>", unsafe_allow_html=True)

    return report_text


# ══════════════════════════════════════════════════════════════════════════════
# [7] HQ 도킹 스테이션 전용 Pull UI 위젯
# ══════════════════════════════════════════════════════════════════════════════
def render_trinity_pull_box(
    client_contact: str = "",
    person_id: str = "",
    agent_id: str = "",
    client_name: str = "",
) -> None:
    """
    HQ 도킹 스테이션에서 CRM 분석 결과를 당겨오는 UI 위젯.
    scan_client_contact 또는 person_id 중 하나가 있을 때 호출.
    """
    if not client_contact and not person_id:
        return

    with st.expander("📥 CRM 분석 결과 불러오기 (트리니티 DB)", expanded=False):
        if st.button("🔄 최신 분석 결과 Pull", key="_trinity_pull_btn",
                     use_container_width=True):
            with st.spinner("중앙 DB 조회 중..."):
                _row = get_analysis_from_db(
                    client_contact=client_contact,
                    agent_id=agent_id,
                    person_id=person_id,
                )
            if _row:
                _analyzed_at = _row.get("analyzed_at", "")[:10]
                _income      = float(_row.get("estimated_income", 0) or 0)
                _kb7         = int(_row.get("kb7_score", 0) or 0)
                _adata       = _row.get("analysis_data") or {}
                st.success(f"✅ 분석 결과 로드 완료 (분석일: {_analyzed_at})")
                st.caption(f"추정 월소득: {_income:,.0f}원 | KB7 종합점수: {_kb7}점")
                _mp_info = {
                    "소속": st.session_state.get("_mp_company", ""),
                    "이름": st.session_state.get("_mp_name", ""),
                    "연락처": st.session_state.get("_mp_phone", ""),
                }
                render_trinity_report(
                    analysis_data=_adata,
                    estimated_income=_income,
                    consultant_info=_mp_info,
                    client_name=client_name,
                    show_kakao=True,
                )
            else:
                st.info(
                    f"아직 {client_name or '이 고객'}의 CRM 분석 결과가 없습니다. "
                    "CRM 앱에서 트리니티 분석을 먼저 실행해 주세요."
                )


# ══════════════════════════════════════════════════════════════════════════════
# [8] 통합 파이프라인 — 파서 ↔ 트리니티 엔진 원-스텝 실행기
# ══════════════════════════════════════════════════════════════════════════════
def execute_integrated_analysis(
    raw_external_data: list,
    client_contact: str,
    nhi_premium: float,
    consultant_info: Optional[dict] = None,
    client_name: str = "",
    agent_id: str = "",
    person_id: str = "",
    kb7_score: int = 0,
    consent_version: str = "",
    source: str = "내보험다보여",
    show_kakao: bool = True,
) -> tuple:
    """
    [통합 파이프라인] 파서 ↔ 트리니티 엔진 완전 통합 원-스텝 실행기.

    데이터 흐름:
      raw_external_data
        → parse_insurance_data()   (재료 손질)
        → run_trinity_analysis()   (Gap 계산)
        → render_trinity_report()  (화면 서빙)
        → save_analysis_to_db()    (HQ-CRM 동기화)
        → save_nibo_consent_log()  (동의 이력 기록)

    Args:
        raw_external_data: 내보험다보여 API 응답 리스트 (파싱 전 RAW)
            지원 필드: prodName / traitName / coverageName → 담보명
                       amt / amount / coverageAmt          → 가입금액
                       status / contStatus                 → 계약 상태
        client_contact:   고객 연락처 원문 [GP-SEC §1: SHA-256 해시 후 DB 저장]
        nhi_premium:      월 건강보험료(원) — 추정 월소득 역산 기준
        consultant_info:  {"소속": "", "이름": "", "연락처": ""}
        client_name:      고객명 (리포트 표시용)
        agent_id:         설계사 ID
        person_id:        CRM person UUID
        kb7_score:        KB 7대 분류 종합점수 (메타데이터)
        consent_version:  내보험다보여 동의 버전 (consent_log 기록)
        source:           데이터 출처 레이블 (로그용)
        show_kakao:       카카오톡 공유 버튼 표시 여부

    Returns:
        (analysis_data dict, unmapped_items list, save_success bool)
    """
    from data_normalizer import (
        parse_insurance_data  as _parse,
        save_nibo_consent_log as _log_consent,
    )

    # ── Step 1: 파싱 (재료 손질) ──────────────────────────────────────────────
    standardized_data, unmapped = _parse(raw_external_data, source=source)
    if unmapped:
        _um_names = ", ".join(
            (u["raw"][:15] if isinstance(u, dict) else str(u)[:15])
            for u in unmapped[:3]
        )
        _um_tail = " ..." if len(unmapped) > 3 else ""
        st.info(
            f"ℹ️ 매핑되지 않은 항목 {len(unmapped)}건 (기타담보 처리): "
            f"{_um_names}{_um_tail}"
        )

    # ── Step 2: 트리니티 엔진 가동 (요리 시작) ────────────────────────────────
    analysis_data, estimated_income = run_trinity_analysis(
        current_coverage=standardized_data,
        nhi_premium=float(nhi_premium),
    )

    # ── Step 3: 리포트 렌더링 (서빙) ─────────────────────────────────────────
    report_text = render_trinity_report(
        analysis_data    = analysis_data,
        estimated_income = estimated_income,
        consultant_info  = consultant_info or {},
        client_name      = client_name,
        show_kakao       = show_kakao,
    )

    # ── Step 4: 중앙 DB 저장 (HQ-CRM 동기화) ─────────────────────────────────
    save_ok = save_analysis_to_db(
        client_contact   = client_contact,
        analysis_data    = analysis_data,
        estimated_income = estimated_income,
        agent_id         = agent_id,
        kb7_score        = kb7_score,
        report_text      = report_text,
        person_id        = person_id,
    )
    if save_ok:
        st.toast("✅ 분석 결과가 중앙 DB에 안전하게 저장되었습니다.", icon="💾")

    # ── Step 5: 동의 이력 기록 ───────────────────────────────────────────────
    if agent_id or person_id:
        try:
            _log_consent(
                agent_id        = agent_id,
                person_id       = person_id,
                consented       = True,
                consent_version = consent_version,
            )
        except Exception:
            pass

    return analysis_data, unmapped, save_ok
