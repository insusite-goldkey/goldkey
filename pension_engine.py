# =============================================================================
# [GP-PENSION] 현실 타격형 연금 지능 엔진
# 금융공학 기반 복리 산식 + 2024~2025 실전 타겟 데이터
# =============================================================================
#
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  💰 PENSION INTELLIGENCE ENGINE                                           ║
# ╠═══════════════════════════════════════════════════════════════════════════╣
# ║  Purpose: 현실 직시형 연금 분석 (희망 고문 금지)                          ║
# ║  Date:    2026-03-31                                                      ║
# ║  Author:  Goldkey AI Masters 2026                                         ║
# ║                                                                           ║
# ║  Features:                                                                ║
# ║  - 월 복리 기반 적립기 계산 (FV)                                          ║
# ║  - 미상환 잔액 복리 방식 수령기 계산 (Annuity)                            ║
# ║  - 트리니티 4% 안전 인출률 시나리오                                        ║
# ║  - 2024~2025 지역별 생활비 DB                                             ║
# ║  - 4층 보장 소득대체율 분석                                               ║
# ║  - 물가상승률 5% 반영 공포 수치 계산                                      ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


# ══════════════════════════════════════════════════════════════════════════════
# [DATA] 2024~2025 실전 타겟 데이터
# ══════════════════════════════════════════════════════════════════════════════

# 지역별 월평균 생활비 (2024년 기준, 단위: 만원)
REGIONAL_LIVING_COST = {
    "광역_단독": 180,
    "광역_부부": 310,
    "중소_단독": 150,
    "중소_부부": 260,
    "농어촌_단독": 120,
    "농어촌_부부": 210,
}

# 4층 보장 소득대체율 (2025년 기준, %)
FOUR_TIER_REPLACEMENT_RATE = {
    "국민연금": 43.0,      # 국민연금공단 2025년 기준
    "퇴직연금_최소": 12.0, # DC형 최소 기여도
    "퇴직연금_최대": 20.0, # DB형 최대 기여도
    "주택연금": 13.5,      # 한국주택금융공사 평균
    "개인연금": 0.0,       # Gap을 채워야 할 영역
}

# 생명보험 연금보험 유지율 통계 (2024년 금감원 공시)
PERSISTENCE_RATE = {
    "1년": 85.0,
    "2년": 70.0,
    "5년": 50.0,
    "10년": 35.0,
}

# 물가상승률 시나리오 (%)
INFLATION_SCENARIOS = {
    "보수적": 3.0,
    "중립": 4.0,
    "공격적": 5.0,
}

# 연금저축 세액공제율 (2026년 기준)
TAX_DEDUCTION_RATE = {
    "저소득_기준": 5500,  # 만원 (총급여 5,500만원 이하)
    "저소득_공제율": 16.5,  # %
    "고소득_공제율": 13.2,  # %
    "연금저축_한도": 600,   # 만원/년
    "IRP_추가한도": 300,    # 만원/년
    "합산_최대한도": 900,   # 만원/년
}


# ══════════════════════════════════════════════════════════════════════════════
# [DATACLASS] 연금 분석 결과 구조체
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class PensionAnalysisResult:
    """연금 분석 결과"""
    # 적립기 결과
    accumulated_amount: float          # 적립 총액 (원)
    monthly_contribution: float        # 월 납입액 (원)
    contribution_years: int            # 납입 기간 (년)
    annual_return_rate: float          # 연 수익률 (%)
    
    # 수령기 결과
    monthly_pension_standard: float    # 월 수령액 - 표준 방식 (원)
    monthly_pension_trinity: float     # 월 수령액 - 트리니티 4% (원)
    pension_duration_years: int        # 수령 기간 (년)
    
    # 생활비 분석
    regional_living_cost: float        # 지역별 최소 생활비 (원)
    inflation_adjusted_cost: float     # 물가 반영 미래 생활비 (원)
    gap_amount: float                  # 부족 금액 (원)
    gap_percentage: float              # 부족 비율 (%)
    
    # 4층 보장 분석
    national_pension: float            # 국민연금 예상액 (원)
    retirement_pension: float          # 퇴직연금 예상액 (원)
    housing_pension: float             # 주택연금 예상액 (원)
    personal_pension: float            # 개인연금 예상액 (원)
    total_replacement_rate: float      # 총 소득대체율 (%)
    
    # 세제 혜택
    annual_tax_benefit: float          # 연간 세액공제액 (원)
    total_tax_benefit: float           # 총 세액공제액 (원)
    
    # 경고 지표
    persistence_risk: str              # 유지율 경고 메시지
    tax_risk: str                      # 세제 리스크 경고
    inflation_warning: str             # 물가 경고 메시지


# ══════════════════════════════════════════════════════════════════════════════
# [ENGINE] 금융공학 기반 복리 산식
# ══════════════════════════════════════════════════════════════════════════════

def calculate_future_value(
    pv: float,           # 현재가치 (원)
    pmt: float,          # 월 납입액 (원)
    annual_rate: float,  # 연 수익률 (%)
    years: int,          # 납입 기간 (년)
) -> float:
    """
    적립기 미래가치 계산 (월 복리 기준)
    
    FV = PV(1 + r)^n + PMT × [(1 + r)^n - 1] / r
    
    Args:
        pv: 현재가치 (초기 투자금)
        pmt: 월 납입액
        annual_rate: 연 수익률 (%)
        years: 납입 기간 (년)
    
    Returns:
        미래가치 (원)
    """
    r = annual_rate / 100 / 12  # 월 수익률
    n = years * 12              # 총 납입 개월수
    
    if r == 0:
        return pv + pmt * n
    
    # FV = PV(1 + r)^n + PMT × [(1 + r)^n - 1] / r
    fv_pv = pv * math.pow(1 + r, n)
    fv_pmt = pmt * (math.pow(1 + r, n) - 1) / r
    
    return fv_pv + fv_pmt


def calculate_annuity_payment(
    fv: float,           # 적립 총액 (원)
    annual_rate: float,  # 연 수익률 (%)
    years: int,          # 수령 기간 (년)
    mode: str = "standard",  # "standard" or "trinity"
) -> float:
    """
    수령기 월 연금액 계산 (미상환 잔액 복리 방식)
    
    Standard Mode: 자산 고갈 방식
    PMT = FV × r / [1 - (1 + r)^(-n)]
    
    Trinity 4% Mode: 원금 보존 방식
    PMT = FV × 0.04 / 12
    
    Args:
        fv: 적립 총액
        annual_rate: 연 수익률 (%)
        years: 수령 기간 (년)
        mode: "standard" (자산 고갈) or "trinity" (원금 보존)
    
    Returns:
        월 수령액 (원)
    """
    if mode == "trinity":
        # 트리니티 4% 룰: 연 4%만 인출 (원금 보존)
        return fv * 0.04 / 12
    
    # Standard Mode: 미상환 잔액 복리 방식
    r = annual_rate / 100 / 12  # 월 수익률
    n = years * 12              # 총 수령 개월수
    
    if r == 0:
        return fv / n
    
    # PMT = FV × r / [1 - (1 + r)^(-n)]
    pmt = fv * r / (1 - math.pow(1 + r, -n))
    
    return pmt


def calculate_inflation_adjusted_cost(
    current_cost: float,      # 현재 생활비 (원)
    inflation_rate: float,    # 물가상승률 (%)
    years: int,               # 기간 (년)
) -> float:
    """
    물가상승률 반영 미래 생활비 계산
    
    Future Cost = Current Cost × (1 + inflation_rate)^years
    
    Args:
        current_cost: 현재 생활비
        inflation_rate: 물가상승률 (%)
        years: 기간 (년)
    
    Returns:
        미래 생활비 (원)
    """
    return current_cost * math.pow(1 + inflation_rate / 100, years)


# ══════════════════════════════════════════════════════════════════════════════
# [ANALYSIS] 통합 연금 분석 엔진
# ══════════════════════════════════════════════════════════════════════════════

def run_pension_analysis(
    # 고객 기본 정보
    age: int,                          # 현재 나이
    retirement_age: int,               # 은퇴 나이
    life_expectancy: int,              # 기대 수명
    region_type: str,                  # 지역 구분 ("광역", "중소", "농어촌")
    household_type: str,               # 가구 구분 ("단독", "부부")
    
    # 연금 납입 정보
    monthly_contribution: float,       # 월 납입액 (원)
    initial_amount: float = 0,         # 초기 투자금 (원)
    annual_return_rate: float = 4.5,   # 연 수익률 (%)
    
    # 4층 보장 정보
    monthly_salary: float = 0,         # 월 급여 (원) - 소득대체율 계산용
    national_pension_amt: float = 0,   # 국민연금 예상액 (원/월)
    retirement_pension_amt: float = 0, # 퇴직연금 예상액 (원/월)
    housing_pension_amt: float = 0,    # 주택연금 예상액 (원/월)
    
    # 옵션
    inflation_scenario: str = "공격적",  # "보수적", "중립", "공격적"
    use_trinity_mode: bool = False,     # 트리니티 4% 모드 사용 여부
    annual_income: float = 0,           # 연 총급여 (만원) - 세액공제율 계산용
) -> PensionAnalysisResult:
    """
    통합 연금 분석 실행
    
    Args:
        age: 현재 나이
        retirement_age: 은퇴 나이
        life_expectancy: 기대 수명
        region_type: 지역 구분
        household_type: 가구 구분
        monthly_contribution: 월 납입액
        initial_amount: 초기 투자금
        annual_return_rate: 연 수익률
        monthly_salary: 월 급여
        national_pension_amt: 국민연금 예상액
        retirement_pension_amt: 퇴직연금 예상액
        housing_pension_amt: 주택연금 예상액
        inflation_scenario: 물가상승률 시나리오
        use_trinity_mode: 트리니티 모드 사용 여부
        annual_income: 연 총급여 (세액공제율 계산용)
    
    Returns:
        PensionAnalysisResult
    """
    # 1. 적립기 계산
    contribution_years = retirement_age - age
    accumulated_amount = calculate_future_value(
        pv=initial_amount,
        pmt=monthly_contribution,
        annual_rate=annual_return_rate,
        years=contribution_years,
    )
    
    # 2. 수령기 계산
    pension_duration_years = life_expectancy - retirement_age
    monthly_pension_standard = calculate_annuity_payment(
        fv=accumulated_amount,
        annual_rate=annual_return_rate,
        years=pension_duration_years,
        mode="standard",
    )
    monthly_pension_trinity = calculate_annuity_payment(
        fv=accumulated_amount,
        annual_rate=annual_return_rate,
        years=pension_duration_years,
        mode="trinity",
    )
    
    # 3. 지역별 생활비 분석
    region_key = f"{region_type}_{household_type}"
    regional_living_cost = REGIONAL_LIVING_COST.get(region_key, 310) * 10000  # 만원 → 원
    
    inflation_rate = INFLATION_SCENARIOS.get(inflation_scenario, 5.0)
    inflation_adjusted_cost = calculate_inflation_adjusted_cost(
        current_cost=regional_living_cost,
        inflation_rate=inflation_rate,
        years=contribution_years,
    )
    
    # 4. Gap 분석
    monthly_pension = monthly_pension_trinity if use_trinity_mode else monthly_pension_standard
    total_monthly_pension = (
        national_pension_amt +
        retirement_pension_amt +
        housing_pension_amt +
        monthly_pension
    )
    
    gap_amount = max(0, inflation_adjusted_cost - total_monthly_pension)
    gap_percentage = (gap_amount / inflation_adjusted_cost * 100) if inflation_adjusted_cost > 0 else 0
    
    # 5. 4층 보장 소득대체율 계산
    if monthly_salary > 0:
        national_pension_rate = (national_pension_amt / monthly_salary * 100) if national_pension_amt > 0 else FOUR_TIER_REPLACEMENT_RATE["국민연금"]
        retirement_pension_rate = (retirement_pension_amt / monthly_salary * 100) if retirement_pension_amt > 0 else FOUR_TIER_REPLACEMENT_RATE["퇴직연금_최소"]
        housing_pension_rate = (housing_pension_amt / monthly_salary * 100) if housing_pension_amt > 0 else FOUR_TIER_REPLACEMENT_RATE["주택연금"]
        personal_pension_rate = (monthly_pension / monthly_salary * 100) if monthly_pension > 0 else 0
        total_replacement_rate = national_pension_rate + retirement_pension_rate + housing_pension_rate + personal_pension_rate
    else:
        total_replacement_rate = 0
    
    # 6. 세제 혜택 계산
    annual_contribution = monthly_contribution * 12
    annual_contribution_10k = annual_contribution / 10000  # 원 → 만원
    
    # 세액공제 한도 적용
    deductible_amount = min(annual_contribution_10k, TAX_DEDUCTION_RATE["합산_최대한도"])
    
    # 세액공제율 결정
    if annual_income > 0 and annual_income <= TAX_DEDUCTION_RATE["저소득_기준"]:
        tax_rate = TAX_DEDUCTION_RATE["저소득_공제율"]
    else:
        tax_rate = TAX_DEDUCTION_RATE["고소득_공제율"]
    
    annual_tax_benefit = deductible_amount * tax_rate / 100 * 10000  # 만원 → 원
    total_tax_benefit = annual_tax_benefit * contribution_years
    
    # 7. 경고 메시지 생성
    persistence_risk = f"⚠️ 5년 유지율 {PERSISTENCE_RATE['5년']}% - 중도 해지 시 세제 혜택 반환 및 원금 손실 위험"
    
    tax_risk = "⚠️ 연금저축(세제적격) 중도 해지 시 세액공제 받은 금액 전액 반환 + 기타소득세 16.5% 추가 부과"
    
    if gap_percentage > 50:
        inflation_warning = f"🔴 심각: 물가상승률 {inflation_rate}% 반영 시 노후 생활비 {gap_percentage:.1f}% 부족 (월 {gap_amount/10000:.0f}만원)"
    elif gap_percentage > 30:
        inflation_warning = f"🟡 경고: 물가상승률 {inflation_rate}% 반영 시 노후 생활비 {gap_percentage:.1f}% 부족 (월 {gap_amount/10000:.0f}만원)"
    elif gap_percentage > 0:
        inflation_warning = f"🟢 주의: 물가상승률 {inflation_rate}% 반영 시 노후 생활비 {gap_percentage:.1f}% 부족 (월 {gap_amount/10000:.0f}만원)"
    else:
        inflation_warning = f"✅ 양호: 물가상승률 {inflation_rate}% 반영 시에도 노후 생활비 충분"
    
    # 8. 결과 반환
    return PensionAnalysisResult(
        accumulated_amount=accumulated_amount,
        monthly_contribution=monthly_contribution,
        contribution_years=contribution_years,
        annual_return_rate=annual_return_rate,
        monthly_pension_standard=monthly_pension_standard,
        monthly_pension_trinity=monthly_pension_trinity,
        pension_duration_years=pension_duration_years,
        regional_living_cost=regional_living_cost,
        inflation_adjusted_cost=inflation_adjusted_cost,
        gap_amount=gap_amount,
        gap_percentage=gap_percentage,
        national_pension=national_pension_amt,
        retirement_pension=retirement_pension_amt,
        housing_pension=housing_pension_amt,
        personal_pension=monthly_pension,
        total_replacement_rate=total_replacement_rate,
        annual_tax_benefit=annual_tax_benefit,
        total_tax_benefit=total_tax_benefit,
        persistence_risk=persistence_risk,
        tax_risk=tax_risk,
        inflation_warning=inflation_warning,
    )


# ══════════════════════════════════════════════════════════════════════════════
# [UTILITY] 보고서 생성 헬퍼 함수
# ══════════════════════════════════════════════════════════════════════════════

def format_pension_report(result: PensionAnalysisResult) -> Dict[str, any]:
    """
    연금 분석 결과를 UI 렌더링용 딕셔너리로 변환
    
    Args:
        result: PensionAnalysisResult
    
    Returns:
        UI 렌더링용 딕셔너리
    """
    return {
        "적립기": {
            "적립_총액": f"{result.accumulated_amount/100000000:.2f}억원",
            "월_납입액": f"{result.monthly_contribution/10000:.1f}만원",
            "납입_기간": f"{result.contribution_years}년",
            "연_수익률": f"{result.annual_return_rate}%",
        },
        "수령기": {
            "월_수령액_표준": f"{result.monthly_pension_standard/10000:.1f}만원",
            "월_수령액_트리니티": f"{result.monthly_pension_trinity/10000:.1f}만원",
            "수령_기간": f"{result.pension_duration_years}년",
        },
        "생활비_분석": {
            "현재_최소생활비": f"{result.regional_living_cost/10000:.0f}만원/월",
            "미래_필요생활비": f"{result.inflation_adjusted_cost/10000:.0f}만원/월",
            "부족_금액": f"{result.gap_amount/10000:.0f}만원/월",
            "부족_비율": f"{result.gap_percentage:.1f}%",
        },
        "4층_보장": {
            "국민연금": f"{result.national_pension/10000:.0f}만원/월",
            "퇴직연금": f"{result.retirement_pension/10000:.0f}만원/월",
            "주택연금": f"{result.housing_pension/10000:.0f}만원/월",
            "개인연금": f"{result.personal_pension/10000:.0f}만원/월",
            "총_소득대체율": f"{result.total_replacement_rate:.1f}%",
        },
        "세제_혜택": {
            "연간_세액공제": f"{result.annual_tax_benefit/10000:.0f}만원",
            "총_세액공제": f"{result.total_tax_benefit/10000:.0f}만원",
        },
        "경고": {
            "유지율_리스크": result.persistence_risk,
            "세제_리스크": result.tax_risk,
            "물가_경고": result.inflation_warning,
        },
    }


# ══════════════════════════════════════════════════════════════════════════════
# [TEST] 테스트 시나리오
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # 테스트 시나리오: 40대 외벌이 가장, 광역도시 거주, 월 30만원 연금 가입
    result = run_pension_analysis(
        age=40,
        retirement_age=65,
        life_expectancy=85,
        region_type="광역",
        household_type="부부",
        monthly_contribution=300000,  # 월 30만원
        initial_amount=0,
        annual_return_rate=4.5,
        monthly_salary=4000000,  # 월 400만원
        national_pension_amt=1720000,  # 국민연금 172만원 (43%)
        retirement_pension_amt=640000,  # 퇴직연금 64만원 (16%)
        housing_pension_amt=540000,     # 주택연금 54만원 (13.5%)
        inflation_scenario="공격적",
        use_trinity_mode=False,
        annual_income=5000,  # 연 5,000만원 (세액공제 13.2%)
    )
    
    report = format_pension_report(result)
    
    print("=" * 80)
    print("[현실 타격형 연금 분석 보고서]")
    print("=" * 80)
    print(f"\n[적립기]")
    for k, v in report["적립기"].items():
        print(f"  {k}: {v}")
    
    print(f"\n[수령기]")
    for k, v in report["수령기"].items():
        print(f"  {k}: {v}")
    
    print(f"\n[생활비 분석]")
    for k, v in report["생활비_분석"].items():
        print(f"  {k}: {v}")
    
    print(f"\n[4층 보장]")
    for k, v in report["4층_보장"].items():
        print(f"  {k}: {v}")
    
    print(f"\n[세제 혜택]")
    for k, v in report["세제_혜택"].items():
        print(f"  {k}: {v}")
    
    print(f"\n[경고]")
    for k, v in report["경고"].items():
        print(f"  {k}")
        print(f"    {v}")
    
    print("\n" + "=" * 80)
