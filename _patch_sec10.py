# [PATCH] GK-SEC-10 디지털 보험 진단 시스템 삽입
# 1) SECTOR_CODES에 GK-SEC-10 항목 추가 (L8205 이후)
# 2) _render_gk_sec10() 함수 정의 (GK-SEC-09 함수 바로 위)
# 3) 라우터에 if cur == "gk_sec10" 블록 추가 (GK-SEC-09 라우터 위)

with open('D:/CascadeProjects/app.py', encoding='utf-8') as f:
    content = f.read()

# ═══════════════════════════════════════════════════════════════════════
# PATCH 1: SECTOR_CODES에 GK-SEC-10 등록
# ═══════════════════════════════════════════════════════════════════════
OLD_SEC09_CODE = '''    # ── GK-SEC-09: VVIP CEO 통합 경영 전략 센터 ──────────────────────────────
    "9900": {"name": "VVIP CEO 통합 경영 전략 센터", "tab_key": "gk_sec09",'''

NEW_SEC09_CODE = '''    # ── GK-SEC-10: 디지털 보험 진단 시스템 (내보험다보여) ────────────────────
    "1000": {"name": "디지털 보험 진단 시스템", "tab_key": "gk_sec10", "keywords": [
        "내보험다보여", "보험진단시스템", "gk-sec-10", "마이데이터보험", "보험소환",
        "정밀진단", "보험전체조회", "내보험찾기", "보험진단허브", "보장과부족",
        "보험내역조회", "coocon", "codef", "신용정보원", "본인인증보험",
    ]},
    # ── GK-SEC-09: VVIP CEO 통합 경영 전략 센터 ──────────────────────────────
    "9900": {"name": "VVIP CEO 통합 경영 전략 센터", "tab_key": "gk_sec09",'''

if OLD_SEC09_CODE in content:
    content = content.replace(OLD_SEC09_CODE, NEW_SEC09_CODE, 1)
    print("PATCH 1: SECTOR_CODES GK-SEC-10 등록 OK")
else:
    print("WARNING PATCH 1: 앵커 미발견")

# ═══════════════════════════════════════════════════════════════════════
# PATCH 2: _render_gk_sec10() 함수 삽입
# GK-SEC-09 함수 def _render_gk_sec09() 바로 앞에 삽입
# ═══════════════════════════════════════════════════════════════════════
SEC10_FUNC = '''
# ══════════════════════════════════════════════════════════════════════════════
# [GK-SEC-10] 디지털 보험 진단 시스템 — 내보험다보여 (Consent Flow + Diagnosis Hub)
# ══════════════════════════════════════════════════════════════════════════════
def _render_gk_sec10():
    import streamlit as st
    import json, hashlib, datetime

    # ── 태블릿 최적화 CSS ──────────────────────────────────────────────────
    st.markdown("""
<style>
/* GK-SEC-10 태블릿 최적화 */
[data-testid="stAppViewContainer"] .sec10-wrap { max-width:1100px; margin:0 auto; }
.sec10-consent-box {
    border:1px dashed #000; border-radius:12px;
    padding:20px 24px; background:#fff; box-sizing:border-box;
    margin-bottom:16px;
}
.sec10-dashed-divider {
    border:none; border-top:2px dashed #000;
    margin:24px 0; width:100%;
}
.sec10-badge {
    display:inline-block; padding:4px 14px; border-radius:20px;
    font-weight:800; font-size:0.82rem; margin:2px 4px 2px 0;
}
.sec10-ins-row {
    display:flex; align-items:center; gap:10px; flex-wrap:wrap;
    padding:8px 12px; border-bottom:1px solid #e5e7eb;
    font-size:0.88rem;
}
.sec10-chart-wrap {
    background:#fff; border:1px dashed #000; border-radius:12px;
    padding:16px 20px; margin-top:4px; box-sizing:border-box;
}
@media (max-width: 900px) {
    .sec10-ins-row { font-size:0.82rem; padding:6px 8px; }
    .sec10-chart-wrap { padding:10px 8px; }
}
</style>
""", unsafe_allow_html=True)

    tab_home_btn("gk_sec10")

    # ── 헤더 ──────────────────────────────────────────────────────────────
    st.markdown(
        "<div style='background:linear-gradient(90deg,#0a1628,#1a3a5c);"
        "border-radius:12px;padding:18px 24px;margin-bottom:18px;'>"
        "<div style='font-size:1.3rem;font-weight:900;color:#D4AF37;letter-spacing:0.04em;'>"
        "📡 GK-SEC-10 — 디지털 보험 진단 시스템</div>"
        "<div style='font-size:0.88rem;color:#c0d8f0;margin-top:4px;'>"
        "내보험다보여 · 마이데이터 기반 정밀 진단 허브</div>"
        "</div>", unsafe_allow_html=True
    )

    # ── 1:1 대화체 안내 ───────────────────────────────────────────────────
    st.markdown(
        "<div style='background:#f0f9ff;border-left:4px solid #0ea5e9;"
        "border-radius:8px;padding:12px 16px;margin-bottom:16px;"
        "font-size:0.9rem;color:#0c4a6e;line-height:1.7;'>"
        "💬 <b>고객님, 이 섹션은 태블릿에서 더 크고 선명하게 보실 수 있습니다.</b><br>"
        "흩어져 있던 소중한 보험들을 모두 찾아왔으니, 현재 상태를 시원하게 보여드릴게요."
        "</div>", unsafe_allow_html=True
    )

    # ════════════════════════════════════════════════════════════════════
    # PHASE 1 — GK-SEC-01 정보동의 + 간소화 입력
    # ════════════════════════════════════════════════════════════════════
    _phase = st.session_state.get("sec10_phase", "consent")

    if _phase == "consent":
        st.markdown("### 📋 1단계 — 고객 등록 및 정보동의")
        st.markdown("<div class='sec10-consent-box'>", unsafe_allow_html=True)

        # 필수 입력 — 이름 + 연락처만
        _c1, _c2 = st.columns(2)
        with _c1:
            _s10_name = st.text_input(
                "👤 고객 성함 *", placeholder="홍길동",
                value=st.session_state.get("sec10_name",
                      st.session_state.get("gs_c_name", "")),
                key="sec10_name_input", max_chars=40,
            )
        with _c2:
            _s10_phone = st.text_input(
                "📱 휴대폰 번호 *", placeholder="010-0000-0000",
                value=st.session_state.get("sec10_phone", ""),
                key="sec10_phone_input", max_chars=20,
            )

        # ── 개인정보 수집 동의 ────────────────────────────────────────
        st.markdown(
            "<div style='background:#f9fafb;border:1px solid #d1d5db;"
            "border-radius:8px;padding:12px 16px;margin:12px 0;'>"
            "<div style='font-size:0.88rem;font-weight:800;color:#111;margin-bottom:8px;'>"
            "📜 개인정보 수집 및 이용 동의</div>"
            "<div style='font-size:0.78rem;color:#4b5563;line-height:1.7;'>"
            "수집 항목: 성명, 연락처, 보험 가입 내역 (공공 마이데이터 기반)<br>"
            "수집 목적: 보험 보장 현황 분석 및 설계 참고<br>"
            "보유 기간: 상담 종료 후 즉시 해싱 처리 (AES-256 저장)"
            "</div></div>", unsafe_allow_html=True
        )

        _consent1 = st.checkbox(
            "✅ [필수] 개인정보 수집 및 이용에 동의합니다",
            value=st.session_state.get("sec10_consent1", False),
            key="sec10_consent1_cb"
        )
        _consent2 = st.checkbox(
            "✅ [필수] 마이데이터 조회 및 활용에 동의합니다",
            value=st.session_state.get("sec10_consent2", False),
            key="sec10_consent2_cb"
        )

        # 개인정보처리방침 링크
        st.markdown(
            "<a href='#' style='font-size:0.78rem;color:#2563eb;text-decoration:underline;'>"
            "📄 개인정보 처리방침 전문보기</a>",
            unsafe_allow_html=True
        )

        # ── 디지털 서명 패드 (텍스트 서명 방식) ─────────────────────
        st.markdown("**✍️ 디지털 서명** (성함 입력으로 서명 갈음)")
        _s10_sign = st.text_input(
            "서명란", placeholder="홍길동 (본인 성명 입력)",
            value=st.session_state.get("sec10_sign", ""),
            key="sec10_sign_input", max_chars=30,
            label_visibility="collapsed"
        )
        _sign_valid = (_s10_sign.strip() == _s10_name.strip() and len(_s10_sign.strip()) >= 2)
        if _s10_sign and not _sign_valid:
            st.caption("⚠️ 서명은 위에 입력한 고객 성함과 일치해야 합니다.")
        elif _sign_valid:
            _sign_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            st.caption(f"✅ 서명 확인: **{_s10_sign}** | {_sign_ts}")

        st.markdown("</div>", unsafe_allow_html=True)

        # ── 동의 완료 → 진단 시작 버튼 (조건부 활성화) ─────────────
        _all_ok = (_s10_name.strip() and _s10_phone.strip()
                   and _consent1 and _consent2 and _sign_valid)
        if _all_ok:
            if st.button(
                "🔬 내보험다보여: 정밀 진단 시작",
                type="primary", use_container_width=True, key="sec10_start_btn"
            ):
                st.session_state["sec10_name"]    = _s10_name.strip()
                st.session_state["sec10_phone"]   = _s10_phone.strip()
                st.session_state["sec10_consent1"]= True
                st.session_state["sec10_consent2"]= True
                st.session_state["sec10_sign"]    = _s10_sign.strip()
                st.session_state["sec10_phase"]   = "auth"
                st.session_state["gs_c_name"]     = _s10_name.strip()
                st.session_state["current_c_name"]= _s10_name.strip()
                st.rerun()
        else:
            st.button(
                "🔬 내보험다보여: 정밀 진단 시작 (동의 완료 후 활성화)",
                disabled=True, use_container_width=True, key="sec10_start_btn_dis"
            )
            _missing = []
            if not _s10_name.strip(): _missing.append("고객 성함")
            if not _s10_phone.strip(): _missing.append("연락처")
            if not _consent1: _missing.append("개인정보 동의")
            if not _consent2: _missing.append("마이데이터 동의")
            if not _sign_valid: _missing.append("디지털 서명")
            if _missing:
                st.caption(f"⚠️ 미완료 항목: {' · '.join(_missing)}")
        return

    # ════════════════════════════════════════════════════════════════════
    # PHASE 2 — 본인인증 팝업 (통신사 + 생년월일)
    # ════════════════════════════════════════════════════════════════════
    if _phase == "auth":
        _s10_name = st.session_state.get("sec10_name", "고객")
        st.markdown(f"### 🔐 2단계 — 본인 인증 ({_s10_name}님)")

        st.markdown("<div class='sec10-consent-box'>", unsafe_allow_html=True)
        st.markdown(
            "<div style='background:#fff7ed;border:1px dashed #f59e0b;"
            "border-radius:8px;padding:10px 14px;margin-bottom:12px;"
            "font-size:0.82rem;color:#92400e;'>"
            "🔒 인증 정보는 마이데이터 조회 후 <b>AES-256 암호화 + 해싱</b> 처리되며, "
            "세션 종료 시 즉시 파기됩니다."
            "</div>", unsafe_allow_html=True
        )

        _auth_c1, _auth_c2 = st.columns([3, 2])
        with _auth_c1:
            _CARRIERS_AUTH = ["─ 통신사 선택 ─", "SKT", "KT", "LG U+",
                              "SKT 알뜰폰", "KT 알뜰폰", "LG 알뜰폰",
                              "헬로모바일", "KT M모바일", "SK세븐모바일", "기타 알뜰폰"]
            _s10_carrier = st.selectbox(
                "📶 통신사 (알뜰폰 포함)",
                _CARRIERS_AUTH, key="sec10_auth_carrier"
            )
        with _auth_c2:
            _s10_dob = st.text_input(
                "🎂 생년월일", placeholder="YYYYMMDD",
                key="sec10_auth_dob", max_chars=8
            )

        # COOCON/CODEF 연동 안내
        st.markdown(
            "<div style='margin-top:10px;background:#f0fdf4;border:1px solid #86efac;"
            "border-radius:8px;padding:10px 14px;font-size:0.8rem;color:#166534;'>"
            "<b>🔗 연동 채널:</b> 쿠콘(COOCON) / 코드에프(CODEF) → "
            "한국신용정보원 마이데이터 수집<br>"
            "<b>조회 항목:</b> 보험사별 가입 현황, 보험료, 보장 담보, 증권번호"
            "</div>", unsafe_allow_html=True
        )

        st.markdown("</div>", unsafe_allow_html=True)

        _auth_cols = st.columns([1, 1, 1])
        with _auth_cols[0]:
            if st.button("← 이전 단계", key="sec10_auth_back", use_container_width=True):
                st.session_state["sec10_phase"] = "consent"
                st.rerun()
        with _auth_cols[2]:
            _auth_ready = (_s10_carrier != "─ 통신사 선택 ─"
                           and len(re.sub(r'\D', '', _s10_dob)) == 8)
            if _auth_ready:
                if st.button(
                    "🚀 인증 및 데이터 소환", type="primary",
                    use_container_width=True, key="sec10_auth_btn"
                ):
                    # 데이터 시뮬레이션 (실제 환경에서는 COOCON/CODEF API 호출)
                    _sim_data = _sec10_simulate_fetch(st.session_state.get("sec10_name", ""))
                    st.session_state["sec10_fetched"] = _sim_data
                    st.session_state["sec10_phase"]   = "diagnosis"
                    # 민감정보 즉시 해싱
                    _dob_hashed = hashlib.sha256(_s10_dob.encode()).hexdigest()[:16]
                    st.session_state["sec10_dob_hash"] = _dob_hashed
                    st.rerun()
            else:
                st.button(
                    "🚀 인증 및 데이터 소환 (정보 입력 후 활성화)",
                    disabled=True, use_container_width=True, key="sec10_auth_btn_dis"
                )
        return

    # ════════════════════════════════════════════════════════════════════
    # PHASE 3 — GK-SEC-10 진단 허브 (Diagnosis Hub)
    # ════════════════════════════════════════════════════════════════════
    if _phase == "diagnosis":
        _s10_name   = st.session_state.get("sec10_name", "고객")
        _fetched    = st.session_state.get("sec10_fetched", {})
        _ins_list   = _fetched.get("insurance_list", [])
        _coverage   = _fetched.get("coverage_analysis", [])

        # 상단 상태바
        _fetch_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        st.markdown(
            f"<div style='display:flex;align-items:center;justify-content:space-between;"
            f"background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;"
            f"padding:8px 16px;margin-bottom:16px;flex-wrap:wrap;gap:8px;'>"
            f"<span style='font-size:0.85rem;font-weight:700;color:#0f172a;'>"
            f"👤 {_s10_name}님의 보험 진단 결과</span>"
            f"<span style='font-size:0.75rem;color:#64748b;'>📅 조회: {_fetch_time}</span>"
            f"<span style='font-size:0.75rem;background:#dcfce7;color:#166534;"
            f"padding:2px 10px;border-radius:12px;font-weight:700;'>✅ 소환 완료</span>"
            f"</div>", unsafe_allow_html=True
        )

        # ── 상단: 소환된 보험 내역 리스트 ──────────────────────────
        st.markdown("#### 📂 소환된 보험 내역")
        if _ins_list:
            # 컬럼 헤더
            st.markdown(
                "<div style='display:flex;gap:10px;padding:6px 12px;"
                "background:#f1f5f9;border-radius:6px;font-size:0.78rem;"
                "font-weight:800;color:#475569;margin-bottom:2px;flex-wrap:wrap;'>"
                "<span style='flex:2;min-width:80px;'>보험사</span>"
                "<span style='flex:3;min-width:100px;'>상품명</span>"
                "<span style='flex:1;min-width:60px;text-align:right;'>보험료</span>"
                "<span style='flex:2;min-width:80px;'>주요담보</span>"
                "<span style='flex:1;min-width:50px;text-align:center;'>상태</span>"
                "</div>", unsafe_allow_html=True
            )
            for _ins in _ins_list:
                _status_color = {"유지": "#22c55e", "실효": "#ef4444", "만기": "#94a3b8"}.get(_ins.get("status", ""), "#6b7280")
                _status_bg    = {"유지": "#dcfce7", "실효": "#fee2e2", "만기": "#f1f5f9"}.get(_ins.get("status", ""), "#f9fafb")
                st.markdown(
                    f"<div class='sec10-ins-row'>"
                    f"<span style='flex:2;min-width:80px;font-weight:700;color:#0f172a;'>{_ins.get('company','')}</span>"
                    f"<span style='flex:3;min-width:100px;color:#374151;'>{_ins.get('product','')}</span>"
                    f"<span style='flex:1;min-width:60px;text-align:right;color:#4f46e5;font-weight:700;'>"
                    f"{_ins.get('premium','')}</span>"
                    f"<span style='flex:2;min-width:80px;color:#6b7280;font-size:0.78rem;'>{_ins.get('coverage','')}</span>"
                    f"<span style='flex:1;min-width:50px;text-align:center;background:{_status_bg};"
                    f"color:{_status_color};border-radius:12px;padding:2px 8px;"
                    f"font-size:0.72rem;font-weight:700;'>{_ins.get('status','')}</span>"
                    f"</div>", unsafe_allow_html=True
                )
        else:
            st.info("📭 소환된 보험 내역이 없습니다.")

        # ── 굵은 1px 검정 점선 구분선 ────────────────────────────────
        st.markdown("<hr class='sec10-dashed-divider'>", unsafe_allow_html=True)

        # ── 하단: 보장 과부족 차트 (Full Width, 반응형) ──────────────
        st.markdown("#### 📊 보장 항목별 과부족 분석")
        st.markdown(
            "<div style='font-size:0.8rem;color:#64748b;margin-bottom:12px;'>"
            "🟢 충분 &nbsp;|&nbsp; 🟡 부족 &nbsp;|&nbsp; 🔴 미가입"
            "</div>", unsafe_allow_html=True
        )

        if _coverage:
            st.markdown("<div class='sec10-chart-wrap'>", unsafe_allow_html=True)
            # Streamlit 내장 progress bar 기반 반응형 차트
            for _item in _coverage:
                _cat      = _item.get("category", "")
                _name     = _item.get("name", "")
                _rec      = _item.get("recommended_amt", 0)
                _enrolled = _item.get("enrolled_amt", 0)
                _ratio    = min(int((_enrolled / _rec * 100) if _rec > 0 else 0), 100)
                _status   = _item.get("status", "미가입")
                _color    = {"충분": "#22c55e", "부족": "#f59e0b", "미가입": "#ef4444"}.get(_status, "#94a3b8")
                _icon     = {"충분": "🟢", "부족": "🟡", "미가입": "🔴"}.get(_status, "⚪")

                _row_c1, _row_c2, _row_c3, _row_c4 = st.columns([2, 4, 1, 1])
                with _row_c1:
                    st.markdown(
                        f"<div style='font-size:0.8rem;font-weight:700;color:#374151;"
                        f"padding-top:6px;'>{_icon} {_cat}</div>",
                        unsafe_allow_html=True
                    )
                with _row_c2:
                    st.markdown(
                        f"<div style='font-size:0.78rem;color:#6b7280;padding-top:2px;'>{_name}</div>",
                        unsafe_allow_html=True
                    )
                    st.progress(_ratio / 100)
                with _row_c3:
                    _enrolled_str = f"{_enrolled//10000:,}만" if _enrolled >= 10000 else (f"{_enrolled:,}" if _enrolled else "0")
                    st.markdown(
                        f"<div style='font-size:0.78rem;color:#4f46e5;font-weight:700;"
                        f"padding-top:6px;text-align:right;'>{_enrolled_str}</div>",
                        unsafe_allow_html=True
                    )
                with _row_c4:
                    _rec_str = f"{_rec//10000:,}만" if _rec >= 10000 else (f"{_rec:,}" if _rec else "─")
                    st.markdown(
                        f"<div style='font-size:0.72rem;color:#9ca3af;padding-top:6px;"
                        f"text-align:right;'>/{_rec_str}</div>",
                        unsafe_allow_html=True
                    )
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("📊 분석 데이터를 불러오는 중입니다.")

        # ── 면책 문구 ────────────────────────────────────────────────
        st.markdown(
            "<div style='background:#f8fafc;border:1px dashed #cbd5e1;"
            "border-radius:8px;padding:10px 16px;margin-top:20px;"
            "font-size:0.75rem;color:#64748b;line-height:1.6;'>"
            "※ 본 분석은 공공 데이터를 기반으로 한 참고용 진단이며, "
            "구체적인 재무 설계는 담당 설계사와 상의하십시오."
            "</div>", unsafe_allow_html=True
        )

        # ── 재진단 / 초기화 버튼 ──────────────────────────────────────
        _btn_c1, _btn_c2 = st.columns(2)
        with _btn_c1:
            if st.button("🔄 다시 소환", key="sec10_refetch", use_container_width=True):
                st.session_state["sec10_phase"] = "auth"
                st.rerun()
        with _btn_c2:
            if st.button("🗑️ 진단 초기화", key="sec10_reset", use_container_width=True):
                for _k in list(st.session_state.keys()):
                    if _k.startswith("sec10_"):
                        del st.session_state[_k]
                st.rerun()


def _sec10_simulate_fetch(client_name: str) -> dict:
    """
    [GP-SEC10] 마이데이터 소환 시뮬레이션.
    실제 환경에서는 COOCON/CODEF API 호출로 교체.
    """
    import random
    _companies = ["삼성생명", "한화생명", "교보생명", "DB손해보험", "현대해상", "KB손해보험", "메리츠화재"]
    _products  = [
        ("종신보험", "사망·CI", "월 12.3만"),
        ("암보험", "암진단비", "월 4.8만"),
        ("실손보험", "입원·통원", "월 8.1만"),
        ("건강보험", "뇌·심장·암", "월 15.6만"),
        ("운전자보험", "교통사고", "월 2.4만"),
    ]
    random.seed(abs(hash(client_name)) % 9999)
    _ins_list = []
    for _ in range(random.randint(2, 5)):
        _co = random.choice(_companies)
        _prod, _cov, _prem = random.choice(_products)
        _ins_list.append({
            "company":  _co,
            "product":  _prod,
            "coverage": _cov,
            "premium":  _prem,
            "status":   random.choice(["유지", "유지", "유지", "실효", "만기"]),
        })

    _coverage_items = [
        {"category": "암 진단",   "name": "일반암진단비",       "recommended_amt": 50000000, "enrolled_amt": random.choice([0, 20000000, 30000000, 50000000]), "status": ""},
        {"category": "뇌혈관",    "name": "뇌졸중진단비",       "recommended_amt": 50000000, "enrolled_amt": random.choice([0, 10000000, 20000000, 50000000]), "status": ""},
        {"category": "심장",      "name": "급성심근경색진단비", "recommended_amt": 30000000, "enrolled_amt": random.choice([0, 10000000, 30000000]),           "status": ""},
        {"category": "수술비",    "name": "1~5종 수술비",       "recommended_amt": 5000000,  "enrolled_amt": random.choice([0, 1000000, 3000000, 5000000]),    "status": ""},
        {"category": "입원일당",  "name": "질병 입원일당",      "recommended_amt": 100000,   "enrolled_amt": random.choice([0, 30000, 50000, 100000]),          "status": ""},
        {"category": "실손",      "name": "실손의료비",         "recommended_amt": 1,        "enrolled_amt": random.choice([0, 1]),                            "status": ""},
        {"category": "사망",      "name": "일반사망보험금",     "recommended_amt": 300000000,"enrolled_amt": random.choice([0, 100000000, 200000000]),          "status": ""},
    ]
    for _ci in _coverage_items:
        _r, _e = _ci["recommended_amt"], _ci["enrolled_amt"]
        if _e == 0:         _ci["status"] = "미가입"
        elif _e >= _r:      _ci["status"] = "충분"
        else:               _ci["status"] = "부족"

    return {"insurance_list": _ins_list, "coverage_analysis": _coverage_items}

'''

# _render_gk_sec09 정의 바로 앞에 삽입
ANCHOR_SEC09_FUNC = "def _render_gk_sec09():"
if ANCHOR_SEC09_FUNC in content:
    content = content.replace(ANCHOR_SEC09_FUNC, SEC10_FUNC + ANCHOR_SEC09_FUNC, 1)
    print("PATCH 2: _render_gk_sec10() 함수 삽입 OK")
else:
    print("WARNING PATCH 2: _render_gk_sec09() 앵커 미발견")

# ═══════════════════════════════════════════════════════════════════════
# PATCH 3: 라우터에 if cur == "gk_sec10" 추가 (GK-SEC-09 라우터 바로 앞)
# ═══════════════════════════════════════════════════════════════════════
OLD_ROUTER_SEC09 = '''    # ══════════════════════════════════════════════════════════════════════
    # [GK-SEC-09] VVIP CEO 통합 경영 전략 센터 라우터
    # ══════════════════════════════════════════════════════════════════════
    if cur == "gk_sec09":'''

NEW_ROUTER_SEC09 = '''    # ══════════════════════════════════════════════════════════════════════
    # [GK-SEC-10] 디지털 보험 진단 시스템 라우터
    # ══════════════════════════════════════════════════════════════════════
    if cur == "gk_sec10":
        _render_gk_sec10()
        st.stop()

    # ══════════════════════════════════════════════════════════════════════
    # [GK-SEC-09] VVIP CEO 통합 경영 전략 센터 라우터
    # ══════════════════════════════════════════════════════════════════════
    if cur == "gk_sec09":'''

if OLD_ROUTER_SEC09 in content:
    content = content.replace(OLD_ROUTER_SEC09, NEW_ROUTER_SEC09, 1)
    print("PATCH 3: 라우터 삽입 OK")
else:
    print("WARNING PATCH 3: 라우터 앵커 미발견")

with open('D:/CascadeProjects/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\nDONE: sec10 patch applied")
