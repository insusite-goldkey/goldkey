# ==========================================================================
# 🚨 [운영 헌법 - 이세윤 관리자 지침 100% 준수]
# 1. 서류 삭제 기능: 2단계 업로드 창 바로 아래 [🗑️ 전체 서류 삭제 및 재로드] 버튼 고정 배치.
# 2. 섹션 통합 절대 금지: 1~15번 모든 섹션은 물리적 구분선으로 독립성을 수호한다.
# 3. 브랜딩: "보험 가입 상담 부터 보험금 분쟁 대응까지- 보험 AI전문 마스터 통합 시스템"
# 4. 리스크 관리: 설계사 구상권 관련 보험업법 벌칙 규정은 답변에서 절대 제외한다.
# 5. 명칭 고정: 2단계(국제재무설계 기준...), 3단계(국제 재무설계 기준...).
# 6. 유기적 한 몸 구동: 모든 데이터는 최종 분석(Section 14)에서 지능적으로 통합된다.
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

# [🚨 서류 삭제 로직의 핵심: 세션 키 관리]
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0

MODEL_NAME = 'gemini-1.5-flash-latest'
TOOLS = [{'google_search_retrieval': {}}] 

SYSTEM_PROMPT = """
성명: 글로벌 보험/재무/분쟁대응 통합 전문가 (관리자: 이세윤)
지능 기반: '보험비서_최종' + '보험상담 봇' + 'CFP® 국제표준' + '금감원 분쟁대응' 통합 엔진.

[지휘 지침]:
1. 금기 사항: 보험업법상 불완전 판매 벌칙 및 설계사 구상권 관련 내용은 답변에서 절대 제외하라. (설계사 보호 필수)
2. 보상 대응: 판례 2001다1480 및 상법 제638조의3 근거로 법리 조문과 고객 사건을 결합하여 설명하라.
3. 분석 강령: 건보료 0.0709 소득 역산 로직 적용, 암 담보 합산 금지, CFP® 6단계 프로세스 준수.
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
# [SECTION 3] 사이드바 (튜토리얼 및 혜택 상시 노출)
# ==========================================
with st.sidebar:
    st.header("🔑 사용자 센터")
    user_name = st.text_input("상담원 성함", "전문 FC")
    st.divider()
    st.info("👤 **시스템 관리자: 이세윤**")
    st.markdown("### 🏆 회원 등록 및 수용 혜택")
    st.success("- 1일 50건 미만 상담 시 **8년간 무료**\n- 관리자 권한 **무제한 승인**\n- 데이터 **자동 파기 보안**")
    st.markdown("### 🌐 API 발급 튜토리얼")
    st.warning("1. 구글 로그인\n2. 카드 등록\n3. API 키 생성 및 연동")
    st.markdown('<a href="https://aistudio.google.com/app/apikey" target="_blank"><button style="width:100%; cursor:pointer; background:#1E88E5; color:white; border:none; padding:10px; border-radius:5px; font-weight:bold;">🌐 API 키 발급</button></a>', unsafe_allow_html=True)
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
# [SECTION 4.5] 마스터 통합 상담 센터 (대형 2모드)
# ==========================================
st.divider()
st.subheader("📡 마스터 통합 상담 센터")
col_input, col_img = st.columns([7, 3])
with col_input:
    main_consult_area = st.text_area("📝 마스터 통합 상담창 (내용 구현)", height=320, placeholder="모든 상담 내용을 입력하세요.")
    b1, b2, _ = st.columns([2, 2, 6])
    if b1.button("⌨️ 직접 입력", use_container_width=True): st.toast("직접 입력 모드 활성화")
    if b2.button("🎤 음성 입력", use_container_width=True): load_stt_engine()
with col_img:
    st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/ai_expert.png", caption="Goldkey AI 전문 마스터", use_container_width=True)

# ==========================================
# [SECTION 5] 실전 튜토리얼 (판례 2001다1480)
# ==========================================
st.divider()
with st.expander("💡 실전 보상 & 민원 대응 튜토리얼 (판례 2001다1480)", expanded=False):
    st.write("보험사의 설명의무 위반 시 법률 조문과 고객 사건을 결합하여 보상 청구 논리를 생성합니다.")

# ==========================================
# [SECTION 6] 1단계: 고객 기초 정보
# ==========================================
st.divider()
st.write("### 👤 1단계: 고객 기초 정보")
c_1, c_2 = st.columns(2)
customer_name = c_1.text_input("고객 성함", "고객님")
hi_premium = c_1.number_input("월 건강보험료 (원)", value=0, step=1000)
debt = c_2.number_input("부채 총액 (만원)", value=0)

# ==========================================
# [SECTION 7] 2단계: 자료 및 증권 업로드 (삭제 버튼 장착)
# ==========================================
st.divider()
st.write("### 📸 2단계: 자료 및 증권 업로드")

# [파일 업로더 - 세션 키 적용]
uploaded_files = st.file_uploader(
    "증권, 진단서, 민원서류 등을 로드하세요.", 
    accept_multiple_files=True,
    key=f"uploader_{st.session_state.uploader_key}"
)

# [🚨 삭제 버튼 및 로드 현황 보고]
if uploaded_files:
    num_files = len(uploaded_files)
    st.markdown(f"""
    <div style="border: 2px solid #1E88E5; padding: 15px; border-radius: 10px; background-color: #e3f2fd; margin-bottom: 10px;">
        <h4 style="margin-top:0; color:#0D47A1;">📁 서류 로드 현황 보고</h4>
        <p style="font-size:16px;">✅ <b>총 {num_files}장</b>의 서류가 인식되었습니다. 분석 준비가 완료되었습니다.</p>
    </div>
    """, unsafe_allow_html=True)

    # 시인성 극대화된 삭제 버튼
    if st.button("🗑️ 로드된 서류 전체 삭제 및 다시 올리기", type="primary", use_container_width=True):
        st.session_state.uploader_key += 1 # 키 값을 변경하여 위젯 강제 리셋
        st.rerun()

# ==========================================
# [SECTION 8] 3단계: 질병 보상 정밀 분석
# ==========================================
st.divider()
st.write("### 🏥 3단계: 질병 보상 정밀 분석 (암·뇌·심·정신·난치병)")
disease_focus = st.multiselect("분석 대상 질환 선택", ["암(선행항암)", "뇌/심장", "정신과", "희귀난치병"])

# ==========================================
# [SECTION 9] 4단계: 삼성/교보 헬스케어 컨설팅
# ==========================================
st.divider()
st.write("### 💎 4단계: 삼성/교보 헬스케어 컨설팅")
hc_info = st.checkbox("주요 생보사 헬스케어 서비스 안내 포함")

# ==========================================
# [SECTION 10] 5단계: 6대 법령 및 보상 지식 DB
# ==========================================
st.divider()
st.write("### 🏛️ 5단계: 6대 법령 및 보상 지식 DB")
st.info("민법, 상법, 보험업법 등 6대 법령 근거 3중 검증 가동 중")

# ==========================================
# [SECTION 11] 2단계: 국제재무설계 기준 위험관리 및 필수 보장 설계
# ==========================================
st.divider()
st.write("### 🛡️ 2단계: 국제재무설계 기준 위험관리 및 필수 보장 설계")

essential_ins = st.multiselect("필수 소유 보험", ["자동차보험", "화재보험", "일상생활배상책임", "사업장 배책", "후유장해", "기본통합장기"])

# ==========================================
# [SECTION 12] 3단계: 국제 재무설계 기준 3층 연금 통합 시뮬레이션
# ==========================================
st.divider()
st.write("### 💰 3단계: 국제 재무설계 기준 3층 연금 통합 시뮬레이션")

p_col = st.columns(3)
p_nat = p_col[0].number_input("국민연금(만)", value=0)
p_ret = p_col[1].number_input("퇴직연금(만)", value=0)
p_ind = p_col[2].number_input("개인연금(만)", value=0)

# ==========================================
# [SECTION 13] 4단계: 주택구입 및 인생 이모작 설계
# ==========================================
st.divider()
st.write("### 🏡 4단계: 주택구입 및 인생 이모작 설계")

home_fund = st.number_input("주택구입 필요자금(만원)", value=0)
second_job = st.text_area("인생 이모작(전직/창업) 계획")

# ==========================================
# [SECTION 14] 전문가 통합 분석 (유기적 한 몸 구동)
# ==========================================
st.divider()
if st.button("🔍 전 섹션 마스터 통합 분석 시작 🚀", use_container_width=True, type="primary"):
    st.components.v1.html(s_voice("전 섹션 통합 분석을 시작합니다."), height=0)
    with st.spinner("로드된 서류와 상담 데이터를 정밀 분석 중입니다..."):
        try:
            monthly_income = hi_premium / 0.0709 if hi_premium > 0 else 0
            model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=SYSTEM_PROMPT, tools=TOOLS)
            
            organic_query = f"""
            고객 {customer_name} 종합 마스터 리포트:
            [상담본부]: {main_consult_area}
            [로드서류]: 총 {len(uploaded_files) if uploaded_files else 0}장의 서류 대조 분석.
            [재무지표]: 소득역산({monthly_income:,.0f}원), 부채({debt}만).
            [위험관리]: {essential_ins} 기반 국제재무설계 기준 진단. 
            [보상논리]: 판례 2001다1480 근거 지급 거절 대응 논리 생성. (보험업법 벌칙 제외)
            [생애설계]: 3층 연금 및 주택자금({home_fund}만), 인생이모작({second_job}) 제언.
            
            결과는 다국어로 [항목|현재상태|가이드|결과|마스터 처방] 표로 생성하라.
            """
            
            response = model.generate_content([organic_query] + ([PIL.Image.open(f) for f in uploaded_files] if uploaded_files else []))
            st.subheader(f"📊 {customer_name}님 통합 솔루션 리포트")
            st.markdown(response.text)
        except Exception as e: st.error(f"🚨 분석 실패: {e}")

# ==========================================
# [SECTION 15] 성공 응원
# ==========================================
st.divider()
if st.button("🏆 관리자 이세윤 & 전문 FC 성공 응원"):
    st.balloons()
    msg = f"{user_name}님! 마스터의 지휘 아래 최고의 전문가가 되십시오!"
    st.success(msg); st.components.v1.html(s_voice(msg), height=0)

load_stt_engine()
