"""
[GP-제14조] 크레딧 과금 시스템 UI 통합 예시
Goldkey AI Masters 2026 - 12단계 파이프라인 적용 샘플 코드
"""
import streamlit as st
from modules.credit_manager import (
    render_coin_button,
    run_analysis_with_credit_control,
    get_existing_analysis,
    check_and_deduct_credit,
    save_analysis_result,
    render_credit_warning
)


# ══════════════════════════════════════════════════════════════════════════
# [예시 1] STEP 4: 통합 스캔 (1코인)
# ══════════════════════════════════════════════════════════════════════════

def render_scan_interface_example(agent_id: str, person_id: str):
    """
    증권 스캔 UI 예시 (1코인 차감).
    """
    st.markdown("### 📸 증권 스캔 및 분석")
    
    # 파일 업로드
    uploaded_file = st.file_uploader(
        "증권 이미지 업로드",
        type=['jpg', 'jpeg', 'png', 'pdf'],
        key="upload_scan"
    )
    
    if not uploaded_file:
        st.info("📤 증권 이미지를 업로드해 주세요.")
        return
    
    # 1코인 버튼 (자동 하드 락)
    if render_coin_button(
        label="🔍 스캔 시작",
        required_coins=1,
        key="btn_start_scan",
        button_type="primary"
    ):
        # 0코인 방어 + 차감 + 저장 자동 처리
        result = run_analysis_with_credit_control(
            user_id=agent_id,
            person_id=person_id,
            analysis_type='SCAN',
            analysis_function=perform_ocr_scan,
            required_coins=1,
            reason="증권 OCR 스캔 및 3단 일람표 생성",
            uploaded_file=uploaded_file
        )
        
        if result:
            st.success("✅ 스캔 완료!")
            display_scan_result(result)


def perform_ocr_scan(uploaded_file):
    """실제 OCR 스캔 함수 (예시)"""
    # 여기에 실제 OCR 로직 구현
    return {
        "policies": [
            {"name": "삼성화재 실손보험", "amount": "5000만원"},
            {"name": "KB손해보험 암보험", "amount": "3000만원"}
        ],
        "scan_date": "2026-03-29"
    }


def display_scan_result(result):
    """스캔 결과 표시 (예시)"""
    st.markdown("#### 📋 스캔 결과")
    for policy in result.get('policies', []):
        st.write(f"- {policy['name']}: {policy['amount']}")


# ══════════════════════════════════════════════════════════════════════════
# [예시 2] STEP 5: AI 트리니티 분석 (3코인)
# ══════════════════════════════════════════════════════════════════════════

def render_trinity_analysis_example(agent_id: str, person_id: str):
    """
    AI 트리니티 분석 UI 예시 (3코인 차감).
    """
    st.markdown("### 🤖 AI 트리니티 분석")
    
    # 코인 부족 경고 (선택사항)
    render_credit_warning(required_coins=3)
    
    # 3코인 버튼
    if render_coin_button(
        label="🎯 AI 분석 시작",
        required_coins=3,
        key="btn_trinity_analysis",
        button_type="primary"
    ):
        # 고객 데이터 조회
        customer_data = get_customer_data(person_id)
        
        # 통합 분석 실행
        result = run_analysis_with_credit_control(
            user_id=agent_id,
            person_id=person_id,
            analysis_type='TRINITY',
            analysis_function=run_trinity_engine,
            required_coins=3,
            reason="AI 트리니티 엔진 분석",
            customer_data=customer_data
        )
        
        if result:
            st.balloons()
            display_trinity_result(result)


def get_customer_data(person_id: str):
    """고객 데이터 조회 (예시)"""
    return {
        "name": "홍길동",
        "age": 35,
        "gender": "M"
    }


def run_trinity_engine(customer_data):
    """트리니티 엔진 실행 (예시)"""
    return {
        "score": 85,
        "gaps": ["암보험 부족", "실손 한도 초과"],
        "recommendations": ["암보험 3000만원 추가", "실손 갱신"]
    }


def display_trinity_result(result):
    """트리니티 결과 표시 (예시)"""
    st.markdown("#### 📊 분석 결과")
    st.metric("종합 점수", f"{result['score']}점")
    
    st.markdown("**보장 갭**")
    for gap in result.get('gaps', []):
        st.write(f"- {gap}")
    
    st.markdown("**추천 사항**")
    for rec in result.get('recommendations', []):
        st.write(f"- {rec}")


# ══════════════════════════════════════════════════════════════════════════
# [예시 3] STEP 9: 감성 제안서 (3코인) - 수동 구현
# ══════════════════════════════════════════════════════════════════════════

def render_emotional_proposal_example(agent_id: str, person_id: str):
    """
    감성 제안서 생성 UI 예시 (3코인 차감, 수동 구현).
    """
    st.markdown("### 💌 감성 제안서 생성")
    
    # 3코인 버튼
    if render_coin_button(
        label="✨ 감성 제안서 작성",
        required_coins=3,
        key="btn_emotional_proposal"
    ):
        # 1. 기존 결과 확인 (0코인 무료 조회)
        existing = get_existing_analysis(person_id, 'EMOTIONAL_PROPOSAL', agent_id)
        
        if existing:
            st.success("✅ 저장된 제안서를 무료로 불러왔습니다. (🪙 0)")
            display_proposal(existing.get('result_data', existing))
            return
        
        # 2. 코인 차감 (이미 render_coin_button에서 확인됨)
        if check_and_deduct_credit(agent_id, 3, "감성 제안서 생성"):
            # 3. AI 제안서 생성
            with st.spinner("✍️ AI가 제안서를 작성 중입니다..."):
                proposal = generate_emotional_proposal(person_id)
            
            # 4. 결과 저장 (다음엔 무료)
            save_analysis_result(
                person_id=person_id,
                agent_id=agent_id,
                analysis_type='EMOTIONAL_PROPOSAL',
                result_data=proposal,
                coins_used=3
            )
            
            # 5. 결과 표시
            st.success("✅ 제안서 작성 완료!")
            display_proposal(proposal)


def generate_emotional_proposal(person_id: str):
    """감성 제안서 생성 (예시)"""
    return {
        "title": "홍길동 고객님을 위한 맞춤 보장 설계",
        "content": "고객님의 소중한 가족을 지키기 위해...",
        "closing": "언제나 고객님 곁에서 함께하겠습니다."
    }


def display_proposal(proposal):
    """제안서 표시 (예시)"""
    st.markdown(f"#### {proposal.get('title', '제안서')}")
    st.write(proposal.get('content', ''))
    st.info(proposal.get('closing', ''))


# ══════════════════════════════════════════════════════════════════════════
# [예시 4] STEP 10: 카카오톡 멘트 (3코인)
# ══════════════════════════════════════════════════════════════════════════

def render_kakao_message_example(agent_id: str, person_id: str):
    """
    카카오톡 오프닝 멘트 생성 UI 예시 (3코인 차감).
    """
    st.markdown("### 💬 카카오톡 오프닝 멘트")
    
    # 3코인 버튼
    if render_coin_button(
        label="📱 카톡 멘트 생성",
        required_coins=3,
        key="btn_kakao_message"
    ):
        # 고객 이름 조회
        customer_name = get_customer_name(person_id)
        
        # 통합 분석 실행
        result = run_analysis_with_credit_control(
            user_id=agent_id,
            person_id=person_id,
            analysis_type='KAKAO_MESSAGE',
            analysis_function=generate_kakao_opening_message,
            required_coins=3,
            reason="카카오톡 오프닝 멘트 AI 작문",
            customer_name=customer_name
        )
        
        if result:
            # 생성된 메시지 표시
            st.markdown("#### 📝 생성된 메시지")
            message = st.text_area(
                "메시지 내용",
                value=result.get('message', ''),
                height=200,
                key="kakao_message_text"
            )
            
            # 발송 버튼
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📤 카카오톡 발송", type="primary"):
                    send_kakao_message(person_id, message)
                    st.success("✅ 카카오톡이 발송되었습니다!")
            
            with col2:
                if st.button("💾 메시지 저장"):
                    st.info("메시지가 저장되었습니다.")


def get_customer_name(person_id: str):
    """고객 이름 조회 (예시)"""
    return "홍길동"


def generate_kakao_opening_message(customer_name: str):
    """카카오톡 멘트 생성 (예시)"""
    return {
        "message": f"{customer_name} 고객님, 안녕하세요! 😊\n\n"
                   f"오늘 분석해 드린 보장 내용 확인하셨나요?\n"
                   f"궁금하신 점이 있으시면 언제든 연락 주세요!"
    }


def send_kakao_message(person_id: str, message: str):
    """카카오톡 발송 (예시)"""
    print(f"[KAKAO] 발송 대상: {person_id}, 메시지: {message}")


# ══════════════════════════════════════════════════════════════════════════
# [예시 5] 수동 버튼 구현 (render_coin_button 미사용)
# ══════════════════════════════════════════════════════════════════════════

def render_manual_button_example(agent_id: str, person_id: str):
    """
    수동 버튼 구현 예시 (render_coin_button 미사용).
    """
    st.markdown("### 🔧 수동 버튼 구현 예시")
    
    # 현재 코인 조회
    current_credits = st.session_state.get('current_credits', 0)
    required_coins = 1
    is_locked = current_credits < required_coins
    
    # 수동 버튼
    if st.button(
        f"🔍 스캔 및 분석하기 (🪙 -{required_coins})",
        disabled=is_locked,
        key="btn_manual_scan"
    ):
        # 코인 차감 및 분석 실행
        if check_and_deduct_credit(agent_id, required_coins, "수동 스캔"):
            result = perform_ocr_scan(None)
            st.success("✅ 스캔 완료!")
            display_scan_result(result)
    
    # 잔액 부족 시 경고
    if is_locked:
        st.error(
            f"🚨 잔여 코인 부족\n"
            f"필요: {required_coins} 🪙 / 현재: {current_credits} 🪙"
        )


# ══════════════════════════════════════════════════════════════════════════
# [메인 실행 예시]
# ══════════════════════════════════════════════════════════════════════════

def main():
    """
    메인 실행 함수 (테스트용).
    """
    st.set_page_config(page_title="크레딧 시스템 예시", layout="wide")
    
    st.title("🪙 크레딧 과금 시스템 통합 예시")
    
    # 테스트 사용자 설정
    agent_id = "test_agent_001"
    person_id = "test_person_001"
    
    # 세션 초기화
    if 'current_credits' not in st.session_state:
        st.session_state['current_credits'] = 100  # 테스트용 초기 코인
    
    # 상단 코인 잔액 표시
    st.sidebar.markdown(f"### 💰 보유 코인: **{st.session_state['current_credits']} 🪙**")
    
    # 탭 구성
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📸 스캔 (1코인)",
        "🤖 트리니티 (3코인)",
        "💌 제안서 (3코인)",
        "💬 카톡 (3코인)",
        "🔧 수동 구현"
    ])
    
    with tab1:
        render_scan_interface_example(agent_id, person_id)
    
    with tab2:
        render_trinity_analysis_example(agent_id, person_id)
    
    with tab3:
        render_emotional_proposal_example(agent_id, person_id)
    
    with tab4:
        render_kakao_message_example(agent_id, person_id)
    
    with tab5:
        render_manual_button_example(agent_id, person_id)


if __name__ == "__main__":
    main()
