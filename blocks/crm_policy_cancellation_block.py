# ══════════════════════════════════════════════════════════════════════════════
# [BLOCK] crm_policy_cancellation_block.py
# STEP 4.5: 계약 중도 해지 시 미래 스케줄 자동 삭제 UI
# 2026-03-29 신규 생성 - GP 전술 명령 4.5
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations
import streamlit as st
from typing import Optional


def render_policy_cancellation_ui(
    policy_id: str,
    policy_data: dict,
    agent_id: str,
) -> None:
    """
    [STEP 4.5] 계약 해지/유지 상태 변경 UI 렌더링.
    
    Args:
        policy_id: 계약 ID
        policy_data: 계약 정보 딕셔너리
        agent_id: 담당 설계사 ID
    """
    if not policy_id or not policy_data:
        return
    
    # ── 헤더 ──────────────────────────────────────────────────────────────
    st.markdown(
        "<div style='background:linear-gradient(135deg, #ef4444 0%, #dc2626 100%);"
        "border-radius:12px;padding:16px;margin:20px 0 16px 0;'>"
        "<div style='font-size:1.1rem;font-weight:700;color:#fff;margin-bottom:6px;'>"
        "🚫 계약 상태 관리</div>"
        "<div style='font-size:0.78rem;color:#fecaca;line-height:1.6;'>"
        "계약을 해지하면 미래의 사후 관리 일정이 자동으로 삭제됩니다. (과거 이력은 보존)</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    
    # ── 현재 상태 표시 ────────────────────────────────────────────────────
    current_status = policy_data.get("status", "active")
    is_cancelled = current_status in ("cancelled", "terminated", "해지", "취소")
    
    status_color = "#dc2626" if is_cancelled else "#059669"
    status_text = "해지됨" if is_cancelled else "유지 중"
    status_icon = "🚫" if is_cancelled else "✅"
    
    st.markdown(
        f"<div style='background:#f9fafb;border:1px dashed #000;border-radius:8px;"
        f"padding:12px 16px;margin-bottom:16px;'>"
        f"<div style='font-size:0.88rem;font-weight:700;color:{status_color};'>"
        f"{status_icon} 현재 상태: {status_text}</div>"
        f"<div style='font-size:0.75rem;color:#6b7280;margin-top:4px;'>"
        f"증권번호: {policy_data.get('policy_number', 'N/A')}</div>"
        f"<div style='font-size:0.75rem;color:#6b7280;'>"
        f"보험사: {policy_data.get('insurance_company', 'N/A')}</div>"
        f"<div style='font-size:0.75rem;color:#6b7280;'>"
        f"상품명: {policy_data.get('product_name', 'N/A')}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    
    # ── 상태 변경 UI ──────────────────────────────────────────────────────
    st.markdown("### 📝 계약 상태 변경")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        new_status = st.selectbox(
            "새로운 상태 선택",
            options=["active", "cancelled", "terminated"],
            format_func=lambda x: {
                "active": "✅ 유지 중",
                "cancelled": "🚫 해지",
                "terminated": "🚫 취소",
            }.get(x, x),
            index=0 if not is_cancelled else 1,
            key=f"policy_status_{policy_id}",
        )
    
    with col2:
        update_btn = st.button(
            "💾 상태 저장",
            key=f"update_status_{policy_id}",
            type="primary",
            use_container_width=True,
        )
    
    # ── 상태 변경 처리 ────────────────────────────────────────────────────
    if update_btn:
        if new_status == current_status:
            st.info("ℹ️ 상태가 변경되지 않았습니다.")
            return
        
        # Supabase 업데이트
        try:
            from db_utils import get_supabase_client
            import datetime
            
            sb = get_supabase_client()
            sb.table("policies").update({
                "status": new_status,
                "updated_at": datetime.datetime.utcnow().isoformat(),
            }).eq("id", policy_id).execute()
            
            st.success(f"✅ 계약 상태가 '{new_status}'로 변경되었습니다.")
            
            # [STEP 4.5] 해지 상태로 변경 시 미래 일정 자동 삭제
            if new_status in ("cancelled", "terminated"):
                with st.spinner("🗑️ 미래 사후 관리 일정 삭제 중..."):
                    from db_utils import cancel_future_schedules
                    
                    result = cancel_future_schedules(
                        policy_id=policy_id,
                        agent_id=agent_id,
                    )
                    
                    if result.get("success"):
                        deleted_count = result.get("deleted_count", 0)
                        preserved_count = result.get("preserved_count", 0)
                        
                        st.success(
                            f"✅ 미래 일정 {deleted_count}건 삭제 완료\n\n"
                            f"📋 과거 일정 {preserved_count}건 보존 (활동 이력)"
                        )
                        
                        # 삭제된 일정 목록 표시
                        if result.get("deleted_schedules"):
                            with st.expander("🗑️ 삭제된 일정 목록", expanded=False):
                                for schedule in result["deleted_schedules"]:
                                    st.caption(
                                        f"• {schedule.get('date')}: {schedule.get('title')}"
                                    )
                    else:
                        st.warning(
                            f"⚠️ 일정 삭제 실패: {result.get('error', '알 수 없는 오류')}"
                        )
            
            # 페이지 새로고침
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ 상태 변경 실패: {e}")
    
    # ── 안내 메시지 ───────────────────────────────────────────────────────
    st.markdown(
        "<div style='background:#fef3c7;border-left:4px solid #f59e0b;"
        "border-radius:8px;padding:12px 16px;margin-top:16px;'>"
        "<div style='font-size:0.82rem;color:#92400e;line-height:1.7;'>"
        "⚠️ <b>중요 안내</b><br>"
        "• 계약을 해지하면 <b>미래의 사후 관리 일정</b>이 자동으로 삭제됩니다.<br>"
        "• <b>과거 일정</b>(오늘 이전)은 설계사의 활동 이력으로 보존됩니다.<br>"
        "• 해지 후 재활성화 시 일정을 다시 생성해야 합니다."
        "</div></div>",
        unsafe_allow_html=True,
    )


def render_policy_status_badge(policy_data: dict) -> None:
    """
    계약 상태 배지 렌더링 (간단한 표시용).
    
    Args:
        policy_data: 계약 정보 딕셔너리
    """
    if not policy_data:
        return
    
    status = policy_data.get("status", "active")
    is_cancelled = status in ("cancelled", "terminated", "해지", "취소")
    
    if is_cancelled:
        st.markdown(
            "<span style='background:#fee2e2;color:#991b1b;padding:4px 10px;"
            "border-radius:6px;font-size:0.75rem;font-weight:700;'>"
            "🚫 해지됨</span>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<span style='background:#d1fae5;color:#065f46;padding:4px 10px;"
            "border-radius:6px;font-size:0.75rem;font-weight:700;'>"
            "✅ 유지 중</span>",
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# 테스트용 샘플 함수
# ══════════════════════════════════════════════════════════════════════════════
def test_policy_cancellation_ui():
    """테스트용 계약 해지 UI 렌더링."""
    st.title("🧪 계약 해지 UI 테스트")
    
    # 샘플 데이터
    sample_policy = {
        "id": "test-policy-001",
        "policy_number": "P2026-001",
        "insurance_company": "KB손해보험",
        "product_name": "실손의료보험",
        "status": "active",
        "contract_date": "2026-03-29",
    }
    
    render_policy_cancellation_ui(
        policy_id=sample_policy["id"],
        policy_data=sample_policy,
        agent_id="test-agent-001",
    )


if __name__ == "__main__":
    test_policy_cancellation_ui()
