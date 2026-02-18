# ==========================================================================
# 🚨 [운영 헌법 - 이세윤 관리자 지침 100% 수호]
# 1. 문법 에러 해결: [Image of...] 태그를 st.image() 코드로 완벽 치환.
# 2. 섹션 무손실 수호: 사이드바 혜택, 민원, 연금, 그림 등 누락된 모든 디테일 복구.
# 3. 섹션 독립: 1~15번 전 섹션을 st.divider()로 물리적 완전 분리 배치.
# 4. 마스터 프리패스: admin / gold1234로 즉시 로그인 보장.
# 5. 기술 해법: Grounding(구글검색) 명칭을 'google_search_retrieval'로 고정.
# ==========================================================================

import streamlit as st
import google.generativeai as genai
import PIL.Image
import json
import os
import re
import time
from datetime import datetime as dt

# --------------------------------------------------------------------------
# [SECTION 1] 설정 및 마스터 계정 보안 로직
# --------------------------------------------------------------------------
st.set_page_config(page_title="골드키지사 AI 마스터", page_icon="👑", layout="wide")

MASTER_ID = "admin"
MASTER_PW = "gold1234"

DB_FILE = 'user_db.json'
def load_db():
    if not os.path.exists(DB_FILE): return {}
    try:
        with open(DB_FILE, 'r') as f: return json.load(f)
    except: return {}

def save_user(username, password, api_key):
    db = load_db()
    if username in db: return False
    db[username] = {'password': password, 'api_key': api_key}
    try:
        with open(DB_FILE, 'w') as f: json.dump(db, f); return True
    except: return False

def verify_user(username, password):
    if username == MASTER_ID and password == MASTER_PW: return "MASTER_ACCESS"
    db = load_db()
    if username in db and db[username]['password'] == password: return db[username]['api_key']
    return None

if 'uploader_key' not in st.session_state: st.session_state.uploader_key = 0
if 'login_status' not in st.session_state: st.session_state.login_status = False
if 'user_api_key' not in st.session_state: st.session_state.user_api_key = ""
if 'current_user' not in st.session_state: st.session_state.current_user = ""

# --------------------------------------------------------------------------
# [SECTION 2] 페르소나 및 음성 엔진 설정
# --------------------------------------------------------------------------
MODEL_NAME = 'gemini-1.5-flash'
TOOLS_CONFIG = [{'google_search_retrieval': {}}] 

SYSTEM_PROMPT = """
성명: 글로벌 보험/재무/분쟁대응 통합 전문가 (관리자: 이세윤)
표어: 보험 가입 상담 부터 보험금 분쟁 대응까지- 보험 AI전문 마스터 통합 시스템
[지휘 강령]:
- 구글 실시간 검색으로 2026년 최신 법령, 판례, 의학 정보를 반영하라.
- 보험업법상 설계사 구상권 관련 벌칙 규정은 답변에서 철저히 제외하라.
- 판례 2001다1480 및 상법 제638조의3 근거를 고객 사건과 매칭하라.
- 건보료 0.0709 소득 역산 및 CFP® 6단계 프로세스를 한 몸처럼 구동하라.
"""

def s_voice(text, lang='ko-KR'):
    if re.search('[a-zA-Z]{5,}', text): lang = 'en-US'
    return f"""<script>
        window.speechSynthesis.cancel(); 
        var msg = new SpeechSynthesisUtterance("{text}");
        msg.lang = "{lang}"; msg.rate = 0.95; 
        window.speechSynthesis.speak(msg);
    </script>"""

# --------------------------------------------------------------------------
# [SECTION 3] 사이드바: 마스터 회원 센터 (상세 혜택 복구)
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("🔑 마스터 회원 센터")
    if st.session_state.login_status:
        st.success(f"👋 **{st.session_state.current_user}** 마스터님")
        if st.button("로그아웃"):
            st.session_state.login_status = False; st.rerun()
    else:
        tab1, tab2 = st.tabs(["로그인", "회원가입"])
        with tab1:
            l_user = st.text_input("아이디")
            l_pass = st.text_input("비밀번호", type="password")
            if st.button("🚀 로그인", use_container_width=True):
                res = verify_user(l_user, l_pass)
                if res:
                    st.session_state.login_status = True; st.session_state.current_user = l_user
                    st.session_state.user_api_key = st.secrets.get("GEMINI_API_KEY", "") if res == "MASTER_ACCESS" else res
                    st.rerun()
                else: st.error("정보 불일치")
        with tab2:
            st.markdown("**신규 마스터 등록**")
            r_user = st.text_input("희망 ID")
            r_pass = st.text_input("비밀번호", type="password")
            r_key = st.text_input("API Key", type="password")
            if st.button("💾 가입 및 저장"):
                if save_user(r_user, r_pass, r_key): st.success("가입 성공! 로그인 하십시오.")
                else: st.error("가입 실패")

    st.divider()
    st.info("👤 **시스템 관리자: 이세윤**")
    st.markdown("### 🏆 회원 등록 수용 혜택")
    st.success("- 1일 50건 미만 상담 시 **8년간 무료**\n- 관리자 권한 **무제한 승인**\n- 로그인 시 **Key 자동 로드**\n- 데이터 **즉시 파기 보안**")
    st.markdown("### 🌐 API 발급 튜토리얼")
    st.warning("1. 구글 로그인\n2. 카드 등록\n3. API 키 생성 및 연동")
    st.markdown('<a href="https://aistudio.google.com/app/apikey" target="_blank"><button style="width:100%; cursor:pointer; background:#1E88E5; color:white; border:none; padding:10px; border-radius:5px; font-weight:bold;">🌐 API 키 발급 바로가기</button></a>', unsafe_allow_html=True)

# --------------------------------------------------------------------------
# [SECTION 4] 브랜드 상단 UI
# --------------------------------------------------------------------------
st.divider()
st.markdown("""
<div style="background-color:#f0f2f6; padding:20px; border-radius:10px; border-left:5px solid #1E88E5;">
    <h3 style="margin:0; color:#0D47A1;">"보험 가입 상담 부터 보험금 분쟁 대응까지"</h3>
    <p style="margin:0; font-size:16px;"><b>보험 AI전문 마스터 통합 시스템</b> (관리자: 이세윤)</p>
</div>
""", unsafe_allow_html=True)

st.title("👑 골드키지사 AI 마스터")

if not st.session_state.login_status:
    st.warning("🔒 관리자님, 로그인이 필요합니다. (admin / gold1234)")
    st.stop()

# --------------------------------------------------------------------------
# [SECTION 4.5] 마스터 통합 상담 센터
# --------------------------------------------------------------------------
st.divider()
st.subheader("📡 마스터 통합 상담 센터")
col_in, col_img = st.columns([7, 3])
with col_in:
    main_consult_area = st.text_area("📝 마스터 통합 상담창", height=320, placeholder="모든 상담 내용을 입력하십시오.")
    b1, b2, b3
