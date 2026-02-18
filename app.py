# ==========================================================================
# 🚨 [운영 헌법 - 관리자 이세윤 지침 100% 준수]
# 1. 섹션 통합 절대 금지: 모든 섹션(7, 8, 9, 10 포함)은 독립된 번호와 영역을 유지한다.
# 2. 유기적 자동 연동: 분리된 각 섹션의 데이터는 최종 분석(Section 14) 시 자동 합산된다.
# 3. 수정/삭제 제한: 관리자 '이세윤'의 답변 없이 본 구조를 변경하지 않는다.
# 4. 핵심 지능: CFP® 표준 + 3층 연금 + 6대 법령 + 구글 실시간 검색(Grounding) 탑재.
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
# [SECTION 1] 설정 및 페르소나 (무손실 보존)
# ==========================================
st.set_page_config(page_title="골드키지사 AI 마스터", page_icon="👑", layout="wide")

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

MODEL_NAME = 'gemini-1.5-flash-latest'
TOOLS = [{'google_search_retrieval': {}}] 

SYSTEM_PROMPT = """
성명: 글로벌 보험/재무/분쟁대응 통합 전문가 (관리자: 이세윤)
지능 기반: '보험비서_최종' + '보험상담 봇' + 'CFP® 국제표준' + '금감원 분쟁대응' 통합 엔진.
[분석 강령]: 0.0709 소득 역산, 암 담보 합산 금지(일반암 기준 분류), 6대 법령 근거 3중 검증.
[운영 규칙]: 모든 리포트는 고객의 언어로 생성하며, 구글 검색 결과를 통해 실시간 팩트체크를 수행하라.
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
            var msg = new SpeechSynthesisUtterance("마스터가 듣고 있습니다. 말씀해 주세요.");
            msg.lang = 'ko-KR'; window.speechSynthesis.speak(msg);
            var recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
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
# [SECTION 3] 사이드바 (관리자 보안 및 로드)
# ==========================================
with st.sidebar:
    st.header("🔑 사용자 센터")
    user_name = st.text_input("상담원 성함", "전문 FC")
    st.divider()
    st.info("👤 **시스템 관리자: 이세윤**")
    st.success("🌐 **다국어/CFP® 시스템 가동**")
    if st.button("❌ 보안 종료 및 데이터 파기", use_container_width=True):
        st.cache_data.clear(); st.session_state.clear(); time.sleep(1); st.rerun()
    st.divider()
    st.caption(f"🕒 업데이트: {dt.now().strftime('%Y-%m-%d %H:%M')}")

# ==========================================
# [SECTION 4] 브랜드 상단 UI
# ==========================================
st.markdown("""
<div style="background-color:#f0f2f6; padding:20px; border-radius:10px; border-left:5px solid #1E88E5; margin-bottom:10px;">
    <h3 style="margin-top:0; color:#0D47A1;">"Life Design & Dispute Resolution Master"</h3>
    <p style="font-size:16px; color:#424242;">보험 가입부터 금감원 분쟁 대응까지 - 이세윤 관리자의 통합 지능 상담 시스템</p>
</div>
""", unsafe_allow_html=True)

st.title("👑 골드키지사 AI 마스터")

# ==========================================
# [SECTION 4.5] 마스터 통합 상담 센터 (2모드 전환형)
# ==========================================
st.divider()
st.subheader("📡 마스터 통합 상담 센터")
col_main_input, col_master_img = st.columns([7, 3])

with col_main_input:
    main_consult_content = st.text_area(
        "📝 마스터 통합 상담창 (내용 구현)", 
        placeholder="보험가입상담, LIFE CYCLE 플랜, 민원/분쟁상담 내용을 입력하거나 음성 버튼을 사용하세요.", 
        height=320,
        key="main_consult_area"
    )
    b_col1, b_col2, b_col3 = st.columns([2, 2, 6])
    with b_col1:
        if st.button("⌨️ 직접 입력", use_container_width=True): st.toast("직접 입력 모드")
    with b_col2:
        if st.button("🎤 음성 입력", use_container_width=True): load_stt_engine()

with col_master_img:
    st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/ai_expert.png", 
             caption="Goldkey AI 전문 마스터", use_container_width=True)

# ==========================================
# [SECTION 5] 실전 튜토리얼 (독립 분리)
# ==========================================
st.divider()
with st.expander("💡 실전 보상 & 민원 대응 튜토리얼", expanded=False):
    st.write("판례 2001다1480 기반 후유증 추가 청구 및 보험사 횡포 대응 전략.")

# ==========================================
# [SECTION 6] 1단계: 고객 기초 정보 (독립 분리)
# ==========================================
st.divider()
st.write("### 👤 1단계: 고객 기초 정보")
c_in1, c_in2 = st.columns(2)
with c_in1:
    customer_name = st.text_input("고객 성함", "고객님")
    hi_premium = st.number_input("월 건강보험료 (원)", value=0, step=1000)
with c_in2:
    debt = st.number_input("부채 총액 (만원)", value=0)

# ==========================================
# [SECTION 7] 2단계: 자료 및 증권 업로드 (독립 분리)
# ==========================================
st.divider()
st.write("### 📸 2단계: 자료 및 증권 업로드")
uploaded_files = st.file_uploader("이미지, PDF 등 분석 자료 로드", accept_multiple_files=True)

# ==========================================
# [SECTION 8] 3단계: 질병 보상 정밀 분석 (독립 분리)
# ==========================================
st.divider()
st.write("### 🏥 3단계: 질병 보상 정밀 분석 (암·뇌·심·정신·난치병)")
with st.expander("선행항암치료 및 고액 치료비 질병 분석 설정", expanded=False):
    disease_focus = st.multiselect("집중 분석 질병", ["암(선행항암 포함)", "뇌/심장(중풍)", "정신과 질환", "희귀난치병", "자녀통합보험"])

# ==========================================
# [SECTION 9] 4단계: 생보사 헬스케어 서비스 컨설팅 (독립 분리)
# ==========================================
st.divider()
st.write("### 💎 4단계: 삼성/교보 헬스케어 컨설팅")
with st.expander("생명보험사 주력 상품 및 서비스 대조", expanded=False):
    healthcare_info = st.checkbox("삼성생명/교보생명 주요 헬스케어 보장 안내 포함")

# ==========================================
# [SECTION 10] 5단계: 법리 및 지식 DB (독립 분리)
# ==========================================
st.divider()
st.write("### 🏛️ 5단계: 6대 법령 및 보상 지식 DB")
with st.expander("보상 근거 법령 및 판례 DB 확인", expanded=False):
    st.info("민법, 상법, 보험업법 등 6대 법령 근거 3중 검증 가동 중.")

# ==========================================
# [SECTION 11] CFP® 위험관리 & 필수 보험 (독립 분리)
# ==========================================
st.divider()
st.write("### 🛡️ 6단계: CFP® 위험관리 및 필수 보장 설계")
with st.expander("자동차, 화재, 일배책 등 필수 보험 체크", expanded=True):
    essential_ins = st.multiselect("소유 및 필수 항목", ["자동차보험", "화재보험(주택/공장)", "일상생활배상책임", "사업장 배책", "충분한 후유장해", "기본통합장기보험"])
    lc_stage = st.selectbox("Life Cycle 단계", ["사회초년생", "신혼기", "자녀양육기", "은퇴준비기"])

# ==========================================
# [SECTION 12] CFP® 3층 연금 통합 설계 (독립 분리)
# ==========================================
st.divider()
st.write("### 💰 7단계: CFP® 3층 연금 통합 시뮬레이션")
with st.expander("국민·퇴직·개인연금 합산 및 전문 답변", expanded=False):
    p_col1, p_col2, p_col3 = st.columns(3)
    p_nat = p_col1.number_input("국민연금(만)", value=0)
    p_ret = p_col2.number_input("퇴직연금(만)", value=0)
    p_ind = p_col3.number_input("개인연금(만)", value=0)
    p_qa = st.text_area("❓ 연금 전문 상담 질문 (세제/수령 등)")

# ==========================================
# [SECTION 13] CFP® 주택구입 & 인생 이모작 (독립 분리)
# ==========================================
st.divider()
st.write("### 🏡 8단계: 주택구입 & 인생 이모작 설계")
with st.expander("주택자금 및 은퇴 후 직업 인생 설계", expanded=False):
    home_fund = st.number_input("주택구입 필요자금(만원)", value=0)
    second_job = st.text_area("인생 이모작(전직/창업) 계획 및 고민")

# ==========================================
# [SECTION 14] 전문가 통합 분석 실행 (유기적 자동 연동)
# ==========================================
st.divider()
if st.button("🔍 전 섹션 마스터 통합 분석 시작 🚀", use_container_width=True, type="primary"):
    st.components.v1.html(s_voice("전 섹션 유기적 통합 분석을 시작합니다."), height=0)
    with st.spinner("관리자 이세윤의 지휘 하에 정밀 리포트를 작성 중입니다..."):
        try:
            monthly_income = hi_premium / 0.0709 if hi_premium > 0 else 0
            model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=SYSTEM_PROMPT, tools=TOOLS)
            
            full_query = f"""
            고객 {customer_name} 종합 마스터 리포트 요청:
            [상담요청]: {main_consult_content}
            [보장분석]: {essential_ins} 가입여부 및 {disease_focus} 난치병 분석.
            [연금설계]: 3층 연금({p_nat+p_ret+p_ind}만) 분석 및 질문({p_qa}) 답변.
            [생애설계]: 주택자금({home_fund}만) 및 인생이모작({second_job}) 제언.
            [재무분석]: 소득역산({monthly_income:,.0f}원) 및 6대 법령 근거 분석.
            결과는 다국어로 [항목|현재|가이드|과부족|처방] 표로 생성하라.
            """
            
            response = model.generate_content([full_query] + ([PIL.Image.open(f) for f in uploaded_files] if uploaded_files else []))
            st.subheader(f"📊 {customer_name}님 종합 생애 설계 리포트")
            st.markdown(response.text)
        except Exception as e: st.error(f"🚨 분석 실패: {e}")

# ==========================================
# [SECTION 15] 성공 응원 및 보안
# ==========================================
st.divider()
if st.button("🏆 관리자 이세윤 & 전문 FC 성공 응원"):
    st.balloons()
    msg = f"{user_name}님! 마스터의 지능과 CFP의 전문성으로 성공을 거두십시오!"
    st.success(msg); st.components.v1.html(s_voice(msg), height=0)

load_stt_engine()
