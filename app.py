import streamlit as st
import google.generativeai as genai
import PIL.Image

# 1. AI 마스터키 설정
genai.configure(api_key="AIzaSyDA500Cw6Gqfrd_lS5OQxEPBblH92oW2Xo")

# 2. 이세윤 설계사 최종 페르소나 및 인사 가이드라인 주입
SYSTEM_PROMPT = """
당신은 '이세윤 설계사'의 30년 경력과 전문성을 계승한 [고객 보험 상담 전문 AI 비서]입니다.

[SECTION 1. 페르소나 및 정체성]
- 성명: 고객 보험 상담 전문 AI 비서 (이세윤 설계사 대행)
- 핵심 가치: 30년 경력의 현장 실무 지식과 고객 중심 보상 철학 계승.
- 전문성: CFP 수준의 자산 관리, 전문의 수준의 의학 지식(암, 뇌심혈관, 치매 등), 손해사정 및 법률 해석 능력.

[SECTION 2. 답변 생성 및 검증 원칙]
- 규칙 1 (근거 중심): 반드시 판결문, 금융감독원 보도자료, 손해사정 실무 지침서를 근거로 작성하십시오.
- 규칙 2 (3중 검증): 답변 전 법률(상법), 의학(KCD), 실무(이세윤 설계사의 위로) 관점에서 자가 검토하십시오.
- 규칙 3 (특화 전략): 중증 질환 특약 매칭, CDR 척도 분석, 과실 비율 및 장해 등급 법률 쟁점을 고지하십시오.

[SECTION 3. 인사 및 화법 가이드라인 - 필수 준수]
- 최초 대화 시: 반드시 "안녕하십니까? 고객님. 30년 상담 경력 보험설계사의 지혜를 담은 AI 비서입니다."라고 인사하며 시작하십시오.
- 이후 대화 시: 반복적인 인사는 생략하고 본론으로 바로 진입하여 효율성을 높이십시오.
- 어조: 철저한 2인칭 대화를 유지하며, 정중하고 신뢰감 있는 '하십시오체'를 사용하십시오.
- 태도: 전문 용어는 사용하되, 고객이 이해하기 쉽게 '이세윤 설계사의 언어'로 풀어서 설명하십시오.
"""

# 3. 페이지 레이아웃 설정
st.set_page_config(page_title="골드키지사 AI 마스터", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #002d5b; color: white; font-weight: bold; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

# 4. 사이드바 구성
st.sidebar.header("🏆 골드키지사 관리자")
customer_name = st.sidebar.text_input("고객 성함", "박성준")
analysis_mode = st.sidebar.selectbox("분석 모드", ["종합 보장 분석", "법률/손해사정 검토", "의학적 보상 상담"])
st.sidebar.divider()
st.sidebar.write(f"**담당 설계사:** 이세윤")
st.sidebar.caption("30년 경력의 노하우와 CFP의 전문성")

# 5. 메인 화면
st.title("🏆 골드키지사 보장분석 AI 마스터")
st.write(f"### {customer_name} 고객님 전문 상담 세션")
st.info("💡 본 리포트는 30년 경력의 실무 지식과 판결문, 금감원 자료를 바탕으로 작성됩니다.")

# 대화 상태 저장 (인사말 규칙 적용용)
if "first_run" not in st.session_state:
    st.session_state.first_run = True

# 6. 증권 분석 로직
uploaded_file = st.file_uploader("증권/진단서 사진을 업로드하십시오", type=['jpg', 'png', 'jpeg', 'pdf'])

if uploaded_file:
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.image(uploaded_file, caption="업로드된 분석 서류", use_container_width=True)
    
    with col2:
        with st.spinner("전문가 그룹의 지식을 취합하여 정밀 분석 중입니다..."):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)
                img = PIL.Image.open(uploaded_file)
                
                # 인사 규칙 적용
                if st.session_state.first_run:
                    prompt = f"이 서류를 분석하여 {customer_name} 고객님께 첫 인사를 포함한 정밀 리포트를 '하십시오체'로 작성하십시오."
                    st.session_state.first_run = False
                else:
                    prompt = f"이 서류를 {analysis_mode} 관점에서 분석하여 본론 위주 리포트를 '하십시오체'로 작성하십시오."
                
                response = model.generate_content([prompt, img])
                
                st.success("✅ 분석이 완료되었습니다.")
                st.markdown("---")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"분석 중 오류가 발생했습니다: {e}")

# 7. 하단 면책 문구
st.divider()
st.caption(f"본 리포트는 이세윤 설계사의 상담 철학을 바탕으로 AI가 작성한 참고 자료입니다. 관련 법조문을 참조하였으나 최종 보상 여부는 약관에 따릅니다.")
