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
  render_trinity_report()   — 통합 리포트 UI + 카카오톡 전송 버튼
  render_trinity_pull_box() — HQ 도킹 스테이션 전용 Pull UI 위젯

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
    트리니티 분석 = 건보료 역산 소득 × KB 표준 교차 분석.

    Args:
        current_coverage: {담보명: 가입금액(원)} dict
                          예) {"암진단비": 30_000_000, "뇌졸중진단비": 20_000_000}
        nhi_premium:      월 건강보험료(원) — 역산 기준. 추정 월소득 = premium × 30
        kb7_result:       HQ _kb_standard_analysis() 결과 list (있으면 메타 병합)

    Returns:
        (analysis_data dict, estimated_monthly_income float)
    """
    monthly_income = float(nhi_premium) * 30.0

    analysis_data: dict = {}
    for item, cfg in _TRINITY_STANDARD.items():
        current_val = float(current_coverage.get(item, 0) or 0)

        if cfg["income_mult"] > 0:
            adequate = monthly_income * cfg["income_mult"]
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

    return analysis_data, monthly_income


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
        f"추정 월소득: <b>{estimated_income:,.0f}원</b> &nbsp;|&nbsp; {_today}</div>"
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
        f"추정 월소득: {estimated_income:,.0f}원",
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
        share_text = (
            f"[AI 보장분석 리포트]\n"
            f"{_name or 'Goldkey'} 설계사가 보내드린 맞춤형 보장 분석 결과입니다.\n"
            f"고객님의 소득 기반 실질 필요 보장액을 확인해보세요.\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            + _gap_lines
        )
        kakao_url = f"kakaotalk://send?text={urllib.parse.quote(share_text)}"
        st.markdown(
            f'<a href="{kakao_url}" target="_blank" style="text-decoration:none;">'
            f'<div style="background:#FEE500;color:#000;padding:12px;border-radius:8px;'
            f'text-align:center;font-weight:900;font-size:0.92rem;margin-top:8px;'
            f'border:1px dashed #000;">💬 카카오톡으로 보고서 전송하기</div></a>',
            unsafe_allow_html=True,
        )

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
