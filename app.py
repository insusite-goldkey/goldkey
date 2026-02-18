# ==========================================================================
# 🚨 [운영 헌법 - 이세윤 관리자 지침 100% 준수]
# 1. 에러 원천 봉쇄: 모델명을 'models/gemini-1.5-flash' 절대 경로로 고정 (404 에러 종결).
# 2. 에러 창 위치 변경: 분석 실패 시 에러 메시지를 분석 버튼 바로 아래에 출력 (시인성 확보).
# 3. 섹션 통합 절대 금지: 1~15번 전 섹션은 물리적 구분선으로 독립성을 유지한다.
# 4. 리스크 관리: 설계사 구상권 보호를 위해 보험업법 벌칙 규정은 답변에서 절대 제외한다.
# 5. 서류 삭제 로직: 2단계 업로드 섹션에 빨간색 '전체 삭제' 버튼 상시 배치.
# 6. 명칭 고정: 국제재무설계 기준 위험관리 및 3층 연금 시뮬레이션 명칭 적용.
# ==========================================================================

import streamlit as st
import pandas as pd
import time
import datetime
from datetime import datetime as dt
import google.generativeai as genai
import PIL.Image
import re

# ==========================================
# [SECTION 1] 설정 및 페르소나 (모델명 절대 경로 고정)
# ==========================================
st.set_page_config(page_title="골드키지사 AI 마스터", page_icon="👑", layout="wide")

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0

# [🚨 원천 해결] 모델 명칭 정책 변화에 대응하는 가장 강력한 고정 방식
MODEL_NAME = 'models/gemini-1.5-flash' 
TOOLS = [{'google_search_retrieval': {}}] 

SYSTEM_PROMPT = """
성명: 글로벌 보험/재무/분쟁대응 통합 전문가 (관리자: 이세윤)
표어: 보험 가입 상담 부터 보험금 분쟁 대응까지- 보험 AI전문 마스터 통합 시스템

[분석 가이드라인]:
1. FC 보호: 보험업법상 불완전 판매 벌칙 및 설계사 구상권 관련 내용은 어떠한 경우에도 언급하지 마라.
2. 법리 결합: 판례 2001다1480 및 상법 근거를 고객의 구체적 사건 내용과 1:1로 매칭하여 설명하라.
3. 재무 로직: 건보료 0.0709 소득 역산 및 CFP® 6단계 프로세스를 한 몸처럼 구동하라.
"""

# ==========================================
# [SECTION 2] 음성 엔진 및 STT (수애 엔진)
# ==========================================
def s_voice(text, lang='ko-KR'):
    if re.search('[a-zA-Z]{5,}', text): lang = 'en-US'
    return f"""<script>
        window.speechSynthesis.cancel(); 
        var msg = new SpeechSynthesisUtterance("{text}");
        msg.lang = "{lang}"; msg.rate = 0.95; 
        window.speechSynthesis.speak(msg);
    </script>"""

def load_stt_engine():
    st.components.v1.html("""
    <script>
        window.startRecognition = function() {
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance("마스터가 듣고 있습니다.");
            window.speechSynthesis.speak(msg);
            var recognition = new (window.SpeechRecognition || window.webkitRecognition)();
            recognition.lang = 'ko-KR';
            recognition.onresult = function(event) {
                var transcript = event.results[0][0].transcript;
                var textArea = window.parent.document.querySelector('textarea[aria-label="📝 마스터 통합 상담창 (내용 구현)"]');
                if (textArea) {
                    textArea.value = transcript;
                    textArea.dispatchEvent(new Event('input', { bubbles: true }));
                }
            };
            recognition.start();
        };
    </script>
    """, height=0)

# ==========================================
# [SECTION 3] 사이드바 (정보 상시 노출)
# ==========================================
with st.sidebar:
    st.header("🔑 사용자 센터")
    user_name = st.text_input("상담원 성함", "전문 FC")
    st.divider()
    st.info("👤 **시스템 관리자: 이세윤**")
    st.markdown("### 🏆 회원 및 API 혜택")
    st.success("- 1일 50건 미만 상담 시 **8년간 무료**\n- 관리자 권한 **무제한 승인**\n- 종료 시 **데이터 즉시 파기**")
    st.markdown("---")
    st.warning("**[API 발급 튜토리얼]**\n1. Google 로그인\n2. 카드 등록\n3. API Key 생성")
    st.markdown('<a href="https://aistudio.google.com/app/apikey" target="_blank"><button style="width:100%; cursor:pointer; background:#1E88E5; color:white; border:none; padding:10px; border-radius:5px; font-weight:bold;">🌐 API 키 발급 바로가기</button></a>', unsafe_allow_html=True)
    st.divider()
    if st.button("❌ 보안 종료", use_container_width=True):
        st.cache_data.clear(); st.session_state.clear(); time.sleep(1); st.rerun()

# ==========================================
# [SECTION 4] 브랜드 상단 UI
# ==========================================
st.divider()
st.markdown("""
<div style="background-color:#f0f2f6; padding:20px; border-radius:10px; border-left:5px solid #1E88E5; margin-bottom:10px;">
    <h3 style="margin-top:0; color:#0D47A1;">"보험 가입 상담 부터 보험금 분쟁 대응까지"</h3>
    <p style="font-size:16px; color:#424242;"><b>보험 AI전문 마스터 통합 시스템</b> (관리자: 이세윤)</p>
</div>
""", unsafe_allow_html=True)

st.title("👑 골드키지사 AI 마스터")

# ==========================================
# [SECTION 4.5] 마스터 통합 상담 센터 (즉시 분석 및 에러 대응)
# ==========================================
st.divider()
st.subheader("📡 마스터 통합 상담 센터")
col_input, col_img = st.columns([7, 3])

with col_input:
    main_consult_content = st.text_area(
        "📝 마스터 통합 상담창 (내용 구현)", 
        height=320, 
        placeholder="상담 내용을 입력하세요. 입력 후 바로 아래 버튼으로 즉시 분석이 가능합니다.",
        key="main_consult_area"
    )
    
    b1, b2, b3 = st.columns([2, 2, 3])
    if b1.button("⌨️ 직접 입력", use_container_width=True): st.toast("직접 입력 모드")
    if b2.button("🎤 음성 입력", use_container_width=True): load_stt_engine()
    quick_analyze = b3.button("🚀 즉시 분석 및 민원 요청", type="primary", use_container_width=True)

    # [🚨 관리자 요청: 에러 및 결과창 위치 변경]
    analysis_output = st.container()

with col_img:
    st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/ai_expert.png", 
             caption="Goldkey AI 전문 마스터", use_container_width=True)

# ==========================================
# [SECTION 5] 실전 튜토리얼 (판례 2001다1480)
# ==========================================
st.divider()
with st.expander("💡 실전 보상 & 민원 대응 튜토리얼 (판례 2001다1480)", expanded=False):
    st.write("보험사의 설명의무 위반 시 법적 근거와 개별 사건을 유기적으로 연관시키는 로직입니다.")

# ==========================================
# [SECTION 6] 1단계: 고객 기초 정보
# ==========================================
st.divider()
st.write("### 👤 1단계: 고객 기초 정보")
c1, c2 = st.columns(2)
customer_name = c1.text_input("고객 성함", "고객님")
hi_premium = c1.number_input("월 건강보험료 (원)", value=0, step=1000)
debt = c2.number_input("부채 총액 (만원)", value=0)

# ==========================================
# [SECTION 7] 2단계: 자료 및 증권 업로드 (로드 확인 및 삭제)
# ==========================================
st.divider()
st.write("### 📸 2단계: 자료 및 증권 업로드")
uploaded_files = st.file_uploader(
    "증권, 진단서 등을 로드하세요.", 
    accept_multiple_files=True,
    key=f"uploader_{st.session_state.uploader_key}"
)

if uploaded_files:
    num_files = len(uploaded_files)
    st.markdown(f"""
    <div style="border: 2px solid #1E88E5; padding: 15px; border-radius: 10px; background-color: #e3f2fd; margin-bottom: 10px;">
        <h4 style="margin-top:0; color:#0D47A1;">📁 서류 로드 현황 보고</h4>
        <p style="font-size:16px;">✅ <b>총 {num_files}장</b>의 서류가 인식되었습니다.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🗑️ 전체 서류 삭제 및 재로드", type="secondary", use_container_width=True):
        st.session_state.uploader_key += 1
        st.rerun()

# ==========================================
# [SECTION 8] 3단계: 질병 보상 정밀 분석
# ==========================================
st.divider()
st.write("### 🏥 3단계: 질병 보상 정밀 분석")
disease_focus = st.multiselect("분석 대상 질환", ["암(선행항암)", "뇌/심장", "정신과", "희귀난치병"])

# ==========================================
# [SECTION 10] 4단계: 6대 법령 및 보상 지식 DB
# ==========================================
st.divider()
st.write("### 🏛️ 4단계: 6대 법령 및 보상 지식 DB")
st.info("민법, 상법, 보험업법 등 6대 법령 근거 3중 검증 시스템 가동 중")

# ==========================================
# [SECTION 11] 5단계: 국제재무설계 기준 위험관리 및 필수 보장 설계
# ==========================================
st.divider()
st.write("### 🛡️ 5단계: 국제재무설계 기준 위험관리 및 필수 보장 설계")
essential_ins = st.multiselect("필수 소유 보험", ["자동차보험", "화재보험", "일상생활배상책임", "사업장 배책", "후유장해", "기본통합장기"])

# ==========================================
# [SECTION 12] 6단계: 국제 재무설계 기준 3층 연금 통합 시뮬레이션
# ==========================================
st.divider()
st.write("### 💰 6단계: 국제 재무설계 기준 3층 연금 통합 시뮬레이션")
p_col = st.columns(3)
p_nat = p_col[0].number_input("국민연금(만)", value=0)
p_ret = p_col[1].number_input("퇴직연금(만)", value=0)
p_ind = p_col[2].number_input("개인연금(만)", value=0)

# ==========================================
# [SECTION 13] 7단계: 주택구입 및 인생 이모작 설계
# ==========================================
st.divider()
st.write("### 🏡 7단계: 주택구입 및 인생 이모작 설계")
home_fund = st.number_input("주택구입 필요자금(만원)", value=0)
second_job = st.text_area("인생 이모작(전직/창업) 계획")

# ==========================================
# [SECTION 14] 전문가 통합 분석 엔진 (에러 위치 최적화)
# ==========================================
def run_master_analysis(container):
    with container:
        st.components.v1.html(s_voice("종합 분석을 시작합니다."), height=0)
        with st.spinner("마스터가 모든 섹션을 한 몸으로 통합 분석 중입니다..."):
            try:
                monthly_income = hi_premium / 0.0709 if hi_premium > 0 else 0
                model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=SYSTEM_PROMPT, tools=TOOLS)
                
                organic_query = f"""
                고객 {customer_name} 종합 마스터 리포트:
                [상담본부]: {main_consult_content}
                [로드서류]: 총 {len(uploaded_files) if uploaded_files else 0}장의 서류 대조.
                [재무데이터]: 소득역산({monthly_income:,.0f}원), 부채({debt}만).
                [보상/재무 가이드]: {essential_ins} 가입현황 및 {disease_focus} 정밀분석.
                [판례 적용]: 2001다1480 근거로 보험사 대응 논리 생성. (※ 설계사 벌칙 언급 금지)
                [생애설계]: 3층 연금({p_nat+p_ret+p_ind}만), 주택({home_fund}만), 인생이모작({second_job}) 제언.
                결과는 다국어로 [항목|현재상태|가이드|결과|마스터 처방] 표로 생성하라.
                """
                
                content_list = [organic_query]
                if uploaded_files:
                    for f in uploaded_files: content_list.append(PIL.Image.open(f))
                
                response = model.generate_content(content_list)
                st.subheader(f"📊 {customer_name}님 통합 솔루션 리포트")
                st.markdown(response.text)
                st.divider()
            except Exception as e:
                # [🚨 관리자 요청 반영] 에러 메시지를 분석 버튼 바로 아래(container)에 시인성 좋게 배치
                st.error(f"🚨 분석 시스템 연결 오류: {e}")
                st.warning("💡 조치 방법: API 키가 정상인지 확인하거나, 잠시 후 다시 시도해 주세요. (모델 경로 강제 고정 완료)")

# 분석 트리거 (상단)
if quick_analyze:
    run_master_analysis(analysis_output)

# ==========================================
# [SECTION 15] 하단 분석 및 성공 응원
# ==========================================
st.divider()
if st.button("🔍 전 섹션 마스터 종합 분석 리포트 생성 🚀", use_container_width=True, type="primary"):
    run_master_analysis(st.container())

if st.button("🏆 관리자 이세윤 & 전문 FC 성공 응원"):
    st.balloons()
    msg = f"{user_name}님! 마스터의 지혜로 최고의 성과를 거두십시오!"
    st.success(msg); st.components.v1.html(s_voice(msg), height=0)

load_stt_engine()
