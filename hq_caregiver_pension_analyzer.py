"""
hq_caregiver_pension_analyzer.py — 간병 공백 및 노후 자산 전용 프로토콜
[GP-STEP15-D] Goldkey AI Masters 2026

목적: 간병 보험의 보장 기간 한계(365일)와 연금의 요양비 전용을 통한 '마르지 않는 재원' 확보

핵심 개념:
- 간병인 보험 365일+180일 리스크: 1년 보장 후 발생하는 보장 공백(면책 기간)
- 개인연금 LTC(장기요양) 전환: 연금을 요양병원비로 전용하는 자급자족 프로토콜
- 치매/파킨슨 융합 설계: 인지 능력은 있으나 거동이 불가한 경우의 보장 공백 방지

핵심 기능:
1. 간병인 보험 365일 공백 분석
2. 연금 LTC 전환 시뮬레이션
3. 치매 및 파킨슨 융합 설계
4. 알츠하이머/혈관성 치매/외상성 치매 연쇄 고리 시각화
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal


# ══════════════════════════════════════════════════════════════════════════════
# [1] 간병인 보험 365일+180일 리스크 분석
# ══════════════════════════════════════════════════════════════════════════════

def analyze_caregiver_insurance_gap(
    daily_benefit: int,
    coverage_days: int = 365,
    waiting_period_days: int = 180,
    monthly_caregiving_cost: int = 4000000
) -> Dict[str, Any]:
    """
    간병인 보험 365일 공백 분석
    
    Args:
        daily_benefit: 일당 (예: 100,000원)
        coverage_days: 보장 일수 (기본값 365일)
        waiting_period_days: 면책 기간 (기본값 180일)
        monthly_caregiving_cost: 월 간병비 (예: 4,000,000원)
    
    Returns:
        dict: {
            "total_benefit": 36500000,
            "coverage_months": 12,
            "gap_period_days": 180,
            "gap_cost": 24000000,
            "recommendations": [...]
        }
    """
    # 총 보험금
    total_benefit = daily_benefit * coverage_days
    
    # 보장 기간 (개월)
    coverage_months = coverage_days // 30
    
    # 공백 기간 비용
    gap_cost = int((waiting_period_days / 30) * monthly_caregiving_cost)
    
    # 일일 간병비
    daily_caregiving_cost = monthly_caregiving_cost // 30
    
    # 보험금 vs 실제 간병비 비교
    actual_caregiving_cost_total = monthly_caregiving_cost * coverage_months
    benefit_shortage = actual_caregiving_cost_total - total_benefit
    
    # 타임라인 생성
    timeline = []
    
    # 1단계: 보장 기간 (365일)
    timeline.append({
        "period": "1~365일 (1년)",
        "status": "보장 중",
        "daily_benefit": daily_benefit,
        "monthly_benefit": daily_benefit * 30,
        "actual_cost": monthly_caregiving_cost,
        "gap": monthly_caregiving_cost - (daily_benefit * 30),
        "description": f"간병인 보험 일당 {daily_benefit:,}원 지급 (실제 비용 대비 부족분 발생 가능)"
    })
    
    # 2단계: 공백 기간 (180일)
    timeline.append({
        "period": "366~545일 (6개월)",
        "status": "보장 공백 (면책 기간)",
        "daily_benefit": 0,
        "monthly_benefit": 0,
        "actual_cost": monthly_caregiving_cost,
        "gap": monthly_caregiving_cost,
        "description": f"⚠️ 전액 자비 부담 (월 {monthly_caregiving_cost:,}원 × 6개월 = {gap_cost:,}원)"
    })
    
    # 3단계: 재보장 (이론상)
    timeline.append({
        "period": "546일~ (재보장)",
        "status": "재보장 가능 (보험사 정책에 따라 다름)",
        "daily_benefit": daily_benefit,
        "monthly_benefit": daily_benefit * 30,
        "actual_cost": monthly_caregiving_cost,
        "gap": monthly_caregiving_cost - (daily_benefit * 30),
        "description": "재보장 여부는 보험사 약관에 따라 다름 (일부 보험사는 재보장 불가)"
    })
    
    # 권고사항
    recommendations = [
        f"⚠️ 간병인 보험 공백 기간: {waiting_period_days}일 ({waiting_period_days // 30}개월)",
        f"⚠️ 공백 기간 비용: {gap_cost:,}원 (월 {monthly_caregiving_cost:,}원 × {waiting_period_days // 30}개월)",
        f"💡 공백 기간 대비 전략: 추가 진단비 {gap_cost:,}원 이상 확보 필요",
        f"💡 또는 연금 LTC 전환으로 자급자족 프로토콜 구축"
    ]
    
    if benefit_shortage > 0:
        recommendations.append(
            f"⚠️ 보장 기간 중에도 부족분 발생: {benefit_shortage:,}원 "
            f"(일당 {daily_benefit:,}원으로는 실제 간병비 {daily_caregiving_cost:,}원 부족)"
        )
    
    return {
        "daily_benefit": daily_benefit,
        "coverage_days": coverage_days,
        "coverage_months": coverage_months,
        "total_benefit": total_benefit,
        "waiting_period_days": waiting_period_days,
        "gap_period_months": waiting_period_days // 30,
        "gap_cost": gap_cost,
        "actual_caregiving_cost_total": actual_caregiving_cost_total,
        "benefit_shortage": benefit_shortage,
        "timeline": timeline,
        "recommendations": recommendations,
        "alert_message": f"⚠️ 간병인 보험 공백: {waiting_period_days}일 ({waiting_period_days // 30}개월) 동안 {gap_cost:,}원 자비 부담"
    }


# ══════════════════════════════════════════════════════════════════════════════
# [2] 개인연금 LTC(장기요양) 전환 시뮬레이션
# ══════════════════════════════════════════════════════════════════════════════

def simulate_pension_ltc_conversion(
    monthly_pension: int,
    ltc_multiplier: float = 2.0,
    ltc_duration_years: int = 10,
    monthly_caregiving_cost: int = 4000000
) -> Dict[str, Any]:
    """
    연금 LTC(장기요양) 전환 시뮬레이션
    
    Args:
        monthly_pension: 월 연금액 (예: 2,000,000원)
        ltc_multiplier: LTC 전환 시 증액 배율 (기본값 2.0배)
        ltc_duration_years: LTC 지급 기간 (기본값 10년)
        monthly_caregiving_cost: 월 간병비 (예: 4,000,000원)
    
    Returns:
        dict: {
            "monthly_pension": 2000000,
            "ltc_monthly_benefit": 4000000,
            "ltc_total_benefit": 480000000,
            "self_sufficiency": True,
            "recommendations": [...]
        }
    """
    # LTC 전환 시 월 지급액
    ltc_monthly_benefit = int(monthly_pension * ltc_multiplier)
    
    # LTC 총 지급액
    ltc_total_benefit = ltc_monthly_benefit * 12 * ltc_duration_years
    
    # 자급자족 가능 여부
    self_sufficiency = ltc_monthly_benefit >= monthly_caregiving_cost
    
    # 부족분 또는 잉여분
    monthly_gap = ltc_monthly_benefit - monthly_caregiving_cost
    
    # 권고사항
    recommendations = []
    
    if self_sufficiency:
        recommendations.append(
            f"✅ 자급자족 프로토콜 성공: LTC 월 {ltc_monthly_benefit:,}원으로 "
            f"간병비 {monthly_caregiving_cost:,}원 충당 가능"
        )
        if monthly_gap > 0:
            recommendations.append(
                f"✅ 잉여분 발생: 월 {monthly_gap:,}원 (가족 생활비로 활용 가능)"
            )
    else:
        shortage = abs(monthly_gap)
        recommendations.append(
            f"⚠️ 자급자족 실패: LTC 월 {ltc_monthly_benefit:,}원으로는 "
            f"간병비 {monthly_caregiving_cost:,}원 부족 (월 {shortage:,}원 부족)"
        )
        recommendations.append(
            f"💡 연금 증액 필요: 월 연금액을 {int(monthly_caregiving_cost / ltc_multiplier):,}원 이상으로 증액"
        )
    
    # LTC 전환 조건
    ltc_conditions = [
        "장기요양등급 1~5등급 판정",
        "또는 일상생활장해(ADLs) 3개 이상 불가",
        "또는 인지장해(치매) 진단"
    ]
    
    return {
        "monthly_pension": monthly_pension,
        "ltc_multiplier": ltc_multiplier,
        "ltc_monthly_benefit": ltc_monthly_benefit,
        "ltc_duration_years": ltc_duration_years,
        "ltc_total_benefit": ltc_total_benefit,
        "monthly_caregiving_cost": monthly_caregiving_cost,
        "monthly_gap": monthly_gap,
        "self_sufficiency": self_sufficiency,
        "ltc_conditions": ltc_conditions,
        "recommendations": recommendations,
        "alert_message": "✅ 마르지 않는 재원: 연금 LTC 전환으로 10년간 자급자족 가능" if self_sufficiency else "⚠️ 연금 증액 필요"
    }


# ══════════════════════════════════════════════════════════════════════════════
# [3] 치매 및 파킨슨 융합 설계
# ══════════════════════════════════════════════════════════════════════════════

# 치매 및 파킨슨 KCD 코드
DEMENTIA_PARKINSONS_CODES = {
    "F00": {
        "name": "알츠하이머병에서의 치매",
        "category": "치매",
        "cognitive_impairment": True,
        "motor_impairment": False,
        "coverage_type": "치매 진단비",
        "average_benefit": 30000000
    },
    "F01": {
        "name": "혈관성 치매",
        "category": "치매",
        "cognitive_impairment": True,
        "motor_impairment": True,
        "coverage_type": "치매 진단비 + 뇌혈관질환 진단비",
        "average_benefit": 50000000,
        "connection": "뇌졸중 후유증으로 발생 가능"
    },
    "F02": {
        "name": "기타 질환에서의 치매",
        "category": "치매",
        "cognitive_impairment": True,
        "motor_impairment": False,
        "coverage_type": "치매 진단비",
        "average_benefit": 30000000
    },
    "F03": {
        "name": "상세불명의 치매",
        "category": "치매",
        "cognitive_impairment": True,
        "motor_impairment": False,
        "coverage_type": "치매 진단비",
        "average_benefit": 30000000
    },
    "G20": {
        "name": "파킨슨병",
        "category": "파킨슨",
        "cognitive_impairment": False,
        "motor_impairment": True,
        "coverage_type": "중대한 파킨슨병 진단비 (운동 능력 상실)",
        "average_benefit": 20000000,
        "gap_risk": "인지 능력은 있으나 거동 불가 시 치매 보험 부지급"
    },
    "G30": {
        "name": "알츠하이머병",
        "category": "치매",
        "cognitive_impairment": True,
        "motor_impairment": False,
        "coverage_type": "치매 진단비",
        "average_benefit": 30000000
    },
    "S06_traumatic": {
        "name": "외상성 뇌손상 후 치매",
        "category": "외상성 치매",
        "cognitive_impairment": True,
        "motor_impairment": True,
        "coverage_type": "치매 진단비 + 후유장해",
        "average_benefit": 50000000,
        "connection": "두부 외상(S06) 후 수년 내 발생 가능"
    }
}


def analyze_dementia_parkinsons_fusion(
    current_coverage: Dict[str, Any]
) -> Dict[str, Any]:
    """
    치매 및 파킨슨 융합 설계 분석
    
    Args:
        current_coverage: {
            "dementia_benefit": 30000000,
            "parkinsons_benefit": 0,
            "has_dementia": True,
            "has_parkinsons": False
        }
    
    Returns:
        dict: 융합 설계 분석 결과
    """
    dementia_benefit = current_coverage.get("dementia_benefit", 0)
    parkinsons_benefit = current_coverage.get("parkinsons_benefit", 0)
    has_dementia = current_coverage.get("has_dementia", False)
    has_parkinsons = current_coverage.get("has_parkinsons", False)
    
    # 보장 공백 분석
    gap_analysis = {
        "cognitive_only": {
            "scenario": "인지 장해만 있는 경우 (알츠하이머, F00)",
            "dementia_coverage": "✅ 지급" if has_dementia else "❌ 부지급",
            "parkinsons_coverage": "해당 없음",
            "risk": "낮음" if has_dementia else "높음"
        },
        "motor_only": {
            "scenario": "운동 장해만 있는 경우 (파킨슨병, G20)",
            "dementia_coverage": "❌ 부지급 (인지 장해 없음)",
            "parkinsons_coverage": "✅ 지급" if has_parkinsons else "❌ 부지급",
            "risk": "낮음" if has_parkinsons else "높음"
        },
        "both": {
            "scenario": "인지+운동 장해 모두 있는 경우 (혈관성 치매, F01)",
            "dementia_coverage": "✅ 지급" if has_dementia else "❌ 부지급",
            "parkinsons_coverage": "✅ 지급" if has_parkinsons else "❌ 부지급",
            "risk": "낮음" if (has_dementia and has_parkinsons) else "중간"
        }
    }
    
    # 보장 공백 리스크 평가
    critical_gap = not has_parkinsons and has_dementia
    
    # 권고사항
    recommendations = []
    
    if critical_gap:
        recommendations.append(
            "⚠️ 보장 공백 발견: 파킨슨병(G20) 특약 미가입"
        )
        recommendations.append(
            "⚠️ 리스크: 인지 능력은 있으나 거동이 불가한 경우 치매 보험 부지급"
        )
        recommendations.append(
            "💡 즉시 조치: 중대한 파킨슨병 진단비 특약 추가 가입 필수"
        )
    elif has_dementia and has_parkinsons:
        recommendations.append(
            "✅ 최적 융합 설계: 치매 + 파킨슨 모두 보장"
        )
        recommendations.append(
            f"✅ 총 보장액: {dementia_benefit + parkinsons_benefit:,}원"
        )
    elif not has_dementia and not has_parkinsons:
        recommendations.append(
            "🚨 긴급: 치매 및 파킨슨 보장 전무"
        )
        recommendations.append(
            "💡 치매 진단비 3,000만원 + 파킨슨병 진단비 2,000만원 즉시 가입 필요"
        )
    
    return {
        "current_coverage": {
            "dementia_benefit": dementia_benefit,
            "parkinsons_benefit": parkinsons_benefit,
            "total_benefit": dementia_benefit + parkinsons_benefit
        },
        "gap_analysis": gap_analysis,
        "critical_gap": critical_gap,
        "recommendations": recommendations,
        "alert_message": "⚠️ 보장 공백: 파킨슨병 특약 미가입" if critical_gap else "✅ 융합 설계 완료"
    }


# ══════════════════════════════════════════════════════════════════════════════
# [4] 알츠하이머/혈관성 치매/외상성 치매 연쇄 고리 시각화
# ══════════════════════════════════════════════════════════════════════════════

def visualize_dementia_chain() -> Dict[str, Any]:
    """
    알츠하이머, 혈관성 치매, 외상성 치매의 연쇄 고리 시각화
    
    Returns:
        dict: 연쇄 고리 데이터
    """
    chain = {
        "alzheimers_pathway": {
            "name": "알츠하이머 경로",
            "trigger": "노화, 유전, 아밀로이드 베타 축적",
            "progression": [
                {
                    "stage": "1단계: 경도 인지 장애 (MCI)",
                    "symptoms": "기억력 저하, 일상생활 가능",
                    "duration": "2~5년",
                    "coverage": "치매 보험 부지급 (진단 기준 미충족)"
                },
                {
                    "stage": "2단계: 초기 알츠하이머 (F00)",
                    "symptoms": "단기 기억 상실, 일상생활 일부 도움 필요",
                    "duration": "3~7년",
                    "coverage": "✅ 치매 진단비 지급"
                },
                {
                    "stage": "3단계: 중기 알츠하이머",
                    "symptoms": "장기 기억 상실, 전적 도움 필요",
                    "duration": "2~10년",
                    "coverage": "✅ 치매 진단비 + 장기요양 연금 전환"
                },
                {
                    "stage": "4단계: 말기 알츠하이머",
                    "symptoms": "의사소통 불가, 와상 상태",
                    "duration": "1~3년",
                    "coverage": "✅ 치매 진단비 + 종신보험 선지급 (80%)"
                }
            ],
            "total_duration": "8~25년",
            "prevention": "레카네맙(Lecanemab) 신약 (연간 3,000만원)"
        },
        "vascular_dementia_pathway": {
            "name": "혈관성 치매 경로",
            "trigger": "뇌졸중, 고혈압, 당뇨",
            "progression": [
                {
                    "stage": "1단계: 뇌졸중 발생 (I63/I64)",
                    "symptoms": "마비, 언어 장애",
                    "duration": "즉시",
                    "coverage": "✅ 뇌졸중 진단비 지급"
                },
                {
                    "stage": "2단계: 뇌졸중 후 인지 장애",
                    "symptoms": "기억력 저하, 판단력 저하",
                    "duration": "6개월~2년",
                    "coverage": "치매 진단 기준 미충족 시 부지급"
                },
                {
                    "stage": "3단계: 혈관성 치매 (F01)",
                    "symptoms": "계단식 인지 저하, 운동 장애",
                    "duration": "2~10년",
                    "coverage": "✅ 치매 진단비 지급"
                },
                {
                    "stage": "4단계: 다발성 뇌경색 치매",
                    "symptoms": "중증 인지 및 운동 장애",
                    "duration": "1~5년",
                    "coverage": "✅ 치매 진단비 + 종신보험 선지급 (80%)"
                }
            ],
            "total_duration": "3~17년",
            "prevention": "뇌졸중 예방 (혈압 관리, 항혈전제)"
        },
        "traumatic_dementia_pathway": {
            "name": "외상성 치매 경로",
            "trigger": "두부 외상 (S06), 교통사고, 낙상",
            "progression": [
                {
                    "stage": "1단계: 두부 외상 (S06.5 경막하출혈 등)",
                    "symptoms": "의식 소실, 뇌손상",
                    "duration": "즉시",
                    "coverage": "✅ 후유장해 보험금 (장해율에 따라)"
                },
                {
                    "stage": "2단계: 외상 후 인지 장애",
                    "symptoms": "기억력 저하, 집중력 저하",
                    "duration": "6개월~5년",
                    "coverage": "치매 진단 기준 미충족 시 부지급"
                },
                {
                    "stage": "3단계: 외상성 치매 (F02)",
                    "symptoms": "진행성 인지 저하",
                    "duration": "5~15년",
                    "coverage": "✅ 치매 진단비 지급"
                },
                {
                    "stage": "4단계: 만성 외상성 뇌병증 (CTE)",
                    "symptoms": "중증 치매, 운동 장애",
                    "duration": "1~10년",
                    "coverage": "✅ 치매 진단비 + 종신보험 선지급 (80%)"
                }
            ],
            "total_duration": "6~30년",
            "prevention": "두부 보호 (헬멧 착용, 낙상 예방)"
        },
        "convergence_point": {
            "title": "3대 치매 경로의 수렴점",
            "description": "알츠하이머, 혈관성 치매, 외상성 치매는 모두 최종적으로 중증 치매로 수렴하며, "
                          "이때 필요한 것은 '마르지 않는 재원'입니다. 연금 LTC 전환이 최후의 보루입니다.",
            "final_stage": {
                "name": "중증 치매 (공통 종착점)",
                "required_resources": [
                    "월 간병비: 400만원 × 10년 = 4억 8,000만원",
                    "가족 가처분 소득: 월 250만원 × 10년 = 3억원",
                    "총 필요 금액: 7억 8,000만원"
                ],
                "insurance_solutions": [
                    "치매 진단비: 3,000만원 (초기 비용)",
                    "종신보험 선지급: 8,000만원~1억 6,000만원 (중기 비용)",
                    "연금 LTC 전환: 월 400만원 × 10년 = 4억 8,000만원 (장기 비용)",
                    "총 확보 가능 금액: 5억 8,000만원~6억 6,000만원"
                ]
            }
        }
    }
    
    return chain


# ══════════════════════════════════════════════════════════════════════════════
# [5] 통합 간병/연금 프로토콜 실행
# ══════════════════════════════════════════════════════════════════════════════

def execute_caregiver_pension_protocol(
    daily_caregiver_benefit: int,
    monthly_pension: int,
    monthly_caregiving_cost: int,
    current_coverage: Dict[str, Any]
) -> Dict[str, Any]:
    """
    간병/연금 통합 프로토콜 실행
    
    Args:
        daily_caregiver_benefit: 간병인 보험 일당
        monthly_pension: 월 연금액
        monthly_caregiving_cost: 월 간병비
        current_coverage: 현재 보장 정보
    
    Returns:
        dict: 통합 분석 결과
    """
    # 1. 간병인 보험 공백 분석
    caregiver_gap = analyze_caregiver_insurance_gap(
        daily_benefit=daily_caregiver_benefit,
        monthly_caregiving_cost=monthly_caregiving_cost
    )
    
    # 2. 연금 LTC 전환 시뮬레이션
    pension_ltc = simulate_pension_ltc_conversion(
        monthly_pension=monthly_pension,
        monthly_caregiving_cost=monthly_caregiving_cost
    )
    
    # 3. 치매/파킨슨 융합 설계
    dementia_parkinsons = analyze_dementia_parkinsons_fusion(
        current_coverage=current_coverage
    )
    
    # 4. 치매 연쇄 고리
    dementia_chain = visualize_dementia_chain()
    
    # 5. 최종 권고사항
    final_recommendations = []
    
    # 간병인 보험 공백 대응
    if caregiver_gap["gap_cost"] > 0:
        final_recommendations.append(
            f"⚠️ 간병인 보험 공백 {caregiver_gap['gap_period_months']}개월: "
            f"{caregiver_gap['gap_cost']:,}원 추가 진단비 확보 필요"
        )
    
    # 연금 LTC 자급자족 여부
    if pension_ltc["self_sufficiency"]:
        final_recommendations.append(
            f"✅ 연금 LTC 자급자족 성공: 월 {pension_ltc['ltc_monthly_benefit']:,}원으로 "
            f"10년간 {pension_ltc['ltc_total_benefit']:,}원 확보"
        )
    else:
        final_recommendations.append(
            f"⚠️ 연금 LTC 부족: 월 연금액 증액 필요 "
            f"(현재 {monthly_pension:,}원 → 권장 {int(monthly_caregiving_cost / 2.0):,}원)"
        )
    
    # 치매/파킨슨 융합 설계
    if dementia_parkinsons["critical_gap"]:
        final_recommendations.append(
            "⚠️ 파킨슨병 특약 미가입: 운동 장해 시 보장 공백 발생"
        )
    
    final_recommendations.extend([
        "📊 3대 치매 경로: 알츠하이머 → 혈관성 치매 → 외상성 치매 모두 중증 치매로 수렴",
        "💡 최후의 보루: 연금 LTC 전환 (월 400만원 × 10년 = 4억 8,000만원)"
    ])
    
    return {
        "caregiver_insurance_gap": caregiver_gap,
        "pension_ltc_conversion": pension_ltc,
        "dementia_parkinsons_fusion": dementia_parkinsons,
        "dementia_chain": dementia_chain,
        "final_recommendations": final_recommendations,
        "protocol_status": "완료"
    }
