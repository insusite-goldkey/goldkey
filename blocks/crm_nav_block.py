"""
[GP-CRM] 메인 대시보드 ↔ 고객 상세 — 양방향 네비 블록.
기존 peach_nav_* 키·스타일 유지 (삭제 금지, 위치만 호출부에서 제어).
"""
from __future__ import annotations

import streamlit as st


def render_crm_dual_nav(*, mode: str, sel_pid: str) -> None:
    """
    mode: 'list' — 초기(목록) 화면 | 'customer' — 고객 상세/업무 화면
    """
    _pn_l, _pn_m, _pn_r = st.columns([1, 6, 1])
    with _pn_l:
        if mode == "list":
            st.button(
                "⬅ 메인 대시보드",
                key="peach_nav_list_l",
                disabled=True,
                use_container_width=True,
                help="현재 화면 (메인)",
            )
        else:
            _back = st.button(
                "⬅ 메인 대시보드",
                key="peach_nav_cust_l",
                use_container_width=True,
                help="메인 대시보드(달력·목록)로 이동 — 선택 고객 유지",
            )
            if _back:
                st.session_state["crm_spa_mode"] = "list"
                st.rerun()
    with _pn_m:
        st.caption("메인 대시보드 ↔ 고객 상세")
    with _pn_r:
        if mode == "list":
            _go = st.button(
                "고객상세화면 ➡",
                key="peach_nav_list_r",
                disabled=not bool(sel_pid),
                use_container_width=True,
                help="선택된 고객 기준 상세·업무 화면으로 이동",
            )
            if _go and sel_pid:
                st.session_state["crm_spa_mode"] = "customer"
                st.session_state.setdefault("crm_spa_screen", "contact")
                st.rerun()
        else:
            st.button(
                "고객상세화면 ➡",
                key="peach_nav_cust_r",
                disabled=True,
                use_container_width=True,
                help="현재 화면 (고객 상세/업무)",
            )
