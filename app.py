# ==========================================================================
# 🚨 [운영 헌법 - 이세윤 관리자 지침 100% 준수]
# 1. 섹션 독립 수호: 1~15번 전 섹션을 st.divider()로 물리적 완전 분리 배치.
# 2. 관리자 프리패스: admin / gold1234 계정으로 DB 상관없이 즉시 로그인 보장.
# 3. 기술 해법 적용: AI STUDIO 방식의 Grounding(구글검색) 및 JSON DB 완벽 이식.
# 4. 리스크 관리: 설계사 구상권 보호를 위해 보험업법 벌칙 규정은 답변에서 제외.
# 5. UI 혁신: 즉시 분석 버튼 및 결과창을 상담창(Section 4.5) 직하단에 배치.
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

# [🚨 관리자 전용 마스터 계정]
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
    # 1순위: 관리자 마스터 계정 체크 (DB 파일 없어도 무조건 통과)
    if username == MASTER_ID and password == MASTER_PW:
        return "MASTER_ACCESS"
    # 2순위: 일반 회원 DB 체크
    db = load_db()
    if username in db and db[username]['password'] == password:
        return db[username]['api_key']
    return None

if 'uploader_key' not in st.session_state: st.session_state.uploader_key = 0
if 'login_status' not in st.session_state: st.session_state.login_status = False
if 'user_api_key' not in st.session_state: st.session_state.user_api_key = ""
if 'current_user' not in st.session_state: st.session_state.current_user = ""

# --------------------------------------------------------------------------
# [SECTION 2] 페르소나 및 음성/STT 엔진 설정
# --------------------------------------------------------------------------
MODEL_NAME = 'gemini-1.5-flash'
TOOLS_CONFIG = [{'google_search': {}}] # 실시간 구글 검색 활성화

SYSTEM_PROMPT = """
성명: 글로벌 보험/재무/분쟁대응 통합 전문가 (관리자: 이세윤)
표어: 보험 가입 상담 부터 보험금 분쟁 대응까지- 보험 AI전문 마스터 통합 시스템
[지휘 지침]:
- 실시간 구글 검색을 통해 2026년 최신 법령, 판례, 의학 정보를 반영하여 분석하라.
- 보험업법상 불완전 판매 벌칙 및 설계사 구상권 내용은 절대 언급하지 마라.
- 판례 2001다1480 및 상법 근거를 고객 사건과 매칭하여 보상 논리를 생성하라.
- 건보료 0.0709 소득 역산 및 CFP® 6단계 프로세스를 준수하라.
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
# [SECTION 3] 사이드바: 관리자/회원 전용 로그인 센터
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("🔑 마스터 회원 센터")
    if st.session_state.login_status:
        st.success(f"👋 **{st.session_state.current_user}** 마스터님")
        if st.button("로그아웃"):
            st.session_state.login_status = False
            st.session_state.user_api_key = ""
            st.session_state.current_user = ""
            st.rerun()
    else:
        tab1, tab2 = st.tabs(["로그인", "회원가입"])
        with tab1:
            l_user = st.text_input("아이디")
            l_pass = st.text_input("비밀번호", type="password")
            if st.button("🚀 로그인", use_container_width=True):
                result = verify_user(l_user, l_pass)
                if result:
                    st.session_state.login_status = True
                    st.session_state.current_user = l_user
                    if result == "MASTER_ACCESS":
                        st.session_state.user_api_key = st.secrets.get("GEMINI_API_KEY", "")
                    else:
                        st.session_state.user_api_key = result
                    st.rerun()
                else: st.error("정보가 일치하지 않습니다.")
        with tab2:
            st.markdown("**신규 회원 등록**")
            r_user = st.text_input("ID", key="reg_u")
            r_pass = st.text_input("PW", type="password", key="reg_p")
            r_key = st.text_input("API Key", type="password", key="reg_k")
            if st.button("💾 가입 및 저장", use_container_width=True):
                if save_user(r_user, r_pass, r_key): st.success("가입 완료! 로그인 해주세요.")
                else: st.error("가입 실패 또는 ID 중복")

    st.divider()
    st.info(f"👤 **시스템 관리자: 이세윤**")
    st.markdown("### 🏆 회원제 혜택\n- 로그인 시 API Key 자동 로드\n- 실시간 검색 기반 정밀 분석\n- 8년간 무료 상담 서비스")

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
# [SECTION 4.5] 마스터 통합 상담 센터 (UI 시인성 최적화)
# --------------------------------------------------------------------------
st.divider()
st.subheader("📡 마스터 통합 상담 센터")
col_in, col_img = st.columns([7, 3])
with col_in:
    main_consult_area = st.text_area("📝 마스터 통합 상담창", height=320, placeholder="가입 상담, 보상 분석, 민원 요청 사항 등을 자유롭게 입력하세요.")
    b1, b2, b3 = st.columns([2, 2, 3])
    if b1.button("⌨️ 직접 입력", use_container_width=True): st.toast("직접 입력 모드 활성화")
    if b2.button("🎤 음성 입력", use_container_width=True): st.info("음성 인식 대기 중...")
    
    # [🚀 즉시 분석 버튼]
    quick_analyze = b3.button("🚀 즉시 분석 및 민원 요청", type="primary", use_container_width=True)
    
    # [🚨 결과 및 에러 출력 전용 구역]
    main_output_area = st.container()

with col_img:
    st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/ai_expert.png", use_container_width=True)

# --------------------------------------------------------------------------
# [SECTION 5] 실전 보상 & 민원 대응 튜토리얼 (판례 2001다1480)
# --------------------------------------------------------------------------
st.divider()
with st.expander("💡 실전 보상 & 민원 대응 튜토리얼 (판례 2001다1480)", expanded=False):
    st.write("보험사의 설명의무 위반 시 대응 법리와 개별 사건을 연계한 마스터만의 전문 로직입니다.")

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
# [SECTION 7] 2단계: 자료 및 증권 업로드 (삭제 버튼 상시화)
# --------------------------------------------------------------------------
st.divider()
st.write("### 📸 2단계: 자료 및 증권 업로드")
files = st.file_uploader("증권 및 관련 서류를 드래그하세요.", accept_multiple_files=True, key=f"u_{st.session_state.uploader_key}")
if files:
    st.info(f"✅ 총 {len(files)}장의 서류가 성공적으로 인식되었습니다.")
    # [🚨 빨간색 전체 삭제 버튼]
    if st.button("🗑️ 전체 서류 삭제 및 재로드", type="primary", use_container_width=True):
        st.session_state.uploader_key += 1
        st.rerun()

# --------------------------------------------------------------------------
# [SECTION 8] 3단계: 질병 보상 정밀 분석
# --------------------------------------------------------------------------
st.divider()
st.write("### 🏥 3단계: 질병 보상 정밀 분석")
dis_focus = st.multiselect("분석 대상 질환 선택", ["암(선행항암)", "뇌/심장", "정신과", "희귀난치병"])

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
st.info("민법, 상법, 보험업법 등 6대 법령 기반 실시간 최신 판례 검색 가동 중")

# --------------------------------------------------------------------------
# [SECTION 11] 6단계: 국제재무설계 기준 위험관리 및 필수 보장 설계
# --------------------------------------------------------------------------
st.divider()
st.write("### 🛡️ 6단계: 국제재무설계 기준 위험관리 및 필수 보장 설계")

ess_ins = st.multiselect("필수 소유 보험 선택", ["자동차", "화재", "일상생활배상책임", "사업장배책", "후유장해", "기본통합장기"])

# --------------------------------------------------------------------------
# [SECTION 12] 7단계: 국제 재무설계 기준 3층 연금 통합 시뮬레이션
# --------------------------------------------------------------------------
st.divider()
st.write("### 💰 7단계: 국제 재무설계 기준 3층 연금 통합 시뮬레이션")

p_col = st.columns(3)
p_nat = p_col[0].number_input("국민연금(만)", value=0)
p_ret = p_col[1].number_input("퇴직연금(만)", value=0)
p_ind = p_col[2].number_input("개인연금(만)", value=0)

# --------------------------------------------------------------------------
# [SECTION 13] 8단계: 국제 재무설계 기준 주택구입 및 인생 이모작 설계
# --------------------------------------------------------------------------
st.divider()
st.write("### 🏡 8단계: 국제 재무설계 기준 주택구입 및 인생 이모작 설계")

home_f = st.number_input("주택구입 필요자금(만원)", value=0)
second_j = st.text_area("인생 이모작(전직/창업) 계획 및 재무 고민")

# --------------------------------------------------------------------------
# [SECTION 14] 전문가 통합 분석 엔진 (유기적 한 몸 구동)
# --------------------------------------------------------------------------
def run_master_analysis(container):
    with container:
        # API 설정 강제 확인
        if not st.session_state.user_api_key:
            st.error("🚨 API Key가 연결되지 않았습니다. 사이드바 하단에서 키를 확인하십시오.")
            return
        
        genai.configure(api_key=st.session_state.user_api_key)
        st.components.v1.html(s_voice("최신 정보를 검색하여 전 섹션 통합 분석을 시작합니다."), height=0)
        
        with st.spinner("🔍 구글 실시간 검색 가동 및 마스터 통합 분석 중..."):
            try:
                # [🚨 핵심 로직] 소득 역산: $Income = \frac{Premium}{0.0709}$
                income = hi_premium / 0.0709 if hi_premium > 0 else 0
                model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=SYSTEM_PROMPT, tools=TOOLS_CONFIG)
                
                query_text = f"""
                고객 {cust_name} 종합 마스터 리포트 (유기적 통합 모드):
                [상담본부]: {main_consult_area}
                [로드서류]: 총 {len(files) if files else 0}장 대조 분석.
                [재무데이터]: 월소득역산({income:,.0f}원), 부채({debt}만).
                [분석대상]: {dis_focus} 및 {ess_ins} 기반 국제재무설계 기준 진단.
                [생애설계]: 3층연금({p_nat+p_ret+p_ind}만), 주택({home_f}만), 이모작({second_j}).
                판례 2001다1480 및 실시간 검색된 최신 법령/뉴스를 근거로 처방하십시오. (설계사 벌칙 제외 필)
                결과는 [항목|현재상태|가이드|결과|마스터 처방] 표로 생성하라.
                """
                
                content_list = [query_text]
                if files:
                    for f in files: content_list.append(PIL.Image.open(f))
                
                response = model.generate_content(content_list)
                st.subheader(f"📊 {cust_name}님 통합 솔루션 리포트")
                st.markdown(response.text)
                
                # 구글 검색 출처 표시 (Grounding Metadata)
                if response.candidates and response.candidates[0].grounding_metadata and response.candidates[0].grounding_metadata.search_entry_point:
                    st.divider()
                    st.caption("🌐 참조된 실시간 검색 소스:")
                    st.html(response.candidates[0].grounding_metadata.search_entry_point.rendered_content)
                
                st.divider()
            except Exception as e:
                st.error(f"🚨 분석 중 오류 발생: {e}")

# 상단 분석 트리거
if quick_analyze: run_master_analysis(main_output_area)

# --------------------------------------------------------------------------
# [SECTION 15] 하단 최종 분석 및 성공 응원
# --------------------------------------------------------------------------
st.divider()
if st.button("🔍 전 섹션 마스터 종합 분석 리포트 생성 🚀", type="primary", use_container_width=True):
    run_master_analysis(st.container())

st.divider()
if st.button("🏆 관리자 이세윤 & 전문 FC 성공 응원"):
    st.balloons(); st.success(f"{st.session_state.current_user} 마스터님, 최고의 성과를 거두십시오!")
