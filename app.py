# ==========================================================================
# 👑 [골드키지사 AI 마스터 - 유료 등급 전용: 문법 완전 교정판]
# 절대규칙: 효율을 위해 섹션을 통합하지 말 것. 각 섹션은 독립된 효능을 가진다.
# 수정사항: Line 151 등 모든 st.image 및 문자열의 따옴표/괄호 폐쇄 확인 완료.
# ==========================================================================

import streamlit as st
import google.generativeai as genai
import PIL.Image
import json
import os
import streamlit.components.v1 as components

# --------------------------------------------------------------------------
# [SECTION 1] 기본 설정 및 마스터 보안
# --------------------------------------------------------------------------
st.set_page_config(page_title="골드키지사 AI 마스터", page_icon="👑", layout="wide")
MASTER_ID = "admin"; MASTER_PW = "gold1234"

for key in ['login_status', 'user_api_key', 'current_user', 'stt_text']:
    if key not in st.session_state:
        st.session_state[key] = False if 'status' in key else ""

def verify_user(u, p): return u == MASTER_ID and p == MASTER_PW

# --------------------------------------------------------------------------
# [SECTION 2] 유료 마스터 엔진 (Paid Tier 보안 가동)
# --------------------------------------------------------------------------
SYSTEM_PROMPT = """당신은 이세윤 관리자가 설계한 '골드키지사 AI 마스터'입니다.
1단계 공식 근거 생성, 2단계 구글 검색 검증을 수행하며 소득 역산 0.0709 공식을 준수합니다."""

def get_master_model(api_key):
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=SYSTEM_PROMPT,
            tools=[{'google_search_retrieval': {}}]
        ), "성공"
    except Exception as e:
        return None, str(e)

# --------------------------------------------------------------------------
# [SECTION 3] 사이드바: 마스터 가이드
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("🔑 마스터 센터")
    if st.session_state.login_status:
        st.success(f"👋 **{st.session_state.current_user}** 마스터님")
        if st.button("❌ 보안 로그아웃"): st.session_state.login_status = False; st.rerun()
    else:
        l_u = st.text_input("아이디"); l_p = st.text_input("비밀번호", type="password")
        if st.button("🚀 로그인", use_container_width=True):
            if verify_user(l_u, l_p):
                st.session_state.login_status = True; st.session_state.current_user = "이세윤"
                if "GEMINI_API_KEY" in st.secrets: st.session_state.user_api_key = st.secrets["GEMINI_API_KEY"]
                st.rerun()
    st.divider()
    st.info("**관리자: 이세윤**\n현장 효능 중심 시스템 가동")

# --------------------------------------------------------------------------
# [SECTION 4] 브랜드 상단 UI & VEO 대화
# --------------------------------------------------------------------------
st.divider()
st.title("👑 골드키지사 AI 마스터")
if not st.session_state.login_status: st.warning("🔒 로그인이 필요합니다."); st.stop()

MASTER_VIDEO_URL = "https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/grok-video-c317d625-a0c7-4ce4-922c-7618ab3d7966.mp4" 

stt_html = f"""
<div style="display: flex; flex-direction: column; align-items: center; background: #ffffff; padding: 20px; border-radius: 20px; border: 2px solid #1E88E5;">
    <video id="v_master" src="{MASTER_VIDEO_URL}" style="width: 250px; height: 250px; border-radius: 50%; object-fit: cover;" playsinline></video>
    <button id="mic_btn" style="margin-top: 20px; background: #1E88E5; color: white; border: none; padding: 10px 40px; border-radius: 35px; cursor: pointer; font-size: 20px; font-weight: bold;">🎤 마스터와 상담 시작</button>
</div>
<script>
    const btn = document.getElementById('mic_btn'); const vid = document.getElementById('v_master');
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'ko-KR';
    btn.onclick = () => {{ vid.play(); vid.onended = () => {{ recognition.start(); }}; }};
    recognition.onresult = (event) => {{
        const text = event.results[0][0].transcript;
        window.parent.postMessage({{type: 'stt_result', text: text}}, '*');
    }};
</script>
"""
components.html(stt_html, height=420)
main_area = st.text_area("📝 마스터 통합 상담창", value=st.session_state.stt_text, height=120)

# --------------------------------------------------------------------------
# [SECTION 5] 실전 보상 & 민원 대응
# --------------------------------------------------------------------------
st.divider()
with st.expander("💡 실전 보상 & 민원 대응 (판례 2001다1480)"):
    st.write("보험사의 설명의무 위반 시 대응 법리 및 판례 매칭 로직입니다.")
    st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/dispute_process.png")



# --------------------------------------------------------------------------
# [SECTION 6] 1단계: 필수 보장 자가 진단
# --------------------------------------------------------------------------
st.divider(); st.write("### 🛡️ 1단계: 필수 보장 자가 진단")
ess_reply = st.text_input("필수보험 5종 준비 상태")

# --------------------------------------------------------------------------
# [SECTION 7] 2단계: 전문 증권 분석 자료 요청
# --------------------------------------------------------------------------
st.divider(); st.write("### 📸 2단계: 전문 증권 분석 자료 요청")
uploaded_files = st.file_uploader("증권 PDF 또는 이미지 업로드", accept_multiple_files=True)

# --------------------------------------------------------------------------
# [SECTION 8] 3단계: 건보료 기반 소득 역산
# --------------------------------------------------------------------------
st.divider(); st.write("### 💰 3단계: 건보료 기반 소득 역산")
nhi_premium = st.number_input("월 국민건강보험료 (원)", value=0, step=1000)
if nhi_premium > 0:
    calc_income = nhi_premium / 0.0709
    st.success(f"📊 역산 월 소득: **{calc_income:,.0f}원** (적정 보험료 15%: **{calc_income*0.15:,.0f}원**)")

# --------------------------------------------------------------------------
# [SECTION 9] 4단계: 질병 보상 정밀 분석 및 가족력
# --------------------------------------------------------------------------
st.divider(); st.write("### 🏥 4단계: 질병 보상 정밀 분석 및 가족력")
dis_text = st.text_area("가족력 및 염려 질환 입력", key="dis_input")

# --------------------------------------------------------------------------
# [SECTION 10] 5단계: 대형 생보사 헬스케어 컨설팅
# --------------------------------------------------------------------------
st.divider(); st.write("### 💎 5단계: 대형 생보사 헬스케어 컨설팅")
hc_ans = st.radio("상급병원 진료 예약 필요성", ["예", "아니오", "미정"])

# --------------------------------------------------------------------------
# [SECTION 11] 6대 법령 및 보상 지식 DB
# --------------------------------------------------------------------------
st.divider(); st.write("### 🏛️ 6대 법령 및 보상 지식 DB")
st.info("민법, 상법, 보험업법 판례 가동 중")

# --------------------------------------------------------------------------
# [SECTION 12] 국제재무설계 기준 위험관리
# --------------------------------------------------------------------------
st.divider(); st.write("### 🛡️ 국제재무설계 기준 위험관리")
st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/cfp_process.png")



# --------------------------------------------------------------------------
# [SECTION 13] 3층 연금 통합 시뮬레이션
# --------------------------------------------------------------------------
st.divider(); st.write("### 💰 3층 연금 통합 시뮬레이션")
st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/pension_3tier.png")



# --------------------------------------------------------------------------
# [SECTION 14] 인생 이모작 및 주택 설계
# --------------------------------------------------------------------------
st.divider(); st.write("### 🏡 인생 이모작 및 주택 설계")
h_f = st.number_input("주택자금 필요액 (만원)", value=0)
s_j = st.text_area("이모작 계획")

# --------------------------------------------------------------------------
# [SECTION 15] 전문가 통합 분석 리포트
# --------------------------------------------------------------------------
st.divider()
if st.button("🚀 유료 엔진 통합 정밀 분석 실행", type="primary", use_container_width=True):
    with st.spinner("🔍 분석 중..."):
        model, msg = get_master_model(st.session_state.user_api_key)
        if not model: st.error(f"연결 실패: {msg}")
        else:
            try:
                income = nhi_premium / 0.0709 if nhi_premium > 0 else 0
                query = f"상담: {main_area}. 소득: {income:.0f}."
                resp = model.generate_content(query)
                st.subheader("📊 유료 마스터 리포트"); st.markdown(resp.text)
            except Exception as e: st.error(f"실행 장애: {e}")

st.divider()
if st.button("🏆 관리자 이세윤 성공 응원"): st.balloons(); st.success("필승하십시오!")

# [STT 브릿지]
components.html("""
<script>
window.addEventListener('message', function(event) {
    if (event.data.type === 'stt_result') {
        const text = event.data.text;
        const input = window.parent.document.querySelector('textarea[aria-label*="마스터 통합 상담창"]');
        if (input) { input.value = text; input.dispatchEvent(new Event('input', { bubbles: true })); }
    }
});
</script>
""", height=0)
