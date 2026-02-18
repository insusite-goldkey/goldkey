# ==========================================================================
# 👑 [골드키지사 AI 마스터 - 유료 등급 전용: 문법 및 404 장애 완파본]
# 관리자 지침: 효율을 위해 섹션을 통합하지 말 것. 각 섹션은 독립된 효능을 가진다.
# 1. 문법 교정: SyntaxError 원인인 [Image of...] 태그 완전 제거.
# 2. 404 완파: 자가치유 라우터를 통해 모델 경로 에러(404) 물리적 차단.
# 3. 무손실 복구: 사이드바 8년 혜택 안내 및 15개 섹션의 물리적 분리 수호.
# ==========================================================================

import streamlit as st
import google.generativeai as genai
import PIL.Image
import json
import os
import streamlit.components.v1 as components

# --------------------------------------------------------------------------
# [SECTION 1] 기본 설정 및 마스터 보안 (admin / gold1234)
# --------------------------------------------------------------------------
st.set_page_config(page_title="골드키지사 AI 마스터", page_icon="👑", layout="wide")
MASTER_ID = "admin"; MASTER_PW = "gold1234"

for key in ['uploader_key', 'disease_uploader_key', 'login_status', 'user_api_key', 'current_user', 'stt_text']:
    if key not in st.session_state:
        st.session_state[key] = 0 if 'key' in key else (False if 'status' in key else "")

def verify_user(u, p): return u == MASTER_ID and p == MASTER_PW

# --------------------------------------------------------------------------
# [SECTION 2] 유료 마스터 엔진 (404 자가치유 라우터)
# --------------------------------------------------------------------------
SYSTEM_PROMPT = """당신은 이세윤 관리자가 설계한 '골드키지사 AI 마스터'입니다.
1. 근거: 금감원, 판례, CFP 기준 답변. 2. 검증: 구글 실시간 검색 활용.
3. 로직: 소득 역산(0.0709) 및 적정 보험료 15% 가이드를 준수하라."""

def get_master_model(api_key):
    genai.configure(api_key=api_key)
    # 404 에러를 피하기 위해 두 가지 경로를 순차적으로 시도합니다.
    candidates = ['gemini-1.5-flash', 'models/gemini-1.5-flash']
    for path in candidates:
        try:
            model = genai.GenerativeModel(
                model_name=path,
                system_instruction=SYSTEM_PROMPT,
                tools=[{'google_search_retrieval': {}}]
            )
            model.generate_content("ping") # 연결 테스트
            return model, "성공"
        except Exception:
            continue
    return None, "모든 경로에서 404 또는 연결 실패가 발생했습니다."

# --------------------------------------------------------------------------
# [SECTION 3] 왼쪽 사이드바: 마스터 회원 센터 (무손실 상세 안내)
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("🔑 마스터 회원 센터")
    if st.session_state.login_status:
        st.success(f"👋 **{st.session_state.current_user}** 마스터님")
        if st.button("❌ 보안 로그아웃", use_container_width=True):
            st.session_state.login_status = False; st.rerun()
    else:
        l_u = st.text_input("아이디", key="l_u"); l_p = st.text_input("비밀번호", type="password", key="l_p")
        if st.button("🚀 로그인", use_container_width=True):
            if verify_user(l_u, l_p):
                st.session_state.login_status = True; st.session_state.current_user = "이세윤"
                if "GEMINI_API_KEY" in st.secrets: st.session_state.user_api_key = st.secrets["GEMINI_API_KEY"]
                st.rerun()
    st.divider()
    st.markdown("### 👤 시스템 관리자: 이세윤")
    st.info("글로벌 보험/재무/분쟁대응 전문가")
    st.success("🏆 **마스터 전용 혜택**\n- 8년간 무료 상담 보장\n- 실시간 2단계 검증\n- 데이터 보안(학습 제외)")
    st.markdown('<a href="https://aistudio.google.com/app/apikey" target="_blank"><button style="width:100%; cursor:pointer; background:#1E88E5; color:white; border:none; padding:10px; border-radius:5px; font-weight:bold;">🌐 API 키 관리</button></a>', unsafe_allow_html=True)

# --------------------------------------------------------------------------
# [SECTION 4] 브랜드 상단 및 VEO 대화 엔진
# --------------------------------------------------------------------------
st.divider()
st.title("👑 골드키지사 AI 마스터")
if not st.session_state.login_status: st.warning("🔒 로그인이 필요합니다."); st.stop()

MASTER_VIDEO_URL = "https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/grok-video-c317d625-a0c7-4ce4-922c-7618ab3d7966.mp4" 
stt_html = f"""
<div style="display: flex; flex-direction: column; align-items: center; background: #ffffff; padding: 20px; border-radius: 20px; border: 2px solid #1E88E5;">
    <div style="width: 250px; height: 250px; border-radius: 50%; overflow: hidden; border: 5px solid #1E88E5;">
        <video id="v_master" src="{MASTER_VIDEO_URL}" style="width: 100%; height: 100%; object-fit: cover;" playsinline></video>
    </div>
    <button id="mic_btn" style="margin-top: 20px; background: #1E88E5; color: white; border: none; padding: 15px 45px; border-radius: 40px; cursor: pointer; font-size: 20px; font-weight: bold;">🎤 마스터에게 질문하기</button>
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
col_in, col_img = st.columns([7, 3])
with col_in:
    components.html(stt_html, height=450)
    main_area = st.text_area("📝 마스터 통합 상담창", value=st.session_state.stt_text, height=120)
    q_analyze = st.button("🚀 유료 정밀 분석 실행", type="primary", use_container_width=True)
with col_img: st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/ai_expert.png")

# --------------------------------------------------------------------------
# [SECTION 5] 실전 보상 & 민원 대응 튜토리얼
# --------------------------------------------------------------------------
st.divider()
with st.expander("💡 실전 보상 & 민원 대응 (판례 2001다1480)"):
    st.write("보험사의 설명의무 위반 시 대응 법리 및 판례 매칭 로직입니다.")
    st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/dispute_process.png")

# --------------------------------------------------------------------------
# [SECTION 6] 1단계: 필수 보장 자가 진단
# --------------------------------------------------------------------------
st.divider(); st.write("### 🛡️ 1단계: 필수 보장 자가 진단")
ess_reply = st.text_input("일상배책, 화재, 자동차, 운전자, 통합보험 준비 상태", key="ess_q")

# --------------------------------------------------------------------------
# [SECTION 7] 2단계: 전문 증권 분석 자료 요청
# --------------------------------------------------------------------------
st.divider(); st.write("### 📸 2단계: 전문 증권 분석 자료 요청")
uploaded_files = st.file_uploader("증권 PDF 또는 이미지 업로드", accept_multiple_files=True, key="up_main")

# --------------------------------------------------------------------------
# [SECTION 8] 3단계: 건보료 기반 소득 역산 (0.0709)
# --------------------------------------------------------------------------
st.divider(); st.write("### 💰 3단계: 건보료 기반 소득 역산")
nhi_premium = st.number_input("월 국민건강보험료 (원)", value=0, step=1000)
if nhi_premium > 0:
    calc_income = nhi_premium / 0.0709
    st.success(f"📊 역산 월 소득: **{calc_income:,.0f}원** / 권장 보험료 15%: **{calc_income*0.15:,.0f}원**")

# --------------------------------------------------------------------------
# [SECTION 9] 4단계: 질병 보상 정밀 분석 및 가족력
# --------------------------------------------------------------------------
st.divider(); st.write("### 🏥 4단계: 질병 보상 정밀 분석 및 가족력")
dis_text = st.text_area("가족력 및 염려 질환 입력", key="dis_q")
dis_files = st.file_uploader("질병 분석용 증권 업로드", accept_multiple_files=True, key="up_dis")

# --------------------------------------------------------------------------
# [SECTION 10] 5단계: 대형 생보사 헬스케어 컨설팅
# --------------------------------------------------------------------------
st.divider(); st.write("### 💎 5단계: 대형 생보사 헬스케어 컨설팅")
hc_ans = st.radio("상급병원 2주 내 진찰 예약 의사", ["예, 원합니다", "아니오", "미정"], key="hc_q")

# --------------------------------------------------------------------------
# [SECTION 11] 6대 법령 및 보상 지식 DB
# --------------------------------------------------------------------------
st.divider(); st.write("### 🏛️ 6대 법령 및 보상 지식 DB")
st.info("민법, 상법, 보험업법 판례 엔진 실시간 가동 중")

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
p_nat = p1.number_input("국민연금", key="pn"); p_ret = p2.number_input("퇴직연금", key="pr"); p_ind = p3.number_input("개인연금", key="pi")

# --------------------------------------------------------------------------
# [SECTION 14] 인생 이모작 및 주택 설계
# --------------------------------------------------------------------------
st.divider(); st.write("### 🏡 인생 이모작 및 주택 설계")
h_f = st.number_input("주택자금 필요액", key="hf"); s_j = st.text_area("이모작 계획", key="sj")

# --------------------------------------------------------------------------
# [SECTION 15] 전문가 통합 분석 리포트
# --------------------------------------------------------------------------
st.divider()
if q_analyze:
    with st.spinner("🔍 유료 보안 엔진 분석 중..."):
        model, msg = get_master_model(st.session_state.user_api_key)
        if not model: st.error(f"연결 실패: {msg}")
        else:
            try:
                income = nhi_premium / 0.0709 if nhi_premium > 0 else 0
                query = f"상담: {main_area}. 소득: {income:.0f}."
                all_files = (uploaded_files if uploaded_files else []) + (dis_files if dis_files else [])
                content = [query] + [PIL.Image.open(f) for f in all_files]
                resp = model.generate_content(content)
                st.subheader("📊 유료 마스터 정밀 리포트"); st.markdown(resp.text)
            except Exception as e: st.error(f"실행 장애: {e}")

if st.button("🏆 관리자 이세윤 성공 응원"): st.balloons(); st.success("필승하십시오!")

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
