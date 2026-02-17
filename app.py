import streamlit as st
import time

# --- 1. 기본 설정 (브랜드 명칭 확정) ---
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

# --- 3. 데이터 보안 파기 함수 ---
def goodbye_sequence():
    return """
        <script>
            var context = new (window.AudioContext || window.webkitAudioContext)();
            var osc = context.createOscillator();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(523.25, context.currentTime);
            osc.connect(context.destination);
            osc.start(); osc.stop(context.currentTime + 0.3);
            
            var msg = new SpeechSynthesisUtterance("방금 로딩한 문서는 보안 규정에 따라 자동으로 파기되었습니다. 오늘도 수고하셨습니다.");
            msg.lang = 'ko-KR';
            window.speechSynthesis.speak(msg);
        </script>
    """

# --- 4. 메인 화면 구성 ---
st.title("👑 골드키지사 AI 마스터")
st.subheader("FC님을 위한 분석 리포트 및 상담 데이터베이스")

# --- 5. 슬림 튜토리얼 (3+2 방식) ---
with st.container(border=True):
    st.info("💡 **골드키지사 AI 이용 가이드 (안내 음성 지원)**")
    t_col1, t_col2, t_col3 = st.columns(3)
    
    with t_col1:
        if st.button("📊 (1) 자료 분석 및\nDB 활용법", use_container_width=True):
            st.write("👉 증권 사진을 로딩하면 전문가 그룹의 식견이 담긴 **상담 데이터베이스**가 생성됩니다.")
            st.components.v1.html(s_voice("보험 증권 사진을 업로드해 주세요. 분석 즉시 자료는 파기되니 안심하셔도 됩니다."), height=0)
            
    with t_col2:
        if st.button("💬 (2) 질문과\n답변 얻기", use_container_width=True):
            st.write("👉 사고, 보상 등 궁금한 내용을 입력창에 물어보세요.")
            st.components.v1.html(s_voice("30년 상담 노하우를 담아 답변해 드립니다. 무엇이든 물어보세요."), height=0)
            
    with t_col3:
        if st.button("👤 (3) 회원가입·탈퇴\n(1년 전면 무료)", use_container_width=True):
            st.success("🎁 **1년간 전면 무료 및 시스템 고도화 기간 안내**")
            st.markdown("""
            - **기간:** 향후 1년간 (시스템 업데이트 및 수정·보안 시기)
            - **취지:** 현장의 목소리를 반영하여 대한민국 최고의 AI 비서를 완성해가는 과정입니다.
            - **보안:** 탈퇴 시 모든 상담 정보는 즉시 파기됩니다.
            """)
            v_msg = "본 서비스는 현재 시스템 업데이트와 수정 보완을 위한 일 년간의 안정화 기간을 거치고 있습니다. 이 기간 동안은 전면 무료로 운영되오니 안심하고 이용하십시오."
            st.components.v1.html(s_voice(v_msg), height=0)

    # 추가 안내 (요청 시 노출)
    with st.expander("❓ 추가 안내 (API 인증키 및 향후 운영)"):
        ex_col1, ex_col2 = st.columns(2)
        if ex_col1.button("🔑 API 인증키 설정"):
            st.write("40만 원 상당의 혜택을 누리는 개인 인증키 등록 방법입니다.")
        if ex_col2.button("💳 향후 운영 방향"):
            st.write("1년 후 시스템 유지보수를 위한 최소한의 'AI 마스터 구독료' 도입 예정입니다.")

# --- 6. FC 성공 응원 공지 섹션 ---
st.divider()
if st.button("🚀 모든 FC님들의 성공을 위한 업데이트 확인"):
    st.balloons()
    st.success("📢 **골드키지사 시스템 고도화 완료**")
    success_msg = "불철주야 고객 상담에 매진하시는 모든 FC님들의 성공을 위해 제가 시스템을 한 단계 더 업그레이드했습니다. 더욱 정교해진 분석 리포트 및 상담 데이터베이스를 경험해 보십시오."
    st.write(success_msg)
    st.components.v1.html(s_voice(success_msg), height=0)

# --- 7. 불편사항 음성 피드백 (녹취 안내) ---
st.divider()
st.subheader("📢 이용 중 불편하신 점이 있나요?")
if st.button("🎤 불편사항 말로 전달하기 (클릭 후 말씀하세요)"):
    st.info("🎙️ 녹음 중입니다... 말씀이 끝나면 [정지]를 눌러주세요. 이세윤 설계사에게 직접 전달됩니다.")
    time.sleep(2)
    st.success("✅ 소중한 의견이 접수되었습니다. FC님만을 위한 맞춤형 업데이트로 보답하겠습니다.")

# --- 8. 서비스 종료 및 보안 파기 ---
st.sidebar.divider()
if st.sidebar.button("❌ 서비스 종료 및 데이터 즉시 파기"):
    st.sidebar.warning("🔒 모든 상담 데이터를 파기 중입니다...")
    st.components.v1.html(goodbye_sequence(), height=0)
    time.sleep(2)
    st.rerun()

st.sidebar.caption("ⓒ 골드키지사 AI 마스터 | 시스템 보안 유지 중")
