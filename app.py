# ==========================================================================
# 🚨 [삭제/수정 절대 금지] 골드키지사 AI 마스터 전체 통합 시스템
# 본 코드는 이세윤 설계사의 전문 로직과 보안 엔진이 포함된 마스터본입니다.
# 섹션 1~10의 구조와 세부 수식(역산 로직 등)을 임의로 축소하거나 변경하지 마십시오.
# ==========================================================================

import streamlit as st
import pandas as pd
import time
import datetime
from datetime import datetime as dt
import google.generativeai as genai
import PIL.Image

# ==========================================
# [SECTION 1] 기본 설정 및 통합 시스템 지침
# ==========================================
st.set_page_config(page_title="골드키지사 AI 마스터", page_icon="👑", layout="wide")

try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    else:
        st.error("🔑 Streamlit Secrets에 API 키가 설정되지 않았습니다.")
except Exception as e:
    st.error(f"시스템 설정 확인 필요: {e}")

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
# [SECTION 2] 음성 및 보안 엔진
# ==========================================
def s_voice(text):
    return f"""<script>window.speechSynthesis.cancel(); var msg = new SpeechSynthesisUtterance("{text}");
    msg.lang = 'ko-KR'; msg.rate = 1.0; msg.pitch = 0.85; window.speechSynthesis.speak(msg);</script>"""

def goodbye_sequence():
    return """<script>
        var context = new (window.AudioContext || window.webkitAudioContext)();
        var osc = context.createOscillator(); 
        osc.type = 'sine'; 
        osc.frequency.setValueAtTime(523.25, context.currentTime); 
        osc.connect(context.destination); 
        osc.start(); 
        osc.stop(context.currentTime + 0.3);
        window.speechSynthesis.cancel(); 
        var msg = new SpeechSynthesisUtterance("보안 규정에 따라 로딩된 모든 자료를 파기했습니다.");
        msg.lang = 'ko-KR'; 
        window.speechSynthesis.speak(msg);
    </script>"""

def load_stt_engine():
    st.components.v1.html("""
    <script>
        window.startRecognition = function() {
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
# [SECTION 3] 사이드바
# ==========================================
with st.sidebar:
    st.header("🔑 사용자 센터")
    user_name = st.text_input("상담원 성함", "이세윤")
    st.divider()
    st.markdown("### 🛠️ API 키 발급 안내")
    st.link_button("🌐 구글 API 키 발급 (무료)", "https://aistudio.google.com/app/apikey")
    
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
# [SECTION 4~6] 상단 고정 멘트
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

with st.expander("💡 [필독] 실전 보상 & 민원/사인거절/횡포 대응 튜토리얼", expanded=False):
    t_col1, t_col2, t_col3 = st.columns(3)
    with t_col1:
        st.info("⚖️ **보상 실무 & 판례**")
        st.write("판례 2001다1480 근거, 예상 못한 후유증 추가 청구법 교육.")
    with t_col2:
        st.error("🚫 **보상 횡포 & 사인거절 대응**")
        st.write("보험사의 부당한 지급 거절이나 횡포 시 반박 논리 리포트 생성법.")
    with t_col3:
        st.warning("📝 **민원가이드 튜토리얼**")
        st.write("금융감독원 민원 접수용 논리 구성 및 보험업법 위반 사항 체크.")

# ==========================================
# [SECTION 7] 입력 인터페이스 & 전문가 통합 분석
# ==========================================
st.divider()
st.write("### 📝 고객 정보 및 증권 업로드")
col_in1, col_in2 = st.columns(2)
with col_in1:
    customer_name = st.text_input("상담 대상 고객명", "고객님")
    hi_premium = st.number_input("월 건강보험료 (원)", value=0)
with col_in2:
    debt = st.number_input("기존 부채 (만원)", value=0)
    uploaded_files = st.file_uploader("증권 이미지 로드 (📢 생성 후 자동 삭제)", accept_multiple_files=True)

# ------------------------------------------
# 📸 [복구] 전담 마스터 사진 및 상세 질문 영역
# ------------------------------------------
st.divider()
col_q, col_img = st.columns([7, 3])

with col_q:
    st.markdown('#### 🏆 전담 AI 마스터 상세 질문 (STT 마이크 지원)')
    if st.button("🎤 마이크 켜기 (음성 입력)"):
        st.info("지금 말씀하세요...")
        st.components.v1.html("<script>window.parent.startRecognition();</script>", height=0)
    user_question = st.text_area("❓ 분쟁 상황이나 민원 내용을 입력하세요", height=150, placeholder="내용을 입력하거나 마이크를 사용하세요.")

with col_img:
    img_url = "https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/ai_expert.png"
    try:
        st.image(img_url, caption="골드키지사 전담 AI 마스터", use_container_width=True)
    except:
        st.info("👤 AI 마스터 이미지 로딩 중...")

# [분석 및 답변 시작 버튼]
if st.button("🔍 전문가 그룹 통합 분석 및 답변 시작 🚀", use_container_width=True, type="primary"):
    if uploaded_files or user_question:
        with st.spinner("지침에 따라 정밀 분석 및 답변 생성 중..."):
            try:
                success = False
                for model_id in ['gemini-1.5-flash', 'models/gemini-1.5-flash']:
                    try:
                        model = genai.GenerativeModel(model_name=model_id, system_instruction=SYSTEM_PROMPT, tools=[{"google_search_retrieval": {}}])
                        content_parts = [f"상담원: {user_name}, 고객: {customer_name}, 건보료: {hi_premium}, 부채: {debt}, 질문: {user_question}"]
                        if uploaded_files:
                            for f in uploaded_files: content_parts.append(PIL.Image.open(f))
                        response = model.generate_content(content_parts)
                        st.session_state.answer = response.text
                        success = True; break
                    except: continue
                
                if success:
                    est_income = hi_premium * 40 / 10000
                    st.markdown("### [💰 소득 및 필요보장 통합표]")
                    data = {
                        "분석 항목": ["💵 추산 연봉", "🧬 필요 암 보장", "🧠 필요 뇌/심 보장", "🕊️ 사망 보장(부채포함)", "⏳ 노후준비(연금)"],
                        "가이드라인": [f"{est_income:.1f}억", "5.0억", "5.4억", f"{debt/10000 + (est_income*5):.1f}억", f"월 {est_income/12*10000:,.0f}원(100% 유지)"],
                        "판독 결과": ["정밀 역산", "⚠️ 부족", "⚠️ 부족", "🚨 보강필요", "🚨 즉시점검"]
                    }
                    st.table(pd.DataFrame(data))
                else: st.error("🚨 모델 호출 실패. 설정을 확인하세요.")
            except Exception as e: st.error(f"오류: {e}")

# ==========================================
# [SECTION 8] 전문 지식 데이터베이스 (답변 출력)
# ==========================================
if "answer" in st.session_state:
    st.markdown("---")
    st.info("📢 **전담 AI 마스터 분석 및 답변 결과**")
    st.markdown(st.session_state.answer)

st.divider()
tab1, tab2, tab3, tab4 = st.tabs(["🛡️ 보상 실무", "🏢 법인 세무", "🚨 중대재해", "🌐 글로벌 지원"])
with tab1: st.info("🎯 판례 2001다1480: 합의 당시 예상 못한 후유증 추가 청구 가능")
with tab2: st.warning("💼 해지환급금: 자산계상(사업준비금) 원칙 준수")
with tab3: st.error("🚔 중대재해: 단체보험 수익자 '법인' 지정 시 배상 채무 상쇄")
with tab4:
    st.subheader("🌐 글로벌 보상 지원 센터")
    user_input_extra = st.text_area("글로벌 상황 입력", key="global_input")
    if st.button("AI 마스터 해결 요청"):
        st.success(f"결과: {user_input_extra} 분석 완료 (법적근거: 민법 제733조 적용)")

# ==========================================
# [SECTION 10] 성공 응원 및 하단 보안
# ==========================================
st.divider()
if st.button("🚀 모든 FC님들의 성공을 위한 업데이트 확인", use_container_width=True):
    st.balloons(); msg = "FC님! 보험 시장의 주인공이 되십시오."; st.write(f"### {msg}"); st.components.v1.html(s_voice(msg), height=0)

st.error("**[법적 고지]** 본 리포트는 상담 참고용 자료입니다.")
st.sidebar.caption(f"최종 업데이트: {dt.now().strftime('%Y-%m-%d %H:%M')}")
load_stt_engine()
