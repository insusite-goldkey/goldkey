"""
hq_adls_judgment_engine.py — ADLs 25% 판정 로직 및 CI 보험금 지급 기준 엔진
[GP-STEP2] Goldkey AI Masters 2026

목적: Activities of Daily Living (일상생활 수행능력) 5대 항목 점수 계산 및
      CI 보험 지급 기준(25% 이상) 충족 여부 판정

핵심 기능:
1. 5대 ADLs 항목별 장해 점수 계산 (이동/식사/배변/탈의/목욕)
2. CI 보험금 지급 기준 25% 충족 여부 실시간 판정
3. 회복의 역설 시뮬레이션 (지팡이 없이 걷는 순간 → 보험금 0원)
4. 장해 판정 타임라인 (6개월 vs 18개월 시간차 분석)
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta


# ══════════════════════════════════════════════════════════════════════════════
# [1] ADLs 5대 항목 정의 및 점수 체계
# ══════════════════════════════════════════════════════════════════════════════

ADLS_5_CATEGORIES = {
    "mobility": {
        "name": "이동 능력 (Mobility)",
        "description": "침대에서 일어나 방 밖으로 나가는 동작",
        "levels": {
            "independent": {"score": 0, "label": "완전 자립", "description": "도움 없이 이동 가능"},
            "assistive_device": {"score": 15, "label": "보조기구 필요", "description": "지팡이, 워커 등 필요"},
            "partial_assistance": {"score": 20, "label": "부분 도움", "description": "타인의 부분적 도움 필요"},
            "full_assistance": {"score": 25, "label": "완전 도움", "description": "타인의 완전한 도움 필요"}
        }
    },
    "eating": {
        "name": "식사 능력 (Eating)",
        "description": "음식을 입으로 가져가 삼키는 동작",
        "levels": {
            "independent": {"score": 0, "label": "완전 자립", "description": "도움 없이 식사 가능"},
            "assistive_device": {"score": 15, "label": "보조기구 필요", "description": "특수 수저, 빨대 등 필요"},
            "partial_assistance": {"score": 20, "label": "부분 도움", "description": "음식 자르기 등 도움 필요"},
            "full_assistance": {"score": 25, "label": "완전 도움", "description": "타인이 먹여줘야 함"}
        }
    },
    "toileting": {
        "name": "배변·배뇨 능력 (Toileting)",
        "description": "화장실 사용 및 위생 처리",
        "levels": {
            "independent": {"score": 0, "label": "완전 자립", "description": "도움 없이 화장실 사용 가능"},
            "assistive_device": {"score": 15, "label": "보조기구 필요", "description": "변기 손잡이 등 필요"},
            "partial_assistance": {"score": 20, "label": "부분 도움", "description": "옷 벗기 등 도움 필요"},
            "full_assistance": {"score": 25, "label": "완전 도움", "description": "기저귀 착용 또는 전적 도움"}
        }
    },
    "dressing": {
        "name": "옷 입고 벗기 (Dressing)",
        "description": "상하의 착탈의 및 단추 채우기",
        "levels": {
            "independent": {"score": 0, "label": "완전 자립", "description": "도움 없이 착탈의 가능"},
            "assistive_device": {"score": 15, "label": "보조기구 필요", "description": "단추 보조기 등 필요"},
            "partial_assistance": {"score": 20, "label": "부분 도움", "description": "단추 채우기 등 도움 필요"},
            "full_assistance": {"score": 25, "label": "완전 도움", "description": "타인이 입혀줘야 함"}
        }
    },
    "bathing": {
        "name": "목욕 능력 (Bathing)",
        "description": "샤워 또는 목욕 수행",
        "levels": {
            "independent": {"score": 0, "label": "완전 자립", "description": "도움 없이 목욕 가능"},
            "assistive_device": {"score": 15, "label": "보조기구 필요", "description": "욕실 손잡이 등 필요"},
            "partial_assistance": {"score": 20, "label": "부분 도움", "description": "등 씻기 등 도움 필요"},
            "full_assistance": {"score": 25, "label": "완전 도움", "description": "타인이 씻겨줘야 함"}
        }
    }
}


# CI 보험금 지급 기준
CI_PAYMENT_THRESHOLD = 25  # 25% 이상 장해 시 지급
MAX_ADLS_SCORE = 125  # 5개 항목 × 25점 = 125점


# ══════════════════════════════════════════════════════════════════════════════
# [2] ADLs 점수 계산 및 CI 지급 판정
# ══════════════════════════════════════════════════════════════════════════════

def calculate_adls_score(
    mobility: str = "independent",
    eating: str = "independent",
    toileting: str = "independent",
    dressing: str = "independent",
    bathing: str = "independent"
) -> Dict[str, Any]:
    """
    ADLs 5대 항목 점수 계산 및 CI 보험금 지급 판정
    
    Args:
        mobility: 이동 능력 수준 (independent/assistive_device/partial_assistance/full_assistance)
        eating: 식사 능력 수준
        toileting: 배변 능력 수준
        dressing: 탈의 능력 수준
        bathing: 목욕 능력 수준
    
    Returns:
        dict: {
            "total_score": 60,
            "disability_percentage": 48.0,
            "ci_payment_eligible": True,
            "payment_amount": 50000000,
            "breakdown": {...},
            "alert_message": "...",
            "recovery_paradox_warning": "..."
        }
    """
    # 각 항목별 점수 추출
    scores = {
        "mobility": ADLS_5_CATEGORIES["mobility"]["levels"][mobility]["score"],
        "eating": ADLS_5_CATEGORIES["eating"]["levels"][eating]["score"],
        "toileting": ADLS_5_CATEGORIES["toileting"]["levels"][toileting]["score"],
        "dressing": ADLS_5_CATEGORIES["dressing"]["levels"][dressing]["score"],
        "bathing": ADLS_5_CATEGORIES["bathing"]["levels"][bathing]["score"]
    }
    
    total_score = sum(scores.values())
    disability_percentage = (total_score / MAX_ADLS_SCORE) * 100
    
    # CI 보험금 지급 여부 판정
    ci_payment_eligible = disability_percentage >= CI_PAYMENT_THRESHOLD
    
    # 지급 금액 계산 (예시: 진단비 5,000만 원 기준)
    diagnosis_benefit = 50000000
    payment_amount = diagnosis_benefit if ci_payment_eligible else 0
    
    # 회복의 역설 경고
    recovery_paradox_warning = ""
    if 20 <= disability_percentage < 25:
        recovery_paradox_warning = f"""
⚠️ **회복의 역설 (Recovery Paradox) 경고**

현재 장해율: {disability_percentage:.1f}% (CI 지급 기준 25% 미만)

**위험 시나리오:**
- 지팡이 없이 걷는 순간 → 이동 능력 점수 15점 → 0점
- 장해율 {disability_percentage:.1f}% → {disability_percentage - 12:.1f}%로 하락
- **CI 보험금 {diagnosis_benefit:,}원 → 0원**

**현실:**
- 재활 치료비: 월 300만 원 × 6개월 = 1,800만 원
- 간병비: 월 400만 원 × 6개월 = 2,400만 원
- 생활비: 월 250만 원 × 6개월 = 1,500만 원
- **총 필요 금액: 5,700만 원**

**결론:**
회복할수록 보험금을 못 받는 '통곡의 벽'에 직면합니다.
이것이 CI 보험의 치명적 맹점입니다.
"""
    
    # 경고 메시지
    if ci_payment_eligible:
        alert_message = f"✅ CI 보험금 지급 대상 (장해율 {disability_percentage:.1f}% ≥ 25%)"
    else:
        alert_message = f"⚠️ CI 보험금 부지급 (장해율 {disability_percentage:.1f}% < 25%)"
    
    # 항목별 상세 분석
    breakdown = {}
    for category, score in scores.items():
        category_data = ADLS_5_CATEGORIES[category]
        level_key = locals()[category]  # mobility, eating 등의 값
        level_data = category_data["levels"][level_key]
        
        breakdown[category] = {
            "name": category_data["name"],
            "level": level_data["label"],
            "score": score,
            "description": level_data["description"]
        }
    
    return {
        "total_score": total_score,
        "disability_percentage": round(disability_percentage, 1),
        "ci_payment_eligible": ci_payment_eligible,
        "payment_amount": payment_amount,
        "breakdown": breakdown,
        "alert_message": alert_message,
        "recovery_paradox_warning": recovery_paradox_warning
    }


# ══════════════════════════════════════════════════════════════════════════════
# [3] 장해 판정 타임라인 시뮬레이션 (6개월 vs 18개월)
# ══════════════════════════════════════════════════════════════════════════════

def simulate_disability_timeline(
    stroke_date: datetime,
    current_adls_score: int
) -> Dict[str, Any]:
    """
    뇌졸중 발병 후 장해 판정 타임라인 시뮬레이션
    
    Args:
        stroke_date: 뇌졸중 발병일
        current_adls_score: 현재 ADLs 총점
    
    Returns:
        dict: {
            "insurance_judgment_date": datetime (6개월 후),
            "national_disability_date": datetime (18개월 후),
            "gap_months": 12,
            "income_loss_during_gap": 30000000,
            "timeline_visualization": "..."
        }
    """
    # 보험사 판정 시점 (6개월 후)
    insurance_judgment_date = stroke_date + timedelta(days=180)
    
    # 국가 장애 판정 시점 (18개월 후)
    national_disability_date = stroke_date + timedelta(days=540)
    
    # 시간 격차 (개월)
    gap_months = 12
    
    # 격차 기간 동안 소득 손실 (월 250만 원 × 12개월)
    monthly_income = 2500000
    income_loss_during_gap = monthly_income * gap_months
    
    # 타임라인 시각화
    timeline_visualization = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
장해 판정 타임라인 (Disability Judgment Timeline)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 뇌졸중 발병일: {stroke_date.strftime('%Y-%m-%d')}
   ↓ (6개월 경과)
   
📋 보험사 CI 판정일: {insurance_judgment_date.strftime('%Y-%m-%d')}
   - 현재 ADLs 점수: {current_adls_score}점
   - 장해율: {(current_adls_score / MAX_ADLS_SCORE) * 100:.1f}%
   - CI 지급 여부: {'✅ 지급' if current_adls_score >= 31.25 else '❌ 부지급'}
   
   ↓ (12개월 무소득 기간)
   
🏛️ 국가 장애 판정일: {national_disability_date.strftime('%Y-%m-%d')}
   - 장애인복지법 기준 판정
   - 장애인 등록 가능 시점
   
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 무소득 기간 (Income Loss Gap)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

기간: {gap_months}개월
월 소득: {monthly_income:,}원
총 소득 손실: {income_loss_during_gap:,}원

**이 기간 동안 가족의 생활비는 누가 책임집니까?**
"""
    
    return {
        "stroke_date": stroke_date,
        "insurance_judgment_date": insurance_judgment_date,
        "national_disability_date": national_disability_date,
        "gap_months": gap_months,
        "income_loss_during_gap": income_loss_during_gap,
        "timeline_visualization": timeline_visualization
    }


# ══════════════════════════════════════════════════════════════════════════════
# [4] 전문가 클로징 스크립트 생성
# ══════════════════════════════════════════════════════════════════════════════

def generate_adls_closing_script(
    adls_result: Dict[str, Any],
    customer_name: str = "사장님"
) -> str:
    """
    ADLs 판정 결과 기반 전문가 클로징 스크립트 생성
    
    Args:
        adls_result: calculate_adls_score() 반환값
        customer_name: 고객 호칭
    
    Returns:
        str: 클로징 스크립트
    """
    disability_pct = adls_result["disability_percentage"]
    ci_eligible = adls_result["ci_payment_eligible"]
    
    if ci_eligible:
        script = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
전문가 클로징 스크립트 A (CI 보험금 지급 대상)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{customer_name}, 현재 장해율은 {disability_pct}%로 CI 보험금 지급 대상입니다.

**하지만 여기서 끝이 아닙니다.**

CI 보험금 5천만 원은 간병인 앞에서는 1년도 못 버팁니다.
- 전문 간병비: 월 400만 원 × 12개월 = 4,800만 원
- 남은 금액: 200만 원

**진단비로 간병비를 내고 나면, 사모님과 아이들 생활비는 누가 줍니까?**

제가 설계한 플랜은 진단비 5천만 원 + 종신보험 선지급 1억 원으로
간병비와 생활비를 **동시에** 책임집니다.
"""
    else:
        script = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
전문가 클로징 스크립트 B (CI 보험금 부지급 - 회복의 역설)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{customer_name}, 현재 장해율은 {disability_pct}%로 CI 보험금 지급 기준(25%)에 미달합니다.

**이것이 바로 '회복의 역설'입니다.**

재활 치료로 조금씩 좋아지는 순간, 보험금은 0원이 됩니다.
- 지팡이 없이 걷는 순간 → 이동 능력 점수 15점 감소
- 장해율 {disability_pct}% → 12.8% 하락
- **CI 보험금 5,000만 원 → 0원**

**하지만 현실은?**
- 재활 치료비: 월 300만 원 × 6개월 = 1,800만 원
- 간병비: 월 400만 원 × 6개월 = 2,400만 원
- 생활비: 월 250만 원 × 6개월 = 1,500만 원
- **총 필요 금액: 5,700만 원**

CI 보험은 '중환자'가 되어야 주지만,
제가 설계한 플랜은 '환자'만 되어도 가족의 생활비까지 책임집니다.
"""
    
    return script.strip()


# ══════════════════════════════════════════════════════════════════════════════
# [5] ADLs 체크리스트 데이터 (UI 렌더링용)
# ══════════════════════════════════════════════════════════════════════════════

def get_adls_checklist_data() -> Dict[str, Any]:
    """
    ADLs 체크리스트 UI 렌더링용 데이터 반환
    
    Returns:
        dict: {
            "categories": ADLS_5_CATEGORIES,
            "threshold": CI_PAYMENT_THRESHOLD,
            "max_score": MAX_ADLS_SCORE
        }
    """
    return {
        "categories": ADLS_5_CATEGORIES,
        "threshold": CI_PAYMENT_THRESHOLD,
        "max_score": MAX_ADLS_SCORE,
        "ui_instructions": """
ADLs 체크리스트 UI 구현 가이드:

1. 5대 항목별 라디오 버튼 또는 슬라이더 제공
2. 실시간 점수 합산 및 장해율(%) 표시
3. 25% 기준선을 붉은색 점선으로 시각화
4. 회복의 역설 경고 (20~25% 구간 진입 시 팝업)
5. 타임라인 차트 (6개월 vs 18개월 시간차)
"""
    }
