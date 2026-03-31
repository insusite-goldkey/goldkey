# ══════════════════════════════════════════════════════════════════════════════
# [GP-PENSION-ENGINE] 현실 타격형 연금 엔진
# 작성일: 2026-03-31
# 목적: 30년 후 물가 반영 연금 Gap 분석 (The Reality Check)
# ══════════════════════════════════════════════════════════════════════════════
"""
[현실 타격형 연금 엔진] 핵심 로직

## 핵심 공식
1. 물가상승률 반영: 현재가치 × (1 + 물가상승률)^년수
2. 연금 Gap: 필요 노후자금 - 현재 가입 연금
3. 월 적립액: Gap ÷ (남은 기간(개월) × 복리계수)

## UI 테마
- 배경: 연분홍(#FFF0F5) / 연하늘(#F0F8FF) 교차
- 강조: 빨강(Gap 부족) / 초록(Gap 충족)
- 레이아웃: 좌우 5:5 분할 또는 세로 스택
"""

import streamlit as st
from typing import Dict, Optional, Tuple
from datetime import datetime


# ══════════════════════════════════════════════════════════════════════════════
# § 1. 핵심 상수 (GP 헌법 제32조 준수)
# ══════════════════════════════════════════════════════════════════════════════

_INFLATION_RATE_DEFAULT = 0.025  # 연 2.5% 물가상승률 (보수적 추정)
_RETIREMENT_AGE_DEFAULT = 65     # 기본 은퇴 연령
_LIFE_EXPECTANCY_DEFAULT = 90    # 기본 기대수명
_COMPOUND_RATE_DEFAULT = 0.03    # 연 3% 복리 수익률 (보수적)


# ══════════════════════════════════════════════════════════════════════════════
# § 2. 연금 Gap 계산 엔진
# ══════════════════════════════════════════════════════════════════════════════

def calculate_future_value(
    current_value: float,
    years: int,
    inflation_rate: float = _INFLATION_RATE_DEFAULT
) -> float:
    """
    현재가치를 미래가치로 환산 (물가상승률 반영)
    
    Args:
        current_value: 현재가치 (원)
        years: 년수
        inflation_rate: 연 물가상승률 (기본 2.5%)
    
    Returns:
        미래가치 (원)
    """
    return current_value * ((1 + inflation_rate) ** years)


def calculate_pension_gap(
    current_age: int,
    retirement_age: int = _RETIREMENT_AGE_DEFAULT,
    life_expectancy: int = _LIFE_EXPECTANCY_DEFAULT,
    monthly_expense_now: float = 3_000_000,
    current_pension_monthly: float = 0,
    inflation_rate: float = _INFLATION_RATE_DEFAULT
) -> Dict:
    """
    연금 Gap 분석 (30년 후 물가 반영)
    
    Args:
        current_age: 현재 나이
        retirement_age: 은퇴 예정 나이
        life_expectancy: 기대수명
        monthly_expense_now: 현재 월 생활비 (원)
        current_pension_monthly: 현재 가입 연금 월 수령액 (원)
        inflation_rate: 연 물가상승률
    
    Returns:
        {
            "years_to_retirement": 은퇴까지 남은 년수,
            "retirement_years": 은퇴 후 생존 년수,
            "future_monthly_expense": 30년 후 월 생활비,
            "future_pension_monthly": 30년 후 연금 월 수령액,
            "monthly_gap": 월 부족액,
            "total_gap": 총 부족액,
            "status": "부족" | "충족"
        }
    """
    _years_to_retirement = max(0, retirement_age - current_age)
    _retirement_years = max(0, life_expectancy - retirement_age)
    
    # 30년 후 물가 반영
    _future_monthly_expense = calculate_future_value(
        monthly_expense_now,
        _years_to_retirement,
        inflation_rate
    )
    
    _future_pension_monthly = calculate_future_value(
        current_pension_monthly,
        _years_to_retirement,
        inflation_rate
    )
    
    _monthly_gap = _future_monthly_expense - _future_pension_monthly
    _total_gap = _monthly_gap * _retirement_years * 12
    
    _status = "충족" if _monthly_gap <= 0 else "부족"
    
    return {
        "years_to_retirement": _years_to_retirement,
        "retirement_years": _retirement_years,
        "future_monthly_expense": _future_monthly_expense,
        "future_pension_monthly": _future_pension_monthly,
        "monthly_gap": _monthly_gap,
        "total_gap": _total_gap,
        "status": _status
    }


def calculate_monthly_savings_needed(
    total_gap: float,
    years_to_retirement: int,
    compound_rate: float = _COMPOUND_RATE_DEFAULT
) -> float:
    """
    목표 달성을 위한 월 적립액 계산 (복리 반영)
    
    Args:
        total_gap: 총 부족액 (원)
        years_to_retirement: 은퇴까지 남은 년수
        compound_rate: 연 복리 수익률 (기본 3%)
    
    Returns:
        월 적립액 (원)
    """
    if years_to_retirement <= 0 or total_gap <= 0:
        return 0
    
    _months = years_to_retirement * 12
    _monthly_rate = compound_rate / 12
    
    # 연금 현가계수 (복리 반영)
    if _monthly_rate > 0:
        _annuity_factor = ((1 + _monthly_rate) ** _months - 1) / _monthly_rate
        _monthly_savings = total_gap / _annuity_factor
    else:
        _monthly_savings = total_gap / _months
    
    return _monthly_savings


# ══════════════════════════════════════════════════════════════════════════════
# § 3. UI 렌더링 (연분홍/연하늘 테마)
# ══════════════════════════════════════════════════════════════════════════════

def inject_pension_engine_styles():
    """
    연금 엔진 전용 스타일 주입 (연분홍/연하늘 배경)
    """
    st.markdown("""
    <style>
    /* ══════════════════════════════════════════════════════════════════════════════
       [연금 엔진] 전용 스타일
    ══════════════════════════════════════════════════════════════════════════════ */
    
    .gp-pension-box-pink {
        background: linear-gradient(135deg, #FFF0F5 0%, #FFE4E1 100%);
        border: 2px dashed #FF69B4;
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        box-shadow: 0 4px 12px rgba(255, 105, 180, 0.15);
    }
    
    .gp-pension-box-blue {
        background: linear-gradient(135deg, #F0F8FF 0%, #E6F3FF 100%);
        border: 2px dashed #4682B4;
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        box-shadow: 0 4px 12px rgba(70, 130, 180, 0.15);
    }
    
    .gp-pension-title {
        font-size: clamp(1.2rem, 3vw, 1.5rem);
        font-weight: 900;
        color: #2C3E50;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .gp-pension-value {
        font-size: clamp(1.8rem, 4vw, 2.5rem);
        font-weight: 900;
        margin: 12px 0;
    }
    
    .gp-pension-value-red {
        color: #E74C3C;
    }
    
    .gp-pension-value-green {
        color: #27AE60;
    }
    
    .gp-pension-label {
        font-size: clamp(0.9rem, 2vw, 1rem);
        color: #7F8C8D;
        font-weight: 600;
        margin-bottom: 8px;
    }
    
    .gp-pension-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 16px;
    }
    
    .gp-pension-table th {
        background: rgba(52, 152, 219, 0.1);
        color: #2C3E50;
        font-size: clamp(0.85rem, 2vw, 0.95rem);
        font-weight: 700;
        padding: 12px;
        text-align: left;
        border-bottom: 2px solid #3498DB;
    }
    
    .gp-pension-table td {
        color: #34495E;
        font-size: clamp(0.9rem, 2vw, 1rem);
        padding: 12px;
        border-bottom: 1px solid #ECF0F1;
    }
    
    .gp-pension-table tr:hover {
        background: rgba(52, 152, 219, 0.05);
    }
    
    .gp-pension-highlight {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        color: #1A1A1A;
        font-weight: 900;
        padding: 4px 8px;
        border-radius: 6px;
        display: inline-block;
    }
    
    </style>
    """, unsafe_allow_html=True)


def render_pension_gap_analysis(
    current_age: int,
    monthly_expense_now: float = 3_000_000,
    current_pension_monthly: float = 0,
    retirement_age: int = _RETIREMENT_AGE_DEFAULT,
    life_expectancy: int = _LIFE_EXPECTANCY_DEFAULT
) -> None:
    """
    연금 Gap 분석 UI 렌더링 (5:5 레이아웃)
    
    Args:
        current_age: 현재 나이
        monthly_expense_now: 현재 월 생활비
        current_pension_monthly: 현재 가입 연금 월 수령액
        retirement_age: 은퇴 예정 나이
        life_expectancy: 기대수명
    """
    # 스타일 주입
    inject_pension_engine_styles()
    
    # Gap 계산
    _gap_result = calculate_pension_gap(
        current_age=current_age,
        retirement_age=retirement_age,
        life_expectancy=life_expectancy,
        monthly_expense_now=monthly_expense_now,
        current_pension_monthly=current_pension_monthly
    )
    
    # 월 적립액 계산
    _monthly_savings = 0
    if _gap_result["total_gap"] > 0:
        _monthly_savings = calculate_monthly_savings_needed(
            total_gap=_gap_result["total_gap"],
            years_to_retirement=_gap_result["years_to_retirement"]
        )
    
    # 5:5 레이아웃
    _col_left, _col_right = st.columns([1, 1], gap="large")
    
    # ══════════════════════════════════════════════════════════════════════════════
    # 좌측: 현재 상태 (연분홍 박스)
    # ══════════════════════════════════════════════════════════════════════════════
    with _col_left:
        st.markdown(f"""
        <div class="gp-pension-box-pink">
            <div class="gp-pension-title">
                <span>📊</span>
                <span>현재 상태 분석</span>
            </div>
            
            <div class="gp-pension-label">현재 월 생활비</div>
            <div class="gp-pension-value gp-pension-value-green">
                {monthly_expense_now:,.0f}원
            </div>
            
            <div class="gp-pension-label">현재 가입 연금 (월 수령액)</div>
            <div class="gp-pension-value gp-pension-value-green">
                {current_pension_monthly:,.0f}원
            </div>
            
            <div class="gp-pension-label">은퇴까지 남은 기간</div>
            <div class="gp-pension-value gp-pension-value-green">
                {_gap_result["years_to_retirement"]}년
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # ══════════════════════════════════════════════════════════════════════════════
    # 우측: 30년 후 현실 (연하늘 박스)
    # ══════════════════════════════════════════════════════════════════════════════
    with _col_right:
        _gap_color = "gp-pension-value-red" if _gap_result["status"] == "부족" else "gp-pension-value-green"
        _gap_icon = "🚨" if _gap_result["status"] == "부족" else "✅"
        
        st.markdown(f"""
        <div class="gp-pension-box-blue">
            <div class="gp-pension-title">
                <span>{_gap_icon}</span>
                <span>30년 후 현실 (물가 반영)</span>
            </div>
            
            <div class="gp-pension-label">30년 후 월 생활비 (물가 2.5% 반영)</div>
            <div class="gp-pension-value {_gap_color}">
                {_gap_result["future_monthly_expense"]:,.0f}원
            </div>
            
            <div class="gp-pension-label">30년 후 연금 월 수령액</div>
            <div class="gp-pension-value {_gap_color}">
                {_gap_result["future_pension_monthly"]:,.0f}원
            </div>
            
            <div class="gp-pension-label">월 부족액 (Gap)</div>
            <div class="gp-pension-value {_gap_color}">
                {_gap_result["monthly_gap"]:,.0f}원
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # ══════════════════════════════════════════════════════════════════════════════
    # 하단: 솔루션 제안 (전체 폭)
    # ══════════════════════════════════════════════════════════════════════════════
    if _gap_result["status"] == "부족":
        st.markdown(f"""
        <div class="gp-pension-box-pink">
            <div class="gp-pension-title">
                <span>💡</span>
                <span>솔루션 제안 (The Reality Check)</span>
            </div>
            
            <table class="gp-pension-table">
                <thead>
                    <tr>
                        <th>항목</th>
                        <th>값</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>총 부족액 (은퇴 후 {_gap_result["retirement_years"]}년)</strong></td>
                        <td><span class="gp-pension-highlight">{_gap_result["total_gap"]:,.0f}원</span></td>
                    </tr>
                    <tr>
                        <td><strong>필요 월 적립액 (복리 3% 가정)</strong></td>
                        <td><span class="gp-pension-highlight">{_monthly_savings:,.0f}원</span></td>
                    </tr>
                    <tr>
                        <td>적립 기간</td>
                        <td>{_gap_result["years_to_retirement"]}년 ({_gap_result["years_to_retirement"] * 12}개월)</td>
                    </tr>
                </tbody>
            </table>
            
            <p style="margin-top: 20px; font-size: 0.95rem; color: #E74C3C; font-weight: 600;">
                ⚠️ <strong>현실 타격:</strong> 지금 당장 월 <span class="gp-pension-highlight">{_monthly_savings:,.0f}원</span>씩 
                {_gap_result["years_to_retirement"]}년간 적립하지 않으면, 은퇴 후 매월 <span class="gp-pension-highlight">{_gap_result["monthly_gap"]:,.0f}원</span>이 부족합니다.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.success(f"✅ 축하합니다! 현재 가입 연금으로 30년 후에도 월 {abs(_gap_result['monthly_gap']):,.0f}원의 여유가 있습니다.")


def render_pension_engine_demo():
    """
    연금 엔진 데모 UI (독립 실행 가능)
    """
    st.title("💰 현실 타격형 연금 엔진 (The Reality Check)")
    
    st.markdown("""
    ### 30년 후 물가를 반영한 연금 Gap 분석
    
    **핵심 질문:**
    - 지금 월 300만원으로 생활한다면, 30년 후에는 얼마가 필요할까?
    - 현재 가입한 연금으로 충분할까?
    - 부족하다면 지금 당장 얼마씩 적립해야 할까?
    """)
    
    st.markdown("---")
    
    # 입력 폼
    _col1, _col2, _col3 = st.columns(3)
    
    with _col1:
        _current_age = st.number_input(
            "현재 나이",
            min_value=20,
            max_value=70,
            value=35,
            step=1
        )
    
    with _col2:
        _retirement_age = st.number_input(
            "은퇴 예정 나이",
            min_value=50,
            max_value=80,
            value=65,
            step=1
        )
    
    with _col3:
        _life_expectancy = st.number_input(
            "기대수명",
            min_value=70,
            max_value=100,
            value=90,
            step=1
        )
    
    _col4, _col5 = st.columns(2)
    
    with _col4:
        _monthly_expense = st.number_input(
            "현재 월 생활비 (원)",
            min_value=1_000_000,
            max_value=10_000_000,
            value=3_000_000,
            step=100_000,
            format="%d"
        )
    
    with _col5:
        _current_pension = st.number_input(
            "현재 가입 연금 월 수령액 (원)",
            min_value=0,
            max_value=5_000_000,
            value=500_000,
            step=100_000,
            format="%d"
        )
    
    st.markdown("---")
    
    # 분석 실행
    if st.button("🚀 연금 Gap 분석 시작", type="primary", use_container_width=True):
        render_pension_gap_analysis(
            current_age=_current_age,
            monthly_expense_now=_monthly_expense,
            current_pension_monthly=_current_pension,
            retirement_age=_retirement_age,
            life_expectancy=_life_expectancy
        )


# ══════════════════════════════════════════════════════════════════════════════
# § 4. 메인 실행 (독립 테스트용)
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    render_pension_engine_demo()
