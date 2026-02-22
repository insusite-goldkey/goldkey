# ==========================================================
# 관리자 전용 멀티페이지
# ==========================================================

import streamlit as st
import sys
import os

def main():
    st.set_page_config(
        page_title="관리자 콘솔", 
        page_icon="🛠️", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 관리자 인증
    if not authenticate_admin():
        st.error("관리자 접근 권한이 없습니다.")
        st.stop()
    
    st.title("🛠️ 마스터 AI 관리자 콘솔")
    st.markdown("---")
    
    # 사이드바 메뉴
    with st.sidebar:
        st.header("🎛️ 관리 메뉴")
        page = st.selectbox("페이지 선택", [
            "📊 대시보드",
            "👥 사용자 관리", 
            "📄 문서 관리",
            "⚙️ 시스템 설정",
            "🔐 보안 로그"
        ])
    
    # 페이지별 렌더링
    if page == "📊 대시보드":
        render_dashboard()
    elif page == "👥 사용자 관리":
        render_user_management()
    elif page == "📄 문서 관리":
        render_document_management()
    elif page == "⚙️ 시스템 설정":
        render_system_settings()
    elif page == "🔐 보안 로그":
        render_security_logs()

def authenticate_admin():
    """관리자 인증"""
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    
    if not st.session_state.admin_authenticated:
        st.subheader("🔐 관리자 인증")
        password = st.text_input("관리자 비밀번호", type="password")
        
        if st.button("인증"):
            if password == "goldkey777":
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("비밀번호가 올바르지 않습니다.")
                return False
    
    return st.session_state.admin_authenticated

def render_dashboard():
    """대시보드 렌더링"""
    st.header("📊 시스템 대시보드")
    
    # 통계 카드
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("총 사용자", "1,234", "+12%")
    with col2:
        st.metric("오늘 상담", "45", "+8%")
    with col3:
        st.metric("문서 처리", "892", "+15%")
    with col4:
        st.metric("시스템 가동", "99.9%", "정상")
    
    # 차트 영역
    st.subheader("📈 사용자 활동")
    chart_data = {
        '시간': ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
        '상담 건수': [12, 19, 34, 45, 38, 22]
    }
    st.line_chart(chart_data)

def render_user_management():
    """사용자 관리 렌더링"""
    st.header("👥 사용자 관리")
    
    # 사용자 검색
    search_term = st.text_input("사용자 검색")
    
    # 사용자 목록 (시뮬레이션)
    users = [
        {"id": "GK_user001", "name": "김철수", "join_date": "2024-01-15", "status": "활성"},
        {"id": "GK_user002", "name": "이영희", "join_date": "2024-02-20", "status": "활성"},
        {"id": "GK_user003", "name": "박민준", "join_date": "2024-03-10", "status": "휴면"}
    ]
    
    # 사용자 테이블
    for user in users:
        if search_term and search_term.lower() not in user['name'].lower():
            continue
            
        with st.expander(f"{user['name']} ({user['id']})"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**가입일:** {user['join_date']}")
            with col2:
                st.write(f"**상태:** {user['status']}")
            with col3:
                if st.button("수정", key=f"edit_{user['id']}"):
                    st.info(f"{user['name']} 사용자 정보 수정")

def render_document_management():
    """문서 관리 렌더링"""
    st.header("📄 문서 관리")
    
    # 문서 통계
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총 문서", "5,678")
    with col2:
        st.metric("오늘 업로드", "234")
    with col3:
        st.metric("저장 공간", "2.3GB")
    
    # 문서 목록
    st.subheader("최근 문서")
    documents = [
        {"name": "보험증권_001.pdf", "user": "김철수", "date": "2024-01-20", "size": "2.1MB"},
        {"name": "진단서_015.jpg", "user": "이영희", "date": "2024-01-20", "size": "1.5MB"},
        {"name": "상담기록_089.pdf", "user": "박민준", "date": "2024-01-19", "size": "3.2MB"}
    ]
    
    for doc in documents:
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.write(f"📄 {doc['name']}")
        with col2:
            st.write(f"👤 {doc['user']}")
        with col3:
            st.write(f"📅 {doc['date']}")
        with col4:
            if st.button("🗑️", key=f"del_doc_{doc['name']}"):
                st.warning(f"{doc['name']} 삭제 예정")

def render_system_settings():
    """시스템 설정 렌더링"""
    st.header("⚙️ 시스템 설정")
    
    # AI 설정
    st.subheader("🤖 AI 엔진 설정")
    ai_model = st.selectbox("AI 모델", ["gemini-1.5-flash", "gemini-1.5-pro"])
    max_tokens = st.slider("최대 토큰 수", 1000, 8000, 4000)
    temperature = st.slider("창의성 수치", 0.0, 1.0, 0.7)
    
    # 보안 설정
    st.subheader("🔐 보안 설정")
    session_timeout = st.slider("세션 타임아웃 (분)", 5, 60, 30)
    max_login_attempts = st.number_input("최대 로그인 시도", min_value=3, max_value=10, value=5)
    
    # 시스템 설정
    st.subheader("⚙️ 시스템 설정")
    debug_mode = st.checkbox("디버그 모드")
    maintenance_mode = st.checkbox("유지보수 모드")
    
    if st.button("설정 저장", type="primary"):
        st.success("설정이 저장되었습니다.")

def render_security_logs():
    """보안 로그 렌더링"""
    st.header("🔐 보안 로그")
    
    # 로그 필터
    col1, col2 = st.columns(2)
    with col1:
        log_level = st.selectbox("로그 레벨", ["전체", "INFO", "WARNING", "ERROR"])
    with col2:
        date_range = st.date_input("기간 선택", value=[dt.now().date() - timedelta(days=7), dt.now().date()])
    
    # 로그 목록 (시뮬레이션)
    logs = [
        {"timestamp": "2024-01-20 14:30:25", "level": "INFO", "user": "김철수", "action": "로그인 성공"},
        {"timestamp": "2024-01-20 14:32:10", "level": "WARNING", "user": "미상용자", "action": "로그인 실패"},
        {"timestamp": "2024-01-20 14:35:45", "level": "INFO", "user": "이영희", "action": "문서 업로드"},
        {"timestamp": "2024-01-20 14:40:20", "level": "ERROR", "user": "시스템", "action": "AI 엔진 오류"}
    ]
    
    for log in logs:
        if log_level != "전체" and log['level'] != log_level:
            continue
            
        color = {
            "INFO": "🟢",
            "WARNING": "🟡", 
            "ERROR": "🔴"
        }.get(log['level'], "⚪")
        
        st.write(f"{color} `{log['timestamp']}` `{log['user']}` `{log['action']}`")

if __name__ == "__main__":
    main()
