# ==========================================================
# 인증 및 보안 모듈
# ==========================================================

import os
import streamlit as st
import hashlib
from datetime import datetime as dt
from cryptography.fernet import Fernet

def get_encryption_key():
    key = os.environ.get("ENCRYPTION_KEY", "")
    if not key:
        try:
            if "ENCRYPTION_KEY" in st.secrets:
                key = st.secrets["ENCRYPTION_KEY"]
        except Exception:
            key = ""
    if not key:
        return b'temporary_fixed_key_for_dev_only_12345='
    return key.encode() if isinstance(key, str) else key

def _get_cipher():
    return Fernet(get_encryption_key())

def encrypt_val(data):
    return _get_cipher().encrypt(data.encode()).decode()

def decrypt_val(data):
    try:
        return _get_cipher().decrypt(data.encode()).decode()
    except:
        return "Decryption Error"

def sanitize_prompt(text):
    danger_words = ["system instruction", "지침", "프롬프트", "비밀번호", "명령어"]
    for word in danger_words:
        if word in text.lower():
            return "보안을 위해 부적절한 요청은 처리되지 않습니다."
    return text

def check_login_status():
    """로그인 상태 체크"""
    if 'user_id' not in st.session_state:
        return False
    return True

def render_login_page():
    """로그인 페이지 렌더링"""
    st.markdown("""
    <div style="text-align: center; padding: 50px 20px;">
        <h1>골드키지사 마스터 AI</h1>
        <p>보안 강화 & 초경량 통합본</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        u_name = st.text_input("성함", placeholder="이름을 입력하세요")
        u_phone = st.text_input("연락처", type="password", placeholder="연락처를 입력하세요")
        
        if st.button("🚀 접속", use_container_width=True, type="primary"):
            if u_name and u_phone:
                # 간단한 인증 로직 (실제로는 더 강화 필요)
                user_id = f"GK_{hashlib.md5(u_name.encode()).hexdigest()[:8]}"
                st.session_state.user_id = user_id
                st.session_state.user_name = u_name
                st.session_state.login_time = dt.now()
                st.rerun()
            else:
                st.error("이름과 연락처를 모두 입력해주세요.")

def render_logout_sidebar():
    """로그아웃 사이드바"""
    if st.sidebar.button("🚪 로그아웃"):
        st.session_state.clear()
        st.rerun()
    
    st.sidebar.markdown(f"""
    <div style="background:#e3f2fd; padding:15px; border-radius:10px;">
        <strong>{st.session_state.user_name} 마스터님</strong><br>
        <small>로그인 시간: {st.session_state.get('login_time', dt.now()).strftime('%H:%M')}</small>
    </div>
    """, unsafe_allow_html=True)
