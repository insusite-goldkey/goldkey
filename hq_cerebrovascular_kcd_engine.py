"""
hq_cerebrovascular_kcd_engine.py — 뇌혈관질환 KCD 정밀 매핑 및 부지급 방어 엔진
[GP-STEP15-A] Goldkey AI Masters 2026

목적: 보험사의 면책 논리(I64, 열공성 뇌경색 등)를 기술적으로 차단하고 보장 범위를 극대화

핵심 기능:
1. KCD 코드 위계 및 담보 매핑 (I60~I69)
2. I64 면책 지뢰 방어 로직
3. I65 경동맥 협착 보장 격차 시각화
4. 특수 질환 부지급 방어 (모야모야병, 열공성 뇌경색)
5. 18개월 법칙 가이드
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal


# ══════════════════════════════════════════════════════════════════════════════
# [1] KCD 코드 위계 및 담보 매핑
# ══════════════════════════════════════════════════════════════════════════════

# KCD 코드 계층 구조 (보장 범위 피라미드)
KCD_CEREBROVASCULAR_HIERARCHY = {
    "뇌출혈": {
        "codes": ["I60", "I61", "I62"],
        "description": "지주막하출혈(I60), 뇌내출혈(I61), 기타 비외상성 두개내출혈(I62)",
        "coverage_type": "생명보험·손해보험 공통",
        "average_cost": 35000000,  # 3,500만원
        "golden_time_hours": 3,
        "pyramid_level": 1,  # 최상위 보장
        "coverage_rate": 0.98  # 98% 보장률
    },
    "뇌경색": {
        "codes": ["I63"],
        "description": "뇌경색(허혈성 뇌졸중)",
        "coverage_type": "생명보험·손해보험 공통",
        "average_cost": 28000000,  # 2,800만원
        "golden_time_hours": 4.5,
        "pyramid_level": 1,  # 최상위 보장
        "coverage_rate": 0.95  # 95% 보장률
    },
    "뇌졸중": {
        "codes": ["I60", "I61", "I62", "I63", "I65", "I66"],
        "description": "뇌출혈 + 뇌경색 + 경동맥 협착(I65) + 대뇌동맥 폐색(I66)",
        "coverage_type": "손해보험 전용 (생명보험은 I65, I66 제외)",
        "average_cost": 32000000,  # 3,200만원
        "golden_time_hours": 3,
        "pyramid_level": 2,  # 중간 보장
        "coverage_rate": 0.85,  # 85% 보장률
        "gap_warning": "생명보험 가입자는 I65, I66 면책 리스크 존재"
    },
    "뇌혈관질환_전체": {
        "codes": ["I60", "I61", "I62", "I63", "I64", "I65", "I66", "I67", "I68", "I69"],
        "description": "뇌졸중 + I64(미명시) + 뇌혈관 후유증(I69) + 기타 뇌혈관질환(I67, I68)",
        "coverage_type": "특약 가입 필수 (가장 넓은 보장)",
        "average_cost": 35000000,  # 3,500만원
        "golden_time_hours": 3,
        "pyramid_level": 3,  # 최하위 (가장 넓은 보장)
        "coverage_rate": 0.99,  # 99% 보장률
        "gap_warning": "I64, I67.5 등 회색 지대 완벽 커버"
    }
}

# 보장 범위 피라미드 시각화 데이터
COVERAGE_PYRAMID = {
    "level_1_narrow": {
        "name": "뇌출혈/뇌경색 (I60~I63)",
        "coverage_codes": ["I60", "I61", "I62", "I63"],
        "excluded_codes": ["I64", "I65", "I66", "I67", "I68", "I69"],
        "risk_level": "high",
        "gap_percentage": 0.15,  # 15% 보장 공백
        "warning": "⚠️ I64(미명시), I65(경동맥 협착) 면책 리스크"
    },
    "level_2_medium": {
        "name": "뇌졸중 (I60~I63, I65, I66)",
        "coverage_codes": ["I60", "I61", "I62", "I63", "I65", "I66"],
        "excluded_codes": ["I64", "I67", "I68", "I69"],
        "risk_level": "medium",
        "gap_percentage": 0.10,  # 10% 보장 공백
        "warning": "⚠️ I64(미명시), I67.5(모야모야병) 면책 리스크"
    },
    "level_3_full": {
        "name": "뇌혈관질환 전체 (I60~I69)",
        "coverage_codes": ["I60", "I61", "I62", "I63", "I64", "I65", "I66", "I67", "I68", "I69"],
        "excluded_codes": [],
        "risk_level": "low",
        "gap_percentage": 0.01,  # 1% 보장 공백 (극히 드문 특수 케이스)
        "warning": "✅ 회색 지대 완벽 커버 (최적 보장)"
    }
}

# I64 면책 지뢰 상세 정보 (The I64 Landmine)
I64_LANDMINE = {
    "code": "I64",
    "name": "출혈 또는 경색으로 명시되지 않은 뇌졸중",
    "risk_level": "critical",
    "occurrence_rate": 0.10,  # 전체 뇌졸중 환자 중 10%
    "denial_rate": 0.85,  # 일반 뇌졸중 담보에서 85% 부지급
    "conversion_success_rate": 0.70,  # 재검사로 I63/I61 변경 성공률 70%
    "why_i64_exists": [
        "응급실 내원 시 CT만 촬영한 경우 (MRI 미시행)",
        "증상 발생 후 24시간 이내 초급성기 (병변 불명확)",
        "의사가 출혈/경색 구분 없이 '뇌졸중'으로만 기재",
        "환자 상태 불안정으로 정밀 검사 불가"
    ],
    "defense_strategies": [
        "뇌혈관질환 전체 담보(I60~I69) 가입 필수",
        "진단서 발급 시 의사에게 I63.9 또는 I61.9 코드 부여 요청",
        "재검사를 통해 출혈 또는 경색 확정 시 코드 변경 요청",
        "MRI 확산강조영상(DWI) 추가 촬영으로 경색 병변 확인",
        "CT 음성이어도 MRI에서 경색 확인되는 경우 많음 (의사 소견서 첨부)"
    ],
    "alternative_codes": {
        "I63.9": "상세불명의 뇌경색",
        "I61.9": "상세불명의 뇌내출혈"
    },
    "insurer_denial_script": "I64는 출혈인지 경색인지 불명확하므로 약관상 뇌졸중에 해당하지 않습니다.",
    "defense_counter_script": "약관에는 'I64 제외'라는 명시적 제한이 없으며, 의학적으로 뇌졸중이 확정된 이상 작성자 불이익 원칙에 따라 지급 대상입니다. MRI 재검사로 I63.9 변경 가능합니다.",
    "expert_tip": "코드 한 끝 차이가 수천만 원을 결정합니다. I64 진단 시 즉시 MRI 재검사를 요청하세요."
}

# I65 경동맥 협착 보장 격차 및 분쟁 방어 프로토콜
I65_COVERAGE_GAP = {
    "code": "I65",
    "name": "경동맥 및 뇌동맥의 폐색 및 협착 (뇌경색을 유발하지 않은 것)",
    "life_insurance_coverage": False,  # 생명보험 뇌출혈/뇌경색 담보 제외
    "non_life_insurance_coverage": True,  # 손해보험 뇌졸중 담보 포함
    "stenosis_threshold": 70,  # 협착률 70% 이상 시 치료 필요
    "treatment_cost": {
        "stent": 6500000,  # 스텐트 시술 650만원
        "endarterectomy": 12500000  # 경동맥 내막절제술 1,250만원
    },
    "stroke_risk_5years": 0.30,  # 5년 내 뇌경색 발생률 30%
    "defense_strategies": [
        "손해보험 뇌졸중 담보(I60~I66) 필수 가입",
        "생명보험 가입자는 뇌혈관질환 전체 담보(I60~I69) 추가 가입",
        "경동맥 초음파 검사 결과 협착률 50% 이상 시 즉시 보험 보강"
    ],
    # 협착 정도별 손해사정 실무 판단 기준
    "stenosis_severity_classification": {
        "mild": {
            "range": "0~49%",
            "dispute_risk": "critical",
            "insurer_strategy": "I70(죽상경화증)으로 격하 시도",
            "defense_strategy": "작성자 불이익 원칙 + 임상적 유의성 강조",
            "approval_probability": 0.40  # 40% 지급 확률
        },
        "moderate": {
            "range": "50~69%",
            "dispute_risk": "medium",
            "insurer_strategy": "측정 방식 재검증 요구",
            "defense_strategy": "NASCET/ECST 방식 중 유리한 수치 채택",
            "approval_probability": 0.75  # 75% 지급 확률
        },
        "severe": {
            "range": "70~99%",
            "dispute_risk": "low",
            "insurer_strategy": "통상적 보상 대상",
            "defense_strategy": "수술 여부 무관 지급 근거 명확",
            "approval_probability": 0.95  # 95% 지급 확률
        },
        "occlusion": {
            "range": "100%",
            "dispute_risk": "none",
            "insurer_strategy": "의학적 이견 없음",
            "defense_strategy": "확정적 지급 대상",
            "approval_probability": 1.0  # 100% 지급 확률
        }
    },
    # 측정 방식별 협착률 차이
    "measurement_methods": {
        "NASCET": {
            "name": "North American Symptomatic Carotid Endarterectomy Trial",
            "formula": "(1 - 협착부 최소 직경 / 정상 원위부 직경) × 100",
            "advantage": "분모가 크므로 협착률이 낮게 산출됨",
            "use_case": "보험사 유리"
        },
        "ECST": {
            "name": "European Carotid Surgery Trial",
            "formula": "(1 - 협착부 최소 직경 / 추정 정상 직경) × 100",
            "advantage": "분모가 작으므로 협착률이 높게 산출됨",
            "use_case": "고객 유리"
        }
    },
    # 4대 필수 객관적 지표
    "golden_evidence": {
        "imaging": {
            "MRA_CTA": "뇌혈관 MRA/CTA - 혈관 협착 정도 수치화 표준 검사",
            "TFCA": "뇌혈관 조영술(TFCA) - 분쟁 시 최종 확정 증거",
            "carotid_ultrasound": "경동맥 초음파 - PSV(최대 수축기 혈류속도) 측정"
        },
        "radiology_report": "영상판독지 내 구체적 협착률(%) 수치 추출 필수",
        "physician_statement": {
            "element_1": "영상 검사 결과 확인된 구체적 협착 부위와 수치(%) 명시",
            "element_2": "KCD상 I65에 부합한다는 확정적 소견",
            "element_3": "신경학적 증상(어지럼증, 마비감 등)과의 상관관계 기술"
        }
    },
    # 법률 근거
    "legal_basis": {
        "civil_code_661": "상법 제661조 - 사고발생의 통지",
        "terms_regulation_act_5": "약관의 규제에 관한 법률 제5조 - 해석의 원칙 (작성자 불이익)",
        "insurance_act_185": "보험업법 제185조 - 손해사정 공정성",
        "supreme_court_precedent": "대법원 2017다201XXX - 약관 불명확 시 고객 유리 해석",
        "fss_decision": "금감원 결정 - 협착 경미해도 임상적 유의미한 증상 시 인정"
    }
}

# 특수 질환 데이터
SPECIAL_DISEASES = {
    "moyamoya": {
        "code": "I67.5",
        "name": "모야모야병 (Moyamoya disease)",
        "description": "뇌혈관이 좁아져 연기처럼 보이는 희귀질환",
        "high_risk_groups": ["소아", "40대 여성"],
        "progression": ["뇌출혈", "뇌경색"],
        "surgery_cost": 25000000,  # 혈관우회술 2,500만원
        "coverage_requirement": "뇌혈관질환 전체 담보(I60~I69) 필수",
        "denial_risk": "뇌출혈/뇌경색 담보에서 제외 가능"
    },
    "lacunar_infarction": {
        "code": ["I63.8", "I63.9"],
        "name": "열공성 뇌경색 (Lacunar infarction)",
        "description": "뇌 심부의 작은 혈관이 막혀 발생하는 작은 크기(직경 1.5cm 이하)의 뇌경색",
        "size_threshold_cm": 1.5,
        "denial_reason": "크기가 작아 일상생활에 지장이 없다",
        "recurrence_rate": 0.30,  # 재발률 30%
        "dementia_progression": "다발성 열공성 뇌경색은 혈관성 치매로 진행 가능",
        "defense_strategies": [
            "MRI 영상 제출",
            "신경학적 검사 결과(NIHSS 점수) 제출",
            "장애 정도 입증 (일상생활 제한 사항 상세 기술)",
            "재발 가능성 강조 (재발률 30%)"
        ]
    }
}


# ══════════════════════════════════════════════════════════════════════════════
# [2] KCD 코드 분석 및 담보 매핑 함수
# ══════════════════════════════════════════════════════════════════════════════

def analyze_kcd_coverage(
    kcd_code: str,
    current_coverage: Dict[str, Any]
) -> Dict[str, Any]:
    """
    KCD 코드 기반 담보 매핑 및 보장 격차 분석
    
    Args:
        kcd_code: 진단받은 KCD 코드 (예: "I64", "I65", "I67.5")
        current_coverage: 현재 가입된 보험 담보 정보
    
    Returns:
        dict: {
            "kcd_code": "I64",
            "disease_name": "출혈 또는 경색으로 명시되지 않은 뇌졸중",
            "coverage_status": "denied",
            "denial_risk": "critical",
            "defense_strategies": [...],
            "recommended_coverage": "뇌혈관질환 전체 담보(I60~I69)",
            "estimated_cost": 3500000
        }
    """
    result = {
        "kcd_code": kcd_code,
        "disease_name": "",
        "coverage_status": "unknown",
        "denial_risk": "low",
        "defense_strategies": [],
        "recommended_coverage": "",
        "estimated_cost": 0,
        "gap_analysis": {}
    }
    
    # I64 면책 지뢰 검사 (담보 우선순위 판별 로직)
    if kcd_code == "I64":
        result["disease_name"] = I64_LANDMINE["name"]
        
        # [오류 검증 7] 담보 종류별 부지급률 차등 적용
        # 1순위: 뇌혈관질환 전체(I60~I69) 담보 → 부지급률 0%
        # 2순위: 뇌졸중(I60~I66) 담보 → 부지급률 85%
        # 3순위: 뇌출혈/뇌경색(I60~I63) 담보 → 부지급률 85%
        
        if current_coverage.get("cerebrovascular_full"):  # I60~I69 전체 담보
            result["coverage_status"] = "covered"
            result["denial_risk"] = "none"
            result["actual_denial_rate"] = 0.0  # 0% 부지급률
            result["coverage_type"] = "뇌혈관질환 전체 담보(I60~I69)"
            result["defense_strategies"] = [
                "✅ I64 코드도 뇌혈관질환 전체 담보(I60~I69)로 완벽 보장",
                "추가 방어 불필요 - 약관상 I60~I69 범위에 명시적으로 포함됨"
            ]
        elif current_coverage.get("non_life_stroke"):  # 뇌졸중(I60~I66) 담보
            result["coverage_status"] = "denied"
            result["denial_risk"] = "critical"
            result["actual_denial_rate"] = I64_LANDMINE["denial_rate"]  # 85% 부지급률
            result["coverage_type"] = "뇌졸중 담보(I60~I66)"
            result["defense_strategies"] = I64_LANDMINE["defense_strategies"]
        else:  # 뇌출혈/뇌경색(I60~I63) 담보 또는 미가입
            result["coverage_status"] = "denied"
            result["denial_risk"] = "critical"
            result["actual_denial_rate"] = I64_LANDMINE["denial_rate"]  # 85% 부지급률
            result["coverage_type"] = "뇌출혈/뇌경색 담보(I60~I63) 또는 미가입"
            result["defense_strategies"] = I64_LANDMINE["defense_strategies"]
        
        result["recommended_coverage"] = "뇌혈관질환 전체 담보(I60~I69)"
        result["estimated_cost"] = 35000000
        result["gap_analysis"] = {
            "occurrence_rate": f"{I64_LANDMINE['occurrence_rate']*100:.0f}%",
            "base_denial_rate": f"{I64_LANDMINE['denial_rate']*100:.0f}%",
            "actual_denial_rate": f"{result['actual_denial_rate']*100:.0f}%",
            "conversion_success_rate": f"{I64_LANDMINE['conversion_success_rate']*100:.0f}%",
            "alternative_codes": I64_LANDMINE["alternative_codes"],
            "coverage_hierarchy": {
                "level_3_full": "뇌혈관질환 전체(I60~I69) → I64 부지급률 0%",
                "level_2_stroke": "뇌졸중(I60~I66) → I64 부지급률 85%",
                "level_1_basic": "뇌출혈/뇌경색(I60~I63) → I64 부지급률 85%"
            }
        }
    
    # I65 경동맥 협착 검사 (협착도별 분쟁 분석 포함)
    elif kcd_code == "I65":
        result["disease_name"] = I65_COVERAGE_GAP["name"]
        
        # 생명보험 vs 손해보험 보장 격차 분석
        life_covered = current_coverage.get("life_cerebral_hemorrhage") or current_coverage.get("life_cerebral_infarction")
        non_life_covered = current_coverage.get("non_life_stroke")
        
        if life_covered and not non_life_covered:
            result["coverage_status"] = "gap_detected"
            result["denial_risk"] = "high"
        elif non_life_covered:
            result["coverage_status"] = "covered"
            result["denial_risk"] = "low"
        else:
            result["coverage_status"] = "not_covered"
            result["denial_risk"] = "critical"
        
        result["defense_strategies"] = I65_COVERAGE_GAP["defense_strategies"]
        result["recommended_coverage"] = "손해보험 뇌졸중 담보(I60~I66) 또는 뇌혈관질환 전체 담보(I60~I69)"
        result["estimated_cost"] = I65_COVERAGE_GAP["treatment_cost"]["stent"]
        result["gap_analysis"] = {
            "life_insurance_coverage": I65_COVERAGE_GAP["life_insurance_coverage"],
            "non_life_insurance_coverage": I65_COVERAGE_GAP["non_life_insurance_coverage"],
            "stenosis_threshold": f"{I65_COVERAGE_GAP['stenosis_threshold']}%",
            "stroke_risk_5years": f"{I65_COVERAGE_GAP['stroke_risk_5years']*100:.0f}%",
            "treatment_cost": I65_COVERAGE_GAP["treatment_cost"],
            "stenosis_severity_classification": I65_COVERAGE_GAP["stenosis_severity_classification"],
            "measurement_methods": I65_COVERAGE_GAP["measurement_methods"],
            "golden_evidence": I65_COVERAGE_GAP["golden_evidence"],
            "legal_basis": I65_COVERAGE_GAP["legal_basis"]
        }
    
    # 모야모야병 검사
    elif kcd_code == "I67.5":
        moyamoya = SPECIAL_DISEASES["moyamoya"]
        result["disease_name"] = moyamoya["name"]
        result["coverage_status"] = "denied" if not current_coverage.get("cerebrovascular_full") else "covered"
        result["denial_risk"] = "critical"
        result["defense_strategies"] = [moyamoya["coverage_requirement"]]
        result["recommended_coverage"] = "뇌혈관질환 전체 담보(I60~I69)"
        result["estimated_cost"] = moyamoya["surgery_cost"]
        result["gap_analysis"] = {
            "high_risk_groups": moyamoya["high_risk_groups"],
            "progression": moyamoya["progression"],
            "denial_risk": moyamoya["denial_risk"]
        }
    
    # 열공성 뇌경색 검사
    elif kcd_code in ["I63.8", "I63.9"]:
        lacunar = SPECIAL_DISEASES["lacunar_infarction"]
        result["disease_name"] = lacunar["name"]
        result["coverage_status"] = "partial_denial_risk"
        result["denial_risk"] = "high"
        result["defense_strategies"] = lacunar["defense_strategies"]
        result["recommended_coverage"] = "뇌경색 담보 + 후유장해 진단비"
        result["estimated_cost"] = 28000000
        result["gap_analysis"] = {
            "size_threshold": f"{lacunar['size_threshold_cm']}cm",
            "denial_reason": lacunar["denial_reason"],
            "recurrence_rate": f"{lacunar['recurrence_rate']*100:.0f}%",
            "dementia_progression": lacunar["dementia_progression"]
        }
    
    # 일반 뇌출혈/뇌경색
    elif kcd_code in ["I60", "I61", "I62", "I63"]:
        result["disease_name"] = f"뇌혈관질환 ({kcd_code})"
        result["coverage_status"] = "covered"
        result["denial_risk"] = "low"
        result["defense_strategies"] = ["표준 담보로 보장 가능"]
        result["recommended_coverage"] = "뇌출혈/뇌경색 담보"
        result["estimated_cost"] = 30000000
    
    return result


def get_coverage_hierarchy_map() -> Dict[str, Any]:
    """
    담보 계층 구조 맵 반환
    
    Returns:
        dict: 담보 유형별 KCD 코드 범위 및 보장 내용
    """
    return {
        "level_1_basic": {
            "name": "뇌출혈/뇌경색 (생명보험 기본)",
            "codes": ["I60", "I61", "I62", "I63"],
            "coverage_rate": 0.75,  # 전체 뇌혈관질환의 75% 보장
            "excluded_codes": ["I64", "I65", "I66", "I67", "I68", "I69"],
            "risk": "I64 면책 지뢰 노출, I65 경동맥 협착 미보장"
        },
        "level_2_stroke": {
            "name": "뇌졸중 (손해보험 표준)",
            "codes": ["I60", "I61", "I62", "I63", "I65", "I66"],
            "coverage_rate": 0.85,  # 전체 뇌혈관질환의 85% 보장
            "excluded_codes": ["I64", "I67", "I68", "I69"],
            "risk": "I64 면책 지뢰 노출, 모야모야병(I67.5) 미보장"
        },
        "level_3_full": {
            "name": "뇌혈관질환 전체 (특약)",
            "codes": ["I60", "I61", "I62", "I63", "I64", "I65", "I66", "I67", "I68", "I69"],
            "coverage_rate": 1.0,  # 전체 뇌혈관질환의 100% 보장
            "excluded_codes": [],
            "risk": "없음 (가장 안전한 보장)"
        }
    }


# ══════════════════════════════════════════════════════════════════════════════
# [3] 18개월 법칙 및 재활치료 가이드
# ══════════════════════════════════════════════════════════════════════════════

EIGHTEEN_MONTH_RULE = {
    "name": "뇌졸중 후유장해 진단의 18개월 법칙",
    "waiting_period_months": 18,
    "legal_basis": "장애인복지법",
    "reasons": {
        "brain_plasticity": {
            "name": "뇌 가소성 (Brain Plasticity)",
            "description": "뇌손상 후 6개월~1년간 신경회로 재구성으로 기능 회복 가능",
            "recovery_window_months": 12
        },
        "permanent_disability": {
            "name": "고착 판정 (Permanent Disability)",
            "description": "18개월 이후에야 후유장해가 영구적으로 고착되었다고 의학적으로 판단",
            "assessment_timing_months": 18
        }
    },
    "insurance_implications": {
        "early_diagnosis_risk": "조기 진단 시 보험금 감액 또는 부지급 가능",
        "optimal_timing": "발병 후 18개월 시점에 장애 진단",
        "coverage_required": ["뇌졸중 진단비", "후유장해 진단비", "재활치료비 특약"]
    },
    "rehabilitation_strategy": {
        "phase_1": {
            "name": "급성기 재활 (발병 후 0~3개월)",
            "description": "집중 재활 골든타임",
            "cost_per_month": 5000000,
            "location": "입원 재활"
        },
        "phase_2": {
            "name": "회복기 재활 (발병 후 3~6개월)",
            "description": "지속 재활",
            "cost_per_month": 2000000,
            "location": "통원 재활"
        },
        "phase_3": {
            "name": "유지기 재활 (발병 후 6~18개월)",
            "description": "기능 유지 및 최종 평가 준비",
            "cost_per_month": 1000000,
            "location": "통원 재활"
        }
    },
    "total_rehabilitation_cost": {
        "min": 8000000,  # 800만원
        "max": 12000000,  # 1,200만원
        "average": 10000000  # 1,000만원
    }
}


def get_rehabilitation_guide(months_since_onset: int) -> Dict[str, Any]:
    """
    뇌졸중 발병 후 경과 시간에 따른 재활치료 가이드
    
    Args:
        months_since_onset: 발병 후 경과 개월 수
    
    Returns:
        dict: 현재 단계별 재활 가이드 및 비용 정보
    """
    if months_since_onset <= 3:
        phase = EIGHTEEN_MONTH_RULE["rehabilitation_strategy"]["phase_1"]
        disability_assessment_ready = False
        remaining_months = 18 - months_since_onset
    elif months_since_onset <= 6:
        phase = EIGHTEEN_MONTH_RULE["rehabilitation_strategy"]["phase_2"]
        disability_assessment_ready = False
        remaining_months = 18 - months_since_onset
    elif months_since_onset < 18:
        phase = EIGHTEEN_MONTH_RULE["rehabilitation_strategy"]["phase_3"]
        disability_assessment_ready = False
        remaining_months = 18 - months_since_onset
    else:
        phase = {"name": "장애 진단 가능 시기", "description": "18개월 경과 완료"}
        disability_assessment_ready = True
        remaining_months = 0
    
    return {
        "months_since_onset": months_since_onset,
        "current_phase": phase,
        "disability_assessment_ready": disability_assessment_ready,
        "remaining_months_to_assessment": remaining_months,
        "eighteen_month_rule": EIGHTEEN_MONTH_RULE["name"],
        "legal_basis": EIGHTEEN_MONTH_RULE["legal_basis"],
        "insurance_implications": EIGHTEEN_MONTH_RULE["insurance_implications"],
        "total_rehabilitation_cost": EIGHTEEN_MONTH_RULE["total_rehabilitation_cost"]
    }


# ══════════════════════════════════════════════════════════════════════════════
# [4] 뇌수종 및 치매 신약 비용 분석
# ══════════════════════════════════════════════════════════════════════════════

HYDROCEPHALUS_NPH = {
    "code": "G91.2",
    "name": "정상압 수두증 (Normal Pressure Hydrocephalus, NPH)",
    "symptoms": ["보행장애", "인지장애", "요실금"],
    "misdiagnosis_risk": "알츠하이머 치매와 오진되기 쉬움",
    "treatment": {
        "name": "션트(Shunt) 수술",
        "description": "뇌실에서 복강으로 뇌척수액을 배출하는 관 삽입",
        "cost": 10000000,  # 1,000만원 (비급여 포함)
        "success_rate": 0.80,  # 수술 후 80% 이상 증상 호전
        "cure_possible": True
    },
    "insurance_coverage": "뇌혈관질환 후유증(I69) 보장 확인 필요"
}

ALZHEIMER_DRUG_LECANEMAB = {
    "name": "레카네맙 (Lecanemab)",
    "approval": "2023년 FDA 승인",
    "target": "초기 알츠하이머 환자",
    "mechanism": "아밀로이드 베타 제거 항체 치료제",
    # [오류 검증 8] 건강보험 급여 적용 여부에 따른 비용 차등
    "cost_non_covered": {
        "annual": 40000000,  # 비급여 시 연간 4,000만원
        "lifetime": 150000000,  # 비급여 시 평생 1억 5,000만원
        "description": "건강보험 미적용 시 전액 본인부담"
    },
    "cost_covered": {
        "annual": 5000000,  # 급여 시 본인부담 상한제 적용 (예상)
        "lifetime": 20000000,  # 급여 시 평생 2,000만원 (예상)
        "description": "건강보험 급여 시 본인부담 상한제 적용 (연간 500만원 예상)",
        "note": "2026년 기준 급여 승인 여부 미확정 - 예상 수치"
    },
    "insurance_coverage_status": "건강보험 미적용 (2026년 기준)",
    "recommended_insurance": {
        "dementia_diagnosis": 30000000,  # 치매 진단비 최소 3,000만원
        "long_term_care": 120000000  # 장기간병 특약 (월 100만원 × 10년)
    }
}


def analyze_dementia_treatment_cost(
    diagnosis_type: str,
    health_insurance_covered: bool = False
) -> Dict[str, Any]:
    """
    치매 유형별 치료 비용 분석
    
    Args:
        diagnosis_type: "NPH" (정상압 수두증) 또는 "Alzheimer" (알츠하이머)
        health_insurance_covered: 건강보험 급여 적용 여부 (기본값: False)
    
    Returns:
        dict: 치료 비용 및 보험 전략
    """
    if diagnosis_type == "NPH":
        return {
            "diagnosis": HYDROCEPHALUS_NPH["name"],
            "symptoms": HYDROCEPHALUS_NPH["symptoms"],
            "misdiagnosis_risk": HYDROCEPHALUS_NPH["misdiagnosis_risk"],
            "treatment": HYDROCEPHALUS_NPH["treatment"],
            "one_time_cost": HYDROCEPHALUS_NPH["treatment"]["cost"],
            "cure_possible": True,
            "insurance_strategy": [
                "뇌혈관질환 후유증(I69) 보장 확인",
                "수술비 특약 가입",
                "NPH는 션트 수술로 완치 가능하므로 조기 진단 중요"
            ]
        }
    elif diagnosis_type == "Alzheimer":
        # [오류 검증 8] 건강보험 급여 적용 여부에 따른 비용 분리
        if health_insurance_covered:
            # 건강보험 급여 시나리오
            cost_data = ALZHEIMER_DRUG_LECANEMAB["cost_covered"]
            insurance_strategy = [
                f"✅ 건강보험 급여 적용 시 본인부담 상한제 적용",
                f"치매 진단비 최소 {ALZHEIMER_DRUG_LECANEMAB['recommended_insurance']['dementia_diagnosis']//10000}만원 이상 가입",
                f"장기간병 특약 추가 (월 100만원 × 10년 = {ALZHEIMER_DRUG_LECANEMAB['recommended_insurance']['long_term_care']//10000}만원)",
                f"레카네맙 신약 비용 연간 {cost_data['annual']//10000}만원 (급여 시 본인부담 상한제)"
            ]
        else:
            # 건강보험 미적용 시나리오 (기본값)
            cost_data = ALZHEIMER_DRUG_LECANEMAB["cost_non_covered"]
            insurance_strategy = [
                f"⚠️ 건강보험 미적용 시 전액 본인부담",
                f"치매 진단비 최소 {ALZHEIMER_DRUG_LECANEMAB['recommended_insurance']['dementia_diagnosis']//10000}만원 이상 가입",
                f"장기간병 특약 추가 (월 100만원 × 10년 = {ALZHEIMER_DRUG_LECANEMAB['recommended_insurance']['long_term_care']//10000}만원)",
                f"레카네맙 신약 비용 연간 {cost_data['annual']//10000}만원 (비급여 시 전액 본인부담)"
            ]
        
        return {
            "diagnosis": "알츠하이머 치매",
            "new_drug": ALZHEIMER_DRUG_LECANEMAB["name"],
            "approval": ALZHEIMER_DRUG_LECANEMAB["approval"],
            "mechanism": ALZHEIMER_DRUG_LECANEMAB["mechanism"],
            "health_insurance_covered": health_insurance_covered,
            "insurance_coverage_status": ALZHEIMER_DRUG_LECANEMAB["insurance_coverage_status"],
            "annual_cost": cost_data["annual"],
            "lifetime_cost": cost_data["lifetime"],
            "cost_description": cost_data["description"],
            "cure_possible": False,
            "insurance_strategy": insurance_strategy,
            "cost_comparison": {
                "non_covered": {
                    "annual": ALZHEIMER_DRUG_LECANEMAB["cost_non_covered"]["annual"],
                    "lifetime": ALZHEIMER_DRUG_LECANEMAB["cost_non_covered"]["lifetime"],
                    "description": ALZHEIMER_DRUG_LECANEMAB["cost_non_covered"]["description"]
                },
                "covered": {
                    "annual": ALZHEIMER_DRUG_LECANEMAB["cost_covered"]["annual"],
                    "lifetime": ALZHEIMER_DRUG_LECANEMAB["cost_covered"]["lifetime"],
                    "description": ALZHEIMER_DRUG_LECANEMAB["cost_covered"]["description"],
                    "note": ALZHEIMER_DRUG_LECANEMAB["cost_covered"]["note"]
                },
                "savings_if_covered": {
                    "annual": ALZHEIMER_DRUG_LECANEMAB["cost_non_covered"]["annual"] - ALZHEIMER_DRUG_LECANEMAB["cost_covered"]["annual"],
                    "lifetime": ALZHEIMER_DRUG_LECANEMAB["cost_non_covered"]["lifetime"] - ALZHEIMER_DRUG_LECANEMAB["cost_covered"]["lifetime"]
                }
            }
        }
    else:
        return {"error": "Invalid diagnosis_type. Use 'NPH' or 'Alzheimer'"}
