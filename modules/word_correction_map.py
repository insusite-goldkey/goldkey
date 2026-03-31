# ══════════════════════════════════════════════════════════════════════════════
# [GP-ZERO-TRUST] 단어 교정 딕셔너리
# AI 환각(Hallucination)으로 인한 오타 자동 교정 맵
# ══════════════════════════════════════════════════════════════════════════════

"""
Zero-Trust 데이터 무결성 파이프라인 - Step 3 검증 레이어
AI가 자주 오타를 내는 금융/의료 전문 용어를 강제 교정
"""

# ── 금융/보험 용어 교정 맵 ────────────────────────────────────────────────
FINANCIAL_CORRECTION_MAP = {
    # 보험사 오타
    "보병사": "보험사",
    "고용사": "보험사",
    "보현사": "보험사",
    
    # 금융 용어 오타
    "손이익": "순이익",
    "조리니합": "순이익",
    "실적악화": "실적 악화",
    "영업익": "영업이익",
    "당기순익": "당기순이익",
    
    # 보험 상품 용어
    "실손의료비": "실손의료비",
    "진단비": "진단비",
    "입원비": "입원비",
    "수술비": "수술비",
    
    # 보험사명 오타 (주요 보험사)
    "삼성생병": "삼성생명",
    "한화생병": "한화생명",
    "교보생병": "교보생명",
    "KB손해보현": "KB손해보험",
    "현대해상": "현대해상",
    "메리츠화재": "메리츠화재",
}

# ── 의료 용어 교정 맵 ────────────────────────────────────────────────────
MEDICAL_CORRECTION_MAP = {
    # 질병명 오타
    "당뇨": "당뇨병",
    "고혈압": "고혈압",
    "암": "암",
    "뇌졸증": "뇌졸중",
    "심근경색": "급성심근경색",
    
    # 의료 기관 오타
    "병원": "병원",
    "의원": "의원",
    "종합병원": "종합병원",
    "대학병원": "대학병원",
    
    # 의료 행위
    "진료": "진료",
    "수술": "수술",
    "입원": "입원",
    "통원": "통원",
}

# ── 통합 교정 맵 ────────────────────────────────────────────────────────
WORD_CORRECTION_MAP = {
    **FINANCIAL_CORRECTION_MAP,
    **MEDICAL_CORRECTION_MAP,
}

# ── 교정 함수 ────────────────────────────────────────────────────────
def apply_word_correction(text: str, correction_map: dict = None) -> tuple[str, list[str]]:
    """
    텍스트에 단어 교정 맵을 적용
    
    Args:
        text: 교정할 텍스트
        correction_map: 사용할 교정 맵 (기본값: WORD_CORRECTION_MAP)
    
    Returns:
        (교정된 텍스트, 교정된 단어 목록)
    """
    if correction_map is None:
        correction_map = WORD_CORRECTION_MAP
    
    corrected_text = text
    corrections_made = []
    
    for wrong, correct in correction_map.items():
        if wrong in corrected_text:
            corrected_text = corrected_text.replace(wrong, correct)
            corrections_made.append(f"{wrong} → {correct}")
    
    return corrected_text, corrections_made


def get_correction_summary(corrections: list[str]) -> str:
    """
    교정 내역을 사용자 친화적인 메시지로 변환
    
    Args:
        corrections: 교정된 단어 목록
    
    Returns:
        교정 요약 메시지
    """
    if not corrections:
        return ""
    
    summary = "⚠️ AI 오타가 시스템에 의해 자동 교정되었습니다. 확인 바랍니다.\n\n"
    summary += "**교정 내역:**\n"
    for correction in corrections:
        summary += f"- {correction}\n"
    
    return summary
