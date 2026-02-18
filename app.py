# ==========================================================================
# 🚨 [골드키지사 AI 마스터 - 최종 무손실 통합 시스템]
# 기준 1: AI STUDIO의 기술 로직(회원제/검색) 수정 없이 그대로 반영.
# 기준 2: 관리자님의 원본 섹션(1~15번) 구조 및 내용 누락 없이 그대로 유지.
# 기준 3: 두 체계의 유기적 연동을 통한 '한 몸' 구동 실현.
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
# [AI STUDIO 기술 로직] 회원 데이터베이스 핸들링
# --------------------------------------------------------------------------
DB_FILE = 'user_db.json'

def load_db():
    if not os.path.exists(DB_FILE): return {}
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_user(username, password, api_key):
    db = load_db()
    if username in db: return False
    db[username] = {'password': password, 'api_key': api_key}
    with open(DB_FILE, 'w') as f: json.dump(db, f)
    return True

def verify_user(username, password):
    db = load_db()
    if username in db and db[username]['password'] == password:
        return db[username]['api_key']
    return None

# [관리자 고정 계정 설정]
MASTER_ID = "admin"
MASTER_PW = "gold1234"

# --------------------------------------------------------------------------
# [SECTION 1] 기본 설정 및 페르소나 (원본 유지)
# --------------------------------------------------------------------------
st.set_page_config(page_title="골드키지사 AI 마스터", page_icon="👑", layout="wide")

if 'uploader_key' not in st.session_state: st.session_state.uploader_key = 0
if 'login_status' not in st.session_state: st.session_state.login_status = False
if 'user_api_key' not in st.session_state: st.session_state.user_api_key = ""
if 'current_user' not in st.session_state: st.session_state.current_user = ""

MODEL_NAME = 'gemini-1.5-flash'
# [AI STUDIO 기술 로직] 구글 검색 도구 설정
TOOLS_CONFIG = [{'google_search': {}}]

SYSTEM_PROMPT = """
성명: 글로벌 보험/재무/분쟁대응 통합 전문가 (관리자: 이세윤)
표어: 보험 가입 상담 부터 보험금 분쟁 대응까지- 보험 AI전문 마스터 통합 시스템

[지휘 지침]:
1. 실시간 검색: 실시간 구글 검색을 통해 최신 법령, 판례, 의학 정보를 반영하라.
2. FC 보호: 보험업법상 불완전 판매 벌칙 및 설계사 구상권 관련 내용은 답변에서 절대 제외하라.
3. 법리 결합: 판례 2001다1480 및 상법 근거를 고객의 사건 내용과 유기적으로 매칭하라.
4. 재무 로직: 건보료 0.0709 소득 역산 및 CFP® 6단계 프로세스를 준수하라.
"""

# --------------------------------------------------------------------------
# [SECTION 2] 음성 엔진 및 STT (원본 유지)
# --------------------------------------------------------------------------
def s_voice(text, lang='ko-KR'):
    if re.search('[a-zA-Z]{5,}', text): lang = 'en-US'
    return f"""<script>
        window.speechSynthesis.cancel(); 
        var msg = new SpeechSynthesisUtterance("{text}");
        msg.lang = "{lang}"; msg.rate = 0.95; 
        window.speechSynthesis.speak(msg);
    </script>"""

# --------------------------------------------------------------------------
# [SECTION 3] 사이드바: 로그인/회원가입 및 혜택 (AI STUDIO + 원본 통합)
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("🔑 마스터 회원 센터")
    
    if st.session_state.login_status:
        st.success(f"👋 **{st.session_state.current_user}** 마스터님")
        if st.button("로그아웃"):
            st.session_state.login_status = False; st.session_state.user_api_key = ""; st.rerun()
    else:
        tab1, tab2 = st.tabs(["로그인", "회원가입"])
        with tab1:
            l_user = st.text_input("아이디")
            l_pass = st.text_input("비밀번호", type="password")
            if st.button("🚀 로그인", use_container_width=True):
                # 마스터 계정 우선 확인
                if l_user == MASTER_ID and l_pass == MASTER_PW:
                    st.session_state.user_api_key = st.secrets.get("GEMINI_API_KEY", "")
                    st.session_state.login_status = True; st.session_state.current_user = "관리자"; st.rerun()
                else:
                    key = verify_user(l_user, l_pass)
                    if key:
                        st.session_state.user_api_key = key
                        st.session_state.login_status = True; st.session_state.current_user = l_user; st.rerun()
                    else: st.error("정보가 불일치합니다.")
        with tab2:
            st.markdown("**신규 마스터 등록**")
            r_user = st.text_input("희망 아이디")
            r_pass = st.text_input("희망 비밀번호", type="password")
            r_key = st.text_input("Google API Key", type="password")
            if st.button("💾 가입 및 저장", use_container_width=True):
                if save_user(r_user, r_pass, r_key): st.success("가입 완료! 로그인 해주세요.")
                else: st.error("이미 사용 중인 아이디입니다.")

    st.divider()
    st.info("👤 **시스템 관리자: 이세윤**")
    st.markdown("### 🏆 마스터 회원 혜택")
    st.success("- 실시간 검색 연동\n- 로그인 시 Key 자동 로드\n- 8년간 무료 상담 가능권")

# --------------------------------------------------------------------------
# [SECTION 4] 브랜드 상단 UI (원본 유지)
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
    st.warning("🔒 로그인이 필요합니다. 관리자님은 설정된 마스터 계정으로 접속하십시오.")
    st.stop()

# --------------------------------------------------------------------------
# [SECTION 4.5] 마스터 통합 상담 센터 (원본 유지 + AI STUDIO 기술)
# --------------------------------------------------------------------------
st.divider()
st.subheader("📡 마스터 통합 상담 센터")
col_in, col_img = st.columns([7, 3])
with col_in:
    main_consult_area = st.text_area("📝 마스터 통합 상담창", height=320, placeholder="상담 내용을 입력하세요.")
    b1, b2, b3 = st.columns([2, 2, 3])
    if b1.button("⌨️ 직접 입력"): st.toast("입력 가능")
    if b2.button("🎤 음성 입력"): st.info("음성 대기 중...")
    quick_analyze = b3.button("🚀 즉시 분석 및 민원 요청", type="primary", use_container_width=True)
    # 분석 결과 및 에러가 나타나는 전용 구역
    main_output_area = st.container()

with col_img:
    st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/ai_expert.png", use_container_width=True)

# --------------------------------------------------------------------------
# [SECTION 5] 실전 보상 & 민원 대응 튜토리얼 (원본 유지)
# --------------------------------------------------------------------------
st.divider()
with st.expander("💡 실전 보상 & 민원 대응 튜토리얼 (판례 2001다1480)"):
    st.write("보험사의 설명의무 위반 시 대응 법리와 개별 사건을 연계한 전문 로직입니다.")

# --------------------------------------------------------------------------
# [SECTION 6] 1단계: 고객 기초 정보 (원본 유지)
# --------------------------------------------------------------------------
st.divider()
st.write("### 👤 1단계: 고객 기초 정보")
c1, c2 = st.columns(2)
cust_name = c1.text_input("고객 성함", "고객님")
hi_premium = c1.number_input("월 건강보험료 (원)", step=1000)
debt = c2.number_input("부채 총액 (만원)", step=100)

# --------------------------------------------------------------------------
# [SECTION 7] 2단계: 자료 및 증권 업로드 (원본 유지)
# --------------------------------------------------------------------------
st.divider()
st.write("### 📸 2단계: 자료 및 증권 업로드")
uploaded_files = st.file_uploader("파일 로드", accept_multiple_files=True, key=f"u_{st.session_state.uploader_key}")
if uploaded_files:
    st.info(f"✅ 총 {len(uploaded_files)}장의 서류 인식됨")
    if st.button("🗑️ 전체 서류 삭제 및 재로드", type="primary"):
        st.session_state.uploader_key += 1; st.rerun()

# --------------------------------------------------------------------------
# [SECTION 8] 3단계: 질병 보상 정밀 분석 (원본 유지)
# --------------------------------------------------------------------------
st.divider()
st.write("### 🏥 3단계: 질병 보상 정밀 분석")
disease_focus = st.multiselect("분석 대상 질환", ["암(선행항암)", "뇌/심장", "정신과", "희귀난치병"])

# --------------------------------------------------------------------------
# [SECTION 9] 4단계: 삼성/교보 헬스케어 컨설팅 (원본 유지)
# --------------------------------------------------------------------------
st.divider()
st.write("### 💎 4단계: 삼성/교보 헬스케어 컨설팅")
hc_info = st.checkbox("주요 생보사 헬스케어 가이드 포함")

# --------------------------------------------------------------------------
# [SECTION 10] 5단계: 6대 법령 및 보상 지식 DB (원본 유지)
# --------------------------------------------------------------------------
st.divider()
st.write("### 🏛️ 5단계: 6대 법령 및 보상 지식 DB")
st.info("민법, 상법 등 6대 법령 근거 및 실시간 최신 판례 검색 중")

# --------------------------------------------------------------------------
# [SECTION 11] 6단계: 위험관리 및 필수 보장 설계 (원본 유지)
# --------------------------------------------------------------------------
st.divider()
st.write("### 🛡️ 6단계: 국제재무설계 기준 위험관리 및 필수 보장 설계")
ess_ins = st.multiselect("필수 소유 보험", ["자동차", "화재", "일배책", "사업장배책", "후유장해", "기본장기"])

# --------------------------------------------------------------------------
# [SECTION 12] 7단계: 3층 연금 시뮬레이션 (원본 유지)
# --------------------------------------------------------------------------
st.divider()
st.write("### 💰 7단계: 국제 재무설계 기준 3층 연금 통합 시뮬레이션")
p_col = st.columns(3)
p_nat = p_col[0].number_input("국민연금(만)", value=0)
p_ret = p_col[1].number_input("퇴직연금(만)", value=0)
p_ind = p_col[2].number_input("개인연금(만)", value=0)

# --------------------------------------------------------------------------
# [SECTION 13] 8단계: 주택구입 및 인생 이모작 설계 (원본 유지)
# --------------------------------------------------------------------------
st.divider()
st.write("### 🏡 8단계: 국제 재무설계 기준 주택구입 및 인생 이모작 설계")
home_f = st.number_input("주택자금(만원)", value=0)
second_job = st.text_area("인생 이모작 계획")

# --------------------------------------------------------------------------
# [SECTION 14] 전문가 통합 분석 엔진 (유기적 한 몸 - AI STUDIO 기술 적용)
# --------------------------------------------------------------------------
def run_master_analysis(container):
    with container:
        if not st.session_state.user_api_key:
            # 관리자 계정인데 secrets에 키가 없을 경우 대비
            st.session_state.user_api_key = st.text_input("🔑 API Key를 수동으로 입력하십시오.", type="password")
            if not st.session_state.user_api_key: return

        genai.configure(api_key=st.session_state.user_api_key)
        st.components.v1.html(s_voice("전 섹션 유기적 통합 분석을 시작합니다."), height=0)
        
        with st.spinner("🔍 구글 실시간 검색 엔진 가동 및 통합 분석 중..."):
            try:
                # [원본 유지] 소득 역산 로직
                income = hi_premium / 0.0709 if hi_premium > 0 else 0
                
                # [AI STUDIO 기술] 모델 및 도구 호출
                model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=SYSTEM_PROMPT, tools=TOOLS_CONFIG)
                
                query_text = f"""
                고객 {cust_name} 종합 마스터 리포트:
                [상담본부]: {main_consult_area}
                [재무데이터]: 월소득역산({income:,.0f}원), 부채({debt}만).
                [판례 적용]: 2001다1480 근거 보상 대응 논리. (설계사 구상권 벌칙 언급 절대 금지)
                [생애/연금]: 3층연금({p_nat+p_ret+p_ind}만), 주택자금({home_f}만), 이모작({second_job}).
                실시간 검색된 최신 뉴스/판례를 반영하여 [항목|현재상태|가이드|결과|마스터 처방] 표로 생성하라.
                """
                
                content = [query_text]
                if uploaded_files:
                    for f in uploaded_files: content.append(PIL.Image.open(f))
                
                response = model.generate_content(content)
                st.subheader(f"📊 {cust_name}님 통합 솔루션 리포트")
                st.markdown(response.text)
                
                # [AI STUDIO 기술] 구글 검색 출처 표시
                if response.candidates and response.candidates[0].grounding_metadata and response.candidates[0].grounding_metadata.search_entry_point:
                    st.divider()
                    st.caption("🌐 참조된 최신 검색 소스:")
                    st.html(response.candidates[0].grounding_metadata.search_entry_point.rendered_content)
                
            except Exception as e:
                st.error(f"🚨 분석 중 오류 발생: {e}")

if quick_analyze: run_master_analysis(main_output_area)

# --------------------------------------------------------------------------
# [SECTION 15] 하단 최종 분석 및 성공 응원 (원본 유지)
# --------------------------------------------------------------------------
st.divider()
if st.button("🔍 전 섹션 마스터 종합 분석 리포트 생성 🚀", type="primary", use_container_width=True):
    run_master_analysis(st.container())

st.divider()
if st.button("🏆 성공 응원"):
    st.balloons(); st.success(f"{st.session_state.current_user} 마스터님, 필승하십시오!")
