# ══════════════════════════════════════════════════════════════════════════════
# [GP-ZERO-TRUST] 공통 검증 레이어
# Zero-Trust 데이터 무결성 파이프라인 - Step 3 검증 레이어
# ══════════════════════════════════════════════════════════════════════════════

"""
Zero-Trust 아키텍처 핵심 검증 모듈

모든 외부 데이터(뉴스, OCR, 크롤링)는 이 검증 레이어를 통과해야 함
- 단어 자동 교정 (WORD_CORRECTION_MAP)
- 수치/날짜 형식 검증
- 타입 검증
"""

import re
from typing import Any, Dict, List, Tuple, Optional
from datetime import datetime
from pydantic import BaseModel, ValidationError

from modules.word_correction_map import (
    WORD_CORRECTION_MAP,
    apply_word_correction,
    get_correction_summary
)


# ══════════════════════════════════════════════════════════════════════════════
# 검증 결과 모델
# ══════════════════════════════════════════════════════════════════════════════

class ValidationResult(BaseModel):
    """검증 결과 컨테이너"""
    is_valid: bool
    data: Dict[str, Any]
    corrections: List[str] = []
    errors: List[str] = []
    warnings: List[str] = []


# ══════════════════════════════════════════════════════════════════════════════
# 수치 검증 함수
# ══════════════════════════════════════════════════════════════════════════════

def validate_korean_amount(amount: str) -> Tuple[bool, Optional[str]]:
    """
    한국어 금액 형식 검증
    
    Args:
        amount: 검증할 금액 문자열 (예: "12조원", "3000억원")
    
    Returns:
        (검증 성공 여부, 에러 메시지)
    """
    # 허용 패턴: 숫자 + (조|억|만|원)
    pattern = r"^-?\d+(\.\d+)?(조|억|만|원)$"
    
    if not re.match(pattern, amount):
        return False, f"금액 형식 오류: '{amount}' (예: 12조원, 3000억원)"
    
    return True, None


def validate_percentage(rate: str) -> Tuple[bool, Optional[str]]:
    """
    퍼센트 형식 검증
    
    Args:
        rate: 검증할 퍼센트 문자열 (예: "15%", "-3.5%")
    
    Returns:
        (검증 성공 여부, 에러 메시지)
    """
    # 허용 패턴: 숫자 + %
    pattern = r"^-?\d+(\.\d+)?%$"
    
    if not re.match(pattern, rate):
        return False, f"퍼센트 형식 오류: '{rate}' (예: 15%, -3.5%)"
    
    return True, None


def validate_date_format(date_str: str, format: str = "%Y-%m-%d") -> Tuple[bool, Optional[str]]:
    """
    날짜 형식 검증
    
    Args:
        date_str: 검증할 날짜 문자열
        format: 날짜 형식 (기본값: YYYY-MM-DD)
    
    Returns:
        (검증 성공 여부, 에러 메시지)
    """
    try:
        datetime.strptime(date_str, format)
        return True, None
    except ValueError:
        return False, f"날짜 형식 오류: '{date_str}' (예: 2026-03-30)"


# ══════════════════════════════════════════════════════════════════════════════
# 통합 검증 함수
# ══════════════════════════════════════════════════════════════════════════════

def validate_financial_data(data: Dict[str, Any]) -> ValidationResult:
    """
    금융 데이터 검증 (뉴스, 공시 등)
    
    Args:
        data: 검증할 데이터 딕셔너리
    
    Returns:
        ValidationResult 객체
    """
    result = ValidationResult(is_valid=True, data=data.copy())
    
    # Step 1: 단어 자동 교정
    for key, value in data.items():
        if isinstance(value, str):
            corrected_value, corrections = apply_word_correction(value)
            if corrections:
                result.data[key] = corrected_value
                result.corrections.extend(corrections)
                result.warnings.append(f"필드 '{key}'에서 자동 교정 발생")
    
    # Step 2: 금액 검증
    if "profit" in result.data:
        is_valid, error = validate_korean_amount(result.data["profit"])
        if not is_valid:
            result.is_valid = False
            result.errors.append(error)
    
    if "revenue" in result.data:
        is_valid, error = validate_korean_amount(result.data["revenue"])
        if not is_valid:
            result.is_valid = False
            result.errors.append(error)
    
    # Step 3: 퍼센트 검증
    if "change_rate" in result.data:
        is_valid, error = validate_percentage(result.data["change_rate"])
        if not is_valid:
            result.is_valid = False
            result.errors.append(error)
    
    # Step 4: 날짜 검증
    if "publish_date" in result.data and result.data["publish_date"]:
        is_valid, error = validate_date_format(result.data["publish_date"])
        if not is_valid:
            result.is_valid = False
            result.errors.append(error)
    
    return result


def validate_medical_data(data: Dict[str, Any]) -> ValidationResult:
    """
    의료 데이터 검증 (의무기록, 진단서 등)
    
    Args:
        data: 검증할 데이터 딕셔너리
    
    Returns:
        ValidationResult 객체
    """
    result = ValidationResult(is_valid=True, data=data.copy())
    
    # Step 1: 단어 자동 교정
    for key, value in data.items():
        if isinstance(value, str):
            corrected_value, corrections = apply_word_correction(value)
            if corrections:
                result.data[key] = corrected_value
                result.corrections.extend(corrections)
                result.warnings.append(f"필드 '{key}'에서 자동 교정 발생")
    
    # Step 2: 필수 필드 검증
    required_fields = ["patient_name", "diagnosis", "hospital"]
    for field in required_fields:
        if field not in result.data or not result.data[field]:
            result.is_valid = False
            result.errors.append(f"필수 필드 누락: '{field}'")
    
    # Step 3: 날짜 검증
    if "treatment_date" in result.data and result.data["treatment_date"]:
        is_valid, error = validate_date_format(result.data["treatment_date"])
        if not is_valid:
            result.is_valid = False
            result.errors.append(error)
    
    return result


# ══════════════════════════════════════════════════════════════════════════════
# Pydantic 모델 검증 래퍼
# ══════════════════════════════════════════════════════════════════════════════

def validate_pydantic_model(
    model_class: type[BaseModel],
    data: Dict[str, Any]
) -> Tuple[Optional[BaseModel], ValidationResult]:
    """
    Pydantic 모델 검증 + Zero-Trust 검증 통합
    
    Args:
        model_class: Pydantic 모델 클래스
        data: 검증할 데이터
    
    Returns:
        (검증된 모델 인스턴스, ValidationResult)
    """
    result = ValidationResult(is_valid=True, data=data.copy())
    
    try:
        # Pydantic 모델 검증
        model_instance = model_class(**data)
        result.data = model_instance.dict()
        
        # Zero-Trust 추가 검증 (모델 타입에 따라 분기)
        if "profit" in result.data or "revenue" in result.data:
            # 금융 데이터
            validation = validate_financial_data(result.data)
        elif "patient_name" in result.data or "diagnosis" in result.data:
            # 의료 데이터
            validation = validate_medical_data(result.data)
        else:
            # 기본 검증 (단어 교정만)
            validation = ValidationResult(is_valid=True, data=result.data)
            for key, value in result.data.items():
                if isinstance(value, str):
                    corrected_value, corrections = apply_word_correction(value)
                    if corrections:
                        validation.data[key] = corrected_value
                        validation.corrections.extend(corrections)
        
        result.data = validation.data
        result.corrections = validation.corrections
        result.warnings = validation.warnings
        result.errors = validation.errors
        result.is_valid = validation.is_valid
        
        # 교정된 데이터로 모델 재생성
        if result.corrections:
            model_instance = model_class(**result.data)
        
        return model_instance, result
        
    except ValidationError as e:
        result.is_valid = False
        result.errors.append(f"Pydantic 검증 실패: {str(e)}")
        return None, result


# ══════════════════════════════════════════════════════════════════════════════
# UI 헬퍼 함수
# ══════════════════════════════════════════════════════════════════════════════

def render_validation_warnings(result: ValidationResult) -> None:
    """
    Streamlit UI에 검증 경고 렌더링
    
    Args:
        result: ValidationResult 객체
    """
    import streamlit as st
    
    # 자동 교정 경고
    if result.corrections:
        correction_summary = get_correction_summary(result.corrections)
        st.warning(correction_summary)
    
    # 일반 경고
    for warning in result.warnings:
        st.toast(f"⚠️ {warning}", icon="⚠️")


def render_validation_errors(result: ValidationResult) -> None:
    """
    Streamlit UI에 검증 에러 렌더링
    
    Args:
        result: ValidationResult 객체
    """
    import streamlit as st
    
    if result.errors:
        st.error("❌ **검증 실패**\n\n다음 항목을 수정해주세요:")
        for error in result.errors:
            st.markdown(f"- {error}")
