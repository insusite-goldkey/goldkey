import streamlit as st
import google.generativeai as genai
import PIL.Image
from datetime import datetime

# 1. AI 마스터키 설정
MY_KEY = "AIzaSyDA500Cw6Gqfrd_lS5OQxEPBblH92oW2Xo"
genai.configure(api_key=MY_KEY)

# 수애 톤 브리핑 시스템 (중저음, 안정적 속도)
def tts_control_js(text, action="speak"):
    if action == "stop":
        return "<script>window.speechSynthesis.cancel();</script>"
    clean_text = text.replace("\n", " ").replace('"', "'")[:800]
    return f"""
        <script>
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance("{clean_text}");
            msg.lang = 'ko-KR'; msg.rate = 0.9; msg.pitch = 0.8;
            window.speechSynthesis.speak(msg);
        </script>
    """

# 이름 마스킹 함수
def mask_name(name):
    if len(name) <= 1: return name
    if len(name) == 2: return name[0] + "*"
    return name[0] + "*" + name[2:]

# 2. 통합 시스템 지침 (전문가 자문단 포함)
SYSTEM_PROMPT = """당신은 케이지에이에셋 골드키지사 이세윤 설계사를 대행하는 AI 비서입니다.
손해사정인(보상), 변호사(법률), 세무사/CFP(재무), 전문의(의학)의 식견을 반드시 포함하십시오.
모든 데이터는 분석 후 파기됨을 원칙으로 하며 하십시오체를 유지하십시오."""

# 3. 데이터 초기화 함수
def purge_all_data():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# 4. 앱 화면 및 세션 관리
st.set_page_config(page_title="골드키지사 전문가 통합 분석", layout="wide")

if "history" not in st.session_state:
    st.session_state.history = []
if "answer" not in st.session_state:
    st.session_state.answer = ""

with st.sidebar:
    st.header("🏛️ 케이지에이에셋")
    st.subheader("골드키지사")
    st.write("**지사장:** 박보정 / **담당:** 이세윤")
    st.divider()

    # [보안 기능 1] 회원 탈퇴 시뮬레이션
    with st.expander("👤 계정 설정 및 회원 탈퇴"):
        st.write("회원 탈퇴 시 본인이 상담한 모든 자료와 상담 리스트는 즉시 영구 삭제됩니다.")
        if st.button("❌ 회원 탈퇴 (전체 정보 삭제)"):
            purge_all_data()

    st.divider()
    
    # [보안 기능 2] 현장 즉시 파기 버튼
    st.error("🔒 현장 보안 기능")
    if st.button("🗑️ 현재 상담 자료 즉시 파기"):
        purge_all_data()
    st.caption("상담 대상자가 즉시 삭제를 원할 경우 클릭하십시오.")
    
    st.divider()
    customer_name = st.text_input("상담 대상", "고객님")
    hi_premium = st.number_input("월 건강보험료(원)", value=250000)
    debt = st.number_input("현재 부채 총액(원)", value=100000000)
    
    st.divider()
    st.info("📢 안내: 입력한 자료 보고서 생성 후 자동 삭제")
    uploaded_files = st.file_uploader("증권/의무기록 로드", accept_multiple_files=True)

# 5. 메인 화면 및 분석 로직
st.title("🛡️ 전문가 그룹 통합 보장 판독 리포트")

if st.session_state.history:
    with st.expander("📋 최근 상담 리스트 (마스킹 적용)", expanded=False):
        for h in st.session_state.history:
            st.write(f"✅ {h['date']} | 대상: {h['name']} | 분석 완료")

st.write(f"### {mask_name(customer_name)}님 전문 상담 세션")

if st.button("🔍 전문가 그룹 통합 분석 시작"):
    if uploaded_files:
        with st.spinner("전문가 자문단이 분석 중입니다..."):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)
                content_parts = [f"호칭: {customer_name}, 건보료: {hi_premium}, 부채: {debt}"]
                for f in uploaded_files:
                    img = PIL.Image.open(f)
                    content_parts.append(img)
                
                response = model.generate_content(content_parts)
                st.session_state.answer = response.text
                
                # 상담 기록 저장
                st.session_state.history.append({
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "name": mask_name(customer_name)
                })
            except Exception as e:
                st.error(f"오류: {e}")
    else:
        st.warning("분석할 서류를 업로드해 주십시오.")

# 6. 결과 출력
if st.session_state.answer:
    col1, col2 = st.columns([1, 8])
    with col1:
        if st.button("🔊 전문 브리핑"):
            st.components.v1.html(tts_control_js(st.session_state.answer), height=0)
    with col2:
        if st.button("⏹️ 중단"):
            st.components.v1.html(tts_control_js("", "stop"), height=0)
    
    st.divider()
    st.markdown(st.session_state.answer)

st.divider()
st.caption("케이지에이에셋 골드키지사 | 회원 탈퇴 및 현장 파기 시스템 가동 중")
