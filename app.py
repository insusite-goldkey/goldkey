# ==========================================================================
# 🚨 [운영 헌법 - 관리자 이세윤 지침 100% 준수]
# 1. 섹션 통합 절대 금지: 모든 섹션은 독립된 번호와 고유 영역을 유지한다.
# 2. 삭제 금지 규칙: 관리자의 승인 없는 코드 삭제는 불가능하며, 모든 기능은 누적 보존한다.
# 3. 사이드바 수호: 관리자 정보, 보안 파기, API 가이드, 업데이트 시각을 상시 노출한다.
# 4. 여성 마스터 배치: 전문가 그룹의 상징인 마스터 사진을 상담창 옆에 고정한다.
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
# [SECTION 1] 설정 및 페르소나 (CFP/분쟁/다국어)
# ==========================================
st.set_page_config(page_title="골드키지사 AI 마스터", page_icon="👑", layout="wide")

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

MODEL_NAME = 'gemini-1.5-flash-latest'
TOOLS = [{'google_search_retrieval': {}}] 

SYSTEM_PROMPT = """
성명: 글로벌 보험/재무/분쟁대응 통합 전문가 (관리자: 이세윤)
지능 기반: '보험비서_최종' + '보험상담 봇' + 'CFP® 재무계산기' + '금감원 분쟁대응 지능' 통합 엔진.
[운영 지침]: 고객의 언어로 응대하며, 실시간 구글 검색(Grounding)과 6대 법령을 기반으로 3중 검증하라.
[분석 강령]: 암 담보 합산 금지, 0.0709 소득 역산, CFP 6단계 프로세스 준수.
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
        var msg = new SpeechSynthesisUtterance("이세윤 관리자 지침에 따라 모든 데이터를 안전하게 파기했습니다.");
        msg.lang = 'ko-KR'; window.speechSynthesis.speak(msg);
    </script>"""

def load_stt_engine():
    st.components.v1.html("""
    <script>
        window.startRecognition = function() {
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance("마스터가 듣고 있습니다. 어떤 상담을 도와드릴까요?");
            msg.lang = 'ko-KR'; window.speechSynthesis.speak(msg);
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
# [SECTION 3] 사이드바 (삭제 내용 완전 복원)
# ==========================================
with st.sidebar:
    st.header("🔑 사용자 센터")
    user_name = st.text_input("상담원 성함", "전문 FC")
    st.divider()
    st.info("👤 **시스템 관리자: 이세윤**")
    st.success("🌐 **다국어/CFP®/실시간검색 가동**")
    
    with st.expander("👤 API 발급 및 보안 설정 (필독)", expanded=False):
        st.info("🔑 API 키는 1일 50건 미만 시 8년간 무료입니다.")
        st.markdown('<a href="https://aistudio.google.com/app/apikey" target="_blank">🌐 구글 API 키 발급받기</a>', unsafe_allow_html=True)
    
    st.divider()
    current_date = dt.now().date()
    expiry_date = datetime.date(2026, 4, 30)
    if current_date <= expiry_date:
        st.success(f"🔓 무제한 승인 모드 (~{expiry_date})")
    
    if st.button("❌ 보안 종료 및 데이터 즉시 파기", use_container_width=True):
        st.components.v1.html(goodbye_sequence(), height=0)
        st.cache_data.clear(); st.session_state.clear(); time.sleep(2); st.rerun()

    st.divider()
    st.caption(f"🕒 최종 업데이트: {dt.now().strftime('%Y-%m-%d %H:%M')}")
    st.caption("© 2026 Goldkey AI Master")

# ==========================================
# [SECTION 4] 브랜드 상단 UI
# ==========================================
st.markdown("""
<div style="background-color:#f0f2f6; padding:20px; border-radius:10px; border-left:5px solid #1E88E5; margin-bottom:20px;">
    <h3 style="margin-top:0; color:#0D47A1;">"Life Design & Dispute Resolution Master"</h3>
    <p style="font-size:16px; color:#424242;">
       30년 현장 노하우가 집약된 <b>이세윤 관리자의 통합 지능 시스템</b>입니다.
    </p>
</div>
""", unsafe_allow_html=True)

st.title("👑 골드키지사 AI 마스터")

# ==========================================
# [SECTION 4.5] 통합 상담창 & 여성 마스터 사진 (위치 고정)
# ==========================================
st.divider()
st.subheader("📡 마스터 통합 상담 센터")
col_input, col_master_img = st.columns([7, 3])

with col_input:
    # 직접 입력 창
    main_consult_input = st.text_area(
        "📝 통합 상담 내용 입력", 
        placeholder="보험가입, 플랜, 민원, 분쟁상담 내용을 입력하거나 아래 마이크를 사용하세요.", 
        height=150
    )
    # 음성 인식 버튼 (물리적 분리 배치)
    if st.button("🎤 음성 상담 마이크 켜기", use_container_width=True):
        load_stt_engine()

with col_master_img:
    # [🚨 여성 마스터 사진 배치]
    st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/ai_expert.png", 
             caption="Goldkey AI 전문 마스터", use_container_width=True)
    st.info("💡 마스터가 실시간 정보를 대조 중입니다.")

# ==========================================
# [SECTION 5] 실전 튜토리얼 (독립 유지)
# ==========================================
st.divider()
with st.expander("💡 실전 보상 & 민원 대응 튜토리얼 (판례 2001다1480)", expanded=False):
    st.write("보험사 횡포 대응 및 금감원 분쟁 심의 전략 리포트 가이드.")

# ==========================================
# [SECTION 6] 1단계: 고객 기초 정보 (독립 유지)
# ==========================================
st.divider()
st.write("### 👤 1단계: 고객 기초 정보")
st.markdown("<style>.stTextArea textarea:focus, .stFileUploader section:hover { border: 2px solid #1E88E5 !important; animation: pulse 1.5s infinite; } @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(30, 136, 229, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(30, 136, 229, 0); } 100% { box-shadow: 0 0 0 0 rgba(30, 136, 229, 0); } }</style>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    customer_name = st.text_input("고객 성함", "고객님")
    hi_premium = st.number_input("월 건강보험료 (원)", value=0, step=1000)
with c2:
    debt = st.number_input("부채 총액 (만원)", value=0)
    uploaded_files = st.file_uploader("📸 증권, 진단서, 민원서류 로드", accept_multiple_files=True)

# ==========================================
# [SECTION 11] CFP® 위험관리 & 필수 보험 (독립 유지)
# ==========================================
st.divider()
st.write("### 🛡️ 2단계: CFP® 위험관리 & 필수 보장 설계")
with st.expander("반드시 있어야 할 보험 및 라이프 사이클 체크", expanded=True):
    essential_ins = st.multiselect("소유 및 필수 항목", ["자동차보험", "화재보험(주택/공장)", "일상생활배상책임", "사업장 배책", "충분한 후유장해", "기본통합장기보험"])
    product_extra = st.multiselect("보강 필요 항목", ["난치성 질병 보장", "자녀 통합보험", "인생 이모작 설계"])

# ==========================================
# [SECTION 12] CFP® 3층 연금 통합 설계 (독립 유지)
# ==========================================
st.divider()
st.write("### 💰 3단계: CFP® 3층 연금 통합 시뮬레이션")

with st.expander("국민·퇴직·개인연금 합산 및 전문 답변 로직", expanded=False):
    p1, p2, p3 = st.columns(3)
    p_nat = p1.number_input("국민연금(만)", value=0)
    p_ret = p2.number_input("퇴직연금(만)", value=0)
    p_ind = p3.number_input("개인연금(만)", value=0)
    p_logic_qa = st.text_area("❓ 연금 전문 상담 (언어로직 가동)")

# ==========================================
# [SECTION 13] CFP® 주택구입 & 인생 이모작 (독립 유지)
# ==========================================
st.divider()
st.write("### 🏡 4단계: 주택구입 & 인생 이모작 설계")

with st.expander("주택자금 및 은퇴 후 직업 인생 설계", expanded=False):
    home_fund = st.number_input("주택구입 필요자금(만원)", value=0)
    second_job = st.text_area("인생 이모작 계획 및 재무 고민")

# ==========================================
# [SECTION 14] 전문가 통합 분석 (유기적 자동 적용)
# ==========================================
st.divider()
if st.button("🔍 종합 마스터 컨설팅 리포트 생성 🚀", use_container_width=True, type="primary"):
    st.components.v1.html(s_voice("종합 분석을 시작합니다."), height=0)
    with st.spinner("마스터가 모든 섹션을 유기적으로 연산 중입니다..."):
        try:
            monthly_income = hi_premium / 0.0709 if hi_premium > 0 else 0
            model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=SYSTEM_PROMPT, tools=TOOLS)
            
            # 전 섹션 데이터 유기적 결합
            full_query = f"""
            고객 {customer_name} 종합 마스터 리포트 요청:
            [상담요청]: {main_consult_input}
            [위험관리]: {essential_ins} 가입여부 및 {product_extra} 보강 전략.
            [3층연금]: 국민({p_nat})+퇴직({p_ret})+개인({p_ind}) 합산 및 질문({p_logic_qa}) 답변.
            [생애설계]: 주택자금({home_fund}만) 및 인생이모작({second_job}) 조언.
            [보험분석]: 소득역산({monthly_income:,.0f}원) 기반 보장 공백(암 분류 엄격) 분석.
            결과는 다국어로 [항목|현재상태|가이드|결과|마스터 처방] 표로 생성하라.
            """
            
            response = model.generate_content([full_query] + ([PIL.Image.open(f) for f in uploaded_files] if uploaded_files else []))
            st.subheader(f"📊 {customer_name}님 마스터 통합 리포트")
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
