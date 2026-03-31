# -*- coding: utf-8 -*-
"""
에이전틱 브리핑 블록 (Agentic Briefing Block)
AI 비서의 전략적 상담 가이드 UI 컴포넌트

작성일: 2026-03-31
버전: 1.0
"""

import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime


def render_persona_quick_selector() -> Dict:
    """
    고객 페르소나 퀵 선택 모듈
    
    Returns:
        dict: 선택된 페르소나 정보
    """
    st.markdown("""
<div style="background:linear-gradient(135deg,#f0f9ff,#e0f2fe);border:2px solid #0284c7;
border-radius:12px;padding:14px 18px;margin-bottom:12px;">
<div style="font-size:0.95rem;font-weight:900;color:#0c4a6e;margin-bottom:8px;">
🤖 AI 비서 활성화 - 고객 페르소나 입력
</div>
<div style="font-size:0.80rem;color:#075985;line-height:1.7;">
고객 정보를 입력하시면 AI 비서가 맞춤형 상담 전략을 즉시 브리핑합니다.<br>
통계청·보험연구원·보건사회연구원 2026년 최신 데이터 기반 분석
</div>
</div>""", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        customer_name = st.text_input(
            "고객명",
            value=st.session_state.get("_persona_customer_name", ""),
            key="_persona_customer_name_input",
            placeholder="홍길동"
        )
        
        age = st.number_input(
            "나이",
            min_value=20,
            max_value=100,
            value=st.session_state.get("_persona_age", 35),
            step=1,
            key="_persona_age_input"
        )
    
    with col2:
        occupation = st.selectbox(
            "직업",
            options=[
                "회사원", "공무원", "교사", "군인", "경찰/소방",
                "사업가", "대표이사", "전문직(의사/변호사/회계사)",
                "생산직", "현장직", "기술직", "운전직",
                "자영업", "프리랜서", "주부", "학생", "기타"
            ],
            index=0,
            key="_persona_occupation_input"
        )
        
        family_type = st.selectbox(
            "가족 형태",
            options=["핵가족", "대가족", "1인가구", "독신", "비혼", "신혼"],
            index=0,
            key="_persona_family_type_input"
        )
    
    with col3:
        interests = st.multiselect(
            "관심사/성향",
            options=[
                "사회봉사", "개인화", "가성비", "가심비",
                "안정성", "수익성", "체면/명예", "자유/독립",
                "가족 중심", "자기 관리", "반려동물"
            ],
            default=st.session_state.get("_persona_interests", []),
            key="_persona_interests_input"
        )
        
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        
        activate_briefing = st.button(
            "🚀 AI 비서 브리핑 생성",
            type="primary",
            use_container_width=True,
            key="_persona_activate_briefing"
        )
    
    # 세션 상태 업데이트
    if activate_briefing:
        st.session_state["_persona_customer_name"] = customer_name
        st.session_state["_persona_age"] = age
        st.session_state["_persona_occupation"] = occupation
        st.session_state["_persona_family_type"] = family_type
        st.session_state["_persona_interests"] = interests
        st.session_state["_persona_briefing_activated"] = True
    
    return {
        "customer_name": customer_name,
        "age": age,
        "occupation": occupation,
        "family_type": family_type,
        "interests": interests,
        "activated": activate_briefing or st.session_state.get("_persona_briefing_activated", False)
    }


def render_agentic_briefing(
    customer_name: str,
    persona_key: str,
    briefing_markdown: str
) -> None:
    """
    에이전틱 브리핑 렌더링
    
    Args:
        customer_name: 고객명
        persona_key: 페르소나 키
        briefing_markdown: 브리핑 마크다운 텍스트
    """
    st.markdown("""
<div style="background:linear-gradient(135deg,#fefce8,#fef3c7);border:3px solid #f59e0b;
border-radius:12px;padding:16px 20px;margin-bottom:14px;box-shadow:0 4px 12px rgba(245,158,11,0.2);">
<div style="font-size:1.05rem;font-weight:900;color:#92400e;margin-bottom:4px;">
🤖 [AI 비서의 한마디] - 설계사님께 드리는 전략 브리핑
</div>
<div style="font-size:0.78rem;color:#78350f;margin-bottom:8px;">
이 브리핑은 설계사님의 명령을 받아 AI 비서가 정밀하게 작성한 전문 보고서입니다.
</div>
</div>""", unsafe_allow_html=True)
    
    # 브리핑 내용 렌더링
    st.markdown(briefing_markdown, unsafe_allow_html=True)
    
    # 관리 가치 시각화
    st.markdown("""
<div style="background:#f0fdf4;border:1px dashed #16a34a;border-radius:8px;
padding:10px 14px;margin-top:12px;">
<div style="font-size:0.80rem;color:#166534;line-height:1.6;">
💡 <b>관리비용의 가치</b>: 이 지식은 통계청 2026년 최신 보고서를 기반으로 
AI 비서가 <b>방금 업데이트</b>한 내용입니다. 설계사님이 지불하시는 관리비용은 
이러한 <b>'최첨단 지능 유지 비용'</b>입니다.
</div>
</div>""", unsafe_allow_html=True)


def render_knowledge_update_dashboard(update_data: Dict) -> None:
    """
    지식 업데이트 현황 대시보드
    
    Args:
        update_data: 업데이트 현황 데이터
    """
    st.markdown("""
<div style="background:linear-gradient(135deg,#f5f3ff,#ede9fe);border:2px solid #8b5cf6;
border-radius:12px;padding:14px 18px;margin-bottom:12px;">
<div style="font-size:0.95rem;font-weight:900;color:#5b21b6;margin-bottom:8px;">
📚 최신 지식 업데이트 현황 (AI 비서 유지관리)
</div>
<div style="font-size:0.78rem;color:#6b21a8;margin-bottom:4px;">
마지막 업데이트: {last_update} | 총 {total} 건의 전문 지식 보유
</div>
</div>""".format(
        last_update=update_data.get("last_update", "2026-03-31"),
        total=update_data.get("total_knowledge_items", 47)
    ), unsafe_allow_html=True)
    
    st.markdown("**최근 업데이트된 지식 (최신 5건)**")
    
    for update in update_data.get("recent_updates", [])[:5]:
        category_color = {
            "법률": "#dc2626",
            "통계": "#2563eb",
            "세무": "#16a34a",
            "보험": "#ea580c",
            "판례": "#9333ea"
        }.get(update.get("category", "기타"), "#64748b")
        
        st.markdown(f"""
<div style="border-left:3px solid {category_color};background:#f8fafc;
padding:8px 12px;margin-bottom:6px;border-radius:4px;">
<div style="font-size:0.82rem;font-weight:700;color:#1e293b;margin-bottom:2px;">
<span style="background:{category_color};color:#fff;padding:2px 6px;border-radius:3px;
font-size:0.70rem;margin-right:6px;">{update.get("category", "기타")}</span>
{update.get("title", "")}
</div>
<div style="font-size:0.72rem;color:#64748b;">
{update.get("date", "")} | 출처: {update.get("source", "")}
</div>
</div>""", unsafe_allow_html=True)
    
    # 관리 가치 메시지
    st.info(update_data.get("maintenance_value_message", ""))


def render_closing_keywords_guide(keywords: List[str], persona_name: str) -> None:
    """
    맞춤형 클로징 키워드 가이드
    
    Args:
        keywords: 클로징 키워드 리스트
        persona_name: 페르소나 이름
    """
    st.markdown(f"""
<div style="background:linear-gradient(135deg,#fef2f2,#fee2e2);border:2px solid #ef4444;
border-radius:12px;padding:14px 18px;margin-bottom:12px;">
<div style="font-size:0.95rem;font-weight:900;color:#991b1b;margin-bottom:8px;">
💬 맞춤형 클로징 키워드 ({persona_name})
</div>
<div style="font-size:0.80rem;color:#7f1d1d;line-height:1.7;">
이 고객님께 가장 효과적인 언어 3가지를 AI 비서가 제안합니다:
</div>
</div>""", unsafe_allow_html=True)
    
    for i, keyword in enumerate(keywords[:3], 1):
        st.markdown(f"""
<div style="background:#fff;border:1px solid #fca5a5;border-radius:8px;
padding:10px 14px;margin-bottom:6px;">
<div style="font-size:0.85rem;font-weight:700;color:#dc2626;">
{i}. {keyword}
</div>
</div>""", unsafe_allow_html=True)
    
    st.caption("💡 상담 시 이 키워드를 자연스럽게 녹여내면 고객의 공감도가 극대화됩니다.")


def render_ai_secretary_header() -> None:
    """
    AI 비서 헤더 - 앱 상단에 표시
    """
    st.markdown("""
<div style="background:linear-gradient(90deg,#1e3a8a,#3b82f6);color:#fff;
padding:12px 20px;border-radius:8px;margin-bottom:14px;
box-shadow:0 4px 12px rgba(59,130,246,0.3);">
<div style="font-size:1.1rem;font-weight:900;margin-bottom:4px;">
🤖 Goldkey AI 비서 - 설계사 전용 에이전틱 지능 시스템
</div>
<div style="font-size:0.78rem;opacity:0.9;">
설계사님의 명령을 받아 AI 비서가 24시간 최신 지식을 업데이트하고 
맞춤형 상담 전략을 브리핑합니다. 이것이 진정한 에이전틱 AI입니다.
</div>
</div>""", unsafe_allow_html=True)
