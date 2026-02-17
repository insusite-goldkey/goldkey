import streamlit as st
import pandas as pd
import time
import datetime
from datetime import datetime as dt
import google.generativeai as genai
import PIL.Image

# ==========================================
# [SECTION 1] 기본 설정 및 시스템 프롬프트
# ==========================================
st.set_page_config(page_title="골드키지사 AI 마스터", page_icon="👑", layout="wide")

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception:
    st.error("시스템 설정 확인이 필요합니다.")

TOKEN_POLICY = """
💡 **골드키지사 AI 사용 정책**
- **4월 30일까지 사용 제한 없음** (고도화 이벤트)
- **2026.09.부터 회원제 시행**
- **무료 회원가입 시 1년간 무료 사용 혜택 제공** (2027.03. 정책변경)
- **약 8년 무료사용 가능 토큰 구글 제공**
"""

SYSTEM_PROMPT = """당신은 30년 현장 지식과 보험 전문성을 갖춘 손해사정 전문 AI입니다. 
모든 답변은 화재보험법, 실화책임법 등 관련 법령과 표준 약관을 근거로 하십시오."""

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
# [SECTION 3-6] 사이드바 및 1단계 분석 (동일 유지)
# ==========================================
with st.sidebar:
    st.header("🔑 사용자 센터")
    user_name = st.text_input("상담원 성함", "")
    st.divider()
    if st.button("📝 회원가입 및 혜택 안내"):
        msg = "2026년 9월부터 회원제가 시행되며, 무료 회원가입 시 1년간 무료 사용 혜택을 드립니다."
        st.info(msg); speak(msg)
    if st.button("🛠️ API 키 발급 가이드"):
        msg = "개인용 API 키를 등록하시면 본인의 토큰을 사용하여 안정적인 분석이 가능합니다."
        st.warning(msg); speak(msg)
        st.markdown('<a href="https://aistudio.google.com/app/apikey" target="_blank" style="text-decoration: none;"><button style="width: 100%; padding: 10px; background-color: #1E88E5; color: white; border: none; border-radius: 5px; cursor: pointer;">🌐 구글 API 키 발급 (새 창)</button></a>', unsafe_allow_html=True)
    if st.button("📖 튜토리얼 시작"):
        msg = "첫번째 증권 분석. 증권을 사진이나 PDF파일로 업로드하세요. 두번째 질문하기. 궁금하신 내용을 말로 하거나, 내용을 입력하세요."
        st.success(msg); speak(msg)
    st.divider()
    st.markdown(TOKEN_POLICY)

st.title("👑 골드키지사 AI 마스터")

# ==========================================
# [SECTION 7] 2단계: 질문창 및 모델 호출 최적화
# ==========================================
st.divider()
st.markdown("""
<style>
    .big-font { font-size:22px !important; font-weight: bold; color: #1E88E5; }
    .small-warn { font-size:13px !important; color: #FF5252; font-weight: normal; margin-left: 10px; }
    .browser-info { font-size:14px !important; color: #4CAF50; font-weight: bold; margin-left: 10px; }
</style>
""", unsafe_allow_html=True)

col_input_area, col_ai_img = st.columns([7, 3])

with col_input_area:
    st.markdown(f'''
        <p class="big-font">🏆 2단계: AI 전문가에게 상세 질문하기 
        <span class="small-warn">⚠️ 주변 소음 시 오타 주의</span>
        <span class="browser-info">🌐 구글 크롬 브라우저 권장</span>
        </p>
    ''', unsafe_allow_html=True)
    
    col_mic, col_btn_desc = st.columns([1, 10])
    with col_mic: st.markdown("## 🎤")
    with col_btn_desc:
        if st.button("🎤 음성 인식 질문 가이드", use_container_width=True):
            guide_msg = "궁금하신 점을 입력하고 답변 요청 버튼을 눌러주세요. 크롬 브라우저를 권장합니다."
            st.toast(guide_msg); speak(guide_msg)
            
    user_question = st.text_area("❓ 전문가에게 물어볼 내용을 상세히 적어주세요", height=330, placeholder="예: 옆집 화재로 인한 우리집 피해 보상 절차는?")

    if st.button("🚀 전담 AI 마스터 답변 요청", use_container_width=True, type="primary"):
        if user_question:
            with st.spinner("마스터가 법령과 약관을 분석 중입니다..."):
                try:
                    # 🔴 에러 해결 핵심: 'latest'를 빼고 정확한 모델 코드 'gemini-1.5-flash' 사용
                    chat_model = genai.GenerativeModel('gemini-1.5-flash')
                    response = chat_model.generate_content(f"{SYSTEM_PROMPT}\n\n질문: {user_question}")
                    st.session_state.chat_answer = response.text
                except Exception as e:
                    # 상세 에러 확인을 위해 e 출력
                    st.error(f"답변 생성 중 오류가 발생했습니다. (모델 확인 필요): {e}")
        else:
            st.warning("질문을 먼저 입력해 주세요.")

with col_ai_img:
    st.write("") 
    if st.button("👤 AI 전문가 인사 듣기", use_container_width=True):
        welcome_msg = "안녕하세요. 궁금하신 사항 있으시면 입력창에 입력해주세요. 구글 크롬을 권장합니다."
        speak(welcome_msg)
    
    img_path = "https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/ai_expert.png"
    try:
        st.image(img_path, caption="골드키지사 전담 AI 마스터", use_container_width=True)
    except:
        st.info("💡 이미지 파일을 불러오고 있습니다.")

# ==========================================
# [SECTION 8-10] 결과 출력
# ==========================================
if "chat_answer" in st.session_state:
    st.markdown("---")
    st.info("📢 **전담 AI 마스터 답변 결과**")
    st.write(st.session_state.chat_answer)

st.divider()
success_msg = "FC님, AI와 함께 첨단 보험상담의 주역이 되세요."
if st.button("🚀 응원 메시지 듣기", use_container_width=True):
    st.balloons(); st.write(f"### {success_msg}"); speak(success_msg)

st.error("**[법적 고지]** 본 리포트의 법률적 책임은 사용자에게 귀속되며 AI 분석 결과는 상담 참고용 자료입니다.")
