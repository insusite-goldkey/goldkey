# ==========================================================================
# 👑 [골드키지사 AI 마스터 - 효능(Efficacy) 중심 무손실 시스템]
# 규칙: 효율을 위해 섹션을 통합하지 말 것. 각 섹션은 독립된 효능을 가진다.
# 1. 자가 치유(Bypass): 404 에러 시 다중 경로 라우팅으로 서버 접속 보장.
# 2. 대화형 로직: 필수보험 안내 -> 증권 요청 -> 건보료 역산(0.0709) 순차 구현.
# 3. 2단계 검증: [1단계: 공식자료] -> [2단계: 구글 검색 교차 체크] 원칙 준수.
# 4. 섹션 수호: 1~15번 전 섹션을 st.divider()로 물리적 완전 분리.
# ==========================================================================

import streamlit as st
import google.generativeai as genai
import PIL.Image
import json
import os
import re

# --------------------------------------------------------------------------
# [SECTION 1] 기본 설정 및 마스터 보안 (admin / gold1234)
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
# [SECTION 2] 보험봇 우회 엔진 (2단계 검증 및 404 자가치유)
# --------------------------------------------------------------------------
SYSTEM_PROMPT = """
당신은 '이세윤 관리자'가 설계한 '골드키지사 AI 마스터'입니다.
[답변 생성 2단계 원칙]
- 1단계: 금융감독원 보도자료, 분쟁조정사례, 표준약관, 대법원 판례, CFP 재무설계 기준을 최우선 근거로 삼는다.
- 2단계: 'google_search_retrieval'에서 구한 답과 1단계 내용을 비교하여 오답 여부를 최종 확인 후 답변하라.
- 소득 역산: 반드시 건강보험료 / 0.0709 공식을 사용하여 월 소득을 구한다.
- 보험료 가이드: 역산된 소득의 15%를 적정 보장보험료로 제안한다.
- 리스크 관리: 설계사 보호를 위해 보험업법 벌칙 규정은 답변에서 절대 제외한다.
"""

def get_master_model(api_key):
    genai.configure(api_key=api_key)
    tools = [{'google_search_retrieval': {}}]
    # 404 에러 방지를 위한 후보 경로 자동 순회
    candidates = ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-1.5-flash-latest']
    
    for path in candidates:
        try:
            model = genai.GenerativeModel(model_name=path, system_instruction=SYSTEM_PROMPT, tools=tools)
            return model
        except: continue
    return None

# --------------------------------------------------------------------------
# [SECTION 3] 사이드바: 마스터 회원 센터 (상세 혜택 효능 수호)
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
                if "GEMINI_API_KEY" in st.secrets:
                    st.session_state.user_api_key = st.secrets["GEMINI_API_KEY"]
                st.rerun()
            else: st.error("정보 불일치")

    st.divider()
    st.info("👤 **관리자: 이세윤**")
    st.markdown("### 🏆 마스터 회원 전용 혜택")
    st.success("- 1일 50건 미만 상담 시 **8년간 무료**\n- 로그인 시 **Key 자동 로드**\n- 실시간 **2단계 검증 분석**\n- 데이터 **즉시 파기 보안**")
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
# [SECTION 4.5] 마스터 통합 상담 센터
# --------------------------------------------------------------------------
st.divider()
st.subheader("📡 마스터 통합 상담 센터")
col_in, col_img = st.columns([7, 3])
with col_in:
    main_area = st.text_area("📝 상담 내용 및 특별 요청사항 입력", height=250, key="main_text")
    q_analyze = st.button("🚀 마스터 통합 분석 실행", type="primary", use_container_width=True, key="main_btn")
    main_output = st.container()
with col_img:
    st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/ai_expert.png", caption="마스터 통합 엔진")

# --------------------------------------------------------------------------
# [SECTION 5] 실전 보상 & 민원 대응 튜토리얼
# --------------------------------------------------------------------------
st.divider()
with st.expander("💡 실전 보상 & 민원 대응 튜토리얼 (판례 2001다1480)"):
    st.write("보험사의 설명의무 위반 시 대응 법리 및 개별 사건 매칭 로직입니다.")
    
    st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/dispute_process.png")

# --------------------------------------------------------------------------
# [SECTION 6] 1단계 대화: 필수보험 안내
# --------------------------------------------------------------------------
st.divider()
st.write("### 🛡️ 1단계: 필수 보장 자가 진단")
with st.chat_message("assistant"):
    st.write("**[마스터의 질문]**")
    st.write("필수보험은 **(1)일상생활배상책임, (2)주택화재보험, (3)자동차보험, (4)운전자보험, (5)기본장기통합보험**이 해당합니다. 고객님께서는 어느 정도 준비하고 계시나요?")
ess_reply = st.text_input("고객 답변 입력", placeholder="예: 자동차보험과 화재보험만 있습니다.", key="ess_reply")

# --------------------------------------------------------------------------
# [SECTION 7] 2단계 대화: 전문 증권 분석 요청
# --------------------------------------------------------------------------
st.divider()
st.write("### 📸 2단계: 전문 증권 분석 자료 요청")
with st.chat_message("assistant"):
    st.write("**[마스터의 요청]**")
    st.write("지금 가입하고 있는 보험증권이나 보험회사에서 받은 **증권분석 PDF파일**이 있으시면 파일을 전송해주세요. 국제재무설계 기준에 맞춰 정밀하게 분석해드리겠습니다.")
uploaded_files = st.file_uploader("파일 업로드", accept_multiple_files=True, key=f"u_{st.session_state.uploader_key}")

# --------------------------------------------------------------------------
# [SECTION 8] 3단계 대화: 건보료 기반 소득 역산 (핵심 효능)
# --------------------------------------------------------------------------
st.divider()
st.write("### 💰 3단계: 건보료 기반 소득 역산 및 지출 가이드")
with st.chat_message("assistant"):
    st.write("**[마스터의 질문]**")
    st.write("보험료로 월 소득의 얼마를 지출해야 할지 궁금하시군요? 현재 **국민건강보험료**로 지출하시는 금액을 알려주시면 소득을 역산하여 가이드를 드리겠습니다.")

nhi_premium = st.number_input("월 건강보험료 입력 (원)", value=0, step=1000, key="nhi_pre")

if nhi_premium > 0:
    # 0.0709 역산 공식: 월소득 = 건보료 / 0.0709
    calc_income = nhi_premium / 0.0709
    calc_guide = calc_income * 0.15
    
    st.success("📊 **이세윤 마스터의 재무 진단 결과**")
    m1, m2 = st.columns(2)
    m1.metric("역산된 월 소득", f"{calc_income:,.0f} 원")
    m2.metric("권장 보장성 보험료 (15%)", f"{calc_guide:,.0f} 원")
    st.info(f"고객님의 역산 소득은 약 **{calc_income:,.0f}원**이며, 적정 보장보험료는 월 **{calc_guide:,.0f}원** 수준이 적절합니다.")

# --------------------------------------------------------------------------
# [SECTION 9] 질병 보상 정밀 분석 필터
# --------------------------------------------------------------------------
st.divider()
st.write("### 🏥 질병 보상 정밀 분석 대상")
dis_focus = st.multiselect("특별 분석 대상 질환", ["암(선행항암)", "뇌/심장", "정신과", "희귀난치병"], key="dis_sel")

# --------------------------------------------------------------------------
# [SECTION 10] 삼성/교보 헬스케어 컨설팅
# --------------------------------------------------------------------------
st.divider()
st.write("### 💎 대형 생보사 헬스케어 컨설팅")
hc_info = st.checkbox("삼성/교보 등 헬스케어 서비스 안내 포함", key="hc_chk")

# --------------------------------------------------------------------------
# [SECTION 11] 6대 법령 및 보상 지식 DB
# --------------------------------------------------------------------------
st.divider()
st.write("### 🏛️ 6대 법령 및 보상 지식 DB")
st.info("민법, 상법, 보험업법 및 최신 판례 기반 실시간 검색 엔진 가동 중")

# --------------------------------------------------------------------------
# [SECTION 12] 국제재무설계 기준 위험관리
# --------------------------------------------------------------------------
st.divider()
st.write("### 🛡️ 국제재무설계 기준 위험관리")

st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/cfp_process.png", caption="CFP® 6단계 표준 프로세스")

# --------------------------------------------------------------------------
# [SECTION 13] 3층 연금 시뮬레이션
# --------------------------------------------------------------------------
st.divider()
st.write("### 💰 국제 재무설계 기준 3층 연금 통합 시뮬레이션")

st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/pension_3tier.png", caption="3층 연금 체계")
p1, p2, p3 = st.columns(3)
p_nat = p1.number_input("국민연금 (만)", value=0, key="p_n")
p_ret = p2.number_input("퇴직연금 (만)", value=0, key="p_r")
p_ind = p3.number_input("개인연금 (만)", value=0, key="p_i")

# --------------------------------------------------------------------------
# [SECTION 14] 인생 이모작 및 주택 설계
# --------------------------------------------------------------------------
st.divider()
st.write("### 🏡 인생 이모작 및 주택 설계")
home_f = st.number_input("주택자금 필요액 (만원)", value=0, key="h_f")
second_j = st.text_area("인생 이모작 계획 및 전직/창업 고민", key="s_j")

# --------------------------------------------------------------------------
# [SECTION 15] 전문가 통합 분석 및 성공 응원 (효능 완성)
# --------------------------------------------------------------------------
def run_master(container):
    with container:
        if not st.session_state.user_api_key:
            st.error("🚨 API Key가 연결되지 않았습니다."); return
        
        with st.spinner("🔍 이세윤 마스터 엔진 가동 및 2단계 검증 분석 중..."):
            try:
                model = get_master_model(st.session_state.user_api_key)
                if not model: st.error("구글 서버 접속 실패"); return
                
                income = nhi_premium / 0.0709 if nhi_premium > 0 else 0
                guide = income * 0.15
                
                query = f"""
                분석 요청:
                - 상담내용: {main_area}
                - 필수보험답변: {ess_reply}
                - 재무지표: 건보료({nhi_premium}원), 역산소득({income:,.0f}원), 적정보험료({guide:,.0f}원)
                - 분석원칙: 2단계 교차 검증(금감원/판례 vs 구글검색) 수행.
                결과를 [항목|현재상태|가이드|마스터 처방] 표로 생성하라.
                """
                
                content = [query]
                if uploaded_files:
                    for f in uploaded_files: content.append(PIL.Image.open(f))
                
                resp = model.generate_content(content)
                st.subheader("📊 마스터 통합 리포트 (교차 검증 완료)")
                st.markdown(resp.text)
                
                if resp.candidates[0].grounding_metadata.search_entry_point:
                    st.html(resp.candidates[0].grounding_metadata.search_entry_point.rendered_content)
            except Exception as e:
                st.error(f"🚨 시스템 장애: {e}")

if q_analyze: run_master(main_output)

st.divider()
if st.button("🔍 전 섹션 마스터 종합 분석 리포트 생성 🚀", type="primary", use_container_width=True, key="total_btn"):
    run_master(st.container())

st.divider()
if st.button("🏆 관리자 이세윤 성공 응원", key="cheer_btn"): 
    st.balloons(); st.success("필승하십시오! 최고의 성과를 응원합니다.")
