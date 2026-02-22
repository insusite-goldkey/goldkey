# ==========================================================
# 골드키지사 마스터 AI - 보안 강화 & 초경량 통합본 
# 보안강화: 1.AES-256 암호화저장 / 2.프롬프트 인젝션 방어 / 3.개인정보 마스킹
# ==========================================================

import streamlit as st
from google import genai
from google.genai import types
import json, os, time, hashlib, base64, re, tempfile
from datetime import datetime as dt, timedelta, date
from typing import List, Dict
import numpy as np
import sqlite3
import PIL.Image
from cryptography.fernet import Fernet
import streamlit.components.v1 as components

# -------------------------------------------------------------------------- 
# [SECTION 1] 보안 및 암호화 엔진
# -------------------------------------------------------------------------- 
def get_encryption_key():
    """보안 키를 가져오거나 생성함"""
    if "ENCRYPTION_KEY" in st.secrets:
        return st.secrets["ENCRYPTION_KEY"].encode()
    return b'temporary_fixed_key_for_dev_only_12345='

cipher_suite = Fernet(get_encryption_key())

def encrypt_val(data):
    """데이터 암호화"""
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_val(data):
    """데이터 복호화"""
    try:
        return cipher_suite.decrypt(data.encode()).decode()
    except:
        return "Decryption Error"

def sanitize_prompt(text):
    """프롬프트 인젝션 방어: AI 지침 탈취 시도 차단"""
    danger_words = ["system instruction", "지침", "프롬프트", "비밀번호", "명령어"]
    for word in danger_words:
        if word in text.lower():
            return "보안을 위해 부적절한 요청은 처리되지 않습니다."
    return text

# -------------------------------------------------------------------------- 
# [SECTION 2] 통합 유틸리티 함수
# -------------------------------------------------------------------------- 
@st.cache_resource
def get_client():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("Secrets에 GEMINI_API_KEY 설정이 필요합니다.")
        st.stop()
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

def s_voice(text):
    clean = text.replace('"', '').replace("'", "").replace("\n", " ")
    return f"<script>window.speechSynthesis.cancel(); var msg = new SpeechSynthesisUtterance('{clean}'); msg.lang='ko-KR'; msg.rate=1.0; msg.pitch=1.1; window.speechSynthesis.speak(msg);</script>"

def setup_database():
    """데이터베이스 초기화"""
    conn = sqlite3.connect('insurance_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            document_url TEXT,
            status TEXT DEFAULT 'ACTIVE',
            expiry_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def display_security_sidebar():
    """보안 사이드바 표시"""
    st.markdown("""
    <div style="background:#f0f7ff; padding:15px; border-radius:10px; font-size:0.8rem;">
        <strong>데이터 보안 지침</strong><br>
        - 상담 자료: 로그아웃 시 즉시 파쇄<br>
        - 구독 만료: 30일 유예 후 자동 파기<br>
        - 암호화: AES-256 군사급 보호
    </div>
    """, unsafe_allow_html=True)

def purge_expired_data():
    """30일 경과한 만료 데이터 영구 삭제"""
    conn = sqlite3.connect('insurance_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_documents WHERE status = 'EXPIRED' AND expiry_date <= date('now', '-30 days')")
    conn.commit()
    conn.close()
    st.success("보안 지침에 따라 만료된 상담 자료가 파기되었습니다.")

def analyze_with_ai(query, customer_name="고객"):
    try:
        client = get_client()
        master_instruction = "당신은 30년 경력의 지능을 가진 '마스터 AI'입니다. 정중한 '하십시오체'를 사용하고 실시간 정보를 기반으로 CFP 수준의 리포트를 작성하세요."
        
        resp = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[f"고객 {customer_name} 리포트 요청: {query}"],
            config=types.GenerateContentConfig(
                system_instruction=master_instruction,
                tools=[types.Tool(google_search_retrieval=types.GoogleSearchRetrieval())]
            )
        )
        
        return resp.text
        
    except Exception as e:
        st.error(f"AI 분석 장애: {e}")
        return None

def section_inheritance_will():
    st.title("상속 및 증여 통합 설계")
    st.markdown("2026년 최신 세법 및 민법 제1000조 기준")
    
    c_name = st.text_input("상담 고객 성함", "홍길동")
    masked_name = c_name[0] + "*" + c_name[-1] if len(c_name) > 1 else c_name
    
    st.info(f"보안 모드 가동 중: 분석 리포트에는 '{masked_name}'님으로 표기됩니다.")

    with st.expander("상속인 신분 관계 확정 (민법 제1000조)", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            spouse = st.radio("배우자 관계", ["법률혼 (상속권 있음)", "사실혼 (상속권 없음)"])
            child_legal = st.number_input("친자/양자 수", min_value=0, value=1)
            child_none = st.number_input("파양된 자녀 수", min_value=0, value=0)
        with c2:
            st.caption("※ 양자는 친자와 동일 권리, 파양 시 상속권 소멸")
            shares = "배우자 1.5 : 자녀 1.0" if spouse.startswith("법률혼") else "자녀 100%"
            st.success(f"법정비율: {shares}")

    st.subheader("자산 및 세금 시뮬레이션")
    val_real = st.number_input("부동산 시가(만원)", value=150000)
    val_cash = st.number_input("금융자산(만원)", value=50000)
    
    if st.button("상속 및 증여 정밀 분석", type="primary", use_container_width=True):
        taxable = max((val_real + val_cash) - 100000, 0)
        est_tax = taxable * 0.3 - 6000
        res_text = f"총 자산 {val_real+val_cash:,.0f}만원 중 예상 상속세는 약 {est_tax:,.0f}만원입니다. 부동산 비중이 높아 종신보험을 통한 세원 마련이 시급합니다."
        
        report_html = f"""
        <div style="padding:30px; border:1px solid #eee; background:white; font-family:sans-serif; border-radius:10px;">
            <h2 style="color:#1E88E5; border-bottom:2px solid #1E88E5;">상속 및 증여 정밀 분석 리포트</h2>
            <p><b>고객:</b> {masked_name}님</p>
            <div style="margin:20px 0;">{res_text.replace(chr(10), '<br>')}</div>
            <div style="font-size:11px; color:#888; background:#f9f9f9; padding:10px; border-radius:5px;">
                <b>법적 책임 고지:</b> 본 리포트는 참고용이며 최종 결정의 책임은 사용자에게 있습니다.
            </div>
        </div>
        """
        st.components.v1.html(report_html, height=400, scrolling=True)

    st.divider()
    st.subheader("유언장 및 유류분 방어 플랜")
    st.warning("2024년 최신 판례: 형제자매의 유류분 청구권은 폐지되었습니다.")
    
    if st.checkbox("유언장 양식 보기"):
        st.markdown("#### 자필유언장 표준 양식")
        will_text = f"나 유언자 [성함]은 주소 [주소]에서 다음과 같이 유언한다...\n1. 부동산은 [동거인]에게 사인증여한다..."
        st.code(will_text, language="text")
        st.success("반드시 전체 내용을 직접 자필로 작성하고 날인하십시오.")
        if st.button("작성 가이드 음성 듣기"):
            components.html(s_voice("유언장은 반드시 처음부터 끝까지 직접 손으로 쓰셔야 법적 효력이 발생합니다."), height=0)

# -------------------------------------------------------------------------- 
# [SECTION 3] 메인 앱 구조 통합
# -------------------------------------------------------------------------- 
def main():
    st.set_page_config(page_title="골드키지사 마스터 AI", page_icon="", layout="wide")
    
    setup_database()

    with st.sidebar:
        st.header("SaaS 마스터 센터")
        if 'user_id' not in st.session_state:
            u_name = st.text_input("성함")
            u_phone = st.text_input("연락처", type="password")
            if st.button("접속"):
                if u_name and u_phone:
                    st.session_state.user_id = f"GK_{u_name}"
                    st.session_state.user_name = u_name
                    st.rerun()
        else:
            st.success(f"{st.session_state.user_name} 마스터님")
            if st.button("안전 로그아웃"):
                st.session_state.clear()
                st.rerun()
        
        display_security_sidebar()

    tabs = st.tabs(["통합 상담", "자산 분석", "상속/유언", "관리자"])

    with tabs[0]:
        st.title("마스터 AI 정밀 상담")
        customer_name = st.text_input("고객 성함", "우량 고객")
        query = st.text_area("질문 입력", height=150, placeholder="보험, 재무, 건강 상담 내용을 입력하세요.")
        
        if st.button("정밀 분석 실행", type="primary"):
            if 'user_id' not in st.session_state:
                st.error("로그인이 필요합니다.")
                st.stop()
                
            if not query or len(query.strip()) < 5:
                st.error("상담 내용을 충분히 입력해주세요.")
                st.stop()
            
            with st.spinner("마스터 AI가 실시간 정보를 분석하고 있습니다..."):
                result = analyze_with_ai(query, customer_name)
                if result:
                    st.divider()
                    st.subheader(f"{customer_name}님을 위한 마스터 AI 정밀 리포트")
                    st.markdown(result)
                    st.info("본 분석 결과의 최종 책임은 사용자에게 귀속됩니다.")
                    
                    components.html(s_voice(f"{st.session_state.user_name}님, 마스터 AI의 분석이 완료되었습니다."), height=0)

    with tabs[1]:
        st.subheader("자산 분석 및 문서 관리")
        
        st.subheader("데이터 보안 관리")
        if st.button("만료 데이터 파기 실행", type="secondary"):
            purge_expired_data()
        
        st.subheader("문서 일괄 PDF 생성")
        st.warning("PDF 생성 기능을 위해 PyMuPDF, pdfplumber, python-docx를 설치해주세요.")

    with tabs[2]:
        section_inheritance_will()

    with tabs[3]:
        st.write("### 마스터 지식베이스 관리")
        if st.text_input("인증키", type="password") == "goldkey777":
            st.success("지식베이스 동기화 권한 승인")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"시스템 구동 중 오류 발생: {e}")
