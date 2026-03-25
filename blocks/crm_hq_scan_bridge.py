# ══════════════════════════════════════════════════════════════════════════════
# [BLOCK] crm_hq_scan_bridge.py
# CRM → HQ 스캔 사령부 공통 딥링크 (scan_hub, policy_scan, claim_scanner, disability)
# 스캔 OCR 본체는 HQ(app.py) 단일 — CRM은 cid+SSO 딥링크만 제공.
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations

import streamlit as st

HQ_SCAN_SECTORS: tuple[tuple[str, str], ...] = (
    ("🔬 통합 스캔 허브", "scan_hub"),
    ("📄 보험증권 분석", "policy_scan"),
    ("🧾 청구 스캐너", "claim_scanner"),
    ("♿ 장해 산출", "disability"),
)


def render_hq_scan_bridge_links(
    *,
    sel_pid: str,
    user_id: str,
    hq_app_url: str = "http://localhost:8501",
) -> None:
    """HQ 스캔 탭 4종 딥링크 (gk_sector = tab_key). cid 없으면 안내만."""
    if not (sel_pid or "").strip():
        st.caption("고객을 표에서 선택하면 HQ 스캔 사령부로 이동할 수 있습니다.")
        return
    _cid = sel_pid.strip()
    st.markdown(
        "<div style='font-size:clamp(11px,1.6vw,13px);font-weight:800;color:#0f172a;"
        "margin:10px 0 6px;'>🔬 HQ 스캔 사령부 — 통합스캔 · 증권 · 청구 · 장해</div>",
        unsafe_allow_html=True,
    )
    _cols = st.columns(4)
    for _i, (_lbl, _sector) in enumerate(HQ_SCAN_SECTORS):
        with _cols[_i]:
            try:
                from shared_components import build_deeplink_to_hq

                _url = build_deeplink_to_hq(
                    cid=_cid,
                    agent_id=user_id,
                    sector=_sector,
                    user_id=user_id,
                )
            except Exception:
                _url = f"{hq_app_url.rstrip('/')}/?gk_sector={_sector}&gk_cid={_cid}"
            st.markdown(
                f'<a href="{_url}" target="_blank" rel="noopener noreferrer" '
                'style="display:block;text-align:center;background:#ecfdf5;color:#065f46;'
                "border:1px solid #6ee7b7;border-radius:10px;padding:8px 6px;"
                'font-size:clamp(10px,1.5vw,12px);font-weight:800;text-decoration:none;">'
                f"{_lbl}</a>",
                unsafe_allow_html=True,
            )
