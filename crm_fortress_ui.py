"""
crm_fortress_ui.py — 마법의 마스터 키 (The Master Gate)
통합 입력 폼 (3단계 스테퍼) + 전략적 전황판 (Strategic Dashboard)

사용법:
    from crm_fortress_ui import render_master_gate, render_strategic_dashboard
    render_master_gate(sb, agent_id)
    render_strategic_dashboard(sb, agent_id)
"""
from __future__ import annotations
import streamlit as st
import uuid
import random
from datetime import datetime, timedelta


# ────────────────────────────────────────────────────────────────────────────
# 공통 CSS
# ────────────────────────────────────────────────────────────────────────────
_CSS_AUTH = """
<style>
.auth-gate {
  border:2px solid #1d4ed8; border-radius:14px;
  padding:22px 20px 18px 20px; background:#eff6ff;
  max-width:460px; margin:30px auto;
}
.auth-gate-title {
  font-size:1.05rem; font-weight:900; color:#1d4ed8;
  margin-bottom:6px;
}
.auth-gate-sub {
  font-size:0.78rem; color:#64748b; margin-bottom:18px;
  line-height:1.6;
}
.auth-otp-box {
  border:2px dashed #1d4ed8; border-radius:10px;
  background:#ffffff; padding:14px 16px; margin:12px 0;
  font-size:1.35rem; font-weight:900; color:#1d4ed8;
  text-align:center; letter-spacing:0.25em;
}
.auth-timer {
  font-size:0.78rem; font-weight:700; color:#dc2626;
  text-align:right; margin-top:4px;
}
.auth-person-card {
  border:1px dashed #16a34a; border-radius:8px;
  background:#f0fdf4; padding:10px 14px; margin-bottom:10px;
  font-size:0.85rem; font-weight:700;
}
</style>
"""

_CSS = """
<style>
.mgk-step-bar {
  display:flex; gap:0; margin-bottom:18px;
}
.mgk-step {
  flex:1; text-align:center; padding:8px 4px;
  font-size:0.78rem; font-weight:900;
  border-bottom: 3px solid #e5e7eb; color:#9ca3af;
}
.mgk-step.active {
  border-bottom: 3px solid #dc2626; color:#000000;
}
.mgk-step.done {
  border-bottom: 3px solid #16a34a; color:#16a34a;
}
.mgk-card {
  border:1px dashed #000000; border-radius:10px;
  padding:14px 16px; margin-bottom:10px;
  background:#ffffff;
}
.mgk-tag {
  display:inline-block; font-size:0.72rem; font-weight:900;
  border-radius:4px; padding:2px 8px; margin-right:4px;
}
.mgk-tag-insured   { background:#fef3c7; border:1px solid #f59e0b; color:#92400e; }
.mgk-tag-contractor{ background:#dbeafe; border:1px solid #93c5fd; color:#1d4ed8; }
.mgk-tag-beneficiary{background:#ede9fe; border:1px solid #c4b5fd; color:#6d28d9; }
.mgk-tag-family    { background:#dcfce7; border:1px solid #86efac; color:#15803d; }
.mgk-tag-intro     { background:#fee2e2; border:1px solid #fca5a5; color:#991b1b; }
.dash-metric {
  border:1px dashed #000000; border-radius:10px;
  padding:14px 12px; background:#fffbeb; text-align:center;
}
.dash-metric .val { font-size:1.4rem; font-weight:900; color:#000000; }
.dash-metric .lbl { font-size:0.74rem; font-weight:700; color:#6b7280; margin-top:2px; }
.policy-row {
  border:1px solid #e5e7eb; border-radius:8px;
  padding:9px 12px; margin-bottom:6px; background:#f9fafb;
}
.policy-row:hover { background:#f0f9ff; }
.family-node {
  border:1px dashed #000; border-radius:8px;
  padding:8px 12px; background:#fff; margin:3px; display:inline-block;
  font-size:0.8rem; font-weight:700; cursor:pointer; min-width:90px;
  text-align:center;
}
.family-node.center {
  border:2px solid #dc2626; background:#fff7ed; color:#dc2626;
}
.gap-bar-wrap { margin-bottom:8px; }
.gap-bar-label {
  font-size:0.78rem; font-weight:900; color:#000; margin-bottom:2px;
}
.gap-bar-bg {
  background:#e5e7eb; border-radius:6px; height:16px; overflow:hidden;
}
.gap-bar-fill {
  height:16px; border-radius:6px;
  transition: width 0.4s;
}
</style>
"""

_KB7_LABELS = [
    ("사망보장",    "질병/상해 사망"),
    ("3대진단",     "암·뇌·심장 진단비"),
    ("수술입원",    "수술/입원비"),
    ("실손",       "실손의료비"),
    ("운전자",      "운전자/배상책임"),
    ("치아치매",    "치아/치매/간병"),
    ("연금저축",    "연금/저축"),
]

_KB7_KEYWORDS = {
    "사망보장":  ["사망", "종신", "정기"],
    "3대진단":   ["암", "뇌", "심장", "진단", "뇌혈관", "심근경색"],
    "수술입원":  ["수술", "입원", "일당", "입원비"],
    "실손":      ["실손", "실비", "의료비"],
    "운전자":    ["운전자", "배상", "자동차"],
    "치아치매":  ["치아", "치매", "간병", "임플란트"],
    "연금저축":  ["연금", "저축", "적립", "노후"],
}


# ────────────────────────────────────────────────────────────────────────────
# 인증 상수
# ────────────────────────────────────────────────────────────────────────────
_OTP_EXPIRE_SECONDS = 180   # 3분
_OTP_MAX_ATTEMPTS   = 5     # 최대 시도 횟수


# ────────────────────────────────────────────────────────────────────────────
# 내부 헬퍼
# ────────────────────────────────────────────────────────────────────────────
def _sb_ok(sb) -> bool:
    return sb is not None


def _fmt_won(v) -> str:
    try:
        n = int(float(v))
        if n >= 100_000_000:
            return f"{n // 100_000_000}억 {(n % 100_000_000) // 10_000:,}만원" if n % 100_000_000 else f"{n // 100_000_000}억원"
        if n >= 10_000:
            return f"{n // 10_000:,}만원"
        return f"{n:,}원"
    except Exception:
        return str(v)


def _age_from_birth(birth: str) -> str:
    try:
        b = datetime.strptime(birth[:8], "%Y%m%d")
        age = (datetime.now() - b).days // 365
        return f"{age}세"
    except Exception:
        return ""


def _kb7_score(policies: list[dict]) -> dict[str, float]:
    """증권 목록에서 KB7 분류별 점수(0~100) 산출"""
    score: dict[str, float] = {k: 0.0 for k, _ in _KB7_LABELS}
    for pol in policies:
        name = (pol.get("product_name") or "") + (pol.get("insurance_company") or "")
        for key, kws in _KB7_KEYWORDS.items():
            for kw in kws:
                if kw in name:
                    score[key] = min(100.0, score[key] + 40.0)
    return score


def _stepper_html(step: int) -> str:
    labels = ["① 인적 자원", "② 관계망", "③ 증권·역할"]
    parts = []
    for i, lbl in enumerate(labels, 1):
        cls = "active" if i == step else ("done" if i < step else "mgk-step")
        if cls == "mgk-step":
            parts.append(f'<div class="mgk-step">{lbl}</div>')
        else:
            parts.append(f'<div class="mgk-step {cls}">{lbl}</div>')
    return f'<div class="mgk-step-bar">{"".join(parts)}</div>'


# ────────────────────────────────────────────────────────────────────────────
# OTP 인증 게이트 — person_id 기반 기기 무관 세션 인증
# ────────────────────────────────────────────────────────────────────────────
def _otp_remaining() -> int:
    """남은 OTP 유효 시간(초). 만료 시 0 반환"""
    issued = st.session_state.get("_crm_otp_issued_at")
    if not issued:
        return 0
    elapsed = (datetime.now() - issued).total_seconds()
    remaining = int(_OTP_EXPIRE_SECONDS - elapsed)
    return max(0, remaining)


def _otp_clear():
    """OTP 관련 세션 상태 초기화"""
    for k in ("_crm_otp_code", "_crm_otp_issued_at",
              "_crm_otp_person", "_crm_otp_attempts"):
        st.session_state.pop(k, None)


def render_crm_person_auth(sb, agent_id: str) -> bool:
    """
    person_id 기반 CRM 인증 게이트.
    인증 완료 시 True 반환 + st.session_state['_crm_auth_person_id'] 설정.
    미완료 시 False 반환 (UI 렌더링 후 caller가 st.stop() 해야 함).
    """
    st.markdown(_CSS_AUTH, unsafe_allow_html=True)

    # ── 이미 인증된 세션 ──────────────────────────────────────
    if st.session_state.get("_crm_auth_person_id"):
        _pid  = st.session_state["_crm_auth_person_id"]
        _pname = st.session_state.get("_crm_auth_person_name", "")
        _c1, _c2 = st.columns([8, 2])
        with _c1:
            st.markdown(
                f'<div class="auth-person-card">'
                f'✅ <b>{_pname}</b> 님으로 인증된 세션입니다.'
                f'<span style="font-size:0.72rem;color:#6b7280;margin-left:8px;">'  
                f'ID: {_pid[:8]}…</span></div>',
                unsafe_allow_html=True,
            )
        with _c2:
            if st.button("🔓 로그아웃", key="crm_auth_logout", use_container_width=True):
                st.session_state.pop("_crm_auth_person_id", None)
                st.session_state.pop("_crm_auth_person_name", None)
                _otp_clear()
                st.rerun()
        return True

    # ── 인증 UI ──────────────────────────────────────────────
    st.markdown(
        '<div class="auth-gate">'
        '<div class="auth-gate-title">🔐 고객 본인 확인</div>'
        '<div class="auth-gate-sub">'
        '어떤 기기에서 접속하더라도 동일한 고객 데이터를 불러옵니다.<br>'
        '등록된 <b>이름</b>과 <b>연락처 끝 4자리</b>를 입력하세요.</div>',
        unsafe_allow_html=True,
    )

    _auth_stage = st.session_state.get("_crm_auth_stage", "input")  # input | otp

    if _auth_stage == "input":
        _a_name    = st.text_input("👤 이름",    placeholder="예) 홍길동",  key="crm_auth_name")
        _a_contact = st.text_input("📱 연락처 끝 4자리", placeholder="예) 1234",
                                   max_chars=4, key="crm_auth_contact")

        if st.button("🔍 조회 및 OTP 발송", key="crm_auth_lookup", use_container_width=True):
            if not _a_name or not _a_contact:
                st.warning("이름과 연락처 끝 4자리를 모두 입력해 주세요.")
            elif not _sb_ok(sb):
                st.error("DB 연결이 필요합니다. 관리자에게 문의하세요.")
            else:
                try:
                    from crm_fortress import find_person_by_name_contact
                    _matched = find_person_by_name_contact(sb, _a_name, _a_contact, agent_id)
                except Exception as _e:
                    st.error(f"조회 오류: {_e}")
                    _matched = []

                if not _matched:
                    st.error(
                        "⚠️ 일치하는 정보를 찾을 수 없습니다.\n\n"
                        "이름 또는 연락처를 다시 확인해 주세요."
                    )
                else:
                    _person = _matched[0]
                    _otp    = str(random.randint(100000, 999999))
                    st.session_state["_crm_otp_code"]      = _otp
                    st.session_state["_crm_otp_issued_at"] = datetime.now()
                    st.session_state["_crm_otp_person"]    = _person
                    st.session_state["_crm_otp_attempts"]  = 0
                    st.session_state["_crm_auth_stage"]    = "otp"
                    st.rerun()

    else:  # otp 입력 단계
        _remaining = _otp_remaining()
        if _remaining <= 0:
            st.error("⏰ 인증 시간이 만료되었습니다. 다시 조회해 주세요.")
            _otp_clear()
            st.session_state["_crm_auth_stage"] = "input"
            st.markdown('</div>', unsafe_allow_html=True)
            if st.button("↩ 다시 시도", key="crm_auth_retry"):
                st.rerun()
            return False

        _person   = st.session_state["_crm_otp_person"]
        _otp_real = st.session_state["_crm_otp_code"]
        _contact  = _person.get("contact", "")
        _tail     = _contact[-4:] if _contact else "****"

        st.markdown(
            f'<div class="auth-otp-box">📲 {_otp_real}</div>'
            f'<div style="font-size:0.73rem;color:#6b7280;text-align:center;margin-bottom:4px;">'
            f'위 6자리 번호가 <b>***-****-{_tail}</b>로 발송되었습니다. (시뮬레이션)</div>'
            f'<div class="auth-timer">⏱ 남은 시간: {_remaining}초</div>',
            unsafe_allow_html=True,
        )

        _attempts = st.session_state.get("_crm_otp_attempts", 0)
        _otp_input = st.text_input(
            "🔢 인증번호 6자리 입력", max_chars=6,
            placeholder="6자리 숫자", key="crm_otp_input",
        )

        _col_verify, _col_cancel = st.columns([3, 1])
        with _col_verify:
            if st.button("✅ 인증 확인", key="crm_otp_verify", use_container_width=True):
                if _attempts >= _OTP_MAX_ATTEMPTS:
                    st.error(f"⛔ 시도 횟수({_OTP_MAX_ATTEMPTS}회)를 초과했습니다. 다시 조회해 주세요.")
                    _otp_clear()
                    st.session_state["_crm_auth_stage"] = "input"
                    st.rerun()
                elif _otp_input.strip() == _otp_real:
                    st.session_state["_crm_auth_person_id"]   = _person["id"]
                    st.session_state["_crm_auth_person_name"] = _person.get("name", "")
                    _otp_clear()
                    st.session_state["_crm_auth_stage"] = "input"
                    st.success(f"✅ {_person.get('name','')} 님 인증 완료!")
                    st.rerun()
                else:
                    st.session_state["_crm_otp_attempts"] = _attempts + 1
                    left = _OTP_MAX_ATTEMPTS - _attempts - 1
                    st.error(f"❌ 인증번호가 일치하지 않습니다. (남은 시도: {left}회)")
        with _col_cancel:
            if st.button("취소", key="crm_otp_cancel", use_container_width=True):
                _otp_clear()
                st.session_state["_crm_auth_stage"] = "input"
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    return False


# ────────────────────────────────────────────────────────────────────────────
# Master Gate — 통합 입력 폼
# ────────────────────────────────────────────────────────────────────────────
def render_master_gate(sb, agent_id: str) -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown(
        "<div style='border:2px solid #dc2626;border-radius:12px;"
        "padding:12px 16px 8px 16px;background:#fff7ed;margin-bottom:14px;'>"
        "<div style='font-size:1.0rem;font-weight:900;color:#dc2626;margin-bottom:2px;'>"
        "🗝️ The Master Gate — 마법의 마스터 키</div>"
        "<div style='font-size:0.78rem;color:#6b7280;'>"
        "한 번의 제출로 people → relationships → policies → policy_roles 에 분산 저장됩니다.</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ── 스텝 초기화 ──────────────────────────────────────────
    if "mgk_step" not in st.session_state:
        st.session_state["mgk_step"] = 1

    step = st.session_state["mgk_step"]
    st.markdown(_stepper_html(step), unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════
    # STEP 1: 인적 자원 등록
    # ════════════════════════════════════════════════════════
    if step == 1:
        st.markdown(
            "<div class='mgk-card'>"
            "<div style='font-weight:900;color:#92400e;margin-bottom:10px;'>"
            "👤 Step 1 — 인적 자원 등록 "
            "<span class='mgk-tag mgk-tag-insured'>TAG: 피보험자</span></div>",
            unsafe_allow_html=True,
        )

        # 기존 인물 검색 (중복 방지)
        _dup_check_name = st.text_input(
            "🔍 성명 입력 (기존 DB 자동 검색)",
            value=st.session_state.get("mgk_name", ""),
            placeholder="예) 홍길동",
            key="mgk_name_input",
        )
        st.session_state["mgk_name"] = _dup_check_name

        _dup_rows: list[dict] = []
        if _dup_check_name and len(_dup_check_name) >= 2 and _sb_ok(sb):
            try:
                from crm_fortress import search_people as _sp
                _dup_rows = _sp(sb, agent_id, _dup_check_name)
            except Exception:
                _dup_rows = []

        if _dup_rows:
            st.markdown(
                f"<div style='background:#fef3c7;border:1px solid #f59e0b;border-radius:6px;"
                f"padding:6px 10px;font-size:0.78rem;font-weight:700;color:#92400e;margin-bottom:6px;'>"
                f"⚠️ 동일 이름 {len(_dup_rows)}명 발견 — 아래에서 선택하거나 신규 등록하세요.</div>",
                unsafe_allow_html=True,
            )
            _dup_options = {"✏️ 신규 등록": None}
            for _d in _dup_rows:
                _lbl = f"{_d.get('name','')}  ({_d.get('birth_date','')})  📞{str(_d.get('contact',''))[-4:]}"
                _dup_options[_lbl] = _d
            _dup_sel = st.selectbox("기존 인물 선택 또는 신규 등록", list(_dup_options.keys()), key="mgk_dup_sel")
            _dup_chosen = _dup_options.get(_dup_sel)
            if _dup_chosen:
                st.session_state["mgk_existing_id"] = _dup_chosen.get("id")
                st.session_state["mgk_dob"]         = _dup_chosen.get("birth_date", "")
                st.session_state["mgk_gender"]      = _dup_chosen.get("gender", "")
                st.session_state["mgk_contact"]     = _dup_chosen.get("contact", "")
                st.session_state["mgk_job"]         = _dup_chosen.get("job", "")
                st.session_state["mgk_sick"]        = _dup_chosen.get("sick", "해당없음")
                st.info(f"✅ [{_dup_chosen.get('name','')}] 기존 인물 선택됨 — 아래 정보를 수정하거나 다음 단계로 진행하세요.")
            else:
                st.session_state["mgk_existing_id"] = None
        else:
            st.session_state["mgk_existing_id"] = None

        _SICK_OPTS = ["해당없음", "심사필요(3개월이내 치료)", "유병자(입원·수술이력)", "유병자(투약중)", "유병자(암·중풍)"]

        _s1c1, _s1c2 = st.columns(2)
        with _s1c1:
            _dob = st.text_input("📅 생년월일 (YYYYMMDD)",
                value=st.session_state.get("mgk_dob", ""),
                placeholder="예) 19800101", max_chars=8, key="mgk_dob_input")
            _contact = st.text_input("📞 연락처",
                value=st.session_state.get("mgk_contact", ""),
                placeholder="예) 010-1234-5678", key="mgk_contact_input")
        with _s1c2:
            _gender = st.selectbox("⚧ 성별",
                ["", "남", "여", "기타"],
                index=["", "남", "여", "기타"].index(st.session_state.get("mgk_gender", "") or ""),
                key="mgk_gender_input")
            _job = st.text_input("💼 직업",
                value=st.session_state.get("mgk_job", ""),
                placeholder="예) 회사원", key="mgk_job_input")

        _sick_idx = _SICK_OPTS.index(st.session_state.get("mgk_sick", "해당없음")) \
                    if st.session_state.get("mgk_sick", "해당없음") in _SICK_OPTS else 0
        _sick = st.selectbox("🩺 유병자 여부", _SICK_OPTS, index=_sick_idx, key="mgk_sick_input")

        _memo = st.text_area("📝 메모", value=st.session_state.get("mgk_memo", ""),
                              placeholder="특이사항, 소개 경로 등", height=70, key="mgk_memo_input")

        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("다음 단계 → 관계망 형성", key="mgk_s1_next", use_container_width=True,
                     type="primary"):
            if not _dup_check_name.strip():
                st.error("❌ 성명을 입력하세요.")
                return
            st.session_state.update({
                "mgk_name":    _dup_check_name.strip(),
                "mgk_dob":     _dob,
                "mgk_gender":  _gender,
                "mgk_contact": _contact,
                "mgk_job":     _job,
                "mgk_sick":    _sick,
                "mgk_memo":    _memo,
                "mgk_step":    2,
            })
            st.rerun()

    # ════════════════════════════════════════════════════════
    # STEP 2: 관계망 형성
    # ════════════════════════════════════════════════════════
    elif step == 2:
        st.markdown(
            "<div class='mgk-card'>"
            "<div style='font-weight:900;color:#1d4ed8;margin-bottom:10px;'>"
            "👥 Step 2 — 관계망 형성 "
            "<span class='mgk-tag mgk-tag-family'>TAG: 관계</span></div>",
            unsafe_allow_html=True,
        )

        _name_now = st.session_state.get("mgk_name", "")
        st.markdown(
            f"<div style='font-size:0.82rem;font-weight:700;color:#374151;margin-bottom:8px;'>"
            f"기준 인물: <b style='color:#dc2626;'>{_name_now}</b>"
            f" — 이 인물이 누구와 연결되어 있는지 설정하세요.</div>",
            unsafe_allow_html=True,
        )

        # 관계 추가 목록 (세션 유지)
        if "mgk_relations" not in st.session_state:
            st.session_state["mgk_relations"] = []

        _RELATION_TYPES = ["배우자", "자녀", "부모", "형제", "소개자", "법인직원", "기타"]

        # 기존 등록 인물 목록 (관계 대상 선택용)
        _existing_people: list[dict] = []
        if _sb_ok(sb):
            try:
                from crm_fortress import search_people as _sp2
                _existing_people = _sp2(sb, agent_id)
            except Exception:
                _existing_people = []

        _people_opts: dict[str, str | None] = {"— 선택 —": None}
        for _p in _existing_people:
            if _p.get("name", "") != _name_now:
                _lbl = f"{_p.get('name','')} ({_p.get('birth_date','')})"
                _people_opts[_lbl] = _p.get("id")

        st.markdown("**[+ 관계 추가]**")
        _r2c1, _r2c2, _r2c3 = st.columns([3, 2, 1])
        with _r2c1:
            _rel_target = st.selectbox("연결 대상 (등록된 인물)", list(_people_opts.keys()),
                                       key="mgk_rel_target")
        with _r2c2:
            _rel_type = st.selectbox("관계 유형", _RELATION_TYPES, key="mgk_rel_type")
        with _r2c3:
            st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
            if st.button("➕ 추가", key="mgk_rel_add", use_container_width=True):
                _tid = _people_opts.get(_rel_target)
                if _tid:
                    _rel_entry = {"target_id": _tid, "target_name": _rel_target, "rel_type": _rel_type}
                    if _rel_entry not in st.session_state["mgk_relations"]:
                        st.session_state["mgk_relations"].append(_rel_entry)
                    st.rerun()
                else:
                    st.warning("연결 대상을 선택하세요.")

        # 새 인물 직접 입력 관계 추가
        with st.expander("✏️ 미등록 인물 직접 추가", expanded=False):
            st.markdown(
                "<div style='font-size:0.76rem;color:#6b7280;margin-bottom:6px;'>"
                "아직 DB에 없는 가족·소개자를 이름만 입력하면 Step 3 저장 시 자동 등록됩니다.</div>",
                unsafe_allow_html=True,
            )
            _nr2c1, _nr2c2, _nr2c3 = st.columns([2, 2, 2])
            with _nr2c1:
                _new_rel_name = st.text_input("이름", placeholder="예) 홍길순", key="mgk_new_rel_name")
            with _nr2c2:
                _new_rel_dob  = st.text_input("생년월일", placeholder="YYYYMMDD", max_chars=8, key="mgk_new_rel_dob")
            with _nr2c3:
                _new_rel_type2 = st.selectbox("관계", _RELATION_TYPES, key="mgk_new_rel_type")
            if st.button("➕ 직접 추가", key="mgk_new_rel_add"):
                if _new_rel_name.strip():
                    _entry = {"target_id": None, "target_name": _new_rel_name.strip(),
                              "target_dob": _new_rel_dob, "rel_type": _new_rel_type2}
                    st.session_state["mgk_relations"].append(_entry)
                    st.rerun()

        # 추가된 관계 목록 표시
        _rels_now = st.session_state["mgk_relations"]
        if _rels_now:
            st.markdown("**추가된 관계:**")
            for _ri, _rr in enumerate(_rels_now):
                _rl_col1, _rl_col2 = st.columns([5, 1])
                with _rl_col1:
                    _tag_cls = "mgk-tag-family" if _rr["rel_type"] not in ("소개자",) else "mgk-tag-intro"
                    st.markdown(
                        f'<div style="border:1px solid #e5e7eb;border-radius:6px;'
                        f'padding:5px 10px;font-size:0.8rem;font-weight:700;">'
                        f'{_name_now} → '
                        f'<span class="mgk-tag {_tag_cls}">{_rr["rel_type"]}</span> '
                        f'{_rr["target_name"]}'
                        f'{"  (" + _rr.get("target_dob","") + ")" if _rr.get("target_dob") else ""}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with _rl_col2:
                    if st.button("🗑️", key=f"mgk_del_rel_{_ri}"):
                        st.session_state["mgk_relations"].pop(_ri)
                        st.rerun()
        else:
            st.caption("관계 없음 — 관계가 없어도 다음 단계로 진행할 수 있습니다.")

        st.markdown("</div>", unsafe_allow_html=True)

        _s2c1, _s2c2 = st.columns([1, 1])
        with _s2c1:
            if st.button("← 이전 단계", key="mgk_s2_back", use_container_width=True):
                st.session_state["mgk_step"] = 1
                st.rerun()
        with _s2c2:
            if st.button("다음 단계 → 증권·역할", key="mgk_s2_next", use_container_width=True,
                         type="primary"):
                st.session_state["mgk_step"] = 3
                st.rerun()

    # ════════════════════════════════════════════════════════
    # STEP 3: 증권 및 역할 할당
    # ════════════════════════════════════════════════════════
    elif step == 3:
        st.markdown(
            "<div class='mgk-card'>"
            "<div style='font-weight:900;color:#065f46;margin-bottom:10px;'>"
            "🛡️ Step 3 — 증권 및 역할 할당</div>",
            unsafe_allow_html=True,
        )

        _name_now = st.session_state.get("mgk_name", "")
        _rels_now = st.session_state.get("mgk_relations", [])

        # 이 증권에서 선택 가능한 인물 목록 (기준인물 + 관계망)
        _candidate_names = [_name_now]
        for _rr in _rels_now:
            if _rr["target_name"] and _rr["target_name"] not in _candidate_names:
                _candidate_names.append(_rr["target_name"])

        st.markdown(
            f"<div style='font-size:0.8rem;color:#374151;margin-bottom:8px;'>"
            f"기준 인물: <b style='color:#dc2626;'>{_name_now}</b> | "
            f"관계망 인물: {', '.join(_candidate_names[1:]) or '없음'}</div>",
            unsafe_allow_html=True,
        )

        # 증권 추가 목록
        if "mgk_policies" not in st.session_state:
            st.session_state["mgk_policies"] = []

        st.markdown("**보험 증권 추가:**")
        _p3c1, _p3c2 = st.columns(2)
        with _p3c1:
            _pol_company  = st.text_input("보험사", placeholder="예) 삼성생명", key="mgk_pol_company")
            _pol_product  = st.text_input("상품명", placeholder="예) 통합건강보험 플러스", key="mgk_pol_product")
            _pol_number   = st.text_input("증권번호 (선택)", placeholder="예) 2023-0001234", key="mgk_pol_number")
            _pol_date     = st.text_input("계약일 (YYYYMMDD)", placeholder="예) 20230101",
                                          max_chars=8, key="mgk_pol_date")
        with _p3c2:
            _pol_premium  = st.text_input("월보험료 (원)", placeholder="예) 150000", key="mgk_pol_premium")
            _pol_type     = st.selectbox("상품 유형 (선택)",
                ["", "종신", "정기", "건강", "암", "실손", "운전자", "저축", "연금", "어린이", "기타"],
                key="mgk_pol_type")
            _pol_contractor = st.selectbox(
                "🔵 계약자 (1명)",
                _candidate_names,
                key="mgk_pol_contractor",
                help="보험료를 납부하는 사람",
            )
            _pol_insureds = st.multiselect(
                "🟠 피보험자 (복수 가능)",
                _candidate_names,
                default=[_name_now],
                key="mgk_pol_insureds",
                help="보장을 받는 사람 — 여러 명 선택 가능",
            )
            _pol_beneficiary = st.selectbox(
                "🟣 수익자 (선택)",
                [""] + _candidate_names,
                key="mgk_pol_beneficiary",
                help="보험금을 수령하는 사람",
            )

        if st.button("➕ 이 증권 목록에 추가", key="mgk_pol_add", use_container_width=True):
            if not _pol_company or not _pol_product:
                st.error("보험사와 상품명을 입력하세요.")
            else:
                _pol_entry = {
                    "company":     _pol_company,
                    "product":     _pol_product,
                    "number":      _pol_number,
                    "date":        _pol_date,
                    "premium":     _pol_premium,
                    "type":        _pol_type,
                    "contractor":  _pol_contractor,
                    "insureds":    list(_pol_insureds),
                    "beneficiary": _pol_beneficiary,
                }
                st.session_state["mgk_policies"].append(_pol_entry)
                st.rerun()

        # 추가된 증권 목록
        _pols_now = st.session_state["mgk_policies"]
        if _pols_now:
            st.markdown("**추가된 증권:**")
            for _pi, _pp in enumerate(_pols_now):
                _pol_col1, _pol_col2 = st.columns([5, 1])
                with _pol_col1:
                    _ins_str = ", ".join(_pp.get("insureds", []))
                    st.markdown(
                        f'<div class="policy-row">'
                        f'<span style="font-weight:900;">{_pp["company"]}</span> '
                        f'<span style="color:#374151;">{_pp["product"]}</span> '
                        f'<span class="mgk-tag mgk-tag-contractor">계약: {_pp.get("contractor","")}</span>'
                        f'<span class="mgk-tag mgk-tag-insured">피보: {_ins_str}</span>'
                        f'{"<span class=mgk-tag mgk-tag-beneficiary>수익: " + _pp["beneficiary"] + "</span>" if _pp.get("beneficiary") else ""}'
                        f'{"  보험료: " + _fmt_won(_pp["premium"]) if _pp.get("premium") else ""}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with _pol_col2:
                    if st.button("🗑️", key=f"mgk_del_pol_{_pi}"):
                        st.session_state["mgk_policies"].pop(_pi)
                        st.rerun()
        else:
            st.caption("증권 없음 — 증권 없이도 인물/관계만 저장할 수 있습니다.")

        st.markdown("</div>", unsafe_allow_html=True)

        _s3c1, _s3c2 = st.columns([1, 2])
        with _s3c1:
            if st.button("← 이전 단계", key="mgk_s3_back", use_container_width=True):
                st.session_state["mgk_step"] = 2
                st.rerun()
        with _s3c2:
            if st.button("🚀 전체 저장 (DB 영구 반영)", key="mgk_s3_submit",
                         use_container_width=True, type="primary"):
                _mgk_save(sb, agent_id)


def _mgk_save(sb, agent_id: str) -> None:
    """Master Gate 전체 저장 실행"""
    from crm_fortress import (
        upsert_person    as _up,
        upsert_relationship as _ur,
        upsert_policy    as _upol,
        link_policy_role as _lr,
    )

    _name     = st.session_state.get("mgk_name", "")
    _dob      = st.session_state.get("mgk_dob", "")
    _gender   = st.session_state.get("mgk_gender", "")
    _contact  = st.session_state.get("mgk_contact", "")
    _job      = st.session_state.get("mgk_job", "")
    _sick     = st.session_state.get("mgk_sick", "")
    _memo     = st.session_state.get("mgk_memo", "")
    _rels     = st.session_state.get("mgk_relations", [])
    _pols     = st.session_state.get("mgk_policies", [])
    _existing = st.session_state.get("mgk_existing_id")

    log: list[str] = []

    if not _sb_ok(sb):
        st.error("❌ Supabase 연결 없음 — 저장 불가")
        return

    try:
        # ① 기준 인물 저장
        _center = _up(
            sb, name=_name, birth_date=_dob, gender=_gender,
            contact=_contact, is_real_client=True, agent_id=agent_id,
            memo=f"직업:{_job} / 유병:{_sick} / {_memo}",
            person_id=_existing,
        )
        _center_id = _center.get("id", _existing)
        log.append(f"✅ 인물 저장: {_name} (ID: {str(_center_id)[:8]}…)")

        # ② 관계망 저장
        _name_to_id: dict[str, str] = {_name: _center_id}
        for _rr in _rels:
            _tid = _rr.get("target_id")
            if not _tid:
                # 미등록 인물 자동 등록
                _rp = _up(sb, name=_rr["target_name"],
                           birth_date=_rr.get("target_dob", ""),
                           agent_id=agent_id)
                _tid = _rp.get("id")
            _name_to_id[_rr["target_name"]] = _tid
            _ur(sb, from_person_id=_center_id, to_person_id=_tid,
                relation_type=_rr["rel_type"], agent_id=agent_id)
            log.append(f"🔗 관계 저장: {_name} →[{_rr['rel_type']}]→ {_rr['target_name']}")

        # ③ 증권 + 역할 저장
        for _pp in _pols:
            _prem_val = None
            try:
                _prem_val = float(str(_pp.get("premium", "")).replace(",", "")) if _pp.get("premium") else None
            except Exception:
                pass
            _pol_row = _upol(
                sb,
                insurance_company=_pp["company"],
                product_name=_pp["product"],
                agent_id=agent_id,
                policy_number=_pp.get("number", ""),
                product_type=_pp.get("type", ""),
                contract_date=_pp.get("date", ""),
                premium=_prem_val,
                source="manual",
            )
            _pol_id = _pol_row.get("id")
            if _pol_id:
                # 계약자 연결
                _con_name = _pp.get("contractor", _name)
                _con_id   = _name_to_id.get(_con_name, _center_id)
                _lr(sb, _pol_id, _con_id, "계약자", agent_id)
                # 피보험자 연결 (복수)
                for _ins_name in _pp.get("insureds", []):
                    _ins_id = _name_to_id.get(_ins_name, _center_id)
                    _lr(sb, _pol_id, _ins_id, "피보험자", agent_id)
                # 수익자 연결
                _bene_name = _pp.get("beneficiary", "")
                if _bene_name:
                    _bene_id = _name_to_id.get(_bene_name, _center_id)
                    _lr(sb, _pol_id, _bene_id, "수익자", agent_id)
                log.append(f"🛡️ 증권 저장: {_pp['company']} {_pp['product']} (계약자:{_con_name})")

        # ④ 세션 저장 + 결과 표시
        st.session_state["_fp_person_id"]        = _center_id
        st.session_state["scan_client_name"]     = _name
        st.session_state["scan_client_dob"]      = _dob
        st.session_state["_mgk_last_person_id"]  = _center_id
        # 캐시 무효화
        for _k in list(st.session_state.keys()):
            if _k.startswith("_fortress_people_"):
                del st.session_state[_k]

        st.success(f"🎉 **전체 저장 완료** — {_name} 인물·관계·증권이 CRM 요새에 영구 저장되었습니다!")
        for _lg in log:
            st.markdown(f"<div style='font-size:0.78rem;color:#374151;'>  {_lg}</div>",
                        unsafe_allow_html=True)

        # 스텝 리셋
        for _k in ["mgk_step", "mgk_name", "mgk_dob", "mgk_gender", "mgk_contact",
                   "mgk_job", "mgk_sick", "mgk_memo", "mgk_relations", "mgk_policies",
                   "mgk_existing_id"]:
            st.session_state.pop(_k, None)

    except Exception as _e:
        st.error(f"❌ 저장 오류: {str(_e)[:200]}")


# ────────────────────────────────────────────────────────────────────────────
# Strategic Dashboard — 전략적 전황판
# ────────────────────────────────────────────────────────────────────────────
def render_strategic_dashboard(sb, agent_id: str) -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown(
        "<div style='border:2px solid #1d4ed8;border-radius:12px;"
        "padding:12px 16px 8px 16px;background:#eff6ff;margin-bottom:14px;'>"
        "<div style='font-size:1.0rem;font-weight:900;color:#1d4ed8;margin-bottom:2px;'>"
        "📊 Strategic Dashboard — 전략적 전황판</div>"
        "<div style='font-size:0.78rem;color:#6b7280;'>"
        "고객 선택 → 가족 단위 보험 합산 분석 · 보장 공백 시각화 · 역할별 증권 리스트</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    if not _sb_ok(sb):
        st.warning("⚠️ Supabase 연결 없음 — 분석 데이터를 로드할 수 없습니다.")
        return

    # ── 고객 선택 ─────────────────────────────────────────────
    _people: list[dict] = []
    try:
        from crm_fortress import search_people as _sp3
        _people = _sp3(sb, agent_id)
    except Exception:
        _people = []

    if not _people:
        st.info("📭 등록된 고객이 없습니다. Master Gate에서 먼저 고객을 등록하세요.")
        return

    _ppl_map: dict[str, str] = {}
    for _p in _people:
        _lbl = f"{_p.get('name','')}  ({_p.get('birth_date','')})"
        _ppl_map[_lbl] = _p.get("id", "")

    _dash_sel = st.selectbox(
        "🔍 분석 대상 고객 선택",
        ["— 선택 —"] + list(_ppl_map.keys()),
        key="dash_person_sel",
        label_visibility="collapsed",
    )
    if _dash_sel == "— 선택 —":
        st.caption("위에서 분석할 고객을 선택하세요.")
        return

    _center_id = _ppl_map.get(_dash_sel, "")
    if not _center_id:
        return

    # ── 데이터 로드 ───────────────────────────────────────────
    try:
        from crm_fortress import (
            get_family_network         as _gfn,
            get_family_policies_summary as _gfps,
            get_person_policies        as _gpp,
        )
        _network = _gfn(sb, _center_id, agent_id)
        _all_ids = _network.get("all_ids", [_center_id])
        _family_summary = _gfps(sb, _all_ids, agent_id)
        _my_policies = _gpp(sb, _center_id)
    except Exception as _de:
        st.error(f"데이터 로드 오류: {str(_de)[:100]}")
        return

    _center_person = _network.get("center") or {}
    _center_name   = _center_person.get("name", "")
    _center_birth  = _center_person.get("birth_date", "")
    _family_members = _network.get("members", [])

    # ════════════════════════════════════════════════════════
    # TOP: Key Metrics
    # ════════════════════════════════════════════════════════
    st.markdown(
        f"<div style='font-weight:900;font-size:0.9rem;color:#000;margin:8px 0 6px 0;'>"
        f"👤 <span style='color:#dc2626;'>{_center_name}</span>"
        f"{'  · ' + _age_from_birth(_center_birth) if _center_birth else ''}"
        f"  &nbsp;|&nbsp; 가족 {len(_family_members)}명 연결</div>",
        unsafe_allow_html=True,
    )

    _total_prem   = _family_summary.get("total_premium", 0)
    _pol_count    = _family_summary.get("policy_count", 0)
    _my_as_insured = len(_my_policies.get("피보험자", []))
    _my_as_contr   = len(_my_policies.get("계약자", []))

    _km1, _km2, _km3, _km4 = st.columns(4)
    for _col, _val, _lbl in [
        (_km1, _fmt_won(_total_prem),        "가족 합산 월보험료"),
        (_km2, f"{_pol_count}건",            "가족 합산 증권 수"),
        (_km3, f"{_my_as_contr}건",          "내가 계약자인 보험"),
        (_km4, f"{_my_as_insured}건",        "내가 피보험자인 보험"),
    ]:
        with _col:
            st.markdown(
                f'<div class="dash-metric"><div class="val">{_val}</div>'
                f'<div class="lbl">{_lbl}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════
    # 3-컬럼 레이아웃: 가족관계도 | 보장공백 | 증권리스트
    # ════════════════════════════════════════════════════════
    _d_left, _d_center, _d_right = st.columns([2, 3, 3], gap="small")

    # ── Left: 가족 관계도 ─────────────────────────────────
    with _d_left:
        st.markdown(
            "<div class='mgk-card' style='min-height:300px;'>"
            "<div style='font-weight:900;font-size:0.85rem;color:#1d4ed8;margin-bottom:10px;'>"
            "🌳 가족 관계도</div>",
            unsafe_allow_html=True,
        )
        # 중심 노드
        st.markdown(
            f'<div style="text-align:center;margin-bottom:10px;">'
            f'<div class="family-node center">'
            f'⭐ {_center_name}<br>'
            f'<span style="font-size:0.68rem;font-weight:700;">'
            f'{_age_from_birth(_center_birth)}</span></div></div>',
            unsafe_allow_html=True,
        )
        if _family_members:
            _rel_node_html = ""
            for _fm in _family_members:
                _fp = _fm.get("person", {})
                _fn = _fp.get("name", "")
                _fb = _fp.get("birth_date", "")
                _ft = _fm.get("relation_type", "")
                _tag_cls = "mgk-tag-family" if _ft not in ("소개자",) else "mgk-tag-intro"
                _rel_node_html += (
                    f'<div style="text-align:center;margin-bottom:6px;">'
                    f'<span class="mgk-tag {_tag_cls}">{_ft}</span><br>'
                    f'<div class="family-node">{_fn}'
                    f'{"<br><span style=font-size:0.65rem;>" + _age_from_birth(_fb) + "</span>" if _fb else ""}'
                    f'</div></div>'
                )
            st.markdown(_rel_node_html, unsafe_allow_html=True)

            # 클릭으로 다른 구성원 분석 전환
            _sel_member = st.selectbox(
                "구성원 전환",
                ["— 선택 —"] + [_fm["person"].get("name", "") for _fm in _family_members],
                key="dash_family_switch",
                label_visibility="collapsed",
            )
            if _sel_member != "— 선택 —":
                for _fm in _family_members:
                    if _fm["person"].get("name") == _sel_member:
                        st.session_state["dash_person_sel"] = (
                            f"{_sel_member}  ({_fm['person'].get('birth_date','')})"
                        )
                        st.rerun()
        else:
            st.caption("연결된 가족·소개자 없음")

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Center: 보장 공백 분석 ────────────────────────────
    with _d_center:
        st.markdown(
            "<div class='mgk-card' style='min-height:300px;'>"
            "<div style='font-weight:900;font-size:0.85rem;color:#15803d;margin-bottom:10px;'>"
            "🎯 보장 공백 분석 (KB 7대 분류)</div>",
            unsafe_allow_html=True,
        )

        # 가족 전체 증권 합산
        _all_pols_flat: list[dict] = []
        _by_role = _family_summary.get("policies_by_role", {})
        for _role_pols in _by_role.values():
            _all_pols_flat.extend(_role_pols)

        _kb7_score = _kb7_score_fn(_all_pols_flat)

        _gap_html = ""
        for _key, _full_name in _KB7_LABELS:
            _score = _kb7_score.get(_key, 0.0)
            _pct   = min(int(_score), 100)
            if _pct >= 70:
                _bar_color = "#16a34a"
                _status    = "✅"
            elif _pct >= 30:
                _bar_color = "#f59e0b"
                _status    = "⚠️"
            else:
                _bar_color = "#dc2626"
                _status    = "❌"
            _gap_html += (
                f'<div class="gap-bar-wrap">'
                f'<div class="gap-bar-label">{_status} {_full_name}</div>'
                f'<div class="gap-bar-bg">'
                f'<div class="gap-bar-fill" style="width:{_pct}%;background:{_bar_color};"></div>'
                f'</div></div>'
            )

        st.markdown(_gap_html, unsafe_allow_html=True)

        _gap_legend = (
            "<div style='font-size:0.72rem;color:#6b7280;margin-top:8px;'>"
            "✅ 보장됨 &nbsp;⚠️ 부분 &nbsp;❌ 공백 (상품명 기준 추정치)</div>"
        )
        st.markdown(_gap_legend, unsafe_allow_html=True)

        # 가족 구성원별 보험료 미니 차트
        _ms = _family_summary.get("members_summary", [])
        if len(_ms) > 1:
            st.markdown("<hr style='margin:10px 0;border-color:#e5e7eb;'>", unsafe_allow_html=True)
            st.markdown("<div style='font-weight:900;font-size:0.78rem;color:#374151;margin-bottom:6px;'>가족 구성원별 보험료</div>",
                        unsafe_allow_html=True)
            _max_prem = max((m.get("total_premium", 0) for m in _ms), default=1) or 1
            for _m in _ms:
                _mprem = _m.get("total_premium", 0)
                _mpct  = int(_mprem / _max_prem * 100)
                st.markdown(
                    f'<div style="margin-bottom:4px;">'
                    f'<span style="font-size:0.76rem;font-weight:700;display:inline-block;width:60px;">{_m["name"][:4]}</span>'
                    f'<div class="gap-bar-bg" style="display:inline-block;width:calc(100% - 110px);vertical-align:middle;">'
                    f'<div class="gap-bar-fill" style="width:{_mpct}%;background:#3b82f6;"></div></div>'
                    f'<span style="font-size:0.72rem;color:#6b7280;margin-left:4px;">{_fmt_won(_mprem)}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Right: 증권 리스트 ────────────────────────────────
    with _d_right:
        st.markdown(
            "<div class='mgk-card' style='min-height:300px;'>"
            "<div style='font-weight:900;font-size:0.85rem;color:#92400e;margin-bottom:10px;'>"
            "📋 증권 리스트 (역할별 분리)</div>",
            unsafe_allow_html=True,
        )

        _tab_contr, _tab_insured, _tab_bene = st.tabs(["💳 계약자", "🛡️ 피보험자", "💰 수익자"])

        def _render_policy_list(pols: list[dict], role_color: str) -> None:
            if not pols:
                st.caption("해당 역할 증권 없음")
                return
            for _pol in pols:
                _pname = _pol.get("product_name", "")
                _pcomp = _pol.get("insurance_company", "")
                _pprem = _pol.get("premium")
                _pdate = _pol.get("contract_date", "")
                st.markdown(
                    f'<div class="policy-row">'
                    f'<span style="font-weight:900;font-size:0.82rem;">{_pcomp}</span> '
                    f'<span style="color:#374151;font-size:0.8rem;">{_pname}</span><br>'
                    f'<span style="font-size:0.72rem;color:#6b7280;">'
                    f'{"계약일: " + _pdate + "  " if _pdate else ""}'
                    f'{"월보험료: " + _fmt_won(_pprem) if _pprem else ""}'
                    f'</span></div>',
                    unsafe_allow_html=True,
                )

        with _tab_contr:
            _render_policy_list(_my_policies.get("계약자", []), "#1d4ed8")
        with _tab_insured:
            _render_policy_list(_my_policies.get("피보험자", []), "#92400e")
        with _tab_bene:
            _render_policy_list(_my_policies.get("수익자", []), "#6d28d9")

        st.markdown("</div>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════
    # Bottom: 가족 합산 전체 증권
    # ════════════════════════════════════════════════════════
    if _family_members:
        with st.expander(f"👨‍👩‍👧‍👦 가족 합산 전체 증권 ({_pol_count}건)", expanded=False):
            _btab_contr, _btab_insured = st.tabs(["💳 계약자 기준", "🛡️ 피보험자 기준"])
            with _btab_contr:
                for _pol in _by_role.get("계약자", []):
                    st.markdown(
                        f'<div class="policy-row">'
                        f'<b>{_pol.get("insurance_company","")}</b> {_pol.get("product_name","")}'
                        f'{"  <span style=color:#6b7280;font-size:0.72rem;>" + _fmt_won(_pol.get("premium")) + "</span>" if _pol.get("premium") else ""}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            with _btab_insured:
                for _pol in _by_role.get("피보험자", []):
                    st.markdown(
                        f'<div class="policy-row">'
                        f'<b>{_pol.get("insurance_company","")}</b> {_pol.get("product_name","")}'
                        f'{"  <span style=color:#6b7280;font-size:0.72rem;>" + _fmt_won(_pol.get("premium")) + "</span>" if _pol.get("premium") else ""}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )


def _kb7_score_fn(policies: list[dict]) -> dict[str, float]:
    """증권 목록에서 KB7 분류별 점수(0~100) 산출"""
    score: dict[str, float] = {k: 0.0 for k, _ in _KB7_LABELS}
    for pol in policies:
        name = (pol.get("product_name") or "") + (pol.get("insurance_company") or "")
        for key, kws in _KB7_KEYWORDS.items():
            for kw in kws:
                if kw in name:
                    score[key] = min(100.0, score[key] + 40.0)
    return score


# ────────────────────────────────────────────────────────────────────────────
# 통합 진입점: Master Gate + Dashboard 탭 렌더링
# ────────────────────────────────────────────────────────────────────────────
def render_crm_gate_full(sb, agent_id: str) -> None:
    """app.py에서 cur == 'crm_gate' 일 때 호출"""
    st.markdown(
        "<div style='border:2px solid #1d4ed8;border-radius:12px;"
        "padding:10px 16px 8px 16px;background:#eff6ff;margin-bottom:14px;'>"
        "<div style='font-size:1.0rem;font-weight:900;color:#1d4ed8;'>"
        "🏰 CRM 요새 — 고객 세션 게이트</div>"
        "<div style='font-size:0.78rem;color:#64748b;'>"
        "person_id 기준으로 세션을 유지합니다. 기기가 달라도 동일 데이터를 불러옵니다.</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ── 인증 게이트 ───────────────────────────────────────────
    _authed = render_crm_person_auth(sb, agent_id)
    if not _authed:
        st.info(
            "🔐 위에서 본인 인증을 완료하면 Master Gate와 Strategic Dashboard가 열립니다.\n\n"
            "**없는 고객이라면?** — 먼저 담당 설계사에게 고객 등록을 요청하세요."
        )
        return

    # ── 인증 완료: person_id를 Dashboard 기본값으로 설정 ─────
    _auth_pid = st.session_state.get("_crm_auth_person_id", "")
    if _auth_pid and not st.session_state.get("_fp_person_id"):
        st.session_state["_fp_person_id"] = _auth_pid

    # ── 탭 렌더링 ─────────────────────────────────────────────
    _tab_gate, _tab_dash = st.tabs(["🗝️ Master Gate (입력)", "📊 Strategic Dashboard (분석)"])
    with _tab_gate:
        render_master_gate(sb, agent_id)
    with _tab_dash:
        render_strategic_dashboard(sb, agent_id)
