"""
crm_proposal_ui.py — AI 감성 세일즈 제안서 칵핏 UI
[GP-STEP8] Goldkey AI Masters 2026

제안서 칵핏 UI:
- 비주얼 리포트 (현재 보장 vs 제안 보장)
- 3가지 플랜 탭 (실속/표준/VIP)
- 감성 스크립트 선택기 (전문적/감성적/직설적)
- 모바일 전용 요약 제안서
"""
from __future__ import annotations
import re, json, datetime
from typing import Optional, Dict, Any, List
import streamlit as st

# ══════════════════════════════════════════════════════════════════════════════
# [1] 제안서 생성 메인 UI
# ══════════════════════════════════════════════════════════════════════════════

def render_proposal_cockpit(person_id: str, agent_id: str, customer_name: str = ""):
    """
    제안서 칵핏 메인 UI
    
    Args:
        person_id: 고객 UUID
        agent_id: 설계사 ID
        customer_name: 고객 이름
    """
    st.markdown(
        f"<div style='font-size:1.2rem;font-weight:900;color:#1E3A8A;margin-bottom:16px;'>"
        f"🧠 AI 감성 세일즈 제안서 — {customer_name}</div>",
        unsafe_allow_html=True
    )
    
    # 제안서 생성 버튼
    if st.button("🚀 AI 제안서 생성", key=f"generate_proposal_{person_id}", use_container_width=True):
        with st.spinner("AI가 제안서를 생성 중입니다..."):
            from hq_proposal_engine import generate_proposal, save_proposal_to_db, update_customer_stage_to_proposal
            
            proposal_data = generate_proposal(person_id, agent_id)
            
            if proposal_data.get("success"):
                # 세션에 저장
                st.session_state[f"proposal_{person_id}"] = proposal_data
                
                # DB 저장
                save_proposal_to_db(proposal_data, person_id, agent_id)
                
                # 에이전틱 단계 업데이트 (4단계 → 5단계)
                update_customer_stage_to_proposal(person_id, agent_id, target_stage=5)
                
                st.success("✅ AI 제안서가 생성되었습니다!")
                st.rerun()
            else:
                st.error(f"❌ 제안서 생성 실패: {proposal_data.get('error', '알 수 없는 오류')}")
    
    # 기존 제안서 표시
    proposal_data = st.session_state.get(f"proposal_{person_id}")
    
    if not proposal_data:
        st.info("💡 '🚀 AI 제안서 생성' 버튼을 클릭하여 맞춤형 제안서를 생성하세요.")
        return
    
    # 제안서 UI 렌더링
    render_proposal_content(proposal_data, person_id, agent_id)


# ══════════════════════════════════════════════════════════════════════════════
# [2] 제안서 콘텐츠 렌더링
# ══════════════════════════════════════════════════════════════════════════════

def render_proposal_content(proposal_data: Dict[str, Any], person_id: str, agent_id: str):
    """
    제안서 콘텐츠 렌더링
    
    Args:
        proposal_data: 제안서 데이터
        person_id: 고객 UUID
        agent_id: 설계사 ID
    """
    # 1. 보장 공백 분석 비주얼 리포트
    render_gap_analysis_visual(proposal_data.get("gap_analysis", {}))
    
    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
    
    # 2. 3가지 플랜 탭
    render_three_plans_tabs(proposal_data.get("three_plans", []))
    
    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
    
    # 3. ADLs 25% 통곡의 벽 시뮬레이터 (PSP-02 Step 2)
    render_adls_wall_simulator(person_id)
    
    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
    
    # 4. 트리니티 가처분 소득 결손 차트 (PSP-02 Step 3)
    render_trinity_income_loss_charts(person_id)
    
    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
    
    # 5. 감성 스크립트 선택기
    render_emotional_scripts_selector(proposal_data.get("emotional_scripts", {}))
    
    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
    
    # 6. 모바일 전용 요약 제안서
    render_mobile_summary(proposal_data, person_id)


# ══════════════════════════════════════════════════════════════════════════════
# [3] 보장 공백 분석 비주얼 리포트
# ══════════════════════════════════════════════════════════════════════════════

def render_gap_analysis_visual(gap_analysis: Dict[str, Any]):
    """
    보장 공백 분석 비주얼 리포트
    
    Args:
        gap_analysis: 보장 공백 분석 결과
    """
    st.markdown(
        "<div style='font-size:1.05rem;font-weight:900;color:#1E3A8A;margin-bottom:12px;'>"
        "📊 보장 공백 분석 (Gap Analysis)</div>",
        unsafe_allow_html=True
    )
    
    current_coverage = gap_analysis.get("current_coverage", {})
    total_premium = gap_analysis.get("total_premium", 0)
    gaps = gap_analysis.get("gaps", [])
    
    # 현재 보장 vs 권장 보장 비교 차트
    col1, col2 = st.columns(2, gap="medium")
    
    with col1:
        st.markdown(
            "<div style='background:#FEE2E2;border:1.5px solid #EF4444;border-radius:10px;padding:14px;'>"
            "<div style='font-size:.88rem;font-weight:700;color:#991B1B;margin-bottom:8px;'>현재 보장 (Red)</div>",
            unsafe_allow_html=True
        )
        
        for coverage_type, count in current_coverage.items():
            st.markdown(
                f"<div style='font-size:.82rem;color:#7F1D1D;margin-bottom:4px;'>"
                f"• {coverage_type}: {count}건</div>",
                unsafe_allow_html=True
            )
        
        st.markdown(
            f"<div style='font-size:.85rem;font-weight:700;color:#991B1B;margin-top:8px;'>"
            f"월 보험료: {int(total_premium):,}원</div>"
            "</div>",
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            "<div style='background:#DCFCE7;border:1.5px solid #22C55E;border-radius:10px;padding:14px;'>"
            "<div style='font-size:.88rem;font-weight:700;color:#166534;margin-bottom:8px;'>필요 보장 (Green)</div>",
            unsafe_allow_html=True
        )
        
        # [GP-PSP-01] 표적항암 최소 기준 7천만원 반영
        # 암보험 공백 시 최소 기준 표시
        cancer_gap = next((g for g in gaps if g.get("type") == "암보험"), None)
        
        if cancer_gap:
            st.markdown(
                f"<div style='font-size:.82rem;color:#14532D;margin-bottom:4px;'>"
                f"• 암보험: 표준 진단비 + 표적항암 치료비 (최소 7천만원) ✅</div>",
                unsafe_allow_html=True
            )
        
        # 기타 보장 표시
        for gap in gaps:
            if gap.get("type") != "암보험":
                st.markdown(
                    f"<div style='font-size:.82rem;color:#14532D;margin-bottom:4px;'>"
                    f"• {gap.get('type', '')}: 권장 보장 ✅</div>",
                    unsafe_allow_html=True
                )
        
        st.markdown(
            f"<div style='font-size:.85rem;font-weight:700;color:#166534;margin-top:8px;'>"
            f"월 보험료: {int(total_premium * 1.5):,}원 (예상)</div>"
            "</div>",
            unsafe_allow_html=True
        )
    
    # 보장 공백 알림 (치료비 상세 포함)
    if gaps:
        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
        
        for gap in gaps:
            severity_color = "#DC2626" if gap.get("severity") == "critical" else ("#EF4444" if gap.get("severity") == "high" else "#F59E0B")
            severity_icon = "🔴" if gap.get("severity") == "critical" else ("⚠️" if gap.get("severity") == "high" else "💡")
            
            message = gap.get('message', '')
            detail = gap.get('detail', '')
            
            st.markdown(
                f"<div style='background:#FEF3C7;border:1.5px solid {severity_color};border-radius:8px;"
                f"padding:10px 12px;margin-bottom:8px;'>"
                f"<div style='font-size:.82rem;color:#78350F;font-weight:700;margin-bottom:4px;'>{severity_icon} {message}</div>"
                f"<div style='font-size:.75rem;color:#92400E;line-height:1.4;'>{detail}</div>"
                f"</div>",
                unsafe_allow_html=True
            )
            
            # [GP-PSP-01-3] 암보험 공백 시 지역 전략 넛지 카드 표시
            if gap.get('type') == '암보험' and gap.get('regional_strategy'):
                render_regional_strategy_nudge_card(gap.get('regional_strategy'), gap.get('economic_paradox'))


# ══════════════════════════════════════════════════════════════════════════════
# [3-1] 지역 전략 넛지 카드 (Regional Strategy Nudge Card)
# ══════════════════════════════════════════════════════════════════════════════

def render_regional_strategy_nudge_card(regional_strategy: Dict[str, Any], economic_paradox: Dict[str, Any]):
    """
    지역 격차 vs 비용 전략 인터랙티브 카드 (War Room 전용)
    
    Args:
        regional_strategy: 병기별 지역 전략 데이터
        economic_paradox: 경제적 역설 분석 데이터
    """
    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    
    st.markdown(
        "<div style='background:linear-gradient(135deg,#EEF2FF 0%,#E0E7FF 100%);"
        "border:2px solid #6366F1;border-radius:12px;padding:16px;'>"
        "<div style='font-size:.95rem;font-weight:900;color:#3730A3;margin-bottom:12px;'>"
        "🏥 암 치료 지역 전략 가이드 (병기별 권장 진료처)</div>",
        unsafe_allow_html=True
    )
    
    # [GP-STEP13] 12px 그리드 내 병기별 권장처/이유/예상 비용 차이 표 형태 시각화
    st.markdown(
        "<div style='display:grid;grid-template-columns:repeat(12,1fr);gap:12px;margin-bottom:12px;'>"
        "<div style='grid-column:span 6;'>"
        "<div style='background:#DCFCE7;border:1.5px solid #22C55E;border-radius:8px;padding:12px;'>"
        "<div style='font-size:.85rem;font-weight:700;color:#166534;margin-bottom:8px;'>📍 1~3기 (초기 암)</div>"
        "<table style='width:100%;font-size:.75rem;color:#14532D;'>"
        "<tr><td style='padding:4px 0;font-weight:600;width:80px;'>권장처</td>"
        f"<td style='padding:4px 0;'>{regional_strategy.get('stage_1_3', {}).get('recommendation', '')}</td></tr>"
        "<tr><td style='padding:4px 0;font-weight:600;vertical-align:top;'>이유</td>"
        f"<td style='padding:4px 0;line-height:1.5;'>{regional_strategy.get('stage_1_3', {}).get('reason', '')}</td></tr>"
        "<tr><td style='padding:4px 0;font-weight:600;vertical-align:top;'>비용 차이</td>"
        f"<td style='padding:4px 0;line-height:1.5;'>{regional_strategy.get('stage_1_3', {}).get('cost_advantage', '')}<br>"
        f"<strong style='color:#166534;'>예후 개선: {regional_strategy.get('stage_1_3', {}).get('survival_benefit', '15% 향상')}</strong></td></tr>"
        "</table></div></div>"
        "<div style='grid-column:span 6;'>"
        "<div style='background:#FEE2E2;border:1.5px solid #EF4444;border-radius:8px;padding:12px;'>"
        "<div style='font-size:.85rem;font-weight:700;color:#991B1B;margin-bottom:8px;'>🔬 4기/재발 (진행성 암)</div>"
        "<table style='width:100%;font-size:.75rem;color:#7F1D1D;'>"
        "<tr><td style='padding:4px 0;font-weight:600;width:80px;'>권장처</td>"
        f"<td style='padding:4px 0;'>{regional_strategy.get('stage_4_recurrence', {}).get('recommendation', '')}</td></tr>"
        "<tr><td style='padding:4px 0;font-weight:600;vertical-align:top;'>이유</td>"
        f"<td style='padding:4px 0;line-height:1.5;'>{regional_strategy.get('stage_4_recurrence', {}).get('reason', '')}</td></tr>"
        "<tr><td style='padding:4px 0;font-weight:600;vertical-align:top;'>비용 차이</td>"
        f"<td style='padding:4px 0;line-height:1.5;'>{regional_strategy.get('stage_4_recurrence', {}).get('cost_advantage', '')}<br>"
        "<strong style='color:#991B1B;'>핵심: 임상시험 접근성</strong></td></tr>"
        "</table></div></div>"
        "</div>",
        unsafe_allow_html=True
    )
    
    # 경제적 역설 분석
    if economic_paradox:
        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
        
        metro_travel = economic_paradox.get('metro_travel_yearly', 0) // 10000
        clinical_savings = economic_paradox.get('clinical_trial_savings', 0) // 10000
        non_covered = economic_paradox.get('non_covered_drug_yearly', 0) // 10000
        net_savings = economic_paradox.get('net_savings', 0) // 10000
        
        st.markdown(
            f"<div style='background:#FEF3C7;border:1.5px solid #F59E0B;border-radius:8px;padding:12px;'>"
            f"<div style='font-size:.85rem;font-weight:700;color:#92400E;margin-bottom:8px;'>💡 경제적 역설 (Economic Paradox)</div>"
            f"<div style='font-size:.75rem;color:#78350F;line-height:1.6;'>"
            f"• 수도권 원정 진료비 (교통+숙박+간병): <strong>연간 {metro_travel:,}만원</strong><br>"
            f"• 임상시험 참여 시 약제비 절감: <strong>연간 {clinical_savings:,}만원 무상</strong><br>"
            f"• 지방 비급여 약제비 (임상 미참여): <strong>연간 {non_covered:,}만원 본인부담</strong><br>"
            f"<div style='margin-top:8px;padding-top:8px;border-top:1px solid #FCD34D;'>"
            f"<strong style='color:#92400E;'>순절감 효과: {net_savings:,}만원</strong> (수도권 원정이 오히려 경제적)</div>"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# [4] 3가지 플랜 탭
# ══════════════════════════════════════════════════════════════════════════════

def render_three_plans_tabs(three_plans: List[Dict[str, Any]]):
    """
    3가지 플랜 탭 렌더링
    
    Args:
        three_plans: 3가지 플랜 목록
    """
    st.markdown(
        "<div style='font-size:1.05rem;font-weight:900;color:#1E3A8A;margin-bottom:12px;'>"
        "💎 AI 추천 플랜 (3가지)</div>",
        unsafe_allow_html=True
    )
    
    if not three_plans or len(three_plans) < 3:
        st.warning("플랜 데이터가 없습니다.")
        return
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["💰 실속형", "⭐ 표준형", "👑 VIP형"])
    
    with tab1:
        render_plan_card(three_plans[0])
    
    with tab2:
        render_plan_card(three_plans[1])
    
    with tab3:
        render_plan_card(three_plans[2])


def render_plan_card(plan: Dict[str, Any]):
    """
    플랜 카드 렌더링
    
    Args:
        plan: 플랜 정보
    """
    plan_type = plan.get("plan_type", "")
    monthly_premium = plan.get("monthly_premium", 0)
    total_coverage = plan.get("total_coverage", "")
    coverage_items = plan.get("coverage_items", [])
    features = plan.get("features", [])
    recommendation = plan.get("recommendation", "")
    
    # 플랜 타입별 배경색
    plan_colors = {
        "실속": "#E0E7FF",  # 소프트 인디고
        "표준": "#DBEAFE",  # 소프트 블루
        "VIP": "#FEF3C7"    # 소프트 골드
    }
    
    bg_color = plan_colors.get(plan_type, "#F3F4F6")
    
    st.markdown(
        f"<div style='background:{bg_color};border:1.5px solid #374151;border-radius:10px;padding:16px;'>"
        f"<div style='font-size:1rem;font-weight:900;color:#1E3A8A;margin-bottom:10px;'>"
        f"{plan_type}형 플랜</div>"
        f"<div style='font-size:.88rem;font-weight:700;color:#374151;margin-bottom:8px;'>"
        f"월 보험료: {monthly_premium:,}원</div>"
        f"<div style='font-size:.85rem;color:#64748B;margin-bottom:12px;'>"
        f"총 보장: {total_coverage}</div>",
        unsafe_allow_html=True
    )
    
    # 보장 항목
    st.markdown(
        "<div style='font-size:.82rem;font-weight:700;color:#1E3A8A;margin-bottom:6px;'>"
        "📋 보장 항목</div>",
        unsafe_allow_html=True
    )
    
    for item in coverage_items:
        st.markdown(
            f"<div style='font-size:.78rem;color:#475569;margin-bottom:4px;'>"
            f"• {item.get('name', '')}: {item.get('amount', '')} (월 {item.get('premium', 0):,}원)</div>",
            unsafe_allow_html=True
        )
    
    # 특징
    st.markdown(
        "<div style='font-size:.82rem;font-weight:700;color:#1E3A8A;margin:12px 0 6px;'>"
        "✨ 특징</div>",
        unsafe_allow_html=True
    )
    
    for feature in features:
        st.markdown(
            f"<div style='font-size:.78rem;color:#475569;margin-bottom:4px;'>"
            f"• {feature}</div>",
            unsafe_allow_html=True
        )
    
    # 추천 멘트
    st.markdown(
        f"<div style='background:rgba(255,255,255,0.5);border-radius:6px;padding:8px 10px;margin-top:12px;'>"
        f"<div style='font-size:.78rem;color:#374151;line-height:1.6;'>"
        f"💡 {recommendation}</div>"
        f"</div>"
        "</div>",
        unsafe_allow_html=True
    )


# ══════════════════════════════════════════════════════════════════════════════
# [5] 감성 스크립트 선택기
# ══════════════════════════════════════════════════════════════════════════════

def render_emotional_scripts_selector(emotional_scripts: Dict[str, Dict[str, str]]):
    """
    감성 스크립트 선택기
    
    Args:
        emotional_scripts: 3가지 톤별 스크립트
    """
    st.markdown(
        "<div style='font-size:1.05rem;font-weight:900;color:#1E3A8A;margin-bottom:12px;'>"
        "🎭 AI 감성 스크립트 (3가지 톤)</div>",
        unsafe_allow_html=True
    )
    
    if not emotional_scripts:
        st.warning("스크립트 데이터가 없습니다.")
        return
    
    # 톤 선택
    tone_options = {
        "professional": "🎓 전문적 톤",
        "emotional": "💖 감성적 톤",
        "direct": "⚡ 직설적 톤"
    }
    
    selected_tone = st.radio(
        "톤 선택",
        options=list(tone_options.keys()),
        format_func=lambda x: tone_options[x],
        horizontal=True,
        key="script_tone_selector",
        label_visibility="collapsed"
    )
    
    # 선택된 톤의 스크립트 표시
    script = emotional_scripts.get(selected_tone, {})
    
    if not script:
        return
    
    st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
    
    # 오프닝 멘트
    st.markdown(
        "<div style='background:#E0E7FF;border:1.5px solid #6366F1;border-radius:10px;padding:12px;margin-bottom:12px;'>"
        "<div style='font-size:.82rem;font-weight:700;color:#1E3A8A;margin-bottom:6px;'>🎤 오프닝 멘트</div>"
        f"<div style='font-size:.78rem;color:#374151;line-height:1.7;'>{script.get('opening', '')}</div>"
        "</div>",
        unsafe_allow_html=True
    )
    
    # 본론
    st.markdown(
        "<div style='background:#DBEAFE;border:1.5px solid #3B82F6;border-radius:10px;padding:12px;margin-bottom:12px;'>"
        "<div style='font-size:.82rem;font-weight:700;color:#1E3A8A;margin-bottom:6px;'>📝 본론</div>"
        f"<div style='font-size:.78rem;color:#374151;line-height:1.7;'>{script.get('body', '')}</div>"
        "</div>",
        unsafe_allow_html=True
    )
    
    # 거절 처리 스크립트
    st.markdown(
        "<div style='background:#FEF3C7;border:1.5px solid #F59E0B;border-radius:10px;padding:12px;'>"
        "<div style='font-size:.82rem;font-weight:700;color:#92400E;margin-bottom:6px;'>🛡️ 거절 처리 스크립트</div>"
        f"<div style='font-size:.78rem;color:#78350F;line-height:1.7;'>{script.get('objection_handling', '')}</div>"
        "</div>",
        unsafe_allow_html=True
    )


# ══════════════════════════════════════════════════════════════════════════════
# [3-2] ADLs 25% 통곡의 벽 시뮬레이터 (PSP-02 Step 2)
# ══════════════════════════════════════════════════════════════════════════════

def render_adls_wall_simulator(person_id: str):
    """
    ADLs 25% 통곡의 벽 시뮬레이터 - 인터랙티브 체크리스트
    
    Args:
        person_id: 고객 UUID
    """
    st.markdown(
        "<div style='font-size:1.05rem;font-weight:900;color:#1E3A8A;margin-bottom:12px;'>"
        "🧩 ADLs 25% 판정 시뮬레이터 (회복의 역설)</div>",
        unsafe_allow_html=True
    )
    
    st.markdown(
        "<div style='background:#FEF3C7;border:1.5px solid #F59E0B;border-radius:10px;padding:12px;margin-bottom:16px;'>"
        "<div style='font-size:.82rem;color:#92400E;line-height:1.6;'>"
        "💡 <strong>CI(중대한 질병) 보험</strong>은 5대 ADLs 항목 중 <strong>장해율 25% 이상</strong>일 때만 보험금을 지급합니다.<br>"
        "재활 치료로 조금씩 좋아지는 순간, <strong style='color:#DC2626;'>보험금은 0원</strong>이 됩니다. 이것이 '회복의 역설'입니다."
        "</div></div>",
        unsafe_allow_html=True
    )
    
    # ADLs 5대 항목 체크리스트
    st.markdown(
        "<div style='font-size:.9rem;font-weight:700;color:#374151;margin-bottom:10px;'>"
        "📋 5대 ADLs 항목별 장해 점수 (실시간 합산)</div>",
        unsafe_allow_html=True
    )
    
    from hq_adls_judgment_engine import ADLS_5_CATEGORIES, calculate_adls_score
    
    # 세션 키 초기화
    if f"adls_mobility_{person_id}" not in st.session_state:
        st.session_state[f"adls_mobility_{person_id}"] = "independent"
        st.session_state[f"adls_eating_{person_id}"] = "independent"
        st.session_state[f"adls_toileting_{person_id}"] = "independent"
        st.session_state[f"adls_dressing_{person_id}"] = "independent"
        st.session_state[f"adls_bathing_{person_id}"] = "independent"
    
    # 5대 항목 선택 UI
    col1, col2 = st.columns(2, gap="medium")
    
    with col1:
        # 1. 이동 능력
        mobility_options = {k: v["label"] for k, v in ADLS_5_CATEGORIES["mobility"]["levels"].items()}
        mobility = st.selectbox(
            "🚶 이동 능력",
            options=list(mobility_options.keys()),
            format_func=lambda x: mobility_options[x],
            key=f"adls_mobility_{person_id}"
        )
        
        # 2. 식사 능력
        eating_options = {k: v["label"] for k, v in ADLS_5_CATEGORIES["eating"]["levels"].items()}
        eating = st.selectbox(
            "🍽️ 식사 능력",
            options=list(eating_options.keys()),
            format_func=lambda x: eating_options[x],
            key=f"adls_eating_{person_id}"
        )
        
        # 3. 배변 능력
        toileting_options = {k: v["label"] for k, v in ADLS_5_CATEGORIES["toileting"]["levels"].items()}
        toileting = st.selectbox(
            "🚽 배변·배뇨 능력",
            options=list(toileting_options.keys()),
            format_func=lambda x: toileting_options[x],
            key=f"adls_toileting_{person_id}"
        )
    
    with col2:
        # 4. 탈의 능력
        dressing_options = {k: v["label"] for k, v in ADLS_5_CATEGORIES["dressing"]["levels"].items()}
        dressing = st.selectbox(
            "👔 옷 입고 벗기",
            options=list(dressing_options.keys()),
            format_func=lambda x: dressing_options[x],
            key=f"adls_dressing_{person_id}"
        )
        
        # 5. 목욕 능력
        bathing_options = {k: v["label"] for k, v in ADLS_5_CATEGORIES["bathing"]["levels"].items()}
        bathing = st.selectbox(
            "🛁 목욕 능력",
            options=list(bathing_options.keys()),
            format_func=lambda x: bathing_options[x],
            key=f"adls_bathing_{person_id}"
        )
    
    # 실시간 점수 계산
    adls_result = calculate_adls_score(
        mobility=mobility,
        eating=eating,
        toileting=toileting,
        dressing=dressing,
        bathing=bathing
    )
    
    # 결과 표시
    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    
    disability_pct = adls_result["disability_percentage"]
    ci_eligible = adls_result["ci_payment_eligible"]
    
    # 장해율 게이지 바
    gauge_color = "#22C55E" if ci_eligible else "#DC2626"
    gauge_width = min(100, disability_pct)
    
    st.markdown(
        f"<div style='background:#F3F4F6;border:1.5px solid #D1D5DB;border-radius:10px;padding:14px;'>"
        f"<div style='font-size:.88rem;font-weight:700;color:#374151;margin-bottom:8px;'>"
        f"📊 현재 장해율: <span style='color:{gauge_color};font-size:1.1rem;'>{disability_pct}%</span></div>"
        f"<div style='background:#E5E7EB;border-radius:6px;height:24px;position:relative;overflow:hidden;'>"
        f"<div style='background:{gauge_color};width:{gauge_width}%;height:100%;transition:width 0.3s;'></div>"
        f"<div style='position:absolute;left:25%;top:0;bottom:0;width:2px;background:#DC2626;'></div>"
        f"<div style='position:absolute;left:25%;top:-20px;font-size:.7rem;color:#DC2626;font-weight:700;'>25% 기준선</div>"
        f"</div>"
        f"<div style='margin-top:10px;font-size:.82rem;color:#64748B;'>"
        f"{adls_result['alert_message']}"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    # 회복의 역설 경고 (20~25% 구간)
    if adls_result["recovery_paradox_warning"]:
        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='background:#FEE2E2;border:2px solid #DC2626;border-radius:10px;padding:14px;'>"
            f"<div style='font-size:.85rem;color:#991B1B;line-height:1.7;white-space:pre-line;'>"
            f"{adls_result['recovery_paradox_warning']}"
            f"</div></div>",
            unsafe_allow_html=True
        )
    
    # 장해 판정 타임라인
    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    
    from hq_adls_judgment_engine import simulate_disability_timeline
    from datetime import datetime
    
    timeline_result = simulate_disability_timeline(
        stroke_date=datetime.now(),
        current_adls_score=adls_result["total_score"]
    )
    
    st.markdown(
        "<div style='font-size:.9rem;font-weight:700;color:#374151;margin-bottom:10px;'>"
        "⏱️ 장해 판정 타임라인 (6개월 vs 18개월)</div>",
        unsafe_allow_html=True
    )
    
    st.markdown(
        f"<div style='background:#E0E7FF;border:1.5px solid #6366F1;border-radius:10px;padding:12px;'>"
        f"<pre style='font-size:.75rem;color:#1E3A8A;line-height:1.6;margin:0;white-space:pre-wrap;font-family:monospace;'>"
        f"{timeline_result['timeline_visualization']}"
        f"</pre></div>",
        unsafe_allow_html=True
    )


# ══════════════════════════════════════════════════════════════════════════════
# [3-3] 트리니티 가처분 소득 결손 차트 (PSP-02 Step 3)
# ══════════════════════════════════════════════════════════════════════════════

def render_trinity_income_loss_charts(person_id: str):
    """
    트리니티 가처분 소득 결손 차트 (왼쪽: 진단비 증발, 오른쪽: 선지급 방어)
    
    Args:
        person_id: 고객 UUID
    """
    st.markdown(
        "<div style='font-size:1.05rem;font-weight:900;color:#1E3A8A;margin-bottom:12px;'>"
        "💰 트리니티 가처분 소득 방어 시뮬레이션</div>",
        unsafe_allow_html=True
    )
    
    st.markdown(
        "<div style='background:#FEF3C7;border:1.5px solid #F59E0B;border-radius:10px;padding:12px;margin-bottom:16px;'>"
        "<div style='font-size:.82rem;color:#92400E;line-height:1.6;'>"
        "💡 <strong>돈의 용도를 분리하십시오</strong><br>"
        "진단비 5,000만 원은 <strong>간병비 전용</strong>, 종신보험 선지급은 <strong>생활비 전용</strong>으로 사용해야 가족의 가처분 소득을 지킬 수 있습니다."
        "</div></div>",
        unsafe_allow_html=True
    )
    
    from hq_trinity_income_loss_engine import calculate_disposable_income_gap, simulate_caregiving_blackhole
    from hq_life_insurance_acceleration import calculate_life_insurance_acceleration, simulate_disposable_income_defense
    
    # 기본 파라미터
    diagnosis_benefit = 50000000
    monthly_caregiving = 4000000
    monthly_living = 2500000
    
    # 가처분 소득 결손 계산
    gap_result = calculate_disposable_income_gap(
        monthly_caregiving_cost=monthly_caregiving,
        monthly_living_cost=monthly_living,
        diagnosis_benefit=diagnosis_benefit,
        simulation_months=24
    )
    
    # 간병비 블랙홀 시뮬레이션
    blackhole_result = simulate_caregiving_blackhole(
        diagnosis_benefit=diagnosis_benefit,
        monthly_caregiving_cost=monthly_caregiving
    )
    
    # 종신보험 선지급 계산 (50%)
    acceleration_result = calculate_life_insurance_acceleration(
        death_benefit=100000000,
        acceleration_rate="50%",
        diagnosis_benefit=diagnosis_benefit
    )
    
    # 가처분 소득 방어 시뮬레이션
    defense_result = simulate_disposable_income_defense(
        diagnosis_benefit=diagnosis_benefit,
        acceleration_amount=acceleration_result["acceleration_amount"],
        monthly_caregiving_cost=monthly_caregiving,
        monthly_living_cost=monthly_living,
        simulation_months=24
    )
    
    # 차트 2개 (왼쪽: 진단비 증발, 오른쪽: 선지급 방어)
    col1, col2 = st.columns(2, gap="medium")
    
    with col1:
        st.markdown(
            "<div style='background:#FEE2E2;border:2px solid #DC2626;border-radius:10px;padding:14px;'>"
            "<div style='font-size:.88rem;font-weight:900;color:#991B1B;margin-bottom:10px;text-align:center;'>"
            "📉 진단비만 사용 (선지급 없음)</div>",
            unsafe_allow_html=True
        )
        
        # 간병비 블랙홀 시각화
        st.markdown(
            f"<pre style='font-size:.7rem;color:#7F1D1D;line-height:1.4;margin:0;white-space:pre-wrap;font-family:monospace;'>"
            f"{blackhole_result['visualization']}"
            f"</pre>",
            unsafe_allow_html=True
        )
        
        # 최종 부족액
        final_deficit = gap_result["total_gap"]
        st.markdown(
            f"<div style='background:rgba(220,38,38,0.1);border-radius:6px;padding:10px;margin-top:10px;'>"
            f"<div style='font-size:.82rem;font-weight:700;color:#DC2626;text-align:center;'>"
            f"최종 부족액: {abs(final_deficit):,}원</div>"
            f"</div></div>",
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            "<div style='background:#DCFCE7;border:2px solid #22C55E;border-radius:10px;padding:14px;'>"
            "<div style='font-size:.88rem;font-weight:900;color:#166534;margin-bottom:10px;text-align:center;'>"
            "📈 진단비 + 선지급 (생존 엔진)</div>",
            unsafe_allow_html=True
        )
        
        # 선지급 방어 시각화
        st.markdown(
            f"<div style='font-size:.75rem;color:#14532D;line-height:1.6;'>"
            f"<strong>진단비 {diagnosis_benefit:,}원</strong> (간병비 전용)<br>"
            f"→ 월 {monthly_caregiving:,}원 × {blackhole_result['depletion_months']}개월<br>"
            f"→ {blackhole_result['depletion_months']}개월 만에 소진<br><br>"
            f"<strong>선지급 {acceleration_result['acceleration_amount']:,}원</strong> (생활비 전용)<br>"
            f"→ 월 {monthly_living:,}원 × {int(acceleration_result['acceleration_amount']/monthly_living)}개월<br>"
            f"→ <span style='color:#22C55E;font-weight:700;'>{int(acceleration_result['acceleration_amount']/monthly_living)}개월 생활비 확보</span>"
            f"</div>",
            unsafe_allow_html=True
        )
        
        # Safety Net 표시
        st.markdown(
            f"<div style='background:rgba(34,197,94,0.1);border-radius:6px;padding:10px;margin-top:10px;'>"
            f"<div style='font-size:.82rem;font-weight:700;color:#22C55E;text-align:center;'>"
            f"✅ Safety Net 가동<br>"
            f"총 확보: {acceleration_result['total_living_benefit']:,}원</div>"
            f"</div></div>",
            unsafe_allow_html=True
        )
    
    # 전문가 클로징 스크립트
    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    
    from hq_trinity_income_loss_engine import generate_trinity_closing_script
    from hq_life_insurance_acceleration import calculate_required_life_insurance_acceleration
    
    acceleration_required = calculate_required_life_insurance_acceleration(
        total_gap=gap_result["total_gap"],
        diagnosis_benefit=diagnosis_benefit
    )
    
    closing_script = generate_trinity_closing_script(
        gap_result=gap_result,
        acceleration_result=acceleration_required,
        customer_name="사장님"
    )
    
    st.markdown(
        "<div style='font-size:.9rem;font-weight:700;color:#374151;margin-bottom:10px;'>"
        "🎤 전문가 클로징 스크립트</div>",
        unsafe_allow_html=True
    )
    
    st.markdown(
        f"<div style='background:#E0E7FF;border:1.5px solid #6366F1;border-radius:10px;padding:14px;'>"
        f"<pre style='font-size:.78rem;color:#1E3A8A;line-height:1.7;margin:0;white-space:pre-wrap;font-family:inherit;'>"
        f"{closing_script}"
        f"</pre></div>",
        unsafe_allow_html=True
    )


# ══════════════════════════════════════════════════════════════════════════════
# [6] 모바일 전용 요약 제안서
# ══════════════════════════════════════════════════════════════════════════════

def render_mobile_summary(proposal_data: Dict[str, Any], person_id: str):
    """
    모바일 전용 요약 제안서
    
    Args:
        proposal_data: 제안서 데이터
        person_id: 고객 UUID
    """
    st.markdown(
        "<div style='font-size:1.05rem;font-weight:900;color:#1E3A8A;margin-bottom:12px;'>"
        "📱 모바일 전용 요약 제안서</div>",
        unsafe_allow_html=True
    )
    
    persona = proposal_data.get("persona", {})
    gap_analysis = proposal_data.get("gap_analysis", {})
    three_plans = proposal_data.get("three_plans", [])
    
    customer_name = persona.get("name", "고객님")
    
    # 모바일 요약 제안서 HTML
    mobile_summary_html = f"""
    <div style='background:linear-gradient(135deg,#E0E7FF,#DBEAFE);border:2px solid #6366F1;
    border-radius:12px;padding:16px;max-width:400px;margin:0 auto;'>
        <div style='text-align:center;font-size:1.1rem;font-weight:900;color:#1E3A8A;margin-bottom:12px;'>
            💎 {customer_name}님을 위한 맞춤 제안
        </div>
        
        <div style='background:rgba(255,255,255,0.7);border-radius:8px;padding:12px;margin-bottom:12px;'>
            <div style='font-size:.85rem;font-weight:700;color:#1E3A8A;margin-bottom:6px;'>
                📊 현재 보장 현황
            </div>
            <div style='font-size:.78rem;color:#374151;'>
                월 보험료: {int(gap_analysis.get('total_premium', 0)):,}원<br>
                보장 공백: {len(gap_analysis.get('gaps', []))}건
            </div>
        </div>
        
        <div style='background:rgba(255,255,255,0.7);border-radius:8px;padding:12px;margin-bottom:12px;'>
            <div style='font-size:.85rem;font-weight:700;color:#1E3A8A;margin-bottom:6px;'>
                💡 AI 추천 플랜
            </div>
    """
    
    # 3가지 플랜 요약
    for idx, plan in enumerate(three_plans[:3]):
        plan_type = plan.get("plan_type", "")
        monthly_premium = plan.get("monthly_premium", 0)
        
        mobile_summary_html += f"""
            <div style='font-size:.78rem;color:#374151;margin-bottom:4px;'>
                {idx+1}. {plan_type}형: 월 {monthly_premium:,}원
            </div>
        """
    
    mobile_summary_html += """
        </div>
        
        <div style='text-align:center;font-size:.75rem;color:#64748B;margin-top:12px;'>
            Powered by Goldkey AI Masters 2026
        </div>
    </div>
    """
    
    st.markdown(mobile_summary_html, unsafe_allow_html=True)
    
    # 카카오톡 공유 버튼
    st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2, gap="small")
    
    with col1:
        if st.button("💬 카카오톡 공유", key=f"share_kakao_{person_id}", use_container_width=True):
            st.info("💬 카카오톡 공유 기능은 곧 추가됩니다.")
    
    with col2:
        if st.button("📄 PDF 다운로드", key=f"download_pdf_{person_id}", use_container_width=True):
            st.info("📄 PDF 다운로드 기능은 곧 추가됩니다.")


# ══════════════════════════════════════════════════════════════════════════════
# [7] 사용 예시
# ══════════════════════════════════════════════════════════════════════════════

"""
## 사용 예시 (crm_client_detail.py 통합)

```python
from crm_proposal_ui import render_proposal_cockpit

# 고객 상세 페이지에서 제안서 칵핏 렌더링
if st.session_state.get("crm_spa_screen") == "proposal":
    person_id = st.session_state.get("crm_selected_pid")
    agent_id = st.session_state.get("crm_user_id")
    customer_name = st.session_state.get("crm_customer_name", "")
    
    if person_id and agent_id:
        render_proposal_cockpit(person_id, agent_id, customer_name)
```

## 독립 페이지로 사용

```python
# crm_app_impl.py

if st.session_state.get("crm_spa_screen") == "proposal":
    person_id = st.session_state.get("crm_selected_pid")
    agent_id = st.session_state.get("crm_user_id")
    customer_name = st.session_state.get("crm_customer_name", "")
    
    if person_id and agent_id:
        render_proposal_cockpit(person_id, agent_id, customer_name)
```
"""
