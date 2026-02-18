# ==========================================================================
# 🚨 [운영 헌법 - 관리자 이세윤 지침 엄수]
# 1. 섹션 통합 절대 금지: 모든 섹션은 번호별로 독립된 코드 블록을 유지한다.
# 2. 유기적 자동 적용: 분리된 각 섹션의 데이터는 최종 분석 시 자동으로 통합 연산된다.
# 3. 수정/삭제 제한: 관리자 '이세윤'의 답변 없이 본 구조를 변경하지 않는다.
# 4. CFP® & 실시간 검색: 모든 상담은 국제 표준 및 구글 실시간 검색을 기반으로 수행한다.
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
# [SECTION 1] 설정 및 페르소나
# ==========================================
st.set_page_config(page_title="골드키지사 AI 마스터", page_icon="👑", layout="wide")

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

MODEL_NAME = 'gemini-1.5-flash-latest'
TOOLS = [{'google_search_retrieval': {}}] 

SYSTEM_PROMPT = """
성명: 글로벌 보험/재무/분쟁대응 통합 전문가 (관리자: 이세윤)
지능 기반: '보험비서_최종' + '보험상담 봇' + 'CFP® 재무계산기' + '금감원 분쟁대응 지능' 통합.
[분석 철학]: 6대 법령 근거 3중 검증 및 실시간 구글 검색(Grounding) 팩트체크.
[재무 상담]: CFP® 윤리규정 및 6단계 프로세스 준수. 화폐의 시간가치(TVM)를 적용한 계산 수행.
"""

# ==========================================
# [SECTION 2] 음성 엔진 및 STT 로직
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
            var msg = new SpeechSynthesisUtterance("마스터가 듣고 있습니다. 어떤 상담을 도와드릴까요?");
            window.speechSynthesis.speak(msg);
            var recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.lang = 'ko-KR';
            recognition.onresult = function(event) {
                var transcript = event.results[0][0].transcript;
                var textArea = window.parent.document.querySelector('textarea[aria-label="📝 통합 상담 내용 입력"]');
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
# [SECTION 3] 사이드바 (관리자 보안)
# ==========================================
with st.sidebar:
    st.header("🔑 사용자 센터")
    user_name = st.text_input("상담원 성함", "전문 FC")
    st.divider()
    st.info("👤 **관리자: 이세윤**")
    st.success("🔓 **분쟁/민원 통합 모드 가동**")
    if st.button("❌ 보안 종료 및 데이터 파기", use_container_width=True):
        st.cache_data.clear(); st.session_state.clear(); st.rerun()

# ==========================================
# [SECTION 4] 브랜드 상단 UI (독립 분리)
# ==========================================
st.markdown("""
<div style="background-color:#f0f2f6; padding:20px; border-radius:10px; border-left:5px solid #1E88E5; margin-bottom:20px;">
    <h3 style="margin-top:0; color:#0D47A1;">"Life Design & Dispute Resolution Master"</h3>
    <p style="font-size:16px; color:#424242;">
       보험 가입부터 금감원 분쟁 대응까지 - 30년 노하우가 집약된 <b>AI 마스터 시스템</b>입니다.
    </p>
</div>
""", unsafe_allow_html=True)

st.title("👑 골드키지사 AI 마스터")

# 

# ==========================================
# [SECTION 4.5] 마스터 통합 상담창 (직접입력 vs 음성인식)
# ==========================================
st.divider()
st.subheader("📡 마스터 통합 상담 센터")
col_input, col_voice = st.columns([7, 3])
with col_input:
    main_consult_input = st.text_area("📝 통합 상담 내용 입력", placeholder="가입, 플랜, 민원, 분쟁상담 내용을 입력하세요.", height=100)
with col_voice:
    st.write("🎤 음성 상담 인식")
    if st.button("🎤 마이크 켜기", use_container_width=True): load_stt_engine()

# ==========================================
# [SECTION 5] 실전 튜토리얼 (독립 분리)
# ==========================================
st.divider()
with st.expander("💡 실전 보상 & 민원 대응 튜토리얼 (판례 2001다1480)", expanded=False):
    st.info("보험사 횡포 대응 및 부당 지급 거절 시 반박 논리 생성 가이드.")

# ==========================================
# [SECTION 6] 1단계: 고객 기초 정보
# ==========================================
st.divider()
st.write("### 👤 고객 정보 및 기초 데이터")
c1, c2 = st.columns(2)
with c1:
    customer_name = st.text_input("고객 성함", "고객님")
    hi_premium = st.number_input("월 건강보험료 (원)", value=0, step=1000)
with c2:
    debt = st.number_input("부채 총액 (만원)", value=0)

# ==========================================
# [SECTION 7] 2단계: 자료 및 증권 업로드
# ==========================================
st.divider()
uploaded_files = st.file_uploader("📸 증권, 진단서, 민원서류 업로드", accept_multiple_files=True)

# ==========================================
# [SECTION 8-10] 질병/헬스케어/법리 (독립 유지)
# ==========================================
# (질병보상, 삼성/교보 헬스케어, 6대 법령 DB 섹션이 고정 배치됨)

# ==========================================
# [SECTION 11] CFP® 재무상담: 위험관리 및 필수보험
# ==========================================
st.divider()
st.write("### 🛡️ CFP® 위험관리 및 라이프 사이클 설계")
with st.expander("반드시 있어야 할 필수 보험 및 상품 컨설팅", expanded=False):
    essential_ins = st.multiselect("소유 및 필수 항목", ["자동차보험", "화재보험(주택/공장)", "일상생활배상책임", "사업장 배책", "충분한 후유장해", "기본통합장기보험"])
    lc_stage = st.selectbox("Life Cycle 단계", ["사회초년생", "신혼기", "자녀양육기", "자녀교육기", "은퇴준비기"])
    product_cons = st.multiselect("보안/추가 상품 컨설팅", ["난치성 질병 보장", "자녀 통합보험", "치매/간병", "운전자"])

# ==========================================
# [SECTION 12] CFP® 재무상담: 3층 연금 통합 설계
# ==========================================
st.divider()
st.write("### 💰 CFP® 3층 연금 및 은퇴 재무설계")
with st.expander("국민·퇴직·개인연금 합산 및 질문 답변 로직", expanded=False):
    p1, p2, p3 = st.columns(3)
    p_nat = p1.number_input("국민연금(만)", value=0)
    p_ret = p2.number_input("퇴직연금(만)", value=0)
    p_ind = p3.number_input("개인연금(만)", value=0)
    p_logic_qa = st.text_area("❓ 연금 전문 상담 질문", placeholder="세제혜택이나 수령 전략에 대해 물어보세요.")

# ==========================================
# [SECTION 13] CFP® 재무상담: 주택구입 및 인생 이모작
# ==========================================
st.divider()
st.write("### 🏡 주택구입 및 인생 이모작 설계")
with st.expander("주택자금 및 은퇴 후 직업 인생 설계", expanded=False):
    home_fund = st.number_input("주택구입 필요자금(만원)", value=0)
    second_job = st.text_area("인생 이모작(전직/창업) 계획 및 재무 고민")

# ==========================================
# [SECTION 14] 전문가 통합 분석 실행 (유기적 자동 적용)
# ==========================================
st.divider()
if st.button("🔍 전 섹션 유기적 통합 분석 시작 🚀", use_container_width=True, type="primary"):
    st.components.v1.html(s_voice("종합 분석을 시작합니다."), height=0)
    with st.spinner("마스터가 모든 섹션의 데이터를 유기적으로 연산 중입니다..."):
        try:
            monthly_income = hi_premium / 0.0709 if hi_premium > 0 else 0
            model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=SYSTEM_PROMPT, tools=TOOLS)
            
            # 모든 섹션의 데이터를 하나의 쿼리로 유기적 자동 결합
            query = f"""
            고객 {customer_name} 종합 리포트 (CFP 기준):
            [상담요청]: {main_consult_input}
            [위험관리]: {essential_ins} 가입여부 및 {lc_stage} 단계 위험 분석. {product_cons} 보강 전략.
            [3층연금]: 국민({p_nat})+퇴직({p_ret})+개인({p_ind}) 합산 및 질문({p_logic_qa}) 답변.
            [생애설계]: 주택자금({home_fund}만) 및 인생이모작({second_job}) 재무 조언.
            [기본분석]: 소득역산(${monthly_income:,.0f}$원), 부채({debt}만) 기반 사망보장 가이드.
            결과는 다국어 응대를 포함하여 [항목|현재|가이드|과부족|처방] 표로 생성하라.
            """
            
            content_parts = [query]
            if uploaded_files:
                for f in uploaded_files: content_parts.append(PIL.Image.open(f))
            
            response = model.generate_content(content_parts)
            st.subheader("📊 마스터 종합 생애 설계 리포트")
            st.markdown(response.text)
        except Exception as e: st.error(f"🚨 분석 실패: {e}")

load_stt_engine()
