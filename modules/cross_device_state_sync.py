# -*- coding: utf-8 -*-
"""
Cross-Device State Sync (기기 간 작업 상태 동기화)
State Persistence: 특정 고객의 전략판 즉시 복원

작성일: 2026-03-31
목적: 제로 프릭션 접속 + 실시간 세션 동기화
"""

import streamlit as st
from typing import Dict, Optional, Any
import json
from datetime import datetime
import uuid


class CrossDeviceStateSync:
    """
    Cross-Device State Sync
    
    핵심 기능:
    1. 작업 상태 실시간 동기화 (Supabase)
    2. 기기 전환 시 즉시 복원
    3. 특정 고객 전략판 보존
    4. Adaptive Auth 통합
    """
    
    def __init__(self):
        """초기화"""
        self.session_key = "cross_device_sync"
        
        # 세션 초기화
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = {
                "device_id": self._get_or_create_device_id(),
                "last_sync_time": None,
                "sync_enabled": True
            }
    
    def _get_or_create_device_id(self) -> str:
        """기기 ID 생성 또는 조회"""
        if "device_id" not in st.session_state:
            st.session_state["device_id"] = str(uuid.uuid4())
        return st.session_state["device_id"]
    
    def save_work_state(
        self,
        user_id: str,
        state_type: str,
        state_data: Dict[str, Any]
    ) -> bool:
        """
        작업 상태 저장 (Supabase)
        
        Args:
            user_id: 사용자(설계사) ID
            state_type: 상태 유형 (draft_report, analysis_in_progress, customer_form 등)
            state_data: 상태 데이터
        
        Returns:
            저장 성공 여부
        """
        try:
            from db_utils import get_supabase_client
            
            supabase = get_supabase_client()
            device_id = self._get_or_create_device_id()
            
            # Upsert (user_id, state_type 조합으로 중복 방지)
            result = supabase.table("agent_work_state").upsert({
                "user_id": user_id,
                "state_type": state_type,
                "state_data": state_data,
                "device_id": device_id,
                "updated_at": datetime.now().isoformat()
            }, on_conflict="user_id,state_type").execute()
            
            # 세션 업데이트
            st.session_state[self.session_key]["last_sync_time"] = datetime.now()
            
            return True
            
        except Exception as e:
            st.error(f"작업 상태 저장 실패: {e}")
            return False
    
    def load_work_state(
        self,
        user_id: str,
        state_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        작업 상태 로드 (Supabase)
        
        Args:
            user_id: 사용자(설계사) ID
            state_type: 상태 유형
        
        Returns:
            상태 데이터 (없으면 None)
        """
        try:
            from db_utils import get_supabase_client
            
            supabase = get_supabase_client()
            
            result = supabase.table("agent_work_state").select("*").eq(
                "user_id", user_id
            ).eq(
                "state_type", state_type
            ).order("updated_at", desc=True).limit(1).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]["state_data"]
            
            return None
            
        except Exception as e:
            st.error(f"작업 상태 로드 실패: {e}")
            return None
    
    def restore_customer_strategy_board(
        self,
        user_id: str,
        customer_id: str
    ) -> bool:
        """
        특정 고객의 전략판 복원
        
        Args:
            user_id: 사용자(설계사) ID
            customer_id: 고객 ID
        
        Returns:
            복원 성공 여부
        """
        state_type = f"customer_strategy_{customer_id}"
        
        # 작업 상태 로드
        state_data = self.load_work_state(user_id, state_type)
        
        if not state_data:
            return False
        
        # 세션 복원
        try:
            # 분석 결과 복원
            if "analysis_results" in state_data:
                st.session_state["analysis_results"] = state_data["analysis_results"]
            
            # 스캔 데이터 복원
            if "scan_data" in state_data:
                st.session_state["scan_data"] = state_data["scan_data"]
            
            # 고객 정보 복원
            if "customer_info" in state_data:
                st.session_state["customer_info"] = state_data["customer_info"]
            
            # 전략 데이터 복원
            if "strategy_data" in state_data:
                st.session_state["strategy_data"] = state_data["strategy_data"]
            
            # 마스터 대시보드 상태 복원
            if "scan_master_dashboard" in state_data:
                st.session_state["scan_master_dashboard"] = state_data["scan_master_dashboard"]
            
            st.success(f"✅ {state_data.get('customer_name', '고객')}님의 전략판이 복원되었습니다")
            
            return True
            
        except Exception as e:
            st.error(f"전략판 복원 실패: {e}")
            return False
    
    def auto_save_current_state(
        self,
        user_id: str,
        customer_id: Optional[str] = None
    ):
        """
        현재 작업 상태 자동 저장
        
        Args:
            user_id: 사용자(설계사) ID
            customer_id: 고객 ID (선택)
        """
        if not st.session_state[self.session_key].get("sync_enabled", True):
            return
        
        # 저장할 상태 데이터 수집
        state_data = {}
        
        # 분석 결과
        if "analysis_results" in st.session_state:
            state_data["analysis_results"] = st.session_state["analysis_results"]
        
        # 스캔 데이터
        if "scan_data" in st.session_state:
            state_data["scan_data"] = st.session_state["scan_data"]
        
        # 고객 정보
        if "customer_info" in st.session_state:
            state_data["customer_info"] = st.session_state["customer_info"]
        
        # 전략 데이터
        if "strategy_data" in st.session_state:
            state_data["strategy_data"] = st.session_state["strategy_data"]
        
        # 마스터 대시보드 상태
        if "scan_master_dashboard" in st.session_state:
            state_data["scan_master_dashboard"] = st.session_state["scan_master_dashboard"]
        
        # 상태 유형 결정
        if customer_id:
            state_type = f"customer_strategy_{customer_id}"
            state_data["customer_id"] = customer_id
            if "customer_info" in st.session_state:
                state_data["customer_name"] = st.session_state["customer_info"].get("name", "")
        else:
            state_type = "general_work_state"
        
        # 저장
        self.save_work_state(user_id, state_type, state_data)
    
    def render_sync_status(self):
        """동기화 상태 표시"""
        sync_data = st.session_state[self.session_key]
        
        if sync_data.get("last_sync_time"):
            last_sync = sync_data["last_sync_time"]
            time_diff = (datetime.now() - last_sync).total_seconds()
            
            if time_diff < 60:
                status_text = "방금 전"
                status_color = "#00d4ff"
            elif time_diff < 3600:
                status_text = f"{int(time_diff // 60)}분 전"
                status_color = "#00d4ff"
            else:
                status_text = f"{int(time_diff // 3600)}시간 전"
                status_color = "#8b9dc3"
            
            st.markdown(
                f"""
                <div style='text-align:right;padding:8px;'>
                    <span style='color:{status_color};font-size:12px;'>
                        ☁️ 마지막 동기화: {status_text}
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )


# ══════════════════════════════════════════════════════════════════════════════
# Streamlit UI 통합 함수
# ══════════════════════════════════════════════════════════════════════════════

def enable_cross_device_sync(user_id: str, customer_id: Optional[str] = None):
    """
    Cross-Device Sync 활성화
    
    사용법:
        from modules.cross_device_state_sync import enable_cross_device_sync
        enable_cross_device_sync(user_id="agent_123", customer_id="person_456")
    
    Args:
        user_id: 사용자(설계사) ID
        customer_id: 고객 ID (선택)
    """
    sync = CrossDeviceStateSync()
    
    # 자동 저장 (5분마다)
    if "last_auto_save" not in st.session_state:
        st.session_state["last_auto_save"] = datetime.now()
    
    time_since_save = (datetime.now() - st.session_state["last_auto_save"]).total_seconds()
    
    if time_since_save > 300:  # 5분
        sync.auto_save_current_state(user_id, customer_id)
        st.session_state["last_auto_save"] = datetime.now()
    
    # 동기화 상태 표시
    sync.render_sync_status()


def restore_previous_session(user_id: str, customer_id: str) -> bool:
    """
    이전 세션 복원
    
    사용법:
        from modules.cross_device_state_sync import restore_previous_session
        if restore_previous_session(user_id="agent_123", customer_id="person_456"):
            st.success("이전 작업이 복원되었습니다")
    
    Args:
        user_id: 사용자(설계사) ID
        customer_id: 고객 ID
    
    Returns:
        복원 성공 여부
    """
    sync = CrossDeviceStateSync()
    return sync.restore_customer_strategy_board(user_id, customer_id)
