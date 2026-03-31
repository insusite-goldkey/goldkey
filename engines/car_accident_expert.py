# -*- coding: utf-8 -*-
"""
자동차사고 전문가 엔진 (Car Accident Expert Engine)
점수제+건수제 복합 할증 로직 및 경상환자 보상 제한 규정 구현

작성일: 2026-03-31
버전: 1.0
"""

import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta


class CarAccidentExpert:
    """
    자동차사고 분석 및 전략 수립 전문가 엔진
    - 점수제 + 건수제 복합 할증 로직
    - 경상환자(12~14급) 보상 제한
    - 경미사고 수리 가이드라인
    - 환입(Payback) 전략 시뮬레이션
    """
    
    # 부상 등급별 점수 및 대인배상 1 한도
    INJURY_GRADE_DATA = {
        1: {"score": 4.0, "liability_limit": 150_000_000, "severity": "사망"},
        2: {"score": 3.5, "liability_limit": 100_000_000, "severity": "중상"},
        3: {"score": 3.0, "liability_limit": 80_000_000, "severity": "중상"},
        4: {"score": 2.5, "liability_limit": 50_000_000, "severity": "중등도"},
        5: {"score": 2.5, "liability_limit": 40_000_000, "severity": "중등도"},
        6: {"score": 2.0, "liability_limit": 35_000_000, "severity": "중등도"},
        7: {"score": 2.0, "liability_limit": 30_000_000, "severity": "중등도"},
        8: {"score": 1.5, "liability_limit": 25_000_000, "severity": "경상"},
        9: {"score": 1.5, "liability_limit": 20_000_000, "severity": "경상"},
        10: {"score": 1.5, "liability_limit": 15_000_000, "severity": "경상"},
        11: {"score": 1.5, "liability_limit": 10_000_000, "severity": "경상"},
        12: {"score": 1.0, "liability_limit": 5_000_000, "severity": "경미"},
        13: {"score": 1.0, "liability_limit": 3_000_000, "severity": "경미"},
        14: {"score": 1.0, "liability_limit": 1_000_000, "severity": "경미"},
    }
    
    # 물적 사고 할증기준금액
    PROPERTY_DAMAGE_THRESHOLD = 2_000_000
    
    def __init__(self):
        """초기화"""
        pass
    
    def calculate_accident_score(
        self,
        injury_grade: Optional[int] = None,
        property_damage_amount: Optional[int] = None,
        is_own_vehicle: bool = False
    ) -> Dict:
        """
        사고 점수 계산
        
        Args:
            injury_grade: 부상 등급 (1~14급, None이면 무상해)
            property_damage_amount: 대물 피해액 (원)
            is_own_vehicle: 자차 단독 사고 여부
        
        Returns:
            dict: 점수, 등급 변동, 상세 정보
        """
        total_score = 0.0
        details = []
        
        # 대인 사고 점수
        if injury_grade:
            if injury_grade in self.INJURY_GRADE_DATA:
                injury_score = self.INJURY_GRADE_DATA[injury_grade]["score"]
                severity = self.INJURY_GRADE_DATA[injury_grade]["severity"]
                total_score += injury_score
                details.append(f"대인 {injury_grade}급({severity}): {injury_score}점")
            else:
                details.append(f"⚠️ 잘못된 부상 등급: {injury_grade}")
        
        # 대물/자차 사고 점수
        if property_damage_amount:
            if is_own_vehicle:
                # 자차 단독 사고
                if property_damage_amount >= self.PROPERTY_DAMAGE_THRESHOLD:
                    property_score = 1.0
                else:
                    property_score = 0.5
                total_score += property_score
                details.append(f"자차 단독 {property_damage_amount:,}원: {property_score}점")
            else:
                # 대물 사고
                if property_damage_amount >= self.PROPERTY_DAMAGE_THRESHOLD:
                    property_score = 1.0
                else:
                    property_score = 0.5
                total_score += property_score
                details.append(f"대물 {property_damage_amount:,}원: {property_score}점")
        
        # 등급 변동 예측 (1점당 1등급 하락)
        grade_drop = int(total_score)
        
        return {
            "total_score": total_score,
            "grade_drop": grade_drop,
            "details": details,
            "accident_count": 1  # 모든 사고는 1건으로 카운트
        }
    
    def analyze_accident_frequency_risk(
        self,
        past_1year_count: int,
        past_3year_count: int,
        current_accident_score: float
    ) -> Dict:
        """
        사고 건수제 요율 리스크 분석
        
        Args:
            past_1year_count: 최근 1년 내 사고 건수
            past_3year_count: 최근 3년 내 사고 건수
            current_accident_score: 이번 사고 점수
        
        Returns:
            dict: 건수 리스크, 경고 레벨, 권고 사항
        """
        # 이번 사고 포함 건수
        new_1year_count = past_1year_count + 1
        new_3year_count = past_3year_count + 1
        
        # 리스크 레벨 판정
        if new_3year_count >= 3:
            risk_level = "🔴 위기"
            warning = "인수 거절 또는 공동인수 전환 고위험"
            premium_impact = "50~100% 폭등 가능"
        elif new_3year_count >= 2:
            risk_level = "🚨 고위험"
            warning = "사고건수요율 대폭 가산"
            premium_impact = "30~50% 상승 예상"
        elif new_1year_count >= 1:
            risk_level = "⚠️ 주의"
            warning = "사고건수요율 가산"
            premium_impact = "10~15% 상승 예상"
        else:
            risk_level = "✅ 정상"
            warning = "건수 요율 영향 미미"
            premium_impact = "5% 이내 상승"
        
        # 환입 권고 여부
        payback_recommended = False
        payback_reason = ""
        
        if current_accident_score <= 0.5 and new_3year_count >= 2:
            payback_recommended = True
            payback_reason = "소액 사고이나 건수 누적으로 인한 요율 폭등 방지"
        elif current_accident_score <= 1.0 and new_3year_count >= 3:
            payback_recommended = True
            payback_reason = "인수 거절 리스크 방어"
        
        return {
            "new_1year_count": new_1year_count,
            "new_3year_count": new_3year_count,
            "risk_level": risk_level,
            "warning": warning,
            "premium_impact": premium_impact,
            "payback_recommended": payback_recommended,
            "payback_reason": payback_reason
        }
    
    def calculate_patient_burden(
        self,
        injury_grade: int,
        fault_ratio: int,
        total_treatment_cost: int,
        coverage_type: str = "자상"
    ) -> Dict:
        """
        경상환자(12~14급) 치료비 본인 부담 계산
        
        Args:
            injury_grade: 부상 등급 (12~14급)
            fault_ratio: 본인 과실 비율 (%)
            total_treatment_cost: 총 치료비 (원)
            coverage_type: 가입 담보 ("자상", "자손", "미가입")
        
        Returns:
            dict: 본인 부담액, 경고 메시지
        """
        if injury_grade not in [12, 13, 14]:
            return {
                "patient_burden": 0,
                "warning": None,
                "applicable": False
            }
        
        # 대인배상 1 한도
        liability_limit = self.INJURY_GRADE_DATA[injury_grade]["liability_limit"]
        
        # 한도 초과분
        excess = max(0, total_treatment_cost - liability_limit)
        
        # 본인 부담액 (과실 비율 적용)
        patient_burden = int(excess * (fault_ratio / 100))
        
        # 담보 확인
        warning = None
        if coverage_type == "자손" and patient_burden > 1_500_000:
            warning = "⚠️ 자손 한도(1,500만 원) 초과 위험 - 자비 부담 발생 가능"
        elif coverage_type == "미가입":
            warning = "🚨 전액 자비 부담 - 즉시 담보 가입 권고"
        elif patient_burden > 0:
            warning = f"⚠️ 치료비 본인 부담 {patient_burden:,}원 발생 예상"
        
        return {
            "patient_burden": patient_burden,
            "liability_limit": liability_limit,
            "excess": excess,
            "warning": warning,
            "applicable": True,
            "coverage_type": coverage_type
        }
    
    def validate_repair_claim(
        self,
        damage_severity: str,
        damaged_part: str,
        vehicle_type: str = "국산차"
    ) -> Dict:
        """
        경미사고 수리 가이드라인 검증
        
        Args:
            damage_severity: 손상 정도 ("코팅손상", "색상손상", "긁힘")
            damaged_part: 손상 부위 ("범퍼", "도어", "펜더" 등)
            vehicle_type: 차량 유형 ("국산차", "수입차", "고급수입차")
        
        Returns:
            dict: 수리 유형, 인정 비용, 비인정 비용
        """
        # 부품별 교체 비용표
        part_prices = {
            "국산차": {
                "범퍼": 300_000, "도어": 500_000, "펜더": 400_000,
                "후드": 600_000, "트렁크리드": 500_000, "루프": 800_000, "쿼터패널": 700_000
            },
            "수입차": {
                "범퍼": 800_000, "도어": 1_500_000, "펜더": 1_200_000,
                "후드": 1_800_000, "트렁크리드": 1_500_000, "루프": 2_500_000, "쿼터패널": 2_000_000
            },
            "고급수입차": {
                "범퍼": 1_500_000, "도어": 3_000_000, "펜더": 2_500_000,
                "후드": 4_000_000, "트렁크리드": 3_000_000, "루프": 5_000_000, "쿼터패널": 4_500_000
            }
        }
        
        # 손상 정도별 인정 비용
        if damage_severity == "코팅손상":
            repair_type = "광택(폴리싱) + 코팅"
            approved_cost = 100_000
        elif damage_severity == "색상손상":
            repair_type = "도장(도색)"
            approved_cost = 300_000
        elif damage_severity == "긁힘":
            repair_type = "판금 + 도장"
            approved_cost = 500_000
        else:
            repair_type = "알 수 없음"
            approved_cost = 0
        
        # 교체 비용 (비인정)
        replacement_cost = part_prices.get(vehicle_type, {}).get(damaged_part, 0)
        
        return {
            "repair_type": repair_type,
            "approved_cost": approved_cost,
            "replacement_cost": replacement_cost,
            "guideline": "금융감독원 경미사고 수리 가이드라인",
            "replacement_allowed": False,
            "damage_severity": damage_severity,
            "damaged_part": damaged_part
        }
    
    def simulate_payback_benefit(
        self,
        accident_score: float,
        insurance_claim_amount: int,
        current_grade: str,
        past_3year_count: int,
        estimated_annual_premium: int
    ) -> Dict:
        """
        환입(Payback) 전략 실익 시뮬레이션
        
        Args:
            accident_score: 사고 점수
            insurance_claim_amount: 보험금 청구액 (원)
            current_grade: 현재 등급 (예: "15Z")
            past_3year_count: 과거 3년 사고 건수
            estimated_annual_premium: 연간 보험료 추정액 (원)
        
        Returns:
            dict: 환입 시/보험처리 시 비교, 권고 사항
        """
        # 환입 시
        payback_immediate_cost = insurance_claim_amount
        payback_accident_count = past_3year_count  # 건수 유지
        payback_grade_change = 0  # 등급 유지
        
        # 보험 처리 시
        claim_immediate_cost = 0
        claim_accident_count = past_3year_count + 1
        claim_grade_change = int(accident_score)
        
        # 3년간 보험료 추정
        if claim_accident_count >= 2:
            claim_premium_multiplier = 1.5  # 50% 상승
        elif claim_accident_count >= 1:
            claim_premium_multiplier = 1.15  # 15% 상승
        else:
            claim_premium_multiplier = 1.0
        
        payback_3year_premium = estimated_annual_premium * 3
        claim_3year_premium = int(estimated_annual_premium * claim_premium_multiplier * 3)
        
        # 총 손익
        payback_total_cost = payback_immediate_cost + payback_3year_premium
        claim_total_cost = claim_immediate_cost + claim_3year_premium
        
        net_benefit = claim_total_cost - payback_total_cost
        
        # 권고 사항
        if net_benefit > 0:
            recommendation = f"✅ 환입 권고 (3년간 약 {net_benefit:,}원 절감)"
        else:
            recommendation = f"❌ 보험 처리 권고 (환입 시 {abs(net_benefit):,}원 손실)"
        
        return {
            "payback_scenario": {
                "immediate_cost": payback_immediate_cost,
                "accident_count": payback_accident_count,
                "grade_change": payback_grade_change,
                "3year_premium": payback_3year_premium,
                "total_cost": payback_total_cost
            },
            "claim_scenario": {
                "immediate_cost": claim_immediate_cost,
                "accident_count": claim_accident_count,
                "grade_change": claim_grade_change,
                "3year_premium": claim_3year_premium,
                "total_cost": claim_total_cost
            },
            "net_benefit": net_benefit,
            "recommendation": recommendation
        }
    
    def generate_ceo_briefing(
        self,
        accident_data: Dict,
        past_history: Dict,
        customer_info: Dict
    ) -> str:
        """
        CEO급 전략 브리핑 생성
        
        Args:
            accident_data: 사고 정보
            past_history: 과거 이력
            customer_info: 고객 정보
        
        Returns:
            str: 마크다운 형식 브리핑
        """
        briefing = f"""
## 🚗 자동차사고 전략 브리핑

### 📋 사고 개요
- **사고 일자**: {accident_data.get('accident_date', 'N/A')}
- **사고 유형**: {accident_data.get('accident_type', 'N/A')}
- **과실 비율**: 본인 {accident_data.get('fault_ratio', 0)}% / 상대방 {100 - accident_data.get('fault_ratio', 0)}%

### 📊 점수제 분석 (등급 영향)
- **사고 점수**: {accident_data.get('score', 0)}점
- **예상 등급 변동**: {accident_data.get('grade_drop', 0)}단계 하락
- **현재 등급**: {past_history.get('current_grade', 'N/A')} → **예상 등급**: {past_history.get('expected_grade', 'N/A')}

### 🔥 건수제 분석 (요율 영향)
- **과거 1년 건수**: {past_history.get('past_1year_count', 0)}건
- **과거 3년 건수**: {past_history.get('past_3year_count', 0)}건
- **이번 사고 포함**: {past_history.get('new_3year_count', 1)}건
- **리스크 레벨**: {past_history.get('risk_level', 'N/A')}
- **보험료 영향**: {past_history.get('premium_impact', 'N/A')}

### 💡 전략 권고
{past_history.get('recommendation', '데이터 부족')}

---
**생성 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return briefing
