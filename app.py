# ==========================================================================
# 🚨 [운영 헌법 - 관리자 이세윤 지침 엄수]
# 1. 섹션 통합 절대 금지: 모든 섹션은 번호별로 독립된 코드 블록을 유지한다.
# 2. 수정/삭제 제한: 관리자 '이세윤'의 답변 없이 본 구조를 변경하지 않는다.
# 3. 다국어 응대: 모든 분석 및 리포트는 입력 언어에 맞춰 글로벌로 출력한다.
# 4. CFP® 설계: 위험관리, 난치병, 연금, 주택, 인생 이모작을 6단계 프로세스로 구동한다.
# 5. 핵심 연산: 건보료 ÷ 0.0709 소득역산 / 암 합산 금지 / 구글 실시간 검색 상시 가동.
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
# [SECTION 1] 설정 및 페르소나 (글로벌 CFP 마스터)
# ==========================================
st.set_page_config(page_title="골드키지사 AI 마스터", page_icon="👑", layout="wide")

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

MODEL_NAME = 'gemini-1.5-flash-latest'
TOOLS = [{'google_search_retrieval': {}}] # 실시간 구글 검색 활성화

# [🚨 관리자 이세윤 지정: 무손실 통합 페르소나 강령]
SYSTEM_PROMPT = """
성명: 글로벌 보험/재무/인생설계 통합 전문가 (관리자: 이세윤)
지능 기반: AI Studio의 '보험비서_최종' + '보험상담 봇' + CFP® 국제표준 지능이 통합된 고성능 엔진.

[검색 강령]: 
최신 법령, 약관 개정, 판례 확인을 위해 반드시 구글 실시간 검색(Grounding) 결과를 대조하여 답변하라.

[분석 철학 - 6대 법령 3중 검증]:
민법, 상법, 보험업법, 형사소송법, 화재법, 실화법에 근거하여 모든 보상 및 재무 상담을 3중 검증하라.

[핵심 컨설팅 규칙]:
1. 데이터 대조: 입력 텍스트와 증권 파일을 동시에 대조하여 보상 누락을 정밀 분석하라.
2. 암 담보 분류: 일반암 진단비를 기준으로 유사암, 소액암, 재진단암을 엄격히 분류하라 (무조건 합산 금지).
3. 12대 핵심 담보 분석: 암, 뇌질환, 심장질환, 후유장해, 입원일당, 수술비, 간병비, 운전자(비용담보), 화재, 배상책임, 연금, 상해담보를 전수 분석하라.
4. 소득 역산(0.0709): 건보료 ÷ 0.0709 로직으로 월소득을 계산하여 라이프 사이클(Life Cycle)에 맞는 보장 크기를 제안하라.
5. 리포트 형식: 반드시 [항목 | 가입금액 합산 | 가이드라인 | 과·부족 결과 | 마스터 처방] 표 형태를 유지하라.

[CFP® 전문 재무설계 확장 규칙]:
- 필수보험 설계: 자동차, 화재(주택/공장), 일배책, 사업장 배책, 후유장해 중심 위험관리.
- 3층 연금 설계: 국민/퇴직/개인연금 통합 및 미래 가치/부족액(Gap) 시뮬레이션.
- 생애 설계: 주택구입 자금 마련 및 '인생 이모작(전직/창업)' 직업 인생 설계 조언.
- 다국어 응대: 고객의 입력 언어에 맞춰 글로벌 수준의 전문 용어를 사용하여 리포트를 생성하라.
"""

# ==========================================
# [SECTION 2] 음성 엔진 및 STT (다국어 지원)
# ==========================================
def s_voice(text, lang='ko-KR'):
    if re.search('[a-zA-Z]{5,}', text): lang = 'en-US'
    return f"""<script>
        window.speechSynthesis.cancel(); 
        var msg = new SpeechSynthesisUtterance("{text}");
        msg.lang = "{lang}"; msg.rate = 0.95; 
        window.speechSynthesis.speak(msg);
    </script>"""

def goodbye_sequence():
    return """<script>
        var context = new (window.AudioContext || window.webkitAudioContext)();
        var osc = context.createOscillator(); osc.type = 'sine'; 
        osc.frequency.setValueAtTime(523.25, context.currentTime); 
        osc.connect(context.destination); osc.start(); osc.stop(context.currentTime + 0.3);
        window.speechSynthesis.cancel(); 
        var msg = new SpeechSynthesisUtterance("관리자 지침에 따라 모든 상담 데이터를 안전하게 파기했습니다.");
        msg.lang = 'ko-KR'; window.speechSynthesis.speak(msg);
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
                var textArea = window.parent.document.querySelector('textarea');
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
# [SECTION 3] 사이드바 (사용자 센터 & 보안)
# ==========================================
with st.sidebar:
    st.header("🔑 사용자 센터")
    user_name = st.text_input("상담원 성함", "전문 FC")
    st.divider()
    st.info("👤 **관리자: 이세윤**")
    st.success("🌐 **다국어/CFP® 시스템 가동**")
    with st.expander("🌐 API 발급 및 보안 가이드", expanded=False):
        st.markdown('<a href="https://aistudio.google.com/app/apikey" target="_blank">🌐 API 키 발급</a>', unsafe_allow_html=True)
    if st.button("❌ 보안 종료 및 데이터 파기", use_container_width=True):
        st.components.v1.html(goodbye_sequence(), height=0)
        st.cache_data.clear(); st.session_state.clear(); time.sleep(2); st.rerun()
    st.divider()
    st.caption(f"🕒 최종 업데이트: {dt.now().strftime('%Y-%m-%d %H:%M')}")

# ==========================================
# [SECTION 4] 브랜드 상단 UI
# ==========================================
st.markdown("""
<div style="background-color:#f0f2f6; padding:20px; border-radius:10px; border-left:5px solid #1E88E5; margin-bottom:20px;">
    <h3 style="margin-top:0; color:#0D47A1;">"Life Design Master with CFP® Standards"</h3>
    <p style="font-size:16px; color:#424242;">
       보험 보장부터 주택, 연금, 인생 이모작까지 - <b>글로벌 다국어 및 실시간 검색</b> 서비스를 제공합니다.
    </p>
</div>
""", unsafe_allow_html=True)

st.title("👑 골드키지사 AI 마스터")

# ==========================================
# [SECTION 5] 실전 튜토리얼
# ==========================================
with st.expander("💡 실전 보상 & 민원 대응 튜토리얼 (판례 2001다1480)", expanded=False):
    st.write("부당 지급 거절 반박 및 후유증 추가 청구 전략 탑재.")

# ==========================================
# [SECTION 6] 1단계: 고객 기초 정보
# ==========================================
st.divider()
st.write("### 📝 1단계: 고객 기초 정보 입력")
st.markdown("<style>.stTextArea textarea:focus, .stFileUploader section:hover { border: 2px solid #1E88E5 !important; animation: pulse 1.5s infinite; } @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(30, 136, 229, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(30, 136, 229, 0); } 100% { box-shadow: 0 0 0 0 rgba(30, 136, 229, 0); } }</style>", unsafe_allow_html=True)
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
st.write("### 📸 2단계: 자료 및 증권 업로드")
uploaded_files = st.file_uploader("증권, 진단서, 재무자료 로드", accept_multiple_files=True)

# ==========================================
# [SECTION 8] 질병 보상 정밀 분석 (난치병/선행항암)
# ==========================================
st.divider()
st.write("### 🏥 3단계: 질병 보상 및 난치성 질환 분석")
with st.expander("선행항암치료 및 고액치료비 질병 설정", expanded=False):
    disease_focus = st.multiselect("집중 분석 질병", ["암(선행항암 포함)", "뇌/심장(중풍)", "정신과 질환", "희귀난치병", "자녀통합보험"])

# ==========================================
# [SECTION 9] 생보사 헬스케어 서비스 컨설팅
# ==========================================
st.divider()
st.write("### 💎 4단계: 삼성/교보 헬스케어 서비스 컨설팅")
healthcare_info = st.checkbox("삼성생명/교보생명 주력 상품 및 헬스케어 보장 대조 포함")

# ==========================================
# [SECTION 10] 법리 및 지식 DB
# ==========================================
st.divider()
with st.expander("🏛️ 6대 법령 및 보상 지식 DB", expanded=False):
    st.info("민법, 상법, 보험업법 등 6대 법령 근거 3중 검증 가동 중.")

# ==========================================
# [SECTION 11] CFP® 재무상담: 필수보험 설계 (위험관리)
# ==========================================
st.divider()
st.write("### 🛡️ 5단계: CFP® 위험관리 및 필수보험 설계")
with st.expander("소유/주요 활동기 필수 보험 체크", expanded=True):
    col_rm1, col_rm2 = st.columns(2)
    with col_rm1:
        essential_ins = st.multiselect("반드시 있어야 할 보험", ["자동차보험", "화재보험(주택/공장)", "일상생활배상책임", "사업장 화재/영업배상", "충분한 후유장해", "기본통합장기보험"])
    with col_rm2:
        life_stage = st.selectbox("Life Cycle 단계", ["사회초년생", "신혼기", "자녀양육기", "자녀교육기", "은퇴준비기"])

# ==========================================
# [SECTION 12] CFP® 재무상담: 3층 연금 통합 설계
# ==========================================
st.divider()
st.write("### 💰 6단계: CFP® 3층 연금 및 미래 가치 설계")
with st.expander("국민·퇴직·개인연금 통합 시뮬레이션", expanded=False):
    p1, p2, p3 = st.columns(3)
    p_nat = p1.number_input("국민연금(월/만)", value=0)
    p_ret = p2.number_input("퇴직연금(월/만)", value=0)
    p_ind = p3.number_input("개인연금(월/만)", value=0)
    p_qa = st.text_area("❓ 연금 관련 질문 (언어로직 답변용)")

# ==========================================
# [SECTION 13] CFP® 재무상담: 주택구입 & 인생 이모작
# ==========================================
st.divider()
st.write("### 🏡 7단계: 주택구입 설계 및 인생 이모작 직업 설계")
with st.expander("생애 주거 및 직업 인생 설계", expanded=False):
    home_fund = st.number_input("주택구입 필요자금(만원)", value=0)
    second_life = st.text_area("인생 이모작(전직/창업) 계획 및 재무 고민")

# ==========================================
# [SECTION 14] 전문가 통합 분석 실행 (유기적 동시 구동)
# ==========================================
st.divider()
if st.button("🔍 종합 마스터 컨설팅 실행 (Global & Real-time) 🚀", use_container_width=True, type="primary"):
    st.components.v1.html(s_voice("전 섹션 유기적 통합 분석을 시작합니다."), height=0)
    with st.spinner("CFP® 마스터가 구글 실시간 검색 결과를 대조 중입니다..."):
        try:
            monthly_income = hi_premium / 0.0709 if hi_premium > 0 else 0
            model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=SYSTEM_PROMPT, tools=TOOLS)
            
            full_analysis_query = f"""
            고객 {customer_name} 종합 마스터 리포트 요청:
            1. [보험/위험]: {life_stage} 단계 필수보험({essential_ins}) 가입 여부 및 {disease_focus} 보장 분석.
            2. [연금/재무]: 3층 연금({p_nat+p_ret+p_ind}만) 가치 분석 및 질문({p_qa}) 답변. 주택자금({home_fund}만) 대안.
            3. [인생]: 인생 이모작({second_life})에 대한 CFP® 기준 재무 조언.
            4. [헬스케어]: 삼성/교보 서비스 연계 방안({healthcare_info}).
            5. [소득역산]: 건보료 기반 추산소득({monthly_income:,.0f}원) 대조.
            모든 리포트는 고객의 입력 언어에 맞게 [항목|현재|가이드|과부족|처방] 표로 생성하라.
            """
            
            content_parts = [full_analysis_query]
            if uploaded_files:
                for f in uploaded_files: content_parts.append(PIL.Image.open(f))
            
            response = model.generate_content(content_parts)
            st.subheader(f"📊 {customer_name}님 종합 생애 설계 리포트")
            st.markdown(response.text)
        except Exception as e: st.error(f"🚨 분석 실패: {e}")

# ==========================================
# [SECTION 15] 성공 응원 및 보안
# ==========================================
st.divider()
if st.button("🎤 마이크 켜기"): load_stt_engine()
if st.button("🏆 관리자 이세윤 & 전문 FC 성공 응원"):
    st.balloons()
    msg = f"{user_name}님! CFP의 전문성과 마스터의 지능으로 성공을 거두십시오!"
    st.success(msg); st.components.v1.html(s_voice(msg), height=0)

st.error("**[법적 고지]** 본 리포트는 참고용입니다.")
load_stt_engine()
