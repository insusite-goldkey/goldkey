# ══════════════════════════════════════════════════════════════════════════════
# [BLOCK] crm_nibo_screen_block.py
# 내보험다보여 — 크롤링 상태 모니터 + 신용정보 동의 UI + HQ 빠른 바로가기
# 원본 위치: crm_app.py SCREEN 3 (_spa_screen == "nibo"), lines 2363–2472
# Cursor 마이그레이션용 독립 블록 (2026-03-24 추출)
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations
import datetime
import base64
import streamlit as st


def _render_hq_context_nudge(hq_app_url: str, person_id: str) -> None:
    """분석 완료 직후 HQ 전문가 모드 유도 카드."""
    _pid = (person_id or "").strip()
    if not _pid:
        return
    _hq_base = (hq_app_url or "http://localhost:8501").rstrip("/")
    _href = f"{_hq_base}/?person_id={_pid}&source=nudge"
    st.markdown(
        "<div style='margin-top:14px;padding:16px 14px;border-radius:14px;"
        "background:linear-gradient(135deg,#fffbeb 0%,#fef3c7 40%,#fde68a 100%);"
        "border:1px solid #f59e0b;'>"
        "<div style='font-size:0.94rem;font-weight:900;color:#92400e;line-height:1.6;'>"
        "심층적인 분석. 전문상담 필요하신가요?</div>"
        "<div style='margin-top:10px;'>"
        f"<a href='{_href}' target='_blank' rel='noopener noreferrer' "
        "style='display:block;text-align:center;text-decoration:none;"
        "padding:12px 10px;border-radius:10px;font-weight:900;color:#fff;"
        "background:linear-gradient(135deg,#b45309 0%,#d97706 50%,#f59e0b 100%);"
        "box-shadow:0 6px 14px rgba(180,83,9,0.25);'>"
        "👉 전문가 모드(HQ) 진입</a></div></div>",
        unsafe_allow_html=True,
    )


def render_crm_nibo_screen(
    sel_cust: dict | None,
    sel_pid: str,
    user_id: str,
    hq_app_url: str = "http://localhost:8501",
) -> None:
    """내보험다보여 스크린 블록.

    Args:
        sel_cust: 선택된 고객 dict (없으면 None)
        sel_pid: 선택된 person_id
        user_id: 로그인 설계사 user_id
        hq_app_url: HQ 앱 URL (딥링크 생성에 사용)
    """
    st.markdown(
        "<div style='background:#eff6ff;padding:7px 12px;border-radius:8px;"
        "font-size:0.8rem;font-weight:900;color:#1e3a8a;border:1px dashed #000;margin-bottom:10px;'>"
        "🌐 내보험다보여 — 신용정보 수집 · 트리니티 분석 파이프라인</div>",
        unsafe_allow_html=True,
    )

    # ── 크롤링 상태 모니터 ─────────────────────────────────────────────────
    if sel_cust:
        try:
            from db_utils import get_crawl_status as _du_crawl_status
            _cs_dict = _du_crawl_status(sel_cust.get("person_id", ""))
            _nibo_crawl = [_cs_dict] if _cs_dict else []
            if _nibo_crawl:
                _cs_n  = _nibo_crawl[0]
                _cst_n = _cs_n.get("status", "idle")
                _css_n_map = {
                    "running": ("background:#fef3c7;border:1px solid #f59e0b;", "⚡ 수집 진행 중..."),
                    "done":    ("background:#dcfce7;border:1px solid #16a34a;", "✅ 수집 완료"),
                    "error":   ("background:#fef2f2;border:1px solid #dc2626;", "❌ 수집 오류"),
                    "idle":    ("background:#F8FBFA;border:1px solid #EAEAEF;", "⏸ 대기 중"),
                }
                _css_n, _lbl_n = _css_n_map.get(_cst_n, _css_n_map["idle"])
                _ts_n = str(_cs_n.get("updated_at", ""))[:16].replace("T", " ")
                st.markdown(
                    f"<div style='{_css_n}border-radius:8px;padding:8px 14px;"
                    f"font-size:0.8rem;margin-bottom:10px;"
                    f"display:flex;justify-content:space-between;align-items:center;'>"
                    f"<span style='font-weight:900;'>📡 HQ 내보험다보여 수집 상태: {_lbl_n}</span>"
                    f"<span style='color:#6b7280;font-size:0.74rem;'>{_ts_n}</span></div>",
                    unsafe_allow_html=True,
                )
                if _cst_n == "error" and _cs_n.get("error_msg"):
                    st.caption(f"오류 내용: {str(_cs_n.get('error_msg', ''))[:80]}")
            else:
                st.markdown(
                    "<div style='background:#F8FBFA;border:1px solid #EAEAEF;border-radius:8px;"
                    "padding:8px 14px;font-size:0.8rem;margin-bottom:10px;color:#6b7280;'>"
                    "📡 HQ 수집 상태: 이력 없음 — 아래에서 분석을 시작하세요.</div>",
                    unsafe_allow_html=True,
                )
        except Exception:
            pass

    # ── 고객 미선택 ────────────────────────────────────────────────────────
    if not sel_cust:
        st.info("고객을 먼저 선택해 주세요.")
        return

    # ── 신용정보 조회 동의 미완료 ─────────────────────────────────────────
    from shared_components import consent_get, consent_set, ss_set_ns

    if not consent_get("nibo_consent_agreed", False):
        st.markdown(
            "<div style='background:#fef9c3;border:1px dashed #fbbf24;border-radius:8px;"
            "padding:6px 12px;margin-bottom:8px;font-size:0.8rem;color:#78350f;font-weight:700;'>"
            "🔐 신용정보 조회 동의 후 이용 가능합니다.</div>",
            unsafe_allow_html=True,
        )
        with st.popover("📋 신용정보 조회 안내 전문 보기", use_container_width=True):
            try:
                from shared_components import _NIBO_CONSENT_HTML as _nibo_html_v
                st.markdown(_nibo_html_v, unsafe_allow_html=True)
            except Exception:
                st.markdown("신용정보의 이용 및 보호에 관한 법률 제32조에 따른 안내문입니다.")
        _nibo_inline_agree = st.checkbox(
            "✅ **[즉석 동의]** '내보험다보여' 연동 및 신용정보 조회·분석에 동의합니다 (신용정보법 제32조)",
            value=False,
            key="crm_nibo_inline_agree",
        )
        if _nibo_inline_agree:
            try:
                from shared_components import _NIBO_CONSENT_VERSION as _nibo_ver
            except Exception:
                _nibo_ver = "2026-03-16-v1"
            consent_set("nibo_consent_agreed", True)
            _ts = datetime.datetime.now().isoformat()
            ss_set_ns("consent", "nibo_consent_version", _nibo_ver)
            ss_set_ns("consent", "nibo_consent_timestamp", _ts)
            st.session_state["nibo_consent_version"] = _nibo_ver
            st.session_state["nibo_consent_timestamp"] = _ts
            st.success("✅ 동의 완료! 트리니티 분석이 활성화됩니다.")
            st.rerun()
        return

    # ── 동의 완료 — HQ 안내 ────────────────────────────────────────────────
    st.markdown(
        "<div style='background:#eff6ff;border:1px dashed #000;"
        "border-radius:10px;padding:12px 14px;margin-bottom:10px;'>"
        "<div style='font-size:0.85rem;font-weight:900;color:#1e3a8a;margin-bottom:6px;'>"
        "✅ 내보험다보여 연동 동의 완료</div>"
        "<div style='font-size:0.8rem;color:#374151;line-height:1.7;'>"
        "📊 JSON 데이터 주입 및 트리니티 정밀 분석은 <b>HQ 앱 → 내보험다보여 센터(GK-SEC-10)</b>에서 실행하세요.<br>"
        "<span style='font-size:0.74rem;color:#6b7280;'>"
        "HQ에서 내보험다보여 API 응답 JSON을 직접 붙여넣기 → 담보 파싱 → DB 저장까지 원클릭 처리됩니다."
        "</span></div></div>",
        unsafe_allow_html=True,
    )

    # ── HQ 빠른 바로가기 (5버튼) ───────────────────────────────────────────
    st.markdown("---")
    st.markdown("**빠른 HQ 바로가기**")
    _quick_cols = st.columns(5)
    _quick_links = [
        ("📥 내보험다보여\nJSON 주입", "gk_sec10"),
        ("🛡️ KB7 분석",               "t3"),
        ("📋 실손 분석",               "t2"),
        ("🎗️ 암보험",                  "cancer"),
        ("🏠 화재보험",                "fire"),
    ]
    for _qi, (_ql, _qs) in enumerate(_quick_links):
        with _quick_cols[_qi]:
            try:
                from shared_components import build_deeplink_to_hq
                _q_url = build_deeplink_to_hq(
                    cid=sel_pid or sel_cust.get("person_id", ""),
                    agent_id=user_id,
                    sector=_qs,
                    user_id=user_id,
                )
            except Exception:
                _q_url = f"{hq_app_url}/?gk_sector={_qs}"
            st.markdown(
                f'<a href="{_q_url}" target="_blank" style="display:block;text-align:center;'
                f'background:#dbeafe;color:#1e3a8a;border-radius:8px;padding:8px;'
                f'font-size:0.82rem;font-weight:900;text-decoration:none;'
                f'border:1px solid #93c5fd;">{_ql}</a>',
                unsafe_allow_html=True,
            )

    # ── HQ 스캔 사령부 (통합스캔·증권·청구·장해) ───────────────────────────
    from blocks.crm_hq_scan_bridge import render_hq_scan_bridge_links

    render_hq_scan_bridge_links(
        sel_pid=sel_pid or sel_cust.get("person_id", ""),
        user_id=user_id,
        hq_app_url=hq_app_url,
    )

    # ── 디바이스 핸드오프 (태블릿↔고객폰) + 동의 기반 카카오 발송 게이트 ───────
    st.markdown("---")
    st.markdown("**디바이스 핸드오프 (Cloud Run HEAD)**")
    _pid = sel_pid or sel_cust.get("person_id", "")
    _skey = f"crm_handoff_session__{_pid}"
    _sess = st.session_state.get(_skey, "")
    _c1, _c2, _c3, _c4 = st.columns([1, 1, 1, 1.2])
    with _c1:
        if st.button("📲 동의 요청 세션 생성", key=f"crm_handoff_create_{_pid}", use_container_width=True):
            from head_api_client import create_handoff_session

            with st.spinner("세션 생성 중..."):
                _r = create_handoff_session(user_id=user_id, person_id=_pid, channel="qr")
            if _r.get("ok") and isinstance(_r.get("session"), dict):
                _sess = _r["session"].get("session_id", "")
                st.session_state[_skey] = _sess
                st.success(f"세션 생성 완료: {_sess[:8]}…")
            else:
                st.warning(f"세션 생성 실패: {_r}")
    with _c2:
        if st.button("🔄 인증 상태 확인", key=f"crm_handoff_poll_{_pid}", use_container_width=True):
            if not _sess:
                st.info("먼저 동의 요청 세션을 생성하세요.")
            else:
                from head_api_client import get_handoff_status

                with st.spinner("인증 상태 조회 중..."):
                    _s = get_handoff_status(_sess)
                st.session_state[f"crm_handoff_status__{_pid}"] = _s
    with _c3:
        if st.button("💬 AI 보고서 발송 요청", key=f"crm_kakao_gate_{_pid}", use_container_width=True):
            from head_api_client import request_kakao_send
            _raw_phone = str(sel_cust.get("contact", "") or "")
            try:
                from shared_components import decrypt_pii as _dec_phone
                _raw_phone = _dec_phone(_raw_phone)
            except Exception:
                pass

            # [GP-SEC §3] 메시지 텍스트 내 고객명 마스킹
            try:
                from shared_components import mask_name as _mn_nibo
                _nibo_masked_name = _mn_nibo(sel_cust.get("name", "고객"))
            except Exception:
                _nibo_masked_name = sel_cust.get("name", "고객")

            st.session_state[f"crm_kakao_send_state__{_pid}"] = "sending"
            with st.spinner("발송 중..."):
                _k = request_kakao_send(
                    user_id=user_id,
                    person_id=_pid,
                    report_type="ai_report",
                    payload={
                        "phone": _raw_phone,
                        "message": f"{_nibo_masked_name}님 AI 보고서가 도착했습니다.",
                    },
                )
            st.session_state[f"crm_kakao_req__{_pid}"] = _k
            st.session_state[f"crm_kakao_send_state__{_pid}"] = "done"
            if _k.get("ok"):
                st.toast("카카오 발송 완료", icon="✅")
            else:
                st.toast("카카오 발송 실패", icon="⚠️")
    with _c4:
        _sst = st.session_state.get(f"crm_kakao_send_state__{_pid}", "")
        if _sst == "sending":
            st.caption("발송 중...")
        elif _sst == "done":
            st.caption("발송 완료")

    _s = st.session_state.get(f"crm_handoff_status__{_pid}", {})
    if isinstance(_s, dict) and _s:
        _session = _s.get("session", {}) if isinstance(_s.get("session"), dict) else {}
        _st = _session.get("status", "-")
        st.caption(
            f"handoff 상태: {_st} · info동의={_session.get('consent_info_lookup', False)} "
            f"· kakao동의={_session.get('consent_kakao_report', False)}"
        )
    _auto = st.checkbox(
        "자동 폴링(3초 간격, 완료 시 자동 중지)",
        value=bool(st.session_state.get(f"crm_handoff_auto__{_pid}", False)),
        key=f"crm_handoff_auto_cb_{_pid}",
    )
    st.session_state[f"crm_handoff_auto__{_pid}"] = _auto

    _poll_box = st.container()
    if _auto and _sess:
        # fragment 단위만 재실행하여 전체 화면 깜빡임 최소화
        @st.fragment(run_every="3s")
        def _handoff_poll_fragment() -> None:
            from head_api_client import fetch_unified_report, get_handoff_status

            _s2 = get_handoff_status(_sess)
            st.session_state[f"crm_handoff_status__{_pid}"] = _s2
            _s2_session = _s2.get("session", {}) if isinstance(_s2, dict) else {}
            if isinstance(_s2_session, dict) and _s2_session.get("status") == "completed":
                st.session_state[f"crm_handoff_auto__{_pid}"] = False
                st.session_state[f"crm_unified_report__{_pid}"] = fetch_unified_report(
                    user_id=user_id, person_id=_pid
                )
                st.success("✅ 고객 폰 인증 완료 — 결과 동기화됨")
            else:
                st.caption("자동 폴링 중... (3초)")

        with _poll_box:
            _handoff_poll_fragment()
    _k = st.session_state.get(f"crm_kakao_req__{_pid}", {})
    if isinstance(_k, dict) and _k:
        if _k.get("ok"):
            st.success(f"카카오 발송 큐 등록됨: event={_k.get('event_id', '-')}")
        else:
            st.warning(f"카카오 발송 거절/실패: {_k.get('error', _k)}")

    # ── 스캔 업로드 후 재분석 트리거 + 통합 보고서 섹션 필터 뷰어 ───────────────
    st.markdown("---")
    st.markdown("**추가계약 스캔 업로드 → 통합 재분석 (Cloud Run HEAD)**")
    st.markdown(
        "<div style='background:#fff7ed;border:1px solid #fdba74;border-radius:10px;"
        "padding:10px 12px;margin:6px 0 10px 0;'>"
        "<div style='font-size:0.82rem;font-weight:900;color:#9a3412;'>"
        "📸 증권을 평평한 곳에 두고, 형광등 반사가 없도록 촬영해 주세요.</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    _u1, _u2 = st.columns([1, 1])
    with _u1:
        _cam = st.camera_input("실시간 촬영 (모바일/태블릿)", key=f"crm_scan_camera_{_pid}")
    with _u2:
        st.caption("파일 업로드와 실시간 촬영을 함께 사용할 수 있습니다.")
    _files = st.file_uploader(
        "파일 선택 업로드 (PDF/JPG/PNG)",
        type=["pdf", "jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key=f"crm_scan_upload_{_pid}",
    )
    if _cam is not None:
        try:
            from head_api_client import preprocess_scan_image

            with st.spinner("Image Guard 전처리 중..."):
                _cam_res = preprocess_scan_image(
                    user_id=user_id,
                    person_id=_pid,
                    image_bytes=_cam.getvalue(),
                    source="camera",
                    filename=getattr(_cam, "name", "camera_capture.jpg"),
                )
            st.session_state[f"crm_scan_guard_cam__{_pid}"] = _cam_res
        except Exception as _cam_e:
            st.session_state[f"crm_scan_guard_cam__{_pid}"] = {"ok": False, "error": str(_cam_e)}

    _cam_guard = st.session_state.get(f"crm_scan_guard_cam__{_pid}", {})
    if isinstance(_cam_guard, dict) and _cam_guard:
        if _cam_guard.get("ok"):
            st.success(
                f"✅ Image Guard 통과 (품질점수 {_cam_guard.get('quality_score', 0):.1f})"
            )
            _pb64 = _cam_guard.get("processed_image_b64", "")
            if _pb64:
                try:
                    st.image(base64.b64decode(_pb64), caption="전처리 결과 (Auto-crop + 반사/그림자 보정)")
                except Exception:
                    pass
        elif _cam_guard.get("status") == "retry_required":
            st.warning(_cam_guard.get("guide", "이미지 품질이 낮습니다. 다시 촬영해 주세요."))
        else:
            st.warning(f"전처리 실패: {_cam_guard.get('error', _cam_guard)}")
    _fcols = st.columns([1, 1, 1, 1])
    with _fcols[0]:
        if st.button("🔁 재분석 트리거", key=f"crm_reanalyze_btn_{_pid}", use_container_width=True):
            from head_api_client import trigger_reanalyze_report, fetch_unified_report

            _names = [getattr(f, "name", "file") for f in (_files or [])]
            if isinstance(_cam_guard, dict) and _cam_guard.get("ok"):
                _names.append("camera_capture_processed.png")
            with st.spinner("재분석 요청 중..."):
                _rq = trigger_reanalyze_report(
                    user_id=user_id,
                    person_id=_pid,
                    source="scan_upload",
                    scan_file_names=_names,
                )
                _ur = fetch_unified_report(user_id=user_id, person_id=_pid)
            st.session_state[f"crm_unified_reanalyze__{_pid}"] = _rq
            st.session_state[f"crm_unified_report__{_pid}"] = _ur
    with _fcols[1]:
        if st.button("📦 통합 보고서 새로고침", key=f"crm_unified_refresh_{_pid}", use_container_width=True):
            from head_api_client import fetch_unified_report

            with st.spinner("통합 보고서 조회 중..."):
                st.session_state[f"crm_unified_report__{_pid}"] = fetch_unified_report(
                    user_id=user_id,
                    person_id=_pid,
                )
    _vr = st.session_state.get(f"crm_unified_report__{_pid}", {})
    if isinstance(_vr, dict) and _vr.get("ok"):
        _sec = _vr.get("sections", {}) if isinstance(_vr.get("sections"), dict) else {}
        st.caption(f"보고서 버전: {_vr.get('version', '-')} · 업데이트: {_vr.get('updated_at', '-')}")
        with _fcols[2]:
            _show_kb = st.toggle("KB 섹션", value=True, key=f"crm_show_kb_{_pid}")
        with _fcols[3]:
            _show_tri = st.toggle("트리니티 섹션", value=True, key=f"crm_show_tri_{_pid}")
        if _show_kb:
            with st.expander("KB 분석 섹션", expanded=False):
                st.json(_sec.get("kb"))
        if _show_tri:
            with st.expander("트리니티 섹션", expanded=False):
                st.json(_sec.get("trinity"))
        if str(_vr.get("status", "")).lower() == "ready":
            _render_hq_context_nudge(hq_app_url=hq_app_url, person_id=_pid)
