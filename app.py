# ==========================================================================
# 🚨 [운영 헌법 - 이세윤 관리자 지침 100% 수호]
# 1. 에러 해결: 'google_search' 필드 오류를 'google_search_retrieval'로 수정.
# 2. 무손실 수호: 사이드바 혜택, 연금, 민원, 그림 등 누락된 모든 디테일 복구.
# 3. 섹션 독립: 1~15번 전 섹션을 st.divider()로 물리적 완전 분리 배치.
# 4. 관리자 프리패스: admin / gold1234로 즉시 로그인 보장.
# 5. 리스크 관리: 설계사 보호를 위해 보험업법 벌칙 규정 답변 절대 제외.
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
# [🚨 에러 해결] 최신 규격인 google_search_retrieval 로 명칭 변경
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
# [SECTION 3] 사이드바: 마스터 회원 센터 (혜택 및 튜토리얼 완전 복구)
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
            r_pass = st.text_input("희망 PW", type="password")
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
# [SECTION 4.5] 마스터 통합 상담 센터 (동선 최적화)
# --------------------------------------------------------------------------
st.divider()
st.subheader("📡 마스터 통합 상담 센터")
col_in, col_img = st.columns([7, 3])
with col_in:
    main_consult_area = st.text_area("📝 마스터 통합 상담창", height=320, placeholder="가입, 보상, 분쟁 등 모든 상담 내용을 입력하십시오.")
    b1, b2, b3 = st.columns([2, 2, 3])
    if b1.button("⌨️ 직접 입력"): st.toast("입력 모드")
    if b2.button("🎤 음성 입력"): st.info("음성 대기 중...")
    quick_analyze = b3.button("🚀 즉시 분석 및 민원 요청", type="primary", use_container_width=True)
    main_output = st.container()

with col_img:
    st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/ai_expert.png", use_container_width=True)

# --------------------------------------------------------------------------
# [SECTION 5] 실전 보상 & 민원 대응 튜토리얼
# --------------------------------------------------------------------------
st.divider()
with st.expander("💡 실전 보상 & 민원 대응 튜토리얼 (판례 2001다1480)", expanded=False):
    st.write("보험사의 설명의무 위반 시 대응 법리와 사건 매칭 로직입니다.")

# --------------------------------------------------------------------------
# [SECTION 6] 1단계: 고객 기초 정보
# --------------------------------------------------------------------------
st.divider()
st.write("### 👤 1단계: 고객 기초 정보")
c1, c2 = st.columns(2)
cust_name = c1.text_input("고객 성함", "고객님")
hi_premium = c1.number_input("월 건강보험료(원)", value=0, step=1000)
debt = c2.number_input("부채 총액(만원)", value=0, step=100)

# --------------------------------------------------------------------------
# [SECTION 7] 2단계: 자료 및 증권 업로드
# --------------------------------------------------------------------------
st.divider()
st.write("### 📸 2단계: 자료 및 증권 업로드")
files = st.file_uploader("파일 로드", accept_multiple_files=True, key=f"u_{st.session_state.uploader_key}")
if files:
    st.info(f"✅ 총 {len(files)}장의 서류 인식됨")
    if st.button("🗑️ 전체 서류 삭제 및 재로드", type="primary", use_container_width=True):
        st.session_state.uploader_key += 1; st.rerun()

# --------------------------------------------------------------------------
# [SECTION 8] 3단계: 질병 보상 정밀 분석
# --------------------------------------------------------------------------
st.divider()
st.write("### 🏥 3단계: 질병 보상 정밀 분석")
dis_focus = st.multiselect("분석 대상 질환", ["암(선행항암)", "뇌/심장", "정신과", "희귀난치병"])

# --------------------------------------------------------------------------
# [SECTION 9] 4단계: 삼성/교보 헬스케어 컨설팅
# --------------------------------------------------------------------------
st.divider()
st.write("### 💎 4단계: 삼성/교보 헬스케어 컨설팅")
hc_info = st.checkbox("주요 생보사 헬스케어 서비스 안내 포함")

# --------------------------------------------------------------------------
# [SECTION 10] 5단계: 6대 법령 및 보상 지식 DB
# --------------------------------------------------------------------------
st.divider()
st.write("### 🏛️ 5단계: 6대 법령 및 보상 지식 DB")
st.info("민법, 상법, 보험업법 등 6대 법령 및 실시간 판례 검색 중")

# --------------------------------------------------------------------------
# [SECTION 11] 6단계: 국제재무설계 기준 위험관리 및 필수 보장 설계
# --------------------------------------------------------------------------
st.divider()
st.write("### 🛡️ 6단계: 국제재무설계 기준 위험관리 및 필수 보장 설계")
[Image of the insurance dispute resolution process in Korea]
ess_ins = st.multiselect("필수 소유 보험", ["자동차", "화재", "일배책", "후유장해", "기본장기"])

# --------------------------------------------------------------------------
# [SECTION 12] 7단계: 국제 재무설계 기준 3층 연금 통합 시뮬레이션
# --------------------------------------------------------------------------
st.divider()
st.write("### 💰 7단계: 국제 재무설계 기준 3층 연금 통합 시뮬레이션")
[Image of the three-tier pension system in Korea: National, Retirement, and Private Pensions]
p1, p2,
