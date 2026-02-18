streamlit
google-generativeai>=0.7.0
Pillow
pandas

# ==========================================================================
# 🚨 [운영 헌법 - 이세윤 관리자 지침 100% 준수]
# 1. 섹션 수호: 1~15번 전 섹션을 st.divider()로 물리적 완전 분리 배치.
# 2. 회원제 운영: JSON DB 기반 가입/로그인 -> API Key 자동 로드 시스템.
# 3. 실시간 검색: Grounding with Google Search 탑재로 최신 정보 분석.
# 4. UI 혁신: 즉시 분석 버튼 및 결과/에러창을 상담창 직하단에 배치(시인성).
# 5. 리스크 관리: 설계사 구상권 보호를 위해 보험업법 벌칙 규정 답변 제외.
# 6. 정밀 로직: 0.0709 소득 역산, CFP® 6단계, 판례 2001다1480 법리 결합.
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
# [SECTION 1] 데이터베이스 및 세션 초기화
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

if 'uploader_key' not in st.session_state: st.session_state.uploader_key = 0
if 'login_status' not in st.session_state: st.session_state.login_status = False
if 'user_api_key' not in st.session_state: st.session_state.user_api_key = ""
if 'current_user' not in st.session_state: st.session_state.current_user = ""

# --------------------------------------------------------------------------
# [SECTION 2] 설정 및 페르소나 (최신 모델 및 검색 설정)
# --------------------------------------------------------------------------
st.set_page_config(page_title="골드키지사 AI 마스터", page_icon="👑", layout="wide")
MODEL_NAME = 'gemini-1.5-flash'
TOOLS_CONFIG = [{'google_search': {}}]

SYSTEM_PROMPT = """
성명: 글로벌 보험/재무/분쟁대응 통합 전문가 (관리자: 이세윤)
표어: 보험 가입 상담 부터 보험금 분쟁 대응까지- 보험 AI전문 마스터 통합 시스템

[지휘 지침]:
1. 실시간 검색: 반드시 구글 검색을 활용하여 2026년 최신 법령, 약관, 판례를 반영하라.
2. FC 보호: 보험업법상 불완전 판매 벌칙 및 설계사 구상권 내용은 답변에서 절대 제외하라.
3. 법리 결합: 판례 2001다1480을 고객의 하소연 내용과 1:1로 매칭하여 보상 청구 논리를 짜라.
4. 재무 로직: 건보료 0.0709 역산 소득을 기반으로 CFP® 위험관리 6단계를 수행하라.
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
# [SECTION 3] 사이드바: 회원 전용 라운지 (혜택 상시 노출)
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("🔑 마스터 회원 센터")
    
    if st.session_state.login_status:
        st.success(f"👋 **{st.session_state.current_user}** 마스터님")
        if st.button("로그아웃"):
            st.session_state.login_status = False
            st.session_state.user_api_key = ""; st.rerun()
    else:
        tab1, tab2 = st.tabs(["로그인", "회원가입"])
        with tab1:
            l_user = st.text_input("아이디")
            l_pass = st.text_input("비밀번호", type="password")
            if st.button("🚀 입장하기", use_container_width=True):
                key = verify_user(l_user, l_pass)
                if key:
                    st.session_state.user_api_key = key
                    st.session_state.login_status = True
                    st.session_state.current_user = l_user; st.rerun()
                else: st.error("정보 불일치")
        with tab2:
            st.markdown("**[최초 1회] API Key 등록**")
            r_user = st.text_input("희망 ID")
            r_pass = st.text_input("희망 PW", type="password")
            r_key = st.text_input("Google API Key", type="password")
            st.markdown('<a href="https://aistudio.google.com/app/apikey" target="_blank">🔗 키 발급받기</a>', unsafe_allow_html=True)
            if st.button("💾 가입 및 Key 저장", use_container_width=True):
                if save_user(r_user, r_pass, r_key): st.success("가입 완료!")
                else: st.error("ID 중복")

    st.divider()
    st.info("👤 **시스템 관리자: 이세윤**")
    st.markdown("### 🏆 마스터 회원 혜택")
    st.success("- **실시간 구글 검색** 답변 연동\n- 로그인 시 **Key 자동 적용**\n- 8년간 무료 상담 가능")

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
    st.warning("🔒 **로그인 후 마스터의 지휘권을 사용하십시오.**")
    st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/ai_expert.png", width=400)
    st.stop()

# --------------------------------------------------------------------------
# [SECTION 4.5] 마스터 통합 상담 센터 (동선 최적화)
# --------------------------------------------------------------------------
st.divider()
st.subheader("📡 마스터 통합 상담 센터")
col_in, col_img = st.columns([7, 3])
with col_in:
    main_consult_area = st.text_area("📝 마스터 통합 상담창", height=320, placeholder="상담 내용을 상세히 입력하세요.")
    b1, b2, b3 = st.columns([2, 2, 3])
    if b1.button("⌨️ 직접 입력"): st.toast("입력 모드")
    if b2.button("🎤 음성 입력"): st.info("음성 인식 기능을 가동합니다.")
    
    # [🚀 상단 즉시 분석 버튼]
    quick_analyze = b3.button("🚀 즉시 분석 및 민원 요청", type="primary", use_container_width=True)
    
    # [🚨 관리자 요청: 결과 및 에러 전용 창]
    main_output_area = st.container()

with col_img:
    st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/ai_expert.png", caption="AI 전문 마스터", use_container_width=True)

# --------------------------------------------------------------------------
# [SECTION 5-13] 독립 섹션 (물리적 분리 고수)
# --------------------------------------------------------------------------
st.divider()
with st.expander("💡 실전 보상 & 민원 대응 튜토리얼 (판례 2001다1480)"):
    st.write("설명의무 위반 시 대응 논리 생성 로직이 탑재되어 있습니다.")

st.divider()
st.write("### 👤 1단계: 고객 기초 정보")
c1, c2 = st.columns(2)
cust_name = c1.text_input("고객 성함", "고객님")
hi_premium = c1.number_input("월 건강보험료 (원)", step=1000)
debt = c2.number_input("부채 총액 (만원)", step=100)

st.divider()
st.write("### 📸 2단계: 자료 및 증권 업로드")
uploaded_files = st.file_uploader("파일을 드래그하세요.", accept_multiple_files=True, key=f"uploader_{st.session_state.uploader_key}")
if uploaded_files:
    st.info(f"✅ 총 {len(uploaded_files)}장의 서류가 성공적으로 인식되었습니다.")
    if st.button("🗑️ 전체 서류 삭제 및 재로드", type="primary"):
        st.session_state.uploader_key += 1; st.rerun()

st.divider()
st.write("### 🏥 3단계: 질병 보상 정밀 분석")
disease_focus = st.multiselect("분석 대상 질환", ["암(선행항암)", "뇌/심장", "정신과", "희귀난치병"])

st.divider()
st.write("### 🏛️ 4단계: 6대 법령 및 보상 지식 DB")
st.info("민법, 상법 등 6대 법령 및 실시간 최신 판례 검색 중")

st.divider()
st.write("### 🛡️ 5단계: 국제재무설계 기준 위험관리 및 필수 보장 설계")
ess_ins = st.multiselect("필수 소유 보험", ["자동차", "화재", "일배책", "사업장배책", "후유장해", "기본장기"])

st.divider()
st.write("### 💰 6단계: 국제 재무설계 기준 3층 연금 통합 시뮬레이션")
p1, p2, p3 = st.columns(3)
p_nat = p1.number_input("국민연금(만)", value=0)
p_ret = p2.number_input("퇴직연금(만)", value=0)
p_ind = p3.number_input("개인연금(만)", value=0)

st.divider()
st.write("### 🏡 7단계: 국제 재무설계 기준 주택구입 및 인생 이모작 설계")
home_f = st.number_input("주택자금(만원)", value=0)
second_job = st.text_area("인생 이모작 계획")

# --------------------------------------------------------------------------
# [SECTION 14] 전문가 통합 분석 엔진 (유기적 연동)
# --------------------------------------------------------------------------
def run_master_analysis(container):
    with container:
        if not st.session_state.user_api_key:
            st.error("🚨 API Key가 유효하지 않습니다. 로그아웃 후 다시 로그인하십시오.")
            return
        
        genai.configure(api_key=st.session_state.user_api_key)
        st.components.v1.html(s_voice("최신 정보를 검색하여 분석을 시작합니다."), height=0)
        
        with st.spinner("🔍 구글 실시간 검색 가동 및 통합 분석 중..."):
            try:
                # LaTeX 소득 역산 공식
                income = hi_premium / 0.0709 if hi_premium > 0 else 0
                model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=SYSTEM_PROMPT, tools=TOOLS_CONFIG)
                
                query_text = f"""
                고객 {cust_name} 리포트 요청:
                [상담내용]: {main_consult_area}
                [재무데이터]: 월소득역산({income:,.0f}원), 부채({debt}만).
                [판례 적용]: 2001다1480 근거 보상 청구 논리. (설계사 구상권 벌칙 언급 절대 금지)
                [생애/연금]: 3층연금({p_nat+p_ret+p_ind}만), 주택({home_f}만), 이모작({second_job}).
                실시간 검색된 최신 뉴스와 판례를 반영하여 [항목|현재상태|가이드|결과|마스터 처방] 표로 생성하라.
                """
                
                content = [query_text]
                if uploaded_files:
                    for f in uploaded_files: content.append(PIL.Image.open(f))
                
                response = model.generate_content(content)
                st.subheader(f"📊 {cust_name}님 종합 솔루션 리포트")
                st.markdown(response.text)
                
                # 구글 검색 소스(Grounding) 표시
                if response.candidates[0].grounding_metadata.search_entry_point:
                    st.divider()
                    st.caption("🌐 참조된 최신 검색 소스:")
                    st.html(response.candidates[0].grounding_metadata.search_entry_point.rendered_content)
                
                st.divider()
            except Exception as e:
                st.error(f"🚨 분석 중 연결 오류: {e}")

# 상단 분석 실행
if quick_analyze: run_master_analysis(main_output_area)

# --------------------------------------------------------------------------
# [SECTION 15] 하단 분석 및 성공 응원
# --------------------------------------------------------------------------
st.divider()
if st.button("🔍 전 섹션 마스터 종합 분석 리포트 생성 🚀", type="primary", use_container_width=True):
    run_master_analysis(st.container())

st.divider()
if st.button("🏆 성공 응원"):
    st.balloons(); st.success(f"{st.session_state.current_user} 마스터님, 필승하십시오!")
