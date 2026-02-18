# ==========================================================================
# 🚨 [운영 헌법 - 이세윤 관리자 지침 100% 수호]
# 1. 이미지 복구: 설명용 태그 제거 및 st.image() 정상 가동 확인.
# 2. 404 에러 해결: 모델명 호출 방식을 최신 SDK 규격으로 정규화.
# 3. 섹션 독립 수호: 1~15번 전 섹션을 st.divider()로 물리적 완전 분리 배치.
# 4. 관리자 프리패스: admin / gold1234로 즉시 로그인 보장.
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
    # 1순위: 관리자 마스터 계정 (무조건 승인)
    if username == MASTER_ID and password == MASTER_PW:
        return "MASTER_ACCESS"
    # 2순위: 일반 회원 DB 확인
    db = load_db()
    if username in db and db[username]['password'] == password:
        return db[username]['api_key']
    return None

if 'uploader_key' not in st.session_state: st.session_state.uploader_key = 0
if 'login_status' not in st.session_state: st.session_state.login_status = False
if 'user_api_key' not in st.session_state: st.session_state.user_api_key = ""
if 'current_user' not in st.session_state: st.session_state.current_user = ""

# --------------------------------------------------------------------------
# [SECTION 2] 페르소나 및 경로 정규화 (404 방어)
# --------------------------------------------------------------------------
# [🚨 404 해결] 'models/' 접두사 없이 모델명만 사용
MODEL_NAME = 'gemini-1.5-flash'
# [🚨 검색 도구 최신 규격 적용]
TOOLS_CONFIG = [{'google_search_retrieval': {}}] 

SYSTEM_PROMPT = """
성명: 글로벌 보험/재무/분쟁대응 통합 전문가 (관리자: 이세윤)
표어: 보험 가입 상담 부터 보험금 분쟁 대응까지- 보험 AI전문 마스터 통합 시스템

[지휘 강령]:
1. 구글 실시간 검색(Grounding)을 통해 2026년 최신 법령, 판례, 의학 정보를 반드시 반영하라.
2. 보험업법상 설계사 구상권 관련 벌칙 규정은 답변에서 철저히 제외하라.
3. 판례 2001다1480 및 상법 근거를 고객 사건과 매칭하여 보상 논리를 생성하라.
4. 건보료 0.0709 소득 역산 및 CFP® 6단계 프로세스를 준수하라.
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
# [SECTION 3] 사이드바: 마스터 회원 센터 (혜택 복구)
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
            l_user = st.text_input("아이디", key="l_id_final")
            l_pass = st.text_input("비밀번호", type="password", key="l_pw_final")
            if st.button("🚀 로그인", use_container_width=True, key="l_btn_final"):
                res = verify_user(l_user, l_pass)
                if res:
                    st.session_state.login_status = True
                    st.session_state.current_user = l_user
                    # 관리자 로그인 시 secrets 혹은 수동 입력 유도
                    st.session_state.user_api_key = st.secrets.get("GEMINI_API_KEY", "") if res == "MASTER_ACCESS" else res
                    st.rerun()
                else: st.error("정보 불일치")
        with tab2:
            st.info("신규 회원은 관리자 승인 후 혜택이 적용됩니다.")

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
# [SECTION 4.5] 마스터 통합 상담 센터 (UI 최적화)
# --------------------------------------------------------------------------
st.divider()
st.subheader("📡 마스터 통합 상담 센터")
col_in, col_img = st.columns([7, 3])
with col_in:
    main_consult_area = st.text_area("📝 마스터 통합 상담창", height=320, placeholder="상담 내용을 상세히 입력하십시오.", key="m_area_final")
    b1, b2, b3 = st.columns([2, 2, 3])
    if b1.button("⌨️ 직접 입력", key="b_in_final"): st.toast("입력 모드")
    if b2.button("🎤 음성 입력", key="b_stt_final"): st.info("음성 대기 중...")
    quick_analyze = b3.button("🚀 즉시 분석 및 민원 요청", type="primary", use_container_width=True, key="b_ana_final")
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
cust_name = c1.text_input("고객 성함", "고객님", key="c_nm_final")
hi_premium = c1.number_input("월 건강보험료(원)", value=0, step=1000, key="c_pr_final")
debt = c2.number_input("부채 총액(만원)", value=0, step=100, key="c_db_final")

# --------------------------------------------------------------------------
# [SECTION 7] 2단계: 자료 및 증권 업로드
# --------------------------------------------------------------------------
st.divider()
st.write("### 📸 2단계: 자료 및 증권 업로드")
files = st.file_uploader("증권 및 관련 서류 로드", accept_multiple_files=True, key=f"u_{st.session_state.uploader_key}")
if files:
    st.info(f"✅ 총 {len(files)}장의 서류 인식됨")
    if st.button("🗑️ 전체 서류 삭제", type="primary", key="f_del_final"):
        st.session_state.uploader_key += 1; st.rerun()

# --------------------------------------------------------------------------
# [SECTION 8] 3단계: 질병 보상 정밀 분석
# --------------------------------------------------------------------------
st.divider()
st.write("### 🏥 3단계: 질병 보상 정밀 분석")
dis_focus = st.multiselect("분석 대상 질환", ["암(선행항암)", "뇌/심장", "정신과", "희귀난치병"], key="c_dis_final")

# --------------------------------------------------------------------------
# [SECTION 9] 4단계: 삼성/교보 헬스케어 컨설팅
# --------------------------------------------------------------------------
st.divider()
st.write("### 💎 4단계: 삼성/교보 헬스케어 컨설팅")
hc_info = st.checkbox("주요 생보사 헬스케어 서비스 안내 포함", key="c_hc_final")

# --------------------------------------------------------------------------
# [SECTION 10] 5단계: 6대 법령 및 보상 지식 DB
# --------------------------------------------------------------------------
st.divider()
st.write("### 🏛️ 5단계: 6대 법령 및 보상 지식 DB")
st.info("민법, 상법, 보험업법 등 6대 법령 및 실시간 판례 검색 가동")

# --------------------------------------------------------------------------
# [SECTION 11] 6단계: 위험관리 및 필수 보장 설계 (이미지 정상화)
# --------------------------------------------------------------------------
st.divider()
st.write("### 🛡️ 6단계: 국제재무설계 기준 위험관리 및 필수 보장 설계")
# [🚨 이미지 태그 제거 후 실제 코드 적용]
st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/dispute_process.png", caption="보험 분쟁 해결 프로세스", use_container_width=True)
ess_ins = st.multiselect("필수 소유 보험", ["자동차", "화재", "일배책", "후유장해", "기본장기"], key="c_ess_final")

# --------------------------------------------------------------------------
# [SECTION 12] 7단계: 3층 연금 통합 시뮬레이션 (이미지 정상화)
# --------------------------------------------------------------------------
st.divider()
st.write("### 💰 7단계: 국제 재무설계 기준 3층 연금 통합 시뮬레이션")
# [🚨 이미지 태그 제거 후 실제 코드 적용]
st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/pension_3tier.png", caption="3층 연금 체계", use_container_width=True)
p_cols = st.columns(3)
p_nat = p_cols[0].number_input("국민연금(만)", value=0, key="p_n_final")
p_ret = p_cols[1].number_input("퇴직연금(만)", value=0, key="p_r_final")
p_ind = p_cols[2].number_input("개인연금(만)", value=0, key="p_i_final")

# --------------------------------------------------------------------------
# [SECTION 13] 8단계: 인생 이모작 설계 (이미지 정상화)
# --------------------------------------------------------------------------
st.divider()
st.write("### 🏡 8단계: 국제 재무설계 기준 주택구입 및 인생 이모작 설계")
# [🚨 이미지 태그 제거 후 실제 코드 적용]
st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/cfp_process.png", caption="CFP 6단계 프로세스", use_container_width=True)
home_f = st.number_input("주택자금(만원)", value=0, key="p_h_final")
second_j = st.text_area("인생 이모작 계획", key="p_j_final")

# --------------------------------------------------------------------------
# [SECTION 14] 전문가 통합 분석 엔진 (404 원천 해결)
# --------------------------------------------------------------------------
def run_master_analysis(container):
    with container:
        if not st.session_state.user_api_key:
            st.error("🚨 API Key가 없습니다. 사이드바 하단에서 키를 확인하십시오."); return
        
        genai.configure(api_key=st.session_state.user_api_key)
        st.components.v1.html(s_voice("전 섹션 유기적 통합 분석 및 실시간 검색을 시작합니다."), height=0)
        
        with st.spinner("🔍 구글 실시간 검색 및 마스터 통합 분석 중..."):
            try:
                income = hi_premium / 0.0709 if hi_premium > 0 else 0
                model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=SYSTEM_PROMPT, tools=TOOLS_CONFIG)
                
                query = f"""
                고객 {cust_name} 종합 마스터 리포트:
                [상담본부]: {main_consult_area}
                [재무데이터]: 월소득역산({income:,.0f}원), 부채({debt}만).
                [분석대상]: {dis_focus} 및 {ess_ins} 기반 국제재무설계 진단. 
                [생애설계]: 3층연금({p_nat+p_ret+p_ind}만), 주택({home_f}만), 이모작({second_j}).
                결과는 판례 2001다1480 매칭 및 실시간 검색 결과를 바탕으로 [항목|현재상태|가이드|결과|마스터 처방] 표로 생성하라.
                ※ 보험업법상 설계사 벌칙 규정은 답변에서 절대 제외할 것.
                """
                
                content = [query]
                if files:
                    for f in files: content.append(PIL.Image.open(f))
                
                resp = model.generate_content(content)
                st.subheader(f"📊 {cust_name}님 통합 분석 리포트")
                st.markdown(resp.text)
                
                if resp.candidates and resp.candidates[0].grounding_metadata and resp.candidates[0].grounding_metadata.search_entry_point:
                    st.divider()
                    st.caption("🌐 참조된 실시간 검색 소스:")
                    st.html(resp.candidates[0].grounding_metadata.search_entry_point.rendered_content)
            except Exception as e:
                st.error(f"🚨 분석 시스템 오류: {e}")
                if "404" in str(e): st.warning("💡 API Key 권한을 확인하거나, 잠시 후 다시 시도하십시오.")

if quick_analyze: run_master_analysis(main_output)

# --------------------------------------------------------------------------
# [SECTION 15] 하단 최종 분석 및 성공 응원
# --------------------------------------------------------------------------
st.divider()
if st.button("🔍 전 섹션 마스터 종합 분석 리포트 생성 🚀", type="primary", use_container_width=True, key="b_fn_final"):
    run_master_analysis(st.container())

st.divider()
if st.button("🏆 관리자 이세윤 & 전문 FC 성공 응원", key="b_win_final"):
    st.balloons(); st.success(f"{st.session_state.current_user} 마스터님, 필승하십시오!")
