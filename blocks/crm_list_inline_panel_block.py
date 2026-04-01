# ══════════════════════════════════════════════════════════════════════════════
# [BLOCK] crm_list_inline_panel_block.py
# 메인 목록(list) 모드에서 SPA 전환 없이 증권분석 패널 인라인 표시 (아웃룩 스타일)
# [2026-04-01] NIBO 기능 제거됨
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations

import streamlit as st


def render_crm_list_inline_panel(
    sel_cust: dict | None,
    sel_pid: str,
    user_id: str,
    hq_app_url: str,
) -> None:
    """crm_list_inline_panel 세션: 'analysis' | 비어 있음. (nibo 제거됨)"""
    _panel = (st.session_state.get("crm_list_inline_panel") or "").strip()
    if not _panel:
        return
    if not sel_pid:
        st.warning("고객을 표에서 선택한 뒤 이용하세요.")
        if st.button("✕ 닫기", key="crm_inline_close_need_cust"):
            st.session_state.pop("crm_list_inline_panel", None)
            st.rerun()
        return

    from shared_components import request_hq_analysis_trigger

    # ── [2026-04-01 내보험다보여 완전 제거] ──
    # if _panel == "nibo":
    #     st.markdown("---")
    #     _h1, _h2 = st.columns([5, 1])
    #     with _h1:
    #         st.markdown(
    #             "<div style='font-size:clamp(14px,2vw,17px);font-weight:900;color:#1e3a8a;'>"
    #             "🌐 내보험다보여 — 현재 화면 유지 · 인라인</div>",
    #             unsafe_allow_html=True,
    #         )
    #     with _h2:
    #         if st.button("✕ 닫기", key="crm_inline_close_nibo"):
    #             st.session_state.pop("crm_list_inline_panel", None)
    #             st.rerun()
    #     with st.spinner("Cloud Run(HQ) 분석 연동 준비 중..."):
    #         try:
    #             _res = request_hq_analysis_trigger(
    #                 person_id=sel_pid,
    #                 agent_id=user_id,
    #                 user_id=user_id,
    #                 sector="gk_sec10",
    #                 timeout_sec=12.0,
    #             )
    #             st.session_state["crm_cc_hq_last_trigger"] = _res
    #         except Exception as _e:
    #             st.session_state["crm_cc_hq_last_trigger"] = {"ok": False, "error": str(_e)}
    #     _tr = st.session_state.get("crm_cc_hq_last_trigger")
    #     if isinstance(_tr, dict) and not _tr.get("ok", True):
    #         st.caption(f"트리거 응답: {_tr}")
    #     if sel_cust:
    #         from blocks.crm_nibo_screen_block import render_crm_nibo_screen
    #
    #         render_crm_nibo_screen(sel_cust, sel_pid, user_id, hq_app_url)
    #     return

    if _panel == "analysis":
        st.markdown("---")
        _a1, _a2 = st.columns([5, 1])
        with _a1:
            st.markdown(
                "<div style='font-size:clamp(14px,2vw,17px);font-weight:900;color:#1e40af;'>"
                "📊 증권분석 — 현재 화면 유지 · 인라인</div>",
                unsafe_allow_html=True,
            )
        with _a2:
            if st.button("✕ 닫기", key="crm_inline_close_analysis"):
                st.session_state.pop("crm_list_inline_panel", None)
                st.rerun()
        with st.spinner("Cloud Run(HQ) 분석 연동 준비 중..."):
            try:
                _res = request_hq_analysis_trigger(
                    person_id=sel_pid,
                    agent_id=user_id,
                    user_id=user_id,
                    sector="policy_scan",
                    timeout_sec=12.0,
                )
                st.session_state["crm_cc_hq_last_trigger"] = _res
            except Exception as _e:
                st.session_state["crm_cc_hq_last_trigger"] = {"ok": False, "error": str(_e)}
        _tr = st.session_state.get("crm_cc_hq_last_trigger")
        if isinstance(_tr, dict) and not _tr.get("ok", True):
            st.caption(f"트리거 응답: {_tr}")
        if sel_cust:
            from blocks.crm_analysis_screen_block import render_crm_analysis_screen

            render_crm_analysis_screen(sel_cust, sel_pid, user_id, hq_app_url)
