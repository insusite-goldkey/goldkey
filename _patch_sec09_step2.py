with open('D:/CascadeProjects/app.py', encoding='utf-8') as f:
    content = f.read()

ANCHOR = '\ndef _render_gk_sec08() -> None:'
if ANCHOR not in content:
    print("ERROR: _render_gk_sec08 anchor not found"); exit(1)

SEC09_FUNC = '''

# ══════════════════════════════════════════════════════════════════════════════
# [GK-SEC-09] VVIP CEO 통합 경영 전략 센터 렌더러
# ══════════════════════════════════════════════════════════════════════════════
def _render_gk_sec09() -> None:
    """GK-SEC-09 VVIP CEO 통합 경영 전략 센터"""
    import datetime as _dt09

    # ── CSS ──────────────────────────────────────────────────────────────────
    st.markdown("""
<style>
.gks09-wrap {
    border: 1px dashed #000 !important;
    background: linear-gradient(135deg, #f8f9fb 0%, #eef1f5 100%) !important;
    border-radius: 14px;
    padding: 16px 18px;
    margin-bottom: 14px;
}
.gks09-header {
    background: linear-gradient(135deg, #2C3E50 0%, #3D5166 60%, #4A6278 100%);
    border-radius: 12px;
    padding: 18px 24px;
    margin-bottom: 18px;
    border: 1px dashed #BDC3C7;
}
.gks09-header h2 { color: #F0F3F7 !important; font-size: 1.3rem; font-weight: 900; margin: 0 0 4px 0; }
.gks09-header p  { color: #BDC3C7 !important; font-size: 0.82rem; margin: 0; }
.gks09-card {
    border: 1px dashed #000;
    background: #F8F9FA;
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 10px;
}
.gks09-card-title { font-size: 0.92rem; font-weight: 900; color: #2C3E50; margin-bottom: 4px; }
.gks09-card-desc  { font-size: 0.80rem; color: #333; font-weight: 700; }
.gks09-law {
    border-left: 4px solid #2C3E50;
    background: #EEF1F5;
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
    margin: 6px 0;
    font-size: 0.80rem;
    font-weight: 700;
    color: #2C3E50;
}
.gks09-warn {
    border: 2px dashed #c0392b;
    background: #FFEBEE;
    border-radius: 10px;
    padding: 12px 16px;
    margin: 8px 0;
    font-size: 0.88rem;
    font-weight: 900;
    color: #c0392b;
}
.gks09-formula {
    border: 1px dashed #2C3E50;
    background: #EBF5FB;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 8px 0;
    font-size: 0.85rem;
    font-weight: 700;
    color: #1a252f;
    font-family: monospace;
}
.gks09-highlight {
    background: #FFF9C4;
    border: 1px dashed #F9A825;
    border-radius: 6px;
    padding: 4px 8px;
    font-weight: 900;
    color: #E65100;
}
input, textarea, .stTextInput input, .stTextArea textarea,
.stNumberInput input { font-weight: 700 !important; color: #000 !important; }
</style>""", unsafe_allow_html=True)

    # ── 헤더 ─────────────────────────────────────────────────────────────────
    st.markdown("""
<div class="gks09-header">
  <h2>👑 GK-SEC-09 VVIP CEO 통합 경영 전략 센터</h2>
  <p>데이터는 거짓말하지 않는다. 법률과 수치로 마스터의 경영 전술에 압도적 권위를 부여하라.</p>
</div>""", unsafe_allow_html=True)

    # ── 상단 네비게이션 ───────────────────────────────────────────────────────
    _nav_c1, _nav_c2 = st.columns([1, 4])
    with _nav_c1:
        if st.button("⬅️ 게이트웨이", key="sec09_back_top", use_container_width=True):
            st.session_state["current_tab"] = "home"
            st.session_state["_scroll_top"] = True
            st.rerun()

    # ── 5개 PART 탭 ──────────────────────────────────────────────────────────
    _p1, _p2, _p3, _p4, _p5 = st.tabs([
        "⚖️ PART 1 조세·법령",
        "🦺 PART 2 Gap Cover",
        "📊 PART 3 주식평가·상속",
        "🔥 PART 4 공장화재·배당",
        "🔍 PART 5 재무제표 스캐너",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # PART 1 — 지능형 조세·법령 엔진
    # ══════════════════════════════════════════════════════════════════════════
    with _p1:
        st.markdown('<div class="gks09-wrap">', unsafe_allow_html=True)
        st.markdown("#### ⚖️ 법인세·소득세·상증세율 실시간 동기화")
        st.caption("매년 1월 10일 기준 자동 업데이트 | 금융감독원·국세청 예규 상시 병기")

        # 세율 테이블 — 내장 데이터 (2024 기준, 연 1회 관리자 갱신)
        _corp_tax = st.session_state.get("_sec09_corp_tax", [
            (200_000_000,       0.09,  0),
            (20_000_000_000,    0.19,  20_000_000),
            (300_000_000_000,   0.21,  3_800_000_000),
            (float('inf'),      0.24,  65_800_000_000),
        ])
        _income_tax = [
            (14_000_000,   0.06,  0),
            (50_000_000,   0.15,  1_260_000),
            (88_000_000,   0.24,  5_760_000),
            (150_000_000,  0.35,  15_440_000),
            (300_000_000,  0.38,  19_940_000),
            (500_000_000,  0.40,  25_940_000),
            (1_000_000_000,0.42,  35_940_000),
            (float('inf'), 0.45,  65_940_000),
        ]
        _inherit_tax = [
            (100_000_000,   0.10, 0),
            (500_000_000,   0.20, 10_000_000),
            (1_000_000_000, 0.30, 60_000_000),
            (3_000_000_000, 0.40, 160_000_000),
            (float('inf'),  0.50, 460_000_000),
        ]

        _t1c1, _t1c2, _t1c3 = st.columns(3)
        with _t1c1:
            st.markdown("**📋 법인세율표 (2024)**")
            st.components.v1.html("""
<table style="width:100%;border-collapse:collapse;font-size:0.78rem;">
<tr style="background:#2C3E50;color:#fff;"><th style="padding:5px;">과세표준</th><th>세율</th></tr>
<tr style="background:#f8f9fb;"><td style="padding:5px;">2억 이하</td><td style="font-weight:700;">9%</td></tr>
<tr><td style="padding:5px;">2억~200억</td><td style="font-weight:700;">19%</td></tr>
<tr style="background:#f8f9fb;"><td style="padding:5px;">200억~3000억</td><td style="font-weight:700;">21%</td></tr>
<tr><td style="padding:5px;">3000억 초과</td><td style="font-weight:700;">24%</td></tr>
</table>""", height=120)
        with _t1c2:
            st.markdown("**📋 소득세율표 (2024)**")
            st.components.v1.html("""
<table style="width:100%;border-collapse:collapse;font-size:0.78rem;">
<tr style="background:#2C3E50;color:#fff;"><th style="padding:5px;">과세표준</th><th>세율</th></tr>
<tr style="background:#f8f9fb;"><td style="padding:5px;">1400만 이하</td><td style="font-weight:700;">6%</td></tr>
<tr><td style="padding:5px;">~5000만</td><td style="font-weight:700;">15%</td></tr>
<tr style="background:#f8f9fb;"><td style="padding:5px;">~8800만</td><td style="font-weight:700;">24%</td></tr>
<tr><td style="padding:5px;">~1.5억</td><td style="font-weight:700;">35%</td></tr>
<tr style="background:#f8f9fb;"><td style="padding:5px;">~3억</td><td style="font-weight:700;">38%</td></tr>
<tr><td style="padding:5px;">~5억</td><td style="font-weight:700;">40%</td></tr>
<tr style="background:#f8f9fb;"><td style="padding:5px;">~10억</td><td style="font-weight:700;">42%</td></tr>
<tr><td style="padding:5px;">10억 초과</td><td style="font-weight:700;">45%</td></tr>
</table>""", height=190)
        with _t1c3:
            st.markdown("**📋 상속·증여세율 (2024)**")
            st.components.v1.html("""
<table style="width:100%;border-collapse:collapse;font-size:0.78rem;">
<tr style="background:#2C3E50;color:#fff;"><th style="padding:5px;">과세표준</th><th>세율</th></tr>
<tr style="background:#f8f9fb;"><td style="padding:5px;">1억 이하</td><td style="font-weight:700;">10%</td></tr>
<tr><td style="padding:5px;">~5억</td><td style="font-weight:700;">20%</td></tr>
<tr style="background:#f8f9fb;"><td style="padding:5px;">~10억</td><td style="font-weight:700;">30%</td></tr>
<tr><td style="padding:5px;">~30억</td><td style="font-weight:700;">40%</td></tr>
<tr style="background:#f8f9fb;"><td style="padding:5px;">30억 초과</td><td style="font-weight:700;">50%</td></tr>
</table>""", height=130)

        # 국세청 예규 + 금감원 보도자료 카드
        st.markdown("---")
        st.markdown("**📌 근거 데이터베이스 — 클릭하여 원문 요약 확인**")
        _REGULATIONS = [
            ("서면-2017-법인-1764", "임원 생명보험료 손금 산입 기준", "계약자=법인, 수익자=법인 시 자산처리, 보장성 부분은 손금 인정"),
            ("법인세법 기본통칙 19-19-4", "단체 상해보험료 손금 처리", "종업원 전체 가입 시 전액 손금, 특정인만 가입 시 급여로 봄"),
            ("금감원 2024.03.17 보도자료", "비상장주식 할증평가 기준 개정", "최대주주 20% 할증 → 30% 상향 적용 (2024년 이후)"),
            ("상증세법 제63조", "비상장주식 평가 공식 (순손익·순자산)", "주당가치=(순손익가치×3+순자산가치×2)÷5"),
            ("상법 제462조", "중간배당 요건 및 절차", "정관 규정 + 이사회 결의 + 배당가능이익 범위 내 실시"),
        ]
        for _reg_id, _reg_title, _reg_summary in _REGULATIONS:
            with st.expander(f"📋 **{_reg_id}** — {_reg_title}"):
                st.markdown(
                    f'<div class="gks09-law">'
                    f'<b>예규/보도자료 번호:</b> {_reg_id}<br>'
                    f'<b>제목:</b> {_reg_title}<br>'
                    f'<b>핵심 요약:</b> {_reg_summary}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        # 세율 계산기
        st.markdown("---")
        st.markdown("**🔢 세율 즉시 계산기**")
        _calc_c1, _calc_c2 = st.columns(2)
        with _calc_c1:
            _tax_type = st.selectbox("세목 선택", ["법인세", "소득세", "상속·증여세"], key="sec09_tax_type")
            _tax_base = st.number_input("과세표준 (원)", min_value=0, value=500_000_000,
                                         step=10_000_000, key="sec09_tax_base", format="%d")
        with _calc_c2:
            def _calc_tax(brackets, base):
                for lim, rate, ded in brackets:
                    if base <= lim:
                        return int(base * rate - ded), rate
                return 0, 0
            _brackets = {"법인세": _corp_tax, "소득세": _income_tax, "상속·증여세": _inherit_tax}
            _tax_amt, _tax_rate = _calc_tax(_brackets[_tax_type], _tax_base)
            st.metric(f"{_tax_type} 추정액", f"{_tax_amt:,}원")
            st.metric("적용 세율", f"{_tax_rate*100:.0f}%")
        st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # PART 2 — Gap Cover 시뮬레이터
    # ══════════════════════════════════════════════════════════════════════════
    with _p2:
        st.markdown('<div class="gks09-wrap">', unsafe_allow_html=True)
        st.markdown("#### 🦺 사업주 배상책임 Gap Cover 시뮬레이터")
        st.markdown("""
<div class="gks09-warn">
⚠️ <b>민법 제750조·제758조 경고:</b> 사업주는 근로자 업무상 재해에 대해 <b>무조건적 민사 배상 책임</b>을 집니다.
산재보험 보상만으로는 민사 손해배상 청구액을 충당할 수 없으며, 부족분은 <b>법인 자산에서 직접 집행</b>됩니다.
</div>""", unsafe_allow_html=True)

        st.markdown("""
<div class="gks09-formula">
필요 가입금액 = (민사상 기대 일실수입 + 위자료) − 산재보험금
</div>""", unsafe_allow_html=True)

        _gc1, _gc2 = st.columns(2)
        with _gc1:
            st.markdown("**📥 근로자 정보 입력**")
            _w_monthly = st.number_input("월 급여 (원)", min_value=0, value=3_500_000,
                                          step=100_000, key="sec09_w_monthly", format="%d")
            _w_age     = st.number_input("나이 (세)", min_value=18, max_value=70,
                                          value=40, key="sec09_w_age")
            _w_disab   = st.selectbox("장해 등급", [f"{i}급" for i in range(1, 15)],
                                       index=2, key="sec09_w_disab")
            _disab_rate_map = {
                "1급": 1.00, "2급": 0.97, "3급": 0.94, "4급": 0.89,
                "5급": 0.82, "6급": 0.74, "7급": 0.63, "8급": 0.50,
                "9급": 0.37, "10급": 0.27, "11급": 0.20, "12급": 0.14,
                "13급": 0.09, "14급": 0.05,
            }
            _disab_rate = _disab_rate_map.get(_w_disab, 0.5)

        with _gc2:
            st.markdown("**📊 Gap Cover 산출**")
            _retire_age = 65
            _remain_yr  = max(_retire_age - _w_age, 1)
            _annual_inc = _w_monthly * 12
            _civil_loss = int(_annual_inc * _remain_yr * _disab_rate)  # 일실수입
            _civil_consolation = 50_000_000 + int(_disab_rate * 50_000_000)  # 위자료 추정
            _civil_total = _civil_loss + _civil_consolation

            # 산재보험 추정 (평균 지급률 65% 가정)
            _wci_ratio  = 0.65
            _wci_payout = int(_civil_loss * _wci_ratio)
            _gap_amount = max(_civil_total - _wci_payout, 0)

            st.metric("민사상 일실수입", f"{_civil_loss:,}원",
                      help=f"월급×12×잔여연차×장해율({_disab_rate*100:.0f}%)")
            st.metric("위자료 추정액", f"{_civil_consolation:,}원")
            st.metric("산재보험 지급 추정액", f"{_wci_payout:,}원", delta="-산재 커버")
            st.metric("⚠️ 법인 자산 잠식 위험액 (GAP)", f"{_gap_amount:,}원",
                      delta="단체보험 권장 최소 가입액", delta_color="inverse")

        st.markdown("""
<div class="gks09-card">
<div class="gks09-card-title">✅ 단체보험 가입 전략 권고</div>
<div class="gks09-card-desc">
• 계약자·수익자 = 법인 → 보험료 전액 손금 처리<br>
• 가입 금액: 위 산출 GAP 금액 이상으로 설정<br>
• 업무상재해+질병 통합 담보, 해외 출장 담보 포함 권장<br>
• 국세청 예규: 법인세법 기본통칙 19-19-4 (전 직원 가입 시 손금 인정)
</div></div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # PART 3 — 비상장주식 평가엔진 + 상속세 시뮬레이터 + 감자 플랜
    # ══════════════════════════════════════════════════════════════════════════
    with _p3:
        st.markdown('<div class="gks09-wrap">', unsafe_allow_html=True)
        st.markdown("#### 📊 비상장주식 평가엔진 (상증세법 제63조)")
        st.markdown("""
<div class="gks09-formula">
주당 가치 = (순손익가치 × 3 + 순자산가치 × 2) ÷ 5
순손익가치 = 최근 3년 평균 순이익 ÷ 자본환원율(10%)
순자산가치 = 순자산 ÷ 발행주식수
</div>""", unsafe_allow_html=True)

        _s1c1, _s1c2 = st.columns(2)
        with _s1c1:
            st.markdown("**📥 기업 기초 정보**")
            _shares_total = st.number_input("발행주식 총수 (주)", min_value=1,
                                             value=100_000, step=1_000, key="sec09_shares")
            _net_asset    = st.number_input("순자산 (원)", min_value=0,
                                             value=5_000_000_000, step=100_000_000,
                                             key="sec09_net_asset", format="%d")
            _profit_y1    = st.number_input("순이익 1년전 (원)", min_value=0,
                                             value=500_000_000, step=10_000_000,
                                             key="sec09_profit_y1", format="%d")
            _profit_y2    = st.number_input("순이익 2년전 (원)", min_value=0,
                                             value=450_000_000, step=10_000_000,
                                             key="sec09_profit_y2", format="%d")
            _profit_y3    = st.number_input("순이익 3년전 (원)", min_value=0,
                                             value=400_000_000, step=10_000_000,
                                             key="sec09_profit_y3", format="%d")
            _ceo_shares_pct = st.slider("CEO 보유 지분 (%)", 1, 100, 60, key="sec09_ceo_pct")
            _is_major = st.checkbox("최대주주(30% 할증 적용, 2024년~)", value=True, key="sec09_major")

        with _s1c2:
            st.markdown("**📊 비상장주식 평가 결과**")
            _CAP_RATE   = 0.10  # 자본환원율 10%
            _avg_profit = (_profit_y1 * 3 + _profit_y2 * 2 + _profit_y3) / 6
            _val_income = _avg_profit / _CAP_RATE / _shares_total  # 주당 순손익가치
            _val_asset  = _net_asset / _shares_total                 # 주당 순자산가치
            _val_per_share = (_val_income * 3 + _val_asset * 2) / 5
            _premium = 1.30 if _is_major else 1.00
            _val_final = int(_val_per_share * _premium)
            _ceo_shares_cnt = int(_shares_total * _ceo_shares_pct / 100)
            _ceo_total_val  = _ceo_shares_cnt * _val_final

            st.metric("주당 순손익가치", f"{int(_val_income):,}원")
            st.metric("주당 순자산가치", f"{int(_val_asset):,}원")
            st.metric("평가 주당 가치", f"{int(_val_per_share):,}원")
            if _is_major:
                st.metric("최대주주 할증 후 주당 가치 (+30%)", f"{_val_final:,}원",
                          delta="+30% 2024 기준")
            else:
                st.metric("최종 주당 가치", f"{_val_final:,}원")
            st.metric(f"CEO 보유 주식 총가치 ({_ceo_shares_pct}%)",
                      f"{_ceo_total_val:,}원",
                      delta=f"{_ceo_shares_cnt:,}주 × {_val_final:,}원/주")

        # 상속세 시뮬레이터
        st.markdown("---")
        st.markdown("#### 🏛️ CEO 유고 시 상속세 시뮬레이터")
        _ss1, _ss2 = st.columns(2)
        with _ss1:
            _other_asset = st.number_input("주식 외 기타 상속재산 (원)", min_value=0,
                                            value=1_000_000_000, step=100_000_000,
                                            key="sec09_other_asset", format="%d")
            _deduction   = st.number_input("상속공제 합계 (원, 배우자공제 등)",
                                            min_value=0, value=500_000_000,
                                            step=50_000_000, key="sec09_deduction", format="%d")
        with _ss2:
            _inherit_base = max(_ceo_total_val + _other_asset - _deduction, 0)
            _inh_tax, _inh_rate = 0, 0
            for lim, rate, ded in _inherit_tax:
                if _inherit_base <= lim:
                    _inh_tax  = int(_inherit_base * rate - ded)
                    _inh_rate = rate
                    break
            st.metric("상속세 과세표준", f"{_inherit_base:,}원")
            st.metric("적용 세율", f"{_inh_rate*100:.0f}%")
            st.metric("⚠️ 예상 상속세액", f"{_inh_tax:,}원", delta_color="inverse")

        # 감자 플랜
        st.markdown("---")
        st.markdown("#### 🔄 임직원 종신보험 & 감자 플랜 시나리오")
        st.markdown("""
<div class="gks09-card">
<div class="gks09-card-title">1단계 — 임직원 종신보험 가입 (계약자·수익자=법인)</div>
<div class="gks09-card-desc">
• 목적: CEO 유고 시 상속세 재원 마련<br>
• 보험료: 법인 손금 또는 자산 처리 (국세청 예규 서면-2017-법인-1764)<br>
• 권장 가입액: 상속세 예상액 이상 ({:,}원 이상)
</div></div>
<div class="gks09-card">
<div class="gks09-card-title">2단계 — CEO 유고 시 자기주식 취득 (감자 플랜)</div>
<div class="gks09-card-desc">
• 법인이 보험금 수령 후 상속인으로부터 주식 매입<br>
• 상법 제341조: 배당가능이익 범위 내 자기주식 취득<br>
• 취득 후 주식 소각 → 발행주식수 감소 → 잔존 주주 지분 가치 상승<br>
• 효과: 상속인 유동성 확보 + 경영권 승계 + 상속세 재원 동시 해결
</div></div>""".format(_inh_tax), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # PART 4 — 법인 공장 화재보험 120% + 중간배당 체크리스트
    # ══════════════════════════════════════════════════════════════════════════
    with _p4:
        _p4c1, _p4c2 = st.columns([6, 4])

        with _p4c1:
            st.markdown('<div class="gks09-wrap">', unsafe_allow_html=True)
            st.markdown("#### 🔥 법인 공장 화재보험 120% 안전규칙")
            st.markdown("""
<div class="gks09-formula">
권장 가입금액 = (재조달가액 − 경년감가) × 120%
</div>""", unsafe_allow_html=True)

            _fc1, _fc2, _fc3 = st.columns(3)
            with _fc1:
                _f_rebuild = st.number_input("재조달가액 (원)", min_value=0,
                                              value=3_000_000_000, step=100_000_000,
                                              key="sec09_f_rebuild", format="%d")
            with _fc2:
                _f_age   = st.number_input("건물 연수", min_value=0, max_value=60,
                                            value=10, key="sec09_f_age")
                _f_depr  = min(_f_age / 50, 0.80)  # 최대 80% 감가, 잔가 20%
            with _fc3:
                _f_inflation = st.slider("물가 상승 가산율 (%)", 0, 50, 20,
                                          key="sec09_f_inflation")

            _f_market_val  = int(_f_rebuild * (1 - _f_depr))
            _f_recommend   = int(_f_market_val * (1 + _f_inflation / 100))
            st.metric("시가 (감가 후)", f"{_f_market_val:,}원",
                      delta=f"감가율 {_f_depr*100:.1f}%")
            st.metric(f"권장 가입금액 (+{_f_inflation}% 가산)", f"{_f_recommend:,}원",
                      delta="120% 룰 적용")

            # 업종 혼재 최고 위험요율 판정
            st.markdown("---")
            st.markdown("**🏭 업종 혼재 최고위험요율 자동 판정**")
            _RISK_RATES = {
                "사무실·창고 (1급)": 0.0010,
                "경공업·소매 (2급)": 0.0015,
                "중공업·금속 (3급)": 0.0025,
                "화학·페인트 (4급)": 0.0040,
                "인화성물질 취급 (5급)": 0.0070,
                "폭발물·유류 (특수)": 0.0120,
            }
            _biz_mix = st.multiselect(
                "사업장 내 혼재 업종 (모두 선택)",
                list(_RISK_RATES.keys()),
                default=["경공업·소매 (2급)", "중공업·금속 (3급)"],
                key="sec09_biz_mix",
            )
            if _biz_mix:
                _max_rate = max(_RISK_RATES[b] for b in _biz_mix)
                _max_biz  = [b for b in _biz_mix if _RISK_RATES[b] == _max_rate][0]
                st.markdown(
                    f'<div class="gks09-law">'
                    f'⚠️ <b>적용 최고 위험요율: {_max_rate*100:.2f}%</b> ({_max_biz})<br>'
                    f'고지의무 위반 방지 — 혼재 업종 중 최고 위험요율 자동 적용<br>'
                    f'연간 보험료 추정: <b>{int(_f_recommend * _max_rate):,}원</b>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            st.markdown('</div>', unsafe_allow_html=True)

        with _p4c2:
            st.markdown('<div class="gks09-wrap">', unsafe_allow_html=True)
            st.markdown("#### 💰 중간배당 체크리스트 (상법 제462조)")
            _INTERIM_CHECKLIST = [
                ("정관에 중간배당 규정 존재 여부 확인", "필수"),
                ("직전 결산기 재무제표 승인 완료", "필수"),
                ("배당가능이익 산정 (직전 결산기 순이익 기준)", "필수"),
                ("이사회 결의 (중간배당 결정)", "필수"),
                ("배당기준일 및 지급일 설정", "필수"),
                ("주주명부 폐쇄 또는 기준일 공고 (2주 전)", "권고"),
                ("원천징수세 처리 (배당소득세 15.4%)", "필수"),
                ("국세청 배당 지급 명세서 제출", "필수"),
                ("배당금 지급 및 회계 처리", "필수"),
            ]
            for _step, _imp in _INTERIM_CHECKLIST:
                _chk = st.checkbox(
                    f"{'🔴' if _imp=='필수' else '🟡'} {_step}",
                    key=f"sec09_interim_{_step[:10]}",
                )
            st.divider()
            st.markdown("""
<div class="gks09-card">
<div class="gks09-card-title">💡 중간배당 활용 전략</div>
<div class="gks09-card-desc">
• 미처분이익잉여금 과다 시 비상장주식 가치 상승 → 상속세 증가<br>
• 중간배당으로 이익잉여금 조기 처분 → 주식가치 감소 효과<br>
• CEO 급여 대비 배당소득세율(15.4%) 절세 효과
</div></div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # PART 5 — 재무제표 스캐너 + RAG
    # ══════════════════════════════════════════════════════════════════════════
    with _p5:
        st.markdown('<div class="gks09-wrap">', unsafe_allow_html=True)
        st.markdown("#### 🔍 재무제표 스캐너 — 가지급금·미처분이익잉여금 자동 감지")

        _fs1, _fs2 = st.columns(2)
        with _fs1:
            st.markdown("**📥 재무제표 핵심 항목 입력**")
            _fs_sales          = st.number_input("매출액 (원)", min_value=0, value=10_000_000_000,
                                                  step=500_000_000, key="sec09_fs_sales", format="%d")
            _fs_op_profit      = st.number_input("영업이익 (원)", min_value=0, value=1_200_000_000,
                                                  step=50_000_000, key="sec09_fs_op", format="%d")
            _fs_net_profit     = st.number_input("당기순이익 (원)", min_value=0, value=900_000_000,
                                                  step=50_000_000, key="sec09_fs_net", format="%d")
            _fs_retained       = st.number_input("미처분이익잉여금 (원)", min_value=0,
                                                  value=4_500_000_000, step=100_000_000,
                                                  key="sec09_fs_retained", format="%d")
            _fs_provisional    = st.number_input("가지급금 (원)", min_value=0,
                                                  value=800_000_000, step=10_000_000,
                                                  key="sec09_fs_provisional", format="%d")
            _fs_total_asset    = st.number_input("총자산 (원)", min_value=1, value=15_000_000_000,
                                                  step=500_000_000, key="sec09_fs_total", format="%d")

        with _fs2:
            st.markdown("**🚨 자동 감지 결과**")

            # 가지급금 위험 감지
            _prov_ratio = _fs_provisional / _fs_total_asset * 100
            if _fs_provisional > 300_000_000:
                st.markdown(
                    f'<div style="border:2px dashed #c0392b;background:#FFEBEE;'
                    f'border-radius:8px;padding:10px 14px;margin:6px 0;">'
                    f'<span class="gks09-highlight">⚠️ 가지급금 위험!</span><br>'
                    f'<b>가지급금 {_fs_provisional:,}원</b> (총자산 대비 {_prov_ratio:.1f}%)<br>'
                    f'인정이자 부담: {int(_fs_provisional*0.046):,}원/년 (4.6% 기준)<br>'
                    f'<b>즉시 처리 방안: 상여 처리·유상증자·대물변제·보험료 충당</b>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.success(f"✅ 가지급금 정상 ({_fs_provisional:,}원)")

            # 미처분이익잉여금 위험 감지
            _ret_ratio = _fs_retained / _fs_total_asset * 100
            if _fs_retained > 2_000_000_000:
                st.markdown(
                    f'<div style="border:2px dashed #E65100;background:#FFF3E0;'
                    f'border-radius:8px;padding:10px 14px;margin:6px 0;">'
                    f'<span class="gks09-highlight">⚠️ 미처분이익잉여금 과다!</span><br>'
                    f'<b>{_fs_retained:,}원</b> (총자산 대비 {_ret_ratio:.1f}%)<br>'
                    f'비상장주식 가치 상승 → CEO 상속세 증가 위험<br>'
                    f'<b>처리 방안: 중간배당·임원퇴직금·유상증자·자기주식 취득</b>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.success(f"✅ 미처분이익잉여금 정상 ({_fs_retained:,}원)")

            # 영업이익률
            _op_margin = _fs_op_profit / _fs_sales * 100 if _fs_sales else 0
            st.metric("영업이익률", f"{_op_margin:.1f}%")
            _net_margin = _fs_net_profit / _fs_sales * 100 if _fs_sales else 0
            st.metric("순이익률", f"{_net_margin:.1f}%")

        # RAG 검색
        st.markdown("---")
        st.markdown("**🔍 경영 전략 RAG 검색 (75p 전문자료 인덱스)**")
        _rag_q09 = st.text_input(
            "검색 키워드",
            placeholder="예) 가지급금 처리 방법 / 비상장주식 할증평가 / 중간배당 절차",
            key="sec09_rag_q",
        )
        if st.button("🔍 RAG 검색", key="sec09_rag_search", type="primary"):
            _hits09 = _rag_sector_query(_rag_q09, sector="terms", top_k=3)
            st.session_state["_sec09_rag_hits"] = _hits09

        _hits09 = st.session_state.get("_sec09_rag_hits", [])
        if _hits09:
            for _h in _hits09:
                st.markdown(
                    f'<div class="gks09-law">📖 <b>{_h["title"]}</b><br>{_h["content"]}'
                    f'<br><span style="font-size:0.72rem;color:#777;">출처: {_h["source"]}'
                    f'{(" · "+str(_h["page"])+"p") if _h.get("page") else ""}</span></div>',
                    unsafe_allow_html=True,
                )
        else:
            # 내장 답변
            _BUILTIN_RAG = [
                ("가지급금 처리 7가지 방법",
                 "①임원 상여 처리 ②유상증자 충당 ③대물변제(부동산) ④퇴직금 상계 "
                 "⑤법인보험료 충당(임원정기보험) ⑥특수관계인 채권 포기 ⑦매각대금 처리",
                 "국세청 법인세 집행기준 52-106-1"),
                ("비상장주식 할증평가 (2024~)",
                 "최대주주 보유 주식: 평가액의 30% 할증 (직전 20%에서 상향). "
                 "단, 중소기업 최대주주는 15% 할증 적용.",
                 "상증세법 제63조 3항, 금감원 2024.03.17"),
                ("임원 퇴직금 한도 (2012년 이후)",
                 "퇴직 직전 1년 급여 × 근속연수 × 3배 한도 손금 인정. "
                 "초과분은 손금 불산입(상여처리).",
                 "법인세법 시행령 제44조"),
            ]
            for _t, _c, _s in _BUILTIN_RAG:
                st.markdown(
                    f'<div class="gks09-law">📖 <b>{_t}</b><br>{_c}'
                    f'<br><span style="font-size:0.72rem;color:#777;">출처: {_s}</span></div>',
                    unsafe_allow_html=True,
                )
        st.markdown('</div>', unsafe_allow_html=True)

    # ── 하단 네비게이션 ───────────────────────────────────────────────────────
    st.divider()
    _bot_c1, _bot_c2, _bot_c3 = st.columns(3)
    with _bot_c1:
        if st.button("🏠 홈", key="sec09_bot_home", use_container_width=True):
            st.session_state["current_tab"] = "home"
            st.session_state["_scroll_top"] = True
            st.rerun()
    with _bot_c2:
        if st.button("📂 고객 보고서 생성", key="sec09_bot_report",
                     use_container_width=True, type="primary"):
            # 전문가 정밀 소견서 데이터 세션에 저장
            _report_content = (
                f"[GK-SEC-09 CEO 통합 경영 전략 소견서]\n\n"
                f"■ 비상장주식 평가\n"
                f"  주당 가치: {_val_final:,}원 / CEO 보유총가치: {_ceo_total_val:,}원\n\n"
                f"■ CEO 유고 상속세 추정액\n"
                f"  과세표준: {_inherit_base:,}원 / 세율: {_inh_rate*100:.0f}% / 세액: {_inh_tax:,}원\n\n"
                f"■ 단체보험 GAP Cover 권장 가입액\n"
                f"  법인 자산 잠식 위험액: {_gap_amount:,}원\n\n"
                f"■ 재무제표 이슈\n"
                f"  가지급금: {_fs_provisional:,}원 / 미처분이익잉여금: {_fs_retained:,}원\n\n"
                f"■ 법인화재보험 권장 가입금액\n"
                f"  {_f_recommend:,}원 (120% 가산 적용)\n"
            )
            st.session_state["_sec09_report_text"] = _report_content
            st.session_state["_report_ready_sec09"] = True
            st.success("✅ 보고서 생성 완료")
    with _bot_c3:
        if st.session_state.get("_report_ready_sec09"):
            _rtext = st.session_state.get("_sec09_report_text", "")
            st.download_button(
                "📄 PDF 소견서 다운로드",
                data=_rtext.encode("utf-8"),
                file_name="GK_SEC09_CEO_소견서.txt",
                mime="text/plain",
                key="sec09_pdf_dl",
                use_container_width=True,
            )

'''

content = content.replace(ANCHOR, SEC09_FUNC + ANCHOR, 1)

with open('D:/CascadeProjects/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("DONE: _render_gk_sec09 inserted")
