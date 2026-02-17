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
- **회원가입 시 1년간 무료** 사용 혜택 제공
- **약 8년 무료사용 가능 토큰 구글 제공**
"""

SYSTEM_PROMPT = """당신은 30년 현장 지식과 손해사정 전문성을 갖춘 보험 분석 AI입니다. 모든 답변은 근거 법령을 바탕으로 하십시오."""

# ==========================================
# [SECTION 2] 음성 및 보안 엔진
# ==========================================
def s_voice(text):
    return f"""<script>window.speechSynthesis.cancel(); var msg = new SpeechSynthesisUtterance("{text}");
    msg.lang = 'ko-KR'; msg.rate = 1.0; msg.pitch = 0.95; window.speechSynthesis.speak(msg);</script>"""

def goodbye_sequence():
    return """<script>window.speechSynthesis.cancel(); var msg = new SpeechSynthesisUtterance("보안 규정에 따라 로딩된 모든 자료를 파기했습니다.");
    msg.lang = 'ko-KR'; window.speechSynthesis.speak(msg);</script>"""

# ==========================================
# [SECTION 3] 사이드바 (회원가입/API/튜토리얼 및 음성안내)
# ==========================================
with st.sidebar:
    st.header("🔑 사용자 센터")
    user_name = st.text_input("상담원 성함", "")
    
    st.divider()
    
    # 1. 회원가입 가이드 (음성 포함)
    if st.button("📝 회원가입 및 혜택 안내"):
        msg = "회원가입 시 1년간 무료 사용 혜택과 구글이 제공하는 8년치 토큰을 우선 배정해 드립니다."
        st.info(msg)
        st.components.v1.html(s_voice(msg), height=0)
        
    # 2. API 키 발급 (음성 포함)
    if st.button("🛠️ API 키 발급 가이드"):
        msg = "개인용 API 키를 등록하시면 본인의 토큰을 사용하여 안정적인 분석이 가능합니다. 새 창에서 발급받아 주세요."
        st.warning(msg)
        st.components.v1.html(s_voice(msg), height=0)
        st.markdown('<a href="https://aistudio.google.com/app/apikey" target="_blank" style="text-decoration: none;"><button style="width: 100%; padding: 10px; background-color: #1E88E5; color: white; border: none; border-radius: 5px; cursor: pointer;">🌐 구글 API 키 발급 (새 창)</button></a>', unsafe_allow_html=True)

    # 3. 사용법 튜토리얼 (음성 포함)
    if st.button("📖 튜토리얼 시작"):
        msg = "1단계에서 증권 사진을 올리고, 2단계에서 AI 전문가에게 상세 내용을 질문하십시오. 상담의 주역이 되실 준비가 되셨습니다."
        st.success(msg)
        st.components.v1.html(s_voice(msg), height=0)

    st.divider()
    
    current_date = dt.now().date()
    expiry_date = datetime.date(2026, 4, 30)
    
    if current_date <= expiry_date:
        st.info("🔓 **정회원 권한 자동 승인 중**")
    else:
        user_status = st.radio("접속 권한", ["방문자(Tutorial)", "정회원 로그인"])
    
    st.markdown(TOKEN_POLICY)
    
    if st.button("❌ 종료 시 데이터 자동 파기", use_container_width=True):
        st.components.v1.html(goodbye_sequence(), height=0)
        st.cache_data.clear()
        st.session_state.clear()
        time.sleep(1.0)
        st.rerun()

# ==========================================
# [SECTION 4] 메인 환영 메시지
# ==========================================
st.title("👑 골드키지사 AI 마스터")
if user_name:
    st.success(f"🌟 {user_name} 상담원님, 반갑습니다!")

# ==========================================
# [SECTION 5] 1단계: 증권 이미지 정밀 분석
# ==========================================
st.write("---")
st.write("### 📂 1단계: 증권 이미지 정밀 분석")
c1, c2, c3 = st.columns([1, 1, 1])
with c1:
    customer_name = st.text_input("상담 대상 고객명", "고객님")
with c2:
    hi_premium = st.number_input("월 건강보험료 (원)", value=0)
with c3:
    debt = st.number_input("기존 부채 (만원)", value=0)

col_upload, col_action = st.columns([2, 1])
with col_upload:
    uploaded_files = st.file_uploader("증권 사진 업로드", accept_multiple_files=True)
with col_action:
    st.write(" ")
    st.write(" ")
    if st.button("🔍 증권 통합 분석 시작 🚀", use_container_width=True, type="primary"):
        if uploaded_files:
            with st.spinner("전문가 그룹이 분석 중입니다..."):
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)
                    content_parts = [f"상담원:{user_name}, 고객:{customer_name}, 건보료:{hi_premium}, 부채:{debt}"]
                    for f in uploaded_files:
                        img = PIL.Image.open(f)
                        content_parts.append(img)
                    response = model.generate_content(content_parts)
                    st.session_state.analysis_answer = response.text
                    
                    est_income = hi_premium * 40 / 10000
                    st.markdown("---")
                    st.markdown("### [💰 소득 및 필요보장 통합표]")
                    data = {
                        "분석 항목": ["💵 추산 연봉", "🧬 필요 암 보장", "🧠 필요 뇌/심 보장", "🕊️ 사망 보장", "⏳ 노후준비(연금)"],
                        "가이드라인": [f"{est_income:.1f}억", "5.0억", "5.4억", f"{debt/10000 + (est_income*5):.1f}억", f"월 {est_income/12*10000:,.0f}원"],
                        "판독 결과": ["정밀 역산", "⚠️ 부족", "⚠️ 부족", "🚨 보강필요", "🚨 즉시점검"]
                    }
                    st.table(pd.DataFrame(data))
                except Exception as e:
                    st.error(f"오류: {e}")

# ==========================================
# [SECTION 6] 증권 분석 결과 출력
# ==========================================
if "analysis_answer" in st.session_state:
    st.markdown(st.session_state.analysis_answer)

# ==========================================
# [SECTION 7] 2단계: AI 전문가 상세 질문 (사진 우측 배치)
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
        if st.button("🎤 음성 인식 질문 가이드 (클릭 시 음성안내)", use_container_width=True):
            guide_msg = "아래 질문창에 분석된 내용 중 궁금한 점을 입력하고 분석 요청 버튼을 눌러주세요."
            st.toast(guide_msg)
            st.components.v1.html(s_voice(guide_msg), height=0)
            
    user_question = st.text_area("❓ 전문가에게 물어볼 내용을 상세히 적어주세요", height=230, placeholder="질문을 입력하세요...")

with col_ai_img:
    st.write("") 
    # insusite-goldkey 계정의 ai_expert.png 이미지를 사용합니다.
    img_url = "https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/ai_expert.png"
    try:
        st.image(img_url, caption="골드키지사 전담 AI 마스터", use_container_width=True)
    except:
        st.info("💡 이미지 파일을 확인 중입니다.")

if st.button("🚀 AI 전문가 그룹 분석 요청", use_container_width=True):
    if user_question:
        with st.spinner("전문가 분석 중..."):
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(f"{SYSTEM_PROMPT}\n\n질문: {user_question}")
            st.session_state.chat_answer = response.text
    else:
        st.warning("질문을 먼저 입력해 주세요.")

# ==========================================
# [SECTION 8] 질문 답변 출력
# ==========================================
if "chat_answer" in st.session_state:
    st.info("📢 **AI 전문가 답변 결과**")
    st.write(st.session_state.chat_answer)

# ==========================================
# [SECTION 9] 성공 응원 및 음성 가이드
# ==========================================
st.divider()
col_success_icon, col_success_btn = st.columns([1, 10])
with col_success_icon:
    st.markdown("## 🎊")
with col_success_btn:
    if st.button("🚀 FC님 AI와 함께 첨단 보험상담의 주역이 되세요", use_container_width=True):
        st.balloons()
        display_name = user_name if user_name else "이세윤"
        msg = f"{display_name} FC님 AI와 함께 첨단 보험상담의 주역이 되세요."
        st.write(f"### {msg}")
        st.components.v1.html(s_voice(msg), height=0)

# ==========================================
# [SECTION 10] 하단 보안 및 법적 고지
# ==========================================
st.error("**[법적 고지]** 본 리포트의 법률적 책임은 사용자에게 귀속되며 AI 분석 결과는 상담 참고용 자료입니다.")
st.sidebar.caption(f"최종 업데이트: {dt.now().strftime('%Y-%m-%d %H:%M')}")
