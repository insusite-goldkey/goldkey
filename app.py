# ==========================================================================
# 👑 [골드키지사 AI 마스터 - 최종 효능 중심 시스템: 문법 완전 교정판]
# 절대규칙: 효율을 위해 섹션을 통합하지 말 것. 각 섹션은 독립된 효능을 가진다.
# 수정사항: SyntaxError(따옴표 미종결) 해결 및 전 섹션 물리적 분리 수호.
# ==========================================================================

import streamlit as st
import google.generativeai as genai
import PIL.Image
import json
import os
import re
import streamlit.components.v1 as components

# --------------------------------------------------------------------------
# [SECTION 1] 기본 설정 및 마스터 보안
# --------------------------------------------------------------------------
st.set_page_config(page_title="골드키지사 AI 마스터", page_icon="👑", layout="wide")
MASTER_ID = "admin"; MASTER_PW = "gold1234"

for key in ['uploader_key', 'disease_uploader_key', 'login_status', 'user_api_key', 'current_user', 'stt_text']:
    if key not in st.session_state:
        st.session_state[key] = 0 if 'key' in key else (False if 'status' in key else "")

def verify_user(u, p): return u == MASTER_ID and p == MASTER_PW

# --------------------------------------------------------------------------
# [SECTION 2] 보험봇 우회 엔진 (404 자가치유)
# --------------------------------------------------------------------------
SYSTEM_PROMPT = """당신은 이세윤 관리자가 설계한 '골드키지사 AI 마스터'입니다.
1단계 공식 근거(금감원, 판례, CFP)를 생성하고, 2단계 구글 검색과 교차 검증합니다.
소득 역산(0.0709) 및 적정 보험료 15% 가이드를 준수하며, 설계사 벌칙 규정은 제외합니다."""

def get_master_model(api_key):
    genai.configure(api_key=api_key)
    tools = [{'google_search_retrieval': {}}]
    for path in ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-1.5-flash-latest']:
        try:
            model = genai.GenerativeModel(model_name=path, system_instruction=SYSTEM_PROMPT, tools=tools)
            return model
        except: continue
    return None

# --------------------------------------------------------------------------
# [SECTION 3] 사이드바: 마스터 센터
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("🔑 마스터 센터")
    if st.session_state.login_status:
        st.success(f"👋 **{st.session_state.current_user}** 마스터님")
        if st.button("❌ 보안 종료"): st.session_state.login_status = False; st.rerun()
    else:
        l_u = st.text_input("아이디", key="l_u"); l_p = st.text_input("비밀번호", type="password", key="l_p")
        if st.button("🚀 로그인", use_container_width=True):
            if verify_user(l_u, l_p):
                st.session_state.login_status = True; st.session_state.current_user = "이세윤"
                if "GEMINI_API_KEY" in st.secrets: st.session_state.user_api_key = st.secrets["GEMINI_API_KEY"]
                st.rerun()
            else: st.error("정보 불일치")
    st.divider(); st.info("👤 **관리자: 이세윤**")

# --------------------------------------------------------------------------
# [SECTION 4] 브랜드 상단 UI
# --------------------------------------------------------------------------
st.divider()
st.markdown("<h3 style='color:#0D47A1;'>\"보험 가입 상담 부터 보험금 분쟁 대응까지\"</h3>", unsafe_allow_html=True)
st.title("👑 골드키지사 AI 마스터")

if not st.session_state.login_status:
    st.warning("🔒 관리자님, 로그인이 필요합니다. (admin / gold1234)"); st.stop()

# --------------------------------------------------------------------------
# [SECTION 4.5] 마스터 통합 상담 센터 (VEO 영상 연동)
# --------------------------------------------------------------------------
st.divider(); st.subheader("📡 마스터 통합 상담 센터")

MASTER_VIDEO_URL = "https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/grok-video-c317d625-a0c7-4ce4-922c-7618ab3d7966.mp4" 

stt_html = f"""
<div style="display: flex; flex-direction: column; align-items: center; background: #ffffff; padding: 25px; border-radius: 20px; border: 2px solid #1E88E5;">
    <div id="vid_box" style="width: 280px; height: 280px; border-radius: 50%; overflow: hidden; border: 6px solid #1E88E5; background: #000;">
        <video id="v_master" src="{MASTER_VIDEO_URL}" style="width: 100%; height: 100%; object-fit: cover;" playsinline></video>
    </div>
    <button id="mic_btn" style="margin-top: 25px; background: #1E88E5; color: white; border: none; padding: 15px 45px; border-radius: 40px; cursor: pointer; font-size: 22px; font-weight: bold;">
        🎤 마스터에게 질문하기
    </button>
    <p id="st_msg" style="margin-top: 15px; color: #333; font-weight: bold;">버튼을 누르면 마스터가 인사를 건넵니다.</p>
</div>
<script>
    const btn = document.getElementById('mic_btn'); const msg = document.getElementById('st_msg');
    const vid = document.getElementById('v_master');
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'ko-KR'; recognition.interimResults = false;

    btn.onclick = () => {{ 
        msg.innerText = "마스터가 인사하는 중입니다..."; 
        vid.play();
        vid.onended = () => {{ 
            msg.innerText = "경청 중... 궁금하신 내용을 말씀하십시오."; 
            recognition.start(); 
            btn.style.background = "red";
        }};
    }};

    recognition.onresult = (event) => {{
        const text = event.results[0][0].transcript; 
        msg.innerText = "인식 완료!";
        btn.style.background = "#1E88E5";
        window.parent.postMessage({{type: 'stt_result', text: text}}, '*');
    }};
</script>
"""
col_in, col_img = st.columns([7, 3])
with col_in:
    components.html(stt_html, height=520)
    main_area = st.text_area("📝 마스터 통합 상담창 (인식 결과)", value=st.session_state.stt_text, height=150, key="main_text")
    q_analyze = st.button("🚀 마스터 정밀 분석 실행", type="primary", use_container_width=True)
    main_output = st.container()

# --------------------------------------------------------------------------
# [SECTION 5] 실전 보상 & 민원 대응
# --------------------------------------------------------------------------
st.divider()
with st.expander("💡 실전 보상 & 민원 대응 (판례 2001다1480)"):
    st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/dispute_process.png")


# --------------------------------------------------------------------------
# [SECTION 6] 1단계: 필수 보장 자가 진단
# --------------------------------------------------------------------------
st.divider(); st.write("### 🛡️ 1단계: 필수 보장 자가 진단")
with st.chat_message("assistant"):
    st.write("필수보험 5종(일상배책, 화재, 자동차, 운전자, 통합보험) 준비 상태를 말씀해주세요.")
ess_reply = st.text_input("고객 답변 입력", key="ess_reply")

# --------------------------------------------------------------------------
# [SECTION 7] 2단계: 전문 증권 분석 자료 요청
# --------------------------------------------------------------------------
st.divider(); st.write("### 📸 2단계: 전문 증권 분석 자료 요청")
uploaded_files = st.file_uploader("증권 PDF 업로드", accept_multiple_files=True, key=f"u_{st.session_state.uploader_key}")

# --------------------------------------------------------------------------
# [SECTION 8] 3단계: 건보료 기반 소득 역산
# --------------------------------------------------------------------------
st.divider(); st.write("### 💰 3단계: 건보료 기반 소득 역산")
nhi_premium = st.number_input("월 건강보험료 입력 (원)", value=0, step=1000, key="nhi_pre")
if nhi_premium > 0:
    calc_income = nhi_premium / 0.0709
    calc_guide = calc_income * 0.15
    st.success(f"📊 역산 소득: **{calc_income:,.0f}원** / 권장 보장보험료(15%): **{calc_guide:,.0f}원**")

# --------------------------------------------------------------------------
# [SECTION 9] 4단계: 질병 보상 정밀 분석 및 가족력
# --------------------------------------------------------------------------
st.divider(); st.write("### 🏥 4단계: 질병 보상 정밀 분석 및 가족력")
with st.chat_message("assistant"):
    st.write("친·인척 가족 중 유전병이나 염려되는 질병을 알려주세요. 정밀 비교 분석해 드립니다.")
dis_text = st.text_area("가족력 및 염려 질환 내용", key="dis_text")
dis_files = st.file_uploader("질병 분석용 증권 업로드", accept_multiple_files=True, key=f"du_{st.session_state.disease_uploader_key}")

# --------------------------------------------------------------------------
# [SECTION 10] 5단계: 대형 생보사 헬스케어 컨설팅
# --------------------------------------------------------------------------
st.divider(); st.write("### 💎 5단계: 대형 생보사 헬스케어 컨설팅")
with st.chat_message("assistant"):
    st.write("난치병 시 **수도권 대형 병원** 진료를 원하시나요? 헬스케어 가입 시 **2주 이내 진찰** 예약이 가능합니다.")
hc_reply = st.radio("수도권 상급병원 진료 의사", ["예, 반드시 필요합니다", "아니오", "미정"], key="hc_radio")

# --------------------------------------------------------------------------
# [SECTION 11] 6대 법령 및 보상 지식 DB
# --------------------------------------------------------------------------
st.divider(); st.write("### 🏛️ 6대 법령 및 보상 지식 DB")
st.info("민법, 상법, 보험업법 판례 실시간 검색 가동")

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

p1, p2, p3 = st.columns(3)
p_nat = p1.number_input("국민연금", value=0); p_ret = p2.number_input("퇴직연금", value=0); p_ind = p3.number_input("개인연금", value=0)

# --------------------------------------------------------------------------
# [SECTION 14] 인생 이모작 및 주택 설계
# --------------------------------------------------------------------------
st.divider(); st.write("### 🏡 인생 이모작 및 주택 설계")
h_f = st.number_input("주택자금 필요액 (만원)", value=0); s_j = st.text_area("이모작 계획", key="s_j")

# --------------------------------------------------------------------------
# [SECTION 15] 전문가 통합 분석 및 성공 응원
# --------------------------------------------------------------------------
def run_master(container):
    with container:
        if not st.session_state.user_api_key: st.error("API Key 미연결"); return
        with st.spinner("🔍 분석 중..."):
            try:
                model = get_master_model(st.session_state.user_api_key)
                income = nhi_premium / 0.0709 if nhi_premium > 0 else 0
                query = f"상담: {main_area}. 건보료: {nhi_premium}. 질병: {dis_text}. 헬스케어: {hc_reply}."
                content = [query]
                all_files = (uploaded_files if uploaded_files else []) + (dis_files if dis_files else [])
                for f in all_files: content.append(PIL.Image.open(f))
                resp = model.generate_content(content)
                st.subheader("📊 통합 분석 리포트"); st.markdown(resp.text)
            except Exception as e: st.error(f"장애: {e}")

if q_analyze: run_master(main_output)
st.divider()
if st.button("🔍 전 섹션 마스터 종합 분석 리포트 생성 🚀", type="primary", use_container_width=True): run_master(st.container())
if st.button("🏆 관리자 이세윤 성공 응원"): st.balloons(); st.success("필승하십시오!")

# --------------------------------------------------------------------------
# [🚨 STT 브릿지 - 닫는 따옴표와 괄호를 확인하십시오]
# --------------------------------------------------------------------------
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
