# ══════════════════════════════════════════════════════════════════════════════
# [MODULE] hq_phase4_insurance_contracts_viewer.py
# HQ M-SECTION 보험계약 조회 UI - Phase 4
# gk_insurance_contracts_detail 테이블 데이터 조회 및 표시
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations
import streamlit as st
from typing import Optional


def render_insurance_contracts_viewer(person_id: str, agent_id: str, key_prefix: str = "hq_ic") -> None:
    """
    [GP-PHASE4] HQ M-SECTION 보험계약 조회 UI.
    
    Args:
        person_id: 고객 ID
        agent_id: 설계사 ID
        key_prefix: 세션 키 접두사
    """
    
    if not person_id or not agent_id:
        st.info("💡 고객을 선택하면 보험계약 정보를 조회할 수 있습니다.")
        return
    
    st.markdown("""
    <div style='background:linear-gradient(135deg,#e0f2fe 0%,#bae6fd 50%,#7dd3fc 100%);
      border-radius:12px;padding:14px 18px;margin-bottom:12px;border-left:4px solid #0284c7;'>
      <div style='color:#0c4a6e;font-size:0.95rem;font-weight:900;letter-spacing:0.04em;'>
    📋 보험계약 관리 (Phase 4)
      </div>
      <div style='color:#075985;font-size:0.75rem;margin-top:4px;'>
    A파트(자사) / B파트(타부점) / C파트(해지·승환) 계약 정보 조회
      </div>
    </div>""", unsafe_allow_html=True)
    
    try:
        import db_utils as du
        
        # 보험계약 조회
        contracts = du.get_insurance_contracts(person_id=person_id, agent_id=agent_id)
        
        if not contracts:
            st.info("📭 등록된 보험계약이 없습니다. CRM 앱에서 계약 정보를 입력하세요.")
            return
        
        # 파트별 분류
        part_a = [c for c in contracts if c.get("contract_status") == "자사계약"]
        part_b = [c for c in contracts if c.get("contract_status") == "타부점계약"]
        part_c = [c for c in contracts if c.get("contract_status") == "해지계약"]
        
        # 요약 카드
        _col1, _col2, _col3, _col4 = st.columns(4)
        with _col1:
            st.metric("📄 전체", len(contracts))
        with _col2:
            st.metric("🏢 A파트 (자사)", len(part_a))
        with _col3:
            st.metric("🏪 B파트 (타부점)", len(part_b))
        with _col4:
            st.metric("❌ C파트 (해지)", len(part_c))
        
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        
        # 파트별 탭
        tab_a, tab_b, tab_c = st.tabs(["🏢 A파트 (자사계약)", "🏪 B파트 (타부점계약)", "❌ C파트 (해지계약)"])
        
        with tab_a:
            if part_a:
                _render_contract_table(part_a, "자사계약", key_prefix + "_a")
            else:
                st.info("자사계약이 없습니다.")
        
        with tab_b:
            if part_b:
                _render_contract_table(part_b, "타부점계약", key_prefix + "_b")
            else:
                st.info("타부점계약이 없습니다.")
        
        with tab_c:
            if part_c:
                _render_contract_table(part_c, "해지계약", key_prefix + "_c")
            else:
                st.info("해지계약이 없습니다.")
        
    except Exception as e:
        st.error(f"❌ 보험계약 조회 오류: {e}")


def _render_contract_table(contracts: list[dict], part_name: str, key_prefix: str) -> None:
    """
    보험계약 테이블 렌더링.
    
    Args:
        contracts: 계약 목록
        part_name: 파트 이름
        key_prefix: 키 접두사
    """
    
    st.markdown(f"""
    <div style='background:#f0f9ff;border:1px solid #0284c7;border-radius:8px;padding:10px;
      margin-bottom:10px;'>
      <div style='color:#0c4a6e;font-size:0.8rem;font-weight:800;'>
    {part_name} 목록 (총 {len(contracts)}건)
      </div>
    </div>""", unsafe_allow_html=True)
    
    for idx, contract in enumerate(contracts):
        _company = contract.get("insurance_company", "미확인")
        _product = contract.get("product_name", "미확인")
        _contract_date = contract.get("contract_date", "")
        _premium = contract.get("monthly_premium", 0)
        _status = contract.get("contract_status", "")
        _created_at = contract.get("created_at", "")
        
        # 상태별 색상
        _status_colors = {
            "자사계약": "#3b82f6",
            "타부점계약": "#f59e0b",
            "해지계약": "#ef4444",
        }
        _status_color = _status_colors.get(_status, "#6b7280")
        
        with st.expander(f"{idx+1}. {_company} - {_product} · {_contract_date[:10] if _contract_date else ''}", expanded=False):
            st.markdown(f"""
            <div style='background:#f8fafc;border-radius:8px;padding:12px;'>
              <div style='display:flex;justify-content:space-between;margin-bottom:8px;'>
                <div style='color:#475569;font-size:0.75rem;font-weight:700;'>보험사</div>
                <div style='color:#1e293b;font-size:0.8rem;font-weight:700;'>{_company}</div>
              </div>
              <div style='display:flex;justify-content:space-between;margin-bottom:8px;'>
                <div style='color:#475569;font-size:0.75rem;font-weight:700;'>상품명</div>
                <div style='color:#1e293b;font-size:0.8rem;'>{_product}</div>
              </div>
              <div style='display:flex;justify-content:space-between;margin-bottom:8px;'>
                <div style='color:#475569;font-size:0.75rem;font-weight:700;'>계약일</div>
                <div style='color:#1e293b;font-size:0.8rem;'>{_contract_date[:10] if _contract_date else '미확인'}</div>
              </div>
              <div style='display:flex;justify-content:space-between;margin-bottom:8px;'>
                <div style='color:#475569;font-size:0.75rem;font-weight:700;'>월 보험료</div>
                <div style='color:#1e293b;font-size:0.8rem;font-weight:700;'>{_premium:,}원</div>
              </div>
              <div style='display:flex;justify-content:space-between;margin-bottom:8px;'>
                <div style='color:#475569;font-size:0.75rem;font-weight:700;'>계약 상태</div>
                <div style='background:{_status_color};color:#fff;font-size:0.7rem;font-weight:800;
                  padding:2px 8px;border-radius:12px;'>{_status}</div>
              </div>
              <div style='color:#64748b;font-size:0.7rem;margin-top:8px;'>
                등록일: {_created_at[:10] if _created_at else '미확인'}
              </div>
            </div>""", unsafe_allow_html=True)
            
            # 추가 정보
            _notes = contract.get("notes", "")
            if _notes:
                st.markdown(f"**📝 메모**: {_notes}")
            
            _coverage_summary = contract.get("coverage_summary", "")
            if _coverage_summary:
                st.markdown(f"**📊 보장 요약**: {_coverage_summary}")


def render_insurance_contracts_summary(person_id: str, agent_id: str) -> None:
    """
    [GP-PHASE4] 보험계약 요약 카드 (간단 버전).
    
    Args:
        person_id: 고객 ID
        agent_id: 설계사 ID
    """
    
    if not person_id or not agent_id:
        return
    
    try:
        import db_utils as du
        
        contracts = du.get_insurance_contracts(person_id=person_id, agent_id=agent_id)
        
        if not contracts:
            return
        
        # 파트별 카운트
        part_a_count = len([c for c in contracts if c.get("contract_status") == "자사계약"])
        part_b_count = len([c for c in contracts if c.get("contract_status") == "타부점계약"])
        part_c_count = len([c for c in contracts if c.get("contract_status") == "해지계약"])
        
        st.markdown(f"""
        <div style='background:#e0f2fe;border:1px solid #0284c7;border-radius:8px;padding:10px 12px;
          margin-bottom:8px;'>
          <div style='color:#0c4a6e;font-size:0.75rem;font-weight:800;margin-bottom:4px;'>
        📋 보험계약 현황
          </div>
          <div style='color:#075985;font-size:0.7rem;'>
        A파트 {part_a_count}건 · B파트 {part_b_count}건 · C파트 {part_c_count}건 · 총 {len(contracts)}건
          </div>
        </div>""", unsafe_allow_html=True)
        
    except Exception:
        pass
