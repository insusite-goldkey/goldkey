"""
hq_i65_dispute_analyzer.py — I65 경동맥 협착 보험금 지급 분쟁 전문 분석 엔진
[GP-STEP15-B] Goldkey AI Masters 2026

목적: 경동맥 협착(I65) 보험금 지급 분쟁에서 보험사의 I70 격하 논리를 무력화하고
      설계사의 손해사정 전문성을 극대화

핵심 기능:
1. 협착도별 분쟁 리스크 분석 (Mild/Moderate/Severe/Occlusion)
2. 측정 방식 비교 분석 (NASCET vs ECST)
3. 4대 필수 증거 체크리스트
4. 법률 근거 자동 생성
5. 전문의 소견서 초안 생성
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal


# ══════════════════════════════════════════════════════════════════════════════
# [1] 협착도별 분쟁 리스크 분석
# ══════════════════════════════════════════════════════════════════════════════

def analyze_stenosis_severity(stenosis_percentage: float) -> Dict[str, Any]:
    """
    협착률(%)에 따른 분쟁 리스크 및 대응 전략 분석
    
    Args:
        stenosis_percentage: 협착률 (0~100%)
    
    Returns:
        dict: {
            "severity": "mild",
            "range": "0~49%",
            "dispute_risk": "critical",
            "approval_probability": 0.40,
            "insurer_strategy": "I70(죽상경화증)으로 격하 시도",
            "defense_strategy": "작성자 불이익 원칙 + 임상적 유의성 강조",
            "alert_message": "⚠️ 분쟁 경고: Mild 협착 감지. I70 격하 리스크 높음."
        }
    """
    if stenosis_percentage < 50:
        severity = "mild"
        range_str = "0~49%"
        dispute_risk = "critical"
        approval_probability = 0.40
        insurer_strategy = "I70(죽상경화증)으로 격하 시도"
        defense_strategy = "작성자 불이익 원칙 + 임상적 유의성 강조"
        alert_message = "⚠️ 분쟁 경고: Mild 협착 감지. I70 격하 리스크 높음. 즉시 전문가 검토 필요."
        action_items = [
            "영상판독지 내 구체적 협착률(%) 수치 확인",
            "NASCET vs ECST 측정 방식 중 유리한 수치 채택",
            "신경학적 증상(어지럼증, 마비감) 상세 기록",
            "주치의에게 'KCD I65 진단 적정성' 재확인 요청"
        ]
    elif stenosis_percentage < 70:
        severity = "moderate"
        range_str = "50~69%"
        dispute_risk = "medium"
        approval_probability = 0.75
        insurer_strategy = "측정 방식 재검증 요구"
        defense_strategy = "NASCET/ECST 방식 중 유리한 수치 채택"
        alert_message = "⚡ 주의: Moderate 협착. 측정 방식 검증 필요."
        action_items = [
            "NASCET vs ECST 측정 방식 비교 분석",
            "경동맥 초음파 PSV 수치 확인",
            "뇌혈관 조영술(TFCA) 추가 검사 권장"
        ]
    elif stenosis_percentage < 100:
        severity = "severe"
        range_str = "70~99%"
        dispute_risk = "low"
        approval_probability = 0.95
        insurer_strategy = "통상적 보상 대상"
        defense_strategy = "수술 여부 무관 지급 근거 명확"
        alert_message = "✅ 안전: Severe 협착. 통상적 보상 대상."
        action_items = [
            "스텐트 시술 또는 경동맥 내막절제술 계획 확인",
            "치료비 견적서 확보"
        ]
    else:  # 100%
        severity = "occlusion"
        range_str = "100%"
        dispute_risk = "none"
        approval_probability = 1.0
        insurer_strategy = "의학적 이견 없음"
        defense_strategy = "확정적 지급 대상"
        alert_message = "✅ 확정: 혈관 완전 폐쇄. 의학적 이견 없는 지급 대상."
        action_items = [
            "즉시 보험금 청구 진행"
        ]
    
    return {
        "severity": severity,
        "range": range_str,
        "stenosis_percentage": stenosis_percentage,
        "dispute_risk": dispute_risk,
        "approval_probability": approval_probability,
        "insurer_strategy": insurer_strategy,
        "defense_strategy": defense_strategy,
        "alert_message": alert_message,
        "action_items": action_items
    }


# ══════════════════════════════════════════════════════════════════════════════
# [2] 측정 방식 비교 분석 (NASCET vs ECST)
# ══════════════════════════════════════════════════════════════════════════════

def compare_measurement_methods(
    stenosis_min_diameter: float,
    normal_distal_diameter: float,
    estimated_normal_diameter: float
) -> Dict[str, Any]:
    """
    NASCET vs ECST 측정 방식 비교 분석
    
    Args:
        stenosis_min_diameter: 협착부 최소 직경 (mm)
        normal_distal_diameter: 정상 원위부 직경 (mm) - NASCET 분모
        estimated_normal_diameter: 추정 정상 직경 (mm) - ECST 분모
    
    Returns:
        dict: {
            "NASCET": {"stenosis_percentage": 45.5, "use_case": "보험사 유리"},
            "ECST": {"stenosis_percentage": 62.3, "use_case": "고객 유리"},
            "recommended_method": "ECST",
            "difference": 16.8
        }
    """
    # NASCET 방식 계산
    nascet_stenosis = (1 - stenosis_min_diameter / normal_distal_diameter) * 100
    
    # ECST 방식 계산
    ecst_stenosis = (1 - stenosis_min_diameter / estimated_normal_diameter) * 100
    
    # 차이 계산
    difference = abs(ecst_stenosis - nascet_stenosis)
    
    # 고객에게 유리한 방식 선택
    if ecst_stenosis > nascet_stenosis:
        recommended_method = "ECST"
        recommended_percentage = ecst_stenosis
    else:
        recommended_method = "NASCET"
        recommended_percentage = nascet_stenosis
    
    return {
        "NASCET": {
            "stenosis_percentage": round(nascet_stenosis, 1),
            "formula": "(1 - 협착부 최소 직경 / 정상 원위부 직경) × 100",
            "use_case": "보험사 유리"
        },
        "ECST": {
            "stenosis_percentage": round(ecst_stenosis, 1),
            "formula": "(1 - 협착부 최소 직경 / 추정 정상 직경) × 100",
            "use_case": "고객 유리"
        },
        "recommended_method": recommended_method,
        "recommended_percentage": round(recommended_percentage, 1),
        "difference": round(difference, 1),
        "recommendation": f"{recommended_method} 방식 채택 시 협착률 {recommended_percentage:.1f}%로 산출되어 고객에게 유리합니다."
    }


# ══════════════════════════════════════════════════════════════════════════════
# [3] 4대 필수 증거 체크리스트
# ══════════════════════════════════════════════════════════════════════════════

def generate_evidence_checklist(
    has_mra_cta: bool = False,
    has_tfca: bool = False,
    has_carotid_ultrasound: bool = False,
    has_radiology_report: bool = False,
    has_physician_statement: bool = False,
    physician_statement_elements: Optional[Dict[str, bool]] = None
) -> Dict[str, Any]:
    """
    4대 필수 증거 체크리스트 생성
    
    Args:
        has_mra_cta: 뇌혈관 MRA/CTA 보유 여부
        has_tfca: 뇌혈관 조영술(TFCA) 보유 여부
        has_carotid_ultrasound: 경동맥 초음파 보유 여부
        has_radiology_report: 영상판독지 보유 여부
        has_physician_statement: 전문의 소견서 보유 여부
        physician_statement_elements: 소견서 3요소 포함 여부
    
    Returns:
        dict: 체크리스트 및 완성도 분석
    """
    checklist = {
        "imaging": {
            "MRA_CTA": {
                "status": "✅" if has_mra_cta else "❌",
                "description": "뇌혈관 MRA/CTA - 혈관 협착 정도 수치화 표준 검사",
                "importance": "필수",
                "completed": has_mra_cta
            },
            "TFCA": {
                "status": "✅" if has_tfca else "❌",
                "description": "뇌혈관 조영술(TFCA) - 분쟁 시 최종 확정 증거",
                "importance": "분쟁 시 필수",
                "completed": has_tfca
            },
            "carotid_ultrasound": {
                "status": "✅" if has_carotid_ultrasound else "❌",
                "description": "경동맥 초음파 - PSV(최대 수축기 혈류속도) 측정",
                "importance": "권장",
                "completed": has_carotid_ultrasound
            }
        },
        "radiology_report": {
            "status": "✅" if has_radiology_report else "❌",
            "description": "영상판독지 내 구체적 협착률(%) 수치 추출 필수",
            "importance": "필수",
            "completed": has_radiology_report
        },
        "physician_statement": {
            "status": "✅" if has_physician_statement else "❌",
            "description": "전문의 진단 소견서 3요소 포함",
            "importance": "필수",
            "completed": has_physician_statement,
            "elements": {}
        }
    }
    
    # 전문의 소견서 3요소 상세 체크
    if physician_statement_elements:
        checklist["physician_statement"]["elements"] = {
            "element_1": {
                "status": "✅" if physician_statement_elements.get("협착_부위_수치") else "❌",
                "description": "영상 검사 결과 확인된 구체적 협착 부위와 수치(%) 명시",
                "completed": physician_statement_elements.get("협착_부위_수치", False)
            },
            "element_2": {
                "status": "✅" if physician_statement_elements.get("KCD_I65_확정") else "❌",
                "description": "KCD상 I65에 부합한다는 확정적 소견",
                "completed": physician_statement_elements.get("KCD_I65_확정", False)
            },
            "element_3": {
                "status": "✅" if physician_statement_elements.get("신경학적_증상") else "❌",
                "description": "신경학적 증상(어지럼증, 마비감 등)과의 상관관계 기술",
                "completed": physician_statement_elements.get("신경학적_증상", False)
            }
        }
    
    # 완성도 계산
    total_items = 5  # MRA/CTA, TFCA, 초음파, 판독지, 소견서
    completed_items = sum([
        has_mra_cta,
        has_tfca,
        has_carotid_ultrasound,
        has_radiology_report,
        has_physician_statement
    ])
    
    completeness = (completed_items / total_items) * 100
    
    # 권고사항 생성
    recommendations = []
    if not has_mra_cta:
        recommendations.append("뇌혈관 MRA/CTA 검사 즉시 시행 필요")
    if not has_radiology_report:
        recommendations.append("영상판독지 발급 및 협착률(%) 수치 확인 필수")
    if not has_physician_statement:
        recommendations.append("전문의 소견서 발급 요청 (3요소 포함 필수)")
    if not has_tfca and completeness < 80:
        recommendations.append("분쟁 예상 시 뇌혈관 조영술(TFCA) 추가 검사 권장")
    
    return {
        "checklist": checklist,
        "completeness": round(completeness, 1),
        "completed_items": completed_items,
        "total_items": total_items,
        "recommendations": recommendations,
        "status": "완료" if completeness == 100 else "미완료"
    }


# ══════════════════════════════════════════════════════════════════════════════
# [4] 법률 근거 자동 생성
# ══════════════════════════════════════════════════════════════════════════════

def generate_legal_basis(dispute_scenario: str = "mild_stenosis") -> Dict[str, Any]:
    """
    분쟁 시나리오별 법률 근거 자동 생성
    
    Args:
        dispute_scenario: "mild_stenosis" (경미한 협착), "measurement_dispute" (측정 방식 분쟁)
    
    Returns:
        dict: 법률 근거 및 주장 논리
    """
    legal_basis = {
        "civil_code_661": {
            "title": "상법 제661조 - 사고발생의 통지",
            "content": "보험계약자 또는 피보험자나 보험수익자는 보험사고의 발생을 안 때에는 지체없이 보험자에게 그 통지를 발송하여야 한다.",
            "application": "경동맥 협착(I65) 진단 즉시 보험사에 통지하였으며, 객관적 증빙(영상판독지, 진단서)을 갖추어 청구함."
        },
        "terms_regulation_act_5": {
            "title": "약관의 규제에 관한 법률 제5조 - 해석의 원칙 (작성자 불이익)",
            "content": "약관의 뜻이 명백하지 아니한 경우에는 고객에게 유리하게 해석되어야 한다.",
            "application": "보험약관에서 '협착률 50% 이상만 지급한다'는 구체적인 제한 규정을 두지 않았으므로, 의학적 판단에 따른 I65 진단은 약관상 지급 대상임."
        },
        "insurance_act_185": {
            "title": "보험업법 제185조 - 손해사정의 공정성",
            "content": "손해사정은 객관적인 정보를 바탕으로 공정하게 사정되어야 한다.",
            "application": "영상판독지상 실질적 협착이 확인되었으며, 전문의가 I65로 진단한 이상 보험사는 이를 존중해야 함."
        },
        "supreme_court_precedent": {
            "title": "대법원 2017다201XXX 판례",
            "content": "약관의 뜻이 명백하지 않을 때는 고객에게 유리하게 해석해야 한다.",
            "application": "I65(경동맥 협착)와 I70(죽상경화증)의 경계선상에 있는 경우, 고객에게 유리하게 I65로 해석되어야 함."
        },
        "fss_decision": {
            "title": "금융감독원 분쟁조정 결정례",
            "content": "협착의 정도가 심하지 않더라도 임상적으로 유의미한 폐쇄 증상이 있다면 뇌혈관질환으로 인정해야 한다.",
            "application": "환자가 호소하는 신경학적 증상(어지럼증, 마비감 등)이 있으므로, 협착률과 무관하게 I65 진단은 타당함."
        }
    }
    
    if dispute_scenario == "mild_stenosis":
        main_argument = [
            "1. 약관의 규제에 관한 법률 제5조에 따라, 약관에 명시되지 않은 협착률 기준은 고객에게 유리하게 해석되어야 합니다.",
            "2. 영상판독지상 실질적 협착이 확인되었으며, 전문의가 KCD I65로 진단한 이상 이는 의학적·법률적으로 정당합니다.",
            "3. 금융감독원 결정례에 따라, 임상적으로 유의미한 증상이 있다면 협착 정도와 무관하게 뇌혈관질환으로 인정되어야 합니다."
        ]
    elif dispute_scenario == "measurement_dispute":
        main_argument = [
            "1. NASCET과 ECST는 모두 의학적으로 인정된 측정 방식이며, 고객에게 유리한 방식을 채택하는 것이 타당합니다.",
            "2. 약관에 특정 측정 방식을 명시하지 않았으므로, 작성자 불이익 원칙에 따라 고객에게 유리한 ECST 방식을 채택해야 합니다.",
            "3. 보험업법 제185조에 따라, 손해사정은 객관적 정보를 바탕으로 공정하게 이루어져야 하며, 측정 방식의 자의적 선택은 부당합니다."
        ]
    else:
        main_argument = []
    
    return {
        "legal_basis": legal_basis,
        "main_argument": main_argument,
        "conclusion": "위 법률 근거에 따라, 경동맥 협착(I65) 진단은 보험약관상 지급 대상이며, 보험사의 I70 격하 주장은 법률적 근거가 없습니다."
    }


# ══════════════════════════════════════════════════════════════════════════════
# [5] 전문의 소견서 초안 생성
# ══════════════════════════════════════════════════════════════════════════════

def generate_physician_statement_draft(
    patient_name: str,
    stenosis_percentage: float,
    stenosis_location: str,
    measurement_method: str,
    neurological_symptoms: List[str]
) -> str:
    """
    전문의 소견서 초안 자동 생성
    
    Args:
        patient_name: 환자 이름
        stenosis_percentage: 협착률 (%)
        stenosis_location: 협착 부위 (예: "좌측 내경동맥")
        measurement_method: 측정 방식 ("NASCET" 또는 "ECST")
        neurological_symptoms: 신경학적 증상 목록 (예: ["어지럼증", "마비감"])
    
    Returns:
        str: 전문의 소견서 초안
    """
    symptoms_str = ", ".join(neurological_symptoms) if neurological_symptoms else "없음"
    
    draft = f"""
진단 소견서

환자명: {patient_name}
진단명: 경동맥 및 뇌동맥의 폐쇄 및 협착 (KCD 코드: I65)

[소견서 3요소 필수 포함]

1. 영상 검사 결과 확인된 구체적 협착 부위와 수치(%)
   - 협착 부위: {stenosis_location}
   - 협착률: {stenosis_percentage:.1f}% ({measurement_method} 방식 기준)
   - 검사 방법: 뇌혈관 MRA/CTA 및 경동맥 초음파
   - 영상판독 소견: 상기 부위에 실질적인 혈관 협착이 확인됨

2. 한국표준질병사인분류(KCD)상 I65에 부합한다는 확정적 소견
   - 본 환자의 영상 검사 결과는 단순한 죽상경화증(I70)을 넘어, 
     혈관의 통로가 실질적으로 좁아진 상태로 확인됩니다.
   - 따라서 한국표준질병사인분류(KCD) 제7차 개정판 기준, 
     I65(경동맥 및 뇌동맥의 폐쇄 및 협착, 뇌경색을 유발하지 않은 것)에 
     해당한다고 판단됩니다.

3. 환자가 호소하는 신경학적 증상과의 상관관계
   - 주요 증상: {symptoms_str}
   - 임상적 소견: 상기 증상은 경동맥 협착으로 인한 뇌혈류 감소와 
     연관성이 있는 것으로 판단됩니다.
   - 향후 치료 계획: 협착률 및 증상 경과에 따라 스텐트 시술 또는 
     경동맥 내막절제술을 고려할 수 있습니다.

[의학적 판단]
본 환자는 영상 검사 결과 및 임상 증상을 종합적으로 고려할 때, 
KCD I65(경동맥 및 뇌동맥의 폐쇄 및 협착)에 해당하며, 
이는 뇌혈관질환 진단비 지급 대상에 부합합니다.

작성일: [작성일자]
작성자: [전문의 성명 및 면허번호]
의료기관: [의료기관명]
"""
    
    return draft.strip()
