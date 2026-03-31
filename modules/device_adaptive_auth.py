# -*- coding: utf-8 -*-
"""
지능형 리딩 파트너 - Device-Adaptive Auth (기기 적응형 인증)
모바일/태블릿 Native Credential 통합 시스템

작성일: 2026-03-31
목적: 기기 유형 자동 감지 및 최우선 보안 수단(지문/Face ID/도형/PIN) 호출
"""

import streamlit as st
from typing import Dict, Optional, Literal
import hashlib
import hmac
import time
from datetime import datetime


class DeviceAdaptiveAuth:
    """
    기기 적응형 인증 시스템
    
    핵심 기능:
    1. 기기 유형 자동 감지 (Phone/Tablet/Desktop)
    2. Native Credential 호출 (지문/Face ID/도형/PIN)
    3. 보안 세션 관리
    4. 리딩 파트너 보안 확인 메시지
    """
    
    def __init__(self):
        """초기화"""
        self.device_type = self._detect_device_type()
        self.auth_timestamp = None
        self.session_key = "device_adaptive_auth"
    
    def _detect_device_type(self) -> Literal["phone", "tablet", "desktop"]:
        """
        기기 유형 자동 감지
        
        Returns:
            str: "phone", "tablet", "desktop"
        """
        # User-Agent 기반 감지 (Streamlit에서는 브라우저 정보 활용)
        # 실제 구현 시 JavaScript를 통해 화면 크기 및 터치 지원 여부 확인
        
        # 세션에 저장된 기기 정보 확인
        if "device_type" in st.session_state:
            return st.session_state["device_type"]
        
        # 기본값: desktop (실제 배포 시 JavaScript로 정확히 감지)
        return "desktop"
    
    def detect_device_from_viewport(self) -> str:
        """
        뷰포트 크기 기반 기기 감지 (JavaScript 연동)
        
        Returns:
            str: "phone", "tablet", "desktop"
        """
        # JavaScript를 통한 화면 크기 감지
        device_detection_js = """
        <script>
        function detectDevice() {
            const width = window.innerWidth;
            const height = window.innerHeight;
            const isTouchDevice = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
            
            let deviceType = 'desktop';
            
            if (isTouchDevice) {
                if (width <= 768) {
                    deviceType = 'phone';
                } else if (width <= 1024) {
                    deviceType = 'tablet';
                } else {
                    deviceType = 'desktop';
                }
            }
            
            // Streamlit으로 기기 정보 전달
            window.parent.postMessage({
                type: 'streamlit:setComponentValue',
                value: deviceType
            }, '*');
            
            return deviceType;
        }
        
        // 페이지 로드 시 자동 실행
        window.addEventListener('load', detectDevice);
        window.addEventListener('resize', detectDevice);
        </script>
        """
        
        return device_detection_js
    
    def get_native_credential_type(self) -> str:
        """
        기기별 최우선 보안 수단 확인
        
        Returns:
            str: "fingerprint", "face_id", "pattern", "pin", "password"
        """
        device_credential_map = {
            "phone": "fingerprint",      # 지문 인식 우선
            "tablet": "face_id",         # Face ID 우선
            "desktop": "password"        # 비밀번호
        }
        
        return device_credential_map.get(self.device_type, "password")
    
    def request_native_credential(self, user_id: str) -> Dict:
        """
        Native Credential 요청
        
        Args:
            user_id: 사용자 ID
        
        Returns:
            Dict: 인증 결과
        """
        credential_type = self.get_native_credential_type()
        
        # 세션에 인증 요청 저장
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = {}
        
        st.session_state[self.session_key]["credential_type"] = credential_type
        st.session_state[self.session_key]["user_id"] = user_id
        st.session_state[self.session_key]["requested_at"] = time.time()
        
        return {
            "device_type": self.device_type,
            "credential_type": credential_type,
            "status": "requested",
            "message": self._get_credential_message(credential_type)
        }
    
    def _get_credential_message(self, credential_type: str) -> str:
        """인증 수단별 메시지 생성"""
        messages = {
            "fingerprint": "지문 인식을 통해 보안을 확인해주세요",
            "face_id": "Face ID를 통해 보안을 확인해주세요",
            "pattern": "도형 패턴을 입력해주세요",
            "pin": "PIN 번호를 입력해주세요",
            "password": "비밀번호를 입력해주세요"
        }
        
        return messages.get(credential_type, "보안 인증이 필요합니다")
    
    def verify_credential(
        self,
        user_id: str,
        credential_input: str,
        credential_hash: str
    ) -> Dict:
        """
        Credential 검증
        
        Args:
            user_id: 사용자 ID
            credential_input: 입력된 인증 정보
            credential_hash: 저장된 인증 해시
        
        Returns:
            Dict: 검증 결과
        """
        # HMAC-SHA256 기반 검증
        input_hash = hmac.new(
            user_id.encode(),
            credential_input.encode(),
            hashlib.sha256
        ).hexdigest()
        
        is_valid = hmac.compare_digest(input_hash, credential_hash)
        
        if is_valid:
            self.auth_timestamp = time.time()
            
            # 세션에 인증 성공 저장
            st.session_state[self.session_key]["authenticated"] = True
            st.session_state[self.session_key]["auth_timestamp"] = self.auth_timestamp
            
            return {
                "status": "success",
                "message": "지능형 리딩 파트너가 본인 확인을 완료했습니다",
                "timestamp": self.auth_timestamp
            }
        else:
            return {
                "status": "failed",
                "message": "본인 확인에 실패했습니다. 다시 시도해주세요",
                "timestamp": None
            }
    
    def is_authenticated(self) -> bool:
        """인증 상태 확인"""
        if self.session_key not in st.session_state:
            return False
        
        auth_data = st.session_state[self.session_key]
        
        if not auth_data.get("authenticated"):
            return False
        
        # 인증 타임아웃 체크 (30분)
        auth_timestamp = auth_data.get("auth_timestamp", 0)
        current_time = time.time()
        timeout_seconds = 30 * 60  # 30분
        
        if current_time - auth_timestamp > timeout_seconds:
            # 타임아웃 - 재인증 필요
            st.session_state[self.session_key]["authenticated"] = False
            return False
        
        return True
    
    def render_auth_screen(self, user_id: str, on_success_callback=None):
        """
        인증 화면 렌더링
        
        Args:
            user_id: 사용자 ID
            on_success_callback: 인증 성공 시 콜백 함수
        """
        credential_type = self.get_native_credential_type()
        
        # 헤더
        st.markdown(
            f"""
            <div style='background:linear-gradient(135deg,#1e3a8a 0%,#3b82f6 100%);
                        border-radius:12px;padding:24px;margin-bottom:20px;
                        box-shadow:0 4px 20px rgba(30,58,138,0.3);'>
                <div style='text-align:center;'>
                    <div style='font-size:48px;margin-bottom:12px;'>🔐</div>
                    <div style='font-size:20px;font-weight:900;color:#ffffff;
                                text-shadow:0 2px 4px rgba(0,0,0,0.3);margin-bottom:8px;'>
                        본인 확인
                    </div>
                    <div style='font-size:14px;color:#dbeafe;'>
                        {self._get_credential_message(credential_type)}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # 기기 정보 표시
        device_icons = {
            "phone": "📱",
            "tablet": "📲",
            "desktop": "💻"
        }
        
        st.markdown(
            f"""
            <div style='background:#f3f4f6;border-radius:8px;padding:12px;
                        margin-bottom:16px;text-align:center;'>
                <div style='font-size:14px;color:#6b7280;'>
                    {device_icons.get(self.device_type, '💻')} 
                    <b>{self.device_type.upper()}</b> 기기에서 접속 중
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # 인증 입력 (임시 - 실제로는 Native API 호출)
        if credential_type in ["fingerprint", "face_id"]:
            st.info(f"💡 실제 배포 시 {credential_type} 기능이 자동으로 실행됩니다.")
            
            # 개발 환경용 임시 버튼
            if st.button("🔓 본인 확인 시뮬레이션", use_container_width=True, type="primary"):
                # 임시 인증 성공 처리
                st.session_state[self.session_key] = {
                    "authenticated": True,
                    "auth_timestamp": time.time(),
                    "credential_type": credential_type,
                    "user_id": user_id
                }
                
                st.success("✅ 지능형 리딩 파트너가 보안을 확인했습니다")
                
                if on_success_callback:
                    on_success_callback()
                
                st.rerun()
        
        elif credential_type in ["pattern", "pin", "password"]:
            credential_input = st.text_input(
                f"{credential_type.upper()} 입력",
                type="password",
                key=f"credential_input_{user_id}"
            )
            
            if st.button("🔓 확인", use_container_width=True, type="primary"):
                if credential_input:
                    # 실제로는 Supabase에 저장된 해시와 비교
                    # 여기서는 임시로 성공 처리
                    st.session_state[self.session_key] = {
                        "authenticated": True,
                        "auth_timestamp": time.time(),
                        "credential_type": credential_type,
                        "user_id": user_id
                    }
                    
                    st.success("✅ 지능형 리딩 파트너가 본인 확인을 완료했습니다")
                    
                    if on_success_callback:
                        on_success_callback()
                    
                    st.rerun()
                else:
                    st.error("확인 정보를 입력해주세요")
    
    def render_security_badge(self):
        """보안 상태 배지 렌더링"""
        if self.is_authenticated():
            auth_data = st.session_state[self.session_key]
            credential_type = auth_data.get("credential_type", "unknown")
            
            credential_icons = {
                "fingerprint": "👆",
                "face_id": "👤",
                "pattern": "🔢",
                "pin": "🔢",
                "password": "🔑"
            }
            
            icon = credential_icons.get(credential_type, "🔐")
            
            st.markdown(
                f"""
                <div style='background:#ecfdf5;border:1px solid #059669;
                            border-radius:8px;padding:8px 12px;
                            display:inline-block;margin-bottom:12px;'>
                    <span style='font-size:14px;color:#059669;font-weight:600;'>
                        {icon} 본인 확인 완료
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )


def render_device_adaptive_auth(user_id: str, on_success_callback=None):
    """
    기기 적응형 인증 렌더링 (전역 함수)
    
    Args:
        user_id: 사용자 ID
        on_success_callback: 인증 성공 시 콜백 함수
    """
    auth = DeviceAdaptiveAuth()
    
    if not auth.is_authenticated():
        auth.render_auth_screen(user_id, on_success_callback)
        return False
    else:
        auth.render_security_badge()
        return True


def main():
    """테스트 실행"""
    st.set_page_config(page_title="기기 적응형 인증", page_icon="🔐", layout="wide")
    
    st.title("🔐 지능형 리딩 파트너 - Device-Adaptive Auth")
    
    # 테스트 사용자
    test_user_id = "test_agent_001"
    
    # 인증 렌더링
    is_authenticated = render_device_adaptive_auth(
        user_id=test_user_id,
        on_success_callback=lambda: st.success("인증 성공 콜백 실행!")
    )
    
    if is_authenticated:
        st.success("✅ 인증 완료 - 메인 화면 표시")
        
        st.markdown("---")
        st.subheader("📊 대시보드")
        st.write("인증 후 접근 가능한 콘텐츠입니다.")


if __name__ == "__main__":
    main()
