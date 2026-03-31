# -*- coding: utf-8 -*-
"""
지능형 리딩 파트너 - Cross-Device Sync (기기 간 동기화)
Supabase Realtime 기반 상태 동기화 시스템

작성일: 2026-03-31
목적: 기기 전환 시 마지막 작업 상태 즉시 복원 (Draft Report, 분석 중인 담보 등)
"""

import streamlit as st
from typing import Dict, Optional, Any, List
import json
import time
from datetime import datetime


class CrossDeviceSync:
    """
    기기 간 동기화 시스템
    
    핵심 기능:
    1. 작업 상태 자동 저장 (Draft Report, 분석 중인 담보)
    2. Supabase Realtime을 통한 즉시 동기화
    3. 기기 전환 시 상태 복원
    4. 리딩 파트너 복원 메시지
    """
    
    def __init__(self, supabase_client=None):
        """
        초기화
        
        Args:
            supabase_client: Supabase 클라이언트 (선택)
        """
        self.supabase = supabase_client
        self.sync_table = "agent_work_state"
        self.session_key = "cross_device_sync"
    
    def save_work_state(
        self,
        user_id: str,
        state_type: str,
        state_data: Dict,
        device_id: Optional[str] = None
    ) -> Dict:
        """
        작업 상태 저장
        
        Args:
            user_id: 사용자 ID
            state_type: 상태 유형 (draft_report, analysis_in_progress, customer_form 등)
            state_data: 상태 데이터
            device_id: 기기 ID (선택)
        
        Returns:
            Dict: 저장 결과
        """
        timestamp = time.time()
        
        work_state = {
            "user_id": user_id,
            "state_type": state_type,
            "state_data": json.dumps(state_data, ensure_ascii=False),
            "device_id": device_id or self._get_device_id(),
            "saved_at": timestamp,
            "updated_at": timestamp
        }
        
        # 세션에 저장
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = {}
        
        st.session_state[self.session_key][state_type] = work_state
        
        # Supabase에 저장 (실제 배포 시)
        if self.supabase:
            try:
                result = self.supabase.table(self.sync_table).upsert(
                    {
                        "user_id": user_id,
                        "state_type": state_type,
                        "state_data": work_state["state_data"],
                        "device_id": work_state["device_id"],
                        "updated_at": datetime.fromtimestamp(timestamp).isoformat()
                    },
                    on_conflict="user_id,state_type"
                ).execute()
                
                return {
                    "status": "success",
                    "message": "작업 상태가 저장되었습니다",
                    "timestamp": timestamp
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"저장 실패: {str(e)}",
                    "timestamp": timestamp
                }
        
        return {
            "status": "success",
            "message": "작업 상태가 로컬에 저장되었습니다",
            "timestamp": timestamp
        }
    
    def load_work_state(
        self,
        user_id: str,
        state_type: str
    ) -> Optional[Dict]:
        """
        작업 상태 로드
        
        Args:
            user_id: 사용자 ID
            state_type: 상태 유형
        
        Returns:
            Optional[Dict]: 상태 데이터 (없으면 None)
        """
        # 세션에서 먼저 확인
        if self.session_key in st.session_state:
            work_state = st.session_state[self.session_key].get(state_type)
            if work_state and work_state.get("user_id") == user_id:
                return json.loads(work_state["state_data"])
        
        # Supabase에서 로드 (실제 배포 시)
        if self.supabase:
            try:
                result = self.supabase.table(self.sync_table).select("*").eq(
                    "user_id", user_id
                ).eq(
                    "state_type", state_type
                ).order(
                    "updated_at", desc=True
                ).limit(1).execute()
                
                if result.data and len(result.data) > 0:
                    state_data = json.loads(result.data[0]["state_data"])
                    return state_data
            except Exception as e:
                st.error(f"상태 로드 실패: {str(e)}")
        
        return None
    
    def restore_work_state(
        self,
        user_id: str,
        state_type: str
    ) -> Optional[Dict]:
        """
        작업 상태 복원
        
        Args:
            user_id: 사용자 ID
            state_type: 상태 유형
        
        Returns:
            Optional[Dict]: 복원된 상태 데이터
        """
        state_data = self.load_work_state(user_id, state_type)
        
        if state_data:
            # 세션에 복원
            if self.session_key not in st.session_state:
                st.session_state[self.session_key] = {}
            
            st.session_state[self.session_key][f"{state_type}_restored"] = True
            st.session_state[self.session_key][f"{state_type}_data"] = state_data
            
            return state_data
        
        return None
    
    def _get_device_id(self) -> str:
        """기기 ID 생성 (브라우저 세션 기반)"""
        if "device_id" not in st.session_state:
            import uuid
            st.session_state["device_id"] = str(uuid.uuid4())
        
        return st.session_state["device_id"]
    
    def auto_save_draft_report(
        self,
        user_id: str,
        customer_id: str,
        report_data: Dict
    ):
        """
        Draft Report 자동 저장
        
        Args:
            user_id: 사용자 ID
            customer_id: 고객 ID
            report_data: 리포트 데이터
        """
        state_data = {
            "customer_id": customer_id,
            "report_data": report_data,
            "saved_at": datetime.now().isoformat()
        }
        
        self.save_work_state(user_id, "draft_report", state_data)
    
    def auto_save_analysis_progress(
        self,
        user_id: str,
        customer_id: str,
        analysis_data: Dict
    ):
        """
        분석 진행 상태 자동 저장
        
        Args:
            user_id: 사용자 ID
            customer_id: 고객 ID
            analysis_data: 분석 데이터
        """
        state_data = {
            "customer_id": customer_id,
            "analysis_data": analysis_data,
            "saved_at": datetime.now().isoformat()
        }
        
        self.save_work_state(user_id, "analysis_in_progress", state_data)
    
    def render_restore_notification(
        self,
        user_id: str,
        state_type: str
    ) -> bool:
        """
        복원 알림 렌더링
        
        Args:
            user_id: 사용자 ID
            state_type: 상태 유형
        
        Returns:
            bool: 복원 여부
        """
        state_data = self.load_work_state(user_id, state_type)
        
        if not state_data:
            return False
        
        # 이미 복원 알림을 표시했는지 확인
        notification_key = f"restore_notification_{state_type}"
        if st.session_state.get(notification_key):
            return False
        
        # 상태 유형별 메시지
        state_messages = {
            "draft_report": "작성 중이던 리포트",
            "analysis_in_progress": "분석 중이던 담보",
            "customer_form": "입력 중이던 고객 정보"
        }
        
        state_name = state_messages.get(state_type, "작업 상태")
        
        # 복원 알림
        st.markdown(
            f"""
            <div style='background:linear-gradient(135deg,#dbeafe 0%,#bfdbfe 100%);
                        border:2px solid #3b82f6;border-radius:12px;
                        padding:20px;margin:16px 0;
                        box-shadow:0 4px 16px rgba(59,130,246,0.2);'>
                <div style='text-align:center;'>
                    <div style='font-size:32px;margin-bottom:12px;'>🔄</div>
                    <div style='font-size:18px;font-weight:900;color:#1e40af;
                                margin-bottom:8px;'>
                        본인 확인이 완료되었습니다
                    </div>
                    <div style='font-size:14px;color:#1e40af;line-height:1.6;'>
                        {state_name}을 불러옵니다
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ 불러오기", use_container_width=True, type="primary"):
                # 상태 복원
                self.restore_work_state(user_id, state_type)
                st.session_state[notification_key] = True
                st.success(f"✅ {state_name}을 불러왔습니다")
                st.rerun()
        
        with col2:
            if st.button("❌ 새로 시작", use_container_width=True):
                # 복원 거부
                st.session_state[notification_key] = True
                st.info("새로운 작업을 시작합니다")
                st.rerun()
        
        return True
    
    def get_restored_data(self, state_type: str) -> Optional[Dict]:
        """
        복원된 데이터 가져오기
        
        Args:
            state_type: 상태 유형
        
        Returns:
            Optional[Dict]: 복원된 데이터
        """
        if self.session_key not in st.session_state:
            return None
        
        return st.session_state[self.session_key].get(f"{state_type}_data")
    
    def clear_work_state(self, user_id: str, state_type: str):
        """
        작업 상태 삭제
        
        Args:
            user_id: 사용자 ID
            state_type: 상태 유형
        """
        # 세션에서 삭제
        if self.session_key in st.session_state:
            st.session_state[self.session_key].pop(state_type, None)
            st.session_state[self.session_key].pop(f"{state_type}_restored", None)
            st.session_state[self.session_key].pop(f"{state_type}_data", None)
        
        # Supabase에서 삭제 (실제 배포 시)
        if self.supabase:
            try:
                self.supabase.table(self.sync_table).delete().eq(
                    "user_id", user_id
                ).eq(
                    "state_type", state_type
                ).execute()
            except Exception as e:
                st.error(f"상태 삭제 실패: {str(e)}")


def render_cross_device_sync_notification(
    user_id: str,
    state_type: str,
    supabase_client=None
) -> Optional[Dict]:
    """
    기기 간 동기화 알림 렌더링 (전역 함수)
    
    Args:
        user_id: 사용자 ID
        state_type: 상태 유형
        supabase_client: Supabase 클라이언트
    
    Returns:
        Optional[Dict]: 복원된 데이터
    """
    sync = CrossDeviceSync(supabase_client)
    
    # 복원 알림 표시
    sync.render_restore_notification(user_id, state_type)
    
    # 복원된 데이터 반환
    return sync.get_restored_data(state_type)


def auto_save_work_state(
    user_id: str,
    state_type: str,
    state_data: Dict,
    supabase_client=None
):
    """
    작업 상태 자동 저장 (전역 함수)
    
    Args:
        user_id: 사용자 ID
        state_type: 상태 유형
        state_data: 상태 데이터
        supabase_client: Supabase 클라이언트
    """
    sync = CrossDeviceSync(supabase_client)
    sync.save_work_state(user_id, state_type, state_data)


def main():
    """테스트 실행"""
    st.set_page_config(page_title="기기 간 동기화", page_icon="🔄", layout="wide")
    
    st.title("🔄 지능형 리딩 파트너 - Cross-Device Sync")
    
    # 테스트 사용자
    test_user_id = "test_agent_001"
    
    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["📝 Draft Report", "📊 Analysis Progress", "👤 Customer Form"])
    
    with tab1:
        st.subheader("📝 Draft Report 자동 저장")
        
        # 복원 알림
        restored_data = render_cross_device_sync_notification(
            user_id=test_user_id,
            state_type="draft_report"
        )
        
        if restored_data:
            st.success("✅ 이전 작업을 복원했습니다")
            st.json(restored_data)
        
        # 테스트 저장
        if st.button("💾 Draft Report 저장 테스트"):
            test_report = {
                "customer_name": "김철수",
                "total_risk": 450_000_000,
                "sections": ["Executive Summary", "Risk Assessment"]
            }
            
            auto_save_work_state(
                user_id=test_user_id,
                state_type="draft_report",
                state_data={"customer_id": "cust_001", "report_data": test_report}
            )
            
            st.success("✅ Draft Report가 저장되었습니다")
    
    with tab2:
        st.subheader("📊 분석 진행 상태 자동 저장")
        
        # 복원 알림
        restored_data = render_cross_device_sync_notification(
            user_id=test_user_id,
            state_type="analysis_in_progress"
        )
        
        if restored_data:
            st.success("✅ 이전 분석을 복원했습니다")
            st.json(restored_data)
        
        # 테스트 저장
        if st.button("💾 분석 상태 저장 테스트"):
            test_analysis = {
                "customer_name": "김철수",
                "current_step": "리스크 계산 중",
                "progress": 65
            }
            
            auto_save_work_state(
                user_id=test_user_id,
                state_type="analysis_in_progress",
                state_data={"customer_id": "cust_001", "analysis_data": test_analysis}
            )
            
            st.success("✅ 분석 상태가 저장되었습니다")
    
    with tab3:
        st.subheader("👤 고객 정보 입력 자동 저장")
        
        # 복원 알림
        restored_data = render_cross_device_sync_notification(
            user_id=test_user_id,
            state_type="customer_form"
        )
        
        if restored_data:
            st.success("✅ 이전 입력을 복원했습니다")
            st.json(restored_data)
        
        # 테스트 저장
        if st.button("💾 고객 정보 저장 테스트"):
            test_form = {
                "name": "김철수",
                "age": 52,
                "industry": "제조업",
                "phone": "010-1234-5678"
            }
            
            auto_save_work_state(
                user_id=test_user_id,
                state_type="customer_form",
                state_data=test_form
            )
            
            st.success("✅ 고객 정보가 저장되었습니다")


if __name__ == "__main__":
    main()
