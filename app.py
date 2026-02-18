# ==========================================================================
# 👑 [골드키지사 AI 마스터 - 운영 헌법 준수 및 15개 섹션 독립 수호 완결본]
# 관리자: 이세윤 (글로벌 CFP 마스터)
# 지침: 섹션 통합 절대 금지 / 6대 법령 3중 검증 / 소득역산 0.0709 공식 준수
# ==========================================================================

import streamlit as st
import google.generativeai as genai
import PIL.Image
import re
import time
from datetime import datetime as dt
import streamlit.components.v1 as components

# --------------------------------------------------------------------------
# [SECTION 1] 설정 및 무손실 통합 페르소나 강령 (獨立)
# --------------------------------------------------------------------------
st.set_page_config(page_title="골드키지사 AI 마스터", page_icon="👑", layout="wide")

# [🚨 관리자 이세윤 지정: 무손실 통합 페르소나 강령]
SYSTEM_PROMPT = """
성명: 글로벌 보험/재무/인생설계 통합 전문가 (관리자: 이세윤)
지능 기반: AI Studio의 '보험비서_최종' + '보험상담 봇' + CFP® 국제표준 지능 통합 엔진.

[검색 강령]: 반드시 구글 실시간 검색(Grounding) 결과를 대조하여 답변하라.
[분석 철학 - 6대 법령 3중 검증]: 민법, 상법, 보험업법, 형사소송법, 화재법, 실화법에 근거하여 3중 검증하라.
[핵심 컨설팅 규칙]:
1. 데이터 대조: 입력 텍스트와 증권 파일을 동시에 대조하여 보상 누락 정밀 분석.
2. 암 담보 분류: 일반암 기준 유사/소액/재진단암 엄격 분류 (합산 금지).
3. 12대 핵심 담보: 암, 뇌, 심, 후유장해, 입원, 수술, 간병, 운전자, 화재, 배책, 연금, 상해 전수 분석.
4. 소득 역산(0.0709): 건보료 ÷ 0.0709 로직으로 월소득 계산 및 라이프 사이클 맞춤 제안.
5. 리포트 형식: 반드시 [항목 | 가입금액 합산 | 가이드라인 | 과·부족 결과 | 마스터 처방] 표 형태 유지.
"""

MODEL_NAME = 'gemini-1.5-flash'
TOOLS = [{'google_search_retrieval': {}}]

# --------------------------------------------------------------------------
# [SECTION 2] 음성 엔진 및 수애 목소리 (獨立)
# --------------------------------------------------------------------------
def s_voice(text, lang='ko-KR'):
    if re.search('[a-zA-Z]{5,}', text): lang = 'en-US'
    clean_text = text.replace('"', '').replace("'", "").replace("\n", " ")
    return f"""<script>
        window.speechSynthesis.cancel(); 
        var msg = new SpeechSynthesisUtterance("{clean_text}");
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

# --------------------------------------------------------------------------
# [SECTION 3] 사이드바 (사용자 센터 & 보안 - 獨立)
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("🔑 사용자 센터")
    user_name = st.text_input("상담원 성함", "이세윤 마스터")
    customer_name = st.text_input("고객 성함", "우량 고객")
    st.divider()
    st.info(f"👤 **관리자: 이세윤**")
    st.success("🌐 **다국어/CFP® 시스템 가동**")
    if st.button("❌ 보안 종료 및 데이터 파기", use_container_width=True):
        components.html(goodbye_sequence(), height=0)
        time.sleep(2); st.cache_data.clear(); st.session_state.clear(); st.rerun()
    st.divider()
    st.caption(f"🕒 최종 업데이트: {dt.now().strftime('%Y-%m-%d %H:%M')}")

# --------------------------------------------------------------------------
# [SECTION 4] 마스터 엔진 상단 UI (獨立)
# --------------------------------------------------------------------------
st.title("👑 골드키지사 AI 마스터")
col_in, col_img = st.columns([7, 3])
with col_in:
    main_area = st.text_area("📝 마스터 통합 상담창 (인식 결과)", height=120)
with col_img: 
    st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/ai_expert.png")

# --------------------------------------------------------------------------
# [SECTION 5] 실전 보상 & 민원 대응 (獨立)
# --------------------------------------------------------------------------
st.divider()
with st.expander("💡 실전 보상 & 민원 대응 (판례 2001다1480)"):
    st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/dispute_process.png")

# --------------------------------------------------------------------------
# [SECTION 6] 1단계: 필수 보장 자가 진단 (獨立)
# --------------------------------------------------------------------------
st.divider(); st.write("### 🛡️ 1단계: 필수 보장 자가 진단")
essential_ins = st.multiselect("보유 보험 선택", ["자동차", "화재", "일배책", "운전자", "통합보험"], key="sec6")

# --------------------------------------------------------------------------
# [SECTION 7] 2단계: 전문 증권 분석 자료 요청 (獨立)
# --------------------------------------------------------------------------
st.divider(); st.write("### 📸 2단계: 전문 증권 분석 자료 요청")
uploaded_files = st.file_uploader("증권 PDF 또는 이미지 업로드", accept_multiple_files=True, key="sec7")

# --------------------------------------------------------------------------
# [SECTION 8] 3단계: 건보료 기반 소득 역산 (獨立)
# --------------------------------------------------------------------------
st.divider(); st.write("### 💰 3단계: 건보료 기반 소득 역산")
hi_premium = st.number_input("월 국민건강보험료 (원)", value=0, step=1000, key="sec8")
if hi_premium > 0:
    monthly_income = hi_premium / 0.0709
    st.success(f"📊 역산 월 소득: **{monthly_income:,.0f}원** / 적정 보험료 15%: **{monthly_income*0.15:,.0f}원**")

# --------------------------------------------------------------------------
# [SECTION 9] 4단계: 질병 보상 정밀 분석 및 가족력 (獨立)
# --------------------------------------------------------------------------
st.divider(); st.write("### 🏥 4단계: 질병 보상 정밀 분석 및 가족력")
disease_focus = st.text_area("가족력 및 집중 분석 질환 입력", key="sec9")

# --------------------------------------------------------------------------
# [SECTION 10] 5단계: 대형 생보사 헬스케어 컨설팅 (獨立)
# --------------------------------------------------------------------------
st.divider(); st.write("### 💎 5단계: 대형 생보사 헬스케어 컨설팅")
healthcare_info = st.radio("상급병원 예약 서비스 필요 여부", ["예", "아니오", "미정"], key="sec10")

# --------------------------------------------------------------------------
# [SECTION 11] 6대 법령 및 보상 지식 DB (獨立)
# --------------------------------------------------------------------------
st.divider(); st.write("### 🏛️ 6대 법령 및 보상 지식 DB")
st.info("민법, 상법, 보험업법, 형사소송법, 화재법, 실화법 3중 검증 엔진 가동")

# --------------------------------------------------------------------------
# [SECTION 12] 국제재무설계 기준 위험관리 (獨立)
# --------------------------------------------------------------------------
st.divider(); st.write("### 🛡️ 국제재무설계 기준 위험관리")
st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/cfp_process.png")

# --------------------------------------------------------------------------
# [SECTION 13] 3층 연금 통합 시뮬레이션 (獨立)
# --------------------------------------------------------------------------
st.divider(); st.write("### 💰 3층 연금 통합 시뮬레이션")
st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/pension_3tier.png")
p_nat = st.number_input("국민연금(만)", key="p_nat"); p_ret = st.number_input("퇴직연금(만)", key="p_ret"); p_ind = st.number_input("개인연금(만)", key="p_ind")
home_fund = st.number_input("주택자금 필요액(만)", key="h_f"); second_life = st.text_area("인생 2막 계획", key="s_l")

# --------------------------------------------------------------------------
# [SECTION 14] 전문가 통합 분석 실행 (유기적 동시 구동)
# --------------------------------------------------------------------------
st.divider()
if st.button("🔍 종합 마스터 컨설팅 실행 (Global & Real-time) 🚀", use_container_width=True, type="primary"):
    components.html(s_voice("전 섹션 유기적 통합 분석을 시작합니다."), height=0)
    with st.spinner("CFP® 마스터가 구글 실시간 검색 결과를 대조 중입니다..."):
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=SYSTEM_PROMPT, tools=TOOLS)
            
            calc_income = hi_premium / 0.0709 if hi_premium > 0 else 0
            full_analysis_query = f"""
            고객 {customer_name} 종합 마스터 리포트 요청:
            1. [보험/위험]: 필수보험({essential_ins}) 가입 여부 및 {disease_focus} 보장 분석.
            2. [연금/재무]: 3층 연금({p_nat+p_ret+p_ind}만) 가치 분석. 주택자금({home_fund}만) 대안.
            3. [인생]: 인생 이모작({second_life})에 대한 CFP® 기준 재무 조언.
            4. [헬스케어]: 서비스 연계 방안({healthcare_info}).
            5. [소득역산]: 건보료 기반 추산소득({calc_income:,.0f}원) 대조.
            항목|현재|가이드|과부족|처방 표로 생성하라.
            """
            
            parts = [full_analysis_query, main_area]
            if uploaded_files:
                for f in uploaded_files: parts.append(PIL.Image.open(f))
            
            resp = model.generate_content(parts)
            st.subheader(f"📊 {customer_name}님 종합 생애 설계 리포트")
            st.markdown(resp.text)
            components.html(s_voice(f"{user_name} 마스터님, 분석이 완료되었습니다."), height=0)
        except Exception as e: st.error(f"🚨 분석 실패: {e}")

# --------------------------------------------------------------------------
# [SECTION 15] 성공 응원 및 보안 (獨立)
# --------------------------------------------------------------------------
st.divider()
if st.button("🏆 관리자 이세윤 & 전문 FC 성공 응원", use_container_width=True):
    st.balloons()
    msg = f"{user_name}님! CFP의 전문성과 마스터의 지능으로 성공을 거두십시오!"
    st.success(msg); components.html(s_voice(msg), height=0)

st.error("**[법적 고지]** 본 리포트는 참고용이며 최종 결정은 전문가와 상의하십시오.")
