"""
[GP-DATA-INTEGRITY] 데이터 무결성 가드 - 내용이 많은 쪽 보존 원칙
동시 로그인 대응: 핸드폰과 태블릿이 동시에 로그인된 상태에서 데이터 저장 시,
단순히 시간순으로 덮어씌우지 않고 '텍스트 양이 더 많거나 정보가 더 구체적인 버전(The Richer Data)'을 우선 보존.
"""
from __future__ import annotations
from typing import Any, Optional


def calculate_data_richness(data: dict) -> int:
    """
    데이터의 풍부함(richness) 점수를 계산.
    
    점수 계산 기준:
    - 텍스트 필드의 총 길이
    - 비어있지 않은 필드 개수
    - 특정 중요 필드(memo, address, job 등)의 가중치
    
    Args:
        data: 평가할 데이터 딕셔너리
    
    Returns:
        풍부함 점수 (정수)
    """
    if not isinstance(data, dict):
        return 0
    
    score = 0
    
    # 중요 필드 가중치 맵
    important_fields = {
        'memo': 3,           # 메모는 가장 중요
        'address': 2,        # 주소
        'job': 2,            # 직업/소속
        'company': 2,        # 법인상호
        'business_number': 2, # 사업자번호
        'birth_date': 1,     # 생년월일
        'gender': 1,         # 성별
        'contact': 1,        # 연락처
    }
    
    for key, value in data.items():
        if value is None or value == '':
            continue
        
        # 비어있지 않은 필드 기본 점수
        score += 1
        
        # 텍스트 길이 점수
        if isinstance(value, str):
            text_length = len(value.strip())
            score += text_length // 10  # 10자당 1점
            
            # 중요 필드 가중치 적용
            weight = important_fields.get(key, 1)
            score += text_length * weight // 20  # 중요 필드는 추가 가산점
    
    return score


def merge_richer_data(
    existing_data: dict,
    new_data: dict,
    preserve_fields: Optional[list[str]] = None
) -> dict:
    """
    두 데이터를 비교하여 더 풍부한 데이터를 보존하며 병합.
    
    Args:
        existing_data: 기존 데이터
        new_data: 새로운 데이터
        preserve_fields: 항상 보존할 필드 목록 (기본값: ['person_id', 'agent_id', 'created_at'])
    
    Returns:
        병합된 데이터
    """
    if preserve_fields is None:
        preserve_fields = ['person_id', 'agent_id', 'created_at', 'id']
    
    # 기존 데이터가 없으면 새 데이터 반환
    if not existing_data:
        return new_data.copy() if new_data else {}
    
    # 새 데이터가 없으면 기존 데이터 반환
    if not new_data:
        return existing_data.copy()
    
    # 전체 풍부함 점수 비교
    existing_score = calculate_data_richness(existing_data)
    new_score = calculate_data_richness(new_data)
    
    # 병합 결과 초기화
    merged = existing_data.copy()
    
    # 필드별 병합
    for key in set(list(existing_data.keys()) + list(new_data.keys())):
        # 보존 필드는 기존 값 유지
        if key in preserve_fields:
            if key in existing_data:
                merged[key] = existing_data[key]
            continue
        
        existing_value = existing_data.get(key)
        new_value = new_data.get(key)
        
        # 둘 다 비어있으면 스킵
        if not existing_value and not new_value:
            continue
        
        # 기존 값이 없으면 새 값 사용
        if not existing_value:
            merged[key] = new_value
            continue
        
        # 새 값이 없으면 기존 값 유지
        if not new_value:
            merged[key] = existing_value
            continue
        
        # 둘 다 있는 경우: 더 긴 텍스트 선택
        if isinstance(existing_value, str) and isinstance(new_value, str):
            existing_len = len(existing_value.strip())
            new_len = len(new_value.strip())
            
            if new_len > existing_len:
                merged[key] = new_value
            else:
                merged[key] = existing_value
        else:
            # 문자열이 아닌 경우: 전체 점수 기준으로 선택
            if new_score > existing_score:
                merged[key] = new_value
            else:
                merged[key] = existing_value
    
    # updated_at 필드는 항상 최신 시간으로 갱신
    if 'updated_at' in new_data:
        merged['updated_at'] = new_data['updated_at']
    
    return merged


def safe_upsert_with_integrity(
    person_id: str,
    agent_id: str,
    new_data: dict,
    fetch_existing_func,
    save_func
) -> dict:
    """
    데이터 무결성을 보장하며 안전하게 upsert.
    
    Args:
        person_id: 고객 ID
        agent_id: 설계사 ID
        new_data: 저장할 새 데이터
        fetch_existing_func: 기존 데이터를 가져오는 함수 (person_id, agent_id) -> dict
        save_func: 데이터를 저장하는 함수 (merged_data) -> bool
    
    Returns:
        저장된 최종 데이터
    """
    try:
        # 기존 데이터 조회
        existing_data = fetch_existing_func(person_id, agent_id)
        
        # 데이터 병합 (더 풍부한 쪽 보존)
        merged_data = merge_richer_data(existing_data, new_data)
        
        # 저장
        success = save_func(merged_data)
        
        if success:
            return merged_data
        else:
            return existing_data or new_data
    
    except Exception as e:
        # 오류 발생 시 새 데이터라도 저장 시도
        try:
            save_func(new_data)
            return new_data
        except Exception:
            return existing_data if existing_data else new_data
