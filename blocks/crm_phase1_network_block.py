"""
blocks/crm_phase1_network_block.py — [GP-PHASE1] 8가지 관계망 태깅 UI 블록

CRM 앱 고객 상세 페이지에서 사용하는 관계망 태깅 UI.
8가지 태그: 상담자, 계약자, 피보험자, 가족, 소개자, 동일법인, 동일단체, 친인척
"""
import streamlit as st
import db_utils as du
from shared_components import encrypt_pii, decrypt_pii


def render_network_tagging_panel(person_id: str, agent_id: str, key_prefix: str = "_ntp"):
    """
    [GP-PHASE1] 고객 관계망 태깅 패널 렌더링.
    
    Args:
        person_id: 고객 UUID
        agent_id: 담당 설계사
        key_prefix: Streamlit 위젯 키 접두사
    """
    if not person_id or not agent_id:
        st.warning("⚠️ 고객 정보가 없습니다.")
        return
    
    st.markdown("""
    <div style='background:#FFF8E1;border:1px dashed #000;border-radius:8px;padding:12px;margin-bottom:16px;'>
        <div style='font-size:0.95rem;font-weight:700;color:#1a1a1a;margin-bottom:8px;'>
            🏷️ 8가지 관계망 태깅 시스템
        </div>
        <div style='font-size:0.80rem;color:#4a5568;line-height:1.5;'>
            고객을 8가지 관계망으로 분류하여 체계적으로 관리합니다.<br>
            <span style='color:#d97706;font-weight:600;'>상담자·계약자·피보험자·가족·소개자·동일법인·동일단체·친인척</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 현재 태그 조회
    current_tags = du.get_relationship_tags(person_id=person_id, agent_id=agent_id)
    
    # 태그 요약 표시
    summary = du.get_network_summary(person_id, agent_id)
    
    st.markdown("**📊 현재 관계망 요약**")
    cols = st.columns(4)
    for idx, (tag_type, count) in enumerate(summary.items()):
        with cols[idx % 4]:
            color = "#10b981" if count > 0 else "#d1d5db"
            st.markdown(f"""
            <div style='background:#f9fafb;border:1px dashed {color};border-radius:6px;padding:8px;text-align:center;'>
                <div style='font-size:0.75rem;color:#6b7280;'>{tag_type}</div>
                <div style='font-size:1.2rem;font-weight:700;color:{color};'>{count}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 태그 추가 폼
    with st.expander("➕ 새 관계망 태그 추가", expanded=False):
        _add_tag_form(person_id, agent_id, key_prefix)
    
    # 기존 태그 목록
    if current_tags:
        st.markdown("**📋 등록된 관계망 태그**")
        for tag in current_tags:
            _render_tag_card(tag, key_prefix)
    else:
        st.info("💡 등록된 관계망 태그가 없습니다. 위 폼에서 추가하세요.")


def _add_tag_form(person_id: str, agent_id: str, key_prefix: str):
    """태그 추가 폼"""
    col1, col2 = st.columns([3, 2])
    
    with col1:
        tag_type = st.selectbox(
            "태그 유형 *",
            options=du.VALID_TAG_TYPES,
            key=f"{key_prefix}_tag_type"
        )
    
    with col2:
        # 관계 대상 선택 (선택 사항)
        customers = du.load_customers(agent_id, "")
        customer_options = ["(없음)"] + [f"{c.get('name', '')} ({c.get('person_id', '')[:8]}...)" for c in customers if c.get("person_id") != person_id]
        related_person = st.selectbox(
            "관계 대상",
            options=customer_options,
            key=f"{key_prefix}_related_person"
        )
    
    memo = st.text_area(
        "메모",
        placeholder="관계 상세 설명 (선택)",
        key=f"{key_prefix}_memo",
        height=80
    )
    
    if st.button("🏷️ 태그 추가", key=f"{key_prefix}_add_btn", use_container_width=True):
        # 관계 대상 person_id 추출
        related_pid = ""
        if related_person != "(없음)":
            try:
                related_pid = related_person.split("(")[1].split(")")[0].replace("...", "")
                # 전체 person_id 찾기
                for c in customers:
                    if c.get("person_id", "").startswith(related_pid):
                        related_pid = c.get("person_id", "")
                        break
            except Exception:
                related_pid = ""
        
        success = du.add_relationship_tag(
            person_id=person_id,
            agent_id=agent_id,
            tag_type=tag_type,
            related_person_id=related_pid,
            memo=memo
        )
        
        if success:
            st.success(f"✅ '{tag_type}' 태그가 추가되었습니다.")
            st.rerun()
        else:
            st.error("❌ 태그 추가 실패. 다시 시도해주세요.")


def _render_tag_card(tag: dict, key_prefix: str):
    """개별 태그 카드 렌더링"""
    tag_id = tag.get("tag_id", "")
    tag_type = tag.get("tag_type", "")
    memo = tag.get("memo", "")
    related_pid = tag.get("related_person_id", "")
    created_at = tag.get("created_at", "")[:10]
    
    # 관계 대상 이름 조회
    related_name = ""
    if related_pid:
        try:
            related_customer = du.get_customer(related_pid, tag.get("agent_id", ""))
            if related_customer:
                related_name = decrypt_pii(related_customer.get("name", ""))
        except Exception:
            related_name = "(알 수 없음)"
    
    tag_color_map = {
        "상담자": "#3b82f6",
        "계약자": "#10b981",
        "피보험자": "#f59e0b",
        "가족": "#ec4899",
        "소개자": "#8b5cf6",
        "동일법인": "#06b6d4",
        "동일단체": "#14b8a6",
        "친인척": "#f97316"
    }
    color = tag_color_map.get(tag_type, "#6b7280")
    
    col1, col2 = st.columns([5, 1])
    
    with col1:
        st.markdown(f"""
        <div style='background:#ffffff;border:1px dashed {color};border-radius:8px;padding:12px;margin-bottom:8px;'>
            <div style='display:flex;align-items:center;gap:8px;margin-bottom:6px;'>
                <span style='background:{color};color:#fff;padding:4px 10px;border-radius:4px;font-size:0.80rem;font-weight:600;'>
                    {tag_type}
                </span>
                {f"<span style='color:#6b7280;font-size:0.75rem;'>→ {related_name}</span>" if related_name else ""}
                <span style='color:#9ca3af;font-size:0.70rem;margin-left:auto;'>{created_at}</span>
            </div>
            {f"<div style='font-size:0.80rem;color:#4a5568;margin-top:6px;'>{memo}</div>" if memo else ""}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("🗑️", key=f"{key_prefix}_del_{tag_id}", help="태그 삭제"):
            if du.remove_relationship_tag(tag_id):
                st.success("✅ 태그가 삭제되었습니다.")
                st.rerun()
            else:
                st.error("❌ 삭제 실패")


def render_insurance_contracts_panel(person_id: str, agent_id: str, key_prefix: str = "_icp"):
    """
    [GP-PHASE1] 보험계약 이력 패널 (자사/타부점/해지).
    
    Args:
        person_id: 고객 UUID
        agent_id: 담당 설계사
        key_prefix: Streamlit 위젯 키 접두사
    """
    if not person_id or not agent_id:
        st.warning("⚠️ 고객 정보가 없습니다.")
        return
    
    st.markdown("""
    <div style='background:#eff6ff;border:1px dashed #000;border-radius:8px;padding:12px;margin-bottom:16px;'>
        <div style='font-size:0.95rem;font-weight:700;color:#1a1a1a;margin-bottom:8px;'>
            📋 보험계약 이력 관리
        </div>
        <div style='font-size:0.80rem;color:#4a5568;line-height:1.5;'>
            자사계약 · 타부점계약 · 해지계약을 분류하여 관리합니다.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 계약 이력 조회
    contracts = du.get_insurance_contracts(person_id=person_id, agent_id=agent_id)
    
    # 상태별 분류
    own_contracts = [c for c in contracts if c.get("contract_status") == "자사계약"]
    other_contracts = [c for c in contracts if c.get("contract_status") == "타부점계약"]
    terminated_contracts = [c for c in contracts if c.get("contract_status") == "해지계약"]
    
    # 탭으로 분리
    tab1, tab2, tab3, tab4 = st.tabs(["➕ 계약 추가", "🏢 자사계약", "🏪 타부점계약", "❌ 해지계약"])
    
    with tab1:
        _add_contract_form(person_id, agent_id, key_prefix)
    
    with tab2:
        _render_contract_list(own_contracts, "자사계약", key_prefix)
    
    with tab3:
        _render_contract_list(other_contracts, "타부점계약", key_prefix)
    
    with tab4:
        _render_contract_list(terminated_contracts, "해지계약", key_prefix)


def _add_contract_form(person_id: str, agent_id: str, key_prefix: str):
    """보험계약 추가 폼"""
    col1, col2 = st.columns(2)
    
    with col1:
        contract_status = st.selectbox(
            "계약 상태 *",
            options=du.VALID_CONTRACT_STATUS,
            key=f"{key_prefix}_status"
        )
        insurance_company = st.text_input(
            "보험회사 *",
            key=f"{key_prefix}_company"
        )
        product_name = st.text_input(
            "보험상품명 *",
            key=f"{key_prefix}_product"
        )
        contract_date = st.text_input(
            "계약년월 (YYYYMM)",
            placeholder="202601",
            key=f"{key_prefix}_date"
        )
    
    with col2:
        contractor_name = st.text_input(
            "계약자명",
            key=f"{key_prefix}_contractor"
        )
        insured_name = st.text_input(
            "피보험자명",
            key=f"{key_prefix}_insured"
        )
        monthly_premium = st.number_input(
            "월납입보험료 (원)",
            min_value=0,
            step=10000,
            key=f"{key_prefix}_premium"
        )
    
    key_point = st.text_area(
        "비고 (주요 핵심 포인트)",
        placeholder="특약 내용, 보장 특징 등",
        key=f"{key_prefix}_keypoint",
        height=80
    )
    
    # 해지 정보 (해지계약인 경우만)
    if contract_status == "해지계약":
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            termination_date = st.text_input(
                "해지일 (YYYYMMDD)",
                key=f"{key_prefix}_term_date"
            )
        with col_t2:
            termination_reason = st.text_input(
                "해지 사유",
                key=f"{key_prefix}_term_reason"
            )
    else:
        termination_date = ""
        termination_reason = ""
    
    if st.button("💾 계약 저장", key=f"{key_prefix}_save_btn", use_container_width=True):
        if not insurance_company or not product_name:
            st.error("❌ 보험회사와 상품명은 필수입니다.")
            return
        
        # PII 암호화
        contractor_enc = encrypt_pii(contractor_name) if contractor_name else ""
        insured_enc = encrypt_pii(insured_name) if insured_name else ""
        
        success = du.add_insurance_contract(
            person_id=person_id,
            agent_id=agent_id,
            contract_status=contract_status,
            insurance_company=insurance_company,
            product_name=product_name,
            contract_date=contract_date,
            contractor_name=contractor_enc,
            insured_name=insured_enc,
            monthly_premium=float(monthly_premium),
            key_point=key_point,
            termination_date=termination_date,
            termination_reason=termination_reason
        )
        
        if success:
            st.success(f"✅ {contract_status} 정보가 저장되었습니다.")
            st.rerun()
        else:
            st.error("❌ 저장 실패. 다시 시도해주세요.")


def _render_contract_list(contracts: list, status: str, key_prefix: str):
    """계약 목록 렌더링"""
    if not contracts:
        st.info(f"💡 등록된 {status} 정보가 없습니다.")
        return
    
    st.markdown(f"**총 {len(contracts)}건**")
    
    for contract in contracts:
        contract_id = contract.get("contract_id", "")
        company = contract.get("insurance_company", "")
        product = contract.get("product_name", "")
        date = contract.get("contract_date", "")
        premium = contract.get("monthly_premium", 0)
        key_point = contract.get("key_point", "")
        contractor = decrypt_pii(contract.get("contractor_name", "")) if contract.get("contractor_name") else ""
        insured = decrypt_pii(contract.get("insured_name", "")) if contract.get("insured_name") else ""
        
        status_color_map = {
            "자사계약": "#10b981",
            "타부점계약": "#f59e0b",
            "해지계약": "#ef4444"
        }
        color = status_color_map.get(status, "#6b7280")
        
        with st.container():
            col1, col2 = st.columns([5, 1])
            
            with col1:
                st.markdown(f"""
                <div style='background:#ffffff;border:1px dashed {color};border-radius:8px;padding:12px;margin-bottom:12px;'>
                    <div style='display:flex;align-items:center;gap:8px;margin-bottom:8px;'>
                        <span style='background:{color};color:#fff;padding:4px 10px;border-radius:4px;font-size:0.80rem;font-weight:600;'>
                            {status}
                        </span>
                        <span style='font-size:0.90rem;font-weight:700;color:#1a1a1a;'>{company}</span>
                        <span style='color:#6b7280;font-size:0.75rem;margin-left:auto;'>{date}</span>
                    </div>
                    <div style='font-size:0.85rem;color:#4a5568;margin-bottom:4px;'>
                        📄 {product}
                    </div>
                    <div style='font-size:0.80rem;color:#6b7280;'>
                        계약자: {contractor or "(미입력)"} | 피보험자: {insured or "(미입력)"} | 월보험료: {premium:,.0f}원
                    </div>
                    {f"<div style='font-size:0.80rem;color:#059669;margin-top:6px;background:#ecfdf5;padding:6px;border-radius:4px;'>💡 {key_point}</div>" if key_point else ""}
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if st.button("🗑️", key=f"{key_prefix}_del_contract_{contract_id}", help="계약 삭제"):
                    if du.delete_insurance_contract(contract_id):
                        st.success("✅ 삭제되었습니다.")
                        st.rerun()
                    else:
                        st.error("❌ 삭제 실패")


def render_consultation_schedule_panel(person_id: str, agent_id: str, key_prefix: str = "_csp"):
    """
    [GP-PHASE1] 상담 일정 및 내용 패널.
    
    Args:
        person_id: 고객 UUID
        agent_id: 담당 설계사
        key_prefix: Streamlit 위젯 키 접두사
    """
    if not person_id or not agent_id:
        st.warning("⚠️ 고객 정보가 없습니다.")
        return
    
    st.markdown("""
    <div style='background:#f0fdf4;border:1px dashed #000;border-radius:8px;padding:12px;margin-bottom:16px;'>
        <div style='font-size:0.95rem;font-weight:700;color:#1a1a1a;margin-bottom:8px;'>
            📅 상담 일정 및 내용 관리
        </div>
        <div style='font-size:0.80rem;color:#4a5568;line-height:1.5;'>
            초회상담 · 보장분석 · 증권점검 · 계약체결 · 사후관리 등 상담 이력을 기록합니다.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 상담 일정 조회
    schedules = du.get_consultation_schedules(person_id=person_id, agent_id=agent_id)
    
    # 완료/미완료 분류
    pending = [s for s in schedules if not s.get("is_completed")]
    completed = [s for s in schedules if s.get("is_completed")]
    
    # 탭으로 분리
    tab1, tab2, tab3 = st.tabs(["➕ 일정 추가", "⏳ 예정 상담", "✅ 완료 상담"])
    
    with tab1:
        _add_schedule_form(person_id, agent_id, key_prefix)
    
    with tab2:
        _render_schedule_list(pending, False, key_prefix)
    
    with tab3:
        _render_schedule_list(completed, True, key_prefix)


def _add_schedule_form(person_id: str, agent_id: str, key_prefix: str):
    """상담 일정 추가 폼"""
    col1, col2 = st.columns(2)
    
    with col1:
        consultation_type = st.selectbox(
            "상담 유형 *",
            options=du.VALID_CONSULTATION_TYPES,
            key=f"{key_prefix}_type"
        )
        schedule_date = st.text_input(
            "상담 예정일 (YYYYMMDD)",
            placeholder="20260328",
            key=f"{key_prefix}_date"
        )
    
    with col2:
        schedule_time = st.text_input(
            "상담 시간 (HHMM)",
            placeholder="1400",
            key=f"{key_prefix}_time"
        )
    
    consultation_content = st.text_area(
        "상담 내용 요약",
        placeholder="상담 주제, 논의 사항 등",
        key=f"{key_prefix}_content",
        height=100
    )
    
    next_action = st.text_input(
        "다음 액션 아이템",
        placeholder="후속 조치 사항",
        key=f"{key_prefix}_next"
    )
    
    if st.button("📅 일정 저장", key=f"{key_prefix}_save_btn", use_container_width=True):
        success = du.add_consultation_schedule(
            person_id=person_id,
            agent_id=agent_id,
            schedule_date=schedule_date,
            schedule_time=schedule_time,
            consultation_type=consultation_type,
            consultation_content=consultation_content,
            next_action=next_action
        )
        
        if success:
            st.success(f"✅ {consultation_type} 일정이 저장되었습니다.")
            st.rerun()
        else:
            st.error("❌ 저장 실패. 다시 시도해주세요.")


def _render_schedule_list(schedules: list, is_completed: bool, key_prefix: str):
    """상담 일정 목록 렌더링"""
    if not schedules:
        status_text = "완료된" if is_completed else "예정된"
        st.info(f"💡 {status_text} 상담 일정이 없습니다.")
        return
    
    st.markdown(f"**총 {len(schedules)}건**")
    
    for schedule in schedules:
        consultation_id = schedule.get("consultation_id", "")
        cons_type = schedule.get("consultation_type", "")
        date = schedule.get("schedule_date", "")
        time = schedule.get("schedule_time", "")
        content = schedule.get("consultation_content", "")
        result = schedule.get("consultation_result", "")
        next_action = schedule.get("next_action", "")
        
        type_color_map = {
            "초회상담": "#3b82f6",
            "보장분석": "#10b981",
            "증권점검": "#f59e0b",
            "계약체결": "#ec4899",
            "사후관리": "#8b5cf6",
            "기타": "#6b7280"
        }
        color = type_color_map.get(cons_type, "#6b7280")
        
        with st.container():
            col1, col2 = st.columns([5, 1])
            
            with col1:
                st.markdown(f"""
                <div style='background:#ffffff;border:1px dashed {color};border-radius:8px;padding:12px;margin-bottom:12px;'>
                    <div style='display:flex;align-items:center;gap:8px;margin-bottom:8px;'>
                        <span style='background:{color};color:#fff;padding:4px 10px;border-radius:4px;font-size:0.80rem;font-weight:600;'>
                            {cons_type}
                        </span>
                        <span style='font-size:0.85rem;color:#1a1a1a;'>{date} {time}</span>
                        {f"<span style='background:#10b981;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.70rem;margin-left:auto;'>완료</span>" if is_completed else ""}
                    </div>
                    {f"<div style='font-size:0.80rem;color:#4a5568;margin-bottom:6px;'>{content}</div>" if content else ""}
                    {f"<div style='font-size:0.80rem;color:#059669;background:#ecfdf5;padding:6px;border-radius:4px;margin-top:6px;'>✅ 결과: {result}</div>" if result else ""}
                    {f"<div style='font-size:0.80rem;color:#d97706;background:#fffbeb;padding:6px;border-radius:4px;margin-top:6px;'>📌 다음: {next_action}</div>" if next_action else ""}
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if not is_completed:
                    if st.button("✅", key=f"{key_prefix}_complete_{consultation_id}", help="상담 완료"):
                        result_input = st.text_input("상담 결과", key=f"{key_prefix}_result_{consultation_id}")
                        if du.complete_consultation(consultation_id, consultation_result=result_input):
                            st.success("✅ 완료 처리되었습니다.")
                            st.rerun()
