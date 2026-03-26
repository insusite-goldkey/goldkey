# ══════════════════════════════════════════════════════════════════════════════
# [BLOCK] crm_trinity_block.py
# 트리니티 가처분 소득 산출기 + AI 가입결과 보고서 + 카카오 발송
# 원본 위치: crm_app.py contact screen RIGHT PANE (섹션 A + 섹션 B)
# Cursor 마이그레이션용 독립 블록 (2026-03-24 추출)
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations
import streamlit as st


def render_crm_trinity_block(
    sel_cust: dict,
    sel_pid: str,
    user_id: str,
    ks_render_send_ui=None,
    kakao_sender_ok: bool = False,
    hq_app_url: str = "http://localhost:8501",
) -> None:
    """트리니티 산출기 블록.

    Args:
        sel_cust: 선택된 고객 dict (customers 테이블 row)
        sel_pid: person_id
        user_id: 로그인 설계사 user_id
        ks_render_send_ui: kakao_sender.render_send_ui 함수 (없으면 None)
        kakao_sender_ok: kakao_sender 모듈 로드 성공 여부
    """
    _tri_sess_key = f"crm_trinity_res_{sel_pid}"

    def _render_hq_context_nudge() -> None:
        """[Context Transfer] 상담 데이터를 Context 객체에 담아 HQ로 인라인 링크 이전."""
        _pid = (sel_pid or "").strip()
        if not _pid:
            return

        _tri_snapshot = dict(st.session_state.get(_tri_sess_key) or {})
        _context_payload: dict = {
            "source":        "crm_trinity",
            "person_id":     _pid,
            "customer": {
                "name":            sel_cust.get("name", ""),
                "management_tier": sel_cust.get("management_tier", 3),
                "status":          sel_cust.get("status", ""),
                "risk_note":       sel_cust.get("risk_note", ""),
                "job":             sel_cust.get("job", ""),
                "monthly_premium": sel_cust.get("monthly_premium", 0),
                "contract_count":  sel_cust.get("contract_count", 0),
            },
            "trinity": _tri_snapshot,
            "agent_id": user_id,
            "transferred_at": __import__("datetime").datetime.utcnow().isoformat(),
        }

        try:
            from shared_components import build_context_transfer_to_hq as _build_ctx_url
            from db_utils import save_consultation_context as _save_ctx
            _ctx_id = _save_ctx(
                person_id=_pid,
                agent_id=user_id,
                context_data=_context_payload,
            )
            _href = _build_ctx_url(
                user_id=user_id,
                person_id=_pid,
                context_id=_ctx_id,
                sector="t3",
            )
        except Exception:
            _hq_base = (hq_app_url or "http://localhost:8501").rstrip("/")
            _href = f"{_hq_base}/?gk_cid={_pid}&gk_sector=t3"

        st.markdown(
            f"<div style='margin-top:16px;padding:10px 0 4px;'>"
            f"<a href='{_href}' target='_blank' rel='noopener noreferrer' "
            f"style='font-size:clamp(12px,1.8vw,14px);color:#1e40af;font-weight:700;"
            f"text-decoration:none;letter-spacing:-0.01em;"
            f"border-bottom:1.5px solid rgba(30,64,175,0.4);padding-bottom:1px;'>"
            f"전문적 상담이 필요하십니까? &#10145;"
            f"</a>"
            f"<span style='font-size:clamp(10px,1.4vw,11px);color:#94a3b8;"
            f"margin-left:8px;'>상담 데이터가 HQ로 자동 이전됩니다</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # ── [섹션 A] 상담 브리핑 카드 ──────────────────────────────────────────
    st.markdown(
        "<div style='background:#eff6ff;border:1px solid #bfdbfe;"
        "border-radius:12px;padding:10px 14px;margin-bottom:8px;'>"
        "<div style='font-size:0.82rem;font-weight:900;color:#1e3a8a;"
        "border-bottom:2px solid #bfdbfe;padding-bottom:4px;margin-bottom:8px;'>"
        "📊 섹션 A — 상담 브리핑</div>",
        unsafe_allow_html=True,
    )
    _a_items = [
        ("충 월납보험료",  f"{sel_cust.get('monthly_premium', 0):,.0f}원"),
        ("유지 계약수",    f"{sel_cust.get('contract_count', 0)}건"),
        ("관리등급",       f"Tier {sel_cust.get('management_tier', 3)}"),
        ("주요 리스크",    " ".join(filter(None, [
            str(sel_cust.get("risk_note", "")),
            str(sel_cust.get("driving_status", "")),
        ]))),
    ]
    for _ak, _av in _a_items:
        st.markdown(
            f"<div style='display:flex;justify-content:space-between;"
            f"font-size:0.78rem;padding:2px 0;border-bottom:1px dotted #dbeafe;'>"
            f"<span style='color:#64748b;'>{_ak}</span>"
            f"<span style='font-weight:700;color:#1e293b;'>{_av}</span></div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    # ── [섹션 B] 트리니티 가처분 소득 산출기 ──────────────────────────────
    st.markdown(
        "<div style='background:#FEF3C7;border:1px solid #f59e0b;"
        "border-radius:8px;padding:10px 14px;margin-bottom:6px;'>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div style='font-size:0.82rem;font-weight:900;color:#92400e;"
        "border-bottom:2px solid #fbbf24;padding-bottom:4px;margin-bottom:10px;'>"
        "💡 섹션 B — 트리니티 가처분 소득 산출기 (HQ 동일 공식)</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div style='font-size:0.78rem;font-weight:900;color:#78350f;"
        "margin-bottom:6px;line-height:1.45;word-break:keep-all;'>"
        "💰 월 건강보험료 납부액 입력"
        "<br><span style='font-weight:500;font-size:0.72rem;color:#92400e;'>"
        "(가처분 소득 산출 &amp; 트리니티 산출 기초)</span></div>",
        unsafe_allow_html=True,
    )
    _nhis_init = int(st.session_state.get(f"crm_nhis__{sel_pid}", 0))
    _tri_ic, _tri_bc = st.columns([3, 2])
    with _tri_ic:
        _nhis_val = st.number_input(
            "월 건강보험료(원)", min_value=0, max_value=2_000_000,
            value=_nhis_init, step=10_000,
            key=f"crm_nhis_inp_{sel_pid}", label_visibility="collapsed",
        )
        st.caption("직장인: 보수월액×3.545% (개인부담)  |  지역가입자: 부과점수×208.4원")
    with _tri_bc:
        st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)
        if st.button(
            "🚀 AI 분석 필요 보험가액 산출 (트리니티 산출법)",
            key=f"crm_tri_calc_{sel_pid}",
        ):
            if _nhis_val > 0:
                from shared_components import calculate_trinity_metrics as _calc_tri
                _tm = _calc_tri(_nhis_val)
                st.session_state[_tri_sess_key] = {
                    "nhis":                 _nhis_val,
                    "monthly":              _tm["monthly_income"],
                    "daily":                _tm["daily_value"],
                    "gap_injury":           _tm["gap_injury"],
                    "gap_disease":          _tm["gap_disease"],
                    "disability_cov_total": _tm["disability_cov_total"],
                    "disability_cov_min":   _tm["disability_cov_min"],
                    "stroke_18":            _tm["stroke_need"],
                    "dementia_6":           int(_tm["monthly_income"] * 6),
                    "cancer_min":           _tm["cancer_min"],
                    "cancer_rec":           _tm["cancer_rec"],
                    "annual":               _tm["gross_annual"],
                }
                st.session_state[f"crm_nhis__{sel_pid}"] = _nhis_val
                # [GP-IMMORTAL §3] trinity 결과 즉시 Supabase 영구 보존
                try:
                    from db_utils import upsert_analysis_report as _u_ar
                    _u_ar(
                        person_id=sel_pid,
                        agent_id=user_id,
                        analysis_data=st.session_state[_tri_sess_key],
                        nhis_premium=_nhis_val,
                    )
                except Exception:
                    pass
            else:
                st.warning("월 건강보험료를 입력해 주세요.")

    # ── 산출 결과 카드 ──────────────────────────────────────────────────────
    _tri_res = st.session_state.get(_tri_sess_key)
    if _tri_res:
        st.markdown(
            "<div style='background:#eff6ff;border:1px solid #bfdbfe;"
            "border-radius:8px;padding:10px 14px;margin-top:10px;'>"
            "<div style='font-size:0.78rem;font-weight:900;color:#1e3a8a;"
            "border-bottom:1px solid #bfdbfe;padding-bottom:4px;margin-bottom:8px;'>"
            "🧠 AI 가입 결과 보고서 요약</div>",
            unsafe_allow_html=True,
        )
        _res_rows = [
            ("필요 월 소득",  f"{_tri_res['monthly']:,.0f}원"),
            ("일일 가치",     f"{_tri_res['daily']:,.0f}원"),
            ("상해 입원일당", f"{_tri_res['gap_injury']:,.0f}원"),
            ("질병 입원일당", f"{_tri_res['gap_disease']:,.0f}원"),
            ("뇌혈줘(18M)",   f"{_tri_res['stroke_18']:,.0f}원"),
            ("암 최소",        f"{_tri_res['cancer_min']:,.0f}원"),
            ("암 권장",        f"{_tri_res['cancer_rec']:,.0f}원"),
        ]
        _r1, _r2 = st.columns(2)
        for _ri2, (_rlbl, _rval) in enumerate(_res_rows):
            with [_r1, _r2][_ri2 % 2]:
                st.markdown(
                    f"<div style='font-size:0.76rem;padding:3px 0;"
                    f"border-bottom:1px dotted #bfdbfe;'>"
                    f"<span style='color:#64748b;'>{_rlbl}</span>"
                    f"<b style='color:#1e3a8a;margin-left:4px;'>{_rval}</b></div>",
                    unsafe_allow_html=True,
                )
        # 후유장해 2-Track 카드
        st.markdown(
            "<div style='grid-column:1/-1;background:rgba(5,150,105,0.07);"
            "border:1.5px solid #6ee7b7;border-radius:8px;padding:8px 12px;"
            "margin-top:8px;font-size:0.76rem;'>"
            "<b style='color:#065f46;'>⑤ 후유장해(3%이상) — 2-Track 산출</b><br>"
            f"<span style='color:#dc2626;font-weight:900;'>"
            f"⚠️ 총 필요금액: {_tri_res['disability_cov_total']:,.0f}원</span><br>"
            f"<span style='color:#059669;font-weight:900;'>"
            f"🛡️ 산재보험 적용 시 최소 대비: {_tri_res['disability_cov_min']:,.0f}원</span>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.caption(
            "※ 산출 근거: 장해율 10% 발생에 따른 직장 상실 리스크(2배수) 반영. "
            "산재보험 최소 대비액은 10% 장해(생산직 기준) 시 평균 보상일수인 176일을 공제하여 "
            "산출한 순수 공백기(189일) 기준입니다."
        )
        st.markdown("</div>", unsafe_allow_html=True)

        # HQ 상세 상담 링크
        try:
            from shared_components import build_deeplink_to_hq
            _hq_detail_url = build_deeplink_to_hq(
                cid=sel_pid, agent_id=user_id, sector="t3", user_id=user_id,
            )
            st.markdown(
                f"<a href='{_hq_detail_url}' target='_blank' style='"
                "display:inline-block;background:#eff6ff;color:#1e3a8a;"
                "border:1px solid #bfdbfe;border-radius:6px;padding:4px 10px;"
                "font-size:0.72rem;font-weight:900;text-decoration:none;"
                "white-space:nowrap;'>📊 상세 상담 이동 →</a>",
                unsafe_allow_html=True,
            )
        except Exception:
            pass

        # 암 5년 일실수익 결론 카드
        _c5yr_man = int(_tri_res.get("annual", 0) / 10_000 * 5)
        if _c5yr_man > 0:
            st.markdown(
                f"<div style='background:#fef3c7;border:1.5px solid #f59e0b;"
                f"border-radius:8px;padding:9px 13px;margin-top:8px;font-size:0.74rem;"
                f"line-height:1.9;border-left:4px solid #d97706;'>"
                f"<b style='color:#92400e;'>&#128204; 암 5년 일실수익 기준 진단비</b><br>"
                f"결론) 암 진단으로 실직할 경우 5년간 필요 소득은 "
                f"<b style='color:#dc2626;font-size:0.82rem;'>{_c5yr_man:,}만원</b>이며, "
                f"여기에 비급여 진료비 평균 15,000만~20,000만원을 추가:<br>"
                f"<b>• 일실수익 5년기준: 최저 {_c5yr_man:,}만원 (+ 암치료비 15,000만원~20,000만원)</b>"
                f"</div>",
                unsafe_allow_html=True,
            )

        # [GP 카카오 발송 파이프라인 Step2] AI 가입결과 보고서 발송
        if kakao_sender_ok and ks_render_send_ui:
            _cust_name  = sel_cust.get("name", "고객")
            _cust_phone = sel_cust.get("contact", "")
            try:
                from shared_components import decrypt_pii as _dpii
                _cust_phone = _dpii(_cust_phone)
            except Exception:
                pass
            # [GP-SEC §3] 리포트 텍스트 내 고객명 마스킹
            try:
                from shared_components import mask_name as _mn_tri
                _cust_name_masked = _mn_tri(_cust_name)
            except Exception:
                _cust_name_masked = _cust_name
            _tri_report_text = (
                f"[골드키 AI 가입결과 보고서]\n"
                f"고객명: {_cust_name_masked}님\n\n"
                f"■ 트리니티 산출법 분석 결과\n"
                f"• 추정 월 소득: {_tri_res.get('monthly', 0):,.0f}원\n"
                f"• 일일 가치: {_tri_res.get('daily', 0):,.0f}원\n"
                f"• 상해 입원일당: {_tri_res.get('gap_injury', 0):,.0f}원\n"
                f"• 질병 입원일당: {_tri_res.get('gap_disease', 0):,.0f}원\n"
                f"• 뇌혈줘(18개월): {_tri_res.get('stroke_18', 0):,.0f}원\n"
                f"• 암 최소 권장: {_tri_res.get('cancer_min', 0):,.0f}원\n"
                f"• 암 권장: {_tri_res.get('cancer_rec', 0):,.0f}원\n"
                f"• 후유장해 필요금액: {_tri_res.get('disability_cov_total', 0):,.0f}원\n"
                f"• 산재 적용 최소 대비: {_tri_res.get('disability_cov_min', 0):,.0f}원\n\n"
                f"■ 암 5년 일실수익 기준\n"
                f"결론) 암 진단 실직 시 5년간 필요 소득: {_c5yr_man:,}만원\n"
                f"• 최저 {_c5yr_man:,}만원 (+ 암치료비 15,000만원~20,000만원)\n\n"
                f"※ 골드키 AI Masters 2026 — 트리니티 산출법 기준"
            )
            ks_render_send_ui(
                report_text=_tri_report_text,
                session_key=f"_tri_send_{sel_pid}",
                default_phone=_cust_phone,
                title="골드키 AI 가입결과 보고서",
                compact=True,
            )

        # 트리니티 산출 성공 직후 하단 컨텍스트 유도
        _render_hq_context_nudge()

        if st.button("🔄 결과 초기화", key=f"crm_tri_reset_{sel_pid}"):
            st.session_state.pop(_tri_sess_key, None)
            st.rerun()
    else:
        st.caption("💡 월 건강보험료 입력 후 버튼을 클릭하면 AI 비협보험 가액이 산출됩니다.")

    st.markdown("</div>", unsafe_allow_html=True)
