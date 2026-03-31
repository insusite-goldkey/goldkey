# -*- coding: utf-8 -*-
"""
업종별 동적 리스크 산출 엔진
제조업/건설업 특화 리스크 계산

작성일: 2026-03-31
목적: 업종별 특화 리스크를 동적으로 계산하여 압박형 브리핑 생성
"""

import json
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass
from engines.ceo_succession_simulator import CEOSuccessionSimulator


@dataclass
class IndustryRiskResult:
    """업종별 리스크 계산 결과"""
    industry: str
    inheritance_tax: int
    additional_risks: Dict[str, int]
    total_risk: int
    briefing: str
    metaphor: str
    pressure_message: str


class IndustryRiskCalculator:
    """
    업종별 동적 리스크 산출 엔진
    
    핵심 기능:
    1. 제조업: 상속세 + 중대재해 합의금 + 설비 경매 손실
    2. 건설업: 상속세 + 면허 유지 자본금 + 연대보증 채무
    3. 압박형 브리핑 자동 생성
    """
    
    def __init__(self):
        """초기화"""
        self.simulator = CEOSuccessionSimulator()
        self.intelligence_data = self._load_intelligence_data()
    
    def _load_intelligence_data(self) -> Dict:
        """업종별 리스크 지능 데이터 로드"""
        json_path = Path(__file__).parent.parent / "hq_backend" / "knowledge_base" / "industry_risk_intelligence.json"
        
        if not json_path.exists():
            raise FileNotFoundError(f"지능 데이터 파일을 찾을 수 없습니다: {json_path}")
        
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def calculate_manufacturing_risk(
        self,
        annual_profit: int,
        net_assets: int,
        ownership: float,
        liquid_assets: int,
        equipment_assets: int,
        expected_accidents: int = 1
    ) -> IndustryRiskResult:
        """
        제조업 리스크 계산
        
        총 리스크 = 상속세 + 중대재해 합의금 + 설비 경매 손실
        
        Args:
            annual_profit: 최근 3년 평균 순이익
            net_assets: 순자산
            ownership: 지분율
            liquid_assets: 유동자산
            equipment_assets: 설비자산 (기계, 토지, 건물)
            expected_accidents: 예상 사고 건수
        
        Returns:
            IndustryRiskResult: 리스크 계산 결과
        """
        # 1. 상속세 계산
        succession_result = self.simulator.simulate_liquidity_crisis(
            annual_profit=annual_profit,
            net_assets=net_assets,
            ownership=ownership,
            liquid_assets=liquid_assets
        )
        
        # 2. 중대재해 합의금
        accident_settlement = 500_000_000 * expected_accidents  # 평균 5억 × 예상 건수
        
        # 3. 설비 경매 손실 (강제 경매 시 30% 손실)
        auction_loss = int(equipment_assets * 0.3)
        
        # 4. 총 리스크
        total_risk = succession_result.tax_amount + accident_settlement + auction_loss
        
        # 5. 설비자산 비중
        equipment_ratio = int((equipment_assets / (net_assets + equipment_assets)) * 100)
        
        # 6. 브리핑 생성
        mfg_data = self.intelligence_data["industries"]["manufacturing"]
        briefing_template = self.intelligence_data["briefing_templates"]["manufacturing"]
        
        briefing_sections = []
        for section in briefing_template["sections"]:
            content = section["content"].format(
                equipment_ratio=equipment_ratio,
                liquid_assets=liquid_assets,
                inheritance_tax=succession_result.tax_amount,
                cash_shortage=succession_result.cash_shortage,
                auction_loss=auction_loss
            )
            briefing_sections.append(f"### {section['section']}\n{content}")
        
        briefing = "\n\n".join(briefing_sections)
        
        # 7. 은유 및 압박 메시지
        metaphor = mfg_data["hooking_phrases"]["opening"]
        pressure = mfg_data["hooking_phrases"]["pressure"]
        
        return IndustryRiskResult(
            industry="제조업",
            inheritance_tax=succession_result.tax_amount,
            additional_risks={
                "중대재해_합의금": accident_settlement,
                "설비_경매_손실": auction_loss
            },
            total_risk=total_risk,
            briefing=briefing,
            metaphor=metaphor,
            pressure_message=pressure
        )
    
    def calculate_construction_risk(
        self,
        annual_profit: int,
        net_assets: int,
        ownership: float,
        liquid_assets: int,
        current_capital: int,
        min_capital: int,
        guarantee_amount: int,
        current_rating: str = "BBB",
        project_count: int = 5
    ) -> IndustryRiskResult:
        """
        건설업 리스크 계산
        
        총 리스크 = 상속세 + 면허 유지 자본금 + 연대보증 채무
        
        Args:
            annual_profit: 최근 3년 평균 순이익
            net_assets: 순자산
            ownership: 지분율
            liquid_assets: 유동자산
            current_capital: 현재 자본금
            min_capital: 면허 유지 최소 자본금
            guarantee_amount: PF 대출 연대보증 총액
            current_rating: 현재 신용등급
            project_count: 진행 중인 프로젝트 수
        
        Returns:
            IndustryRiskResult: 리스크 계산 결과
        """
        # 1. 상속세 계산
        succession_result = self.simulator.simulate_liquidity_crisis(
            annual_profit=annual_profit,
            net_assets=net_assets,
            ownership=ownership,
            liquid_assets=liquid_assets
        )
        
        # 2. 면허 유지 자본금 부족액
        capital_shortage = max(0, min_capital - current_capital)
        
        # 3. 연대보증 채무 (전액 대물림)
        guarantee_debt = guarantee_amount
        
        # 4. 총 리스크
        total_risk = succession_result.tax_amount + capital_shortage + guarantee_debt
        
        # 5. 자본금 비율
        capital_ratio = int((current_capital / min_capital) * 100) if min_capital > 0 else 100
        
        # 6. 신용등급 하락 예상
        downgrade_rating = self._downgrade_rating(current_rating)
        
        # 7. 브리핑 생성
        const_data = self.intelligence_data["industries"]["construction"]
        briefing_template = self.intelligence_data["briefing_templates"]["construction"]
        
        briefing_sections = []
        for section in briefing_template["sections"]:
            content = section["content"].format(
                current_capital=current_capital,
                min_capital=min_capital,
                capital_ratio=capital_ratio,
                inheritance_tax=succession_result.tax_amount,
                cash_shortage=succession_result.cash_shortage,
                guarantee_amount=guarantee_amount,
                current_rating=current_rating,
                downgrade_rating=downgrade_rating,
                project_count=project_count
            )
            briefing_sections.append(f"### {section['section']}\n{content}")
        
        briefing = "\n\n".join(briefing_sections)
        
        # 8. 은유 및 압박 메시지
        metaphor = const_data["hooking_phrases"]["opening"]
        pressure = const_data["hooking_phrases"]["pressure"]
        
        return IndustryRiskResult(
            industry="건설업",
            inheritance_tax=succession_result.tax_amount,
            additional_risks={
                "면허_유지_자본금_부족": capital_shortage,
                "연대보증_채무": guarantee_debt
            },
            total_risk=total_risk,
            briefing=briefing,
            metaphor=metaphor,
            pressure_message=pressure
        )
    
    def _downgrade_rating(self, current_rating: str) -> str:
        """신용등급 하락 예상"""
        rating_map = {
            "AAA": "AA",
            "AA": "A",
            "A": "BBB",
            "BBB": "BB",
            "BB": "B",
            "B": "CCC",
            "CCC": "CC",
            "CC": "C",
            "C": "D"
        }
        return rating_map.get(current_rating, "D")
    
    def generate_industry_report(
        self,
        industry: str,
        **kwargs
    ) -> str:
        """
        업종별 전략적 보고서 생성
        
        Args:
            industry: "manufacturing" 또는 "construction"
            **kwargs: 업종별 필수 파라미터
        
        Returns:
            str: 전략적 보고서 (Markdown)
        """
        if industry == "manufacturing":
            result = self.calculate_manufacturing_risk(**kwargs)
        elif industry == "construction":
            result = self.calculate_construction_risk(**kwargs)
        else:
            raise ValueError(f"지원하지 않는 업종입니다: {industry}")
        
        report = f"""
# 🏭 {result.industry} CEO 리스크 분석 보고서

## 🔥 은유적 진단

{result.metaphor}

---

## 📊 리스크 계산 결과

### 상속세
**{result.inheritance_tax:,}원**

### 추가 리스크
"""
        
        for risk_name, risk_amount in result.additional_risks.items():
            report += f"- **{risk_name.replace('_', ' ')}**: {risk_amount:,}원\n"
        
        report += f"""
### 총 리스크
**{result.total_risk:,}원**

---

## 📋 상세 브리핑

{result.briefing}

---

## ⚡ 압박형 결론

{result.pressure_message}

---

**작성일**: 2026-03-31  
**작성자**: goldkey_Ai_masters2026 업종별 리스크 분석 엔진
"""
        
        return report


def main():
    """테스트 실행"""
    print("=" * 70)
    print("🏭 업종별 동적 리스크 산출 엔진")
    print("=" * 70)
    
    calculator = IndustryRiskCalculator()
    
    # 시나리오 1: 제조업
    print("\n📊 시나리오 1: 제조업 CEO")
    print("-" * 70)
    
    mfg_result = calculator.calculate_manufacturing_risk(
        annual_profit=5_000_000_000,  # 연 순이익 50억
        net_assets=20_000_000_000,    # 순자산 200억
        ownership=0.80,                # 지분 80%
        liquid_assets=2_000_000_000,  # 유동자산 20억
        equipment_assets=30_000_000_000,  # 설비자산 300억
        expected_accidents=1           # 예상 사고 1건
    )
    
    print(f"\n상속세: {mfg_result.inheritance_tax:,}원")
    print(f"중대재해 합의금: {mfg_result.additional_risks['중대재해_합의금']:,}원")
    print(f"설비 경매 손실: {mfg_result.additional_risks['설비_경매_손실']:,}원")
    print(f"총 리스크: {mfg_result.total_risk:,}원")
    
    # 시나리오 2: 건설업
    print("\n\n📊 시나리오 2: 건설업 CEO")
    print("-" * 70)
    
    const_result = calculator.calculate_construction_risk(
        annual_profit=3_000_000_000,  # 연 순이익 30억
        net_assets=15_000_000_000,    # 순자산 150억
        ownership=0.70,                # 지분 70%
        liquid_assets=1_000_000_000,  # 유동자산 10억
        current_capital=8_000_000_000,  # 현재 자본금 80억
        min_capital=7_000_000_000,    # 최소 자본금 70억
        guarantee_amount=20_000_000_000,  # 연대보증 200억
        current_rating="BBB",
        project_count=5
    )
    
    print(f"\n상속세: {const_result.inheritance_tax:,}원")
    print(f"면허 유지 자본금 부족: {const_result.additional_risks['면허_유지_자본금_부족']:,}원")
    print(f"연대보증 채무: {const_result.additional_risks['연대보증_채무']:,}원")
    print(f"총 리스크: {const_result.total_risk:,}원")
    
    # 전략적 보고서 생성
    print("\n\n" + "=" * 70)
    print("📄 제조업 전략적 보고서")
    print("=" * 70)
    
    mfg_report = calculator.generate_industry_report(
        industry="manufacturing",
        annual_profit=5_000_000_000,
        net_assets=20_000_000_000,
        ownership=0.80,
        liquid_assets=2_000_000_000,
        equipment_assets=30_000_000_000,
        expected_accidents=1
    )
    
    print(mfg_report)


if __name__ == "__main__":
    main()
