"""
[GP-CRM] 상담 센터 — 고객정보 입력 하단 5:5 분할 (분석·연동 | 리포트).
유동 타이포(clamp) · 파스텔 · 수평형 그리드 준수.
"""
from __future__ import annotations

import streamlit as st


def render_crm_consultation_center(
    user_id: str,
    *,
    sel_pid: str = "",
    hq_app_url: str = "http://localhost:8501",
) -> None:
    """좌: 건보료·트리니티·Nibo·동의 / 우: AI 증권분석 보고서 박스.

    sel_pid 미전달 시 session_state crm_selected_pid 사용 (고객 목록 화면).
    """
    st.markdown(
        "<div class='crm-responsive-shell' style='max-width:min(100%,960px);width:100%;"
        "margin:4px auto 6px;'>"
        "<div style='font-size:clamp(13px,2vw,16px);font-weight:900;color:#0f172a;"
        "margin-bottom:4px;'>🏥 상담 센터</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    _bridge_pid = (sel_pid or "").strip() or str(
        st.session_state.get("crm_selected_pid", "") or ""
    ).strip()
    from blocks.crm_hq_scan_bridge import render_hq_scan_bridge_links

    with st.expander("🔬 HQ 스캔 사령부 (통합스캔 · 증권 · 청구 · 장해)", expanded=False):
        render_hq_scan_bridge_links(
            sel_pid=_bridge_pid,
            user_id=user_id,
            hq_app_url=hq_app_url,
        )
    _c_l, _c_r = st.columns([1, 1], gap="medium")

    with _c_l:
        st.markdown(
            "<div style='font-size:clamp(12px,1.8vw,15px);font-weight:800;color:#1e40af;'>"
            "분석 및 연동</div>",
            unsafe_allow_html=True,
        )
        _nhi = st.number_input(
            "월납입 건보료 (원)",
            min_value=0,
            max_value=50_000_000,
            value=int(st.session_state.get("crm_cc_nhi", 350_000)),
            step=10_000,
            key="crm_cc_nhi_input",
        )
        st.session_state["crm_cc_nhi"] = _nhi
        if st.button("🤖 AI 분석 실행", key="crm_cc_run_tri", use_container_width=True):
            try:
                from shared_components import calculate_trinity_metrics

                st.session_state["crm_cc_tri"] = calculate_trinity_metrics(int(_nhi))
            except Exception as _e:
                st.session_state["crm_cc_tri"] = None
                st.warning(f"분석 오류: {_e}")
        _tri = st.session_state.get("crm_cc_tri")
        if _tri:
            st.success(
                f"가처분 월소득(추정): {_tri.get('monthly_income', 0):,}원 · "
                f"일실수입(일): {_tri.get('daily_value', 0):,}원"
            )
        _consent = st.checkbox(
            "개인정보·분석 목적 동의 (필수)",
            value=st.session_state.get("crm_cc_consent", False),
            key="crm_cc_consent_cb",
        )
        st.session_state["crm_cc_consent"] = _consent
        _b1, _b2 = st.columns(2)
        with _b1:
            if st.button("⏱ 트리니티 요약", key="crm_cc_btn_tri", use_container_width=True):
                st.info("상세 트리니티는 HQ 정밀 분석 탭에서 확인하세요.")
        with _b2:
            if st.button("🌐 내보험다보여", key="crm_cc_btn_nibo", use_container_width=True):
                if not _consent:
                    st.warning("동의 후 이용 가능합니다.")
                elif not _bridge_pid:
                    st.warning("고객을 표에서 먼저 선택하세요.")
                else:
                    st.session_state["crm_list_inline_panel"] = "nibo"
                    st.rerun()
        # [GP-44] 내보험다보여 하단 이동 설치 — 증권AI분석·카카오·핸드폰스캔
        st.markdown(
            "<div style='font-size:0.72rem;font-weight:700;color:#475569;margin:6px 0 3px;'>"
            "📌 고객 선택 후 사용 가능</div>",
            unsafe_allow_html=True,
        )
        _b3, _b4, _b5 = st.columns(3)
        with _b3:
            if st.button("📊 보험증권 AI 분석", key="crm_cc_btn_analysis", use_container_width=True):
                if not _bridge_pid:
                    st.warning("고객을 표에서 먼저 선택하세요.")
                else:
                    st.session_state["crm_spa_mode"] = "customer"
                    st.session_state["crm_spa_screen"] = "analysis"
                    st.rerun()
        with _b4:
            if st.button("💬 카카오 알림톡·문자", key="crm_cc_btn_kakao", use_container_width=True):
                if not _bridge_pid:
                    st.warning("고객을 표에서 먼저 선택하세요.")
                else:
                    st.session_state["crm_spa_mode"] = "customer"
                    st.session_state["crm_spa_screen"] = "kakao"
                    st.rerun()
        with _b5:
            if st.button("📱 핸드폰 증권 스캔", key="crm_cc_btn_settings", use_container_width=True):
                st.session_state["crm_spa_mode"] = "customer"
                st.session_state["crm_spa_screen"] = "settings"
                st.rerun()
        with st.expander("📷 증권 스캔 최근 목록 (최대 5건)", expanded=False):
            _scans = st.session_state.get("crm_cc_scans", [])
            if not _scans:
                st.caption("최근 스캔 기록이 없습니다. HQ 또는 내보험 탭에서 스캔하세요.")
            else:
                _box = (
                    "<div style='max-height:8.5rem;overflow-y:auto;font-size:clamp(11px,1.5vw,13px);"
                    "line-height:1.45;padding:6px;border:1px dashed #cbd5e1;border-radius:8px;'>"
                )
                for _i, _s in enumerate(_scans[-5:][::-1]):
                    _box += f"<div>{_i+1}. {_s}</div>"
                _box += "</div>"
                st.markdown(_box, unsafe_allow_html=True)

    with _c_r:
        st.markdown(
            "<div style='font-size:clamp(13px,2vw,17px);font-weight:900;color:#0f172a;'>"
            "AI 증권분석 보고서</div>",
            unsafe_allow_html=True,
        )
        _tri = st.session_state.get("crm_cc_tri")
        _tri_lines = "—"
        if _tri:
            _tri_lines = (
                f"가처분 월소득: {_tri.get('monthly_income', 0):,} 원\n"
                f"일실수입: {_tri.get('daily_value', 0):,} 원\n"
                f"사망·암 등 완성형 보장(요약): 일실수입×개월수 기반\n"
                f"(상세 수치는 HQ 리포트 참조)\n"
                f"user: {user_id[:8]}…"
            )
        st.markdown(
            "<div style='font-size:clamp(11px,1.5vw,13px);font-weight:700;color:#334155;"
            "margin:6px 0 4px;'>박스 1 · 트리니티 보험금 산출 요약</div>",
            unsafe_allow_html=True,
        )
        st.text_area(
            "tri_box",
            value=_tri_lines[:2000],
            height=120,
            disabled=True,
            key="crm_cc_tri_box",
            label_visibility="collapsed",
        )
        _hq_txt = st.session_state.get(
            "crm_cc_hq_analysis",
            "HQ 연동 분석 결과가 없습니다. 고객 선택 후 HQ 심화 분석을 실행하세요.",
        )
        st.markdown(
            "<div style='font-size:clamp(11px,1.5vw,13px);font-weight:700;color:#334155;"
            "margin:8px 0 4px;'>박스 2 · HQ 연동 AI 증권분석</div>",
            unsafe_allow_html=True,
        )
        st.text_area(
            "hq_box",
            value=_hq_txt[:2000],
            height=120,
            disabled=True,
            key="crm_cc_hq_box",
            label_visibility="collapsed",
        )
