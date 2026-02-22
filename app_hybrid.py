# ==========================================================
# 골드키지사 마스터 AI - 하이브리드 모듈화 구조
# 사용자: 모바일 최적화 SPA / 관리자: PC 최적화 멀티페이지
# ==========================================================

import streamlit as st
from modules import auth, ai_engine, pdf_generator, database
import streamlit.components.v1 as components

def main():
    # 1. 기기별 최적화 CSS 로드
    load_device_optimized_css()
    
    # 2. 로그인 체크
    auth.check_login_status()
    
    # 3. 기기별 UI 분기
    is_mobile = detect_device()
    
    if is_mobile:
        render_mobile_interface()
    else:
        render_desktop_interface()

def detect_device():
    """기기 감지"""
    user_agent = st.context.headers.get("user-agent", "").lower()
    return any(m in user_agent for m in ["android", "iphone", "ipad", "mobile"])

def load_device_optimized_css():
    """기기별 최적화 CSS"""
    if detect_device():
        # 모바일 최적화
        st.markdown("""
        <style>
        .stApp { padding: 0.5rem !important; }
        .stButton>button { width: 100% !important; margin: 0.5rem 0; }
        .stTextInput>div>input, .stTextArea>div>textarea { 
            font-size: 16px !important; 
            padding: 12px !important;
        }
        .stSegmentedControl { 
            flex-direction: column !important; 
            gap: 0.5rem !important;
        }
        .element-container { padding: 0.5rem !important; }
        </style>
        """, unsafe_allow_html=True)
    else:
        # PC 최적화
        st.markdown("""
        <style>
        .stApp { max-width: 1200px !important; }
        .stSidebar { width: 300px !important; }
        .element-container { padding: 1rem !important; }
        </style>
        """, unsafe_allow_html=True)

def render_mobile_interface():
    """모바일 SPA 인터페이스"""
    # 상단 사용자 정보
    if 'user_id' in st.session_state:
        st.markdown(f"""
        <div style="background:#f8f9fa; padding:10px; border-radius:8px; text-align:center; margin-bottom:15px;">
            <strong>{st.session_state.user_name} 마스터님</strong>
            <a href="#" onclick="if(confirm('로그아웃 하시겠습니까?')) {{ window.location.reload(); }}" 
               style="float:right; color:#dc3545; text-decoration:none;">로그아웃</a>
        </div>
        """, unsafe_allow_html=True)
    else:
        auth.render_login_page()
        return
    
    # 모바일 메뉴
    menu = st.segmented_control(
        "메뉴 선택", 
        ["💬 상담", "📊 분석", "📄 내문서", "🏛️ 상속"], 
        selection_mode="single",
        key="mobile_menu"
    )
    
    # 메뉴별 기능 렌더링
    if menu == "💬 상담":
        ai_engine.render_chat_interface()
    elif menu == "📊 분석":
        pdf_generator.render_upload_interface()
    elif menu == "📄 내문서":
        pdf_generator.render_document_manager()
    elif menu == "🏛️ 상속":
        ai_engine.render_inheritance_planning()

def render_desktop_interface():
    """PC 데스크톱 인터페이스"""
    # 사이드바 로그인/정보
    with st.sidebar:
        if 'user_id' not in st.session_state:
            auth.render_login_page()
            return
        else:
            auth.render_logout_sidebar()
    
    # 메인 컨텐츠 영역
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.title("💬 마스터 AI 정밀 상담")
        ai_engine.render_chat_interface()
    
    with col2:
        st.title("📊 자산 분석")
        pdf_generator.render_upload_interface()

def load_hybrid_css():
    """하이브리드 CSS 로드"""
    st.markdown("""
    <style>
    /* 공통 */
    .stApp { max-width: 100% !important; }
    .main .block-container { padding-top: 1rem !important; }
    
    /* 모바일 */
    @media (max-width: 768px) {
        .stApp { padding: 0.5rem !important; }
        .stButton>button { width: 100% !important; }
        .stTextInput>div>input { font-size: 16px !important; }
    }
    
    /* PC */
    @media (min-width: 769px) {
        .stApp { max-width: 1200px !important; margin: 0 auto; }
        .stSidebar { width: 280px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
