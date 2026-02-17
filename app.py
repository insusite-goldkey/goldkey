# ==========================================================================
# 🚨 [삭제/수정 절대 금지] 골드키지사 AI 마스터 전체 통합 시스템
# 본 코드는 이세윤 설계사의 전문 로직과 '수예' 음성 엔진이 포함된 마스터본입니다.
# 섹션 1~10의 구조와 보안 예외 처리 로직을 절대 변경하거나 축소하지 마십시오.
# ==========================================================================

import streamlit as st
import pandas as pd
import time
import datetime
from datetime import datetime as dt
import google.generativeai as genai
import PIL.Image

# ==========================================
# [SECTION 1] 기본 설정 및 보안 엔진
# ==========================================
st.set_page_config(page_title="골드키지사 AI 마스터", page_icon="👑", layout="wide")

try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    else:
        st.error("🔑 Streamlit Secrets에 API 키가 설정되지 않았습니다.")
except Exception as e:
    st.error(f"⚠️ 시스템 설정 확인 필요: {e}")

TOKEN_POLICY = """
💡 **골드키지사 AI 사용 정책**
- **2026년 4월 30일까지 사용 제한 없음** (고도화 이벤트)
- **회원가입 시 1년간 무료** 사용 혜택 제공
- 정식 전환 시 압도적인 토큰 분량 제공
"""

SYSTEM_PROMPT = """
성명: 고객 보험 상담 전문 AI 비서 (이세윤 설계사 대행)
페르소나: '보험비서_최종' & '보험상담 봇, 함께 만들어요' 통합 지능.
[분석 철학]: 6대 법령(민법, 상법, 보험업법, 형사소송법, 화재법, 실화법) 근거 3중 검증.
[핵심 로직]: 보험사의 보상 횡포, 사인거절 시 약관과 판례(민법 733조 등) 근거 강력 방어.
[보고서 구조]: 🚨판독 총평 -> 💰필요보장 통합표 -> 📊영역별 분석 -> 🔍보상 실무 근거 순서로 작성.
"""

# ==========================================
# [SECTION 2] 수예 음성 엔진 (Tone: 수예)
# ==========================================
def s_voice(text):
    return f"""<script>
        window.speechSynthesis.cancel(); 
        var msg = new SpeechSynthesisUtterance("{text}");
        msg.lang = 'ko-KR'; msg.rate = 0.95; msg.pitch = 1.1; 
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
            var msg = new SpeechSynthesisUtterance("지금 말씀하세요. 수예가 듣고 있습니다.");
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
# [SECTION 3] 사이드바 (🚨 새 창 열기 확실히 강제)
# ==========================================
with st.sidebar:
    st.header("🔑 사용자 센터")
    user_name = st.text_input("상담원 성함", "이세윤")
    st.divider()
    st.markdown("### 🛠️ API 키 발급 안내")
    # [수정] <a> 태그와 target="_blank"를 사용하여 브라우저에서 새 탭 열기를 강제함
    st.markdown('''
        <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer">
            <button style="width:100%; padding:12px; background-color:#1E88E5; color:white; border:none; border-radius:8px; cursor:pointer; font-weight:bold;">
                🌐 구글 API 키 발급 (새 창 열기)
            </button>
        </a>
    ''', unsafe_allow_html=True)
    
    current_date = dt.now().date()
    expiry_date = datetime.date(2026, 4, 30)
    if current_date <= expiry_date:
        st.info(f"🔓 **2026년 4월 30일까지 무제한 승인 모드**")
    
    st.markdown(TOKEN_POLICY)
    st.divider()
    if st.button("❌ 종료 시 모든 데이터 자동 파기", use_container_width=True):
        st.components.v1.html(goodbye_sequence(), height=0)
        st.cache_data.clear(); st.session_state.clear(); time.sleep(2.5); st.rerun()

# ==========================================
# [SECTION 4~6] 상단 고정 브랜드 멘트 및 튜토리얼 원문 복구
# ==========================================
st.markdown(f"""
<div style="background-color:#f0f2f6; padding:20px; border-radius:10px; border-left:5px solid #1E88E5; margin-bottom:20px;">
    <h3 style="margin-top:0; color:#0D47A1;">"보험설계사는 보상 전문가여야 합니다."</h3>
    <p style="font-size:16px; color:#424242; line-height:1.6;">
        AI Studio의 <b>'보험비서_최종'</b>과 <b>'보험상담 봇, 함께 만들어요'</b> 지능이 통합되었습니다.<br>
        30년 현장 노하우를 담은 <b>이세윤 설계사 대행 AI 마스터</b>가 보상 상담의 격을 높여드립니다.
    </p>
</div>
""", unsafe_allow_html=True)

st.title("👑 골드키지사 AI 마스터")

# [수정] 튜토리얼이 시각적으로 명확하게 구분되도록 보강
with st.expander("💡 [필독] 실전 보상 & 민원/사인거절/횡포 대응 튜토리얼", expanded=False):
    t_col1, t_col2, t_col3 = st.columns(3)
    with t_col1:
        st.info("⚖️ **보상 실무 & 판례**")
        st.write("판례 2001다1480 근거, 예상 못한 후유증 추가 청구법 교육.")
        if st.button("판례 상세 보기"):
            st.write("🔎 **민법 제750조 및 판례 2001다1480:** 불법행위로 인한 손해배상 청구권의 소멸시효 및 추가 청구 요건 확인.")
    with t_col2:
        st.error("🚫 **보상 횡포 & 사인거절 대응**")
        st.write("보험사의 부당한 지급 거절이나 횡포 시 반박 논리 리포트 생성법.")
        if st.button("반박 논리 예시"):
            st.write("📑 **대응 매뉴얼:** 약관의 규제에 관한 법률 제4조(신의성실의 원칙) 근거 보상 거절의 부당성 주장.")
    with t_col3:
        st.warning("📝 **민원가이드 튜토리얼**")
        st.write("금융감독원 민원 접수용 논리 구성 및 보험업법 위반 사항 체크.")
        if st.button("민원 작성 가이드"):
            st.write("📝 **가이드:** 민원 신청 시 '보험업법 제127조의3' 위반 여부를 명시하여 금융감독원 압박.")

# ==========================================
# [SECTION 7] 전문가 그룹 통합 분석 (UI 최적화)
# ==========================================
st.divider()
st.write("### 📝 고객 정보 및 증권 업로드")
col_in1, col_in2 = st.columns(2)
with col_in1:
    customer_name = st.text_input("상담 대상 고객명", "고객님")
    hi_premium = st.number_input("월 건강보험료 (원)", value=0)
with col_in2:
    debt = st.number_input("기존 부채 (만원)", value=0)
    uploaded_files = st.file_uploader("증권 이미지 로드", accept_multiple_files=True)

st.divider()
col_q, col_img = st.columns([6, 4])
with col_q:
    st.markdown('#### 🏆 전담 AI 마스터 상세 질문 (수예 음성 지원)')
    if st.button("🎤 마이크 켜기 (수예 음성 안내)"):
        st.components.v1.html("<script>window.parent.startRecognition();</script>", height=0)
    user_question = st.text_area("❓ 분쟁 상황이나 민원 내용을 입력하세요", height=300)

with col_img:
    img_url = "https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/ai_expert.png"
    st.image(img_url, caption="골드키지사 전담 AI 마스터 '수예'", use_container_width=True)

if st.button("🔍 전문가 그룹 통합 분석 시작 🚀", use_container_width=True, type="primary"):
    if uploaded_files or user_question:
        with st.spinner("수예가 전문가 그룹과 협업하여 리포트를 작성 중입니다..."):
            try:
                model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)
                content_parts = [f"상담원: {user_name}, 고객: {customer_name}, 건보료: {hi_premium}, 부채: {debt}, 질문: {user_question}"]
                if uploaded_files:
                    for f in uploaded_files:
                        content_parts.append(PIL.Image.open(f))
                
                response = model.generate_content(content_parts)
                st.session_state.answer = response.text
                
                # 역산 로직 (무손실 유지)
                est_income = hi_premium * 40 / 10000
                st.markdown("### [💰 소득 및 필요보장 통합표]")
                data = {
                    "분석 항목": ["💵 추산 연봉", "🧬 필요 암 보장", "🧠 필요 뇌/심 보장", "🕊️ 사망 보장(부채포함)", "⏳ 노후준비(연금)"],
                    "가이드라인": [f"{est_income:.1f}억", "5.0억", "5.4억", f"{debt/10000 + (est_income*5):.1f}억", f"월 {est_income/12*10000:,.0f}원(100% 유지)"],
                    "판독 결과": ["정밀 역산", "⚠️ 부족", "⚠️ 부족", "🚨 보강필요", "🚨 즉시점검"]
                }
                st.table(pd.DataFrame(data))
            except Exception as e:
                st.error(f"🚨 전문가 분석 연결 실패: {e}")

# ==========================================
# [SECTION 8] 결과 출력
# ==========================================
if "answer" in st.session_state:
    st.markdown("---")
    st.info("📢 **수예의 분석 및 답변 결과**")
    st.markdown(st.session_state.answer)

# ==========================================
# [SECTION 9] 지식 데이터베이스 탭
# ==========================================
st.divider()
tab1, tab2, tab3, tab4 = st.tabs(["🛡️ 보상 실무", "🏢 법인 세무", "🚨 중대재해", "🌐 글로벌 지원"])
with tab1: st.info("🎯 판례 2001다1480: 합의 당시 예상 못한 중대 후유증은 추가 청구 가능")
with tab4:
    st.subheader("🌐 글로벌 보상 지원 센터")
    global_input = st.text_area("🌍 상황 입력", key="global_input_area")
    if st.button("수예에게 해결 요청"):
        if global_input:
            model = genai.GenerativeModel('gemini-1.5-flash')
            res = model.generate_content(f"수예의 민법 제733조 근거 답변: {global_input}")
            st.success("✅ 분석 완료"); st.markdown(res.text)

# ==========================================
# [SECTION 10] 성공 응원 및 하단 보안
# ==========================================
st.divider()
if st.button("🚀 모든 FC님들의 성공을 위한 업데이트 확인", use_container_width=True):
    st.balloons(); msg = "FC님! 보험 시장의 주인공이 되십시오."; st.write(f"### {msg}"); st.components.v1.html(s_voice(msg), height=0)

st.error("**[법적 고지]** 본 리포트는 상담 참고용 자료입니다.")
st.sidebar.caption(f"최종 업데이트: {dt.now().strftime('%Y-%m-%d %H:%M')}")
load_stt_engine()
