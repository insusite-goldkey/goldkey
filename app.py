# ==========================================================================
# 🚨 [삭제 금지] 모델 고정 및 404 에러 원천 차단 로직
# ==========================================================================

import streamlit as st
import pandas as pd
import time
import datetime
from datetime import datetime as dt
import google.generativeai as genai
import PIL.Image

# [기본 설정]
st.set_page_config(page_title="골드키지사 AI 마스터", page_icon="👑", layout="wide")

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error(f"API 키 설정 오류: {e}")

# [이세윤 설계사 대행 페르소나]
SYSTEM_PROMPT = """
성명: 고객 보험 상담 전문 AI 비서 (이세윤 설계사 대행)
핵심 가치: 30년 경력의 이세윤 설계사가 가진 '현장 실무 지식' 계승.
전문성: 금융(CFP), 의학(질환 이해), 법률(손해사정 법리) 통합 분석.
"""

# ==========================================
# [SECTION 2] 음성 재생 엔진
# ==========================================
def speak(text):
    ts = int(time.time())
    html_code = f"""<div id="voicetarget_{ts}"></div><script>window.speechSynthesis.cancel(); var msg = new SpeechSynthesisUtterance("{text}"); msg.lang = 'ko-KR'; msg.rate = 1.0; msg.pitch = 0.95; window.speechSynthesis.speak(msg);</script>"""
    return st.components.v1.html(html_code, height=0)

# ==========================================
# [SECTION 3] 사이드바 (튜토리얼 유지)
# ==========================================
with st.sidebar:
    st.header("🔑 사용자 센터")
    user_name = st.text_input("상담원 성함", "")
    st.divider()
    if st.button("📖 튜토리얼 시작"):
        msg = "첫번째 증권 분석. 두번째 질문하기."
        st.success(msg); speak(msg)
    st.info("💡 **2026.09. 회원제 시행 예정**\n무료 회원가입 시 1년간 무료")

st.title("👑 골드키지사 AI 마스터")

# ==========================================
# [SECTION 7] 2단계: 질문창 (자동 모델 복구 로직)
# ==========================================
st.divider()
col_input_area, col_ai_img = st.columns([7, 3])

with col_input_area:
    st.markdown('<p style="font-size:22px; font-weight:bold; color:#1E88E5;">🏆 2단계: 전담 AI 마스터 상세 질문</p>', unsafe_allow_html=True)
    user_question = st.text_area("❓ 전문가에게 물어볼 내용을 상세히 적어주세요", height=330, placeholder="예: 자동차 사고 입원 시 합의금 산출 방식은?")

    if st.button("🚀 전담 AI 마스터 답변 요청", use_container_width=True, type="primary"):
        if user_question:
            with st.spinner("마스터가 답변을 생성 중입니다..."):
                # 🔴 [테스트 결과 반영] 404 에러를 피하기 위한 순차적 시도 리스트
                # 최신 버전에서는 'models/'를 생략한 이름이 가장 잘 작동합니다.
                model_names = ['gemini-1.5-flash', 'gemini-1.5-pro', 'models/gemini-1.5-flash']
                final_response = None
                
                for m_name in model_names:
                    try:
                        # 구글 검색(Grounding) 기능을 포함한 모델 설정
                        model = genai.GenerativeModel(
                            model_name=m_name,
                            system_instruction=SYSTEM_PROMPT,
                            tools=[{"google_search_retrieval": {}}]
                        )
                        final_response = model.generate_content(user_question)
                        if final_response:
                            st.session_state.chat_answer = final_response.text
                            break # 성공 시 루프 탈출
                    except Exception as inner_error:
                        # 실패 시 다음 모델명으로 시도
                        continue
                
                if final_response is None:
                    st.error("구글 API 서비스 점검 중이거나 모델 연결에 실패했습니다. API 키 권한을 다시 확인해 주세요.")
        else:
            st.warning("질문을 먼저 입력해 주세요.")

with col_ai_img:
    st.write("") 
    if st.button("👤 AI 전문가 인사 듣기", use_container_width=True):
        speak("안녕하세요. 이세윤 설계사 대행 AI 마스터입니다.")
    
    img_path = "https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/ai_expert.png"
    try: st.image(img_path, caption="골드키지사 전담 AI 마스터", use_container_width=True)
    except: st.info("💡 이미지 파일을 확인 중입니다.")

# ==========================================
# [SECTION 8-10] 결과 및 마무리
# ==========================================
if "chat_answer" in st.session_state:
    st.markdown("---")
    st.info("📢 **전담 AI 마스터 분석 결과**")
    st.write(st.session_state.chat_answer)

st.divider()
if st.button("🚀 응원 메시지 듣기", use_container_width=True):
    st.balloons(); speak("FC님, AI와 함께 첨단 보험상담의 주역이 되세요.")

st.error("**[법적 고지]** 본 리포트의 법률적 책임은 사용자에게 귀속되며 AI 분석 결과는 상담 참고용 자료입니다.")
