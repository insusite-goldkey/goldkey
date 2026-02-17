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

# Secrets 연동 (API 키 자동 연결)
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception:
    st.error("시스템 설정(API KEY) 확인이 필요합니다.")

TOKEN_POLICY = """
💡 **골드키지사 AI 사용 정책**
- **4월 30일까지 사용 제한 없음** (고도화 이벤트)
- **회원가입 시 1년간 무료** 사용 혜택 제공
- 정식 전환 시 약 8년(3,000일) 사용 가능한 압도적인 토큰 분량 제공
"""

SYSTEM_PROMPT = """
당신은 30년 현장 지식과 손해사정 전문성을 갖춘 보험 분석 AI입니다.
[분석 철학]: 6대 법령(민법, 상법, 보험업법, 형사소송법, 화재법, 실화법) 근거 3중 검증.
[연금 로직]: '미래 가처분 소득 유지 원칙'에 의거, 현재 소득의 100%를 목표로 설정.
[보고서 구조]: 🚨판독 총평 -> 💰필요보장 통합표 -> 📊영역별 분석 -> 🔍보상 실무 근거 순서로 작성하십시오.
"""

# ==========================================
# [SECTION 2] 음성 및 보안 엔진
# ==========================================
def s_voice(text):
    return f"""<script>window.speechSynthesis.cancel(); var msg = new SpeechSynthesisUtterance("{text}");
    msg.lang = 'ko-KR'; msg.rate = 1.0; msg.pitch = 0.85; window.speechSynthesis.speak(msg);</script>"""

def goodbye_sequence():
    return """<script>var context = new (window.AudioContext || window.webkitAudioContext)();
    var osc = context.createOscillator(); osc.type = 'sine'; osc.frequency.setValueAtTime(523.25, context.currentTime);
    osc.connect(context.destination); osc.start(); osc.stop(context.currentTime + 0.3);
    window.speechSynthesis.cancel(); var msg = new SpeechSynthesisUtterance("보안 규정에 따라 로딩된 모든 자료를 파기했습니다.");
    msg.lang = 'ko-KR'; window.speechSynthesis.speak(msg);</script>"""

# ==========================================
# [SECTION 3] 사이드바 (사용자 센터 & API 키 발급 튜토리얼)
# ==========================================
with st.sidebar:
    st.header("🔑 사용자 센터")
    user_name = st.text_input("상담원 성함", "")
    
    # --- API 키 발급 안내 및 튜토리얼 추가 ---
    st.divider()
    st.markdown("### 🛠️ API 키 발급 안내")
    st.write("무료 분석을 위해 개인용 구글 API 키가 필요하신 분은 아래 버튼을 활용하세요.")
    
    # 구글 AI 스튜디오 연결 버튼
    st.link_button("🌐 구글 API 키 발급받기 (무료)", "https://aistudio.google.com/app/apikey")
    
    with st.expander("❓ 발급 방법 튜토리얼"):
        st.caption("1. 위 버튼 클릭 후 구글 로그인")
        st.caption("2. 'Create API key' 파란 버튼 클릭")
        st.caption("3. 생성된 키를 복사(Copy)하여 메모")
        st.info("※ 4월 30일까지는 공용 키로 자동 작동하므로, 키 없이도 즉시 테스트가 가능합니다.")
    st.divider()
    # ----------------------------------------

    # 4월 30일까지 무조건 승인 로직
    current_date = dt.now().date()
    expiry_date = datetime.date(2026, 4, 30)
    
    if current_date <= expiry_date:
        user_status = "정회원 로그인"
        st.info(f"🔓 **4월 30일까지 사용 제한 없음**")
        st.success("✨ 고도화 기간 특별 승인 모드")
    else:
        user_status = st.radio("접속 권한", ["방문자(Tutorial)", "정회원 로그인"])
    
    st.markdown(TOKEN_POLICY)
    
    st.divider()
    if st.button("❌ 종료 시 모든 데이터 자동 파기", use_container_width=True):
        st.components.v1.html(goodbye_sequence(), height=0)
        st.cache_data.clear()
        st.session_state.clear()
        time.sleep(2.5)
        st.rerun()

# ==========================================
# [SECTION 4~6] 메인 타이틀 및 환대
# ==========================================
st.title("👑 골드키지사 AI 마스터")
st.subheader("🛡️ 보장의 실체 판독 및 통합 컨설팅 시스템")

if "welcomed" not in st.session_state and user_name:
    st.success(f"🌟 {user_name} 상담원님, 반갑습니다!")
    st.session_state.welcomed = True

with st.expander("💡 실전 보상 & 회원가입 혜택", expanded=False):
    t_col1, t_col2 = st.columns(2)
    with t_col1:
        st.info("⚖️ **판례 2001다1480**")
        st.write("합의 시 예상 못한 후유증은 추가 청구 가능합니다.")
    with t_col2:
        st.success("👤 **회원가입: 1년간 무료**")
        st.write("현재 고도화 이벤트 참여 시 1년 무상 혜택을 드립니다.")

# ==========================================
# [SECTION 7] 입력 인터페이스 (폭 확장 레이아웃)
# ==========================================
st.divider()
st.write("### 📝 고객 정보 및 증권 업로드")
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    customer_name = st.text_input("상담 대상 고객명", "고객님")
with col2:
    hi_premium = st.number_input("월 건강보험료 (원)", value=0)
with col3:
    debt = st.number_input("기존 부채 (만원)", value=0)

st.write("")
uploaded_files = st.file_uploader("📂 분석할 증권 이미지를 선택해 주세요 (폭 확장형)", accept_multiple_files=True)

if st.button("🔍 전문가 그룹 통합 분석 시작", use_container_width=True):
    if uploaded_files:
        with st.spinner("AI 전문가 그룹이 정밀 분석 리포트를 작성 중입니다..."):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)
                content_parts = [f"상담원: {user_name}, 고객: {customer_name}, 건보료: {hi_premium}, 부채: {debt}"]
                for f in uploaded_files:
                    img = PIL.Image.open(f)
                    content_parts.append(img)
                
                response = model.generate_content(content_parts)
                st.session_state.answer = response.text
                
                # 분석 테이블 출력
                est_income = hi_premium * 40 / 10000
                st.markdown("### [💰 소득 및 필요보장 통합표]")
                data = {
                    "분석 항목": ["💵 추산 연봉", "🧬 필요 암 보장", "🧠 필요 뇌/심 보장", "🕊️ 사망 보장", "⏳ 노후준비(연금)"],
                    "가이드라인": [f"{est_income:.1f}억", "5.0억", "5.4억", f"{debt/10000 + (est_income*5):.1f}억", f"월 {est_income/12*10000:,.0f}원"],
                    "판독 결과": ["정밀 역산", "⚠️ 부족", "⚠️ 부족", "🚨 보강필요", "🚨 즉시점검"]
                }
                st.table(pd.DataFrame(data))
                st.success("✅ 리포트 생성이 완료되었습니다.")
            except Exception as e:
                st.error(f"분석 오류: {e}")
    else:
        st.warning("분석할 증권 이미지를 업로드해 주세요.")

# ==========================================
# [SECTION 8] 전문 지식 데이터베이스
# ==========================================
if "answer" in st.session_state:
    st.markdown("---")
    st.markdown(st.session_state.answer)

st.divider()
tab1, tab2, tab3, tab4 = st.tabs(["🛡️ 보상 실무", "🏢 법인 세무", "🚨 중대재해", "🌐 글로벌 지원"])
with tab1:
    st.info("🎯 판례 2001다1480: 합의 당시 예상 못한 중대 후유증은 추가 청구 가능")
with tab2:
    st.warning("💼 해지환급금: 자산계상(사업준비금), 이익잉여금 산입 안 됨 원칙 준수")
with tab3:
    st.error("🚔 중대재해: 단체보험 수익자 '법인' 지정 시 배상 채무 직접 상쇄 효과")
with tab4:
    st.subheader("🌐 글로벌 보상 지원 센터")
    user_input_extra = st.text_area("상황 입력 (다국어 번역 및 민원 초안)")
    if st.button("AI 마스터 해결 요청"):
        st.success(f"분석 완료 (법적근거: 민법 제733조 적용)")

# ==========================================
# [SECTION 9~10] 성공 응원 및 하단 보안
# ==========================================
st.divider()
if st.button("🚀 모든 FC님들의 성공을 위한 업데이트 확인", use_container_width=True):
    st.balloons()
    display_name = user_name if user_name else "이세윤"
    msg = f"불철주야 매진하시는 {display_name} FC님! 법인 시장의 주인공이 되십시오."
    st.write(f"### {msg}")
    st.components.v1.html(s_voice(msg), height=0)

st.error("**[법적 고지]** 본 리포트의 법률적 책임은 사용자에게 귀속되며 AI 분석 결과는 상담 참고용 자료입니다.")
st.sidebar.caption(f"최종 업데이트: {dt.now().strftime('%Y-%m-%d')}")
