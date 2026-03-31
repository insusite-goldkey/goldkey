# -*- coding: utf-8 -*-
"""
modules/property_dashboard_55.py
────────────────────────────────────────────────────────────────────────────
🏢 건물 급수 산출 5:5 대시보드 UI
화재보험 전문가 로직 - 좌측 입력 + 우측 분석창
────────────────────────────────────────────────────────────────────────────
"""
import streamlit as st
from modules.property_engine import (
    classify_building_grade,
    calculate_premium,
    calculate_asset_valuation,
    calculate_coinsurance_payout,
    calculate_replacement_cost_by_area,
    get_structure_options,
    get_roof_options,
    get_wall_options,
    get_building_use_options,
    format_grade_result,
    format_asset_valuation,
    format_coinsurance_result,
    get_land_exclusion_warning,
    get_underinsurance_warning_2026,
)
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────────
# §1  CSS 스타일 (파스텔 테마)
# ─────────────────────────────────────────────────────────────────────────────

def inject_property_dashboard_css():
    """건물 급수 대시보드 전용 CSS 주입."""
    st.markdown("""
    <style>
    /* 좌측 입력 패널 (연분홍) */
    .property-left-panel {
        background: linear-gradient(135deg, #FFF0F5 0%, #FFE4E9 100%);
        border: 1px dashed #607D8B;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 16px;
    }
    
    /* 우측 분석 패널 (연하늘) */
    .property-right-panel {
        background: linear-gradient(135deg, #F0F8FF 0%, #E6F3FF 100%);
        border: 1px dashed #607D8B;
        border-radius: 12px;
        padding: 24px;
        min-height: 500px;
    }
    
    /* 급수 배지 */
    .grade-badge {
        display: inline-block;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 900;
        font-size: 18px;
        margin: 8px 0;
    }
    
    .grade-1 {
        background: linear-gradient(135deg, #4CAF50 0%, #66BB6A 100%);
        color: white;
    }
    
    .grade-2 {
        background: linear-gradient(135deg, #2196F3 0%, #42A5F5 100%);
        color: white;
    }
    
    .grade-3 {
        background: linear-gradient(135deg, #FF9800 0%, #FFB74D 100%);
        color: white;
    }
    
    .grade-4 {
        background: linear-gradient(135deg, #F44336 0%, #EF5350 100%);
        color: white;
    }
    
    /* 위험도 표시 */
    .risk-indicator {
        padding: 12px;
        border-radius: 8px;
        margin: 12px 0;
        font-weight: 700;
    }
    
    .risk-low {
        background: #E8F5E9;
        border-left: 4px solid #4CAF50;
    }
    
    .risk-medium {
        background: #E3F2FD;
        border-left: 4px solid #2196F3;
    }
    
    .risk-high {
        background: #FFF3E0;
        border-left: 4px solid #FF9800;
    }
    
    .risk-very-high {
        background: #FFEBEE;
        border-left: 4px solid #F44336;
    }
    
    /* 보험료 표시 */
    .premium-box {
        background: white;
        border: 1px dashed #607D8B;
        border-radius: 8px;
        padding: 16px;
        margin: 16px 0;
    }
    
    .premium-amount {
        font-size: 28px;
        font-weight: 900;
        color: #1976D2;
    }
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# §2  좌측 입력 패널
# ─────────────────────────────────────────────────────────────────────────────

def render_left_input_panel() -> dict:
    """
    좌측 입력 패널 렌더링.
    
    Returns:
        사용자 입력값 딕셔너리
    """
    st.markdown("### 🏗️ 건물 정보 입력")
    
    # 구조 선택
    structure = st.selectbox(
        "기둥/보/바닥 구조",
        options=get_structure_options(),
        help="건물의 주요 구조 재료를 선택하세요",
    )
    
    # 지붕 선택
    roof = st.selectbox(
        "지붕 재료",
        options=get_roof_options(),
        help="지붕의 재료를 선택하세요",
    )
    
    # 외벽 선택
    wall = st.selectbox(
        "외벽 재료",
        options=get_wall_options(),
        help="외벽의 재료를 선택하세요",
    )
    
    st.markdown("---")
    st.markdown("### 💰 자산 가치 평가 (2026년 기준)")
    
    # 계산 방식 선택
    calc_method = st.radio(
        "재조달가액 계산 방식",
        options=["면적 기반 자동 계산", "직접 입력"],
        help="면적 기반 자동 계산 시 2026년 용도별 평당 단가를 적용합니다",
    )
    
    if calc_method == "면적 기반 자동 계산":
        # 건물 용도 선택
        building_use = st.selectbox(
            "건물 용도",
            options=get_building_use_options(),
            help="건물의 주요 용도를 선택하세요 (2026년 평당 단가 적용)",
        )
        
        # 연면적 입력
        area_pyeong = st.number_input(
            "연면적 (평)",
            min_value=10.0,
            max_value=10000.0,
            value=100.0,
            step=10.0,
            help="건물의 전체 연면적을 평 단위로 입력하세요",
        )
        
        # 친환경/스마트 빌딩 여부
        is_green_building = st.checkbox(
            "친환경/스마트 빌딩",
            value=False,
            help="친환경 인증 또는 스마트 빌딩 설비가 있는 경우 체크 (15~20% 프리미엄 적용)",
        )
        
        # 재조달가액 자동 계산
        rc_calc = calculate_replacement_cost_by_area(
            area_pyeong=area_pyeong,
            building_use=building_use,
            is_green_building=is_green_building,
        )
        replacement_cost = rc_calc["total_replacement_cost"]
        
        # 계산 결과 표시
        st.info(f"""
        **자동 계산 결과**  
        - 평당 단가: {rc_calc['unit_price']:,.0f}만원  
        - 기본 비용: {rc_calc['base_cost']:,.0f}만원  
        - 부대비용 (5%): {rc_calc['overhead_cost']:,.0f}만원  
        - **재조달가액 (신가): {replacement_cost:,.0f}만원**
        """)
    else:
        # 직접 입력
        building_use = None
        area_pyeong = None
        is_green_building = False
        
        replacement_cost = st.number_input(
            "재조달가액 (신가, 만원)",
            min_value=1000,
            max_value=1000000,
            value=100000,
            step=1000,
            help="사고 시점에 건물을 새로 짓는 데 드는 비용 (신가)",
        )
    
    # 토지 가액 배제 경고
    with st.expander("⚠️ 중요: 토지 가액 배제 원칙"):
        st.warning(get_land_exclusion_warning())
    
    # 건축 연도 입력
    current_year = datetime.now().year
    building_year = st.number_input(
        "건축 연도",
        min_value=1950,
        max_value=current_year,
        value=2004,
        step=1,
        help="건물이 지어진 연도를 입력하세요",
    )
    
    st.markdown("---")
    st.markdown("### 🚨 80% 코인슈어런스 시뮬레이션")
    
    # 가입금액 입력
    insured_amount = st.number_input(
        "가입금액 (만원)",
        min_value=1000,
        max_value=1000000,
        value=70000,
        step=1000,
        help="실제 가입하려는 보험금액",
    )
    
    # 손해액 입력
    loss_amount = st.number_input(
        "예상 손해액 (만원)",
        min_value=100,
        max_value=100000,
        value=5000,
        step=100,
        help="사고 발생 시 예상되는 손해액",
    )
    
    return {
        "structure": structure,
        "roof": roof,
        "wall": wall,
        "replacement_cost": replacement_cost,
        "building_year": building_year,
        "current_year": current_year,
        "insured_amount": insured_amount,
        "loss_amount": loss_amount,
        "building_use": building_use,
        "area_pyeong": area_pyeong,
        "is_green_building": is_green_building,
    }


# ─────────────────────────────────────────────────────────────────────────────
# §3  우측 분석 패널
# ─────────────────────────────────────────────────────────────────────────────

def render_right_analysis_panel(result, valuation, coinsurance, premium_info):
    """
    우측 분석 패널 렌더링.
    
    Args:
        result: BuildingGradeResult 객체
        valuation: AssetValuation 객체
        coinsurance: CoinsuranceResult 객체
        premium_info: 보험료 정보 딕셔너리
    """
    # 급수 배지
    grade_class = f"grade-{result.grade}"
    st.markdown(f"""
    <div class="grade-badge {grade_class}">
        {result.grade_name} ({result.grade}급)
    </div>
    """, unsafe_allow_html=True)
    
    # 위험도 표시
    risk_class_map = {
        "낮음": "risk-low",
        "보통": "risk-medium",
        "높음": "risk-high",
        "매우높음": "risk-very-high",
    }
    risk_class = risk_class_map.get(result.risk_level, "risk-medium")
    
    risk_emoji = {
        "낮음": "✅",
        "보통": "⚠️",
        "높음": "🔥",
        "매우높음": "🚨",
    }
    
    st.markdown(f"""
    <div class="risk-indicator {risk_class}">
        {risk_emoji.get(result.risk_level, "⚠️")} <strong>위험도: {result.risk_level}</strong>
    </div>
    """, unsafe_allow_html=True)
    
    # 건물 정보
    st.markdown("### 🏗️ 건물 구성")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("구조", result.structure)
    with col2:
        st.metric("지붕", result.roof)
    with col3:
        st.metric("외벽", result.wall)
    
    # 요율 정보
    st.markdown("### 💰 요율 정보")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("기본 요율", f"{result.final_rate:.2f}%")
    with col2:
        st.metric("할증률 (1급 대비)", f"{result.surcharge_rate:.0f}%")
    
    # 보험료 계산
    st.markdown("### 💵 예상 보험료")
    st.markdown(f"""
    <div class="premium-box">
        <div style="font-size: 14px; color: #666; margin-bottom: 8px;">
            건물 가액: {premium_info['building_value']:,}만원
        </div>
        <div style="margin-bottom: 12px;">
            <div style="font-size: 16px; font-weight: 700; color: #333;">연간 보험료</div>
            <div class="premium-amount">{premium_info['annual_premium']:,}원</div>
        </div>
        <div>
            <div style="font-size: 16px; font-weight: 700; color: #333;">월 보험료</div>
            <div style="font-size: 24px; font-weight: 900; color: #FF6B6B;">
                {premium_info['monthly_premium']:,}원
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 권장사항
    st.markdown("### 💡 권장사항")
    st.info(result.recommendation)
    
    # 상세 설명
    with st.expander("📝 상세 설명 보기"):
        st.markdown(result.details)
    
    # 자산 가치 평가 결과
    st.markdown("---")
    st.markdown("### 💰 자산 가치 평가")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("재조달가액 (신가)", f"{valuation.replacement_cost:,.0f}만원")
        st.metric("건축 경과년수", f"{valuation.building_age}년")
        st.metric("연간 감가율", f"{valuation.depreciation_rate:.2f}%")
    with col2:
        st.metric("총 감가액", f"{valuation.total_depreciation:,.0f}만원")
        st.metric("보험가액 (시가)", f"{valuation.actual_cash_value:,.0f}만원")
        st.metric("80% 최소액", f"{valuation.coinsurance_minimum:,.0f}만원")
    
    # 재조달가액 vs 보험가액 설명
    with st.expander("💡 재조달가액 vs 보험가액 설명"):
        st.markdown("""
        **재조달가액 (Replacement Cost)**  
        사고 시점에 건물을 새 상태로 복구하는 데 필요한 현재 시장 가격 (신가)
        
        **보험가액 (Actual Cash Value)**  
        재조달가액에서 건물의 노후화(감가상각)를 뺀 현재의 실제 가치 (시가)
        
        **공식**: 보험가액 = 재조달가액 - 경년감가액
        """)
    
    # 80% 코인슈어런스 시뮬레이션 결과
    st.markdown("---")
    st.markdown("### 🚨 80% 코인슈어런스 시뮬레이션")
    
    # 2026년 과소 보험 경고
    with st.expander("🚨 2026년 긴급 경고: 과소 보험 위험"):
        st.error(get_underinsurance_warning_2026())
    
    # 경고 메시지 (과소 보험인 경우)
    if not coinsurance.is_adequate:
        shortage_pct = (1 - coinsurance.penalty_ratio) * 100
        shortage_amount = coinsurance.coinsurance_minimum - coinsurance.insured_amount
        st.error(f"""
        🚨 **과소 보험 경고!**
        
        현재 물가 상승으로 인해 고객님의 건물은 80% 기준 미달입니다.  
        사고 시 보상액이 **{shortage_pct:.1f}% 삭감**될 위험이 있습니다.
        
        - 부족 금액: {shortage_amount:,.0f}만원
        - 보상 삭감률: {shortage_pct:.1f}%
        - 실제 지급액: {coinsurance.actual_payout:,.0f}만원 (손해액 {coinsurance.loss_amount:,.0f}만원 중)
        
        **재평가가 시급합니다!** 현재 건물 가치를 재산정하여 적정 가입금액을 확인하세요.
        """)
    else:
        st.success(coinsurance.warning_message)
    
    # 시뮬레이션 결과 표
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("가입금액", f"{coinsurance.insured_amount:,.0f}만원")
        st.metric("가입 비율", f"{(coinsurance.insured_amount/coinsurance.actual_cash_value*100):.1f}%")
    with col2:
        st.metric("손해액", f"{coinsurance.loss_amount:,.0f}만원")
        st.metric("비례보상 비율", f"{coinsurance.penalty_ratio*100:.1f}%")
    with col3:
        st.metric("실제 지급액", f"{coinsurance.actual_payout:,.0f}만원")
        st.metric("패널티 금액", f"{coinsurance.penalty_amount:,.0f}만원")
    
    # 80% 코인슈어런스 설명
    with st.expander("💡 80% 코인슈어런스란?"):
        st.markdown("""
        **80% 코인슈어런스 (Co-insurance Clause)**  
        재물보험에서 사고 발생 시 실제 손해액 전액을 보상받기 위한 부보 비율 규칙
        
        **의무 가입 기준**: 건물 가액(보험가액)의 80% 이상 설정 필수
        
        **비례 보상 공식**:  
        보험금 = 손해액 × (실제 가입금액 / (보험가액 × 80%))
        
        **핵심**:
        - 보험가액의 80% 이상 가입 시: 실손보상 (손해액 전액)
        - 80% 미만 가입 시: 비례보상 (패널티 적용)
        """)
    
    # 1급 대비 비교 (1급이 아닌 경우)
    st.markdown("---")
    if result.grade != 1:
        st.markdown("### 📊 1급 건물과 비교")
        grade1_premium = premium_info['building_value'] * 10000 * 0.0005
        diff_premium = premium_info['annual_premium'] - grade1_premium
        
        st.markdown(f"""
        <div style="background: #FFF9C4; padding: 16px; border-radius: 8px; border-left: 4px solid #FBC02D;">
            <div style="font-size: 14px; margin-bottom: 8px;">
                만약 이 건물이 <strong>1급</strong>이었다면:
            </div>
            <div style="font-size: 18px; font-weight: 700; color: #F57C00;">
                연간 <strong>{int(diff_premium):,}원</strong> 절감 가능
            </div>
            <div style="font-size: 12px; color: #666; margin-top: 8px;">
                (월 {int(diff_premium/12):,}원 절감)
            </div>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# §4  메인 대시보드 렌더링
# ─────────────────────────────────────────────────────────────────────────────

def render_property_dashboard_55():
    """건물 급수 산출 5:5 대시보드 메인 렌더링."""
    
    # CSS 주입
    inject_property_dashboard_css()
    
    # 페이지 헤더
    st.markdown("# 🏢 건물 급수 산출")
    st.markdown("화재보험 전문가 로직 - 건물 구조/지붕/외벽 기반 급수 자동 판정")
    st.markdown("---")
    
    # 5:5 레이아웃
    left_col, right_col = st.columns(2)
    
    with left_col:
        st.markdown('<div class="property-left-panel">', unsafe_allow_html=True)
        inputs = render_left_input_panel()
        
        # 분석 실행 버튼
        analyze_button = st.button(
            "🔍 급수 판정 실행",
            type="primary",
            use_container_width=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with right_col:
        st.markdown('<div class="property-right-panel">', unsafe_allow_html=True)
        
        # 분석 실행 또는 기존 결과 표시
        if analyze_button or st.session_state.get("property_grade_result"):
            if analyze_button:
                # 급수 판정
                result = classify_building_grade(
                    structure=inputs["structure"],
                    roof=inputs["roof"],
                    wall=inputs["wall"],
                )
                
                # 자산 가치 평가
                valuation = calculate_asset_valuation(
                    replacement_cost=inputs["replacement_cost"],
                    building_year=inputs["building_year"],
                    current_year=inputs["current_year"],
                    structure=inputs["structure"],
                    building_use=inputs.get("building_use"),
                    area_pyeong=inputs.get("area_pyeong"),
                    is_green_building=inputs.get("is_green_building", False),
                )
                
                # 80% 코인슈어런스 계산
                coinsurance = calculate_coinsurance_payout(
                    actual_cash_value=valuation.actual_cash_value,
                    insured_amount=inputs["insured_amount"],
                    loss_amount=inputs["loss_amount"],
                )
                
                # 보험료 계산 (보험가액 기준)
                premium_info = calculate_premium(
                    building_value=valuation.actual_cash_value,
                    grade_result=result,
                )
                
                # 세션에 저장
                st.session_state["property_grade_result"] = result
                st.session_state["property_valuation"] = valuation
                st.session_state["property_coinsurance"] = coinsurance
                st.session_state["property_premium_info"] = premium_info
                st.session_state["property_inputs"] = inputs
            
            # 결과 렌더링
            render_right_analysis_panel(
                st.session_state["property_grade_result"],
                st.session_state["property_valuation"],
                st.session_state["property_coinsurance"],
                st.session_state["property_premium_info"],
            )
        else:
            # 초기 안내 메시지
            st.markdown("""
            <div style="text-align:center; padding:60px 20px; color:#78909c;">
                <div style="font-size:48px; margin-bottom:16px;">🏢</div>
                <div style="font-size:18px; font-weight:700; margin-bottom:8px;">
                    건물 급수 판정 대기 중
                </div>
                <div style="font-size:14px;">
                    좌측에서 건물 정보를 입력하고<br>
                    '급수 판정 실행' 버튼을 눌러주세요
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# §5  테스트 실행
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    st.set_page_config(
        page_title="건물 급수 산출",
        page_icon="🏢",
        layout="wide",
    )
    render_property_dashboard_55()
