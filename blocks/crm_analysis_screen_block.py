# ══════════════════════════════════════════════════════════════════════════════
# [BLOCK] crm_analysis_screen_block.py
# 증권분석 — HQ 정밀 분석 발사대 + GCS Raw Data 백오피스
# 원본 위치: crm_app.py SCREEN 4 (_spa_screen == "analysis"), lines 2473–2650
# Cursor 마이그레이션용 독립 블록 (2026-03-24 추출)
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations
import streamlit as st


def render_crm_analysis_screen(
    sel_cust: dict | None,
    sel_pid: str,
    user_id: str,
    hq_app_url: str = "http://localhost:8501",
) -> None:
    """증권분석 스크린 블록.

    Args:
        sel_cust: 선택된 고객 dict (없으면 None)
        sel_pid: 선택된 person_id
        user_id: 로그인 설계사 user_id
        hq_app_url: HQ 앱 URL (딥링크/API 베이스 생성에 사용)
    """
    st.markdown(
        "<div style='background:#eff6ff;padding:7px 12px;border-radius:8px;"
        "font-size:0.8rem;font-weight:900;color:#1e3a8a;border:1px dashed #000;margin-bottom:10px;'>"
        "📊 증권분석 — Raw Data 백오피스 + HQ 정밀 분석 발사대</div>",
        unsafe_allow_html=True,
    )

    if not sel_cust:
        st.info("고객을 먼저 선택해 주세요.")
        return

    from blocks.crm_hq_scan_bridge import render_hq_scan_bridge_links

    render_hq_scan_bridge_links(
        sel_pid=sel_pid or sel_cust.get("person_id", ""),
        user_id=user_id,
        hq_app_url=hq_app_url,
    )

    _an1, _an2 = st.columns([5, 5])

    # ── 좌측: HQ 정밀 분석 발사대 ─────────────────────────────────────────
    with _an1:
        st.markdown(
            "<div style='background:#F8FBFA;border:1px dashed #000;"
            "border-radius:10px;padding:14px;'>",
            unsafe_allow_html=True,
        )
        st.markdown("**🚀 HQ 정밀 분석 발사대**")

        _sector_opts = {
            "KB 7대 보장 분석": "t3",
            "보험금 청구 상담": "t1",
            "실손보험 분석":    "t2",
            "암보험 분석":      "cancer",
            "뇌혈관 분석":      "brain",
            "심장 분석":        "heart",
            "화재보험 분석":    "fire",
            "AI 상담 리포트":   "home",
        }
        _sel_sector_label = st.selectbox(
            "📍 분석 섹터", list(_sector_opts.keys()), key="spa_sector_sel",
        )
        _sel_sector = _sector_opts[_sel_sector_label]

        try:
            from shared_components import build_deeplink_to_hq
            _dl_url = build_deeplink_to_hq(
                cid=sel_cust.get("person_id", ""),
                agent_id=user_id,
                sector=_sel_sector,
                user_id=user_id,
            )
        except Exception:
            _dl_url = f"{hq_app_url}/?gk_sector={_sel_sector}"

        st.markdown(
            f"<div style='text-align:center;padding:12px 0;'>"
            f"<a href='{_dl_url}' target='_blank' "
            f"style='background:#dbeafe;color:#1e3a8a;padding:10px 24px;"
            f"border-radius:8px;font-size:0.9rem;font-weight:900;"
            f"text-decoration:none;border:1px solid #93c5fd;'>"
            f"🚀 {sel_cust.get('name')} → HQ 분석 시작</a></div>",
            unsafe_allow_html=True,
        )

        with st.expander("❓ HQ 앱이 열리지 않는다면?", expanded=False):
            st.caption(f"직접 접속: {hq_app_url}")

        with st.expander("🔌 HQ 증권분석 API (Cloud Run)", expanded=False):
            try:
                from shared_components import get_hq_api_base
                _api_base = get_hq_api_base()
            except Exception:
                _api_base = hq_app_url.rstrip("/") + "/api/v1"
            st.caption(
                f"엔드포인트 베이스: `{_api_base}` — "
                "`HQ_API_URL` 또는 `HQ_APP_URL`+`/api/v1` 환경변수로 설정."
            )
            _hc1, _hc2 = st.columns(2)
            with _hc1:
                if st.button("헬스 확인", key="crm_hq_api_health", use_container_width=True):
                    import json as _hj_h
                    import urllib.request as _uhr_h
                    try:
                        _hu = f"{_api_base.rstrip('/')}/health"
                        with _uhr_h.urlopen(_hu, timeout=12) as _rh:
                            st.json(_hj_h.loads(_rh.read().decode()))
                    except Exception as _he:
                        st.warning(f"연결 실패: {_he}")
            with _hc2:
                if st.button("분석 트리거 (API)", key="crm_hq_api_trig", use_container_width=True):
                    try:
                        from shared_components import request_hq_analysis_trigger
                        _api_res = request_hq_analysis_trigger(
                            person_id=sel_cust.get("person_id", ""),
                            agent_id=user_id,
                            user_id=user_id,
                            sector=_sel_sector,
                        )
                    except Exception as _atre:
                        _api_res = {"ok": False, "error": str(_atre)}
                    if _api_res.get("ok") and _api_res.get("hq_deeplink"):
                        st.success("API 응답 수신 — 아래 링크로 HQ 정밀 분석을 여세요.")
                        _hdl = _api_res["hq_deeplink"]
                        st.markdown(
                            f"<a href='{_hdl}' target='_blank' rel='noopener' "
                            "style='display:inline-block;background:#dbeafe;color:#1e3a8a;"
                            "padding:10px 18px;border-radius:8px;font-weight:900;"
                            "text-decoration:none;border:1px solid #93c5fd;'>"
                            "🚀 HQ 분석 열기 (API)</a>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.error(_api_res)

        st.markdown("</div>", unsafe_allow_html=True)

    # ── 우측: GCS Raw Data 백오피스 ───────────────────────────────────────
    with _an2:
        st.markdown(
            "<div style='background:#F8FBFA;border:1px dashed #000;"
            "border-radius:10px;padding:14px;'>",
            unsafe_allow_html=True,
        )
        st.markdown("**🗂️ GCS 원시 데이터 (Raw Data)**")
        _raw_tab = st.radio(
            "조회",
            ["🧾 기본 정보", "📋 증권 목록", "🔗 관계망"],
            horizontal=True,
            key="spa_raw_tab",
            label_visibility="collapsed",
        )

        # 기본 정보
        if _raw_tab == "🧾 기본 정보":
            _raw_fields = [
                ("이름",         sel_cust.get("name", "")),
                ("person_id",    sel_cust.get("person_id", "")[:16]),
                ("등급",         sel_cust.get("management_tier", "")),
                ("생년(나이대)", sel_cust.get("birth_year", "")),
                ("직업",         sel_cust.get("job", "")),
                ("직업급수",     sel_cust.get("job_grade", "")),
                ("운전유형",     sel_cust.get("driving_type", "")),
                ("이륜차여부",   sel_cust.get("bike_usage", "")),
                ("자동차만기월", sel_cust.get("auto_renewal_month", "")),
                ("화재만기월",   sel_cust.get("fire_renewal_month", "")),
                ("상태",         sel_cust.get("status", "")),
                ("소개자",       sel_cust.get("referrer_name", "")),
                ("updated_at",   str(sel_cust.get("updated_at", ""))[:19]),
            ]
            for _fn, _fv in _raw_fields:
                if _fv:
                    st.markdown(
                        f"<div style='display:flex;justify-content:space-between;"
                        f"padding:4px 8px;border-bottom:1px solid #EAEAEF;"
                        f"font-size:0.8rem;'>"
                        f"<span style='color:#64748b;'>{_fn}</span>"
                        f"<b>{_fv}</b></div>",
                        unsafe_allow_html=True,
                    )

        # 증권 목록
        elif _raw_tab == "📋 증권 목록" and sel_pid:
            try:
                from db_utils import get_person_policies_summary as _du_pol_sum
                _policies_raw = _du_pol_sum(sel_pid)
                if _policies_raw:
                    import pandas as _pd_raw
                    _pol_rows = []
                    for _pr in _policies_raw:
                        _p = _pr.get("policies") or {}
                        _pol_rows.append({
                            "보험사": _p.get("insurance_company", ""),
                            "상품명": _p.get("product_name", ""),
                            "역할":   _pr.get("role", "") or _pr.get("role_type", ""),
                            "보험료": f"{_p.get('premium', 0):,}원" if _p.get("premium") else "-",
                            "계약일": str(_p.get("contract_date", ""))[:10],
                            "만기일": str(_p.get("expiry_date", ""))[:10],
                        })
                    st.dataframe(
                        _pd_raw.DataFrame(_pol_rows),
                        use_container_width=True,
                        height=220,
                    )
                else:
                    st.caption("등록된 증권 없음")
            except Exception as _pr_e:
                st.caption(f"조회 오류: {_pr_e}")

        # 관계망
        elif _raw_tab == "🔗 관계망" and sel_pid:
            try:
                from db_utils import get_person_relationships as _du_rels
                _rels_raw = _du_rels(sel_pid, user_id)
                if _rels_raw:
                    for _rr in _rels_raw:
                        _fn = (_rr.get("from_person") or {}).get("name", "?")
                        _tn = (_rr.get("to_person") or {}).get("name", "?")
                        _rt = _rr.get("relation_type", "")
                        st.markdown(
                            f"<div style='font-size:0.8rem;padding:5px 8px;"
                            f"border-left:3px solid #93c5fd;margin-bottom:4px;'>"
                            f"<b>{_fn}</b> → <span style='color:#1d4ed8;'>{_rt}</span>"
                            f" → <b>{_tn}</b></div>",
                            unsafe_allow_html=True,
                        )
                else:
                    st.caption("등록된 관계망 없음")
            except Exception as _rel_e:
                st.caption(f"조회 오류: {_rel_e}")

        st.markdown("</div>", unsafe_allow_html=True)
