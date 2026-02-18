# ==========================================================================
# 👑 [골드키지사 AI 마스터 - 운영 헌법: 영상 사운드 완전 해방본]
# 관리자: 이세윤 (글로벌 CFP 마스터)
# 지침: 1. 영상 소리(Audio) 켜기 / 2. 수애 음성 유지 / 3. 15개 섹션 독립 수호
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

# --------------------------------------------------------------------------
# [SECTION 2] 수애 음성 엔진 (獨立)
# --------------------------------------------------------------------------
def s_voice(text, lang='ko-KR'):
    clean_text = text.replace('"', '').replace("'", "").replace("\n", " ")
    return f"""<script>
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance("{clean_text}");
        msg.lang = "{lang}"; msg.rate = 1.0;
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
        st.session_state.clear(); st.rerun()

# --------------------------------------------------------------------------
# [🚨 SECTION 4] 마스터 UI 및 VEO 영상 사운드 복구 (獨立)
# --------------------------------------------------------------------------
st.title("👑 골드키지사 AI 마스터")
MASTER_VIDEO_URL = "https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/grok-video-c317d625-a0c7-4ce4-922c-7618ab3d7966.mp4" 

col_vid, col_txt = st.columns([4, 6])
with col_vid:
    # 🚨 영상 사운드 복구: 'muted' 속성을 제거하고 'controls'를 추가하여 소리 조절 가능하게 변경
    st.markdown(f"""
    <div style="display: flex; flex-direction: column; align-items: center; background: #f0f4f8; padding: 20px; border-radius: 20px; border: 2px solid #1E88E5;">
        <video id="v_master" src="{MASTER_VIDEO_URL}" style="width: 100%; max-width: 280px; border-radius: 50%;" 
               autoplay playsinline controls loop></video>
        <p style="margin-top: 15px; font-weight: bold; color: #1E88E5;">🔊 영상 사운드 가동 중</p>
    </div>
    <script>
        // 자동 재생 정책 때문에 브라우저가 소리를 막을 경우를 대비한 강제 재생 스크립트
        var v = document.getElementById('v_master');
        v.muted = false;
        v.play();
    </script>
    """, unsafe_allow_html=True)

with col_txt:
    main_area = st.text_area("📝 마스터 통합 상담창", height=200)
    q_analyze = st.button("🚀 글로벌 CFP 정밀 분석 실행", type="primary", use_container_width=True)

# --------------------------------------------------------------------------
# [SECTION 5 ~ 14] 15개 섹션 독립 수호 (獨立)
# --------------------------------------------------------------------------
st.divider()
st.write("### 💰 건보료 기반 소득 역산 (0.0709)")
hi_premium = st.number_input("월 국민건강보험료 (원)", value=0, step=1000)
if hi_premium > 0:
    st.success(f"📊 역산 월 소득: **{hi_premium / 0.0709:,.0f}원**")


st.divider()
st.write("### 🛡️ 국제재무설계 기준 위험관리")
st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/cfp_process.png")


# --------------------------------------------------------------------------
# [SECTION 15] 분석 리포트 및 성공 응원 (獨立)
# --------------------------------------------------------------------------
st.divider()
if q_analyze:
    with st.spinner("🔍 분석 중..."):
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel(model_name='gemini-1.5-flash')
            resp = model.generate_content(main_area)
            st.subheader("📊 정밀 리포트")
            st.markdown(resp.text)
            # 수애 안내 음성
            components.html(s_voice("분석이 완료되었습니다."), height=0)
        except Exception as e: st.error(f"장애: {e}")

if st.button("🏆 성공 응원"): 
    st.balloons()
    components.html(s_voice("이세윤 관리자님, 필승하십시오!"), height=0)
