"""
hq_phase1_network_viewer.py — [GP-PHASE1] HQ 앱 8가지 관계망 네트워크 조회 UI

HQ 앱 고객 대시보드에서 사용하는 관계망 네트워크 시각화.
Read-Only 조회 전용 (데이터 입력은 CRM 앱에서만).
"""
import streamlit as st
import db_utils as du
from shared_components import decrypt_pii


def render_network_dashboard(person_id: str, agent_id: str, key_prefix: str = "_hq_net"):
    """
    [GP-PHASE1] HQ 앱 관계망 네트워크 대시보드 (Read-Only).
    
    Args:
        person_id: 고객 UUID
        agent_id: 담당 설계사
        key_prefix: Streamlit 위젯 키 접두사
    """
    if not person_id or not agent_id:
        st.warning("⚠️ 고객 정보가 없습니다.")
        return
    
    # 고객 정보 조회
    customer = du.get_customer(person_id, agent_id)
    if not customer:
        st.error("❌ 고객 정보를 찾을 수 없습니다.")
        return
    
    customer_name = decrypt_pii(customer.get("name", ""))
    
    st.markdown(f"""
    <div style='background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);border:1px dashed #000;border-radius:12px;padding:16px;margin-bottom:20px;color:#fff;'>
        <div style='font-size:1.1rem;font-weight:700;margin-bottom:8px;'>
            🕸️ {customer_name}님의 관계망 네트워크
        </div>
        <div style='font-size:0.85rem;opacity:0.9;'>
            8가지 관계망 태그로 분류된 고객 네트워크를 한눈에 확인하세요.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 관계망 요약
    summary = du.get_network_summary(person_id, agent_id)
    
    # 요약 카드 그리드
    st.markdown("### 📊 관계망 요약")
    cols = st.columns(4)
    
    tag_icons = {
        "상담자": "💬",
        "계약자": "📝",
        "피보험자": "🛡️",
        "가족": "👨‍👩‍👧‍👦",
        "소개자": "🤝",
        "동일법인": "🏢",
        "동일단체": "🏛️",
        "친인척": "👪"
    }
    
    tag_colors = {
        "상담자": "#3b82f6",
        "계약자": "#10b981",
        "피보험자": "#f59e0b",
        "가족": "#ec4899",
        "소개자": "#8b5cf6",
        "동일법인": "#06b6d4",
        "동일단체": "#14b8a6",
        "친인척": "#f97316"
    }
    
    for idx, (tag_type, count) in enumerate(summary.items()):
        with cols[idx % 4]:
            icon = tag_icons.get(tag_type, "🏷️")
            color = tag_colors.get(tag_type, "#6b7280")
            
            st.markdown(f"""
            <div style='background:#ffffff;border:2px solid {color};border-radius:10px;padding:16px;text-align:center;margin-bottom:12px;'>
                <div style='font-size:2rem;margin-bottom:8px;'>{icon}</div>
                <div style='font-size:0.80rem;color:#6b7280;margin-bottom:4px;'>{tag_type}</div>
                <div style='font-size:1.8rem;font-weight:900;color:{color};'>{count}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 태그별 상세 조회
    st.markdown("### 🔍 관계망 상세")
    
    # 탭으로 분리
    tabs = st.tabs([f"{tag_icons.get(t, '🏷️')} {t}" for t in du.VALID_TAG_TYPES])
    
    for idx, tag_type in enumerate(du.VALID_TAG_TYPES):
        with tabs[idx]:
            _render_tag_detail(person_id, agent_id, tag_type, tag_colors.get(tag_type, "#6b7280"), key_prefix)
    
    st.markdown("---")
    
    # 보험계약 이력 요약
    st.markdown("### 📋 보험계약 이력 요약")
    _render_contracts_summary(person_id, agent_id, key_prefix)
    
    st.markdown("---")
    
    # 상담 일정 요약
    st.markdown("### 📅 상담 일정 요약")
    _render_schedules_summary(person_id, agent_id, key_prefix)


def _render_tag_detail(person_id: str, agent_id: str, tag_type: str, color: str, key_prefix: str):
    """특정 태그 유형의 상세 목록"""
    tags = du.get_relationship_tags(person_id=person_id, agent_id=agent_id, tag_type=tag_type)
    
    if not tags:
        st.info(f"💡 '{tag_type}' 태그가 등록되지 않았습니다.")
        return
    
    st.markdown(f"**총 {len(tags)}건의 {tag_type} 관계**")
    
    for tag in tags:
        related_pid = tag.get("related_person_id", "")
        memo = tag.get("memo", "")
        created_at = tag.get("created_at", "")[:10]
        
        # 관계 대상 정보 조회
        related_info = ""
        if related_pid:
            try:
                related_customer = du.get_customer(related_pid, agent_id)
                if related_customer:
                    related_name = decrypt_pii(related_customer.get("name", ""))
                    related_contact = decrypt_pii(related_customer.get("contact", ""))
                    related_job = related_customer.get("job", "")
                    related_info = f"""
                    <div style='background:#f9fafb;border-left:3px solid {color};padding:8px;margin-top:8px;border-radius:4px;'>
                        <div style='font-size:0.85rem;font-weight:600;color:#1a1a1a;margin-bottom:4px;'>
                            👤 {related_name}
                        </div>
                        <div style='font-size:0.75rem;color:#6b7280;'>
                            {related_job} · {related_contact}
                        </div>
                    </div>
                    """
            except Exception:
                related_info = f"<div style='font-size:0.75rem;color:#9ca3af;'>관계 대상: {related_pid[:8]}...</div>"
        
        st.markdown(f"""
        <div style='background:#ffffff;border:1px dashed {color};border-radius:8px;padding:14px;margin-bottom:12px;'>
            <div style='display:flex;align-items:center;gap:8px;margin-bottom:8px;'>
                <span style='background:{color};color:#fff;padding:4px 12px;border-radius:6px;font-size:0.80rem;font-weight:600;'>
                    {tag_type}
                </span>
                <span style='color:#9ca3af;font-size:0.70rem;margin-left:auto;'>등록일: {created_at}</span>
            </div>
            {f"<div style='font-size:0.80rem;color:#4a5568;margin-bottom:8px;background:#fffbeb;padding:8px;border-radius:4px;'>💡 {memo}</div>" if memo else ""}
            {related_info}
        </div>
        """, unsafe_allow_html=True)


def _render_contracts_summary(person_id: str, agent_id: str, key_prefix: str):
    """보험계약 이력 요약"""
    contracts = du.get_insurance_contracts(person_id=person_id, agent_id=agent_id)
    
    if not contracts:
        st.info("💡 등록된 보험계약 이력이 없습니다.")
        return
    
    # 상태별 분류
    own = len([c for c in contracts if c.get("contract_status") == "자사계약"])
    other = len([c for c in contracts if c.get("contract_status") == "타부점계약"])
    terminated = len([c for c in contracts if c.get("contract_status") == "해지계약"])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style='background:#ecfdf5;border:2px solid #10b981;border-radius:8px;padding:16px;text-align:center;'>
            <div style='font-size:0.80rem;color:#059669;margin-bottom:4px;'>🏢 자사계약</div>
            <div style='font-size:2rem;font-weight:900;color:#10b981;'>{own}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style='background:#fffbeb;border:2px solid #f59e0b;border-radius:8px;padding:16px;text-align:center;'>
            <div style='font-size:0.80rem;color:#d97706;margin-bottom:4px;'>🏪 타부점계약</div>
            <div style='font-size:2rem;font-weight:900;color:#f59e0b;'>{other}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style='background:#fef2f2;border:2px solid #ef4444;border-radius:8px;padding:16px;text-align:center;'>
            <div style='font-size:0.80rem;color:#dc2626;margin-bottom:4px;'>❌ 해지계약</div>
            <div style='font-size:2rem;font-weight:900;color:#ef4444;'>{terminated}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 최근 계약 5건 표시
    with st.expander("📋 최근 계약 이력 보기", expanded=False):
        recent_contracts = sorted(contracts, key=lambda x: x.get("contract_date", ""), reverse=True)[:5]
        
        for contract in recent_contracts:
            status = contract.get("contract_status", "")
            company = contract.get("insurance_company", "")
            product = contract.get("product_name", "")
            date = contract.get("contract_date", "")
            premium = contract.get("monthly_premium", 0)
            
            status_colors = {
                "자사계약": "#10b981",
                "타부점계약": "#f59e0b",
                "해지계약": "#ef4444"
            }
            color = status_colors.get(status, "#6b7280")
            
            st.markdown(f"""
            <div style='background:#ffffff;border-left:4px solid {color};padding:10px;margin-bottom:8px;border-radius:4px;'>
                <div style='display:flex;align-items:center;gap:8px;'>
                    <span style='background:{color};color:#fff;padding:2px 8px;border-radius:4px;font-size:0.70rem;font-weight:600;'>
                        {status}
                    </span>
                    <span style='font-size:0.85rem;font-weight:600;'>{company}</span>
                    <span style='color:#9ca3af;font-size:0.70rem;margin-left:auto;'>{date}</span>
                </div>
                <div style='font-size:0.80rem;color:#6b7280;margin-top:4px;'>
                    {product} · 월 {premium:,.0f}원
                </div>
            </div>
            """, unsafe_allow_html=True)


def _render_schedules_summary(person_id: str, agent_id: str, key_prefix: str):
    """상담 일정 요약"""
    schedules = du.get_consultation_schedules(person_id=person_id, agent_id=agent_id)
    
    if not schedules:
        st.info("💡 등록된 상담 일정이 없습니다.")
        return
    
    # 완료/미완료 분류
    pending = len([s for s in schedules if not s.get("is_completed")])
    completed = len([s for s in schedules if s.get("is_completed")])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div style='background:#eff6ff;border:2px solid #3b82f6;border-radius:8px;padding:16px;text-align:center;'>
            <div style='font-size:0.80rem;color:#1d4ed8;margin-bottom:4px;'>⏳ 예정 상담</div>
            <div style='font-size:2rem;font-weight:900;color:#3b82f6;'>{pending}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style='background:#ecfdf5;border:2px solid #10b981;border-radius:8px;padding:16px;text-align:center;'>
            <div style='font-size:0.80rem;color:#059669;margin-bottom:4px;'>✅ 완료 상담</div>
            <div style='font-size:2rem;font-weight:900;color:#10b981;'>{completed}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 최근 상담 5건 표시
    with st.expander("📅 최근 상담 이력 보기", expanded=False):
        recent_schedules = sorted(schedules, key=lambda x: x.get("schedule_date", ""), reverse=True)[:5]
        
        for schedule in recent_schedules:
            cons_type = schedule.get("consultation_type", "")
            date = schedule.get("schedule_date", "")
            time = schedule.get("schedule_time", "")
            content = schedule.get("consultation_content", "")
            is_completed = schedule.get("is_completed", False)
            
            type_colors = {
                "초회상담": "#3b82f6",
                "보장분석": "#10b981",
                "증권점검": "#f59e0b",
                "계약체결": "#ec4899",
                "사후관리": "#8b5cf6",
                "기타": "#6b7280"
            }
            color = type_colors.get(cons_type, "#6b7280")
            
            st.markdown(f"""
            <div style='background:#ffffff;border-left:4px solid {color};padding:10px;margin-bottom:8px;border-radius:4px;'>
                <div style='display:flex;align-items:center;gap:8px;'>
                    <span style='background:{color};color:#fff;padding:2px 8px;border-radius:4px;font-size:0.70rem;font-weight:600;'>
                        {cons_type}
                    </span>
                    <span style='font-size:0.85rem;'>{date} {time}</span>
                    {f"<span style='background:#10b981;color:#fff;padding:2px 6px;border-radius:4px;font-size:0.65rem;margin-left:auto;'>완료</span>" if is_completed else "<span style='background:#f59e0b;color:#fff;padding:2px 6px;border-radius:4px;font-size:0.65rem;margin-left:auto;'>예정</span>"}
                </div>
                {f"<div style='font-size:0.75rem;color:#6b7280;margin-top:4px;'>{content}</div>" if content else ""}
            </div>
            """, unsafe_allow_html=True)


def render_backup_history_panel(person_id: str, key_prefix: str = "_hq_backup"):
    """
    [GP-PHASE1] 고객 정보 백업 이력 조회 패널 (HQ 전용).
    
    Args:
        person_id: 고객 UUID
        key_prefix: Streamlit 위젯 키 접두사
    """
    if not person_id:
        st.warning("⚠️ 고객 정보가 없습니다.")
        return
    
    st.markdown("""
    <div style='background:#fef3c7;border:1px dashed #000;border-radius:8px;padding:12px;margin-bottom:16px;'>
        <div style='font-size:0.95rem;font-weight:700;color:#1a1a1a;margin-bottom:8px;'>
            🔒 고객 정보 백업 이력 (이중화 보안)
        </div>
        <div style='font-size:0.80rem;color:#4a5568;line-height:1.5;'>
            정보보호법 준수를 위한 자동 백업 이력입니다. 데이터 손실 시 복원 가능합니다.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 백업 이력 조회
    backups = du.get_backup_history(person_id, limit=10)
    
    if not backups:
        st.info("💡 백업 이력이 없습니다.")
        return
    
    st.markdown(f"**최근 백업 {len(backups)}건**")
    
    for backup in backups:
        backup_id = backup.get("backup_id", "")
        backup_created = backup.get("backup_created_at", "")[:19]
        backup_reason = backup.get("backup_reason", "")
        original_updated = backup.get("original_updated_at", "")[:19]
        
        reason_text = {
            "auto_mirror": "자동 미러링",
            "manual_backup": "수동 백업"
        }.get(backup_reason, backup_reason)
        
        st.markdown(f"""
        <div style='background:#ffffff;border:1px dashed #d97706;border-radius:8px;padding:12px;margin-bottom:10px;'>
            <div style='display:flex;align-items:center;gap:8px;margin-bottom:6px;'>
                <span style='background:#f59e0b;color:#fff;padding:4px 10px;border-radius:4px;font-size:0.75rem;font-weight:600;'>
                    {reason_text}
                </span>
                <span style='color:#9ca3af;font-size:0.70rem;margin-left:auto;'>백업일시: {backup_created}</span>
            </div>
            <div style='font-size:0.75rem;color:#6b7280;'>
                원본 수정일시: {original_updated}
            </div>
            <div style='font-size:0.70rem;color:#9ca3af;margin-top:4px;'>
                백업 ID: {backup_id[:16]}...
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption("⚠️ 백업 복원은 시스템 관리자에게 문의하세요.")
