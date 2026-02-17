# ==========================================================================
# 🚨 [삭제/수정 절대 금지] 골드키지사 AI 마스터 전체 통합 시스템
# 모델 호출 경로 문제를 해결한 최종 안정화 버전입니다.
# ==========================================================================

import streamlit as st
import pandas as pd
import time
import datetime
from datetime import datetime as dt
import google.generativeai as genai
import PIL.Image

# [1] 기본 페이지 설정
st.set_page_config(page_title="골드키지사 AI 마스터", page_icon="👑", layout="wide")

# [2] API 연결 및 에러 방지 설정
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception:
    st.error("🔑 API 키 설정을 확인해주세요 (Streamlit Secrets)")

# [3] 통합 페르소나 지침 (보험비서_최종 지침 반영)
SYSTEM_PROMPT = """
성명: 고객 보험 상담 전문 AI 비서 (이세윤 설계사 대행)
핵심 가치: 30년 경력의 이세윤 설계사가 가진 '현장 실무 지식' 계승.
전문성: 금융(CFP), 의학(질환 이해), 법률(손해사정) 통합 분석.
답변 원칙: 근거 법령 및 실시간 구글 검색(Grounding) 활용.
"""

# [4] 음성 재생 엔진
def speak(text):
    ts = int(time.time())
    html_code = f"""<div id="voicetarget_{ts}"></div><script>window.speechSynthesis.cancel(); var msg = new SpeechSynthesisUtterance("{text}"); msg.lang = 'ko-KR'; msg.rate = 1.0; msg.pitch = 0.95; window.speechSynthesis.speak(msg);</script>"""
    st.components.v1.html(html_code, height=0)

# ==========================================
# [SECTION 3] 사이드바 (사용자 센터 유지)
# ==========================================
with st.sidebar:
    st.header("🔑 사용자 센터")
    user_name = st.text_input("상담원 성함", "이세윤")
    st.divider()
    if st.button("📝 회원가입 및 혜택 안내"):
        msg = "2026년 9월부터 회원제가 시행되며, 1년간 무료 혜택을 드립니다."
        st.info(msg); speak(msg)
    if st.button("📖 튜토리얼 시작"):
        msg = "1단계 증권 분석 후 2단계 상세 질문을 이용하세요."
        st.success(msg); speak(msg)
    st.divider()
    st.info("💡 **골드키지사 AI 사용 정책**\n- 2026.09. 회원제 시행 예정")
    if st.button("❌ 데이터 자동 파기", use_container_width=True):
        st.cache_data.clear(); st.session_state.clear(); st.rerun()

st.title("👑 골드키지사 AI 마스터")

# ==========================================
# [SECTION 4] 1단계: 증권 이미지 정밀 분석 (유지)
# ==========================================
st.write("---")
st.write("### 📂 1단계: 증권 이미지 정밀 분석")
c1, c2, c3 = st.columns([1, 1, 1])
with c1: customer_name = st.text_input("고객명", "고객님")
with c2: hi_premium = st.number_input("월 보험료(원)", value=0)
with c3: debt = st.number_input("부채(만원)", value=0)

uploaded_files = st.file_uploader("증권 사진/PDF 업로드", accept_multiple_files=True)

if st.button("🔍 증권 통합 분석 시작 🚀", type="primary"):
    if uploaded_files:
        with st.spinner("분석 중..."):
            try:
                # 🔴 404 해결: 모델 리스트를 직접 확인하거나 표준 명칭 강제 사용
                model = genai.GenerativeModel('gemini-1.5-flash')
                content_parts = [SYSTEM_PROMPT, f"상담원:{user_name}, 고객:{customer_name}", "증권을 분석해줘."]
                for f in uploaded_files:
                    img_data = PIL.Image.open(f)
                    content_parts.append(img_data)
                response = model.generate_content(content_parts)
                st.session_state.analysis_answer = response.text
            except Exception as e:
                st.error(f"분석 오류: {e}")

if "analysis_answer" in st.session_state:
    st.markdown(st.session_state.analysis_answer)

# ==========================================
# [SECTION 7] 2단계: 질문창 (수정된 문구 및 에러 해결 로직)
# ==========================================
st.divider()
col_input_area, col_ai_img = st.columns([7, 3])

with col_input_area:
    st.markdown('<p style="font-size:22px; font-weight:bold; color:#1E88E5;">🏆 2단계: 전담 AI 마스터 상세 질문</p>', unsafe_allow_html=True)
    user_question = st.text_area("❓ 상세 내용을 적어주세요", height=330, placeholder="예: 자동차 사고 합의금 산출 방식은?")

    if st.button("🚀 전담 AI 마스터 답변 요청", use_container_width=True, type="primary"):
        if user_question:
            with st.spinner("분석 중..."):
                try:
                    # 🔴 404 에러를 우회하는 하이브리드 호출 방식
                    # tools(구글 서치)를 사용하되 모델 명칭에서 'models/'를 제거하여 시도
                    model = genai.GenerativeModel(
                        model_name='gemini-1.5-flash',
                        tools=[{"google_search_retrieval": {}}]
                    )
                    response = model.generate_content(f"{SYSTEM_PROMPT}\n\n질문: {user_question}")
                    st.session_state.chat_answer = response.text
                except Exception as e:
                    # 최종 비상 로직: 서치 기능 없이 가장 기초적인 모델로 응답
                    try:
                        model_basic = genai.GenerativeModel('gemini-1.5-flash')
                        response_basic = model_basic.generate_content(f"{SYSTEM_PROMPT}\n\n질문: {user_question}")
                        st.session_state.chat_answer = response_basic.text
                    except Exception as e2:
                        st.error(f"연결 실패: {e2}")
        else:
            st.warning("질문을 입력해 주세요.")

with col_ai_img:
    img_path = "https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/ai_expert.png"
    try: st.image(img_path, caption="골드키지사 전담 AI 마스터", use_container_width=True)
    except: st.info("💡 이미지 로딩 중...")

if "chat_answer" in st.session_state:
    st.markdown("---")
    st.info("📢 **전담 AI 마스터 답변 결과**")
    st.write(st.session_state.chat_answer)

st.divider()
st.error("**[법적 고지]** 본 분석 결과는 참고용이며 최종 결정은 전문가와 상의하십시오.")
