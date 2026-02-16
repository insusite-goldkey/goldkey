import streamlit as st
import google.generativeai as genai
import PIL.Image

# 1. AI 마스터키 설정
genai.configure(api_key="AIzaSyDA500Cw6Gqfrd_lS5OQxEPBblH92oW2Xo")

# 2. 통합 가이드라인 주입
SYSTEM_PROMPT = """
당신은 '이세윤 설계사'의 30년 경력과 전문성을 계승한 [고객 보험 상담 전문 AI 비서]입니다.
[SECTION 1. 페르소나 및 상담 기본 원칙]
- 핵심 가치: 30년 현장 실무 지식, 고객 중심 보상 철학.
- 전문성: CFP 수준 재무설계, 전문의 수준 의학 지식, 손해사정 및 법률 해석 능력.
[SECTION 2. 답변 생성 원칙]
- 규칙 1: 금감원 보도자료, 판례, 손해사정 지침서 기준 필수.
- 규칙 2: 법률(상법), 의학(KCD), 실무 순으로 자체 검토 후 답변.
[SECTION 3. 인사 및 화법 가이드라인]
- 최초 대화 시: "안녕하십니까? 고객님. 30년 상담 경력 보험설계사의 지혜를 담은 AI 비서입니다."라고 인사하십시오.
- 이후 대화 시: 반복 인사 생략, 효율적 본론 진입.
- 화법 및 어조: 정중하고 따뜻하며 신뢰감 있는 '하십시오체'를 사용할 것.
"""

st.set_page_config(page_title="골드키지사 AI", layout="wide")
st.sidebar.header("🏆 골드키지사 관리자")
customer_name = st.sidebar.text_input("고객 성함", "박성준")

st.title("🏆 골드키지사 보장분석 AI 마스터")
st.write(f"### {customer_name} 고객님 전문 상담 세션")

uploaded_file = st.file_uploader("증권/진단서 사진 업로드", type=['jpg', 'png', 'jpeg', 'pdf'])

if uploaded_file:
    with st.spinner("전문가 그룹의 지식을 취합하여 분석 중입니다..."):
        try:
            model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)
            img = PIL.Image.open(uploaded_file)
            prompt = f"{customer_name} 고객님의 증권을 분석하고, 하십시오체로 답변하십시오."
            response = model.generate_content([prompt, img])
            st.success("✅ 분석 완료")
            st.markdown("---")
            st.markdown(response.text)
        except Exception as e:
            st.error(f"오류 발생: {e}")
