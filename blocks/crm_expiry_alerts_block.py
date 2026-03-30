"""
[GP-EXPIRY] 보험 만기 관리 대상자 UI 블록
STEP 2. 영업일정 점검 화면에서 사용
"""
import streamlit as st
from typing import Optional


def render_expiry_alerts_block(agent_id: str) -> None:
    """
    🚨 보험 만기 관리 대상자 섹션 렌더링.
    
    D-28일(4주전), D-14일(2주전) 만기 대상 고객을 표시하고
    감성 멘트 생성 및 카카오톡 발송 기능 제공.
    
    Args:
        agent_id: 설계사 ID
    """
    from db_utils import get_expiry_alerts, generate_expiry_renewal_message
    
    # 만기 알림 대상자 조회
    alerts = get_expiry_alerts(agent_id, priority_only=True)
    
    if not alerts:
        return
    
    # 섹션 헤더
    st.markdown(
        "<div style='background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);"
        "padding:16px 20px;border-radius:12px;margin-bottom:16px;'>"
        "<h3 style='color:white;margin:0;font-size:1.2rem;'>"
        "🚨 보험 만기 관리 대상자</h3>"
        "<p style='color:#f0f0f0;margin:4px 0 0 0;font-size:0.85rem;'>"
        "D-28일(4주전), D-14일(2주전) 만기 예정 고객입니다. 재가입 상담을 진행하세요!</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    
    # 우선순위별 그룹화
    priority_1 = [a for a in alerts if a.get("alert_priority") == 1]  # D-28
    priority_2 = [a for a in alerts if a.get("alert_priority") == 2]  # D-14
    
    # D-14 (긴급) 먼저 표시
    if priority_2:
        st.markdown("### 🔴 긴급 (D-14일 이내)")
        for alert in priority_2:
            _render_alert_card(alert, is_urgent=True)
    
    # D-28 (주의) 표시
    if priority_1:
        st.markdown("### 🟡 주의 (D-28일 이내)")
        for alert in priority_1:
            _render_alert_card(alert, is_urgent=False)


def _render_alert_card(alert: dict, is_urgent: bool = False) -> None:
    """
    개별 만기 알림 카드 렌더링.
    
    Args:
        alert: 만기 알림 정보
        is_urgent: 긴급 여부 (D-14)
    """
    from db_utils import generate_expiry_renewal_message
    
    # 우선순위 아이콘
    priority_icon = "🔴" if is_urgent else "🟡"
    
    # 고객명 및 보험 유형
    customer_name = alert.get("customer_name", "고객")
    sub_type = alert.get("sub_type", "보험")
    days_until = alert.get("days_until_expiry", 0)
    
    # Expander로 카드 렌더링
    with st.expander(
        f"{priority_icon} {customer_name} - {sub_type} (D-{days_until})",
        expanded=is_urgent,  # 긴급 알림은 기본 펼침
    ):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**📋 보험 정보**")
            st.write(f"• **보험사:** {alert.get('insurance_company', '미등록')}")
            st.write(f"• **상품명:** {alert.get('product_name', '미등록')}")
            st.write(f"• **만기일:** {alert.get('expiry_date', '')}")
            
            # 태그 표시
            tags = alert.get("tags", [])
            if tags:
                tag_str = " ".join([f"`{tag}`" for tag in tags])
                st.markdown(f"**태그:** {tag_str}")
        
        with col2:
            st.markdown(f"**⏰ D-Day**")
            st.metric(
                label="만기까지",
                value=f"{days_until}일",
                delta=f"{'긴급' if is_urgent else '주의'}",
                delta_color="inverse" if is_urgent else "normal",
            )
        
        st.markdown("---")
        
        # 감성 멘트 생성
        message = generate_expiry_renewal_message(
            customer_name=customer_name,
            sub_type=sub_type,
            expiry_date=alert.get("expiry_date", ""),
            days_until=days_until,
            insurance_company=alert.get("insurance_company", ""),
            product_name=alert.get("product_name", ""),
        )
        
        st.markdown("**📱 카카오톡 발송 메시지**")
        
        # 메시지 편집 가능한 텍스트 영역
        edited_message = st.text_area(
            "메시지 내용 (수정 가능)",
            value=message,
            height=200,
            key=f"msg_{alert.get('id', '')}",
            label_visibility="collapsed",
        )
        
        # 액션 버튼
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            if st.button(
                "📞 전화하기",
                key=f"call_{alert.get('id', '')}",
                use_container_width=True,
            ):
                st.info("💡 전화 연결 기능은 향후 구현 예정입니다.")
        
        with col_btn2:
            if st.button(
                "💬 카톡 발송",
                key=f"kakao_{alert.get('id', '')}",
                use_container_width=True,
                type="primary",
            ):
                # 카카오톡 발송 로직 (향후 구현)
                st.success(f"✅ {customer_name} 고객님께 카카오톡 발송 완료!")
                st.balloons()
        
        with col_btn3:
            if st.button(
                "✅ 완료",
                key=f"done_{alert.get('id', '')}",
                use_container_width=True,
            ):
                # 일정 완료 처리 (향후 구현)
                st.success("일정이 완료 처리되었습니다.")


def render_expiry_summary_widget(agent_id: str) -> None:
    """
    만기 알림 요약 위젯 (대시보드 상단용).
    
    Args:
        agent_id: 설계사 ID
    """
    from db_utils import get_expiry_alerts
    
    # 만기 알림 대상자 조회
    alerts = get_expiry_alerts(agent_id, priority_only=True)
    
    if not alerts:
        return
    
    # 우선순위별 카운트
    urgent_count = len([a for a in alerts if a.get("alert_priority") == 2])
    warning_count = len([a for a in alerts if a.get("alert_priority") == 1])
    
    # 요약 위젯
    st.markdown(
        f"<div style='background:#fff3cd;border-left:4px solid #f59e0b;"
        f"padding:12px 16px;border-radius:8px;margin-bottom:16px;'>"
        f"<div style='font-size:0.9rem;font-weight:700;color:#92400e;margin-bottom:4px;'>"
        f"🚨 보험 만기 알림</div>"
        f"<div style='font-size:0.8rem;color:#78350f;'>"
        f"긴급(D-14): <b>{urgent_count}건</b> | 주의(D-28): <b>{warning_count}건</b>"
        f"</div></div>",
        unsafe_allow_html=True,
    )
