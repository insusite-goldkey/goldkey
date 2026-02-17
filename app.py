import streamlit as st
import pandas as pd
import time
import datetime
from datetime import datetime as dt
import google.generativeai as genai
import PIL.Image

# ==========================================
# [SECTION 1] AI Studio '보험비서_최종' 페르소나 주입
# ==========================================
st.set_page_config(page_title="골드키지사 AI 마스터", page_icon="👑", layout="wide")

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception:
    st.error("시스템 설정 확인이 필요합니다.")

# 🔴 AI Studio에서 설계사님이 작성하신 페르소나 내용을 그대로 이식했습니다.
SYSTEM_PROMPT = """
### 1. 페르소나 정의 (Identity)
성명: 고객 보험 상담 전문 AI 비서 (이세윤 설계사 대행)
핵심 가치: 30년 경력의 이세윤 설계사가 가진 '현장 실무 지식'과 '고객 중심의 보상 철학' 계승.

### 2. 전문성 범위
- 금융: CFP(국제공인재무설계사) 수준의 자산 관리 및 판매 전문성 보유.
- 의학: 암(혈액/간담췌 등), 뇌·심혈관, 치매·신경과, 항암 의약품 등 전문의 수준의 질환 이해도 확보.
- 법률: 손해배상 전문 변호사 및 손해사정사의 법리 해석 능력 보유.

### 3. 답변 원칙
- 모든 답변은 근거 법령, 최신 손해사정 사례, 의학적 근거를 바탕으로 합니다.
- 단순 정보 전달을 넘어 '이세윤 설계사' 특유의 고객 중심 해결책을 제시합니다.
"""

# ==========================================
# [SECTION 2] 음성 재생 엔진
# ==========================================
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
    return st.components.v1.html(html_code, height=0)

# ==========================================
# [SECTION 3] 사이드바 및 정책
# ==========================================
with st.sidebar:
    st.header("🔑 사용자 센터")
    user_name = st.text_input("상담원 성함", "")
    st.divider()
    if st.button("📖 튜토리얼 시작"):
        msg = "첫번째 증권 분석. 증권을 사진이나 PDF파일로 업로드하세요. 두번째 질문하기. 궁금하신 내용을 말로 하거나, 내용을 입력하세요."
        st.success(msg); speak(msg)
    
    st.info("""
    💡 **골드키지사 AI 사용 정책**
    - 2026.09.부터 회원제 시행
    - 무료 회원가입 시 1년간 무료 사용 (2027.03. 정책변경)
    """)

# ==========================================
# [SECTION 7] 2단계: 질문창 (구글 서치 그라운딩 연동)
# ==========================================
st.divider()
col_input_area, col_ai_img = st.columns([7, 3])

with col_input_area:
    st.markdown('<p style="font-size:22px; font-weight:bold; color:#1E88E5;">🏆 2단계: 전담 AI 마스터 상세 질문</p>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:14px; color:#4CAF50;"><b>🌐 실시간 구글 검색(Grounding) 기능이 활성화되어 최신 정보를 분석합니다.</b></p>', unsafe_allow_html=True)
            
    user_question = st.text_area("❓ 전문가에게 물어볼 내용을 상세히 적어주세요", height=330, placeholder="예: 화재보험 구상권 청구 시 실화법 적용 사례는?")

    if st.button("🚀 전담 AI 마스터 답변 요청", use_container_width=True, type="primary"):
        if user_question:
            with st.spinner("마스터가 실시간 검색과 지식 베이스를 통합 분석 중입니다..."):
                try:
                    # 🔴 1.5 플래시 모델 설정 (구글 검색 도구 추가)
                    model = genai.GenerativeModel(
                        model_name='gemini-1.5-flash',
                        system_instruction=SYSTEM_PROMPT,
                        tools=[{"google_search_retrieval": {}}] # 🔴 실시간 구글 검색 그라운딩 활성화
                    )
                    
                    response = model.generate_content(user_question)
                    st.session_state.chat_answer = response.text
                except Exception as e:
                    st.error(f"답변 생성 오류: {e}")
        else:
            st.warning("질문을 먼저 입력해 주세요.")

with col_ai_img:
    st.write("") 
    if st.button("👤 AI 전문가 인사 듣기", use_container_width=True):
        speak("안녕하세요. 30년 경력의 이세윤 설계사 대행 AI 비서입니다. 최신 법률과 의학 정보를 바탕으로 정밀한 상담을 도와드리겠습니다.")
    
    img_path = "https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/ai_expert.png"
    try: st.image(img_path, caption="골드키지사 전담 AI 마스터", use_container_width=True)
    except: st.info("💡 이미지 파일을 확인 중입니다.")

# ==========================================
# [SECTION 8-10] 결과 출력
# ==========================================
if "chat_answer" in st.session_state:
    st.markdown("---")
    st.info("📢 **전담 AI 마스터 분석 리포트**")
    st.write(st.session_state.chat_answer)

st.divider()
success_msg = "FC님, AI와 함께 첨단 보험상담의 주역이 되세요."
if st.button("🚀 응원 메시지 듣기", use_container_width=True):
    st.balloons(); speak(success_msg)

st.error("**[법적 고지]** 본 리포트의 법률적 책임은 사용자에게 귀속되며 AI 분석 결과는 상담 참고용 자료입니다.")
