# =============================================================================
# [GP-PENSION-UI] 현실 타격형 연금 5:5 마스터 대시보드
# 좌측(#FFF0F5 연분홍) + 우측(#F0F8FF 연하늘) 전문가용 파스텔 테마
# =============================================================================
#
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  💰 PENSION MASTER DASHBOARD 5:5                                          ║
# ╠═══════════════════════════════════════════════════════════════════════════╣
# ║  Purpose: 상담 현장에서 태블릿을 고객 쪽으로 돌렸을 때                     ║
# ║           "이건 국가 통계와 법령에 기반한 과학적 분석입니다"               ║
# ║           라는 확신을 주는 전문가용 대시보드                               ║
# ║                                                                           ║
# ║  Layout:                                                                  ║
# ║  ┌─────────────────┬─────────────────┐                                   ║
# ║  │ 좌측 (입력부)    │ 우측 (분석부)    │                                   ║
# ║  │ #FFF0F5 연분홍   │ #F0F8FF 연하늘   │                                   ║
# ║  │ 따뜻한 환대      │ 냉철한 AI 분석   │                                   ║
# ║  └─────────────────┴─────────────────┘                                   ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

import streamlit as st
from typing import Dict, Optional
from pension_engine import (
    run_pension_analysis,
    format_pension_report,
    PensionAnalysisResult,
    REGIONAL_LIVING_COST,
    FOUR_TIER_REPLACEMENT_RATE,
    TAX_DEDUCTION_RATE,
    INFLATION_SCENARIOS,
)


# ══════════════════════════════════════════════════════════════════════════════
# [CSS] 5:5 대시보드 전용 스타일
# ══════════════════════════════════════════════════════════════════════════════

def inject_pension_dashboard_css():
    """연금 대시보드 전용 CSS 주입"""
    st.markdown("""
    <style>
    /* 5:5 대시보드 컨테이너 */
    .pension-dashboard-container {
        display: flex;
        gap: 20px;
        margin: 20px 0;
    }
    
    /* 좌측 입력부 - 연분홍 (#FFF0F5) */
    .pension-left-panel {
        flex: 1;
        background: #FFF0F5;
        border: 2px solid #607D8B;
        border-radius: 8px;
        padding: 24px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* 우측 분석부 - 연하늘 (#F0F8FF) */
    .pension-right-panel {
        flex: 1;
        background: #F0F8FF;
        border: 2px solid #607D8B;
        border-radius: 8px;
        padding: 24px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* 섹션 헤더 */
    .pension-section-header {
        font-size: clamp(16px, 4vw, 20px);
        font-weight: 900;
        color: #1a237e;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 2px dashed #607D8B;
    }
    
    /* 데이터 카드 */
    .pension-data-card {
        background: white;
        border: 1px dashed #000;
        border-radius: 4px;
        padding: 16px;
        margin-bottom: 16px;
    }
    
    /* 메트릭 라벨 */
    .pension-metric-label {
        font-size: clamp(12px, 3vw, 14px);
        color: #546e7a;
        margin-bottom: 4px;
    }
    
    /* 메트릭 값 */
    .pension-metric-value {
        font-size: clamp(18px, 5vw, 24px);
        font-weight: 900;
        color: #1a237e;
    }
    
    /* 경고 박스 */
    .pension-warning-box {
        background: #fff3cd;
        border: 2px solid #ffc107;
        border-radius: 4px;
        padding: 12px;
        margin: 12px 0;
    }
    
    .pension-danger-box {
        background: #f8d7da;
        border: 2px solid #dc3545;
        border-radius: 4px;
        padding: 12px;
        margin: 12px 0;
    }
    
    .pension-success-box {
        background: #d4edda;
        border: 2px solid #28a745;
        border-radius: 4px;
        padding: 12px;
        margin: 12px 0;
    }
    
    /* 4층 보장 바 차트 */
    .pension-tier-bar {
        display: flex;
        height: 40px;
        border-radius: 4px;
        overflow: hidden;
        margin: 16px 0;
        border: 1px solid #607D8B;
    }
    
    .pension-tier-segment {
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 700;
        font-size: clamp(10px, 2.5vw, 12px);
        transition: all 0.3s;
    }
    
    .pension-tier-segment:hover {
        opacity: 0.8;
        transform: scale(1.05);
    }
    
    /* 세제 가이드 테이블 */
    .pension-tax-table {
        width: 100%;
        border-collapse: collapse;
        margin: 16px 0;
        font-size: clamp(11px, 3vw, 13px);
    }
    
    .pension-tax-table th {
        background: #1a237e;
        color: white;
        padding: 12px 8px;
        text-align: left;
        font-weight: 700;
        border: 1px solid #607D8B;
    }
    
    .pension-tax-table td {
        padding: 10px 8px;
        border: 1px dashed #607D8B;
        background: white;
    }
    
    .pension-tax-table tr:hover {
        background: #f5f5f5;
    }
    
    /* 반응형 - 모바일 스태킹 */
    @media (max-width: 768px) {
        .pension-dashboard-container {
            flex-direction: column;
        }
        
        .pension-left-panel,
        .pension-right-panel {
            width: 100% !important;
        }
        
        .pension-tier-bar {
            flex-direction: column;
            height: auto;
        }
        
        .pension-tier-segment {
            width: 100% !important;
            padding: 8px;
        }
    }
    </style>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# [UI] 좌측 입력부 렌더링
# ══════════════════════════════════════════════════════════════════════════════

def render_left_input_panel() -> Dict:
    """
    좌측 입력부 렌더링 (#FFF0F5 연분홍)
    
    Returns:
        사용자 입력값 딕셔너리
    """
    st.markdown('<div class="pension-section-header">📝 고객 정보 입력</div>', unsafe_allow_html=True)
    
    # 기본 정보
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("현재 나이", min_value=20, max_value=70, value=40, step=1)
        retirement_age = st.number_input("은퇴 예정 나이", min_value=age+1, max_value=80, value=65, step=1)
    
    with col2:
        life_expectancy = st.number_input("기대 수명", min_value=retirement_age+1, max_value=100, value=85, step=1)
        monthly_salary = st.number_input("월 급여 (만원)", min_value=0, max_value=2000, value=400, step=10) * 10000
    
    st.markdown("---")
    
    # 지역 및 가구 구분
    st.markdown('<div class="pension-section-header">🏠 생활비 기준 설정</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        region_type = st.selectbox("거주 지역", ["광역", "중소", "농어촌"], index=0)
    
    with col2:
        household_type = st.selectbox("가구 구분", ["단독", "부부"], index=1)
    
    st.markdown("---")
    
    # 연금 납입 정보
    st.markdown('<div class="pension-section-header">💰 연금 납입 계획</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        monthly_contribution = st.number_input(
            "월 납입액 (만원)", 
            min_value=10, 
            max_value=500, 
            value=30, 
            step=10,
            help="연금저축 + IRP 합산 월 납입액"
        ) * 10000
    
    with col2:
        annual_return_rate = st.slider(
            "예상 연 수익률 (%)", 
            min_value=2.0, 
            max_value=8.0, 
            value=4.5, 
            step=0.5,
            help="보수적: 3~4%, 중립: 4~5%, 공격적: 5~7%"
        )
    
    st.markdown("---")
    
    # 4층 보장 정보
    st.markdown('<div class="pension-section-header">🏛️ 4층 보장 현황</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        national_pension = st.number_input(
            "국민연금 예상액 (만원/월)", 
            min_value=0, 
            max_value=500, 
            value=172,
            help="국민연금공단 예상 수령액"
        ) * 10000
        
        retirement_pension = st.number_input(
            "퇴직연금 예상액 (만원/월)", 
            min_value=0, 
            max_value=300, 
            value=64,
            help="DC형/DB형 퇴직연금 예상 수령액"
        ) * 10000
    
    with col2:
        housing_pension = st.number_input(
            "주택연금 예상액 (만원/월)", 
            min_value=0, 
            max_value=300, 
            value=54,
            help="한국주택금융공사 주택연금 예상액"
        ) * 10000
        
        annual_income = st.number_input(
            "연 총급여 (만원)", 
            min_value=0, 
            max_value=20000, 
            value=5000,
            help="세액공제율 계산용 (5,500만원 기준)"
        )
    
    st.markdown("---")
    
    # 옵션
    st.markdown('<div class="pension-section-header">⚙️ 분석 옵션</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        inflation_scenario = st.selectbox(
            "물가상승률 시나리오", 
            ["보수적", "중립", "공격적"], 
            index=2,
            help="보수적: 3%, 중립: 4%, 공격적: 5%"
        )
    
    with col2:
        use_trinity_mode = st.checkbox(
            "트리니티 4% 모드", 
            value=False,
            help="원금 보존하며 연 4%만 인출 (안전 인출률)"
        )
    
    return {
        "age": age,
        "retirement_age": retirement_age,
        "life_expectancy": life_expectancy,
        "region_type": region_type,
        "household_type": household_type,
        "monthly_contribution": monthly_contribution,
        "annual_return_rate": annual_return_rate,
        "monthly_salary": monthly_salary,
        "national_pension_amt": national_pension,
        "retirement_pension_amt": retirement_pension,
        "housing_pension_amt": housing_pension,
        "inflation_scenario": inflation_scenario,
        "use_trinity_mode": use_trinity_mode,
        "annual_income": annual_income,
    }


# ══════════════════════════════════════════════════════════════════════════════
# [UI] 우측 분석부 렌더링
# ══════════════════════════════════════════════════════════════════════════════

def render_right_analysis_panel(result: PensionAnalysisResult, inputs: Dict):
    """
    우측 분석부 렌더링 (#F0F8FF 연하늘)
    
    Args:
        result: 연금 분석 결과
        inputs: 사용자 입력값
    """
    st.markdown('<div class="pension-section-header">📊 AI 연금 전략 분석</div>', unsafe_allow_html=True)
    
    # 1. 적립기 요약
    st.markdown(f"""
    <div class="pension-data-card">
        <div class="pension-metric-label">🎯 {result.contribution_years}년 후 적립 예상액</div>
        <div class="pension-metric-value">{result.accumulated_amount/100000000:.2f}억원</div>
        <div style="font-size:12px; color:#546e7a; margin-top:8px;">
            월 {result.monthly_contribution/10000:.0f}만원 × {result.contribution_years}년 × 연 {result.annual_return_rate}% 복리
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. 수령기 요약
    mode_label = "트리니티 4% (원금 보존)" if inputs["use_trinity_mode"] else "표준 방식 (자산 고갈)"
    monthly_pension = result.monthly_pension_trinity if inputs["use_trinity_mode"] else result.monthly_pension_standard
    
    st.markdown(f"""
    <div class="pension-data-card">
        <div class="pension-metric-label">💵 월 수령 예상액 ({mode_label})</div>
        <div class="pension-metric-value">{monthly_pension/10000:.0f}만원/월</div>
        <div style="font-size:12px; color:#546e7a; margin-top:8px;">
            {result.pension_duration_years}년간 수령 예정
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 3. 생활비 Gap 분석 (공포 수치)
    st.markdown('<div class="pension-section-header">⚠️ 물가 반영 노후 생활비 분석</div>', unsafe_allow_html=True)
    
    inflation_rate = INFLATION_SCENARIOS[inputs["inflation_scenario"]]
    
    # Gap 심각도에 따른 박스 색상
    if result.gap_percentage > 50:
        box_class = "pension-danger-box"
        icon = "🔴"
        status = "심각"
    elif result.gap_percentage > 30:
        box_class = "pension-warning-box"
        icon = "🟡"
        status = "경고"
    elif result.gap_percentage > 0:
        box_class = "pension-warning-box"
        icon = "🟢"
        status = "주의"
    else:
        box_class = "pension-success-box"
        icon = "✅"
        status = "양호"
    
    st.markdown(f"""
    <div class="{box_class}">
        <div style="font-weight:900; font-size:16px; margin-bottom:8px;">
            {icon} {status}: 물가상승률 {inflation_rate}% 반영 시
        </div>
        <div style="font-size:14px;">
            • 현재 최소 생활비: <strong>{result.regional_living_cost/10000:.0f}만원/월</strong><br>
            • {result.contribution_years}년 후 필요 생활비: <strong>{result.inflation_adjusted_cost/10000:.0f}만원/월</strong><br>
            • 4층 보장 합계: <strong>{(result.national_pension + result.retirement_pension + result.housing_pension + result.personal_pension)/10000:.0f}만원/월</strong><br>
            • <span style="color:#d32f2f; font-weight:900;">부족 금액: {result.gap_amount/10000:.0f}만원/월 ({result.gap_percentage:.1f}%)</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 4. 4층 보장 소득대체율 시각화
    st.markdown('<div class="pension-section-header">🏛️ 4층 보장 소득대체율</div>', unsafe_allow_html=True)
    
    if inputs["monthly_salary"] > 0:
        national_pct = (result.national_pension / inputs["monthly_salary"] * 100)
        retirement_pct = (result.retirement_pension / inputs["monthly_salary"] * 100)
        housing_pct = (result.housing_pension / inputs["monthly_salary"] * 100)
        personal_pct = (result.personal_pension / inputs["monthly_salary"] * 100)
        
        st.markdown(f"""
        <div class="pension-tier-bar">
            <div class="pension-tier-segment" style="width:{national_pct}%; background:#1976d2;">
                국민연금<br>{national_pct:.1f}%
            </div>
            <div class="pension-tier-segment" style="width:{retirement_pct}%; background:#388e3c;">
                퇴직연금<br>{retirement_pct:.1f}%
            </div>
            <div class="pension-tier-segment" style="width:{housing_pct}%; background:#f57c00;">
                주택연금<br>{housing_pct:.1f}%
            </div>
            <div class="pension-tier-segment" style="width:{personal_pct}%; background:#7b1fa2;">
                개인연금<br>{personal_pct:.1f}%
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="text-align:center; font-size:14px; color:#546e7a; margin-top:8px;">
            총 소득대체율: <strong style="color:#1a237e; font-size:18px;">{result.total_replacement_rate:.1f}%</strong>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 5. 세제 혜택
    st.markdown('<div class="pension-section-header">💸 세제 혜택 분석</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="pension-data-card">
        <div style="display:flex; justify-content:space-between; margin-bottom:12px;">
            <div>
                <div class="pension-metric-label">연간 세액공제</div>
                <div class="pension-metric-value" style="font-size:20px;">{result.annual_tax_benefit/10000:.0f}만원</div>
            </div>
            <div>
                <div class="pension-metric-label">{result.contribution_years}년 총 혜택</div>
                <div class="pension-metric-value" style="font-size:20px;">{result.total_tax_benefit/10000:.0f}만원</div>
            </div>
        </div>
        <div style="font-size:12px; color:#546e7a;">
            연 총급여 {inputs['annual_income']}만원 기준 세액공제율 적용
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 6. 경고 메시지
    st.markdown('<div class="pension-section-header">⚠️ 리스크 경고</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="pension-warning-box">
        <div style="font-weight:700; margin-bottom:8px;">유지율 리스크</div>
        <div style="font-size:13px;">{result.persistence_risk}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="pension-danger-box">
        <div style="font-weight:700; margin-bottom:8px;">세제 리스크</div>
        <div style="font-size:13px;">{result.tax_risk}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 7. 2026 개인연금 세제 가이드
    st.markdown('<div class="pension-section-header">📋 2026 개인연금 세제 가이드</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <table class="pension-tax-table">
        <thead>
            <tr>
                <th>구분</th>
                <th>기준</th>
                <th>세액공제율</th>
                <th>최대 환급액</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>저소득 구간</strong></td>
                <td>총급여 5,500만원 이하</td>
                <td>16.5%</td>
                <td>148.5만원 (900만원 납입 시)</td>
            </tr>
            <tr>
                <td><strong>고소득 구간</strong></td>
                <td>총급여 5,500만원 초과</td>
                <td>13.2%</td>
                <td>118.8만원 (900만원 납입 시)</td>
            </tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="pension-data-card">
        <div style="font-weight:700; margin-bottom:12px; color:#1a237e;">💡 효율적 납입 전략</div>
        <div style="font-size:13px; line-height:1.8;">
            <strong>1단계:</strong> 연금저축(펀드/보험)에 <strong>600만원</strong> 선순위 납입<br>
            <strong>2단계:</strong> IRP에 추가 <strong>300만원</strong> 납입 (합산 900만원 세액공제 풀 세트)<br>
            <strong>3단계:</strong> 10년 만기 '주머니 쪼개기' 전략으로 중도 해지 리스크 분산<br>
            <strong>4단계:</strong> 연금 수령 5년 연기로 세제 혜택 극대화
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 8. 출처 표기
    st.markdown("""
    <div style="margin-top:24px; padding-top:12px; border-top:1px dashed #607D8B; font-size:11px; color:#78909c; text-align:center;">
        출처: 국가통계포털(KOSIS) · 국민연금공단 · 한국주택금융공사 · 금융감독원 2024~2025
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# [MAIN] 5:5 대시보드 메인 렌더링 함수
# ══════════════════════════════════════════════════════════════════════════════

def render_pension_dashboard_55():
    """
    현실 타격형 연금 5:5 마스터 대시보드 렌더링
    
    Usage:
        from modules.pension_dashboard_55 import render_pension_dashboard_55
        render_pension_dashboard_55()
    """
    # CSS 주입
    inject_pension_dashboard_css()
    
    # A/B 테스트 그룹 할당
    agent_id = st.session_state.get("user_id", "unknown")
    if "pension_ab_test_group" not in st.session_state:
        from modules.pension_analytics import get_ab_test_group, get_recommended_inflation_scenario
        test_group = get_ab_test_group(agent_id)
        st.session_state["pension_ab_test_group"] = test_group
        st.session_state["pension_recommended_scenario"] = get_recommended_inflation_scenario(test_group)
    
    # 페이지 뷰 로깅
    from modules.pension_analytics import log_dashboard_usage
    log_dashboard_usage(agent_id, page_view=True)
    
    # 타이틀
    st.markdown("""
    <div style="text-align:center; margin-bottom:24px;">
        <h1 style="color:#1a237e; font-weight:900; font-size:clamp(20px, 5vw, 28px);">
            💰 현실 타격형 연금 지능 분석
        </h1>
        <p style="color:#546e7a; font-size:clamp(12px, 3vw, 14px);">
            금융공학 기반 복리 산식 + 2024~2025 실전 타겟 데이터
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 5:5 레이아웃
    left_col, right_col = st.columns(2)
    
    with left_col:
        st.markdown('<div class="pension-left-panel">', unsafe_allow_html=True)
        inputs = render_left_input_panel()
        
        # 분석 실행 버튼
        analyze_button = st.button(
            "🚀 연금 분석 실행",
            type="primary",
            use_container_width=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with right_col:
        st.markdown('<div class="pension-right-panel">', unsafe_allow_html=True)
        
        if analyze_button or st.session_state.get("pension_analysis_result"):
            # 분석 실행
            if analyze_button:
                with st.spinner("🔬 AI가 연금 전략을 분석 중입니다..."):
                    result = run_pension_analysis(**inputs)
                    st.session_state["pension_analysis_result"] = result
                    st.session_state["pension_inputs"] = inputs
                    
                    # 분석 로그 기록
                    from modules.pension_analytics import log_pension_analysis, log_dashboard_usage
                    log_pension_analysis(
                        agent_id=agent_id,
                        analysis_params=inputs,
                        analysis_result=result.__dict__,
                    )
                    
                    # 대시보드 사용 통계 (분석 실행)
                    log_dashboard_usage(agent_id, analysis_run=True)
            
            # 결과 렌더링
            render_right_analysis_panel(
                st.session_state["pension_analysis_result"],
                st.session_state["pension_inputs"]
            )
        else:
            # 초기 안내 메시지
            st.markdown("""
            <div style="text-align:center; padding:60px 20px; color:#78909c;">
                <div style="font-size:48px; margin-bottom:16px;">📊</div>
                <div style="font-size:18px; font-weight:700; margin-bottom:8px;">
                    AI 연금 분석 대기 중
                </div>
                <div style="font-size:14px;">
                    좌측에서 고객 정보를 입력하고<br>
                    '연금 분석 실행' 버튼을 눌러주세요
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# [TEST] 테스트 실행
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    st.set_page_config(
        page_title="연금 지능 분석 5:5 대시보드",
        page_icon="💰",
        layout="wide",
    )
    
    render_pension_dashboard_55()
