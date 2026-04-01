"""
hq_life_insurance_acceleration.py — 종신보험 생존 자산 전환(Acceleration) 엔진
[GP-STEP3-B] Goldkey AI Masters 2026

목적: 사망 보험금을 질병·장해 발생 시 생존 중 선지급받아
      가족의 가처분 소득을 방어하는 '생존 엔진' 전환 로직

핵심 개념:
"사망 보험금은 죽어서 주는 위로금이 아니라,
 가족의 가처분 소득을 지켜내는 '생존 엔진'이다."

핵심 기능:
1. 종신보험 사망 보험금 → 질병장해 선지급 전환 (50%/80%)
2. 선지급 후 잔여 사망 보험금 계산
3. 가처분 소득 방어 시뮬레이션
4. 최적 선지급 비율 추천
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal


# ══════════════════════════════════════════════════════════════════════════════
# [1] 종신보험 선지급 전환 로직
# ══════════════════════════════════════════════════════════════════════════════

ACCELERATION_RATES = {
    "50%": {
        "rate": 0.50,
        "name": "질병장해 50% 선지급",
        "description": "사망 보험금의 50%를 질병·장해 발생 시 생존 중 선지급",
        "trigger_conditions": [
            "뇌졸중(I60~I69) 진단 확정",
            "심근경색(I21~I22) 진단 확정",
            "암(C00~C97) 진단 확정",
            "장해율 50% 이상"
        ]
    },
    "80%": {
        "rate": 0.80,
        "name": "질병장해 80% 선지급",
        "description": "사망 보험금의 80%를 질병·장해 발생 시 생존 중 선지급",
        "trigger_conditions": [
            "뇌졸중(I60~I69) 진단 확정",
            "심근경색(I21~I22) 진단 확정",
            "암(C00~C97) 진단 확정",
            "장해율 80% 이상"
        ]
    }
}


def calculate_life_insurance_acceleration(
    death_benefit: int = 100000000,  # 사망 보험금 1억 원
    acceleration_rate: str = "50%",   # 선지급 비율 (50% 또는 80%)
    diagnosis_benefit: int = 50000000  # 기존 진단비
) -> Dict[str, Any]:
    """
    종신보험 사망 보험금 → 질병장해 선지급 전환 계산
    
    Args:
        death_benefit: 사망 보험금 (원)
        acceleration_rate: 선지급 비율 ("50%" 또는 "80%")
        diagnosis_benefit: 기존 진단비 (원)
    
    Returns:
        dict: {
            "death_benefit": 100000000,
            "acceleration_rate": "50%",
            "acceleration_amount": 50000000,
            "remaining_death_benefit": 50000000,
            "total_living_benefit": 100000000,
            "benefit_breakdown": {...},
            "alert_message": "..."
        }
    """
    # 선지급 비율 정보
    rate_info = ACCELERATION_RATES.get(acceleration_rate, ACCELERATION_RATES["50%"])
    rate_value = rate_info["rate"]
    
    # 선지급 금액
    acceleration_amount = int(death_benefit * rate_value)
    
    # 선지급 후 잔여 사망 보험금
    remaining_death_benefit = death_benefit - acceleration_amount
    
    # 총 생존 급부 (진단비 + 선지급)
    total_living_benefit = diagnosis_benefit + acceleration_amount
    
    # 급부 분해
    benefit_breakdown = {
        "diagnosis_benefit": {
            "amount": diagnosis_benefit,
            "purpose": "간병비 전용",
            "coverage_months": int(diagnosis_benefit / 4000000)  # 월 400만 원 간병비 기준
        },
        "acceleration_benefit": {
            "amount": acceleration_amount,
            "purpose": "생활비 전용",
            "coverage_months": int(acceleration_amount / 2500000)  # 월 250만 원 생활비 기준
        },
        "total_living_benefit": {
            "amount": total_living_benefit,
            "purpose": "간병비 + 생활비",
            "coverage_months": int(diagnosis_benefit / 4000000) + int(acceleration_amount / 2500000)
        },
        "remaining_death_benefit": {
            "amount": remaining_death_benefit,
            "purpose": "사망 시 유족 보장"
        }
    }
    
    # 경고 메시지
    alert_message = f"""
✅ **종신보험 생존 자산 전환 (Life Insurance Acceleration)**

**사망 보험금 재배치:**
- 원래 사망 보험금: {death_benefit:,}원 (사망 시에만 지급)
- 선지급 비율: {acceleration_rate} ({rate_info['name']})
- 선지급 금액: {acceleration_amount:,}원 (생존 중 지급)
- 잔여 사망 보험금: {remaining_death_benefit:,}원

**생존 급부 총액:**
- 진단비: {diagnosis_benefit:,}원 (간병비 전용)
- 선지급: {acceleration_amount:,}원 (생활비 전용)
- **총 {total_living_benefit:,}원 확보**

**보장 기간:**
- 간병비 ({diagnosis_benefit:,}원 ÷ 월 400만 원): {benefit_breakdown['diagnosis_benefit']['coverage_months']}개월
- 생활비 ({acceleration_amount:,}원 ÷ 월 250만 원): {benefit_breakdown['acceleration_benefit']['coverage_months']}개월

**핵심 메시지:**
사망 보험금 {death_benefit:,}원을 죽어서 받는 것이 아니라,
생존 중 {acceleration_amount:,}원을 선지급받아 가족의 생활비를 지킵니다.
"""
    
    return {
        "death_benefit": death_benefit,
        "acceleration_rate": acceleration_rate,
        "acceleration_rate_value": rate_value,
        "acceleration_amount": acceleration_amount,
        "remaining_death_benefit": remaining_death_benefit,
        "total_living_benefit": total_living_benefit,
        "benefit_breakdown": benefit_breakdown,
        "trigger_conditions": rate_info["trigger_conditions"],
        "alert_message": alert_message
    }


# ══════════════════════════════════════════════════════════════════════════════
# [2] 가처분 소득 방어 시뮬레이션 (선지급 전후 비교)
# ══════════════════════════════════════════════════════════════════════════════

def simulate_disposable_income_defense(
    diagnosis_benefit: int = 50000000,
    acceleration_amount: int = 0,
    monthly_caregiving_cost: int = 4000000,
    monthly_living_cost: int = 2500000,
    simulation_months: int = 24
) -> Dict[str, Any]:
    """
    종신보험 선지급 전후 가처분 소득 방어 시뮬레이션
    
    Args:
        diagnosis_benefit: 진단비 (원)
        acceleration_amount: 선지급 금액 (원)
        monthly_caregiving_cost: 월 간병비 (원)
        monthly_living_cost: 월 생활비 (원)
        simulation_months: 시뮬레이션 기간 (개월)
    
    Returns:
        dict: {
            "without_acceleration": {...},
            "with_acceleration": {...},
            "comparison": {...}
        }
    """
    # [시나리오 A] 선지급 없이 진단비만 사용
    without_acceleration = {
        "total_available": diagnosis_benefit,
        "monthly_breakdown": [],
        "depletion_month": None,
        "final_deficit": 0
    }
    
    remaining_a = diagnosis_benefit
    for month in range(1, simulation_months + 1):
        monthly_expense = monthly_caregiving_cost + monthly_living_cost
        remaining_a -= monthly_expense
        
        if remaining_a < 0 and without_acceleration["depletion_month"] is None:
            without_acceleration["depletion_month"] = month
        
        without_acceleration["monthly_breakdown"].append({
            "month": month,
            "remaining": max(0, remaining_a),
            "deficit": abs(min(0, remaining_a))
        })
    
    without_acceleration["final_deficit"] = abs(min(0, remaining_a))
    
    # [시나리오 B] 선지급 포함 (진단비 = 간병비, 선지급 = 생활비)
    with_acceleration = {
        "total_available": diagnosis_benefit + acceleration_amount,
        "caregiving_fund": diagnosis_benefit,
        "living_fund": acceleration_amount,
        "monthly_breakdown": [],
        "depletion_month": None,
        "final_deficit": 0
    }
    
    remaining_caregiving = diagnosis_benefit
    remaining_living = acceleration_amount
    
    for month in range(1, simulation_months + 1):
        # 간병비는 간병 펀드에서 차감
        remaining_caregiving -= monthly_caregiving_cost
        
        # 생활비는 생활 펀드에서 차감
        remaining_living -= monthly_living_cost
        
        total_remaining = max(0, remaining_caregiving) + max(0, remaining_living)
        total_deficit = abs(min(0, remaining_caregiving)) + abs(min(0, remaining_living))
        
        if total_remaining == 0 and with_acceleration["depletion_month"] is None:
            with_acceleration["depletion_month"] = month
        
        with_acceleration["monthly_breakdown"].append({
            "month": month,
            "caregiving_remaining": max(0, remaining_caregiving),
            "living_remaining": max(0, remaining_living),
            "total_remaining": total_remaining,
            "deficit": total_deficit
        })
    
    with_acceleration["final_deficit"] = abs(min(0, remaining_caregiving)) + abs(min(0, remaining_living))
    
    # 비교 분석
    comparison = {
        "deficit_reduction": without_acceleration["final_deficit"] - with_acceleration["final_deficit"],
        "extended_months": (with_acceleration["depletion_month"] or simulation_months) - (without_acceleration["depletion_month"] or simulation_months),
        "safety_net_message": f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
가처분 소득 방어 비교 (Disposable Income Defense Comparison)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**[시나리오 A] 진단비만 사용 (선지급 없음)**
- 가용 금액: {diagnosis_benefit:,}원
- 소진 시점: {without_acceleration['depletion_month']}개월
- 최종 부족액: {without_acceleration['final_deficit']:,}원

**[시나리오 B] 진단비 + 선지급 (생존 엔진 가동)**
- 가용 금액: {diagnosis_benefit + acceleration_amount:,}원
  - 간병비 펀드: {diagnosis_benefit:,}원
  - 생활비 펀드: {acceleration_amount:,}원
- 소진 시점: {with_acceleration['depletion_month'] or '24개월 이상'}
- 최종 부족액: {with_acceleration['final_deficit']:,}원

**개선 효과:**
- 부족액 감소: {without_acceleration['final_deficit'] - with_acceleration['final_deficit']:,}원
- 보장 기간 연장: {(with_acceleration['depletion_month'] or simulation_months) - (without_acceleration['depletion_month'] or 0)}개월

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 결론: 종신보험 선지급은 가족의 생활비를 지키는 Safety Net입니다.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    }
    
    return {
        "without_acceleration": without_acceleration,
        "with_acceleration": with_acceleration,
        "comparison": comparison
    }


# ══════════════════════════════════════════════════════════════════════════════
# [3] 최적 선지급 비율 추천
# ══════════════════════════════════════════════════════════════════════════════

def recommend_optimal_acceleration_rate(
    total_gap: int,
    death_benefit: int = 100000000,
    family_dependents: int = 3  # 부양 가족 수
) -> Dict[str, Any]:
    """
    가처분 소득 결손액 기반 최적 선지급 비율 추천
    
    Args:
        total_gap: 가처분 소득 결손액 (마이너스 값)
        death_benefit: 종신보험 사망 보험금 (원)
        family_dependents: 부양 가족 수
    
    Returns:
        dict: {
            "recommended_rate": "80%",
            "reason": "...",
            "alternative_rate": "50%"
        }
    """
    deficit = abs(total_gap) if total_gap < 0 else 0
    
    # 50% 선지급 시 확보 금액
    acceleration_50 = int(death_benefit * 0.5)
    
    # 80% 선지급 시 확보 금액
    acceleration_80 = int(death_benefit * 0.8)
    
    # 추천 로직
    if deficit > acceleration_50:
        recommended_rate = "80%"
        reason = f"""
부족액 {deficit:,}원을 메우기 위해서는 80% 선지급이 필요합니다.

- 50% 선지급: {acceleration_50:,}원 (부족액 대비 {int((acceleration_50/deficit)*100)}%)
- 80% 선지급: {acceleration_80:,}원 (부족액 대비 {int((acceleration_80/deficit)*100)}%)

부양 가족 {family_dependents}명의 생활비를 고려하면 80% 선지급이 적정합니다.
"""
        alternative_rate = "50%"
    else:
        recommended_rate = "50%"
        reason = f"""
부족액 {deficit:,}원은 50% 선지급으로 충분히 커버 가능합니다.

- 50% 선지급: {acceleration_50:,}원 (부족액 대비 {int((acceleration_50/deficit)*100)}%)
- 잔여 사망 보험금: {int(death_benefit * 0.5):,}원 (유족 보장 유지)

50% 선지급으로 생활비를 방어하면서도 유족 보장을 50% 유지할 수 있습니다.
"""
        alternative_rate = "80%"
    
    return {
        "recommended_rate": recommended_rate,
        "reason": reason,
        "alternative_rate": alternative_rate,
        "acceleration_50": acceleration_50,
        "acceleration_80": acceleration_80,
        "deficit": deficit
    }


# ══════════════════════════════════════════════════════════════════════════════
# [4] 전문가 클로징 스크립트 생성
# ══════════════════════════════════════════════════════════════════════════════

def generate_acceleration_closing_script(
    acceleration_result: Dict[str, Any],
    customer_name: str = "사장님"
) -> str:
    """
    종신보험 선지급 전환 기반 전문가 클로징 스크립트
    
    Args:
        acceleration_result: calculate_life_insurance_acceleration() 반환값
        customer_name: 고객 호칭
    
    Returns:
        str: 클로징 스크립트
    """
    death_benefit = acceleration_result["death_benefit"]
    acceleration_amount = acceleration_result["acceleration_amount"]
    acceleration_rate = acceleration_result["acceleration_rate"]
    total_living_benefit = acceleration_result["total_living_benefit"]
    
    script = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
전문가 클로징 스크립트 (Life Insurance Acceleration)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{customer_name}, 종신보험 사망 보험금 {death_benefit:,}원을 죽어서 받으시겠습니까?
아니면 살아서 받으시겠습니까?

**제가 설계한 플랜은 이렇습니다.**

종신보험 사망 보험금 {death_benefit:,}원에
질병장해 {acceleration_rate} 선지급 특약을 추가하면,

**뇌졸중 진단 확정 시:**
- 사망하지 않아도 생존 중 {acceleration_amount:,}원 선지급
- 이 돈으로 사모님과 아이들 생활비 {int(acceleration_amount/2500000)}개월 확보
- 간병비는 진단비로, 생활비는 선지급으로 **용도 분리**

**사망 시:**
- 잔여 사망 보험금 {acceleration_result['remaining_death_benefit']:,}원 유족에게 지급

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 핵심 메시지
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**사망 보험금은 죽어서 주는 위로금이 아니라,
가족의 가처분 소득을 지켜내는 '생존 엔진'입니다.**

{customer_name}, 보험은 죽어서 받는 것이 아닙니다.
살아서 가족을 지키는 것입니다.
"""
    
    return script.strip()


# ══════════════════════════════════════════════════════════════════════════════
# [5] 차트 데이터 생성 (UI 시각화용)
# ══════════════════════════════════════════════════════════════════════════════

def generate_acceleration_chart_data(
    simulation_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    종신보험 선지급 전후 비교 차트 데이터 생성
    
    Args:
        simulation_result: simulate_disposable_income_defense() 반환값
    
    Returns:
        dict: {
            "left_chart": {...},   # 선지급 없음 (수직 낙하)
            "right_chart": {...}   # 선지급 있음 (안전 방어)
        }
    """
    without = simulation_result["without_acceleration"]["monthly_breakdown"]
    with_acc = simulation_result["with_acceleration"]["monthly_breakdown"]
    
    left_chart = {
        "title": "진단비만 사용 (선지급 없음)",
        "x_axis": "개월",
        "y_axis": "잔액 (원)",
        "data": [
            {"month": item["month"], "remaining": item["remaining"]}
            for item in without
        ],
        "color": "red",
        "danger_zone": True
    }
    
    right_chart = {
        "title": "진단비 + 선지급 (생존 엔진 가동)",
        "x_axis": "개월",
        "y_axis": "잔액 (원)",
        "data": [
            {
                "month": item["month"],
                "caregiving_remaining": item["caregiving_remaining"],
                "living_remaining": item["living_remaining"],
                "total_remaining": item["total_remaining"]
            }
            for item in with_acc
        ],
        "color": "green",
        "safety_zone": True
    }
    
    return {
        "left_chart": left_chart,
        "right_chart": right_chart,
        "visualization_instructions": """
**왼쪽 차트 (위험):**
- 붉은색 급강하 라인
- 진단비가 간병비+생활비로 빠르게 소진
- 위험 구역(Danger Zone) 표시

**오른쪽 차트 (안전):**
- 초록색 2단 라인 (간병비 펀드 + 생활비 펀드)
- 용도 분리로 안정적 방어
- 안전 구역(Safety Zone) 표시
"""
    }
