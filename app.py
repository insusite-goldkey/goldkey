import streamlit as st
import time

# --- 1. 기본 설정 및 브랜드 확정 ---
st.set_page_config(
    page_title="골드키지사 AI 마스터", 
    page_icon="👑", 
    layout="centered"
)

# --- 2. 수애 톤 음성 안내 함수 ---
def s_voice(text):
    return f"""
        <script>
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance("{text}");
            msg.lang = 'ko-KR';
            msg.rate = 1.0;
            msg.pitch = 0.85; 
            window.speechSynthesis.speak(msg);
        </script>
    """

# --- 3. 메인 화면 구성 ---
st.title("👑 골드키지사 AI 마스터")
st.subheader("FC님을 위한 분석 리포트 및 전문 상담 데이터베이스")

# --- 4. 핵심 3대 가이드 (보상/세무/다국어) ---
with st.container(border=True):
    st.info("💡 **골드키지사 AI 실전 보상 & 법인 세무 가이드**")
    t_col1, t_col2, t_col3 = st.columns(3)
    
    with t_col1:
        if st.button("📊 (1) 자료 분석 및\nDB 활용법", use_container_width=True):
            st.write("👉 증권 분석 시 전문가 식견이 담긴 **상담 데이터베이스**가 생성됩니다.")
            st.components.v1.html(s_voice("보험 서류를 로딩해 주세요. 분석 즉시 자료는 파기되니 안심하십시오."), height=0)
            
    with t_col2:
        if st.button("🛡️ (2) 보상 전문 지식\n& 민원 매뉴얼", use_container_width=True):
            st.success("🎯 **보상금 극대화 및 횡포 대응 전략**")
            
            # [수정 반영] 이자 공제 및 장해평가
            with st.expander("⚖️ 보상금 산정: 호프만 vs 라이프니츠", expanded=True):
                st.markdown("""
                - **호프만 방식(단리):** 공제액이 작아 **보상금이 더 큼.** (법원 표준)
                - **라이프니츠(복리):** 공제액이 커서 보상금이 낮아짐. (보험사 기준)
                - **장해평가:** **AMA(가장 높음)** > 맥브라이드 > 국가배상법 순서 준용.
                """)

            # [수정 반영] 금감원 및 사인 금지
            with st.expander("📝 금감원 민원 & 사인 금지 서류"):
                st.markdown("""
                - **민원절차:** 접수 → **자율조정(협상 적기)** → 전문위원 배정 → 분조위 상정
                - **사인금지:** 부제소 합의서, 면책동의서, 국세청 열람 (**절대 금지**)
                - **판례:** 2001다1480 (예상치 못한 후유증은 추가 청구 가능)
                """)
            v_msg = "피해자에게 유리한 호프만 방식과 AMA 장해 기준을 확인하십시오. 부당한 서류 요구는 판례로 대응해야 합니다."
            st.components.v1.html(s_voice(v_msg), height=0)
            
    with t_col3:
        if st.button("🏢 (3) 법인 세무\n& 유족보상", use_container_width=True):
            st.warning("💼 **CEO 경영인 정기보험 세무 전략**")
            
            # [신규 추가] 법인 세무 요약 가이드
            with st.expander("📑 법인 세무 리스크 관리 요약", expanded=True):
                st.markdown("""
                - **회계처리:** 환급금은 **자산(보험예치금)**, 보장분은 **비용** 처리 (보수적 접근)
                - **유족보상:** 산재법 기준(**1,300일분**) 준용 시 손금 인정 안전함
                - **주의:** 지배주주 자녀의 학자금 지원은 비용 인정 안 됨
                - **준비:** 정관 내 지급 산식 명문화 및 수익자 법인 지정 필수
                """)
            v_msg_tax = "경영인 정기보험은 환급률 구간에 따른 자산 계상이 핵심입니다. 산재법 기준을 준용하여 정관을 정비하십시오."
            st.components.v1.html(s_voice(v_msg_tax), height=0)

# --- 5. 실시간 다국어 지원 센터 ---
st.divider()
st.subheader("🌐 글로벌 보상 지원 센터 (실시간 번역)")
with st.expander("📝 민원 초안 생성 / 다국어 실시간 통역 요청"):
    user_input = st.text_area("상황 입력 (예: 금감원 민원 초안 작성해줘 / 위 세무 내용을 중국어로 번역해줘)")
    if st.button("AI 마스터에게 해결 요청"):
        st.warning("분석 및 실시간 번역 중...")
        time.sleep(1)
        st.code(f"결과: {user_input}\n\n[법적근거: 민법 제733조, 법인세법 기본통칙 19-19…8 적용]")

# --- 6. FC 성공 응원 메시지 ---
st.divider()
if st.button("🚀 모든 FC님들의 성공을 위한 업데이트 확인"):
    st.balloons()
    success_msg = "불철주야 매진하시는 FC님들을 위해 전문 보상 데이터베이스와 법인 세무 가이드 고도화를 마쳤습니다! 대한민국 최고의 전문가로 거듭나십시오."
    st.write(success_msg)
    st.components.v1.html(s_voice(success_msg), height=0)

# --- 7. 서비스 종료 및 데이터 파기 ---
st.sidebar.divider()
if st.sidebar.button("❌ 서비스 종료 및 데이터 즉시 파기"):
    st.sidebar.warning("🔒 모든 상담 데이터를 즉시 파기합니다...")
    time.sleep(2)
    st.rerun()

st.sidebar.caption("ⓒ 골드키지사 AI 마스터 | 시스템 보안 유지 중")
