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
- **약 8년 무료 사용 가능 토큰 구글 제공**
"""

SYSTEM_PROMPT = """당신은 30년 현장 지식과 손해사정 전문성을 갖춘 보험 분석 AI입니다. 모든 답변은 근거 법령을 바탕으로 하십시오."""

# ==========================================
# [SECTION 2] 음성 및 보안 엔진
# ==========================================
def s_voice(text):
    return f"""<script>window.speechSynthesis.cancel(); var msg = new SpeechSynthesisUtterance("{text}");
    msg.lang = 'ko-KR'; msg.rate = 1.0; msg.pitch = 0.85; window.speechSynthesis.speak(msg);</script>"""

def goodbye_sequence():
    return """<script>window.speechSynthesis.cancel(); var msg = new SpeechSynthesisUtterance("보안 규정에 따라 로딩된 모든 자료를 파기했습니다.");
    msg.lang = 'ko-KR'; window.speechSynthesis.speak(msg);</script>"""

# ==========================================
# [SECTION 3] 사이드바 (사용자 센터 & API 가이드)
# ==========================================
with st.sidebar:
    st.header("🔑 사용자 센터")
    user_name = st.text_input("상담원 성함", "")
    
    st.divider()
    st.markdown("### 🛠️ API 키 발급 안내")
    st.link_button("🌐 구글 API 키 발급받기 (무료)", "https://aistudio.google.com/app/apikey")
    
    st.divider()
    current_date = dt.now().date()
    expiry_date = datetime.date(2026, 4, 30)
    
    if current_date <= expiry_date:
        user_status = "정회원 로그인"
        st.info("🔓 **4월 30일까지 사용 제한 없음**")
    else:
        user_status = st.radio("접속 권한", ["방문자(Tutorial)", "정회원 로그인"])
    
    st.markdown(TOKEN_POLICY)
    
    st.divider()
    if st.button("❌ 종료 시 모든 데이터 자동 파기", use_container_width=True):
        st.components.v1.html(goodbye_sequence(), height=0)
        st.cache_data.clear()
        st.session_state.clear()
        time.sleep(2.0)
        st.rerun()

# ==========================================
# [SECTION 4] 메인 환대 메시지
# ==========================================
st.title("👑 골드키지사 AI 마스터")
if user_name:
    st.success(f"🌟 {user_name} 상담원님, 반갑습니다! 오늘 상담도 성공하시길 응원합니다.")

# ==========================================
# [SECTION 5] 최상단 직관적 질문 센터 (🎤 마이크 & ❓ 퀘스쳔마크)
# ==========================================
st.write("---")
st.markdown("### 🎤 여기를 클릭하고 질문하세요! (또는 아래에 입력)")
q_col1, q_col2 = st.columns([0.05, 0.95])
with q_col1:
    st.title("❓")
with q_col2:
    user_question = st.text_area("", placeholder="여기에 질문을 입력하세요. (예: 뇌혈관 질환 진단비 합의 요령 알려줘)", height=100)

if st.button("🚀 AI 전문가에게 질문하기", use_container_width=True):
    if user_question:
        with st.spinner("전문가 그룹이 답변을 준비 중입니다..."):
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(f"{SYSTEM_PROMPT}\n\n질문: {user_question}")
            st.session_state.chat_answer = response.text
    else:
        st.warning("질문을 입력해 주세요.")

if "chat_answer" in st.session_state:
    st.info("📢 **AI 전문가 답변 결과**")
    st.write(st.session_state.chat_answer)

# ==========================================
# [SECTION 6] 증권 분석 센터 (폭 확장 레이아웃)
# ==========================================
st.divider()
st.write("### 📂 2단계: 증권 분석 및 고객 맞춤 컨설팅")
c1, c2, c3 = st.columns([1, 1, 1])
with c1:
    customer_name = st.text_input("상담 대상 고객명", "고객님")
with c2:
    hi_premium = st.number_input("월 건강보험료 (원)", value=0)
with c3:
    debt = st.number_input("기존 부채 (만원)", value=0)

uploaded_files = st.file_uploader("📂 분석할 증권 이미지를 선택해 주세요 (여러 장 가능)", accept_multiple_files=True)

if st.button("🔍 증권 통합 분석 시작", use_container_width=True):
    if uploaded_files:
        with st.spinner("증권을 정밀 분석 중입니다..."):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)
                content_parts = [f"상담원:{user_name}, 고객:{customer_name}, 건보료:{hi_premium}, 부채:{debt}"]
                for f in uploaded_files:
                    img = PIL.Image.open(f)
                    content_parts.append(img)
                response = model.generate_content(content_parts)
                st.session_state.analysis_answer = response.text
                
                # 가처분 소득 로직 테이블
                est_income = hi_premium * 40 / 10000
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
# [SECTION 7] 분석 결과 리포트 출력
# ==========================================
if "analysis_answer" in st.session_state:
    st.markdown("---")
    st.markdown(st.session_state.analysis_answer)

# ==========================================
# [SECTION 8] 전문 지식 데이터베이스
# ==========================================
st.divider()
tab1, tab2, tab3 = st.tabs(["🛡️ 보상 실무 데이터", "🏢 법인 세무 가이드", "👤 회원가입 혜택"])
with tab1:
    st.info("🎯 판례 2001다1480: 합의 당시 예상 못한 중대 후유증은 추가 청구 가능")
    st.write("- 보험사 면책 주장에 대한 법리적 대응 근거 제공")
with tab2:
    st.warning("💼 해지환급금: 자산계상(사업준비금) 원칙 준수 가이드")
    st.write("- CEO 플랜 시 법인세 절감 및 비용 처리 적정성 분석")
with tab3:
    st.success("🎁 회원가입 혜택: 1년간 무료 사용")
    st.write("- 고도화 이벤트 종료 후에도 1년간 무상 지원 예정")

# ==========================================
# [SECTION 9] 성공 응원 및 음성 엔진
# ==========================================
st.divider()
if st.button("🚀 모든 FC님들의 성공을 위한 업데이트 확인", use_container_width=True):
    st.balloons()
    display_name = user_name if user_name else "이세윤"
    msg = f"불철주야 매진하시는 {display_name} FC님! 보험 시장의 주인공이 되십시오."
    st.write(f"### {msg}")
    st.components.v1.html(s_voice(msg), height=0)

# ==========================================
# [SECTION 10] 하단 보안 및 법적 고지
# ==========================================
st.error("**[법적 고지]** 본 리포트의 법률적 책임은 사용자에게 귀속되며 AI 분석 결과는 상담 참고용 자료입니다.")
st.sidebar.caption(f"최종 업데이트: {dt.now().strftime('%Y-%m-%d %H:%M')}")
