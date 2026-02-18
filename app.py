# ==========================================================================
# 🚨 [절대삭제금지] 골드키지사 AI 마스터 전 섹션 무손실 통합 시스템
# 1. 페르소나: '보험비서_최종' + '보험상담 봇' 통합 지능 (6대 법령 근거)
# 2. 월소득 로직: 건보료 ÷ 0.0709 (매년 상승비율 반영) [절대삭제금지]
# 3. UI/UX: 섹션별 완전 분리 / 터치 시 Pulse 애니메이션 / API 가이드 팝업화
# 4. 음성안내: "마스터가 듣고 있어요" (음성은 전문 수애 엔진 사용)
# 5. 분석강령: 텍스트+이미지 '반드시' 동시 대조 및 암 담보 합산 금지 원칙
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
# [SECTION 1] 기본 설정 및 페르소나
# ==========================================
st.set_page_config(page_title="골드키지사 AI 마스터", page_icon="👑", layout="wide")

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

SYSTEM_PROMPT = """
성명: 고객 보험 상담 전문 AI 비서 (고도화된 전문 FC 대행)
페르소나: '보험비서_최종' & '보험상담 봇, 함께 만들어요' 통합 지능.
[언어 윤리 규정]: 욕설, 비하 발언, 성차별, 노인 비하 금지. 모든 언어는 순수 고객 상담 목적.
[분석 철학]: 6대 법령(민법, 상법, 보험업법, 형사소송법, 화재법, 실화법) 근거 3중 검증 실시.
[반드시 실행]: 입력된 텍스트(사유)와 로딩된 파일(이미지/증권)을 '반드시' 동시에 대조하여 통합 분석할 것.
[고급 답변 규칙]: 쟁점 시 [다수의견]과 [소수의견] 분리 제시. 암 담보 합산 금지(일반암 기준 분류). 
서류 안내 시 "본 준비 서류 목록은 2차적인 서류로 1차 보험사에 물어보고 준비하세요" 포함.
리포트 출력: 반드시 [항목 | 가입금액 합산 | 가이드라인 | 과·부족 결과 | 마스터 처방] 형태의 표로 제시.
"""

# ==========================================
# [SECTION 2] 음성 엔진 및 STT
# ==========================================
def s_voice(text, lang='ko-KR'):
    if re.search('[a-zA-Z]{5,}', text): lang = 'en-US'
    return f"""<script>
        window.speechSynthesis.cancel(); 
        var msg = new SpeechSynthesisUtterance("{text}");
        msg.lang = "{lang}"; msg.rate = 0.95; msg.pitch = 1.1; 
        window.speechSynthesis.speak(msg);
    </script>"""

def goodbye_sequence():
    return """<script>
        var context = new (window.AudioContext || window.webkitAudioContext)();
        var osc = context.createOscillator(); osc.type = 'sine'; 
        osc.frequency.setValueAtTime(523.25, context.currentTime); 
        osc.connect(context.destination); osc.start(); osc.stop(context.currentTime + 0.3);
        window.speechSynthesis.cancel(); 
        var msg = new SpeechSynthesisUtterance("보안 규정에 따라 로딩된 모든 자료를 파기했습니다.");
        msg.lang = 'ko-KR'; msg.rate = 0.95; msg.pitch = 1.1;
        window.speechSynthesis.speak(msg);
    </script>"""

def load_stt_engine():
    st.components.v1.html("""
    <script>
        window.startRecognition = function() {
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance("지금 말씀하세요. 마스터가 듣고 있습니다.");
            msg.lang = 'ko-KR'; msg.rate = 0.95; msg.pitch = 1.1;
            window.speechSynthesis.speak(msg);
            var recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.lang = 'ko-KR';
            recognition.onresult = function(event) {
                var transcript = event.results[0][0].transcript;
                var textArea = window.parent.document.querySelector('textarea');
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
# [SECTION 3] 사이드바 (API 가이드 및 종료)
# ==========================================
with st.sidebar:
    st.header("🔑 사용자 센터")
    user_name = st.text_input("상담원 성함", "전문 FC")
    st.divider()
    with st.expander("👤 회원 등록 및 API 발급 가이드 (필독)", expanded=False):
        st.info("🔑 **API 키 발급은 우리 앱의 생명줄과 같습니다.**")
        st.markdown("1. 새 창 열기 / 2. 지메일 로그인 / 3. 카드 등록(형식적) / 4. 8년 무료 혜택")
        st.markdown('<a href="https://aistudio.google.com/app/apikey" target="_blank" style="text-decoration: none;"><button style="width: 100%; border-radius: 5px; background-color: #1E88E5; color: white; border: none; padding: 10px; cursor: pointer; font-weight: bold; width:100%;">🌐 API 키 발급 (새 창)</button></a>', unsafe_allow_html=True)
    st.divider()
    if st.button("❌ 종료 시 모든 데이터 자동 파기", use_container_width=True):
        st.components.v1.html(goodbye_sequence(), height=0)
        st.cache_data.clear(); st.session_state.clear(); time.sleep(2.5); st.rerun()

# ==========================================
# [SECTION 4] 브랜드 멘트
# ==========================================
st.markdown(f"""
<div style="background-color:#f0f2f6; padding:20px; border-radius:10px; border-left:5px solid #1E88E5; margin-bottom:20px;">
    <h3 style="margin-top:0; color:#0D47A1;">"보험설계사는 보상 전문가여야 합니다."</h3>
    <p style="font-size:16px; color:#424242; line-height:1.6;">
       AI Studio의 <b>'보험비서_최종'</b>과 <b>'보험상담 봇'</b> 지능이 통합되었습니다.<br>
       30년 현장 노하우를 담은 <b>고도화된 전문 FC를 대행</b>하는 AI 마스터가 상담의 격을 높여드립니다.
    </p>
</div>
""", unsafe_allow_html=True)

st.title("👑 골드키지사 AI 마스터")

# ==========================================
# [SECTION 5] 실전 튜토리얼
# ==========================================
with st.expander("💡 [필독] 실전 보상 & 민원/사인거절/횡포 대응 튜토리얼", expanded=False):
    t_col1, t_col2, t_col3 = st.columns(3)
    with t_col1: st.info("⚖️ **보상 실무 & 판례**\n\n판례 2001다1480 근거 후유증 추가 청구법 교육.")
    with t_col2: st.error("🚫 **보상 횡포 & 사인거절 대응**\n\n부당 지급 거절 시 반박 논리 리포트 생성법.")
    with t_col3: st.warning("📝 **보험금 청구 가이드**\n\n보험사 홈페이지 및 앱 간편 청구 안내.")

# ==========================================
# [SECTION 6] 1단계: 고객 정보 입력
# ==========================================
st.divider()
st.markdown("<style>.stTextArea textarea:focus, .stFileUploader section:hover { border: 2px solid #1E88E5 !important; animation: pulse 1.5s infinite; } @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(30,136,229, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(30,136,229, 0); } 100% { box-shadow: 0 0 0 0 rgba(30,136,229, 0); } }</style>", unsafe_allow_html=True)
st.write("### 📝 1단계: 고객 정보 입력")
col_in1, col_in2 = st.columns(2)
with col_in1:
    customer_name = st.text_input("상담 대상 고객명", "고객님")
    hi_premium = st.number_input("월 건강보험료 (원)", value=0, step=1000)
with col_in2:
    debt = st.number_input("기존 부채 (만원)", value=0)
    st.info("💡 아래 입력창이나 파일창을 터치하면 상담이 활성화됩니다.")

# ==========================================
# [SECTION 7] 2단계: 정밀 분석 자료 접수
# ==========================================
st.divider()
st.write("### 🔍 2단계: 정밀 분석 자료 접수")
col_q, col_img = st.columns([6, 4])
with col_q:
    if st.button("🎤 마이크 켜기 (마스터 안내)"): load_stt_engine()
    user_question = st.text_area("❓ [사유 입력] 민원 사유나 궁금한 점을 입력하세요.", height=150, placeholder="터치 시 파동 효과 발생")
    uploaded_files = st.file_uploader("📸 [서류 로드] 증권, 진단서 등을 업로드하세요.", accept_multiple_files=True)
with col_img:
    st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/ai_expert.png", caption="마스터가 전문가 그룹과 협업할 준비를 마쳤습니다.", use_container_width=True)

# ==========================================
# [SECTION 8] 전문가 그룹 통합 분석 (누락 없음 확인)
# ==========================================
if st.button("🔍 전문가 그룹 통합 분석 시작 🚀", use_container_width=True, type="primary"):
    if user_question or uploaded_files:
        st.components.v1.html(s_voice("분석과 답변을 시작합니다."), height=0)
        with st.spinner("마스터가 전문가 그룹과 협업하여 정밀 리포트를 작성 중입니다..."):
            try:
                # [🚨 절대삭제금지: 월소득 추산 로직]
                monthly_income = hi_premium / 0.0709 if hi_premium > 0 else 0
                model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)
                
                # [🚨 텍스트+이미지 반드시 동시 분석 로직]
                content_parts = [f"상담사: {user_name}, 고객: {customer_name}, 월소득: {monthly_income:,.0f}원, 질문: {user_question}"]
                if uploaded_files:
                    for f in uploaded_files: content_parts.append(PIL.Image.open(f))
                
                response = model.generate_content(content_parts)
                st.session_state.answer = response.text
                
                # 결과 테이블
                st.markdown("### [💰 정밀 소득 역산 결과]")
                st.caption("※ 본 계산은 매년 건강보험료 상승비율에 따라 달라질 수 있습니다. [절대삭제금지]")
                st.table(pd.DataFrame({"분석 항목": ["추산 월 소득", "추산 연봉", "사망 보장(부채+5배)"], 
                                       "가이드라인": [f"{monthly_income:,.0f}원", f"{monthly_income*12:,.0f}원", f"{(debt*10000)+(monthly_income*12*5):,.0f}원"]}))
                
                st.markdown("---")
                st.info("📢 **마스터의 통합 분석 결과**")
                st.markdown(st.session_state.answer)
                st.components.v1.html(s_voice("분석이 완료되었습니다. 리포트를 확인해 주십시오."), height=0)
            except Exception as e: st.error(f"🚨 분석 실패: {e}")

# ==========================================
# [SECTION 9] 지식 데이터베이스
# ==========================================
st.divider()
st.write("### 🛡️ 보상 실무 및 글로벌 지원 지식 DB")
tab1, tab2, tab3 = st.tabs(["🏛️ 판례 및 법리", "🏢 법인/중대재해", "🌍 글로벌 보상"])
with tab1: st.info("🎯 **대법원 판례 2001다1480**\n\n합의 당시 예상치 못한 후유증 추가 청구의 법리적 근거.")
with tab2: st.warning("💼 **법인 자산계상 및 배상책임**\n\n해지환급금 자산계상 원칙 및 중대재해 배상 채무 상쇄 전략.")
with tab3:
    g_q = st.text_area("🌍 글로벌 상황 입력", key="g_q")
    if st.button("글로벌 해결 요청"):
        if g_q:
            res = genai.GenerativeModel('gemini-1.5-flash').generate_content(f"민법 733조 근거 답변: {g_q}")
            st.markdown(res.text)

# ==========================================
# [SECTION 10] 성공 응원 및 보안
# ==========================================
st.divider()
st.write("### 🚀 성공 응원 및 시스템 보안")
if st.button("🏆 모든 FC님들의 성공을 위한 업데이트 확인", use_container_width=True):
    st.balloons()
    msg = f"{user_name} FC님! 마스터가 당신의 성공을 진심으로 응원합니다!"
    st.success(f"### {msg}")
    st.components.v1.html(s_voice(msg), height=0)
st.error("**[법적 고지]** 본 리포트는 참고용입니다.")
st.sidebar.caption(f"최종 업데이트: {dt.now().strftime('%Y-%m-%d %H:%M')}")
load_stt_engine()
