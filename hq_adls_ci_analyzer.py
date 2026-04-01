"""
hq_adls_ci_analyzer.py — CI(중대한) 뇌졸중 및 ADLs 25% 판정 프로토콜
[GP-STEP15-B] Goldkey AI Masters 2026

목적: CI 보험의 '중대한'이라는 수식어 뒤에 숨겨진 높은 지급 문턱(ADLs 25%)을 수치로 폭로하고,
      일반 뇌졸중(진단 중심) vs 중대한 뇌졸중(장해 중심)의 지급 확률 피라미드를 시각화

핵심 개념:
- ADLs(Activities of Daily Living): 일상생활 동작 5대 항목
- CI(Critical Illness) 보험: 중대한 질병 보험 (장해율 25% 이상 필요)
- 회복의 역설: 뇌졸중 진단 후 지팡이 없이 걷게 되는 순간, CI 보험금은 0원이 됨

핵심 기능:
1. ADLs 5대 항목 장해율 정밀 계산
2. CI 보험 지급 문턱(25%) 시뮬레이션
3. 일반 뇌졸중 vs CI 뇌졸중 지급 확률 비교
4. 회복의 역설 스크립트 생성
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal


# ══════════════════════════════════════════════════════════════════════════════
# [1] ADLs 5대 항목 상세 분류 및 장해율 계산
# ══════════════════════════════════════════════════════════════════════════════

# ADLs 5대 항목 장해율 기준
ADLS_CRITERIA = {
    "mobility": {
        "name": "이동하기",
        "description": "휠체어 사용 및 타인 부축 여부",
        "levels": {
            "independent": {
                "description": "스스로 걷기 가능 (지팡이 사용 가능)",
                "disability_rate": 0
            },
            "cane_required": {
                "description": "지팡이 필수 (타인 부축 불필요)",
                "disability_rate": 10
            },
            "assistance_required": {
                "description": "타인 부축 필요 (실내 이동)",
                "disability_rate": 25
            },
            "wheelchair_partial": {
                "description": "휠체어 사용 (일부 자력 이동 가능)",
                "disability_rate": 30
            },
            "wheelchair_full": {
                "description": "휠체어 전적 의존 (타인 도움 필수)",
                "disability_rate": 40
            }
        }
    },
    "eating": {
        "name": "음식물 섭취",
        "description": "튜브 영양 및 수저 사용 불가 여부",
        "levels": {
            "independent": {
                "description": "스스로 식사 가능",
                "disability_rate": 0
            },
            "utensil_difficulty": {
                "description": "수저 사용 어려움 (손떨림, 흘림)",
                "disability_rate": 5
            },
            "assistance_required": {
                "description": "타인이 음식을 입에 넣어줘야 함",
                "disability_rate": 15
            },
            "tube_feeding": {
                "description": "튜브 영양 (비위관, 위루관)",
                "disability_rate": 20
            }
        }
    },
    "toileting": {
        "name": "배변/배뇨",
        "description": "기저귀 착용 및 화장실 이용 타인 도움 여부",
        "levels": {
            "independent": {
                "description": "스스로 화장실 이용 가능",
                "disability_rate": 0
            },
            "assistance_required": {
                "description": "화장실 이동 시 타인 도움 필요",
                "disability_rate": 10
            },
            "diaper_partial": {
                "description": "기저귀 착용 (일부 자력 배변 가능)",
                "disability_rate": 15
            },
            "diaper_full": {
                "description": "기저귀 전적 의존 (배변 조절 불가)",
                "disability_rate": 20
            }
        }
    },
    "dressing": {
        "name": "옷 입고 벗기",
        "description": "스스로 탈의 가능 여부",
        "levels": {
            "independent": {
                "description": "스스로 옷 입고 벗기 가능",
                "disability_rate": 0
            },
            "partial_assistance": {
                "description": "단추, 지퍼 등 일부 도움 필요",
                "disability_rate": 5
            },
            "full_assistance": {
                "description": "타인이 전적으로 옷 입혀줘야 함",
                "disability_rate": 10
            }
        }
    },
    "bathing": {
        "name": "목욕하기",
        "description": "전신 목욕 타인 도움 여부",
        "levels": {
            "independent": {
                "description": "스스로 전신 목욕 가능",
                "disability_rate": 0
            },
            "partial_assistance": {
                "description": "등, 머리 감기 등 일부 도움 필요",
                "disability_rate": 5
            },
            "full_assistance": {
                "description": "타인이 전적으로 목욕시켜줘야 함",
                "disability_rate": 10
            }
        }
    }
}


def calculate_adls_disability_rate(
    mobility_level: str,
    eating_level: str,
    toileting_level: str,
    dressing_level: str,
    bathing_level: str
) -> Dict[str, Any]:
    """
    ADLs 5대 항목 장해율 정밀 계산
    
    Args:
        mobility_level: 이동하기 수준 (예: "wheelchair_full")
        eating_level: 음식물 섭취 수준 (예: "independent")
        toileting_level: 배변/배뇨 수준 (예: "diaper_partial")
        dressing_level: 옷 입고 벗기 수준 (예: "partial_assistance")
        bathing_level: 목욕하기 수준 (예: "full_assistance")
    
    Returns:
        dict: {
            "total_disability_rate": 70,
            "ci_eligible": True,
            "breakdown": {...},
            "alert_message": "..."
        }
    """
    breakdown = {
        "mobility": {
            "name": ADLS_CRITERIA["mobility"]["name"],
            "level": mobility_level,
            "description": ADLS_CRITERIA["mobility"]["levels"][mobility_level]["description"],
            "disability_rate": ADLS_CRITERIA["mobility"]["levels"][mobility_level]["disability_rate"]
        },
        "eating": {
            "name": ADLS_CRITERIA["eating"]["name"],
            "level": eating_level,
            "description": ADLS_CRITERIA["eating"]["levels"][eating_level]["description"],
            "disability_rate": ADLS_CRITERIA["eating"]["levels"][eating_level]["disability_rate"]
        },
        "toileting": {
            "name": ADLS_CRITERIA["toileting"]["name"],
            "level": toileting_level,
            "description": ADLS_CRITERIA["toileting"]["levels"][toileting_level]["description"],
            "disability_rate": ADLS_CRITERIA["toileting"]["levels"][toileting_level]["disability_rate"]
        },
        "dressing": {
            "name": ADLS_CRITERIA["dressing"]["name"],
            "level": dressing_level,
            "description": ADLS_CRITERIA["dressing"]["levels"][dressing_level]["description"],
            "disability_rate": ADLS_CRITERIA["dressing"]["levels"][dressing_level]["disability_rate"]
        },
        "bathing": {
            "name": ADLS_CRITERIA["bathing"]["name"],
            "level": bathing_level,
            "description": ADLS_CRITERIA["bathing"]["levels"][bathing_level]["description"],
            "disability_rate": ADLS_CRITERIA["bathing"]["levels"][bathing_level]["disability_rate"]
        }
    }
    
    # 총 장해율 계산
    total_disability_rate = sum([item["disability_rate"] for item in breakdown.values()])
    
    # CI 보험 지급 대상 여부 (25% 이상)
    ci_eligible = total_disability_rate >= 25
    
    # 경고 메시지 생성
    if total_disability_rate < 25:
        alert_message = f"⚠️ CI 보험 부지급: 장해율 {total_disability_rate}% (25% 미만). 일반 뇌졸중 진단비만 지급됩니다."
        recovery_paradox = "회복의 역설: 지팡이 없이 걷게 되는 순간, CI 보험금은 0원이 됩니다."
    elif total_disability_rate < 50:
        alert_message = f"✅ CI 보험 지급 대상: 장해율 {total_disability_rate}% (25% 이상). 그러나 50% 미만으로 일부 보험사는 감액 지급할 수 있습니다."
        recovery_paradox = ""
    else:
        alert_message = f"✅ CI 보험 확정 지급: 장해율 {total_disability_rate}% (50% 이상). 중대한 뇌졸중으로 확정됩니다."
        recovery_paradox = ""
    
    return {
        "total_disability_rate": total_disability_rate,
        "ci_eligible": ci_eligible,
        "ci_threshold": 25,
        "breakdown": breakdown,
        "alert_message": alert_message,
        "recovery_paradox": recovery_paradox
    }


# ══════════════════════════════════════════════════════════════════════════════
# [2] CI 보험 지급 문턱(25%) 시뮬레이션
# ══════════════════════════════════════════════════════════════════════════════

def simulate_ci_threshold_scenarios() -> List[Dict[str, Any]]:
    """
    CI 보험 25% 문턱 시나리오 시뮬레이션
    
    Returns:
        list: 다양한 장해 시나리오별 CI 지급 여부
    """
    scenarios = [
        {
            "scenario_name": "시나리오 1: 지팡이 보행 (경증 회복)",
            "mobility": "cane_required",
            "eating": "independent",
            "toileting": "independent",
            "dressing": "independent",
            "bathing": "independent",
            "expected_result": "부지급 (10% < 25%)"
        },
        {
            "scenario_name": "시나리오 2: 타인 부축 필요 (중등도)",
            "mobility": "assistance_required",
            "eating": "independent",
            "toileting": "independent",
            "dressing": "independent",
            "bathing": "independent",
            "expected_result": "지급 (25% = 25%)"
        },
        {
            "scenario_name": "시나리오 3: 휠체어 + 식사 도움 (중증)",
            "mobility": "wheelchair_full",
            "eating": "assistance_required",
            "toileting": "diaper_partial",
            "dressing": "full_assistance",
            "bathing": "full_assistance",
            "expected_result": "확정 지급 (90% > 50%)"
        },
        {
            "scenario_name": "시나리오 4: 경계선 케이스 (24%)",
            "mobility": "cane_required",
            "eating": "utensil_difficulty",
            "toileting": "independent",
            "dressing": "partial_assistance",
            "bathing": "partial_assistance",
            "expected_result": "부지급 (24% < 25%)"
        },
        {
            "scenario_name": "시나리오 5: 경계선 케이스 (26%)",
            "mobility": "assistance_required",
            "eating": "independent",
            "toileting": "independent",
            "dressing": "independent",
            "bathing": "partial_assistance",
            "expected_result": "지급 (26% > 25%)"
        }
    ]
    
    results = []
    for scenario in scenarios:
        calc_result = calculate_adls_disability_rate(
            mobility_level=scenario["mobility"],
            eating_level=scenario["eating"],
            toileting_level=scenario["toileting"],
            dressing_level=scenario["dressing"],
            bathing_level=scenario["bathing"]
        )
        
        results.append({
            "scenario_name": scenario["scenario_name"],
            "total_disability_rate": calc_result["total_disability_rate"],
            "ci_eligible": calc_result["ci_eligible"],
            "expected_result": scenario["expected_result"],
            "alert_message": calc_result["alert_message"],
            "recovery_paradox": calc_result["recovery_paradox"]
        })
    
    return results


# ══════════════════════════════════════════════════════════════════════════════
# [3] 일반 뇌졸중 vs CI 뇌졸중 지급 확률 피라미드
# ══════════════════════════════════════════════════════════════════════════════

def generate_stroke_payment_pyramid() -> Dict[str, Any]:
    """
    일반 뇌졸중(진단 중심) vs 중대한 뇌졸중(장해 중심) 지급 확률 피라미드
    
    Returns:
        dict: 지급 확률 피라미드 데이터
    """
    pyramid = {
        "general_stroke": {
            "name": "일반 뇌졸중 (진단 중심)",
            "coverage_type": "진단비",
            "trigger": "뇌졸중 진단 즉시",
            "payment_probability": 0.95,  # 95% 지급 확률
            "average_benefit": 30000000,  # 평균 3,000만원
            "conditions": [
                "뇌혈관 MRI/CT 확인",
                "신경학적 증상 확인",
                "전문의 진단서"
            ],
            "advantages": [
                "진단 즉시 지급",
                "장해 정도 무관",
                "회복 후에도 지급 유지"
            ],
            "disadvantages": [
                "보험료 상대적 고가",
                "일부 보험사 I64 면책"
            ]
        },
        "ci_stroke": {
            "name": "중대한 뇌졸중 (장해 중심, CI)",
            "coverage_type": "중대한 질병 진단비",
            "trigger": "뇌졸중 진단 + 장해율 25% 이상",
            "payment_probability": 0.35,  # 35% 지급 확률
            "average_benefit": 50000000,  # 평균 5,000만원
            "conditions": [
                "뇌졸중 진단",
                "ADLs 장해율 25% 이상",
                "진단 후 일정 기간(30~90일) 경과",
                "장해 상태 지속 확인"
            ],
            "advantages": [
                "보험료 저렴 (일반 뇌졸중 대비 50~70%)",
                "보험금 고액 (5,000만원 이상)"
            ],
            "disadvantages": [
                "지급 문턱 높음 (25%)",
                "회복 시 부지급 (회복의 역설)",
                "대기 기간 존재 (30~90일)"
            ]
        },
        "payment_gap": {
            "description": "일반 뇌졸중 환자 중 CI 보험 지급 대상 비율",
            "general_stroke_patients": 100,
            "ci_eligible_patients": 35,
            "gap_percentage": 65,
            "gap_explanation": "뇌졸중 환자 100명 중 65명은 CI 보험금을 받지 못합니다. (장해율 25% 미만)"
        },
        "wall_of_25_percent": {
            "title": "The Wall of 25% (25%의 벽)",
            "description": "CI 보험의 지급 문턱. 이 벽을 넘지 못하면 보험금은 0원입니다.",
            "examples": [
                "지팡이 보행 가능 → 장해율 10% → 부지급",
                "타인 부축 필요 → 장해율 25% → 지급",
                "휠체어 사용 → 장해율 40% → 확정 지급"
            ]
        }
    }
    
    return pyramid


# ══════════════════════════════════════════════════════════════════════════════
# [4] 회복의 역설 스크립트 생성
# ══════════════════════════════════════════════════════════════════════════════

def generate_recovery_paradox_script(
    patient_name: str = "고객님",
    diagnosis_benefit_general: int = 30000000,
    diagnosis_benefit_ci: int = 50000000
) -> str:
    """
    회복의 역설 스크립트 생성
    
    Args:
        patient_name: 환자 이름
        diagnosis_benefit_general: 일반 뇌졸중 진단비
        diagnosis_benefit_ci: CI 뇌졸중 진단비
    
    Returns:
        str: 회복의 역설 설명 스크립트
    """
    script = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🛡️ [회복의 역설] CI(중대한) 뇌졸중 보험의 숨겨진 함정
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{patient_name}께서 뇌졸중 진단을 받으셨습니다.

[상황 1] 일반 뇌졸중 보험 가입 시
✅ 진단 즉시 {diagnosis_benefit_general:,}원 지급
✅ 재활 치료 후 지팡이 보행 가능 → 보험금 유지
✅ 완전 회복 → 보험금 유지

[상황 2] CI(중대한) 뇌졸중 보험만 가입 시
⏳ 진단 후 30~90일 대기
⏳ 장해율 측정 (ADLs 5대 항목)

  → 장해율 10% (지팡이 보행 가능)
     ❌ 부지급 (25% 미만)
     💸 보험금 0원

  → 장해율 25% (타인 부축 필요)
     ✅ 지급 ({diagnosis_benefit_ci:,}원)
     
  → 장해율 40% (휠체어 사용)
     ✅ 확정 지급 ({diagnosis_benefit_ci:,}원)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 회복의 역설 (The Recovery Paradox)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"재활 치료로 지팡이 없이 걷게 되는 순간,
 CI 보험금 {diagnosis_benefit_ci:,}원은 0원이 됩니다."

이것이 CI(중대한) 보험의 실체입니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 전문가 권고사항
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 일반 뇌졸중 진단비 (3,000만원 이상) 필수 가입
2. CI 보험은 보험료 절감용 보조 수단으로만 활용
3. 두 가지를 혼합하여 설계하는 것이 최선의 전략

예시:
- 일반 뇌졸중 진단비: 3,000만원 (확정 지급)
- CI 뇌졸중 진단비: 2,000만원 (보험료 절감)
→ 총 보장: 5,000만원 (경증 시 3,000만원, 중증 시 5,000만원)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    return script.strip()


# ══════════════════════════════════════════════════════════════════════════════
# [5] CI 담보 감사 엔진
# ══════════════════════════════════════════════════════════════════════════════

def audit_ci_coverage(
    current_coverage: Dict[str, Any]
) -> Dict[str, Any]:
    """
    현재 가입된 보험의 CI 담보 감사
    
    Args:
        current_coverage: {
            "general_stroke_benefit": 30000000,
            "ci_stroke_benefit": 50000000,
            "has_general_stroke": True,
            "has_ci_stroke": True
        }
    
    Returns:
        dict: 감사 결과 및 권고사항
    """
    general_benefit = current_coverage.get("general_stroke_benefit", 0)
    ci_benefit = current_coverage.get("ci_stroke_benefit", 0)
    has_general = current_coverage.get("has_general_stroke", False)
    has_ci = current_coverage.get("has_ci_stroke", False)
    
    audit_result = {
        "current_coverage": {
            "general_stroke_benefit": general_benefit,
            "ci_stroke_benefit": ci_benefit,
            "total_benefit_max": general_benefit + ci_benefit,
            "total_benefit_min": general_benefit if has_general else 0
        },
        "risk_assessment": {},
        "recommendations": []
    }
    
    # 리스크 평가
    if not has_general and has_ci:
        audit_result["risk_assessment"] = {
            "risk_level": "critical",
            "description": "CI 보험만 가입. 회복의 역설 리스크 극대화.",
            "payment_probability": 0.35,
            "expected_benefit": ci_benefit * 0.35
        }
        audit_result["recommendations"] = [
            "⚠️ 긴급: 일반 뇌졸중 진단비 3,000만원 이상 즉시 추가 가입 필요",
            "CI 보험만으로는 65%의 뇌졸중 환자가 보험금을 받지 못합니다.",
            "지팡이 보행 가능 시 보험금 0원 리스크 존재"
        ]
    elif has_general and not has_ci:
        audit_result["risk_assessment"] = {
            "risk_level": "low",
            "description": "일반 뇌졸중 보험 가입. 안정적 보장.",
            "payment_probability": 0.95,
            "expected_benefit": general_benefit * 0.95
        }
        audit_result["recommendations"] = [
            "✅ 안정적 보장 구조",
            "보험료 절감을 원하시면 CI 보험 추가 고려 가능",
            f"현재 보장액 {general_benefit:,}원이 충분한지 검토 필요"
        ]
    elif has_general and has_ci:
        audit_result["risk_assessment"] = {
            "risk_level": "optimal",
            "description": "일반 + CI 혼합 설계. 최적 구조.",
            "payment_probability_min": 0.95,
            "payment_probability_max": 1.0,
            "expected_benefit_min": general_benefit,
            "expected_benefit_max": general_benefit + ci_benefit
        }
        audit_result["recommendations"] = [
            "✅ 최적 보장 구조",
            f"경증 회복 시: {general_benefit:,}원 지급",
            f"중증 장해 시: {general_benefit + ci_benefit:,}원 지급",
            "회복의 역설 리스크 최소화"
        ]
    else:
        audit_result["risk_assessment"] = {
            "risk_level": "critical",
            "description": "뇌졸중 보장 없음. 즉시 가입 필요.",
            "payment_probability": 0,
            "expected_benefit": 0
        }
        audit_result["recommendations"] = [
            "🚨 긴급: 뇌졸중 보장 전무",
            "일반 뇌졸중 진단비 3,000만원 이상 즉시 가입 필요",
            "뇌졸중 발생 시 치료비 3,800만원 자비 부담 리스크"
        ]
    
    return audit_result
