"""
[GP-CRM] 에이젠틱 칵핏 UI 컴포넌트 (Agentic Cockpit UI)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 목적
HQ 중앙 통제실에서 전달받은 브리핑 데이터를 CRM 대시보드에 시각화하여
사용자가 "지금 당장 해야 할 일"을 직관적으로 파악할 수 있도록 지원

## 핵심 컴포넌트
1. render_agentic_briefing() - 브리핑 박스 (소프트 인디고 배경)
2. render_12step_progress() - 12단계 세일즈 프로세스 진행 바
3. render_dashboard_grid() - 반응형 대시보드 그리드

## 사용법
```python
from crm_cockpit_ui import render_agentic_briefing, render_12step_progress

# 브리핑 박스 렌더링
render_agentic_briefing(agent_id="agent_123")

# 12단계 진행 바 렌더링
render_12step_progress(current_stage=4, customer_name="홍길동")
```
"""

import streamlit as st
from typing import Dict, Any, Optional


# ══════════════════════════════════════════════════════════════════════════════
# §1 에이젠틱 브리핑 박스
# ══════════════════════════════════════════════════════════════════════════════

def render_agentic_briefing(agent_id: str) -> None:
    """
    HQ 중앙 통제실 브리핑 박스 렌더링 (대시보드 최상단)
    
    Args:
        agent_id: 설계사 ID
    """
    from hq_briefing import get_daily_briefing, format_briefing_message, get_briefing_icon
    
    # HQ에서 브리핑 데이터 가져오기
    briefing_data = get_daily_briefing(agent_id)
    priority_actions = briefing_data.get("priority_actions", [])
    stats = briefing_data.get("stats", {})
    
    # 브리핑 박스 CSS
    briefing_css = """
    <style>
    .agentic-briefing-container {
        background: linear-gradient(135deg, var(--gp-block-base, #E0E7FF) 0%, var(--gp-bg-soft, #F9FAFB) 100%);
        border: 1px solid var(--gp-border, #374151);
        border-radius: var(--gp-radius, 8px);
        padding: calc(var(--gp-gap, 12px) * 1.5);
        margin-bottom: calc(var(--gp-gap, 12px) * 2);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    .briefing-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: var(--gp-gap, 12px);
        flex-wrap: wrap;
        gap: 8px;
    }
    .briefing-title {
        font-size: clamp(18px, 2.5vw, 24px);
        font-weight: 900;
        color: var(--gp-text-dark, #1F2937);
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .briefing-timestamp {
        font-size: clamp(12px, 1.5vw, 14px);
        color: var(--gp-text-muted, #6B7280);
    }
    .briefing-stats {
        display: flex;
        gap: calc(var(--gp-gap, 12px) * 2);
        margin-bottom: calc(var(--gp-gap, 12px) * 1.5);
        flex-wrap: wrap;
    }
    .stat-item {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .stat-value {
        font-size: clamp(20px, 3vw, 28px);
        font-weight: 900;
        color: var(--gp-text-dark, #1F2937);
    }
    .stat-label {
        font-size: clamp(12px, 1.5vw, 14px);
        color: var(--gp-text, #4B5563);
    }
    .briefing-actions {
        display: flex;
        flex-direction: column;
        gap: var(--gp-gap, 12px);
    }
    .action-card {
        background: #ffffff;
        border: 1px solid var(--gp-border-light, #D1D5DB);
        border-radius: var(--gp-radius-sm, 6px);
        padding: var(--gp-gap, 12px);
        display: flex;
        align-items: flex-start;
        gap: var(--gp-gap, 12px);
        transition: all 0.2s ease;
    }
    .action-card:hover {
        border-color: var(--gp-border, #374151);
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
        transform: translateY(-1px);
    }
    .action-icon {
        font-size: 24px;
        flex-shrink: 0;
    }
    .action-content {
        flex: 1;
        min-width: 0;
    }
    .action-message {
        font-size: clamp(13px, 1.6vw, 15px);
        color: var(--gp-text-dark, #1F2937);
        line-height: 1.6;
        word-wrap: break-word;
    }
    .no-actions-message {
        text-align: center;
        padding: calc(var(--gp-gap, 12px) * 2);
        font-size: clamp(14px, 1.8vw, 16px);
        color: var(--gp-text-muted, #6B7280);
    }
    @media (max-width: 768px) {
        .briefing-stats {
            gap: var(--gp-gap, 12px);
        }
        .stat-item {
            flex: 1 1 45%;
            min-width: 120px;
        }
    }
    </style>
    """
    
    st.markdown(briefing_css, unsafe_allow_html=True)
    
    # 브리핑 박스 HTML
    briefing_html = f"""
    <div class='agentic-briefing-container'>
        <div class='briefing-header'>
            <div class='briefing-title'>
                🎯 오늘의 우선순위 액션
            </div>
            <div class='briefing-timestamp'>
                {briefing_data.get('generated_at', '')[:16].replace('T', ' ')}
            </div>
        </div>
        
        <div class='briefing-stats'>
            <div class='stat-item'>
                <div class='stat-value'>{stats.get('total_customers', 0)}</div>
                <div class='stat-label'>전체 고객</div>
            </div>
            <div class='stat-item'>
                <div class='stat-value'>{stats.get('active_policies', 0)}</div>
                <div class='stat-label'>활성 계약</div>
            </div>
            <div class='stat-item'>
                <div class='stat-value'>{stats.get('today_schedules', 0)}</div>
                <div class='stat-label'>오늘 일정</div>
            </div>
        </div>
        
        <div class='briefing-actions'>
    """
    
    if priority_actions:
        for action in priority_actions:
            icon = get_briefing_icon(action.get("type", ""))
            message = format_briefing_message(action)
            
            briefing_html += f"""
            <div class='action-card'>
                <div class='action-icon'>{icon}</div>
                <div class='action-content'>
                    <div class='action-message'>{message}</div>
                </div>
            </div>
            """
    else:
        briefing_html += """
        <div class='no-actions-message'>
            ✅ 현재 긴급한 액션이 없습니다. 좋은 하루 되세요!
        </div>
        """
    
    briefing_html += """
        </div>
    </div>
    """
    
    st.markdown(briefing_html, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# §2 12단계 세일즈 프로세스 진행 바
# ══════════════════════════════════════════════════════════════════════════════

# 12단계 세일즈 프로세스 정의
SALES_PROCESS_STEPS = [
    {"stage": 1, "name": "초기 접촉", "weapon": "명함·소개 자료"},
    {"stage": 2, "name": "니즈 파악", "weapon": "질문지·체크리스트"},
    {"stage": 3, "name": "정보 수집", "weapon": "스캔·OCR"},
    {"stage": 4, "name": "분석 진행", "weapon": "AI 분석 엔진"},
    {"stage": 5, "name": "리포트 작성", "weapon": "자동 보고서"},
    {"stage": 6, "name": "1차 제안", "weapon": "설계안·견적서"},
    {"stage": 7, "name": "이의 처리", "weapon": "FAQ·사례"},
    {"stage": 8, "name": "2차 제안", "weapon": "수정 설계안"},
    {"stage": 9, "name": "계약 준비", "weapon": "청약서·동의서"},
    {"stage": 10, "name": "계약 체결", "weapon": "전자 서명"},
    {"stage": 11, "name": "사후 관리", "weapon": "캘린더·알림"},
    {"stage": 12, "name": "재계약·추천", "weapon": "네트워크 맵"},
]


def render_12step_progress(
    current_stage: int = 1,
    customer_name: Optional[str] = None
) -> None:
    """
    12단계 세일즈 프로세스 진행 바 렌더링
    
    Args:
        current_stage: 현재 단계 (1-12)
        customer_name: 고객 이름 (선택)
    """
    # 진행률 계산
    progress_percent = int((current_stage / 12) * 100)
    
    # 현재 단계 정보
    current_step = next((s for s in SALES_PROCESS_STEPS if s["stage"] == current_stage), SALES_PROCESS_STEPS[0])
    
    # 다음 단계 정보
    next_step = next((s for s in SALES_PROCESS_STEPS if s["stage"] == current_stage + 1), None)
    
    # 진행 바 CSS
    progress_css = """
    <style>
    .sales-progress-container {
        background: var(--gp-bg-soft, #F9FAFB);
        border: 1px solid var(--gp-border-light, #D1D5DB);
        border-radius: var(--gp-radius, 8px);
        padding: calc(var(--gp-gap, 12px) * 1.5);
        margin-bottom: calc(var(--gp-gap, 12px) * 2);
    }
    .progress-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: var(--gp-gap, 12px);
        flex-wrap: wrap;
        gap: 8px;
    }
    .progress-title {
        font-size: clamp(15px, 2vw, 18px);
        font-weight: 900;
        color: var(--gp-text-dark, #1F2937);
    }
    .progress-percent {
        font-size: clamp(14px, 1.8vw, 16px);
        font-weight: 700;
        color: var(--gp-text, #4B5563);
    }
    .progress-bar-wrapper {
        width: 100%;
        height: 32px;
        background: var(--gp-border-light, #D1D5DB);
        border-radius: var(--gp-radius-sm, 6px);
        overflow: hidden;
        position: relative;
        margin-bottom: var(--gp-gap, 12px);
    }
    .progress-bar-fill {
        height: 100%;
        background: linear-gradient(
            90deg,
            var(--gp-success, #DCFCE7) 0%,
            var(--gp-block-base, #E0E7FF) 100%
        );
        transition: width 0.5s ease;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        padding-right: 12px;
    }
    .progress-stage-number {
        font-size: 14px;
        font-weight: 900;
        color: var(--gp-text-dark, #1F2937);
    }
    .progress-steps-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 8px;
        margin-bottom: var(--gp-gap, 12px);
    }
    .step-item {
        background: #ffffff;
        border: 1px solid var(--gp-border-light, #D1D5DB);
        border-radius: var(--gp-radius-sm, 6px);
        padding: 8px;
        text-align: center;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    .step-item.current {
        background: var(--gp-success, #DCFCE7);
        border-color: var(--gp-border, #374151);
        font-weight: 900;
    }
    .step-item.completed {
        background: var(--gp-bg-soft, #F9FAFB);
        opacity: 0.7;
    }
    .step-item:hover {
        border-color: var(--gp-border, #374151);
        transform: translateY(-1px);
    }
    .step-number {
        font-size: clamp(11px, 1.4vw, 13px);
        color: var(--gp-text-muted, #6B7280);
    }
    .step-name {
        font-size: clamp(12px, 1.5vw, 14px);
        color: var(--gp-text-dark, #1F2937);
        margin-top: 4px;
    }
    .next-weapon-info {
        background: var(--gp-warning, #FEE2E2);
        border: 1px solid var(--gp-border, #374151);
        border-radius: var(--gp-radius-sm, 6px);
        padding: var(--gp-gap, 12px);
        font-size: clamp(13px, 1.6vw, 15px);
        color: var(--gp-text-dark, #1F2937);
        line-height: 1.6;
    }
    @media (max-width: 768px) {
        .progress-steps-grid {
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
        }
    }
    </style>
    """
    
    st.markdown(progress_css, unsafe_allow_html=True)
    
    # 진행 바 HTML
    customer_display = f" - {customer_name}" if customer_name else ""
    
    progress_html = f"""
    <div class='sales-progress-container'>
        <div class='progress-header'>
            <div class='progress-title'>📊 세일즈 프로세스{customer_display}</div>
            <div class='progress-percent'>{progress_percent}% 완료</div>
        </div>
        
        <div class='progress-bar-wrapper'>
            <div class='progress-bar-fill' style='width: {progress_percent}%;'>
                <div class='progress-stage-number'>Step {current_stage}/12</div>
            </div>
        </div>
        
        <div class='progress-steps-grid'>
    """
    
    for step in SALES_PROCESS_STEPS:
        stage = step["stage"]
        name = step["name"]
        
        if stage < current_stage:
            css_class = "step-item completed"
        elif stage == current_stage:
            css_class = "step-item current"
        else:
            css_class = "step-item"
        
        progress_html += f"""
        <div class='{css_class}' title='{step["weapon"]}'>
            <div class='step-number'>Step {stage}</div>
            <div class='step-name'>{name}</div>
        </div>
        """
    
    progress_html += "</div>"
    
    # 다음 단계 무기 정보
    if next_step:
        progress_html += f"""
        <div class='next-weapon-info'>
            🎯 <b>다음 단계:</b> {next_step['name']}<br>
            🛡️ <b>핵심 무기:</b> {next_step['weapon']}
        </div>
        """
    else:
        progress_html += """
        <div class='next-weapon-info'>
            🎉 <b>모든 단계를 완료했습니다!</b> 재계약 및 추천 고객 발굴을 시작하세요.
        </div>
        """
    
    progress_html += "</div>"
    
    st.markdown(progress_html, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# §3 반응형 대시보드 그리드
# ══════════════════════════════════════════════════════════════════════════════

def render_dashboard_grid(cards: list) -> None:
    """
    반응형 대시보드 그리드 렌더링 (flex-wrap 기반)
    
    Args:
        cards: 카드 데이터 리스트
            [{"title": "제목", "value": "값", "icon": "🔥"}, ...]
    """
    # 그리드 CSS
    grid_css = """
    <style>
    .dashboard-grid {
        display: flex;
        flex-wrap: wrap;
        gap: var(--gp-gap, 12px);
        margin-bottom: calc(var(--gp-gap, 12px) * 2);
    }
    .dashboard-card {
        flex: 1 1 calc(33.333% - var(--gp-gap, 12px));
        min-width: 200px;
        background: #ffffff;
        border: 1px solid var(--gp-border-light, #D1D5DB);
        border-radius: var(--gp-radius, 8px);
        padding: calc(var(--gp-gap, 12px) * 1.5);
        transition: all 0.2s ease;
    }
    .dashboard-card:hover {
        border-color: var(--gp-border, #374151);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }
    .card-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: var(--gp-gap, 12px);
    }
    .card-icon {
        font-size: 28px;
    }
    .card-title {
        font-size: clamp(13px, 1.6vw, 15px);
        font-weight: 700;
        color: var(--gp-text, #4B5563);
    }
    .card-value {
        font-size: clamp(24px, 3.5vw, 32px);
        font-weight: 900;
        color: var(--gp-text-dark, #1F2937);
    }
    @media (max-width: 1024px) {
        .dashboard-card {
            flex: 1 1 calc(50% - var(--gp-gap, 12px));
        }
    }
    @media (max-width: 768px) {
        .dashboard-card {
            flex: 1 1 100%;
        }
    }
    </style>
    """
    
    st.markdown(grid_css, unsafe_allow_html=True)
    
    # 그리드 HTML
    grid_html = "<div class='dashboard-grid'>"
    
    for card in cards:
        grid_html += f"""
        <div class='dashboard-card'>
            <div class='card-header'>
                <div class='card-icon'>{card.get('icon', '📊')}</div>
                <div class='card-title'>{card.get('title', '제목 없음')}</div>
            </div>
            <div class='card-value'>{card.get('value', '0')}</div>
        </div>
        """
    
    grid_html += "</div>"
    
    st.markdown(grid_html, unsafe_allow_html=True)
