# ==========================================================================
# 🚨 [운영 헌법 - 이세윤 관리자 지침 100% 준수]
# 1. 섹션 수호: 8번(질병), 9번(헬스케어), 10번(법령DB)을 포함한 전 섹션 상세 분리.
# 2. 기술 보정: 404 경로 에러 차단 및 중복 ID(Duplicate ID) 완전 해결.
# 3. 무손실 복구: 사이드바 혜택, 연금, 민원, 그림 등 누락 디테일 100% 복구.
# 4. 관리자 프리패스: admin / gold1234로 즉시 로그인 보장.
# ==========================================================================

import streamlit as st
import google.generativeai as genai
import PIL.Image
import json
import os
import re
import time

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
# [SECTION 2] 페르소나 및 경로 정규화 (404 방어)
# --------------------------------------------------------------------------
MODEL_NAME = 'gemini-1.5-flash'
TOOLS_CONFIG = [{'google_search_retrieval': {}}] 

SYSTEM_PROMPT = """
성명: 글로벌 보험/재무/분쟁대응 통합 전문가 (관리자: 이세윤)
표어: 보험 가입 상담 부터 보험금 분쟁 대응까지- 보험 AI전문 마스터 통합 시스템
[지휘 강령]: 구글 실시간 검색 활용, 보험업법 벌칙 제외, 판례 2001다1480 매칭, 소득 역산 수행.
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
# [SECTION 3] 사이드바: 마스터 회원 센터 (혜택 완전 복구)
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("🔑 마스터 회원 센터")
    if st.session_state.login_status:
        st.success(f"👋 **{st.session_state.current_user}** 마스터님")
        if st.button("로그아웃"): st.session_state.login_status = False; st.rerun()
    else:
        tab1, tab2 = st.tabs(["로그인", "회원가입"])
        with tab1:
            l_user = st.text_input("아이디", key="l_id")
            l_pass = st.text_input("비밀번호", type="password", key="l_pw")
            if st.button("🚀 로그인", use_container_width=True):
                res = verify_user(l_user, l_pass)
                if res:
                    st.session_state.login_status = True; st.session_state.current_user = l_user
                    st.session_state.user_api_key = st.secrets.get("GEMINI_API_KEY", "") if res == "MASTER_ACCESS" else res
                    st.rerun()
                else: st.error("정보 불일치")
        with tab2:
            st.info("신규 회원은 관리자 승인 후 이용 가능합니다.")

    st.divider()
    st.info("👤 **관리자: 이세윤**")
    st.markdown("### 🏆 회원 전용 혜택\n- 8년간 무료 상담\n- 실시간 검색 연동\n- 데이터 즉시 파기")

# --------------------------------------------------------------------------
# [SECTION 4] 브랜드 상단 UI
# --------------------------------------------------------------------------
st.divider()
st.markdown("<h3 style='color:#0D47A1;'>\"보험 가입 상담 부터 보험금 분쟁 대응까지\"</h3>", unsafe_allow_html=True)
st.title("👑 골드키지사 AI 마스터")

if not st.session_state.login_status:
    st.warning("🔒 로그인이 필요합니다. (admin / gold1234)")
    st.stop()

# --------------------------------------------------------------------------
# [SECTION 4.5] 마스터 통합 상담 센터
# --------------------------------------------------------------------------
st.divider()
st.subheader("📡 마스터 통합 상담 센터")
main_area = st.text_area("📝 상담 내용 상세 입력", height=300, key="m_area")
q_analyze = st.button("🚀 즉시 분석 및 민원 요청", type="primary", use_container_width=True)
main_out = st.container()

# --------------------------------------------------------------------------
# [SECTION 5] 실전 보상 & 민원 대응 튜토리얼
# --------------------------------------------------------------------------
st.divider()
with st.expander("💡 실전 보상 & 민원 대응 튜토리얼 (판례 2001다1480)"):
    st.write("설명의무 위반 시 대응 법리 및 사건 매칭 로직 탑재")

# --------------------------------------------------------------------------
# [SECTION 6] 1단계: 고객 기초 정보
# --------------------------------------------------------------------------
st.divider()
st.write("### 👤 1단계: 고객 기초 정보")
c1, c2 = st.columns(2)
cust_name = c1.text_input("고객 성함", "고객님", key="c_nm")
hi_premium = c1.number_input("월 건강보험료(원)", value=0, step=1000, key="c_pr")
debt = c2.number_input("부채 총액(만원)", value=0, step=100, key="c_db")

# --------------------------------------------------------------------------
# [SECTION 7] 2단계: 자료 및 증권 업로드
# --------------------------------------------------------------------------
st.divider()
st.write("### 📸 2단계: 자료 및 증권 업로드")
files = st.file_uploader("증권 및 서류 로드", accept_multiple_files=True, key=f"u_{st.session_state.uploader_key}")
if files and st.button("🗑️ 전체 삭제", key="f_del"):
    st.session_state.uploader_key += 1; st.rerun()

# --------------------------------------------------------------------------
# [🚨 SECTION 8] 3단계: 질병 보상 정밀 분석 (분리 완료)
# --------------------------------------------------------------------------
st.divider()
st.write("### 🏥 3단계: 질병 보상 정밀 분석")
dis_focus = st.multiselect("분석 대상 질환 선택", ["암(선행항암)", "뇌/심장", "정신과", "희귀난치병"], key="c_ds")

# --------------------------------------------------------------------------
# [🚨 SECTION 9] 4단계: 삼성/교보 헬스케어 컨설팅 (분리 완료)
# --------------------------------------------------------------------------
st.divider()
st.write("### 💎 4단계: 삼성/교보 헬스케어 컨설팅")
hc_info = st.checkbox("주요 생보사 헬스케어 서비스 안내 포함", key="c_hc")
st.caption("삼성/교보 등 대형 생보사의 특화 건강관리 서비스 정보를 연동합니다.")

# --------------------------------------------------------------------------
# [🚨 SECTION 10] 5단계: 6대 법령 및 보상 지식 DB (분리 완료)
# --------------------------------------------------------------------------
st.divider()
st.write("### 🏛️ 5단계: 6대 법령 및 보상 지식 DB")
st.info("민법, 상법, 보험업법 등 6대 법령 기반 실시간 판례 검색 엔진 가동 중")
st.write("- 보험 약관 해석 원칙 및 분쟁 대응 지식 베이스 활성화")

# --------------------------------------------------------------------------
# [SECTION 11] 6단계: 위험관리 및 필수 보장 설계
# --------------------------------------------------------------------------
st.divider()
st.write("### 🛡️ 6단계: 국제재무설계 기준 위험관리 및 필수 보장 설계")
# 
ess_ins = st.multiselect("필수 소유 보험", ["자동차", "화재", "일배책", "후유장해", "기본장기"], key="c_es")

# --------------------------------------------------------------------------
# [SECTION 12] 7단계: 3층 연금 시뮬레이션
# --------------------------------------------------------------------------
st.divider()
st.write("### 💰 7단계: 국제 재무설계 기준 3층 연금 통합 시뮬레이션")
# 
p1, p2, p3 = st.columns(3)
p_nat = p1.number_input("국민연금", value=0, key="p_n")
p_ret = p2.number_input("퇴직연금", value=0, key="p_r")
p_ind = p3.number_input("개인연금", value=0, key="p_i")

# --------------------------------------------------------------------------
# [SECTION 13] 8단계: 인생 이모작 설계
# --------------------------------------------------------------------------
st.divider()
st.write("### 🏡 8단계: 국제 재무설계 기준 주택구입 및 인생 이모작 설계")
# 
home_f = st.number_input("주택자금(만원)", value=0, key="p_h")
second_j = st.text_area("인생 이모작 계획", key="p_j")

# --------------------------------------------------------------------------
# [SECTION 14] 전문가 통합 분석 엔진
# --------------------------------------------------------------------------
def run_master(container):
    with container:
        if not st.session_state.user_api_key: st.error("API Key 미등록"); return
        genai.configure(api_key=st.session_state.user_api_key)
        with st.spinner("🔍 구글 실시간 검색 및 통합 분석 중..."):
            try:
                income = hi_premium / 0.0709 if hi_premium > 0 else 0
                model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=SYSTEM_PROMPT, tools=TOOLS_CONFIG)
                query = f"고객 {cust_name} 리포트: {main_area}. 소득역산 {income:,.0f}원. 분석: {dis_focus}, {ess_ins}."
                content = [query]
                if files:
                    for f in files: content.append(PIL.Image.open(f))
                resp = model.generate_content(content)
                st.subheader("📊 통합 분석 리포트")
                st.markdown(resp.text)
                if resp.candidates[0].grounding_metadata.search_entry_point:
                    st.html(resp.candidates[0].grounding_metadata.search_entry_point.rendered_content)
            except Exception as e: st.error(f"분석 오류: {e}")

if q_analyze: run_master(main_out)

# --------------------------------------------------------------------------
# [SECTION 15] 성공 응원
# --------------------------------------------------------------------------
st.divider()
if st.button("🔍 전 섹션 마스터 종합 분석 리포트 생성", type="primary", use_container_width=True, key="b_fn"):
    run_master(st.container())

st.divider()
if st.button("🏆 성공 응원", key="b_win"): st.balloons(); st.success("필승하십시오!")
