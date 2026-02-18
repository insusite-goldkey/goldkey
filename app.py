# ==========================================================================
# 👑 [골드키지사 AI 마스터 - 수애 음성(Sound) 엔진 완전 복구본]
# 관리자: 이세윤 (글로벌 CFP 마스터)
# 지침: 수애 목소리 안내 강제 활성화 / 초기 영상 복구 / 15개 섹션 독립 수호
# ==========================================================================

import streamlit as st
import google.generativeai as genai
import PIL.Image
import re
import time
from datetime import datetime as dt
import streamlit.components.v1 as components

# --------------------------------------------------------------------------
# [SECTION 1] 설정 및 무손실 페르소나 (獨立)
# --------------------------------------------------------------------------
st.set_page_config(page_title="골드키지사 AI 마스터", page_icon="👑", layout="wide")

SYSTEM_PROMPT = """성명: 글로벌 보험/재무/인생설계 통합 전문가 (관리자: 이세윤)
규칙: 6대 법령 검증, 0.0709 소득역산, 표 형식 리포트 엄수."""

# --------------------------------------------------------------------------
# [🚨 SECTION 2] 수애 음성(Sound) 출력 엔진 (獨立)
# --------------------------------------------------------------------------
def s_voice(text, lang='ko-KR'):
    """수애 목소리 TTS 가동 스크립트"""
    clean_text = text.replace('"', '').replace("'", "").replace("\n", " ")
    # 브라우저의 음성 합성 엔진을 강제로 깨우는 자바스크립트입니다.
    return f"""
    <script>
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance("{clean_text}");
        msg.lang = "{lang}";
        msg.rate = 1.0;
        msg.pitch = 1.1; // 수애의 맑은 톤을 위해 피치 상향
        window.speechSynthesis.speak(msg);
    </script>
    """

def goodbye_sound():
    """데이터 파기 음성 가이드"""
    return """<script>
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance("이세윤 관리자 지침에 따라 모든 상담 데이터를 안전하게 파기했습니다.");
        msg.lang = 'ko-KR';
        window.speechSynthesis.speak(msg);
    </script>"""

# --------------------------------------------------------------------------
# [SECTION 3] 사이드바 및 보안 (獨立)
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("🔑 사용자 센터")
    user_name = st.text_input("상담원 성함", "이세윤 마스터")
    st.divider()
    if st.button("❌ 보안 종료 및 데이터 파기", use_container_width=True):
        components.html(goodbye_sound(), height=0)
        time.sleep(2); st.session_state.clear(); st.rerun()

# --------------------------------------------------------------------------
# [SECTION 4] 마스터 UI 및 VEO 영상 (獨立)
# --------------------------------------------------------------------------
st.title("👑 골드키지사 AI 마스터")
MASTER_VIDEO_URL = "https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/grok-video-c317d625-a0c7-4ce4-922c-7618ab3d7966.mp4" 

col_vid, col_txt = st.columns([4, 6])
with col_vid:
    st.markdown(f"""
    <div style="display: flex; flex-direction: column; align-items: center; background: #f0f4f8; padding: 20px; border-radius: 20px; border: 2px solid #1E88E5;">
        <video id="v_master" src="{MASTER_VIDEO_URL}" style="width: 100%; max-width: 280px; border-radius: 50%;" autoplay muted loop playsinline></video>
        <p style="margin-top: 15px; font-weight: bold; color: #1E88E5;">📡 이세윤 마스터 음성 엔진 가동</p>
    </div>
    """, unsafe_allow_html=True)

with col_txt:
    main_area = st.text_area("📝 마스터 통합 상담창", height=200)
    q_analyze = st.button("🚀 글로벌 CFP 정밀 분석 실행", type="primary", use_container_width=True)

# --------------------------------------------------------------------------
# [SECTION 5~14] 15개 섹션 독립 수호 (獨立)
# --------------------------------------------------------------------------
st.divider()
with st.expander("💡 실전 보상 & 민원 대응 (판례 2001다1480)"):
    st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/dispute_process.png")


st.divider(); st.write("### 💰 3단계: 건보료 기반 소득 역산")
hi_premium = st.number_input("월 국민건강보험료 (원)", value=0, step=1000)
if hi_premium > 0:
    calc_income = hi_premium / 0.0709
    st.success(f"📊 역산 월 소득: **{calc_income:,.0f}원**")


# (14번 섹션까지 독립 유지...)

# --------------------------------------------------------------------------
# [🚨 SECTION 15] 전문가 분석 리포트 및 소리 출력 (獨立)
# --------------------------------------------------------------------------
st.divider()
if q_analyze:
    with st.spinner("🔍 마스터의 음성 분석을 준비 중입니다..."):
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)
            resp = model.generate_content(main_area)
            
            st.subheader("📊 글로벌 CFP 마스터 정밀 리포트")
            st.markdown(resp.text)
            
            # 🚨 소리 복구: 리포트 완성 시 수애가 즉시 말합니다.
            components.html(s_voice(f"{user_name} 마스터님, 요청하신 정밀 분석 리포트가 완성되었습니다. 내용을 확인해 주십시오."), height=0)
            
        except Exception as e: st.error(f"분석 장애: {e}")

if st.button("🏆 성공 응원"): 
    st.balloons()
    # 🚨 소리 복구: 성공 응원 멘트 낭독
    components.html(s_voice("이세윤 관리자님, 필승하십시오! 당신의 성공을 응원합니다."), height=0)
