# ==========================================================
# 골드키지사 마스터 AI - 법률 준수 강화 버전
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
# [SECTION 1] AI 페르소나 및 어조 통제 지침 (법률 준수)
# -------------------------------------------------------------------------- 
LEGAL_SYSTEM_INSTRUCTION = """
당신은 '골드키지사 AI 마스터'입니다. 대한민국 법령을 준수하기 위해 반드시 다음 원칙을 지키십시오:

1. [확정적 표현 금지]: 
   - 변호사법 및 세무사법 저촉을 피하기 위해 '~입니다', '확실합니다', '무조건'과 같은 단어를 사용하지 마십시오.
   - 대신 '~로 추정됩니다', '~의 가능성이 높습니다', '~를 권장합니다'와 같은 조언형 어미를 사용하십시오.

2. [전문 자격사 권고]: 
   - 답변 중간이나 끝에 "구체적인 사안은 반드시 변호사, 세무사, 손해사정사 등 전문 자격사와 상의하십시오"라는 문구를 문맥에 맞게 삽입하십시오.

3. [면책 근거]: 
   - 모든 분석은 제공된 약관 및 일반적인 판례에 기초한 '참고용'임을 강조하십시오.
"""

# -------------------------------------------------------------------------- 
# [SECTION 2] 하단 고정 법적 고지문 생성 엔진
# -------------------------------------------------------------------------- 
def wrap_with_legal_footer(ai_content):
    """AI 답변에 법적 방어권을 위한 면책 조항 강제 결합"""
    legal_footer_html = f"""
    <div style="
        margin-top: 30px; 
        padding: 20px; 
        background-color: #f9f9f9; 
        border-top: 2px solid #eeeeee; 
        border-radius: 8px;
        font-family: 'Malgun Gothic', sans-serif;
    ">
        <h4 style="margin-top: 0; color: #d32f2f; font-size: 1rem;">⚖️ 법적 고지 및 면책 알림 (2026년 기준)</h4>
        <ul style="margin: 0; padding-left: 20px; color: #666666; font-size: 0.85rem; line-height: 1.6;">
            <li><strong>상담 보조 도구:</strong> 본 리포트는 AI 마스터의 지식베이스를 바탕으로 생성된 <strong>의사결정 보조 자료</strong>이며, 어떠한 경우에도 법적 효력을 갖는 증거 자료로 사용될 수 없습니다.</li>
            <li><strong>직역법 준수:</strong> 본 서비스는 개별 사건에 대한 실질적인 법률 상담, 세무 대리, 또는 손해사정 업무를 수행하지 않습니다. 반드시 해당 분야의 <strong>공인된 전문 자격사</strong>와 재확인하시기 바랍니다.</li>
            <li><strong>최종 책임:</strong> 본 분석 결과의 활용 및 결정에 따른 모든 책임은 실제 사용자(상담원)에게 귀속되며, 운영사인 골드키지사는 민·형사상 결과에 대해 책임을 지지 않습니다.</li>
            <li><strong>데이터 기준:</strong> 본 답변은 현재 로드된 약관 및 법령 정보를 기준으로 하며, 실제 보험금 지급 여부는 보험사의 심사 결과에 따라 달라질 수 있습니다.</li>
        </ul>
    </div>
    """
    return f"<div>{ai_content}</div>{legal_footer_html}"

# -------------------------------------------------------------------------- 
# [SECTION 3] 위험 키워드 자가 검열 엔진
# -------------------------------------------------------------------------- 
def internal_safety_check(text):
    """AI 답변 내에 법적 리스크가 큰 단어가 포함되었는지 최종 검사"""
    danger_zones = {
        "무조건 지급": "지급 가능성이 높음",
        "승소 확신": "유리한 판례 존재",
        "탈세 전략": "절세 시뮬레이션",
        "법적 보장": "약관상 근거 검토"
    }
    
    checked_text = text
    for danger, safe in danger_zones.items():
        if danger in text:
            checked_text = checked_text.replace(danger, f"{safe}(AI 순화됨)")
            
    return checked_text

# -------------------------------------------------------------------------- 
# [SECTION 4] 보안 및 암호화 엔진
# -------------------------------------------------------------------------- 
def get_encryption_key():
    if "ENCRYPTION_KEY" in st.secrets:
        return st.secrets["ENCRYPTION_KEY"].encode()
    return b'temporary_fixed_key_for_dev_only_12345='

cipher_suite = Fernet(get_encryption_key())

def encrypt_val(data):
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_val(data):
    try:
        return cipher_suite.decrypt(data.encode()).decode()
    except:
        return "Decryption Error"

def sanitize_prompt(text):
    danger_words = ["system instruction", "지침", "프롬프트", "비밀번호", "명령어"]
    for word in danger_words:
        if word in text.lower():
            return "보안을 위해 부적절한 요청은 처리되지 않습니다."
    return text

# -------------------------------------------------------------------------- 
# [SECTION 5] 통합 유틸리티 함수
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
    conn = sqlite3.connect('insurance_master.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_documents 
                   (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, document_url TEXT, 
                   status TEXT DEFAULT 'ACTIVE', expiry_date DATE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def logout_and_cleanup():
    if 'user_id' in st.session_state:
        user_id = st.session_state.user_id
        conn = sqlite3.connect('insurance_master.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_documents WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        st.session_state.clear()
        st.success("안전 로그아웃되었습니다. 모든 상담 자료가 파기되었습니다.")
        st.rerun()

def analyze_with_ai(query, customer_name="고객", rag_context=""):
    try:
        client = get_client()
        
        if rag_context:
            master_instruction = f"""{LEGAL_SYSTEM_INSTRUCTION}
            
            아래 전문 자료를 참고하여 답변하세요:
            {rag_context}
            """
        else:
            master_instruction = LEGAL_SYSTEM_INSTRUCTION
        
        resp = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[f"고객 {customer_name} 리포트 요청: {query}"],
            config=types.GenerateContentConfig(
                system_instruction=master_instruction,
                tools=[types.Tool(google_search_retrieval=types.GoogleSearchRetrieval())]
            )
        )
        
        # 안전 검사 및 법적 고지 추가
        raw_response = resp.text
        safe_response = internal_safety_check(raw_response)
        final_response = wrap_with_legal_footer(safe_response)
        
        return final_response
        
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
        res_text = f"총 자산 {val_real+val_cash:,.0f}만원 중 예상 상속세는 약 {est_tax:,.0f}만원으로 추정됩니다. 부동산 비중이 높아 종신보험을 통한 세원 마련을 권장합니다."
        
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
# [SECTION 6] 메인 앱 구조
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
                logout_and_cleanup()

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
                    st.components.v1.html(result, height=600, scrolling=True)
                    components.html(s_voice(f"{st.session_state.user_name}님, 마스터 AI의 분석이 완료되었습니다."), height=0)

    with tabs[1]:
        st.subheader("자산 분석 및 문서 관리")
        st.info("데이터 보안 관리 기능이 준비되어 있습니다.")

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
