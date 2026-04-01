"""
hq_trinity_income_loss_engine.py — 트리니티 가처분 소득 결손 엔진
[GP-STEP3] Goldkey AI Masters 2026

목적: 뇌졸중 발병 후 가족의 가처분 소득(Disposable Income) 결손액 계산 및
      간병비 블랙홀 시뮬레이션을 통한 생존 자산 필요성 증명

핵심 공식:
Total Gap = (Monthly Caregiving + Monthly Living Cost) × 24 - Diagnosis Benefit

핵심 기능:
1. 가처분 소득 결손액 계산 (간병비 + 생활비 - 진단비)
2. 간병비 블랙홀 시뮬레이션 (진단비 5천만 원 → 1년 내 증발)
3. 무소득 기간 현금 흐름 분석 (24개월 시뮬레이션)
4. 종신보험 선지급 필요액 역산
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta


# ══════════════════════════════════════════════════════════════════════════════
# [1] 트리니티 가처분 소득 결손 공식
# ══════════════════════════════════════════════════════════════════════════════

def calculate_disposable_income_gap(
    monthly_caregiving_cost: int = 4000000,  # 전문 간병비 월 400만 원
    monthly_living_cost: int = 2500000,      # 가족 생활비 월 250만 원
    diagnosis_benefit: int = 50000000,       # 진단비 5,000만 원
    simulation_months: int = 24              # 시뮬레이션 기간 24개월
) -> Dict[str, Any]:
    """
    트리니티 가처분 소득 결손액 계산
    
    Args:
        monthly_caregiving_cost: 월 간병비 (원)
        monthly_living_cost: 월 생활비 (원)
        diagnosis_benefit: 진단비 (원)
        simulation_months: 시뮬레이션 기간 (개월)
    
    Returns:
        dict: {
            "total_gap": -60000000,
            "caregiving_total": 96000000,
            "living_total": 60000000,
            "diagnosis_benefit": 50000000,
            "monthly_breakdown": [...],
            "blackhole_month": 12,
            "alert_message": "..."
        }
    """
    # 총 필요 금액
    caregiving_total = monthly_caregiving_cost * simulation_months
    living_total = monthly_living_cost * simulation_months
    total_required = caregiving_total + living_total
    
    # 가처분 소득 결손액 (마이너스 = 부족)
    total_gap = diagnosis_benefit - total_required
    
    # 월별 현금 흐름 시뮬레이션
    monthly_breakdown = []
    remaining_diagnosis = diagnosis_benefit
    cumulative_deficit = 0
    blackhole_month = None
    
    for month in range(1, simulation_months + 1):
        monthly_expense = monthly_caregiving_cost + monthly_living_cost
        remaining_diagnosis -= monthly_expense
        
        if remaining_diagnosis < 0 and blackhole_month is None:
            blackhole_month = month
        
        cumulative_deficit = min(0, remaining_diagnosis)
        
        monthly_breakdown.append({
            "month": month,
            "caregiving_cost": monthly_caregiving_cost,
            "living_cost": monthly_living_cost,
            "total_expense": monthly_expense,
            "remaining_diagnosis": max(0, remaining_diagnosis),
            "cumulative_deficit": abs(cumulative_deficit),
            "status": "safe" if remaining_diagnosis >= 0 else "deficit"
        })
    
    # 경고 메시지
    if total_gap < 0:
        alert_message = f"""
⚠️ **가처분 소득 결손 경고 (Disposable Income Deficit Alert)**

진단비 {diagnosis_benefit:,}원으로는 {simulation_months}개월을 버틸 수 없습니다.

**필요 금액:**
- 간병비: {monthly_caregiving_cost:,}원 × {simulation_months}개월 = {caregiving_total:,}원
- 생활비: {monthly_living_cost:,}원 × {simulation_months}개월 = {living_total:,}원
- **총 필요: {total_required:,}원**

**현재 보장:**
- 진단비: {diagnosis_benefit:,}원

**부족액: {abs(total_gap):,}원**

진단비는 {blackhole_month}개월 만에 증발하고,
남은 {simulation_months - blackhole_month}개월 동안 가족의 생활비는 **마이너스 {abs(total_gap):,}원**이 됩니다.
"""
    else:
        alert_message = f"✅ 진단비 {diagnosis_benefit:,}원으로 {simulation_months}개월 생활 가능 (여유: {total_gap:,}원)"
    
    return {
        "total_gap": total_gap,
        "caregiving_total": caregiving_total,
        "living_total": living_total,
        "total_required": total_required,
        "diagnosis_benefit": diagnosis_benefit,
        "monthly_breakdown": monthly_breakdown,
        "blackhole_month": blackhole_month,
        "simulation_months": simulation_months,
        "alert_message": alert_message
    }


# ══════════════════════════════════════════════════════════════════════════════
# [2] 간병비 블랙홀 시뮬레이션 (진단비 증발 과정 시각화)
# ══════════════════════════════════════════════════════════════════════════════

def simulate_caregiving_blackhole(
    diagnosis_benefit: int = 50000000,
    monthly_caregiving_cost: int = 4000000
) -> Dict[str, Any]:
    """
    간병비 블랙홀 시뮬레이션 (진단비가 간병비로 증발하는 과정)
    
    Args:
        diagnosis_benefit: 진단비 (원)
        monthly_caregiving_cost: 월 간병비 (원)
    
    Returns:
        dict: {
            "depletion_months": 12,
            "monthly_drain": [...],
            "visualization": "..."
        }
    """
    remaining = diagnosis_benefit
    monthly_drain = []
    
    month = 0
    while remaining > 0:
        month += 1
        remaining -= monthly_caregiving_cost
        
        monthly_drain.append({
            "month": month,
            "caregiving_cost": monthly_caregiving_cost,
            "remaining": max(0, remaining),
            "depletion_rate": ((diagnosis_benefit - max(0, remaining)) / diagnosis_benefit) * 100
        })
    
    depletion_months = month
    
    # 시각화 텍스트
    visualization = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
간병비 블랙홀 시뮬레이션 (Caregiving Blackhole Simulation)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

진단비: {diagnosis_benefit:,}원
월 간병비: {monthly_caregiving_cost:,}원

"""
    
    for data in monthly_drain[:6]:  # 처음 6개월만 표시
        bar_length = int(data["depletion_rate"] / 2)
        bar = "█" * bar_length
        visualization += f"{data['month']:2d}개월: {data['remaining']:>12,}원 남음 [{bar}] {data['depletion_rate']:.1f}%\n"
    
    visualization += f"""
...

{depletion_months}개월: 0원 남음 [██████████████████████████████████████████████████] 100.0%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 결론: 진단비 {diagnosis_benefit:,}원은 간병비로 인해 {depletion_months}개월 만에 증발합니다.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    return {
        "depletion_months": depletion_months,
        "monthly_drain": monthly_drain,
        "visualization": visualization
    }


# ══════════════════════════════════════════════════════════════════════════════
# [3] 종신보험 선지급 필요액 역산
# ══════════════════════════════════════════════════════════════════════════════

def calculate_required_life_insurance_acceleration(
    total_gap: int,
    diagnosis_benefit: int = 50000000
) -> Dict[str, Any]:
    """
    가처분 소득 결손액을 메우기 위한 종신보험 선지급 필요액 역산
    
    Args:
        total_gap: 가처분 소득 결손액 (마이너스 값)
        diagnosis_benefit: 현재 진단비 (원)
    
    Returns:
        dict: {
            "required_acceleration": 60000000,
            "life_insurance_death_benefit": 120000000,
            "acceleration_rate_50": 60000000,
            "acceleration_rate_80": 96000000,
            "recommendation": "..."
        }
    """
    # 부족액 (절댓값)
    deficit = abs(total_gap) if total_gap < 0 else 0
    
    # 필요한 선지급액 (부족액 + 안전 마진 20%)
    required_acceleration = int(deficit * 1.2)
    
    # 종신보험 사망 보험금 역산 (50% 선지급 기준)
    life_insurance_death_benefit_50 = required_acceleration * 2
    
    # 종신보험 사망 보험금 역산 (80% 선지급 기준)
    life_insurance_death_benefit_80 = int(required_acceleration / 0.8)
    
    # 50% 선지급 시 금액
    acceleration_rate_50 = int(life_insurance_death_benefit_50 * 0.5)
    
    # 80% 선지급 시 금액
    acceleration_rate_80 = int(life_insurance_death_benefit_80 * 0.8)
    
    # 권고사항
    recommendation = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
종신보험 선지급 필요액 역산 (Life Insurance Acceleration Required)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**현재 상황:**
- 진단비: {diagnosis_benefit:,}원
- 부족액: {deficit:,}원
- 필요 선지급액 (안전 마진 20% 포함): {required_acceleration:,}원

**솔루션 A: 50% 선지급 기준**
- 종신보험 사망 보험금: {life_insurance_death_benefit_50:,}원
- 선지급 금액 (50%): {acceleration_rate_50:,}원
- 총 확보 금액: {diagnosis_benefit + acceleration_rate_50:,}원

**솔루션 B: 80% 선지급 기준**
- 종신보험 사망 보험금: {life_insurance_death_benefit_80:,}원
- 선지급 금액 (80%): {acceleration_rate_80:,}원
- 총 확보 금액: {diagnosis_benefit + acceleration_rate_80:,}원

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 권고사항
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

종신보험 사망 보험금 {life_insurance_death_benefit_50:,}원 이상 가입 필수.
질병장해 50% 선지급 특약으로 {acceleration_rate_50:,}원 확보 시,
진단비 {diagnosis_benefit:,}원과 합쳐 총 {diagnosis_benefit + acceleration_rate_50:,}원으로
가족의 생활비를 24개월 이상 방어할 수 있습니다.

**사망 보험금은 죽어서 주는 위로금이 아니라,
가족의 가처분 소득을 지켜내는 '생존 엔진'입니다.**
"""
    
    return {
        "deficit": deficit,
        "required_acceleration": required_acceleration,
        "life_insurance_death_benefit_50": life_insurance_death_benefit_50,
        "life_insurance_death_benefit_80": life_insurance_death_benefit_80,
        "acceleration_rate_50": acceleration_rate_50,
        "acceleration_rate_80": acceleration_rate_80,
        "total_coverage_50": diagnosis_benefit + acceleration_rate_50,
        "total_coverage_80": diagnosis_benefit + acceleration_rate_80,
        "recommendation": recommendation
    }


# ══════════════════════════════════════════════════════════════════════════════
# [4] 전문가 클로징 스크립트 생성
# ══════════════════════════════════════════════════════════════════════════════

def generate_trinity_closing_script(
    gap_result: Dict[str, Any],
    acceleration_result: Dict[str, Any],
    customer_name: str = "사장님"
) -> str:
    """
    트리니티 가처분 소득 결손 분석 기반 전문가 클로징 스크립트
    
    Args:
        gap_result: calculate_disposable_income_gap() 반환값
        acceleration_result: calculate_required_life_insurance_acceleration() 반환값
        customer_name: 고객 호칭
    
    Returns:
        str: 클로징 스크립트
    """
    deficit = acceleration_result["deficit"]
    diagnosis_benefit = gap_result["diagnosis_benefit"]
    required_acceleration = acceleration_result["required_acceleration"]
    blackhole_month = gap_result["blackhole_month"]
    
    script = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
전문가 클로징 스크립트 (Trinity Disposable Income Defense)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{customer_name}, 진단비 {diagnosis_benefit:,}원은 간병인 앞에서는 {blackhole_month}개월도 못 버팁니다.

**현실을 직시하십시오.**

- 전문 간병비: 월 400만 원 × 24개월 = 9,600만 원
- 가족 생활비: 월 250만 원 × 24개월 = 6,000만 원
- **총 필요 금액: 1억 5,600만 원**

**현재 보장:**
- 진단비: {diagnosis_benefit:,}원

**부족액: {deficit:,}원**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 솔루션: 돈의 용도를 분리하십시오
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**진단비 {diagnosis_benefit:,}원 → 간병비 전용**
- 전문 간병인 고용
- 재활 치료비
- 의료비

**종신보험 선지급 {required_acceleration:,}원 → 생활비 전용**
- 사모님과 아이들 생활비
- 주거비 (월세/관리비)
- 교육비

**이것이 트리니티 가처분 소득 방어 프로토콜입니다.**

진단비로 간병비를 내고 나면, 사모님과 아이들 생활비는 누가 줍니까?
제가 설계한 플랜은 간병비와 생활비를 **동시에** 책임집니다.
"""
    
    return script.strip()


# ══════════════════════════════════════════════════════════════════════════════
# [5] 차트 데이터 생성 (UI 시각화용)
# ══════════════════════════════════════════════════════════════════════════════

def generate_income_loss_chart_data(
    gap_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    가처분 소득 결손 차트 데이터 생성 (UI 시각화용)
    
    Args:
        gap_result: calculate_disposable_income_gap() 반환값
    
    Returns:
        dict: {
            "left_chart": {...},  # 진단비 수직 낙하 차트
            "right_chart": {...}  # 종신보험 선지급 방어 차트
        }
    """
    monthly_breakdown = gap_result["monthly_breakdown"]
    
    # 왼쪽 차트: 진단비 수직 낙하
    left_chart = {
        "title": "진단비 증발 과정 (Diagnosis Benefit Depletion)",
        "x_axis": "개월 (Month)",
        "y_axis": "잔액 (원)",
        "data": [
            {"month": item["month"], "remaining": item["remaining_diagnosis"]}
            for item in monthly_breakdown
        ],
        "color": "red",
        "description": "진단비가 간병비로 인해 급격히 수직 낙하하여 0원에 수렴하는 모습"
    }
    
    # 오른쪽 차트: 종신보험 선지급 방어
    # (실제 데이터는 acceleration_result 필요, 여기서는 구조만 정의)
    right_chart = {
        "title": "종신보험 선지급 방어 (Life Insurance Acceleration Defense)",
        "x_axis": "개월 (Month)",
        "y_axis": "잔액 (원)",
        "data": [],  # 실제 구현 시 acceleration_result 기반 계산
        "color": "green",
        "description": "종신보험 선지급금이 투입되어 가처분 소득(생활비) 라인을 안전하게 방어하는 모습"
    }
    
    return {
        "left_chart": left_chart,
        "right_chart": right_chart,
        "visualization_instructions": """
차트 시각화 가이드:

**왼쪽 차트 (진단비 증발):**
- 붉은색 급강하 라인
- Y축 0원 지점에 붉은 점선 (위험선)
- 블랙홀 지점(진단비 소진 시점)에 경고 아이콘

**오른쪽 차트 (종신보험 방어):**
- 초록색 안정 라인
- Y축 생활비 필요선에 초록 점선 (안전선)
- Safety Net 영역 표시
"""
    }
