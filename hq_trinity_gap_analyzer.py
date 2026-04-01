"""
hq_trinity_gap_analyzer.py — 트리니티 가처분 소득 결손 및 자산 전환 프로토콜
[GP-STEP15-C] Goldkey AI Masters 2026

목적: 진단비가 간병비로 증발할 때 사라지는 '가족의 생활비'를 사망 보험금 선지급으로 방어

핵심 개념:
- 트리니티 결손(Trinity Gap): 간병비 + 치료비 + 가처분 소득 결손의 3중 재정 위기
- 간병비 블랙홀: 진단비가 간병비로 1년 내 소진되는 현상
- 종신보험 생존 자산 전환(Acceleration): 사망 담보를 질병장해 시 선지급하여 현금 흐름 확보

핵심 기능:
1. 트리니티 결손 시뮬레이션 (간병비 + 치료비 + 가처분 소득)
2. 종신보험 선지급 시뮬레이션 (50%/80% 장해 시 선지급)
3. 간병비 블랙홀 분석
4. 두부 외상성 장해(S코드) 연동
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal


# ══════════════════════════════════════════════════════════════════════════════
# [1] 트리니티 결손 시뮬레이션
# ══════════════════════════════════════════════════════════════════════════════

def calculate_trinity_gap(
    monthly_caregiving_cost: int,
    monthly_disposable_income: int,
    diagnosis_benefit: int,
    duration_months: int = 24
) -> Dict[str, Any]:
    """
    트리니티 결손 시뮬레이션
    
    수식:
    Total Gap = (Monthly Caregiving + Disposable Income) × Duration - Diagnosis Benefit
    
    Args:
        monthly_caregiving_cost: 월 간병비 (예: 4,000,000원)
        monthly_disposable_income: 월 가처분 소득 (예: 2,500,000원)
        diagnosis_benefit: 진단비 (예: 50,000,000원)
        duration_months: 기간 (개월, 기본값 24개월)
    
    Returns:
        dict: {
            "total_gap": 106000000,
            "caregiving_total": 96000000,
            "disposable_income_loss": 60000000,
            "diagnosis_benefit": 50000000,
            "gap_breakdown": {...}
        }
    """
    # 간병비 총액
    caregiving_total = monthly_caregiving_cost * duration_months
    
    # 가처분 소득 결손 총액
    disposable_income_loss = monthly_disposable_income * duration_months
    
    # 총 필요 금액
    total_required = caregiving_total + disposable_income_loss
    
    # 트리니티 결손 (부족분)
    total_gap = total_required - diagnosis_benefit
    
    # 월별 분석
    monthly_breakdown = []
    remaining_benefit = diagnosis_benefit
    
    for month in range(1, duration_months + 1):
        monthly_expense = monthly_caregiving_cost + monthly_disposable_income
        
        if remaining_benefit >= monthly_expense:
            remaining_benefit -= monthly_expense
            status = "진단비 충당"
        elif remaining_benefit > 0:
            deficit = monthly_expense - remaining_benefit
            remaining_benefit = 0
            status = f"부족 {deficit:,}원"
        else:
            status = f"전액 부족 {monthly_expense:,}원"
        
        monthly_breakdown.append({
            "month": month,
            "caregiving_cost": monthly_caregiving_cost,
            "disposable_income": monthly_disposable_income,
            "total_expense": monthly_expense,
            "remaining_benefit": max(0, remaining_benefit),
            "status": status
        })
    
    # 진단비 소진 시점
    depletion_month = 0
    cumulative = 0
    for month in range(1, duration_months + 1):
        cumulative += monthly_caregiving_cost + monthly_disposable_income
        if cumulative >= diagnosis_benefit:
            depletion_month = month
            break
    
    return {
        "total_gap": total_gap,
        "caregiving_total": caregiving_total,
        "disposable_income_loss": disposable_income_loss,
        "diagnosis_benefit": diagnosis_benefit,
        "total_required": total_required,
        "depletion_month": depletion_month,
        "monthly_breakdown": monthly_breakdown,
        "gap_breakdown": {
            "caregiving_cost": {
                "monthly": monthly_caregiving_cost,
                "total": caregiving_total,
                "percentage": round((caregiving_total / total_required) * 100, 1)
            },
            "disposable_income_loss": {
                "monthly": monthly_disposable_income,
                "total": disposable_income_loss,
                "percentage": round((disposable_income_loss / total_required) * 100, 1)
            }
        },
        "alert_message": f"⚠️ 트리니티 결손: {total_gap:,}원. 진단비는 {depletion_month}개월 내 소진됩니다."
    }


# ══════════════════════════════════════════════════════════════════════════════
# [2] 종신보험 생존 자산 전환 (Acceleration) 시뮬레이션
# ══════════════════════════════════════════════════════════════════════════════

def simulate_life_insurance_acceleration(
    death_benefit: int,
    disability_50_rate: float = 0.50,
    disability_80_rate: float = 0.80,
    trinity_gap: int = 0
) -> Dict[str, Any]:
    """
    종신보험 선지급 시뮬레이션
    
    Args:
        death_benefit: 사망 보험금 (예: 100,000,000원)
        disability_50_rate: 50% 장해 시 선지급 비율 (기본값 0.50)
        disability_80_rate: 80% 장해 시 선지급 비율 (기본값 0.80)
        trinity_gap: 트리니티 결손액 (예: 106,000,000원)
    
    Returns:
        dict: {
            "death_benefit": 100000000,
            "acceleration_50": 50000000,
            "acceleration_80": 80000000,
            "gap_coverage_50": "부족",
            "gap_coverage_80": "부족",
            "recommendations": [...]
        }
    """
    # 50% 장해 시 선지급액
    acceleration_50 = int(death_benefit * disability_50_rate)
    
    # 80% 장해 시 선지급액
    acceleration_80 = int(death_benefit * disability_80_rate)
    
    # 트리니티 결손 커버 여부
    gap_coverage_50 = "충분" if acceleration_50 >= trinity_gap else "부족"
    gap_coverage_80 = "충분" if acceleration_80 >= trinity_gap else "부족"
    
    # 부족분 계산
    shortage_50 = max(0, trinity_gap - acceleration_50)
    shortage_80 = max(0, trinity_gap - acceleration_80)
    
    # 권고사항 생성
    recommendations = []
    
    if trinity_gap == 0:
        recommendations.append("트리니티 결손 데이터가 없습니다. 먼저 결손 분석을 수행하세요.")
    else:
        if gap_coverage_50 == "부족":
            recommendations.append(
                f"⚠️ 50% 장해 시 부족: {shortage_50:,}원. "
                f"사망 보험금을 {int((trinity_gap / disability_50_rate)):,}원 이상으로 증액 필요."
            )
        else:
            recommendations.append(
                f"✅ 50% 장해 시 충분: {acceleration_50:,}원으로 트리니티 결손 {trinity_gap:,}원 커버 가능."
            )
        
        if gap_coverage_80 == "부족":
            recommendations.append(
                f"⚠️ 80% 장해 시 부족: {shortage_80:,}원. "
                f"사망 보험금을 {int((trinity_gap / disability_80_rate)):,}원 이상으로 증액 필요."
            )
        else:
            recommendations.append(
                f"✅ 80% 장해 시 충분: {acceleration_80:,}원으로 트리니티 결손 {trinity_gap:,}원 커버 가능."
            )
    
    # 최적 사망 보험금 계산
    optimal_death_benefit_50 = int(trinity_gap / disability_50_rate) if trinity_gap > 0 else 0
    optimal_death_benefit_80 = int(trinity_gap / disability_80_rate) if trinity_gap > 0 else 0
    
    return {
        "death_benefit": death_benefit,
        "acceleration_50": {
            "rate": disability_50_rate,
            "amount": acceleration_50,
            "gap_coverage": gap_coverage_50,
            "shortage": shortage_50
        },
        "acceleration_80": {
            "rate": disability_80_rate,
            "amount": acceleration_80,
            "gap_coverage": gap_coverage_80,
            "shortage": shortage_80
        },
        "trinity_gap": trinity_gap,
        "optimal_death_benefit": {
            "for_50_disability": optimal_death_benefit_50,
            "for_80_disability": optimal_death_benefit_80,
            "recommended": optimal_death_benefit_80  # 80% 기준 권장
        },
        "recommendations": recommendations
    }


# ══════════════════════════════════════════════════════════════════════════════
# [3] 간병비 블랙홀 분석
# ══════════════════════════════════════════════════════════════════════════════

def analyze_caregiving_blackhole(
    diagnosis_benefit: int,
    monthly_caregiving_cost: int,
    monthly_treatment_cost: int = 0
) -> Dict[str, Any]:
    """
    간병비 블랙홀 분석: 진단비가 간병비로 소진되는 시점 계산
    
    Args:
        diagnosis_benefit: 진단비 (예: 50,000,000원)
        monthly_caregiving_cost: 월 간병비 (예: 4,000,000원)
        monthly_treatment_cost: 월 치료비 (예: 500,000원)
    
    Returns:
        dict: {
            "depletion_month": 11,
            "monthly_expense": 4500000,
            "blackhole_description": "...",
            "timeline": [...]
        }
    """
    monthly_expense = monthly_caregiving_cost + monthly_treatment_cost
    
    # 진단비 소진 시점 (개월)
    depletion_month = int(diagnosis_benefit / monthly_expense)
    
    # 월별 타임라인
    timeline = []
    remaining_benefit = diagnosis_benefit
    
    for month in range(1, min(depletion_month + 3, 25)):  # 최대 24개월
        if remaining_benefit >= monthly_expense:
            remaining_benefit -= monthly_expense
            status = "진단비 충당"
        elif remaining_benefit > 0:
            deficit = monthly_expense - remaining_benefit
            remaining_benefit = 0
            status = f"부족 {deficit:,}원 (진단비 소진)"
        else:
            status = f"전액 자비 부담 {monthly_expense:,}원"
        
        timeline.append({
            "month": month,
            "caregiving_cost": monthly_caregiving_cost,
            "treatment_cost": monthly_treatment_cost,
            "total_expense": monthly_expense,
            "remaining_benefit": max(0, remaining_benefit),
            "status": status
        })
    
    blackhole_description = (
        f"진단비 {diagnosis_benefit:,}원은 월 간병비 {monthly_caregiving_cost:,}원 + "
        f"치료비 {monthly_treatment_cost:,}원으로 {depletion_month}개월 내 소진됩니다. "
        f"이후 모든 비용은 가족의 자비 부담으로 전환되며, 이때 가족의 가처분 소득이 전액 결손됩니다."
    )
    
    return {
        "depletion_month": depletion_month,
        "monthly_expense": monthly_expense,
        "diagnosis_benefit": diagnosis_benefit,
        "blackhole_description": blackhole_description,
        "timeline": timeline,
        "alert_message": f"⚠️ 간병비 블랙홀: 진단비는 {depletion_month}개월 후 소진됩니다."
    }


# ══════════════════════════════════════════════════════════════════════════════
# [4] 두부 외상성 장해 (S코드) 연동
# ══════════════════════════════════════════════════════════════════════════════

# 두부 외상성 장해 S코드 기준
TRAUMATIC_BRAIN_INJURY_CODES = {
    "S06.0": {
        "name": "뇌진탕",
        "disability_rate_range": "3~10%",
        "typical_disability": 5,
        "description": "의식 소실 동반 뇌진탕"
    },
    "S06.1": {
        "name": "외상성 뇌부종",
        "disability_rate_range": "10~30%",
        "typical_disability": 20,
        "description": "뇌부종으로 인한 신경학적 장해"
    },
    "S06.2": {
        "name": "미만성 뇌손상",
        "disability_rate_range": "30~70%",
        "typical_disability": 50,
        "description": "광범위한 뇌 손상"
    },
    "S06.3": {
        "name": "국소 뇌손상",
        "disability_rate_range": "20~50%",
        "typical_disability": 35,
        "description": "특정 부위 뇌 손상"
    },
    "S06.4": {
        "name": "경막외출혈",
        "disability_rate_range": "30~80%",
        "typical_disability": 55,
        "description": "경막 외 출혈로 인한 뇌압 상승"
    },
    "S06.5": {
        "name": "외상성 경막하출혈",
        "disability_rate_range": "40~90%",
        "typical_disability": 65,
        "description": "경막 하 출혈로 인한 심각한 뇌손상"
    },
    "S06.6": {
        "name": "외상성 지주막하출혈",
        "disability_rate_range": "30~80%",
        "typical_disability": 55,
        "description": "지주막 하 출혈"
    },
    "S06.7": {
        "name": "지속적 혼수를 동반한 두개내손상",
        "disability_rate_range": "80~100%",
        "typical_disability": 90,
        "description": "식물인간 상태 또는 중증 의식장애"
    },
    "S06.8": {
        "name": "기타 두개내손상",
        "disability_rate_range": "10~50%",
        "typical_disability": 30,
        "description": "기타 뇌손상"
    },
    "S06.9": {
        "name": "상세불명의 두개내손상",
        "disability_rate_range": "10~50%",
        "typical_disability": 30,
        "description": "상세불명의 뇌손상"
    }
}


def analyze_traumatic_brain_injury(
    s_code: str,
    current_coverage: Dict[str, Any]
) -> Dict[str, Any]:
    """
    두부 외상성 장해(S코드) 분석 및 보장 규모 확장
    
    Args:
        s_code: S코드 (예: "S06.5")
        current_coverage: 현재 보장 정보
    
    Returns:
        dict: {
            "s_code": "S06.5",
            "injury_name": "외상성 경막하출혈",
            "typical_disability": 65,
            "disability_range": "40~90%",
            "life_insurance_acceleration": {...},
            "recommendations": [...]
        }
    """
    if s_code not in TRAUMATIC_BRAIN_INJURY_CODES:
        return {
            "error": f"알 수 없는 S코드: {s_code}",
            "valid_codes": list(TRAUMATIC_BRAIN_INJURY_CODES.keys())
        }
    
    injury_data = TRAUMATIC_BRAIN_INJURY_CODES[s_code]
    typical_disability = injury_data["typical_disability"]
    
    # 현재 보장 분석
    death_benefit = current_coverage.get("death_benefit", 0)
    
    # 50% 및 80% 장해 시 선지급 가능 여부
    acceleration_possible_50 = typical_disability >= 50
    acceleration_possible_80 = typical_disability >= 80
    
    # 예상 선지급액
    if acceleration_possible_80:
        expected_acceleration = int(death_benefit * 0.80)
        acceleration_rate = "80%"
    elif acceleration_possible_50:
        expected_acceleration = int(death_benefit * 0.50)
        acceleration_rate = "50%"
    else:
        expected_acceleration = 0
        acceleration_rate = "선지급 불가"
    
    # 권고사항
    recommendations = []
    
    if typical_disability >= 80:
        recommendations.append(
            f"✅ 중증 장해 ({typical_disability}%): 종신보험 80% 선지급 가능 ({int(death_benefit * 0.80):,}원)"
        )
    elif typical_disability >= 50:
        recommendations.append(
            f"⚠️ 중등도 장해 ({typical_disability}%): 종신보험 50% 선지급 가능 ({int(death_benefit * 0.50):,}원)"
        )
    else:
        recommendations.append(
            f"⚠️ 경증 장해 ({typical_disability}%): 종신보험 선지급 불가. 진단비 및 후유장해 특약 의존"
        )
    
    if death_benefit < 100000000:
        recommendations.append(
            f"⚠️ 사망 보험금 부족: 현재 {death_benefit:,}원. 최소 1억원 이상 권장."
        )
    
    return {
        "s_code": s_code,
        "injury_name": injury_data["name"],
        "description": injury_data["description"],
        "typical_disability": typical_disability,
        "disability_range": injury_data["disability_rate_range"],
        "life_insurance_acceleration": {
            "death_benefit": death_benefit,
            "acceleration_possible_50": acceleration_possible_50,
            "acceleration_possible_80": acceleration_possible_80,
            "expected_acceleration": expected_acceleration,
            "acceleration_rate": acceleration_rate
        },
        "recommendations": recommendations
    }


# ══════════════════════════════════════════════════════════════════════════════
# [5] 통합 트리니티 프로토콜 실행
# ══════════════════════════════════════════════════════════════════════════════

def execute_trinity_protocol(
    monthly_caregiving_cost: int,
    monthly_disposable_income: int,
    diagnosis_benefit: int,
    death_benefit: int,
    duration_months: int = 24
) -> Dict[str, Any]:
    """
    트리니티 프로토콜 통합 실행
    
    Args:
        monthly_caregiving_cost: 월 간병비
        monthly_disposable_income: 월 가처분 소득
        diagnosis_benefit: 진단비
        death_benefit: 사망 보험금
        duration_months: 기간 (개월)
    
    Returns:
        dict: 통합 분석 결과
    """
    # 1. 트리니티 결손 계산
    trinity_gap_result = calculate_trinity_gap(
        monthly_caregiving_cost=monthly_caregiving_cost,
        monthly_disposable_income=monthly_disposable_income,
        diagnosis_benefit=diagnosis_benefit,
        duration_months=duration_months
    )
    
    # 2. 종신보험 선지급 시뮬레이션
    acceleration_result = simulate_life_insurance_acceleration(
        death_benefit=death_benefit,
        trinity_gap=trinity_gap_result["total_gap"]
    )
    
    # 3. 간병비 블랙홀 분석
    blackhole_result = analyze_caregiving_blackhole(
        diagnosis_benefit=diagnosis_benefit,
        monthly_caregiving_cost=monthly_caregiving_cost
    )
    
    # 4. 최종 권고사항
    final_recommendations = []
    
    if trinity_gap_result["total_gap"] > 0:
        final_recommendations.append(
            f"⚠️ 트리니티 결손 {trinity_gap_result['total_gap']:,}원 발생. "
            f"진단비만으로는 {trinity_gap_result['depletion_month']}개월 후 자비 부담 시작."
        )
    
    if acceleration_result["acceleration_80"]["gap_coverage"] == "부족":
        final_recommendations.append(
            f"⚠️ 종신보험 사망 보험금 증액 필요: "
            f"현재 {death_benefit:,}원 → 권장 {acceleration_result['optimal_death_benefit']['recommended']:,}원"
        )
    else:
        final_recommendations.append(
            f"✅ 종신보험 80% 선지급으로 트리니티 결손 커버 가능: "
            f"{acceleration_result['acceleration_80']['amount']:,}원"
        )
    
    final_recommendations.extend([
        f"📊 간병비 블랙홀: 진단비는 {blackhole_result['depletion_month']}개월 후 소진",
        f"💡 최후의 보루: 종신보험 선지급이 가족의 가처분 소득을 지킵니다."
    ])
    
    return {
        "trinity_gap": trinity_gap_result,
        "life_insurance_acceleration": acceleration_result,
        "caregiving_blackhole": blackhole_result,
        "final_recommendations": final_recommendations,
        "protocol_status": "완료"
    }
