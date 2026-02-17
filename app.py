# ==========================================================================
# 🚨 [삭제/수정 금지] 골드키지사 AI 마스터 전체 통합 시스템
# 사이드바, 1단계 증권분석, 2단계 마스터 답변 기능이 모두 포함된 코드입니다.
# ==========================================================================

import streamlit as st
import pandas as pd
import time
import datetime
from datetime import datetime as dt
import google.generativeai as genai
import PIL.Image

# [1] 기본 페이지 설정 및 스타일
st.set_page_config(page_title="골드키지사 AI 마스터", page_icon="👑", layout="wide")

# [2] API 연결 및 모델 설정 (설계사님의 API 권한 설정 반영)
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception:
    st.error("🔑 API 키 설정을 확인해주세요 (Streamlit Secrets)")

# [3] 통합 페르소나 지침 (보험비서_최종 & 보험상담 봇)
SYSTEM_PROMPT = """
성명: 고객 보험 상담 전문 AI 비서 (이세윤 설계사 대행)
핵심 가치: 30년 경력의 이세윤 설계사가 가진 '현장 실무 지식'과 '고객 중심의 보상 철학' 계승.
전문성: 금융(CFP), 의학(전문의 수준 질환 이해), 법률(손해사정 법리) 통합 분석.
답변 원칙: 모든 답변은 근거 법령 및 실시간 구글 검색(Grounding)을 바탕으로 함.
"""

# [4] 음성 재생 엔진 함수
def speak(text):
    ts = int(time.time())
    html_code = f"""
    <div id="voicetarget_{ts}"></div>
    <script>
        window.speechSynthesis.cancel(); 
        var msg = new SpeechSynthesisUtterance("{text}");
        msg.lang = 'ko-KR'; 
        msg.rate = 1.0; 
        msg.pitch = 0.95; 
        window.speechSynthesis.speak(msg);
    </script>
    """
    st.components.v1.html(html_code, height=0)

# ==========================================
# [SECTION 3] 사이드바 (사용자 센터 전체 복구)
# ==========================================
with st.sidebar:
    st.header("🔑 사용자 센터")
    user_name = st.text_input("상담원 성함", "이세윤")
    st.divider()
    if st.button("📝 회원가입 및 혜택 안내"):
        msg = "2026년 9월부터 회원제가 시행되며, 무료 회원가입 시 1년간 무료 혜택을 드립니다."
        st.info(msg); speak(msg)
    if st.button("🛠️ API 키 발급 가이드"):
        st.warning("개인용 API 키 등록 시 더 안정적인 사용이 가능합니다.")
        st.markdown('[구글 API 키 발급](https://aistudio.google.com/app/apikey)')
    if st.button("📖 튜토리얼 시작"):
        msg = "1단계에서 증권을 분석하고, 2단계에서 마스터에게 상세 질문을 하세요."
        st.success(msg); speak(msg)
    st.divider()
    st.info("💡 **골드키지사 AI 사용 정책**\n- 4월 30일까지 고도화 이벤트\n- 2026.09. 회원제 시행 예정")
    if st.button("❌ 데이터 자동 파기", use_container_width=True):
        st.cache_data.clear(); st.session_state.clear(); st.rerun()

st.title("👑 골드키지사 AI 마스터")
if user_name:
    st.success(f"🌟 {user_name} 상담원님, 환영합니다!")

# ==========================================
# [SECTION 4] 1단계: 증권 이미지 정밀 분석
# ==========================================
st.write("---")
st.write("### 📂 1단계: 증권 이미지 정밀 분석")
c1, c2, c3 = st.columns([1, 1, 1])
with c1: customer_name = st.text_input("고객명", "고객님")
with c2: hi_premium = st.number_input("월 보험료(원)", value=0)
with c3: debt = st.number_input("부채(만원)", value=0)

col_upload, col_action = st.columns([2, 1])
with col_upload:
    uploaded_files = st.file_uploader("증권 사진/PDF 업로드", accept_multiple_files=True)
with col_action:
    st.write(" ")
    st.write(" ")
    if st.button("🔍 증권 통합 분석 시작 🚀", use_container_width=True, type="primary"):
        if uploaded_files:
            with st.spinner("전문가 그룹이 분석 중입니다..."):
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)
                    content_parts = [f"상담원:{user_name}, 고객:{customer_name}, 보험료:{hi_premium}, 부채:{debt}"]
                    for f in uploaded_files:
                        img_data = PIL.Image.open(f)
                        content_parts.append(img_data)
                    response = model.generate_content(content_parts)
                    st.session_state.analysis_answer = response.text
                except Exception as e:
                    st.error(f"분석 오류: {e}")
        else:
            st.warning("분석할 파일을 업로드해주세요.")

if "analysis_answer" in st.session_state:
    st.markdown(st.session_state.analysis_answer)

# ==========================================
# [SECTION 7] 2단계: 질문창 (마스터 답변 요청)
# ==========================================
st.divider()
col_input_area, col_ai_img = st.columns([7, 3])

with col_input_area:
    st.markdown('<p style="font-size:22px; font-weight:bold; color:#1E88E5;">🏆 2단계: 전담 AI 마스터 상세 질문</p>', unsafe_allow_html=True)
    user_question = st.text_area("❓ 전문가에게 물어볼 내용을 상세히 적어주세요", height=330, placeholder="예: 자동차 사고 입원 시 합의금 산출 방식은?")

    # 🔴 수정된 문구 적용
    if st.button("🚀 전담 AI 마스터 답변 요청", use_container_width=True, type="primary"):
        if user_question:
            with st.spinner("마스터가 실시간 정보를 분석 중입니다..."):
                try:
                    # Grounding 기능을 포함한 최신 모델 호출 방식 적용
                    model = genai.GenerativeModel(
                        model_name='gemini-1.5-flash',
                        system_instruction=SYSTEM_PROMPT,
                        tools=[{"google_search_retrieval": {}}]
                    )
                    response = model.generate_content(user_question)
                    st.session_state.chat_answer = response.text
                except Exception as e:
                    # 비상 복구 로직
                    try:
                        model_basic = genai.GenerativeModel('gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)
                        response_basic = model_basic.generate_content(user_question)
                        st.session_state.chat_answer = response_basic.text
                    except Exception as e2:
                        st.error(f"연결 오류: {e2}")
        else:
            st.warning("질문을 입력해 주세요.")

with col_ai_img:
    if st.button("👤 AI 전문가 인사 듣기", use_container_width=True):
        speak(f"안녕하세요 {user_name} 상담원님, 30년 경력 설계사 대행 AI 마스터입니다.")
    img_path = "https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/ai_expert.png"
    try: st.image(img_path, caption="골드키지사 전담 AI 마스터", use_container_width=True)
    except: st.info("💡 이미지 파일을 불러오는 중...")

if "chat_answer" in st.session_state:
    st.markdown("---")
    st.info("📢 **전담 AI 마스터 답변 결과**")
    st.write(st.session_state.chat_answer)

# ==========================================
# [SECTION 10] 마무리 및 고지
# ==========================================
st.divider()
if st.button("🚀 응원 메시지 듣기", use_container_width=True):
    st.balloons(); speak(f"{user_name} FC님, AI와 함께 첨단 보험상담의 주역이 되세요.")

st.error("**[법적 고지]** 본 분석 결과는 참고용이며 최종 결정은 법률 및 보험 전문가와 상의하십시오.")
st.sidebar.caption(f"최종 업데이트: {dt.now().strftime('%Y-%m-%d %H:%M')}")
