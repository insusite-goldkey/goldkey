"""
[GP-SEC §MULTIDEVICE] 멀티디바이스 동기화 및 충돌 방어 모듈
Optimistic Concurrency Control + Richer Data Wins

Author: Goldkey AI Masters 2026
Created: 2026-03-28
"""
from __future__ import annotations
import datetime
from typing import Optional, Dict, Any, Tuple


def compare_timestamps(
    local_updated: str,
    remote_updated: str
) -> int:
    """
    타임스탬프 비교
    
    Args:
        local_updated: 로컬(세션) 데이터의 updated_at (ISO 8601)
        remote_updated: 원격(DB) 데이터의 updated_at (ISO 8601)
    
    Returns:
        int: -1 (로컬이 오래됨), 0 (동일), 1 (로컬이 최신)
    """
    if not local_updated or not remote_updated:
        return 0
    
    try:
        local_dt = datetime.datetime.fromisoformat(local_updated.replace("Z", "+00:00"))
        remote_dt = datetime.datetime.fromisoformat(remote_updated.replace("Z", "+00:00"))
        
        if local_dt < remote_dt:
            return -1
        elif local_dt > remote_dt:
            return 1
        else:
            return 0
    except Exception:
        return 0


def calculate_payload_size(data: Dict[str, Any]) -> int:
    """
    데이터 페이로드 크기 계산 (Richer Data 판별용)
    
    Args:
        data: 데이터 딕셔너리
    
    Returns:
        int: 페이로드 크기 (바이트)
    """
    import json
    try:
        return len(json.dumps(data, ensure_ascii=False))
    except Exception:
        return 0


def check_conflict(
    local_data: Dict[str, Any],
    remote_data: Dict[str, Any],
    conflict_threshold_seconds: int = 5
) -> Tuple[bool, str]:
    """
    데이터 충돌 감지 (Optimistic Concurrency Control)
    
    Args:
        local_data: 로컬(세션) 데이터
        remote_data: 원격(DB) 데이터
        conflict_threshold_seconds: 충돌 판정 임계값 (초)
    
    Returns:
        (충돌 여부, 충돌 사유)
        
    충돌 판정 기준:
        1. 원격 데이터가 더 최신 (타임스탬프 비교)
        2. 원격 데이터가 더 풍부 (페이로드 크기 비교)
    """
    if not remote_data:
        # 원격 데이터 없음 → 충돌 없음 (신규 생성)
        return (False, "")
    
    # 1. 타임스탬프 비교
    local_updated = local_data.get("updated_at", "")
    remote_updated = remote_data.get("updated_at", "")
    
    ts_cmp = compare_timestamps(local_updated, remote_updated)
    
    if ts_cmp == -1:
        # 로컬이 오래됨 → 원격이 더 최신
        return (True, "다른 기기에서 업데이트된 최신 데이터가 존재합니다.")
    
    # 2. Richer Data Wins (페이로드 크기 비교)
    local_size = calculate_payload_size(local_data)
    remote_size = calculate_payload_size(remote_data)
    
    if remote_size > local_size * 1.2:  # 20% 이상 차이
        # 원격 데이터가 훨씬 풍부함
        return (True, "다른 기기에서 더 상세한 정보가 입력되었습니다.")
    
    # 충돌 없음
    return (False, "")


def merge_data_smart(
    local_data: Dict[str, Any],
    remote_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    스마트 데이터 병합 (충돌 해결)
    
    Args:
        local_data: 로컬(세션) 데이터
        remote_data: 원격(DB) 데이터
    
    Returns:
        병합된 데이터
        
    병합 규칙:
        - 비어있지 않은 필드 우선
        - 타임스탬프는 최신 것 사용
        - 페이로드가 더 큰 쪽 우선
    """
    merged = remote_data.copy()
    
    for key, local_value in local_data.items():
        remote_value = remote_data.get(key)
        
        # 로컬 값이 있고 원격 값이 없으면 로컬 사용
        if local_value and not remote_value:
            merged[key] = local_value
        # 둘 다 있으면 더 긴 것 사용 (문자열인 경우)
        elif isinstance(local_value, str) and isinstance(remote_value, str):
            if len(local_value) > len(remote_value):
                merged[key] = local_value
    
    # updated_at은 항상 현재 시간으로 갱신
    merged["updated_at"] = datetime.datetime.now().isoformat()
    
    return merged


def check_session_timeout(
    last_activity_time: Optional[str],
    timeout_minutes: int = 60
) -> bool:
    """
    세션 타임아웃 확인
    
    Args:
        last_activity_time: 마지막 활동 시간 (ISO 8601)
        timeout_minutes: 타임아웃 시간 (분)
    
    Returns:
        bool: True (타임아웃), False (유효)
    """
    if not last_activity_time:
        return False
    
    try:
        last_dt = datetime.datetime.fromisoformat(last_activity_time.replace("Z", "+00:00"))
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        
        elapsed = (now_dt - last_dt).total_seconds() / 60  # 분 단위
        
        return elapsed > timeout_minutes
    except Exception:
        return False


def update_activity_time() -> str:
    """
    현재 시간을 활동 시간으로 반환
    
    Returns:
        str: 현재 시간 (ISO 8601)
    """
    return datetime.datetime.now(datetime.timezone.utc).isoformat()
