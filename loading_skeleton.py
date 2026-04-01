"""
[GP-UI] 스켈레톤 UI 및 로딩 애니메이션 (백화 현상 차단)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 목적
st.rerun() 호출 시 화면이 하얗게 변하는 '백화 현상(Ghosting)'을 방지하기 위해
데이터 로딩 중에 Agentic Soft-Tech V4 디자인 시스템을 활용한 스켈레톤 UI를 표시

## 사용법
```python
from loading_skeleton import render_skeleton_ui, render_loading_spinner

# 데이터 로딩 중
with st.spinner():
    render_skeleton_ui(num_cards=3)
    # 또는
    render_loading_spinner(message="데이터 로딩 중...")
```
"""

import streamlit as st


def render_skeleton_ui(num_cards: int = 3, card_height: str = "120px") -> None:
    """
    스켈레톤 UI 렌더링 (Agentic Soft-Tech V4 디자인)
    
    Args:
        num_cards: 표시할 스켈레톤 카드 개수
        card_height: 카드 높이 (CSS 단위)
    """
    skeleton_css = f"""
    <style>
    .skeleton-container {{
        display: flex;
        flex-direction: column;
        gap: var(--gp-gap, 12px);
        padding: var(--gp-gap, 12px);
        width: 100%;
        max-width: 100%;
    }}
    .skeleton-card {{
        background: linear-gradient(
            90deg,
            var(--gp-bg-soft, #F9FAFB) 0%,
            var(--gp-block-base, #E0E7FF) 50%,
            var(--gp-bg-soft, #F9FAFB) 100%
        );
        background-size: 200% 100%;
        animation: skeleton-loading 1.5s ease-in-out infinite;
        border: 1px solid var(--gp-border-light, #D1D5DB);
        border-radius: var(--gp-radius, 8px);
        height: {card_height};
        width: 100%;
    }}
    @keyframes skeleton-loading {{
        0% {{ background-position: 200% 0; }}
        100% {{ background-position: -200% 0; }}
    }}
    .skeleton-text {{
        background: var(--gp-border-light, #D1D5DB);
        border-radius: var(--gp-radius-sm, 6px);
        height: 16px;
        margin: 8px 12px;
        animation: skeleton-pulse 1.5s ease-in-out infinite;
    }}
    .skeleton-text.short {{
        width: 60%;
    }}
    .skeleton-text.long {{
        width: 80%;
    }}
    @keyframes skeleton-pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.5; }}
    }}
    </style>
    """
    
    skeleton_html = skeleton_css + "<div class='skeleton-container'>"
    
    for i in range(num_cards):
        skeleton_html += f"""
        <div class='skeleton-card'>
            <div class='skeleton-text short'></div>
            <div class='skeleton-text long'></div>
        </div>
        """
    
    skeleton_html += "</div>"
    
    st.markdown(skeleton_html, unsafe_allow_html=True)


def render_loading_spinner(
    message: str = "데이터 로딩 중...",
    spinner_color: str = "var(--gp-border, #374151)"
) -> None:
    """
    커스텀 로딩 스피너 (Agentic Soft-Tech V4 디자인)
    
    Args:
        message: 로딩 메시지
        spinner_color: 스피너 색상 (CSS 변수 또는 hex)
    """
    spinner_html = f"""
    <style>
    .loading-container {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: calc(var(--gp-gap, 12px) * 3);
        width: 100%;
        max-width: 100%;
    }}
    .spinner {{
        border: 4px solid var(--gp-border-light, #D1D5DB);
        border-top: 4px solid {spinner_color};
        border-radius: 50%;
        width: 48px;
        height: 48px;
        animation: spin 1s linear infinite;
    }}
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    .loading-message {{
        margin-top: var(--gp-gap, 12px);
        font-size: clamp(14px, 1.8vw, 16px);
        font-weight: 700;
        color: var(--gp-text-dark, #1F2937);
        text-align: center;
    }}
    </style>
    <div class='loading-container'>
        <div class='spinner'></div>
        <div class='loading-message'>{message}</div>
    </div>
    """
    
    st.markdown(spinner_html, unsafe_allow_html=True)


def render_auth_loading() -> None:
    """
    로그인 중 전용 로딩 화면 (백화 현상 방지)
    """
    loading_html = """
    <style>
    .auth-loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: var(--gp-bg, #F3F4F6);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 9999;
    }
    .auth-spinner {
        border: 6px solid var(--gp-border-light, #D1D5DB);
        border-top: 6px solid var(--gp-success, #DCFCE7);
        border-radius: 50%;
        width: 64px;
        height: 64px;
        animation: auth-spin 1.2s linear infinite;
    }
    @keyframes auth-spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .auth-loading-text {
        margin-top: calc(var(--gp-gap, 12px) * 2);
        font-size: clamp(16px, 2vw, 20px);
        font-weight: 900;
        color: var(--gp-text-dark, #1F2937);
        text-align: center;
    }
    .auth-loading-subtext {
        margin-top: var(--gp-gap, 12px);
        font-size: clamp(13px, 1.6vw, 15px);
        color: var(--gp-text-muted, #6B7280);
        text-align: center;
    }
    </style>
    <div class='auth-loading-overlay'>
        <div class='auth-spinner'></div>
        <div class='auth-loading-text'>🏆 Goldkey AI Masters 2026</div>
        <div class='auth-loading-subtext'>로그인 중입니다...</div>
    </div>
    """
    
    st.markdown(loading_html, unsafe_allow_html=True)


def render_data_sync_progress(
    current_step: int,
    total_steps: int,
    step_name: str = ""
) -> None:
    """
    데이터 동기화 진행률 표시 (4자 동시 연동 시각화)
    
    Args:
        current_step: 현재 단계 (1부터 시작)
        total_steps: 전체 단계 수
        step_name: 현재 단계 이름
    """
    progress_percent = int((current_step / total_steps) * 100)
    
    progress_html = f"""
    <style>
    .sync-progress-container {{
        width: 100%;
        max-width: 600px;
        margin: calc(var(--gp-gap, 12px) * 2) auto;
        padding: var(--gp-gap, 12px);
        background: var(--gp-bg-soft, #F9FAFB);
        border: 1px solid var(--gp-border-light, #D1D5DB);
        border-radius: var(--gp-radius, 8px);
    }}
    .sync-progress-bar {{
        width: 100%;
        height: 24px;
        background: var(--gp-border-light, #D1D5DB);
        border-radius: var(--gp-radius-sm, 6px);
        overflow: hidden;
        position: relative;
    }}
    .sync-progress-fill {{
        height: 100%;
        background: linear-gradient(
            90deg,
            var(--gp-success, #DCFCE7) 0%,
            var(--gp-block-base, #E0E7FF) 100%
        );
        width: {progress_percent}%;
        transition: width 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: 900;
        color: var(--gp-text-dark, #1F2937);
    }}
    .sync-step-info {{
        margin-top: var(--gp-gap, 12px);
        font-size: clamp(13px, 1.6vw, 15px);
        color: var(--gp-text, #4B5563);
        text-align: center;
    }}
    </style>
    <div class='sync-progress-container'>
        <div class='sync-progress-bar'>
            <div class='sync-progress-fill'>{progress_percent}%</div>
        </div>
        <div class='sync-step-info'>
            {step_name} ({current_step}/{total_steps})
        </div>
    </div>
    """
    
    st.markdown(progress_html, unsafe_allow_html=True)
