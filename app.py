# ==========================================================================
# 🚨 [운영 헌법 - 이세윤 관리자 지침 100% 준수]
# 1. 브랜딩: "보험 가입 상담 부터 보험금 분쟁 대응까지- 보험 AI전문 마스터 통합 시스템"
# 2. 사이드바: 회원 혜택 및 API 가이드 상시 노출 (접힘 금지)
# 3. 섹션 분리: 1~15번까지 모든 섹션은 물리적 구분선으로 완전 독립한다.
# 4. 통합 상담창: 대형 창(height=320) + 직접/음성 2모드 전환형 버튼 + 마스터 이미지 배치.
# 5. 유기적 구동: 각 섹션은 분리되어 있으나 분석 시 데이터가 신경망처럼 한 몸으로 연산된다.
# 6. 핵심 지능: 건보료 ÷ 0.0709 역산 / 암 합산 금지 / CFP® 6단계 / 6대 법령 검증.
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
# [SECTION 1] 설정 및 페르소나 (관리자 이세윤 강령)
# ==========================================
st.set_page_config(page_title="골드키지사 AI 마스터", page_icon="👑", layout="wide")

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

MODEL_NAME = 'gemini-1.5-flash-latest'
TOOLS = [{'google_search_retrieval': {}}] 

SYSTEM_PROMPT = """
성명: 글로벌 보험/재무/분쟁대응 통합 전문가 (관리자: 이세윤)
지능 기반: '보험비서_최종' + '보험상담 봇' + 'CFP® 국제표준' + '금감원 분쟁대응' 통합 엔진.

[유기적 구동 지표]:
입력된 상담창 내용, 소득, 부채, 필수보험 가입현황, 3층 연금, 주택 및 인생 이모작 데이터를 '한 사람의 인생'으로 통합하여 분석하라.

[핵심 분석 철학]:
1. 보상 검증: 6대 법령(민법, 상법, 보험업법, 형사소송법, 화재법, 실화법) 근거 3중 검증.
2. 암 분류: 일반암 기준 엄격 분류 (유사/소액/재진단암 합산 절대 금지).
3. 소득 역산: 건보료 기반 월소득 역산 로직 적용 ($Income = Premium / 0.0709$).
4. CFP® 표준: 화폐의 시간가치(TVM)를 적용한 NPV, IRR, FV 연산 수행.
5. 실시간 검색: 구글 검색(Grounding)을 통해 최신 판례와 약관을 팩트체크하라.
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
# [SECTION 3] 사이드바 (혜택 및 튜토리얼 상시 노출)
# ==========================================
with st.sidebar:
    st.header("🔑 사용자 센터")
    user_name = st.text_input("상담원 성함", "전문 FC")
    st.divider()
    
    st.info("👤 **시스템 관리자: 이세윤**")
    
    st.markdown("### 🏆 회원 등록 및 수용 혜택")
    st.success("""
    - **API 혜택**: 1일 50건 미만 상담 시 **8년간 무료**
    - **무제한 모드**: 현재 관리자 권한으로 승인됨
    - **보안**: 종료 시 모든 상담 데이터 즉시 파기
    """)
    
    st.markdown("---")
    st.warning("**[API 키 발급 튜토리얼]**")
    st.markdown("""
    1. **구글 로그인**: Gmail 계정 필요
    2. **카드 등록**: 형식적 절차(결제 미발생)
    3. **키 생성**: API Key 발급 후 앱 연동
    """)
    st.markdown('<a href="https://aistudio.google.com/app/apikey" target="_blank"><button style="width:100%; cursor:pointer; background:#1E88E5; color:white; border:none; padding:10px; border-radius:5px; font-weight:bold;">🌐 API 키 발급 (새 창)</button></a>', unsafe_allow_html=True)

    st.divider()
    if st.button("❌ 보안 종료 및 데이터 파기", use_container_width=True):
        st.cache_data.clear(); st.session_state.clear(); time.sleep(1); st.rerun()
    
    st.caption(f"🕒 최종 업데이트: {dt.now().strftime('%Y-%m-%d %H:%M')}")

# ==========================================
# [SECTION 4] 브랜드 상단 UI
# ==========================================
st.markdown("""
<div style="background-color:#f0f2f6; padding:20px; border-radius:10px; border-left:5px solid #1E88E5; margin-bottom:10px;">
    <h3 style="margin-top:0; color:#0D47A1;">"보험 가입 상담 부터 보험금 분쟁 대응까지"</h3>
    <p style="font-size:16px; color:#424242;"><b>보험 AI전문 마스터 통합 시스템</b> (관리자: 이세윤)</p>
</div>
""", unsafe_allow_html=True)

st.title("👑 골드키지사 AI 마스터")

# ==========================================
# [SECTION 4.5] 마스터 통합 상담 센터 (신경망 본체)
# ==========================================
st.divider()
st.subheader("📡 마스터 통합 상담 센터")
col_main_input, col_master_img = st.columns([7, 3])

with col_main_input:
    # 대형 상담 구현창 (마스터 이미지와 높이 일치)
    main_consult_content = st.text_area(
        "📝 마스터 통합 상담창 (내용 구현)", 
        placeholder="상담 내용을 입력하거나 음성 버튼을 사용하세요. 가입, 플랜, 분쟁 등 모든 상담을 통합합니다.", 
        height=320,
        key="main_consult_area"
    )
    # 물리적 2버튼 전환
    b_col1, b_col2, b_col3 = st.columns([2, 2, 6])
    if b_col1.button("⌨️ 직접 입력", use_container_width=True): st.toast("직접 입력 모드 활성화")
    if b_col2.button("🎤 음성 입력", use_container_width=True): load_stt_engine(); st.toast("음성 인식 활성화")

with col_master_img:
    st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/ai_expert.png", 
             caption="Goldkey AI 전문 마스터", use_container_width=True)

# ==========================================
# [SECTION 5] 실전 튜토리얼 (판례/민원)
# ==========================================
st.divider()
with st.expander("💡 실전 보상 & 민원 대응 튜토리얼 (판례 2001다1480)", expanded=False):
    st.write("부당 지급 거절 반박 및 금감원 분쟁 심의 전략 리포트 가이드.")

# ==========================================
# [SECTION 6] 1단계: 고객 기초 정보
# ==========================================
st.divider()
st.write("### 👤 1단계: 고객 기초 정보")
c_in1, c_in2 = st.columns(2)
customer_name = c_in1.text_input("고객 성함", "고객님")
hi_premium = c_in1.number_input("월 건강보험료 (원)", value=0, step=1000)
debt = c_in2.number_input("부채 총액 (만원)", value=0)
uploaded_files = c_in2.file_uploader("📸 증권, 진단서, 민원서류 로드", accept_multiple_files=True)

# ==========================================
# [SECTION 7-10] 질병 / 헬스케어 / 법리 DB (각각 독립 배치)
# ==========================================
st.divider()
st.write("### 🏥 질병 보상 및 생보사 헬스케어 분석")
disease_focus = st.multiselect("분석 대상 질환", ["암(선행항암 포함)", "뇌/심장(중풍)", "정신과", "희귀난치병"])
hc_service = st.checkbox("삼성생명/교보생명 주요 헬스케어 서비스 안내 포함")
st.info("🏛️ 6대 법령 근거 3중 검증 및 실시간 구글 검색 지능 상시 가동")

# ==========================================
# [SECTION 11] CFP® 위험관리 및 필수 보험
# ==========================================
st.divider()
st.write("### 🛡️ 2단계: CFP® 위험관리 및 필수 보장 설계")

essential_ins = st.multiselect("반드시 있어야 할 보험", ["자동차보험", "화재보험(주택/공장)", "일상생활배상책임", "사업장 배책", "후유장해", "기본통합장기"])
lc_stage = st.selectbox("현재 Life Cycle", ["사회초년생", "가족형성기", "자녀양육기", "자녀교육기", "은퇴준비기"])

# ==========================================
# [SECTION 12] CFP® 3층 연금 통합 설계
# ==========================================
st.divider()
st.write("### 💰 3단계: CFP® 3층 연금 통합 시뮬레이션")

p_nat = st.number_input("국민연금(만)", value=0)
p_ret = st.number_input("퇴직연금(만)", value=0)
p_ind = st.number_input("개인연금(만)", value=0)
p_qa = st.text_area("❓ 연금 전문 상담 질문 (세제/수령 전략 등)")

# ==========================================
# [SECTION 13] CFP® 주택구입 & 인생 이모작
# ==========================================
st.divider()
st.write("### 🏡 4단계: 주택구입 및 인생 이모작 설계")

home_fund = st.number_input("주택구입 필요자금(만원)", value=0)
second_job = st.text_area("인생 이모작(전직/창업) 계획 및 재무 고민")

# ==========================================
# [SECTION 14] 전문가 통합 분석 실행 (유기적 한 몸 구동)
# ==========================================
st.divider()
if st.button("🔍 전 섹션 마스터 통합 분석 시작 🚀", use_container_width=True, type="primary"):
    st.components.v1.html(s_voice("전 섹션 유기적 통합 분석을 시작합니다."), height=0)
    with st.spinner("관리자 이세윤의 지휘 하에 전 섹션을 신경망으로 연결 중입니다..."):
        try:
            # 0.0709 소득 역산 로직
            monthly_income = hi_premium / 0.0709 if hi_premium > 0 else 0
            model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=SYSTEM_PROMPT, tools=TOOLS)
            
            # 모든 섹션 변수를 유기적으로 결합한 최종 쿼리
            organic_query = f"""
            고객 {customer_name} 종합 마스터 리포트 (유기적 한 몸 모드):
            
            [상담본부]: {main_consult_content}
            [재무지표]: 소득역산({monthly_income:,.0f}원), 부채({debt}만).
            [위험관리]: {lc_stage} 단계 필수보험({essential_ins}) 및 {disease_focus} 분석.
            [3층연금]: 국({p_nat})+퇴({p_ret})+개({p_ind}) 합산 및 질문({p_qa}) 답변.
            [생애설계]: 주택자금({home_fund}만) 및 인생이모작({second_job}) 제언.
            [서비스]: 삼성/교보 헬스케어({hc_service}) 연계 전략.
            
            결과는 다국어로 [항목|현재상태|가이드|결과|마스터 처방] 표로 생성하라.
            """
            
            response = model.generate_content([organic_query] + ([PIL.Image.open(f) for f in uploaded_files] if uploaded_files else []))
            st.subheader(f"📊 {customer_name}님 종합 생애 설계 리포트")
            st.markdown(response.text)
        except Exception as e: st.error(f"🚨 분석 실패: {e}")

# ==========================================
# [SECTION 15] 성공 응원 및 보안
# ==========================================
st.divider()
if st.button("🏆 관리자 이세윤 & 전문 FC 성공 응원"):
    st.balloons()
    msg = f"{user_name}님! 마스터의 지휘와 CFP의 전문성으로 필승하십시오!"
    st.success(msg); st.components.v1.html(s_voice(msg), height=0)

load_stt_engine()
