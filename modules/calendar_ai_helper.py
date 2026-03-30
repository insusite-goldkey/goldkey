# ══════════════════════════════════════════════════════════════════════════════
# [MODULE] calendar_ai_helper.py
# STEP 11 하이브리드: 프로 전용 AI 전략 브리핑 및 맞춤 작문 엔진
# 2026-03-30 신규 생성 - GP 마스터플랜 등급 체계
# ══════════════════════════════════════════════════════════════════════════════

from typing import Optional, Dict, Any
import streamlit as st
from db_utils import _get_sb
import random


# ══════════════════════════════════════════════════════════════════════════════
# [§AUDIT] AI 상담 점검 엔진 (3단계 전문가 검증)
# ══════════════════════════════════════════════════════════════════════════════

def _run_ai_audit(user_id: str, customer_name: str, person_id: Optional[str], event_date: str) -> None:
    """
    AI 상담 점검 실행 - 3단계 전문가 검증.
    
    점검 항목:
    1. 이전 상담 메모 분석
    2. 트리니티 기반 보장 공백 재확인
    3. 업셀링(Up-selling) 가능성 도출
    
    Args:
        user_id: 설계사 ID
        customer_name: 고객 이름
        person_id: 고객 person_id
        event_date: 일정 날짜
    """
    with st.spinner("🔍 AI가 상담 이력을 정밀 점검 중입니다..."):
        # TODO: 실제 DB 조회 및 AI 분석 로직 연동
        # 현재는 시뮬레이션 데이터 사용
        
        # STEP 1: 이전 상담 메모 분석
        memo_analysis = _analyze_consultation_memo(person_id)
        
        # STEP 2: 트리니티 기반 보장 공백 재확인
        gap_analysis = _check_coverage_gap(person_id)
        
        # STEP 3: 업셀링 가능성 도출
        upsell_potential = _calculate_upsell_potential(memo_analysis, gap_analysis)
        
        # 컴팩트 카드 UI 렌더링
        _render_audit_result_card(customer_name, memo_analysis, gap_analysis, upsell_potential)


def _analyze_consultation_memo(person_id: Optional[str]) -> Dict[str, Any]:
    """
    이전 상담 메모 분석.
    
    Returns:
        {
            "last_contact": str,
            "main_concerns": list,
            "follow_up_needed": bool
        }
    """
    # TODO: 실제 DB 조회
    return {
        "last_contact": "2026-03-15",
        "main_concerns": ["암보험 보장 부족", "실손보험 갱신"],
        "follow_up_needed": True
    }


def _check_coverage_gap(person_id: Optional[str]) -> Dict[str, Any]:
    """
    트리니티 기반 보장 공백 재확인.
    
    Returns:
        {
            "critical_gaps": list,
            "severity": str,
            "recommendation": str
        }
    """
    # TODO: 실제 트리니티 엔진 연동
    gaps = [
        {"type": "암보장", "current": "3천만원", "recommended": "1억원", "gap": "7천만원"},
        {"type": "뇌/심장질환", "current": "1천만원", "recommended": "4천만원", "gap": "3천만원"}
    ]
    
    return {
        "critical_gaps": gaps,
        "severity": "높음",
        "recommendation": "암 보장 대비 뇌/심장 질환 가입 금액이 낮아 실무적 보완이 시급합니다."
    }


def _calculate_upsell_potential(memo: Dict, gap: Dict) -> Dict[str, Any]:
    """
    업셀링 가능성 도출.
    
    Returns:
        {
            "score": int (0-100),
            "priority_products": list,
            "optimal_approach": str
        }
    """
    # TODO: 실제 AI 분석 로직
    score = random.randint(70, 95)
    
    return {
        "score": score,
        "priority_products": ["뇌/심장질환 보험", "CI(Critical Illness) 보험"],
        "optimal_approach": "기존 암보험 보완 → 뇌/심장 추가 제안 순서로 진행"
    }


def _render_audit_result_card(
    customer_name: str,
    memo: Dict,
    gap: Dict,
    upsell: Dict
) -> None:
    """
    [GP-STEP11] AI 상담 점검 리포트 출력 - A4 1장 최적화 전문가용 디자인.
    딥블루(#1e3a8a) + 라이트골드(#fbbf24) 컬러 스킴.
    """
    # A4 1장 최적화 컴팩트 병렬 레이아웃
    st.markdown(
        "<div style='max-width:800px;margin:20px auto;background:#fff;"
        "border:3px solid #1e3a8a;border-radius:16px;padding:24px;"
        "box-shadow:0 8px 24px rgba(30,58,138,0.2);'>"
        
        # 헤더: 에이젠틱 AI 전문가용 리포트
        "<div style='text-align:center;margin-bottom:20px;'>"
        "<div style='background:linear-gradient(135deg,#1e3a8a,#3b82f6);"
        "color:#fff;padding:16px;border-radius:12px;'>"
        "<h2 style='margin:0;font-size:1.4rem;font-weight:900;'>"
        "🤖 에이젠틱 AI 전문가용 상담 점검 리포트</h2>"
        f"<div style='font-size:0.9rem;margin-top:8px;opacity:0.95;'>"
        f"고객: <b>{customer_name}</b>님 | 점검일: {memo['last_contact']}</div>"
        "</div></div>"
        
        # 병렬 레이아웃: 좌측(가입 항목) + 우측(보장 공백)
        "<div style='display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px;'>"
        
        # 좌측: 가입 항목 점검
        "<div style='background:linear-gradient(135deg,#f0f9ff,#e0f2fe);"
        "border:2px solid #3b82f6;border-radius:12px;padding:16px;'>"
        "<div style='font-size:1rem;font-weight:900;color:#1e40af;margin-bottom:12px;'>"
        "✅ 가입 항목 점검</div>"
        "<div style='font-size:0.82rem;color:#1e3a8a;line-height:1.7;'>",
        unsafe_allow_html=True
    )
    
    # 가입 항목 상세 (시뮬레이션 데이터)
    holdings = [
        {"icon": "🏥", "name": "실손의료비", "amount": "5천만원"},
        {"icon": "🎗️", "name": "암보험", "amount": "3천만원"},
        {"icon": "💊", "name": "CI보험", "amount": "1천만원"}
    ]
    
    for h in holdings:
        st.markdown(
            f"<div style='margin-bottom:8px;padding:8px;background:#fff;"
            f"border-radius:6px;border-left:3px solid #3b82f6;'>"
            f"<b>{h['icon']} {h['name']}</b><br>"
            f"<span style='color:#0369a1;font-weight:700;font-size:0.95rem;'>{h['amount']}</span></div>",
            unsafe_allow_html=True
        )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 우측: 보장 공백 진단
    st.markdown(
        "<div style='background:linear-gradient(135deg,#fef3c7,#fde68a);"
        "border:2px solid #fbbf24;border-radius:12px;padding:16px;'>"
        "<div style='font-size:1rem;font-weight:900;color:#92400e;margin-bottom:12px;'>"
        f"⚠️ 보장 공백 진단 (심각도: <span style='color:#dc2626;'>{gap['severity']}</span>)</div>"
        "<div style='font-size:0.82rem;color:#78350f;line-height:1.7;'>",
        unsafe_allow_html=True
    )
    
    # 보장 공백 상세 (퍼센티지 그래프)
    for g in gap["critical_gaps"]:
        # 부족률 계산 (시뮬레이션)
        current_val = int(g['current'].replace('천만원', '000').replace('만원', ''))
        recommended_val = int(g['recommended'].replace('억원', '0000').replace('천만원', '000'))
        gap_percent = int((1 - current_val / recommended_val) * 100) if recommended_val > 0 else 0
        
        st.markdown(
            f"<div style='margin-bottom:10px;'>"
            f"<div style='font-weight:700;color:#92400e;margin-bottom:4px;'>{g['type']}</div>"
            f"<div style='background:#fff;border-radius:6px;height:20px;position:relative;overflow:hidden;'>"
            f"<div style='background:linear-gradient(90deg,#dc2626,#f59e0b);height:100%;"
            f"width:{gap_percent}%;border-radius:6px;'></div>"
            f"<div style='position:absolute;top:0;left:0;right:0;bottom:0;"
            f"display:flex;align-items:center;justify-content:center;"
            f"font-size:0.75rem;font-weight:700;color:#1f2937;'>"
            f"부족률: {gap_percent}%</div></div>"
            f"<div style='font-size:0.75rem;color:#a16207;margin-top:2px;'>"
            f"현재 {g['current']} → 권장 {g['recommended']}</div></div>",
            unsafe_allow_html=True
        )
    
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    # 하단: 최적 제안 포인트 (조사 생략형 핵심 명사 문구)
    st.markdown(
        "<div style='background:linear-gradient(135deg,#f0fdf4,#dcfce7);"
        "border:2px solid #10b981;border-radius:12px;padding:16px;margin-top:16px;'>"
        "<div style='font-size:1rem;font-weight:900;color:#065f46;margin-bottom:10px;'>"
        f"� 최적 제안 포인트 (업셀링 가능성: <span style='color:#dc2626;font-size:1.2rem;'>{upsell['score']}점</span>/100)</div>"
        "<div style='font-size:0.88rem;color:#064e3b;line-height:1.8;'>",
        unsafe_allow_html=True
    )
    
    # 조사 생략형 핵심 명사 문구
    key_points = [
        f"<b style='color:#0369a1;'>뇌혈관 질환 특약</b> 제안 요망",
        f"<b style='color:#0369a1;'>심장질환 보장</b> 추가 검토 필요",
        f"기존 암보험 보완 → <b style='color:#0369a1;'>CI보험 추가</b> 순서 진행",
        f"<b style='color:#dc2626;'>실무적 보완 시급</b> (현재 대비 권장 보장액 70% 부족)"
    ]
    
    for point in key_points:
        st.markdown(
            f"<div style='margin-bottom:6px;padding-left:12px;border-left:3px solid #10b981;'>"
            f"• {point}</div>",
            unsafe_allow_html=True
        )
    
    st.markdown(
        f"<div style='margin-top:12px;padding:10px;background:#fff;border-radius:8px;"
        f"border:1px dashed #10b981;'>"
        f"<div style='font-size:0.85rem;color:#065f46;font-weight:700;'>"
        f"📋 최적 접근법</div>"
        f"<div style='font-size:0.82rem;color:#047857;margin-top:4px;'>"
        f"{upsell['optimal_approach']}</div></div>"
        "</div>"
        
        # 푸터: 에이젠틱 AI 브랜딩
        "<div style='text-align:center;margin-top:20px;padding-top:16px;"
        "border-top:2px dashed #d1d5db;'>"
        "<div style='font-size:0.75rem;color:#6b7280;'>"
        "🤖 <b>Powered by Goldkey Agentic AI</b> | 전문가다운 완벽한 상담 준비</div>"
        "</div>"
        
        "</div>",
        unsafe_allow_html=True
    )
    
    # 코인 차감 안내
    st.success("✅ **AI 점검 리포트 출력 완료** (3코인 차감) - 상담 직전 참고 자료로 활용하세요.")


def check_pro_tier(user_id: str) -> bool:
    """
    프로 등급 여부 확인.
    
    Args:
        user_id: 회원 ID
        
    Returns:
        True: 프로 등급 (subscription_status == "active" or current_credits >= 150)
        False: 베이직 등급
    """
    sb = _get_sb()
    if not sb or not user_id:
        return False
    
    try:
        resp = sb.table("gk_members").select("subscription_status, current_credits").eq("user_id", user_id).execute()
        if not resp.data:
            return False
        
        member = resp.data[0]
        status = member.get("subscription_status", "")
        credits = member.get("current_credits", 0)
        
        # 프로 조건: 구독 활성 또는 150코인 이상 보유
        return status == "active" or credits >= 150
    except Exception:
        return False


def render_pro_upsell_tooltip(feature_name: str = "AI 맞춤 작문", customer_name: str = "") -> None:
    """
    [GP-STEP11] 프로 기능 업셀링 말풍선 (Speech Bubble).
    
    Args:
        feature_name: 기능 이름
        customer_name: 고객 이름 (STEP 11 하이브리드용)
    """
    # STEP 11 하이브리드: 고객명이 있으면 특화된 마케팅 넛지
    if customer_name and "AI" in feature_name:
        from modules.access_control import render_step11_marketing_nudge
        render_step11_marketing_nudge(customer_name)
        return
    
    # 일반 업셀링 팝업
    st.markdown(
        f"<div style='background:linear-gradient(135deg,#fef3c7,#fde68a);"
        f"border:2px solid #f59e0b;border-radius:12px;padding:16px 20px;"
        f"margin:12px 0;box-shadow:0 4px 12px rgba(245,158,11,0.2);'>"
        f"<div style='font-size:1.05rem;font-weight:900;color:#92400e;margin-bottom:8px;'>"
        f"🚀 PRO 전용 기능: {feature_name}</div>"
        f"<div style='font-size:0.88rem;color:#78350f;line-height:1.6;margin-bottom:12px;'>"
        f"지금 프로로 업그레이드 하시면 이 고객님께 보낼 <b style='color:#b45309;'>감동적인 안부 카톡</b>을 "
        f"AI가 대신 써드립니다!<br>"
        f"<span style='font-size:0.82rem;color:#a16207;'>✨ 현재 300코인 즉시 지급 이벤트 중</span></div>"
        f"<div style='text-align:center;'>"
        f"<a href='#' style='display:inline-block;background:linear-gradient(135deg,#f59e0b,#d97706);"
        f"color:#fff;padding:10px 24px;border-radius:8px;text-decoration:none;"
        f"font-weight:700;font-size:0.9rem;box-shadow:0 2px 8px rgba(217,119,6,0.3);'>"
        f"💎 프로로 업그레이드 하기</a></div>"
        f"</div>",
        unsafe_allow_html=True
    )


def render_ai_strategy_briefing(
    user_id: str,
    customer_name: str,
    event_date: str,
    event_type: str = "상담일정",
    person_id: Optional[str] = None,
) -> None:
    """
    [⭐프로전용] AI 상담 점검 시스템 - 3단계 전문가 검증.
    
    Args:
        user_id: 설계사 ID
        customer_name: 고객 이름
        event_date: 일정 날짜
        event_type: 일정 유형
        person_id: 고객 person_id (선택)
    """
    # 프로 등급 확인
    if not check_pro_tier(user_id):
        render_pro_upsell_tooltip("AI 상담 점검", customer_name=customer_name)
        return
    
    # 프로 전용 헤더
    st.markdown(
        f"<div style='background:linear-gradient(135deg,#dbeafe,#bfdbfe);"
        f"border:2px solid #3b82f6;border-radius:12px;padding:16px;margin:12px 0;'>"
        f"<div style='font-size:1rem;font-weight:900;color:#1e40af;margin-bottom:8px;'>"
        f"🤖 AI 상담 점검 시스템 <span style='background:#3b82f6;color:#fff;padding:2px 8px;"
        f"border-radius:6px;font-size:0.75rem;margin-left:6px;'>⭐프로전용</span></div>"
        f"<div style='font-size:0.85rem;color:#1e3a8a;margin-bottom:10px;'>"
        f"고객: <b>{customer_name}</b> | 일정: {event_date} ({event_type})</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    # AI 상담 점검 버튼
    if st.button(
        "� AI 상담 점검 실행 (3코인 차감)",
        key=f"ai_audit_{event_date}_{customer_name}",
        use_container_width=True,
        help="이전 상담 메모 분석 → 보장 공백 재확인 → 업셀링 가능성 도출",
        type="primary"
    ):
        _run_ai_audit(user_id, customer_name, person_id, event_date)
