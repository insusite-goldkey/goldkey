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

    # ── [통합스캔 모듈] 5:5 레이아웃 — 좌측(스캔 버튼), 우측(목록+AI요약) ──────────
    st.markdown(
        "<div style='font-size:clamp(11px,1.6vw,13px);font-weight:700;color:#475569;margin:8px 0 4px;'>"
        "📷 통합 스캔 모듈 (증권분석, 보험금청구, 의무기록, 법무기록 등)</div>",
        unsafe_allow_html=True,
    )
    _scan_l, _scan_r = st.columns([1, 1], gap="medium")
    
    with _scan_l:
        st.markdown(
            "<div style='font-size:clamp(11px,1.5vw,13px);font-weight:700;color:#1e40af;margin:4px 0;'>"
            "🔍 스캔 시작</div>",
            unsafe_allow_html=True,
        )
        if not _bridge_pid:
            st.caption("고객을 표에서 선택하면 HQ 스캔 사령부로 이동할 수 있습니다.")
        else:
            # HQ 스캔 4종 버튼 (세로 배치)
            _HQ_SCAN_SECTORS = (
                ("🔬 통합 스캔 허브", "scan_hub"),
                ("📄 보험증권 분석", "policy_scan"),
                ("🧾 청구 스캐너", "claim_scanner"),
                ("♿ 장해 산출", "disability"),
            )
            
            # 보험사기 신고 센터 링크 (최상단 배치)
            st.markdown(
                '<a href="https://www.fss.or.kr" target="_blank" rel="noopener noreferrer" '
                'style="display:block;text-align:center;background:#fee2e2;color:#991b1b;'
                "border:1px solid #fca5a5;border-radius:10px;padding:10px 8px;margin:4px 0 8px;"
                'font-size:clamp(11px,1.6vw,13px);font-weight:800;text-decoration:none;">'
                "🚨 보험사기 신고 센터 (FSS) ☎️ 1332</a>",
                unsafe_allow_html=True,
            )
            
            for _lbl, _sector in _HQ_SCAN_SECTORS:
                try:
                    from shared_components import build_deeplink_to_hq
                    _url = build_deeplink_to_hq(
                        cid=_bridge_pid,
                        agent_id=user_id,
                        sector=_sector,
                        user_id=user_id,
                    )
                except Exception:
                    _url = f"{hq_app_url.rstrip('/')}/?gk_sector={_sector}&gk_cid={_bridge_pid}"
                st.markdown(
                    f'<a href="{_url}" target="_blank" rel="noopener noreferrer" '
                    'style="display:block;text-align:center;background:#ecfdf5;color:#065f46;'
                    "border:1px solid #6ee7b7;border-radius:10px;padding:10px 8px;margin:4px 0;"
                    'font-size:clamp(11px,1.6vw,13px);font-weight:800;text-decoration:none;">'
                    f"{_lbl}</a>",
                    unsafe_allow_html=True,
                )
    
    with _scan_r:
        st.markdown(
            "<div style='font-size:clamp(11px,1.5vw,13px);font-weight:700;color:#1e40af;margin:4px 0;'>"
            "📋 스캔 목록 & AI 요약</div>",
            unsafe_allow_html=True,
        )
        _scans = st.session_state.get("crm_cc_scans", [])
        _ai_summary = st.session_state.get("crm_cc_scan_ai_summary", "")
        
        if not _scans and not _ai_summary:
            st.caption("최근 스캔 기록이 없습니다. 좌측 버튼으로 HQ에서 스캔하세요.")
        else:
            # 스캔 목록 (최대 5건)
            if _scans:
                _scan_box = (
                    "<div style='font-size:clamp(10px,1.4vw,12px);font-weight:700;color:#334155;margin:4px 0 2px;'>"
                    "최근 스캔 (최대 5건)</div>"
                    "<div style='max-height:5rem;overflow-y:auto;font-size:clamp(10px,1.4vw,12px);"
                    "line-height:1.4;padding:4px;border:1px dashed #cbd5e1;border-radius:6px;margin-bottom:6px;'>"
                )
                for _i, _s in enumerate(_scans[-5:][::-1]):
                    _scan_box += f"<div>{_i+1}. {_s}</div>"
                _scan_box += "</div>"
                st.markdown(_scan_box, unsafe_allow_html=True)
            
            # AI 요약 분석 (7줄 스크롤)
            if _ai_summary:
                st.markdown(
                    "<div style='font-size:clamp(10px,1.4vw,12px);font-weight:700;color:#334155;margin:4px 0 2px;'>"
                    "🤖 AI 요약 분석</div>",
                    unsafe_allow_html=True,
                )
                st.text_area(
                    "scan_ai_summary",
                    value=_ai_summary,
                    height=140,
                    disabled=True,
                    key="crm_cc_scan_ai_summary_box",
                    label_visibility="collapsed",
                )
            else:
                st.caption("AI 요약은 HQ 스캔 완료 후 자동 생성됩니다.")
    
    st.markdown("<hr style='border:none;border-top:1px solid #e2e8f0;margin:12px 0;'>", unsafe_allow_html=True)
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

                _tri_result = calculate_trinity_metrics(int(_nhi))
                st.session_state["crm_cc_tri"] = _tri_result
                
                # ── [박스1] 트리니티 보험금 산출 요약 자동 생성 ──────────────────
                _monthly = _tri_result.get('monthly_income', 0)
                _daily = _tri_result.get('daily_value', 0)
                _box1_lines = [
                    f"✅ 가처분 월소득(추정): {_monthly:,}원",
                    f"✅ 일실수입(일당): {_daily:,}원",
                    f"━━━━━━━━━━━━━━━━━━━━━━",
                    f"📊 트리니티 5대 필수 보장 산출 기준",
                    f"━━━━━━━━━━━━━━━━━━━━━━",
                    f"1. 암 진단비: {_monthly * 24:,}원 (2년 필수준비기간)",
                    f"2. 치매 간병비: 실비형 필수 (월 200만원 수준)",
                    f"3. 연금: 현재 소득 80~100% 유지 목표",
                    f"4. 상해후유장해: 300,000,000원 ~ 500,000,000원",
                    f"5. 사망보장: 최소 100,000,000원 이상",
                ]
                st.session_state["crm_cc_tri_box1"] = "\n".join(_box1_lines)
                
                # ── [박스2] HQ 연동 AI 증권분석 (KB손보 기준 비교) ──────────────
                _box2_lines = [
                    f"📋 트리니티 vs KB손보 기준 비교표",
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    f"구분          | 트리니티 2년 | KB손보 기준",
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    f"암 진단비     | {_monthly * 24:,}원 | 50,000,000원",
                    f"뇌졸중        | {_monthly * 24:,}원 | 30,000,000원",
                    f"급성심근경색  | {_monthly * 24:,}원 | 30,000,000원",
                    f"수술비        | {_daily * 365:,}원 | 10,000,000원",
                    f"입원일당      | {_daily:,}원/일 | 100,000원/일",
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    f"💡 트리니티는 고객 소득 기반 맞춤 설계",
                    f"💡 KB손보는 업계 표준 권장 금액",
                ]
                st.session_state["crm_cc_hq_analysis"] = "\n".join(_box2_lines)
                
                st.success("✅ AI 분석 완료! 우측 박스1, 박스2를 확인하세요.")
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
        
        # ── [트리니티 요약 버튼 삭제] 하단 AI 트리니티 지식 박스에서 설명하므로 불필요 ──
        if st.button("🌐 내보험다보여", key="crm_cc_btn_nibo", use_container_width=True):
            if not _consent:
                st.warning("동의 후 이용 가능합니다.")
            elif not _bridge_pid:
                st.warning("고객을 표에서 먼저 선택하세요.")
            else:
                st.session_state["crm_list_inline_panel"] = "nibo"
                # DOM 에러 방지: rerun 전 플래그 설정
                if not st.session_state.get("_rerun_pending"):
                    st.session_state["_rerun_pending"] = True
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
                    # DOM 에러 방지: rerun 전 플래그 설정
                    if not st.session_state.get("_rerun_pending"):
                        st.session_state["_rerun_pending"] = True
                        st.rerun()
        with _b4:
            if st.button("💬 카카오 알림톡·문자", key="crm_cc_btn_kakao", use_container_width=True):
                if not _bridge_pid:
                    st.warning("고객을 표에서 먼저 선택하세요.")
                else:
                    st.session_state["crm_spa_mode"] = "customer"
                    st.session_state["crm_spa_screen"] = "kakao"
                    # DOM 에러 방지: rerun 전 플래그 설정
                    if not st.session_state.get("_rerun_pending"):
                        st.session_state["_rerun_pending"] = True
                        st.rerun()
        with _b5:
            if st.button("📱 핸드폰 증권 스캔", key="crm_cc_btn_settings", use_container_width=True):
                st.session_state["crm_spa_mode"] = "customer"
                st.session_state["crm_spa_screen"] = "settings"
                # DOM 에러 방지: rerun 전 플래그 설정
                if not st.session_state.get("_rerun_pending"):
                    st.session_state["_rerun_pending"] = True
                    st.rerun()

    with _c_r:
        st.markdown(
            "<div style='font-size:clamp(13px,2vw,17px);font-weight:900;color:#0f172a;'>"
            "AI 증권분석 보고서</div>",
            unsafe_allow_html=True,
        )
        _tri_box1_text = st.session_state.get(
            "crm_cc_tri_box1",
            "좌측 '🤖 AI 분석 실행' 버튼을 클릭하여 분석을 시작하세요.",
        )
        st.markdown(
            "<div style='font-size:clamp(11px,1.5vw,13px);font-weight:700;color:#334155;"
            "margin:6px 0 4px;'>박스 1 · 트리니티 보험금 산출 요약</div>",
            unsafe_allow_html=True,
        )
        st.text_area(
            "tri_box",
            value=_tri_box1_text,
            height=240,
            disabled=True,
            key="crm_cc_tri_box",
            label_visibility="collapsed",
        )
        _hq_txt = st.session_state.get(
            "crm_cc_hq_analysis",
            "좌측 '🤖 AI 분석 실행' 버튼을 클릭하여 분석을 시작하세요.",
        )
        st.markdown(
            "<div style='font-size:clamp(11px,1.5vw,13px);font-weight:700;color:#334155;"
            "margin:8px 0 4px;'>박스 2 · HQ 연동 AI 증권분석</div>",
            unsafe_allow_html=True,
        )
        st.text_area(
            "hq_box",
            value=_hq_txt,
            height=240,
            disabled=True,
            key="crm_cc_hq_box",
            label_visibility="collapsed",
        )
