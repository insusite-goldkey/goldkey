# ==========================================================================
# 👑 [골드키지사 AI 마스터 - 운영 헌법 제1조: 완전무결 통합본]
# 관리자: 이세윤 (글로벌 CFP 마스터)
# 지침: 1.영상 사운드 해방 / 2.수애 음성 유지 / 3.15개 섹션 독립 수호 / 4.병합 금지
# ==========================================================================

import streamlit as st
import google.generativeai as genai
import PIL.Image
import re
import time
from datetime import datetime as dt
import streamlit.components.v1 as components

# --------------------------------------------------------------------------
# [SECTION 1] 설정 및 무손실 페르소나 강령 (獨立)
# --------------------------------------------------------------------------
st.set_page_config(page_title="골드키지사 AI 마스터", page_icon="👑", layout="wide")

SYSTEM_PROMPT = """
성명: 글로벌 보험/재무/인생설계 통합 전문가 (관리자: 이세윤)
지능 기반: AI Studio '보험비서_최종' + CFP® 국제표준 엔진 통합.
[분석 철학]: 민법, 상법, 보험업법 등 6대 법령 3중 검증.
[핵심 규칙]: 0.0709 소득역산 준수 및 [항목|현재|가이드|과부족|처방] 표 형식 엄수.
"""

# --------------------------------------------------------------------------
# [SECTION 2] 음성 엔진 및 수애 목소리 (獨立)
# --------------------------------------------------------------------------
def s_voice(text, lang='ko-KR'):
    clean_text = text.replace('"', '').replace("'", "").replace("\n", " ")
    return f"""<script>
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance("{clean_text}");
        msg.lang = "{lang}"; msg.rate = 1.0; msg.pitch = 1.1;
        window.speechSynthesis.speak(msg);
    </script>"""

def goodbye_sound():
    return """<script>
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance("이세윤 관리자 지침에 따라 모든 상담 데이터를 안전하게 파기했습니다.");
        msg.lang = 'ko-KR'; window.speechSynthesis.speak(msg);
    </script>"""

# --------------------------------------------------------------------------
# [SECTION 3] 사이드바: 사용자 센터 및 보안 (獨立)
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("🔑 사용자 센터")
    user_name = st.text_input("상담원 성함", "이세윤 마스터")
    customer_name = st.text_input("고객 성함", "우량 고객")
    st.divider()
    st.info(f"👤 **관리자: 이세윤**")
    st.success("🌐 **다국어/CFP® 시스템 가동**")
    if st.button("❌ 보안 종료 및 데이터 파기", use_container_width=True):
        components.html(goodbye_sound(), height=0)
        time.sleep(2)
        st.session_state.clear(); st.rerun()
    st.divider()
    st.caption(f"🕒 최종 업데이트: {dt.now().strftime('%Y-%m-%d %H:%M')}")

# --------------------------------------------------------------------------
# [SECTION 4] 마스터 UI 및 VEO 영상 사운드 해방 (獨立)
# --------------------------------------------------------------------------
st.title("👑 골드키지사 AI 마스터")
MASTER_VIDEO_URL = "https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/grok-video-c317d625-a0c7-4ce4-922c-7618ab3d7966.mp4" 

col_vid, col_txt = st.columns([4, 6])
with col_vid:
    st.markdown(f"""
    <div style="display: flex; flex-direction: column; align-items: center; background: #f0f4f8; padding: 20px; border-radius: 20px; border: 2px solid #1E88E5;">
        <video id="v_master" src="{MASTER_VIDEO_URL}" style="width: 100%; max-width: 280px; border-radius: 50%;" 
               autoplay playsinline loop controls></video>
        <p style="margin-top: 15px; font-weight: bold; color: #1E88E5;">🔊 마스터 음성 대화 가동 중</p>
    </div>
    <script>
        var v = document.getElementById('v_master');
        v.muted = false; v.volume = 0.8; v.play();
    </script>
    """, unsafe_allow_html=True)

with col_txt:
    main_area = st.text_area("📝 마스터 통합 상담창", height=200, placeholder="상담 내용을 입력하세요.")
    q_analyze = st.button("🚀 글로벌 CFP 정밀 분석 실행", type="primary", use_container_width=True)

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
    calc_income = hi_premium / 0.0709
    st.success(f"📊 역산 월 소득: **{calc_income:,.0f}원** / 적정 보험료 15%: **{calc_income*0.15:,.0f}원**")


# --------------------------------------------------------------------------
# [SECTION 9] 4단계: 질병 보상 정밀 분석 및 가족력 (獨立)
# --------------------------------------------------------------------------
st.divider(); st.write("### 🏥 4단계: 질병 보상 정밀 분석 및 가족력")
disease_focus = st.text_area("가족력 및 집중 분석 질환 입력", key="sec9")

# --------------------------------------------------------------------------
# [SECTION 10] 5단계: 대형 생보사 헬스케어 컨설팅 (獨立)
# --------------------------------------------------------------------------
st.divider(); st.write("### 💎 5단계: 대형 생보사 헬스케어 컨설팅")
hc_ans = st.radio("상급병원 2주 내 진찰 예약 서비스 필요 여부", ["예", "아니오", "미정"], key="sec10")

# --------------------------------------------------------------------------
# [SECTION 11] 6대 법령 및 보상 지식 DB (獨立)
# --------------------------------------------------------------------------
st.divider(); st.write("### 🏛️ 6대 법령 및 보상 지식 DB")
st.info("민법, 상법, 보험업법, 형사소송법, 화재법, 실화법 3중 검증 가동")

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

p_nat = st.number_input("국민연금(만)", key="p_nat")
p_ret = st.number_input("퇴직연금(만)", key="p_ret")
p_ind = st.number_input("개인연금(만)", key="p_ind")

# --------------------------------------------------------------------------
# [SECTION 14] 인생 이모작 및 주택 설계 (獨立)
# --------------------------------------------------------------------------
st.divider(); st.write("### 🏡 인생 이모작 및 주택 설계")
home_fund = st.number_input("주택자금 필요액(만)", key="h_f")
second_life = st.text_area("인생 2막 계획 및 노후 주거 설계", key="s_l")

# --------------------------------------------------------------------------
# [SECTION 15] 전문가 통합 분석 및 성공 응원 (獨立)
# --------------------------------------------------------------------------
st.divider()
if q_analyze:
    components.html(s_voice("전 섹션 유기적 통합 분석을 시작합니다."), height=0)
    with st.spinner("🔍 글로벌 CFP 마스터 엔진 분석 중..."):
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)
            income = hi_premium / 0.0709 if hi_premium > 0 else 0
            query = f"상담: {main_area}. 소득: {income:.0f}. 필수: {essential_ins}. 질환: {disease_focus}."
            
            parts = [query]
            if uploaded_files:
                for f in uploaded_files: parts.append(PIL.Image.open(f))
            
            resp = model.generate_content(parts)
            st.subheader(f"📊 {customer_name}님 정밀 리포트")
            st.markdown(resp.text)
            components.html(s_voice(f"{user_name} 마스터님, 분석이 완료되었습니다."), height=0)
        except Exception as e: st.error(f"분석 장애: {e}")

if st.button("🏆 관리자 이세윤 성공 응원", use_container_width=True): 
    st.balloons()
    components.html(s_voice("이세윤 관리자님, 필승하십시오! 당신의 성공을 응원합니다."), height=0)
