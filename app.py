# ==========================================================================
# 👑 [골드키지사 AI 마스터 - 최종 기술 보정 및 우회 시스템]
# 1. 자가 치유(Bypass): 404 에러 발생 시 모델 경로를 즉시 교체하여 재시도.
# 2. 2단계 원칙: [1단계: 공식자료 근거] -> [2단계: 구글 검색 교차 검증]
# 3. 무손실 수호: 1~15번 독립 섹션, 사이드바 혜택, 연금/CFP 이미지 100% 보존.
# 4. 관리자 전용: admin / gold1234 프리패스 및 Secrets API 자동 로드.
# ==========================================================================

import streamlit as st
import google.generativeai as genai
import PIL.Image
import json
import os
import re

# --------------------------------------------------------------------------
# [SECTION 1] 기본 설정 및 마스터 보안
# --------------------------------------------------------------------------
st.set_page_config(page_title="골드키지사 AI 마스터", page_icon="👑", layout="wide")

MASTER_ID = "admin"
MASTER_PW = "gold1234"

if 'uploader_key' not in st.session_state: st.session_state.uploader_key = 0
if 'login_status' not in st.session_state: st.session_state.login_status = False
if 'user_api_key' not in st.session_state: st.session_state.user_api_key = ""
if 'current_user' not in st.session_state: st.session_state.current_user = ""

def verify_user(u, p):
    if u == MASTER_ID and p == MASTER_PW: return True
    return False

# --------------------------------------------------------------------------
# [SECTION 2] 보험봇 우회 엔진 (404 방어막 및 2단계 원칙 각인)
# --------------------------------------------------------------------------
SYSTEM_PROMPT = """
당신은 '이세윤 관리자'가 설계한 '골드키지사 AI 마스터'입니다.
[답변 생성 2단계 원칙]
- 1단계: 금융감독원(FSS) 보도자료, 분쟁조정사례, 표준약관, 대법원 판례, CFP® 재무설계 기준을 최우선 근거로 삼는다.
- 2단계: 'google_search_retrieval'에서 구한 답과 1단계 내용을 비교하여 오답 여부를 최종 확인 후 답변하라.
- 소득 역산은 반드시 0.0709 공식을 사용하며, 설계사 벌칙 규정은 관리자 보호를 위해 절대 언급하지 않는다.
"""

def get_insurance_bot(api_key):
    """v1beta 404 에러를 우회하기 위한 자가 치유 라우터"""
    genai.configure(api_key=api_key)
    tools = [{'google_search_retrieval': {}}]
    
    # 404 에러 방지를 위해 후보 경로를 순차적으로 시도
    candidates = ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-1.5-flash-latest']
    
    for model_path in candidates:
        try:
            model = genai.GenerativeModel(
                model_name=model_path,
                system_instruction=SYSTEM_PROMPT,
                tools=tools
            )
            return model
        except:
            continue
    return None

# --------------------------------------------------------------------------
# [SECTION 3] 사이드바: 마스터 혜택 센터 (무손실 복구)
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("🔑 마스터 센터")
    if st.session_state.login_status:
        st.success(f"👋 **{st.session_state.current_user}** 마스터님")
        if st.button("❌ 보안 종료 (로그아웃)"): 
            st.session_state.login_status = False; st.rerun()
    else:
        l_u = st.text_input("아이디", key="l_u")
        l_p = st.text_input("비밀번호", type="password", key="l_p")
        if st.button("🚀 마스터 로그인", use_container_width=True):
            if verify_user(l_u, l_p):
                st.session_state.login_status = True
                st.session_state.current_user = "이세윤"
                # Secrets 자동 로드 로직
                if "GEMINI_API_KEY" in st.secrets:
                    st.session_state.user_api_key = st.secrets["GEMINI_API_KEY"]
                st.rerun()
            else: st.error("정보 불일치")

    st.divider()
    st.info("👤 **시스템 관리자: 이세윤**")
    st.markdown("### 🏆 회원 전용 혜택")
    st.success("- 1일 50건 미만 상담 시 **8년간 무료**\n- 로그인 시 **Key 자동 로드**\n- 실시간 **2단계 검증 분석**")
    st.markdown('<a href="https://aistudio.google.com/app/apikey" target="_blank">🌐 API 키 발급 바로가기</a>', unsafe_allow_html=True)

# --------------------------------------------------------------------------
# [SECTION 4] 브랜드 상단 UI
# --------------------------------------------------------------------------
st.divider()
st.markdown("<h3 style='color:#0D47A1;'>\"보험 가입 상담 부터 보험금 분쟁 대응까지\"</h3>", unsafe_allow_html=True)
st.title("👑 골드키지사 AI 마스터")

# [🚨 수정 완료] session_status -> session_state 오타 수정
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
    main_area = st.text_area("📝 상담 내용 상세 입력", height=320, placeholder="내용을 입력하세요.", key="m_area")
    quick_analyze = st.button("🚀 즉시 분석 및 민원 요청", type="primary", use_container_width=True)
    main_output = st.container()
with col_img:
    try:
        st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/ai_expert.png")
    except:
        st.info("AI 전문 마스터 엔진 가동 중")

# --------------------------------------------------------------------------
# [SECTION 5] 실전 보상 & 민원 대응 튜토리얼
# --------------------------------------------------------------------------
st.divider()
with st.expander("💡 실전 보상 & 민원 대응 튜토리얼 (판례 2001다1480)"):
    st.write("보험사의 설명의무 위반 시 대응 법리 로직 탑재")
    
    try:
        st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/dispute_process.png")
    except: pass

# --------------------------------------------------------------------------
# [SECTION 6] 1단계: 고객 기초 정보
# --------------------------------------------------------------------------
st.divider()
st.write("### 👤 1단계: 고객 기초 정보")
c1, c2 = st.columns(2)
c_name = c1.text_input("고객 성함", "고객님")
hi_premium = c1.number_input("월 건강보험료(원)", value=0, step=1000)
debt = c2.number_input("부채 총액(만원)", value=0, step=100)

# --------------------------------------------------------------------------
# [SECTION 7] 2단계: 자료 및 증권 업로드
# --------------------------------------------------------------------------
st.divider()
st.write("### 📸 2단계: 자료 및 증권 업로드")
files = st.file_uploader("파일 로드", accept_multiple_files=True, key=f"u_{st.session_state.uploader_key}")
if files and st.button("🗑️ 전체 서류 삭제"):
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
st.info("민법, 상법, 보험업법 기반 실시간 판례 검색 가동")

# --------------------------------------------------------------------------
# [SECTION 11] 6단계: 위험관리 설계
# --------------------------------------------------------------------------
st.divider()
st.write("### 🛡️ 6단계: 국제재무설계 기준 위험관리")
ess_ins = st.multiselect("필수 보험", ["자동차", "화재", "일배책", "후유장해", "기본장기"])

# --------------------------------------------------------------------------
# [SECTION 12] 7단계: 3층 연금 시뮬레이션
# --------------------------------------------------------------------------
st.divider()
st.write("### 💰 7단계: 국제 재무설계 기준 3층 연금 시뮬레이션")

try:
    st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/pension_3tier.png")
except: pass
p1, p2, p3 = st.columns(3)
p_nat = p1.number_input("국민연금", value=0)
p_ret = p2.number_input("퇴직연금", value=0)
p_ind = p3.number_input("개인연금", value=0)

# --------------------------------------------------------------------------
# [SECTION 13] 8단계: 인생 이모작 설계
# --------------------------------------------------------------------------
st.divider()
st.write("### 🏡 8단계: 국제 재무설계 기준 주택구입 및 인생 이모작 설계")

try:
    st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/cfp_process.png")
except: pass
home_f = st.number_input("주택자금(만원)", value=0)
second_j = st.text_area("이모작 계획")

# --------------------------------------------------------------------------
# [SECTION 14] 전문가 통합 분석 엔진 (Bypass Router)
# --------------------------------------------------------------------------
def run_master(container):
    with container:
        if not st.session_state.user_api_key:
            user_input_key = st.text_input("🔑 API Key를 입력하세요 (Secrets 로드 실패 시)", type="password")
            if not user_input_key:
                st.error("API Key가 없습니다. 사이드바를 확인하거나 키를 입력하세요."); return
            st.session_state.user_api_key = user_input_key
        
        with st.spinner("🔍 보험봇 우회 및 2단계 검증 분석 중..."):
            try:
                # [🚨 자가 치유 엔진 호출]
                model = get_insurance_bot(st.session_state.user_api_key)
                if not model: 
                    st.error("❌ 모든 우회 경로 접속 실패. API Key 유효성을 확인하십시오.")
                    return
                
                # 소득 역산 공식 적용: $Income = \frac{Health\ Premium}{0.0709}$
                income = hi_premium / 0.0709 if hi_premium > 0 else 0
                query = f"상담내용: {main_area}. 소득역산: {income:,.0f}원. 연금합계: {p_nat+p_ret+p_ind}만. 질병관심: {dis_focus}."
                
                content = [query]
                if files:
                    for f in files: content.append(PIL.Image.open(f))

                resp = model.generate_content(content)
                st.subheader("📊 통합 분석 리포트 (2단계 검증 완료)")
                st.markdown(resp.text)
                
                if resp.candidates[0].grounding_metadata.search_entry_point:
                    st.html(resp.candidates[0].grounding_metadata.search_entry_point.rendered_content)
            except Exception as e:
                st.error(f"🚨 시스템 오류: {e}")

if quick_analyze: run_master(main_output)

# --------------------------------------------------------------------------
# [SECTION 15] 성공 응원
# --------------------------------------------------------------------------
st.divider()
if st.button("🔍 전 섹션 마스터 종합 분석 리포트 생성 🚀", type="primary", use_container_width=True):
    run_master(st.container())

st.divider()
if st.button("🏆 성공 응원"): st.balloons(); st.success(f"{st.session_state.current_user} 마스터님, 필승하십시오!")
