# -*- coding: utf-8 -*-
"""
CEO 상속세 시뮬레이션 엔진
비상장주식 평가 및 유동성 위기 분석

작성일: 2026-03-31
목적: 1원 단위 정밀 상속세 추정 및 현금 부족액 계산
페르소나: 황금 감옥에 갇힌 성주 (5060 CEO)
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class CompanyValuation:
    """법인 가치 평가 결과"""
    profit_value: int  # 순손익가치
    asset_value: int  # 순자산가치
    total_value: int  # 보충적 평가액
    method: str  # 평가 방법


@dataclass
class InheritanceTaxResult:
    """상속세 계산 결과"""
    taxable_amount: int  # 과세표준
    tax_amount: int  # 상속세액
    liquid_assets: int  # 유동자산
    cash_shortage: int  # 현금 부족액
    insurance_needed: int  # 필요 보험금액
    metaphor: str  # 은유적 표현


class CEOSuccessionSimulator:
    """
    CEO 상속세 시뮬레이션 엔진
    
    핵심 기능:
    1. 비상장주식 가치 평가 (순손익가치 60% + 순자산가치 40%)
    2. 상속세 1원 단위 정밀 계산
    3. 현금 부족액 추정
    4. 은유적 후킹 언어 생성
    """
    
    # 상속세 누진세율표
    TAX_BRACKETS = [
        (100000000, 0.10, 0),  # 1억 이하
        (500000000, 0.20, 10000000),  # 5억 이하
        (1000000000, 0.30, 60000000),  # 10억 이하
        (3000000000, 0.40, 160000000),  # 30억 이하
        (float('inf'), 0.50, 460000000)  # 30억 초과
    ]
    
    # 최대주주 할증
    LARGEST_SHAREHOLDER_PREMIUM = 0.20
    
    # 법인세율 (중소기업 기준)
    CORPORATE_TAX_RATE = 0.22
    
    def __init__(self):
        """초기화"""
        pass
    
    def evaluate_unlisted_stock(
        self,
        annual_profit: int,
        net_assets: int,
        discount_rate: float = 0.10
    ) -> CompanyValuation:
        """
        비상장주식 가치 평가
        
        보충적 평가 방식:
        - 순손익가치 60% + 순자산가치 40%
        
        Args:
            annual_profit: 최근 3년 평균 순이익
            net_assets: 순자산 (자산 - 부채)
            discount_rate: 환원율 (기본 10%)
        
        Returns:
            CompanyValuation: 평가 결과
        """
        # 순손익가치 = (평균 순이익 × 3) / 환원율
        profit_value = int((annual_profit * 3) / discount_rate)
        
        # 순자산가치 = 순자산
        asset_value = net_assets
        
        # 보충적 평가 = 순손익가치 × 0.6 + 순자산가치 × 0.4
        total_value = int(profit_value * 0.6 + asset_value * 0.4)
        
        return CompanyValuation(
            profit_value=profit_value,
            asset_value=asset_value,
            total_value=total_value,
            method="보충적 평가 (순손익 60% + 순자산 40%)"
        )
    
    def calculate_inheritance_tax(
        self,
        company_value: int,
        ownership: float,
        is_largest_shareholder: bool = True,
        deduction: int = 200000000  # 기초공제 2억
    ) -> Tuple[int, int]:
        """
        상속세 계산
        
        Args:
            company_value: 법인 가치
            ownership: 지분율 (0.0 ~ 1.0)
            is_largest_shareholder: 최대주주 여부
            deduction: 공제액 (기본 2억)
        
        Returns:
            Tuple[과세표준, 상속세액]
        """
        # 상속 재산 = 법인 가치 × 지분율
        inherited_value = int(company_value * ownership)
        
        # 최대주주 할증 (20%)
        if is_largest_shareholder and ownership >= 0.5:
            inherited_value = int(inherited_value * (1 + self.LARGEST_SHAREHOLDER_PREMIUM))
        
        # 과세표준 = 상속 재산 - 공제액
        taxable_amount = max(0, inherited_value - deduction)
        
        # 누진세율 적용
        tax_amount = 0
        remaining = taxable_amount
        
        for limit, rate, quick_deduction in self.TAX_BRACKETS:
            if remaining <= limit:
                tax_amount = int(remaining * rate - quick_deduction)
                break
        
        return taxable_amount, tax_amount
    
    def simulate_liquidity_crisis(
        self,
        annual_profit: int,
        net_assets: int,
        ownership: float,
        liquid_assets: int,
        is_largest_shareholder: bool = True
    ) -> InheritanceTaxResult:
        """
        유동성 위기 시뮬레이션
        
        Args:
            annual_profit: 최근 3년 평균 순이익
            net_assets: 순자산
            ownership: 지분율
            liquid_assets: 유동자산 (현금 + 예금)
            is_largest_shareholder: 최대주주 여부
        
        Returns:
            InheritanceTaxResult: 시뮬레이션 결과
        """
        # 1. 법인 가치 평가
        valuation = self.evaluate_unlisted_stock(annual_profit, net_assets)
        
        # 2. 상속세 계산
        taxable_amount, tax_amount = self.calculate_inheritance_tax(
            company_value=valuation.total_value,
            ownership=ownership,
            is_largest_shareholder=is_largest_shareholder
        )
        
        # 3. 현금 부족액 계산
        cash_shortage = max(0, tax_amount - liquid_assets)
        
        # 4. 필요 보험금액 (여유 20% 추가)
        insurance_needed = int(cash_shortage * 1.2)
        
        # 5. 은유적 표현 생성
        if cash_shortage > 0:
            metaphor = f"대표님의 성(Castle)은 {valuation.total_value:,}원의 가치를 지니지만, 국세청의 청구서 {tax_amount:,}원을 낼 현금이 {cash_shortage:,}원 부족합니다. 이는 대표님의 평생을 건 마지막 세무조사가 될 것입니다."
        else:
            metaphor = f"대표님의 성(Castle)은 안전합니다. 상속세 {tax_amount:,}원을 충분히 낼 수 있는 현금 {liquid_assets:,}원을 보유하고 계십니다."
        
        return InheritanceTaxResult(
            taxable_amount=taxable_amount,
            tax_amount=tax_amount,
            liquid_assets=liquid_assets,
            cash_shortage=cash_shortage,
            insurance_needed=insurance_needed,
            metaphor=metaphor
        )
    
    def calculate_insurance_roi(
        self,
        annual_premium: int,
        insurance_amount: int,
        years: int = 20
    ) -> Dict[str, int]:
        """
        경영인정기보험 ROI 계산
        
        Args:
            annual_premium: 연 보험료
            insurance_amount: 보험금액
            years: 납입 기간
        
        Returns:
            Dict: ROI 분석 결과
        """
        # 총 납입 보험료
        total_premium = annual_premium * years
        
        # 법인세 절감액 (연 보험료 × 법인세율 × 납입 기간)
        tax_savings = int(annual_premium * self.CORPORATE_TAX_RATE * years)
        
        # 실질 부담액
        net_cost = total_premium - tax_savings
        
        # ROI (보험금 / 실질 부담액)
        roi = (insurance_amount / net_cost) if net_cost > 0 else 0
        
        return {
            "total_premium": total_premium,
            "tax_savings": tax_savings,
            "net_cost": net_cost,
            "insurance_amount": insurance_amount,
            "roi": round(roi, 2),
            "roi_percentage": round((roi - 1) * 100, 2)
        }
    
    def generate_strategic_report(
        self,
        annual_profit: int,
        net_assets: int,
        ownership: float,
        liquid_assets: int,
        annual_premium: int
    ) -> str:
        """
        전략적 보고서 생성
        
        Args:
            annual_profit: 최근 3년 평균 순이익
            net_assets: 순자산
            ownership: 지분율
            liquid_assets: 유동자산
            annual_premium: 연 보험료
        
        Returns:
            str: 전략적 보고서 (Markdown)
        """
        # 시뮬레이션 실행
        result = self.simulate_liquidity_crisis(
            annual_profit=annual_profit,
            net_assets=net_assets,
            ownership=ownership,
            liquid_assets=liquid_assets
        )
        
        # ROI 계산
        roi = self.calculate_insurance_roi(
            annual_premium=annual_premium,
            insurance_amount=result.insurance_needed
        )
        
        report = f"""
# 🏰 CEO 상속세 유동성 위기 분석 보고서

## 📊 현황 진단

### 법인 가치 평가
- **평가 방법**: 보충적 평가 (순손익 60% + 순자산 40%)
- **최근 3년 평균 순이익**: {annual_profit:,}원
- **순자산**: {net_assets:,}원
- **평가액**: {result.taxable_amount + 200000000:,}원

### 상속세 추정
- **지분율**: {ownership * 100:.1f}%
- **최대주주 할증**: 20% 적용
- **과세표준**: {result.taxable_amount:,}원
- **상속세액**: **{result.tax_amount:,}원**

### 유동성 분석
- **보유 현금**: {liquid_assets:,}원
- **현금 부족액**: **{result.cash_shortage:,}원**
- **필요 보험금액**: {result.insurance_needed:,}원 (여유 20% 포함)

---

## 🔥 은유적 진단

{result.metaphor}

---

## 💡 경영인정기보험 전략

### 보험 설계
- **연 보험료**: {annual_premium:,}원
- **보험금액**: {result.insurance_needed:,}원
- **납입 기간**: 20년

### 법인세 절감 효과
- **총 납입 보험료**: {roi['total_premium']:,}원
- **법인세 절감액**: {roi['tax_savings']:,}원 (법인세율 22%)
- **실질 부담액**: {roi['net_cost']:,}원

### ROI 분석
- **투자 수익률**: {roi['roi_percentage']:.2f}%
- **해석**: 실질 부담 {roi['net_cost']:,}원으로 {result.insurance_needed:,}원의 상속 재원 확보

---

## 🛡️ 전략적 실행 계획

### STEP 1: 정관 변경 (퇴직금 지급 규정)
**목적**: 보험금을 법인이 수령 → 임원 퇴직금으로 지급 → 유가족에게 전달

**법적 근거**: 상법 제388조, 근로기준법 제34조

**핵심 문구**:
> "준비되지 않은 퇴직금 규정은 독이 됩니다. 이 플랜은 보험 가입이 아니라, **법인 정관이라는 방패**를 수선하는 작업입니다."

### STEP 2: 자기주식 취득 전략
**목적**: 보험금으로 자기주식 취득 → 유가족 지분율 유지 → 경영권 방어

**법적 근거**: 상법 제341조

**핵심 문구**:
> "보험금은 상속세 전용 비상금이자, 유가족이 경영권을 방어할 수 있는 **최후의 보루**입니다."

### STEP 3: 세금 세탁 (합법적 절세)
**목적**: 국가에 낼 세금을 깎아서 대표님 가족의 상속 재원으로 치환

**핵심 문구**:
> "이 보험료는 비용입니다. 국가에 낼 세금을 깎아서 대표님 가족의 **상속 재원**으로 치환하는 **세금 세탁(합법적 절세)**의 과정입니다."

---

## 🎯 최종 메시지

**국세청에 회사를 뺏기지 않을 '현금 성벽'을 쌓으십시오.**

대표님의 성(Castle)에 현금이라는 다리를 놓아, 유가족이 경영권을 지킬 수 있게 하겠습니다.

---

**작성일**: 2026-03-31  
**작성자**: goldkey_Ai_masters2026 CEO 상속세 시뮬레이션 엔진
"""
        
        return report


def main():
    """테스트 실행"""
    print("=" * 70)
    print("🏰 CEO 상속세 시뮬레이션 엔진")
    print("=" * 70)
    
    simulator = CEOSuccessionSimulator()
    
    # 시나리오: 중소기업 CEO
    print("\n📊 시나리오: 중소기업 CEO (58세)")
    print("-" * 70)
    
    result = simulator.simulate_liquidity_crisis(
        annual_profit=5_000_000_000,  # 연 순이익 50억
        net_assets=20_000_000_000,  # 순자산 200억
        ownership=0.80,  # 지분 80%
        liquid_assets=2_000_000_000  # 유동자산 20억
    )
    
    print(f"\n법인 가치: {result.taxable_amount + 200_000_000:,}원")
    print(f"상속세액: {result.tax_amount:,}원")
    print(f"보유 현금: {result.liquid_assets:,}원")
    print(f"현금 부족액: {result.cash_shortage:,}원")
    print(f"필요 보험금액: {result.insurance_needed:,}원")
    
    print(f"\n🔥 {result.metaphor}")
    
    # 전략적 보고서 생성
    print("\n" + "=" * 70)
    print("📄 전략적 보고서 생성")
    print("=" * 70)
    
    report = simulator.generate_strategic_report(
        annual_profit=5_000_000_000,
        net_assets=20_000_000_000,
        ownership=0.80,
        liquid_assets=2_000_000_000,
        annual_premium=500_000_000  # 연 보험료 5억
    )
    
    print(report)


if __name__ == "__main__":
    main()
