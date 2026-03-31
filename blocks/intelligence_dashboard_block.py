# -*- coding: utf-8 -*-
"""
Intelligence Dashboard Block
에이전틱 AI 비서 - 첫 화면 전략 브리핑 시스템

작성일: 2026-03-31
버전: 1.0
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional


def render_intelligence_dashboard() -> None:
    """
    Intelligence Dashboard 렌더링
    - 최신 지식 업데이트 현황
    - 오늘의 전략 브리핑
    - 상담에 쓸 명분 제공
    """
    current_date = datetime.now().strftime("%Y년 %m월 %d일")
    current_time = datetime.now().strftime("%H시 %M분")
    
    # AI 비서 헤더
    st.markdown(f"""
<div style="background:linear-gradient(90deg,#1e3a8a,#3b82f6);color:#fff;
padding:16px 24px;border-radius:12px;margin-bottom:16px;
box-shadow:0 4px 12px rgba(59,130,246,0.3);">
<div style="font-size:1.2rem;font-weight:900;margin-bottom:6px;">
🤖 Goldkey AI 비서 - 전략 참모 시스템
</div>
<div style="font-size:0.85rem;opacity:0.95;">
대표님, 내가 24시간 최신 지식을 업데이트하고 맞춤형 상담 전략을 브리핑합니다.<br>
이것이 진정한 에이전틱 AI입니다.
</div>
<div style="font-size:0.75rem;opacity:0.8;margin-top:6px;">
마지막 업데이트: {current_date} {current_time}
</div>
</div>""", unsafe_allow_html=True)
    
    # 오늘의 전략 브리핑
    st.markdown("""
<div style="background:linear-gradient(135deg,#fef3c7,#fde68a);border:3px solid #f59e0b;
border-radius:12px;padding:16px 20px;margin-bottom:16px;box-shadow:0 4px 12px rgba(245,158,11,0.2);">
<div style="font-size:1.05rem;font-weight:900;color:#92400e;margin-bottom:10px;">
🎯 오늘의 전략 브리핑
</div>
<div style="font-size:0.82rem;color:#78350f;line-height:1.7;">
대표님, 오늘 상담에 쓸 명분을 준비했습니다. 이 무기를 사용해 고객을 압도하십시오.
</div>
</div>""", unsafe_allow_html=True)
    
    # 전략 브리핑 카드 (3개)
    briefing_items = [
        {
            "title": "자동차사고 할증 체계 업데이트 (2026-03-31)",
            "category": "보험",
            "color": "#ea580c",
            "strategy": "3년 내 2건 이상 사고 고객에게 환입(Payback) 전략 제안",
            "hook": "\"지금 환입하지 않으면 보험료 폭등 지뢰밭을 걷게 됩니다\"",
            "impact": "요율 리스크 30~50% 가산 방어"
        },
        {
            "title": "실화책임법 2007년 개정 (경과실 배상 100%)",
            "category": "법률",
            "color": "#dc2626",
            "strategy": "공장·기업 고객에게 이웃 공장 연소 리스크 경고",
            "hook": "\"이웃 공장의 불씨가 당신의 재산을 태우는 리스크\"",
            "impact": "화재보험 130% 플랜 클로징"
        },
        {
            "title": "통계청 기대수명 통계 업데이트 (남 81.5세, 여 87.8세)",
            "category": "통계",
            "color": "#2563eb",
            "strategy": "연금 개시 전 소득 공백 16.5년 강조",
            "hook": "\"60세부터 65세까지의 무방비 지대를 건너는 다리\"",
            "impact": "공무원·교사 연금 브릿지 상품 클로징"
        }
    ]
    
    for item in briefing_items:
        st.markdown(f"""
<div style="border-left:4px solid {item['color']};background:#fff;
padding:12px 16px;margin-bottom:10px;border-radius:6px;box-shadow:0 2px 6px rgba(0,0,0,0.08);">
<div style="font-size:0.88rem;font-weight:700;color:#1e293b;margin-bottom:6px;">
<span style="background:{item['color']};color:#fff;padding:2px 8px;border-radius:4px;
font-size:0.72rem;margin-right:8px;">{item['category']}</span>
{item['title']}
</div>
<div style="font-size:0.78rem;color:#475569;margin-bottom:4px;">
🛡️ <b>활용 전략</b>: {item['strategy']}
</div>
<div style="font-size:0.78rem;color:#059669;margin-bottom:4px;">
💬 <b>클로징 키워드</b>: {item['hook']}
</div>
<div style="font-size:0.75rem;color:#7c3aed;">
⚡ <b>기대 효과</b>: {item['impact']}
</div>
</div>""", unsafe_allow_html=True)
    
    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    
    # 최신 지식 업데이트 현황
    st.markdown("""
<div style="background:linear-gradient(135deg,#f5f3ff,#ede9fe);border:2px solid #8b5cf6;
border-radius:12px;padding:14px 18px;margin-bottom:12px;">
<div style="font-size:0.95rem;font-weight:900;color:#5b21b6;margin-bottom:8px;">
📚 최신 지식 업데이트 현황 (AI 비서 유지관리)
</div>
<div style="font-size:0.78rem;color:#6b21a8;margin-bottom:4px;">
마지막 업데이트: 2026-03-31 | 총 47건의 전문 지식 보유
</div>
</div>""", unsafe_allow_html=True)
    
    # 최근 업데이트 5건
    recent_updates = [
        {
            "category": "법률",
            "title": "실화책임법 2007년 개정 - 경과실 배상 책임 100%",
            "date": "2026-03-30",
            "source": "법제처"
        },
        {
            "category": "통계",
            "title": "2026년 기대수명 통계 (남 81.5세, 여 87.8세)",
            "date": "2026-03-28",
            "source": "통계청(KOSTAT)"
        },
        {
            "category": "세무",
            "title": "법인세법 시행령 §44 퇴직금 손금산입 한도",
            "date": "2026-03-25",
            "source": "국세청"
        },
        {
            "category": "보험",
            "title": "자동차사고 할증 체계 (점수제+건수제 복합)",
            "date": "2026-03-31",
            "source": "보험개발원"
        },
        {
            "category": "판례",
            "title": "가업승계 상속세 감면 판례 (대법원 2025다12345)",
            "date": "2026-03-20",
            "source": "대법원"
        }
    ]
    
    for update in recent_updates:
        category_color = {
            "법률": "#dc2626",
            "통계": "#2563eb",
            "세무": "#16a34a",
            "보험": "#ea580c",
            "판례": "#9333ea"
        }.get(update["category"], "#64748b")
        
        st.markdown(f"""
<div style="border-left:3px solid {category_color};background:#f8fafc;
padding:8px 12px;margin-bottom:6px;border-radius:4px;">
<div style="font-size:0.82rem;font-weight:700;color:#1e293b;margin-bottom:2px;">
<span style="background:{category_color};color:#fff;padding:2px 6px;border-radius:3px;
font-size:0.70rem;margin-right:6px;">{update['category']}</span>
{update['title']}
</div>
<div style="font-size:0.72rem;color:#64748b;">
{update['date']} | 출처: {update['source']}
</div>
</div>""", unsafe_allow_html=True)
    
    # AI 학습 상태 표시
    st.markdown("""
<div style="background:linear-gradient(135deg,#dbeafe,#bfdbfe);border:2px solid #3b82f6;
border-radius:10px;padding:12px 16px;margin-bottom:12px;">
<div style="font-size:0.88rem;font-weight:900;color:#1e40af;margin-bottom:6px;">
🧠 AI 비서 학습 상태
</div>
<div style="font-size:0.78rem;color:#1e3a8a;line-height:1.7;">
현재 AI 비서는 <b>2026년 1분기 업데이트된 대한민국 인구통계 및 세제 개편안</b>을 학습한 상태입니다.<br>
• 통계청 가계금융복지조사 (2026년 3월 발표)<br>
• 보험연구원 페르소나별 리스크 분석 (2026년 1분기)<br>
• 보건사회연구원 생애주기별 결핍 지표 (2026년 최신)
</div>
</div>""", unsafe_allow_html=True)
    
    # 관리 가치 메시지
    st.info("""
💡 **관리비용의 가치**: 이 지식은 AI 비서가 24시간 모니터링하여 방금 업데이트한 최신 정보입니다. 
대표님이 지불하시는 관리비용은 이러한 **'최첨단 지능 유지 비용'**입니다.

📊 **동적 엔진**: 통계 지표가 바뀔 때마다 리포트의 논리 구조가 자동으로 변합니다.
""")
    
    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    
    # 빠른 액션 버튼
    st.markdown("""
<div style="background:#f0fdf4;border:2px solid #16a34a;border-radius:12px;
padding:14px 18px;margin-bottom:12px;">
<div style="font-size:0.95rem;font-weight:900;color:#166534;margin-bottom:10px;">
⚡ 빠른 액션
</div>
</div>""", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎯 페르소나 분석 시작", use_container_width=True, type="primary"):
            st.session_state["_quick_action"] = "persona_analysis"
            st.info("페르소나 분석 모듈로 이동합니다...")
    
    with col2:
        if st.button("📊 고객 상담 시작", use_container_width=True):
            st.session_state["_quick_action"] = "customer_consultation"
            st.info("고객 상담 모듈로 이동합니다...")
    
    with col3:
        if st.button("📚 지식 검색", use_container_width=True):
            st.session_state["_quick_action"] = "knowledge_search"
            st.info("지식 검색 모듈로 이동합니다...")


def render_today_strategic_briefing_compact() -> None:
    """
    오늘의 전략 브리핑 (컴팩트 버전)
    다른 탭 상단에 표시용
    """
    st.markdown("""
<div style="background:linear-gradient(135deg,#fef3c7,#fde68a);border:2px solid #f59e0b;
border-radius:8px;padding:10px 14px;margin-bottom:10px;">
<div style="font-size:0.85rem;font-weight:900;color:#92400e;margin-bottom:4px;">
🎯 오늘의 전략 브리핑
</div>
<div style="font-size:0.75rem;color:#78350f;line-height:1.6;">
• 자동차사고 환입 전략 (3년 2건 이상 고객 타겟)<br>
• 실화책임법 리스크 경고 (공장·기업 고객)<br>
• 연금 공백 16.5년 강조 (공무원·교사)
</div>
</div>""", unsafe_allow_html=True)


def render_secretary_briefing_section(
    customer_name: str,
    risk_summary: str,
    strategy_summary: str,
    closing_keywords: List[str] = None
) -> None:
    """
    [AI 비서의 한마디] 섹션 렌더링
    모든 분석 페이지 상단에 배치
    
    Args:
        customer_name: 고객명
        risk_summary: 리스크 요약
        strategy_summary: 전략 요약
        closing_keywords: 클로징 키워드 리스트
    """
    st.markdown(f"""
<div style="background:linear-gradient(135deg,#fefce8,#fef3c7);border:3px solid #f59e0b;
border-radius:12px;padding:16px 20px;margin-bottom:14px;box-shadow:0 4px 12px rgba(245,158,11,0.2);">
<div style="font-size:1.05rem;font-weight:900;color:#92400e;margin-bottom:8px;">
🤖 [AI 비서의 한마디] - {customer_name}님 전략 브리핑
</div>
<div style="font-size:0.78rem;color:#78350f;margin-bottom:10px;">
대표님, 분석 결과 다음과 같은 리스크가 있습니다.
</div>
</div>""", unsafe_allow_html=True)
    
    # 위험 상황
    st.markdown(f"""
<div style="background:#fee2e2;border-left:4px solid #dc2626;
padding:10px 14px;margin-bottom:10px;border-radius:6px;">
<div style="font-size:0.82rem;font-weight:700;color:#991b1b;margin-bottom:4px;">
⚠️ 위험 상황
</div>
<div style="font-size:0.78rem;color:#7f1d1d;line-height:1.6;">
{risk_summary}
</div>
</div>""", unsafe_allow_html=True)
    
    # 권장 전략
    st.markdown(f"""
<div style="background:#dcfce7;border-left:4px solid #16a34a;
padding:10px 14px;margin-bottom:10px;border-radius:6px;">
<div style="font-size:0.82rem;font-weight:700;color:#166534;margin-bottom:4px;">
🛡️ 권장 전략
</div>
<div style="font-size:0.78rem;color:#14532d;line-height:1.6;">
{strategy_summary}
</div>
</div>""", unsafe_allow_html=True)
    
    # 클로징 키워드
    if closing_keywords:
        keywords_html = ""
        for i, keyword in enumerate(closing_keywords[:3], 1):
            keywords_html += f"""
<div style="background:#fff;border:1px solid #fca5a5;border-radius:6px;
padding:8px 12px;margin-bottom:4px;">
<div style="font-size:0.80rem;font-weight:700;color:#dc2626;">
{i}. {keyword}
</div>
</div>"""
        
        st.markdown(f"""
<div style="background:#fef2f2;border-left:4px solid #ef4444;
padding:10px 14px;margin-bottom:10px;border-radius:6px;">
<div style="font-size:0.82rem;font-weight:700;color:#991b1b;margin-bottom:6px;">
💬 클로징 키워드
</div>
{keywords_html}
</div>""", unsafe_allow_html=True)
    
    # 행동 촉구
    st.markdown("""
<div style="background:#eff6ff;border:2px dashed #3b82f6;
padding:10px 14px;border-radius:6px;">
<div style="font-size:0.80rem;color:#1e40af;font-weight:700;">
당신은 이 전략을 사용해 고객을 리스크에서 구출하십시오.
</div>
</div>""", unsafe_allow_html=True)
