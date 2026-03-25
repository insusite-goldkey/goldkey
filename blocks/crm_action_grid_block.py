"""
[GP-44] CRM 메인 대시보드 — 수평 액션 그리드 블록.
배치: 달력·「고객 정보 입력」필터 블록 직후(메인 목록 모드).
레이블·순서는 rules.json → shared_components.get_crm_action_definitions().
"""
from __future__ import annotations

import streamlit as st


# 목록 화면 유지 + 인라인 패널 (SPA 전환 없음)
_INLINE_PANEL_KEYS = frozenset({"nibo", "analysis"})


_ACTION_GRID_SCROLL_CSS = """
<style>
/* [GP-ACTION-SCROLL] 액션 그리드 수평 스크롤 — no-wrap + overflow-x:auto */
[data-testid="stHorizontalBlock"]:has([class*="st-key-crm_dash_ag_"]) {
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    overflow-x: auto !important;
    overflow-y: visible !important;
    -ms-overflow-style: none !important;
    scrollbar-width: none !important;
    padding-bottom: 4px !important;
    gap: 6px !important;
    -webkit-mask-image: linear-gradient(to right, black 85%, transparent 100%);
    mask-image: linear-gradient(to right, black 85%, transparent 100%);
}
[data-testid="stHorizontalBlock"]:has([class*="st-key-crm_dash_ag_"])::-webkit-scrollbar {
    display: none !important;
}
[data-testid="stHorizontalBlock"]:has([class*="st-key-crm_dash_ag_"]) > [data-testid="column"] {
    flex-shrink: 0 !important;
    min-width: 80px !important;
    max-width: 120px !important;
    width: auto !important;
}
</style>
"""


def render_crm_dashboard_action_grid(_user_id: str, _all_custs: list) -> None:
    """메인 대시보드: 고객 표 직후 — rules 기반 수평 액션 그리드."""
    from shared_components import get_crm_action_grid_title, get_crm_action_definitions

    st.markdown(_ACTION_GRID_SCROLL_CSS, unsafe_allow_html=True)

    _sel = st.session_state.get("crm_selected_pid", "")
    _sel_c = (
        next((c for c in _all_custs if c.get("person_id") == _sel), None) if _sel else None
    )
    _actions = get_crm_action_definitions()
    _title = get_crm_action_grid_title()

    st.markdown(
        "<div class='crm-responsive-shell crm-action-grid-wrap'>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='font-size:clamp(13px,2vw,16px);font-weight:900;color:#880e4f;"
        f"margin:4px 0 8px;'>{_title}</div>",
        unsafe_allow_html=True,
    )
    # 모든 버튼을 단일 수평 블록에 배치하고, CSS flex-wrap으로 반응형 래핑 처리
    _cols = st.columns(max(1, len(_actions)))
    for _ci, (_lbl, _sk, _req_c) in enumerate(_actions):
        with _cols[_ci]:
            _dis = _req_c and not _sel_c
            if st.button(
                _lbl,
                key=f"crm_dash_ag_{_sk}",
                disabled=_dis,
                use_container_width=True,
            ):
                if _sk in _INLINE_PANEL_KEYS:
                    st.session_state["crm_list_inline_panel"] = _sk
                    st.session_state["crm_spa_mode"] = "list"
                else:
                    st.session_state["crm_spa_mode"] = "customer"
                    st.session_state["crm_spa_screen"] = _sk
                    st.session_state.pop("crm_spa_screen_radio", None)
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
