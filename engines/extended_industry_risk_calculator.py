# -*- coding: utf-8 -*-
"""
확장 업종별 동적 리스크 산출 엔진
유통/의료/IT/의료종합병원 특화 리스크 계산

작성일: 2026-03-31
목적: 확장 업종별 특화 리스크를 동적으로 계산하여 압박형 브리핑 생성
"""

import json
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass
from engines.ceo_succession_simulator import CEOSuccessionSimulator


@dataclass
class ExtendedIndustryRiskResult:
    """확장 업종별 리스크 계산 결과"""
    industry: str
    inheritance_tax: int
    additional_risks: Dict[str, int]
    total_risk: int
    briefing: str
    metaphor: str
    pressure_message: str


class ExtendedIndustryRiskCalculator:
    """
    확장 업종별 동적 리스크 산출 엔진
    
    핵심 기능:
    1. 유통/물류업: 상속세 + 재고 덤핑 손실 + 미수금 회수 불능액
    2. 의료/병의원: 상속세 + 의료장비 대출 잔액 + 병원 권리금 손실
    3. IT/지식서비스업: 상속세 + 핵심 인력 이탈 손실 + 스톡옵션 행사 비용
    4. 의료종합병원: 낙오 원장 대출 잔액 + 동료 채무 전가액 + 유가족 상속 채무
    """
    
    def __init__(self):
        """초기화"""
        self.simulator = CEOSuccessionSimulator()
        self.intelligence_data = self._load_intelligence_data()
    
    def _load_intelligence_data(self) -> Dict:
        """확장 업종별 리스크 지능 데이터 로드"""
        json_path = Path(__file__).parent.parent / "hq_backend" / "knowledge_base" / "extended_industry_risk_intelligence.json"
        
        if not json_path.exists():
            raise FileNotFoundError(f"지능 데이터 파일을 찾을 수 없습니다: {json_path}")
        
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def calculate_distribution_risk(
        self,
        annual_profit: int,
        net_assets: int,
        ownership: float,
        liquid_assets: int,
        inventory_value: int,
        receivables: int,
        dumping_loss_rate: float = 0.30
    ) -> ExtendedIndustryRiskResult:
        """
        유통/물류업 리스크 계산
        
        총 리스크 = 상속세 + 재고 덤핑 손실 + 미수금 회수 불능액
        
        Args:
            annual_profit: 최근 3년 평균 순이익
            net_assets: 순자산
            ownership: 지분율
            liquid_assets: 유동자산
            inventory_value: 재고자산 가치
            receivables: 매출채권 (미수금)
            dumping_loss_rate: 덤핑 손실률 (기본 30%)
        
        Returns:
            ExtendedIndustryRiskResult: 리스크 계산 결과
        """
        # 1. 상속세 계산
        succession_result = self.simulator.simulate_liquidity_crisis(
            annual_profit=annual_profit,
            net_assets=net_assets,
            ownership=ownership,
            liquid_assets=liquid_assets
        )
        
        # 2. 재고 덤핑 손실 (급매각 시 30% 손실)
        dumping_loss = int(inventory_value * dumping_loss_rate)
        
        # 3. 미수금 회수 불능액 (20% 회수 불능 가정)
        bad_debt = int(receivables * 0.20)
        
        # 4. 총 리스크
        total_risk = succession_result.tax_amount + dumping_loss + bad_debt
        
        # 5. 재고자산 비중
        inventory_ratio = int((inventory_value / (net_assets + inventory_value)) * 100)
        
        # 6. 재고 회전율 (가정: 연 4회)
        turnover_rate = 4.0
        
        # 7. 브리핑 생성
        dist_data = self.intelligence_data["industries"]["distribution"]
        briefing_template = self.intelligence_data["briefing_templates"]["distribution"]
        
        briefing_sections = []
        for section in briefing_template["sections"]:
            content = section["content"].format(
                inventory_value=inventory_value,
                inventory_ratio=inventory_ratio,
                turnover_rate=turnover_rate,
                inheritance_tax=succession_result.tax_amount,
                dumping_loss=dumping_loss
            )
            briefing_sections.append(f"### {section['section']}\n{content}")
        
        briefing = "\n\n".join(briefing_sections)
        
        # 8. 은유 및 압박 메시지
        metaphor = dist_data["hooking_phrases"]["opening"]
        pressure = dist_data["hooking_phrases"]["pressure"]
        
        return ExtendedIndustryRiskResult(
            industry="유통/물류업",
            inheritance_tax=succession_result.tax_amount,
            additional_risks={
                "재고_덤핑_손실": dumping_loss,
                "미수금_회수_불능액": bad_debt
            },
            total_risk=total_risk,
            briefing=briefing,
            metaphor=metaphor,
            pressure_message=pressure
        )
    
    def calculate_medical_risk(
        self,
        annual_profit: int,
        net_assets: int,
        ownership: float,
        liquid_assets: int,
        equipment_debt: int,
        personal_debt: int,
        hospital_goodwill_rate: float = 0.50
    ) -> ExtendedIndustryRiskResult:
        """
        의료/병의원 리스크 계산
        
        총 리스크 = 상속세 + 의료장비 대출 잔액 + 병원 권리금 손실
        
        Args:
            annual_profit: 최근 3년 평균 순이익
            net_assets: 순자산
            ownership: 지분율
            liquid_assets: 유동자산
            equipment_debt: 의료장비 리스 및 대출 잔액
            personal_debt: 원장 개인 보증 대출
            hospital_goodwill_rate: 병원 가치 중 권리금 비중 (기본 50%)
        
        Returns:
            ExtendedIndustryRiskResult: 리스크 계산 결과
        """
        # 1. 상속세 계산
        succession_result = self.simulator.simulate_liquidity_crisis(
            annual_profit=annual_profit,
            net_assets=net_assets,
            ownership=ownership,
            liquid_assets=liquid_assets
        )
        
        # 2. 의료장비 대출 잔액 (전액 상환 필요)
        equipment_debt_total = equipment_debt
        
        # 3. 병원 권리금 손실 (원장 유고 시 권리금 소멸)
        hospital_value = net_assets + equipment_debt
        goodwill_loss = int(hospital_value * hospital_goodwill_rate)
        
        # 4. 총 리스크
        total_risk = succession_result.tax_amount + equipment_debt_total + goodwill_loss
        
        # 5. 브리핑 생성
        med_data = self.intelligence_data["industries"]["medical"]
        briefing_template = self.intelligence_data["briefing_templates"]["medical"]
        
        briefing_sections = []
        for section in briefing_template["sections"]:
            content = section["content"].format(
                equipment_debt=equipment_debt,
                inheritance_tax=succession_result.tax_amount,
                personal_debt=personal_debt
            )
            briefing_sections.append(f"### {section['section']}\n{content}")
        
        briefing = "\n\n".join(briefing_sections)
        
        # 6. 은유 및 압박 메시지
        metaphor = med_data["hooking_phrases"]["opening"]
        pressure = med_data["hooking_phrases"]["pressure"]
        
        return ExtendedIndustryRiskResult(
            industry="의료/병의원",
            inheritance_tax=succession_result.tax_amount,
            additional_risks={
                "의료장비_대출_잔액": equipment_debt_total,
                "병원_권리금_손실": goodwill_loss
            },
            total_risk=total_risk,
            briefing=briefing,
            metaphor=metaphor,
            pressure_message=pressure
        )
    
    def calculate_it_service_risk(
        self,
        annual_profit: int,
        net_assets: int,
        ownership: float,
        liquid_assets: int,
        keyman_count: int,
        keyman_ratio: float,
        stock_option_value: int
    ) -> ExtendedIndustryRiskResult:
        """
        IT/지식서비스업 리스크 계산
        
        총 리스크 = 상속세 + 핵심 인력 이탈 손실 + 스톡옵션 행사 비용
        
        Args:
            annual_profit: 최근 3년 평균 순이익
            net_assets: 순자산
            ownership: 지분율
            liquid_assets: 유동자산
            keyman_count: 핵심 인력 수
            keyman_ratio: 핵심 인력 매출 기여도
            stock_option_value: 스톡옵션 미행사분 가치
        
        Returns:
            ExtendedIndustryRiskResult: 리스크 계산 결과
        """
        # 1. 상속세 계산
        succession_result = self.simulator.simulate_liquidity_crisis(
            annual_profit=annual_profit,
            net_assets=net_assets,
            ownership=ownership,
            liquid_assets=liquid_assets
        )
        
        # 2. 핵심 인력 이탈 손실 (기업 가치의 keyman_ratio만큼 손실)
        company_value = succession_result.taxable_amount + 200_000_000
        keyman_loss = int(company_value * keyman_ratio)
        
        # 3. 스톡옵션 행사 비용 (핵심 인력 유지 비용)
        stock_option_cost = stock_option_value
        
        # 4. 총 리스크
        total_risk = succession_result.tax_amount + keyman_loss + stock_option_cost
        
        # 5. 브리핑 생성
        it_data = self.intelligence_data["industries"]["it_service"]
        briefing_template = self.intelligence_data["briefing_templates"]["it_service"]
        
        briefing_sections = []
        for section in briefing_template["sections"]:
            content = section["content"].format(
                annual_profit=annual_profit,
                stock_value=company_value,
                inheritance_tax=succession_result.tax_amount,
                keyman_count=keyman_count,
                keyman_ratio=int(keyman_ratio * 100)
            )
            briefing_sections.append(f"### {section['section']}\n{content}")
        
        briefing = "\n\n".join(briefing_sections)
        
        # 6. 은유 및 압박 메시지
        metaphor = it_data["hooking_phrases"]["opening"]
        pressure = it_data["hooking_phrases"]["pressure"]
        
        return ExtendedIndustryRiskResult(
            industry="IT/지식서비스업",
            inheritance_tax=succession_result.tax_amount,
            additional_risks={
                "핵심_인력_이탈_손실": keyman_loss,
                "스톡옵션_행사_비용": stock_option_cost
            },
            total_risk=total_risk,
            briefing=briefing,
            metaphor=metaphor,
            pressure_message=pressure
        )
    
    def calculate_medical_group_risk(
        self,
        doctor_count: int,
        total_debt: int,
        dropout_doctor_debt: int,
        dropout_doctor_revenue_ratio: float
    ) -> ExtendedIndustryRiskResult:
        """
        의료종합병원 리스크 계산
        
        총 리스크 = 낙오 원장 대출 잔액 + 동료 채무 전가액 + 유가족 상속 채무
        
        Args:
            doctor_count: 총 원장 수
            total_debt: 총 대출액
            dropout_doctor_debt: 낙오 원장의 대출 잔액
            dropout_doctor_revenue_ratio: 낙오 원장의 수익 기여도
        
        Returns:
            ExtendedIndustryRiskResult: 리스크 계산 결과
        """
        # 1. 낙오 원장 대출 잔액
        dropout_debt = dropout_doctor_debt
        
        # 2. 동료 채무 전가액 (나머지 원장들이 분담)
        remaining_doctors = doctor_count - 1
        colleague_burden = dropout_debt  # 전액 분담
        per_doctor_burden = int(colleague_burden / remaining_doctors) if remaining_doctors > 0 else 0
        
        # 3. 유가족 상속 채무 (개인 대출 전액)
        inherited_debt = dropout_debt
        
        # 4. 총 리스크
        total_risk = dropout_debt + colleague_burden + inherited_debt
        
        # 5. 인당 대출 분담률
        per_doctor_debt = int(total_debt / doctor_count)
        
        # 6. 브리핑 생성
        mg_data = self.intelligence_data["industries"]["medical_group"]
        briefing_template = self.intelligence_data["briefing_templates"]["medical_group"]
        
        briefing_sections = []
        for section in briefing_template["sections"]:
            content = section["content"].format(
                total_debt=total_debt,
                doctor_count=doctor_count,
                per_doctor_debt=per_doctor_debt,
                dropout_debt=dropout_debt,
                remaining_doctors=remaining_doctors,
                additional_burden=per_doctor_burden,
                inherited_debt=inherited_debt
            )
            briefing_sections.append(f"### {section['section']}\n{content}")
        
        briefing = "\n\n".join(briefing_sections)
        
        # 7. 은유 및 압박 메시지
        metaphor = mg_data["hooking_phrases"]["opening"]
        pressure = mg_data["hooking_phrases"]["pressure"]
        
        return ExtendedIndustryRiskResult(
            industry="의료종합병원",
            inheritance_tax=0,  # 상속세는 별도 계산
            additional_risks={
                "낙오_원장_대출_잔액": dropout_debt,
                "동료_채무_전가액": colleague_burden,
                "유가족_상속_채무": inherited_debt
            },
            total_risk=total_risk,
            briefing=briefing,
            metaphor=metaphor,
            pressure_message=pressure
        )
    
    def generate_industry_report(
        self,
        industry: str,
        **kwargs
    ) -> str:
        """
        확장 업종별 전략적 보고서 생성
        
        Args:
            industry: "distribution", "medical", "it_service", "medical_group"
            **kwargs: 업종별 필수 파라미터
        
        Returns:
            str: 전략적 보고서 (Markdown)
        """
        if industry == "distribution":
            result = self.calculate_distribution_risk(**kwargs)
        elif industry == "medical":
            result = self.calculate_medical_risk(**kwargs)
        elif industry == "it_service":
            result = self.calculate_it_service_risk(**kwargs)
        elif industry == "medical_group":
            result = self.calculate_medical_group_risk(**kwargs)
        else:
            raise ValueError(f"지원하지 않는 업종입니다: {industry}")
        
        report = f"""
# 🏢 {result.industry} CEO 리스크 분석 보고서

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
**작성자**: goldkey_Ai_masters2026 확장 업종별 리스크 분석 엔진
"""
        
        return report


def main():
    """테스트 실행"""
    print("=" * 70)
    print("🏢 확장 업종별 동적 리스크 산출 엔진")
    print("=" * 70)
    
    calculator = ExtendedIndustryRiskCalculator()
    
    # 시나리오 1: 유통/물류업
    print("\n📊 시나리오 1: 유통/물류업 CEO")
    print("-" * 70)
    
    dist_result = calculator.calculate_distribution_risk(
        annual_profit=3_000_000_000,  # 연 순이익 30억
        net_assets=10_000_000_000,    # 순자산 100억
        ownership=0.70,                # 지분 70%
        liquid_assets=1_000_000_000,  # 유동자산 10억
        inventory_value=15_000_000_000,  # 재고자산 150억
        receivables=5_000_000_000     # 매출채권 50억
    )
    
    print(f"\n상속세: {dist_result.inheritance_tax:,}원")
    print(f"재고 덤핑 손실: {dist_result.additional_risks['재고_덤핑_손실']:,}원")
    print(f"미수금 회수 불능액: {dist_result.additional_risks['미수금_회수_불능액']:,}원")
    print(f"총 리스크: {dist_result.total_risk:,}원")
    
    # 시나리오 2: 의료종합병원
    print("\n\n📊 시나리오 2: 의료종합병원 (5명 공동 운영)")
    print("-" * 70)
    
    mg_result = calculator.calculate_medical_group_risk(
        doctor_count=5,
        total_debt=15_000_000_000,  # 총 대출 150억
        dropout_doctor_debt=3_000_000_000,  # 낙오 원장 대출 30억
        dropout_doctor_revenue_ratio=0.25  # 수익 기여도 25%
    )
    
    print(f"\n낙오 원장 대출 잔액: {mg_result.additional_risks['낙오_원장_대출_잔액']:,}원")
    print(f"동료 채무 전가액: {mg_result.additional_risks['동료_채무_전가액']:,}원")
    print(f"유가족 상속 채무: {mg_result.additional_risks['유가족_상속_채무']:,}원")
    print(f"총 리스크: {mg_result.total_risk:,}원")


if __name__ == "__main__":
    main()
