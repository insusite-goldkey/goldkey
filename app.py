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

# 🔴 정책 변경 반영 (2026.09 회원제 / 2027.03 정책변경)
TOKEN_POLICY = """
💡 **골드키지사 AI 사용 정책**
- **4월 30일까지 사용 제한 없음** (고도화 이벤트)
- **2026.09.부터 회원제 시행**
- **무료 회원가입 시 1년간 무료 사용 혜택 제공** (2027.03. 정책변경)
- **약 8년 무료사용 가능 토큰 구글 제공**
"""

SYSTEM_PROMPT = """당신은 30년 현장 지식과 손해사정 전문성을 갖춘 보험 분석 AI입니다. 모든 답변은 근거 법령을 바탕으로 하십시오."""

# ==========================================
# [SECTION 2] 음성 재생 엔진 (누를 때마다 재생되는 로직)
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
# [SECTION 3] 사이드바 (업데이트된 정책 반영)
# ==========================================
with st.sidebar:
    st.header("🔑 사용자 센터")
    user_name = st.text_input("상담원 성함", "")
    st.divider()
    
    if st.button("📝 회원가입 및 혜택 안내"):
        msg = "2026년 9월부터 회원제가 시행되며, 무료 회원가입 시 1년간 무료 사용 혜택을 드립니다. 이는 2027년 3월 변경된 정책에 따릅니다."
        st.info(msg)
        speak(msg)
        
    if st.button("🛠️ API 키 발급 가이드"):
        msg = "개인용 API 키를 등록하시면 본인의 토큰을 사용하여 안정적인 분석이 가능합니다."
        st.warning(msg)
        speak(msg)
        st.markdown('<a href="https://aistudio.google.com/app/apikey" target="_blank" style="text-decoration: none;"><button style="width: 100%; padding: 10px; background-color: #1E88E5; color: white; border: none; border-radius: 5px; cursor: pointer;">🌐 구글 API 키 발급 (새 창)</button></a>', unsafe_allow_html=True)

    if st.button("📖 튜토리얼 시작"):
        msg = "1단계에서 증권을 분석하고, 2단계에서 AI 전문가에게 상세 내용을 질문하십시오."
        st.success(msg)
        speak(msg)

    st.divider()
    st.markdown(TOKEN_POLICY)
    
    if st.button("❌ 종료 시 데이터 자동 파기", use_container_width=True):
        speak("보안 규정에 따라 로딩된 모든 자료를 파기했습니다.")
        st.cache_data.clear()
        st.session_state.clear()
        time.sleep(1.0)
        st.rerun()

# ==========================================
# [SECTION 4-6] 메인 및 1단계 (동일 유지)
# ==========================================
st.title("👑 골드키지사 AI 마스터")
if user_name:
    st.success(f"🌟 {user_name} 상담원님, 반갑습니다!")

st.write("---")
st.write("### 📂 1단계: 증권 이미지 정밀 분석")
c1, c2, c3 = st.columns([1, 1, 1])
with c1: customer_name = st.text_input("고객명", "고객님")
with c2: hi_premium = st.number_input("월 보험료(원)", value=0)
with c3: debt = st.number_input("부채(만원)", value=0)

col_upload, col_action = st.columns([2, 1])
with col_upload:
    uploaded_files = st.file_uploader("증권 사진 업로드", accept_multiple_files=True)
with col_action:
    st.write(" ")
    st.write(" ")
    if st.button("🔍 증권 통합 분석 시작 🚀", use_container_width=True, type="primary"):
        if uploaded_files:
            with st.spinner("전문가 그룹이 분석 중입니다..."):
                # 실제 이미지 처리 및 Gemini 분석 로직 실행
                pass

# ==========================================
# [SECTION 7] 2단계: 질문창 (사진 높이 정렬 및 음성 안내)
# ==========================================
st.divider()
st.markdown("""<style>.big-font { font-size:22px !important; font-weight: bold; color: #1E88E5; }</style>""", unsafe_allow_html=True)

col_input_area, col_ai_img = st.columns([7, 3])

with col_input_area:
    st.markdown('<p class="big-font">🏆 2단계: AI 전문가에게 상세 질문하기</p>', unsafe_allow_html=True)
    
    col_mic, col_btn_desc = st.columns([1, 10])
    with col_mic:
        st.markdown("## 🎤")
    with col_btn_desc:
        # 누를 때마다 음성이 나오도록 speak 함수 호출
        if st.button("🎤 음성 인식 질문 가이드", use_container_width=True):
            guide_msg = "아래 질문창에 궁금한 점을 입력하고 분석 요청 버튼을 눌러주세요."
            st.toast(guide_msg)
            speak(guide_msg)
            
    # 사진 높이와 맞추기 위해 height=330 설정
    user_question = st.text_area("❓ 전문가에게 물어볼 내용을 상세히 적어주세요", height=330, placeholder="질문을 입력하세요...")

with col_ai_img:
    st.write("") 
    img_url = "https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/ai_expert.png"
    
    # 사진 위 안내 버튼 (클릭 시 환영 인사)
    if st.button("👤 AI 전문가 인사 듣기", use_container_width=True):
        welcome_msg = "안녕하세요. 궁금하신 사항 있으시면 제 옆에 있는 마이크 버튼을 누르고 말을 하거나 입력창에 입력해주세요."
        speak(welcome_msg)
        
    try:
        st.image(img_url, caption="골드키지사 전담 AI 마스터", use_container_width=True)
    except:
        st.info("💡 이미지 파일을 불러오고 있습니다.")

if st.button("🚀 AI 전문가 그룹 분석 요청", use_container_width=True):
    if user_question:
        with st.spinner("전문가 분석 중..."):
            # 질문 분석 로직 실행
            pass

# [이하 하단 공통]
