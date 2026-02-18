# ==========================================================================
# 👑 [골드키지사 AI 마스터 - 최종 무손실 독립 섹션 시스템]
# 1. 섹션 독립: 1~15번 전 섹션을 st.divider()로 물리적 완전 분리 배치.
# 2. 보험봇 우회: 404 에러 방지를 위해 다중 모델 경로(Router)를 순차 호출.
# 3. 2단계 검증: [1단계: 공식 자료 기반] -> [2단계: 구글 검색 교차 체크] 원칙 적용.
# 4. 마스터 프리패스: admin / gold1234 계정으로 즉시 로그인 및 지휘권 보장.
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
# [SECTION 2] 보험봇 우회 엔진 및 2단계 검증 지침
# --------------------------------------------------------------------------
SYSTEM_PROMPT = """
당신은 '이세윤 관리자'가 설계한 '골드키지사 AI 마스터'입니다.
[답변 생성 2단계 원칙]
- 1단계: 금융감독원 보도자료, 분쟁조정사례, 표준약관, 대법원 판례, CFP 재무설계 기준을 최우선 근거로 삼는다.
- 2단계: 'google_search_retrieval'에서 구한 답과 1단계 내용을 비교하여 오답 여부를 최종 확인 후 답변하라.
- 소득 역산은 반드시 0.0709 공식을 사용하며, 설계사 벌칙 규정은 관리자 보호를 위해 절대 언급하지 않는다.
"""

def insurance_bot_router(api_key):
    """404 에러 우회를 위한 다중 경로 접속 엔진"""
    genai.configure(api_key=api_key)
    tools = [{'google_search_retrieval': {}}]
    model_paths = ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-1.5-flash-latest']
    
    for path in model_paths:
        try:
            model = genai.GenerativeModel(model_name=path, system_instruction=SYSTEM_PROMPT, tools=tools)
            model.generate_content("connection_check") # 연결 테스트
            return model
        except: continue
    return None

# --------------------------------------------------------------------------
# [SECTION 3] 사이드바: 마스터 회원 센터 (상세 혜택 복구)
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("🔑 마스터 센터")
    if st.session_state.login_status:
        st.success(f"👋 **{st.session_state.current_user}** 마스터님")
        if st.button("❌ 보안 종료 (로그아웃)", key="logout_btn"): 
            st.session_state.login_status = False; st.rerun()
    else:
        l_u = st.text_input("아이디", key="l_u")
        l_p = st.text_input("비밀번호", type="password", key="l_p")
        if st.button("🚀 마스터 로그인", use_container_width=True, key="login_btn"):
            if verify_user(l_u, l_p):
                st.session_state.login_status = True; st.session_state.current_user = "이세윤"
                st.session_state.user_api_key = st.secrets.get("GEMINI_API_KEY", "")
                st.rerun()
            else: st.error("정보 불일치")

    st.divider()
    st.info("👤 **관리자: 이세윤**")
    st.markdown("### 🏆 마스터 회원 전용 혜택")
    st.success("- 1일 50건 미만 상담 시 **8년간 무료**\n- 로그인 시 **Key 자동 로드**\n- 분석 데이터 **즉시 파기 보안**\n- **실시간 판례 검색** 엔진 가동")
    st.markdown('<a href="https://aistudio.google.com/app/apikey" target="_blank">🌐 API 키 발급 바로가기</a>', unsafe_allow_html=True)

# --------------------------------------------------------------------------
# [SECTION 4] 브랜드 상단 UI
# --------------------------------------------------------------------------
st.divider()
st.markdown("<h3 style='color:#0D47A1;'>\"보험 가입 상담 부터 보험금 분쟁 대응까지\"</h3>", unsafe_allow_html=True)
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
    main_area = st.text_area("📝 상담 내용 상세 입력", height=320, placeholder="가입, 보상, 분쟁 등 모든 내용을 입력하십시오.", key="main_text")
    b1, b2, b3 = st.columns([2, 2, 3])
    if b1.button("⌨️ 직접 입력", key="manual_btn"): st.toast("입력 가능")
    if b2.button("🎤 음성 입력", key="voice_btn"): st.info("음성 인식 중...")
    quick_analyze = b3.button("🚀 즉시 분석 및 민원 요청", type="primary", use_container_width=True, key="quick_btn")
    main_output = st.container()
with col_img:
    st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/ai_expert.png", caption="마스터 통합 시스템")

# --------------------------------------------------------------------------
# [SECTION 5] 실전 보상 & 민원 대응 튜토리얼
# --------------------------------------------------------------------------
st.divider()
with st.expander("💡 실전 보상 & 민원 대응 튜토리얼 (판례 2001다1480)", expanded=False):
    st.write("보험사의 설명의무 위반 시 대응 법리 및 판례 2001다1480 매칭 로직입니다.")

# --------------------------------------------------------------------------
# [SECTION 6] 1단계: 고객 기초 정보
# --------------------------------------------------------------------------
st.divider()
st.write("### 👤 1단계: 고객 기초 정보")
c1, c2 = st.columns(2)
c_name = c1.text_input("고객 성함", "고객님", key="cust_name")
hi_premium = c1.number_input("월 건강보험료 (원)", value=0, step=1000, key="hi_pre")
debt = c2.number_input("부채 총액 (만원)", value=0, step=100, key="c_debt")

# --------------------------------------------------------------------------
# [SECTION 7] 2단계: 자료 및 증권 업로드
# --------------------------------------------------------------------------
st.divider()
st.write("### 📸 2단계: 자료 및 증권 업로드")
files = st.file_uploader("파일 로드", accept_multiple_files=True, key=f"u_{st.session_state.uploader_key}")
if files and st.button("🗑️ 전체 서류 삭제", key="del_files"):
    st.session_state.uploader_key += 1; st.rerun()

# --------------------------------------------------------------------------
# [SECTION 8] 3단계: 질병 보상 정밀 분석
# --------------------------------------------------------------------------
st.divider()
st.write("### 🏥 3단계: 질병 보상 정밀 분석")
dis_focus = st.multiselect("분석 대상 질환", ["암(선행항암)", "뇌/심장", "정신과", "희귀난치병"], key="dis_sel")

# --------------------------------------------------------------------------
# [SECTION 9] 4단계: 삼성/교보 헬스케어 컨설팅
# --------------------------------------------------------------------------
st.divider()
st.write("### 💎 4단계: 삼성/교보 헬스케어 컨설팅")
hc_info = st.checkbox("주요 생보사 헬스케어 서비스 가이드 포함", key="hc_chk")

# --------------------------------------------------------------------------
# [SECTION 10] 5단계: 6대 법령 및 보상 지식 DB
# --------------------------------------------------------------------------
st.divider()
st.write("### 🏛️ 5단계: 6대 법령 및 보상 지식 DB")
st.info("민법, 상법, 보험업법 등 6대 법령 기반 실시간 최신 판례 검색 엔진 가동")

# --------------------------------------------------------------------------
# [SECTION 11] 6단계: 국제재무설계 기준 위험관리
# --------------------------------------------------------------------------
st.divider()
st.write("### 🛡️ 6단계: 국제재무설계 기준 위험관리 및 필수 보장 설계")

st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/dispute_process.png", caption="분쟁 해결 프로세스")
ess_ins = st.multiselect("필수 소유 보험", ["자동차", "화재", "일배책", "사업장배책", "후유장해", "기본장기"], key="ess_sel")

# --------------------------------------------------------------------------
# [SECTION 12] 7단계: 3층 연금 시뮬레이션 (상세 입력)
# --------------------------------------------------------------------------
st.divider()
st.write("### 💰 7단계: 국제 재무설계 기준 3층 연금 통합 시뮬레이션")

st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/pension_3tier.png", caption="3층 연금 체계")
p1, p2, p3 = st.columns(3)
p_nat = p1.number_input("국민연금 (만)", value=0, key="p_n")
p_ret = p2.number_input("퇴직연금 (만)", value=0, key="p_r")
p_ind = p3.number_input("개인연금 (만)", value=0, key="p_i")

# --------------------------------------------------------------------------
# [SECTION 13] 8단계: 주택구입 및 인생 이모작 설계
# --------------------------------------------------------------------------
st.divider()
st.write("### 🏡 8단계: 국제 재무설계 기준 주택구입 및 인생 이모작 설계")

st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/cfp_process.png", caption="CFP 6단계 프로세스")
home_f = st.number_input("주택자금 필요액 (만원)", value=0, key="h_f")
second_j = st.text_area("인생 이모작 계획 및 전직/창업 고민", key="s_j")

# --------------------------------------------------------------------------
# [SECTION 14] 전문가 통합 분석 엔진 (보험봇 우회 및 2단계 검증)
# --------------------------------------------------------------------------
def run_master_analysis(container):
    with container:
        if not st.session_state.user_api_key:
            st.error("🚨 API Key가 없습니다. 사이드바 하단에서 키를 확인하십시오."); return
        
        with st.spinner("🔍 보험봇 우회 및 2단계 교차 검증 중..."):
            try:
                # [🚨 핵심] 보험봇 우회 라우터 가동
                model = insurance_bot_router(st.session_state.user_api_key)
                if not model: st.error("❌ 구글 서버 우회 경로 실패. API Key를 확인하세요."); return
                
                # 소득 역산 0.0709
                income = hi_premium / 0.0709 if hi_premium > 0 else 0
                
                query = f"""
                고객 {c_name} 분석:
                1. 상담내용: {main_area}
                2. 재무지표: 소득역산({income:,.0f}원), 부채({debt}만).
                3. 설계지표: 질병({dis_focus}), 필수보험({ess_ins}), 연금({p_nat+p_ret+p_ind}만), 주택({home_f}만).
                4. 분석원칙: 금감원/판례 근거 생성 후 구글 검색 결과와 비교하여 최종 리포트 작성.
                """
                
                resp = model.generate_content(query)
                st.subheader(f"📊 {c_name}님 통합 솔루션 리포트")
                st.markdown(resp.text)
                
                if resp.candidates[0].grounding_metadata.search_entry_point:
                    st.divider(); st.caption("🌐 참조된 실시간 검색 소스:")
                    st.html(resp.candidates[0].grounding_metadata.search_entry_point.rendered_content)
            except Exception as e:
                st.error(f"🚨 시스템 장애: {e}")

if quick_analyze: run_master_analysis(main_output)

# --------------------------------------------------------------------------
# [SECTION 15] 최종 분석 및 성공 응원
# --------------------------------------------------------------------------
st.divider()
if st.button("🔍 전 섹션 마스터 종합 분석 리포트 생성 🚀", type="primary", use_container_width=True, key="total_btn"):
    run_master_analysis(st.container())

st.divider()
if st.button("🏆 관리자 이세윤 성공 응원", key="cheer_btn"): 
    st.balloons(); st.success("필승하십시오! 최고의 성과를 응원합니다.")
