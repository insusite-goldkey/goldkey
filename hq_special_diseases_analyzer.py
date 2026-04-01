"""
hq_special_diseases_analyzer.py — 특수 뇌혈관질환 부지급 방어 엔진
[GP-STEP15-A] Goldkey AI Masters 2026

목적: 열공성 뇌경색(I63.8/9), 모야모야병(I67.5), 기타 뇌혈관질환(I67.8)의
      부지급 논리를 무력화하고 의학적/법률적 지급 근거 자동 생성

핵심 기능:
1. 열공성 뇌경색 크기 기반 부지급 방어
2. 모야모야병 희귀질환 보장 격차 분석
3. I67.8 기타 뇌혈관질환 청구 로직
4. 의사 소견 요청서 템플릿 생성
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal


# ══════════════════════════════════════════════════════════════════════════════
# [1] 열공성 뇌경색 (Lacunar Infarction) 부지급 방어
# ══════════════════════════════════════════════════════════════════════════════

LACUNAR_INFARCTION_DATA = {
    "codes": ["I63.8", "I63.9"],
    "name": "열공성 뇌경색 (Lacunar infarction)",
    "description": "뇌 심부의 작은 혈관이 막혀 발생하는 작은 크기(직경 1.5cm 이하)의 뇌경색",
    "size_threshold_cm": 1.5,
    "denial_reason": "크기가 작아 일상생활에 지장이 없다",
    "recurrence_rate": 0.30,  # 재발률 30%
    "dementia_progression": "다발성 열공성 뇌경색은 혈관성 치매(F01)로 진행 가능",
    "average_cost": 15000000,  # 1,500만원
    "insurer_denial_script": "병변 크기가 1.5cm 이하로 경미하여 일상생활에 지장이 없으므로 부지급합니다.",
    "defense_strategies": [
        "MRI 영상 제출 (병변 위치 및 크기 확인)",
        "신경학적 검사 결과(NIHSS 점수) 제출",
        "장애 정도 입증 (일상생활 제한 사항 상세 기술)",
        "재발 가능성 강조 (재발률 30%)",
        "약관에 '크기 제한' 명시 없음 → 작성자 불이익 원칙 적용"
    ]
}


def analyze_lacunar_infarction(
    lesion_size_cm: float,
    nihss_score: int = 0,
    daily_life_impact: str = ""
) -> Dict[str, Any]:
    """
    열공성 뇌경색 부지급 방어 분석
    
    Args:
        lesion_size_cm: 병변 크기 (cm)
        nihss_score: NIHSS(미국 국립보건원 뇌졸중 척도) 점수 (0~42)
        daily_life_impact: 일상생활 영향 설명
    
    Returns:
        dict: {
            "lesion_size_cm": 1.2,
            "size_category": "small",
            "denial_risk": "high",
            "defense_strategy": "...",
            "physician_statement_required": True,
            "recommended_evidence": [...]
        }
    """
    size_category = "small" if lesion_size_cm <= 1.5 else "large"
    denial_risk = "high" if lesion_size_cm <= 1.5 else "low"
    
    # NIHSS 점수 기반 중증도 평가
    if nihss_score == 0:
        severity = "무증상 (asymptomatic)"
        denial_probability = 0.90
    elif nihss_score <= 4:
        severity = "경증 (minor stroke)"
        denial_probability = 0.70
    elif nihss_score <= 15:
        severity = "중등도 (moderate stroke)"
        denial_probability = 0.30
    else:
        severity = "중증 (severe stroke)"
        denial_probability = 0.10
    
    # 방어 전략
    defense_strategy = f"""
열공성 뇌경색 부지급 방어 전략:

1. 약관 해석의 원칙
   - 보험약관에 '병변 크기 1.5cm 이하 제외'라는 명시적 제한 없음
   - 작성자 불이익 원칙(약관규제법 제5조)에 따라 고객 유리 해석 필요
   - KCD 코드 I63.8/I63.9는 뇌경색의 하위 분류로 뇌경색 담보에 포함

2. 의학적 근거
   - 병변 크기: {lesion_size_cm}cm (기준 1.5cm 이하)
   - NIHSS 점수: {nihss_score}점 ({severity})
   - 신경학적 결손: {daily_life_impact if daily_life_impact else '일상생활 제한 사항 기술 필요'}
   - 재발률: 30% (향후 다발성 뇌경색 및 혈관성 치매 진행 가능)

3. 필수 제출 증거
   - MRI 영상 (병변 위치 및 크기 확인)
   - 신경학적 검사 결과 (NIHSS 점수)
   - 일상생활 제한 사항 상세 기술 (보행, 언어, 인지 기능 등)
   - 전문의 소견서 (재발 가능성 및 장애 정도 명시)

4. 법률 근거
   - 약관의 규제에 관한 법률 제5조 (해석의 원칙)
   - 대법원 판례: 약관 불명확 시 고객 유리 해석
   - 금감원 결정: 크기가 작아도 신경학적 증상 있으면 지급 대상
"""
    
    recommended_evidence = [
        "MRI 영상 (DICOM 파일 또는 CD)",
        "신경학적 검사 결과 (NIHSS 점수 포함)",
        "일상생활 제한 사항 상세 기술서",
        "전문의 소견서 (재발 가능성 및 장애 정도 명시)",
        "재활 치료 기록 (물리치료, 작업치료 등)"
    ]
    
    physician_statement_required = True if denial_probability > 0.5 else False
    
    return {
        "lesion_size_cm": lesion_size_cm,
        "size_category": size_category,
        "nihss_score": nihss_score,
        "severity": severity,
        "denial_risk": denial_risk,
        "denial_probability": denial_probability,
        "defense_strategy": defense_strategy,
        "physician_statement_required": physician_statement_required,
        "recommended_evidence": recommended_evidence,
        "alert_message": f"⚠️ 열공성 뇌경색 ({lesion_size_cm}cm): 부지급 확률 {denial_probability*100:.0f}%. 전문의 소견서 필수." if denial_probability > 0.5 else f"✅ 열공성 뇌경색 ({lesion_size_cm}cm): 통상적 보상 대상."
    }


# ══════════════════════════════════════════════════════════════════════════════
# [2] 모야모야병 (Moyamoya Disease) 보장 격차 분석
# ══════════════════════════════════════════════════════════════════════════════

MOYAMOYA_DISEASE_DATA = {
    "code": "I67.5",
    "name": "모야모야병 (Moyamoya disease)",
    "description": "뇌혈관이 좁아져 연기처럼 보이는 희귀질환",
    "high_risk_groups": ["소아", "40대 여성"],
    "progression": ["뇌출혈", "뇌경색"],
    "surgery_cost": 25000000,  # 혈관우회술 2,500만원
    "coverage_requirement": "뇌혈관질환 전체 담보(I60~I69) 필수",
    "denial_risk": "뇌출혈/뇌경색 담보에서 제외 가능",
    "insurer_denial_script": "모야모야병(I67.5)은 뇌출혈(I60~I62) 또는 뇌경색(I63)이 아니므로 부지급합니다.",
    "defense_strategies": [
        "뇌혈관질환 전체 담보(I60~I69) 가입 필수",
        "약관에 'I67.5 제외' 명시 없음 → 작성자 불이익 원칙",
        "모야모야병은 뇌출혈/뇌경색의 원인 질환 → 인과관계 강조",
        "혈관우회술 비용 2,500만원 → 고액 치료비 근거"
    ]
}


def analyze_moyamoya_disease(
    current_coverage: Dict[str, Any],
    has_hemorrhage: bool = False,
    has_infarction: bool = False
) -> Dict[str, Any]:
    """
    모야모야병 보장 격차 분석
    
    Args:
        current_coverage: 현재 가입 담보 정보
        has_hemorrhage: 뇌출혈 동반 여부
        has_infarction: 뇌경색 동반 여부
    
    Returns:
        dict: 보장 격차 분석 결과
    """
    cerebrovascular_full = current_coverage.get("cerebrovascular_full", False)
    cerebral_hemorrhage = current_coverage.get("cerebral_hemorrhage", False)
    cerebral_infarction = current_coverage.get("cerebral_infarction", False)
    
    # 보장 상태 분석
    if cerebrovascular_full:
        coverage_status = "covered"
        denial_risk = "low"
        alert_message = "✅ 뇌혈관질환 전체 담보 가입: 모야모야병(I67.5) 보장 가능"
    elif (has_hemorrhage and cerebral_hemorrhage) or (has_infarction and cerebral_infarction):
        coverage_status = "conditional"
        denial_risk = "medium"
        alert_message = "⚡ 조건부 보장: 뇌출혈/뇌경색 동반 시 해당 담보로 청구 가능"
    else:
        coverage_status = "denied"
        denial_risk = "critical"
        alert_message = "⚠️ 부지급 리스크: 모야모야병(I67.5) 단독 진단 시 뇌출혈/뇌경색 담보에서 제외 가능"
    
    # 방어 전략
    defense_strategy = f"""
모야모야병(I67.5) 보장 격차 방어 전략:

1. 현재 보장 상태
   - 뇌혈관질환 전체 담보: {'가입' if cerebrovascular_full else '미가입'}
   - 뇌출혈 담보: {'가입' if cerebral_hemorrhage else '미가입'}
   - 뇌경색 담보: {'가입' if cerebral_infarction else '미가입'}
   - 뇌출혈 동반: {'있음' if has_hemorrhage else '없음'}
   - 뇌경색 동반: {'있음' if has_infarction else '없음'}

2. 보장 격차 분석
   - 보장 상태: {coverage_status}
   - 부지급 리스크: {denial_risk}

3. 방어 논리
   - 약관에 'I67.5 제외' 명시 없음 → 작성자 불이익 원칙 적용
   - 모야모야병은 뇌출혈/뇌경색의 원인 질환 → 인과관계 강조
   - 혈관우회술 비용 2,500만원 → 고액 치료비 근거
   - 희귀질환 특성상 조기 치료 필수 → 보험 보장 필요성 강조

4. 권고사항
   - {'뇌혈관질환 전체 담보(I60~I69) 추가 가입 필수' if not cerebrovascular_full else '현재 보장 유지'}
"""
    
    recommendations = []
    if not cerebrovascular_full:
        recommendations.append("⚠️ 긴급: 뇌혈관질환 전체 담보(I60~I69) 추가 가입 필수")
        recommendations.append("모야모야병은 뇌출혈/뇌경색으로 진행 가능 → 전체 담보 필요")
    
    if has_hemorrhage or has_infarction:
        recommendations.append("✅ 뇌출혈/뇌경색 동반 시 해당 담보로 청구 가능")
        recommendations.append("진단서에 I60~I63 코드 병기 요청")
    
    return {
        "code": "I67.5",
        "disease_name": "모야모야병",
        "coverage_status": coverage_status,
        "denial_risk": denial_risk,
        "has_hemorrhage": has_hemorrhage,
        "has_infarction": has_infarction,
        "defense_strategy": defense_strategy,
        "recommendations": recommendations,
        "alert_message": alert_message,
        "surgery_cost": MOYAMOYA_DISEASE_DATA["surgery_cost"]
    }


# ══════════════════════════════════════════════════════════════════════════════
# [3] 의사 소견 요청서 템플릿 생성
# ══════════════════════════════════════════════════════════════════════════════

def generate_physician_statement_template(
    disease_code: str,
    patient_name: str = "환자명",
    specific_request: str = ""
) -> str:
    """
    질환별 의사 소견 요청서 템플릿 생성
    
    Args:
        disease_code: KCD 코드 (예: "I63.8", "I67.5")
        patient_name: 환자 이름
        specific_request: 특정 요청 사항
    
    Returns:
        str: 의사 소견 요청서 템플릿
    """
    if disease_code in ["I63.8", "I63.9"]:
        template = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
의사 소견 요청서 (열공성 뇌경색)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

환자명: {patient_name}
진단명: 열공성 뇌경색 (Lacunar infarction)
KCD 코드: {disease_code}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
요청 사항
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

다음 사항에 대한 전문의 소견을 부탁드립니다:

1. 영상 검사 결과
   - MRI 영상상 확인된 병변의 위치 및 크기(cm)를 구체적으로 명시해 주세요.
   - 병변 크기: _____ cm

2. 신경학적 검사 결과
   - NIHSS(미국 국립보건원 뇌졸중 척도) 점수: _____ 점
   - 신경학적 결손 소견 (운동 기능, 감각 기능, 언어 기능, 인지 기능 등):
     
     

3. 일상생활 제한 사항
   - 보행 능력: □ 정상  □ 제한적  □ 불가능
   - 언어 기능: □ 정상  □ 제한적  □ 불가능
   - 인지 기능: □ 정상  □ 제한적  □ 불가능
   - 기타 일상생활 제한 사항:
     
     

4. 재발 가능성 및 예후
   - 재발 가능성: □ 높음  □ 중간  □ 낮음
   - 향후 다발성 뇌경색 또는 혈관성 치매로 진행 가능성:
     
     

5. KCD 코드 확정
   - 본 환자의 진단이 뇌경색(I63)에 해당함을 확인합니다.
   - 서명: _______________  날짜: _______________

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
참고 사항
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

보험 청구 시 병변 크기가 작다는 이유로 부지급될 수 있으나, 약관에는 크기 제한이
명시되어 있지 않으며, 신경학적 결손이 있는 경우 보험금 지급 대상입니다.

따라서 신경학적 검사 결과 및 일상생활 제한 사항을 상세히 기술해 주시면
보험금 청구에 큰 도움이 됩니다.

{specific_request if specific_request else ''}
"""
    
    elif disease_code == "I67.5":
        template = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
의사 소견 요청서 (모야모야병)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

환자명: {patient_name}
진단명: 모야모야병 (Moyamoya disease)
KCD 코드: I67.5

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
요청 사항
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

다음 사항에 대한 전문의 소견을 부탁드립니다:

1. 진단 근거
   - 뇌혈관 조영술(angiography) 또는 MRA 소견:
     
     
   - 모야모야 혈관(moyamoya vessels) 확인 여부: □ 확인  □ 미확인

2. 동반 질환
   - 뇌출혈(I60~I62) 동반: □ 있음  □ 없음
     - 있는 경우 KCD 코드: _____
   - 뇌경색(I63) 동반: □ 있음  □ 없음
     - 있는 경우 KCD 코드: _____

3. 치료 계획
   - 혈관우회술(bypass surgery) 필요 여부: □ 필요  □ 불필요
   - 예상 수술 비용: _______________

4. 예후 및 합병증
   - 향후 뇌출혈 또는 뇌경색 발생 가능성: □ 높음  □ 중간  □ 낮음
   - 기타 합병증:
     
     

5. KCD 코드 확정
   - 본 환자의 진단이 모야모야병(I67.5)에 해당함을 확인합니다.
   - 동반 질환이 있는 경우 해당 KCD 코드도 병기해 주세요.
   - 서명: _______________  날짜: _______________

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
참고 사항
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

모야모야병은 희귀질환으로, 뇌출혈/뇌경색 담보에서 제외될 수 있습니다.
따라서 뇌출혈 또는 뇌경색이 동반된 경우 해당 KCD 코드를 병기해 주시면
보험금 청구에 큰 도움이 됩니다.

{specific_request if specific_request else ''}
"""
    
    else:
        template = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
의사 소견 요청서
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

환자명: {patient_name}
KCD 코드: {disease_code}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
요청 사항
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{specific_request if specific_request else '진단 근거 및 치료 계획에 대한 소견을 부탁드립니다.'}

서명: _______________  날짜: _______________
"""
    
    return template.strip()
