"""
crm_policy_status_ui.py — 에이젠틱 상태 제어 버튼 UI
[GP-STEP11] Goldkey AI Masters 2026

계약 상태 제어 UI:
- 승환해지/실효해지/일반해지 버튼
- 상태 변경 시 미래 일정 자동 삭제
- V4 디자인 시스템 준수
- 피드백 메시지 표시
"""
from __future__ import annotations
import re, json, datetime
from typing import Optional, Dict, Any
import streamlit as st

# ══════════════════════════════════════════════════════════════════════════════
# [1] 상태 제어 버튼 그룹
# ══════════════════════════════════════════════════════════════════════════════

def render_policy_status_controls(
    policy_id: str,
    agent_id: str,
    current_status: str = "정상",
    policy_category: str = "장기"
) -> Optional[str]:
    """
    계약 상태 제어 버튼 그룹
    
    Args:
        policy_id: 증권 ID
        agent_id: 설계사 ID
        current_status: 현재 상태
        policy_category: 보험 유형
    
    Returns:
        str: 변경된 상태 또는 None
    """
    st.markdown(
        "<div style='font-size:0.88rem;font-weight:700;color:#374151;margin-bottom:8px;'>"
        "⚙️ 계약 상태 관리</div>",
        unsafe_allow_html=True
    )
    
    # 현재 상태 표시
    status_colors = {
        "정상": "#DCFCE7",
        "실효": "#FEF3C7",
        "해지": "#FEE2E2",
        "철회": "#E5E7EB",
        "갱신": "#DBEAFE"
    }
    
    status_color = status_colors.get(current_status, "#F3F4F6")
    
    st.markdown(
        f"<div style='background:{status_color};border:1.5px solid #9CA3AF;border-radius:8px;"
        f"padding:10px;margin-bottom:12px;font-size:0.82rem;color:#374151;text-align:center;'>"
        f"현재 상태: <b>{current_status}</b></div>",
        unsafe_allow_html=True
    )
    
    # 상태가 '정상'일 때만 변경 버튼 표시
    if current_status != "정상":
        st.info(f"💡 이 계약은 이미 '{current_status}' 상태입니다.")
        return None
    
    # 상태 변경 버튼
    col1, col2, col3 = st.columns(3, gap="small")
    
    with col1:
        if st.button(
            "🔄 승환해지",
            key=f"convert_cancel_{policy_id}",
            use_container_width=True,
            help="다른 상품으로 전환하며 해지"
        ):
            return "승환해지"
    
    with col2:
        if st.button(
            "⚠️ 실효해지",
            key=f"lapse_cancel_{policy_id}",
            use_container_width=True,
            help="보험료 미납으로 인한 실효"
        ):
            return "실효"
    
    with col3:
        if st.button(
            "❌ 일반해지",
            key=f"normal_cancel_{policy_id}",
            use_container_width=True,
            help="고객 요청에 의한 일반 해지"
        ):
            return "해지"
    
    # 자동차 보험인 경우 갱신 버튼 추가
    if policy_category == "자동차":
        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
        
        if st.button(
            "🔄 갱신",
            key=f"renew_{policy_id}",
            use_container_width=True,
            type="primary",
            help="차년도 계약 자동 생성"
        ):
            return "갱신"
    
    return None


# ══════════════════════════════════════════════════════════════════════════════
# [2] 상태 변경 확인 다이얼로그
# ══════════════════════════════════════════════════════════════════════════════

@st.dialog("계약 상태 변경 확인", width="medium")
def show_status_change_confirmation(
    policy_id: str,
    agent_id: str,
    new_status: str,
    customer_name: str = ""
):
    """
    상태 변경 확인 다이얼로그
    
    Args:
        policy_id: 증권 ID
        agent_id: 설계사 ID
        new_status: 변경할 상태
        customer_name: 고객 이름
    """
    st.markdown(
        f"<div style='font-size:0.95rem;color:#374151;line-height:1.7;margin-bottom:16px;'>"
        f"<b>{customer_name}</b>님의 계약을 <b style='color:#EF4444;'>{new_status}</b> 상태로 변경하시겠습니까?"
        f"</div>",
        unsafe_allow_html=True
    )
    
    # 경고 메시지
    if new_status in ["해지", "실효", "철회"]:
        st.warning(
            f"⚠️ {new_status} 처리 시 해당 계약과 연결된 **모든 미래 일정이 자동으로 삭제**됩니다."
        )
    
    # 변경 사유 입력
    reason = st.text_area(
        "변경 사유 (선택)",
        key=f"status_change_reason_{policy_id}",
        placeholder="예: 고객 요청, 타사 전환, 보험료 부담 등",
        height=80
    )
    
    col1, col2 = st.columns(2, gap="medium")
    
    with col1:
        if st.button("취소", key=f"cancel_status_change_{policy_id}", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button(
            "확인",
            key=f"confirm_status_change_{policy_id}",
            use_container_width=True,
            type="primary"
        ):
            # 상태 변경 실행
            from hq_policy_manager import update_policy_status
            
            result = update_policy_status(
                policy_id=policy_id,
                agent_id=agent_id,
                new_status=new_status,
                reason=reason,
                changed_by=agent_id
            )
            
            if result["success"]:
                st.success(f"✅ {result['message']}")
                
                # 세션 상태 업데이트
                st.session_state[f"policy_status_changed_{policy_id}"] = True
                st.session_state[f"policy_new_status_{policy_id}"] = new_status
                
                st.rerun()
            else:
                st.error(f"❌ {result['message']}")


# ══════════════════════════════════════════════════════════════════════════════
# [3] 갱신 확인 다이얼로그
# ══════════════════════════════════════════════════════════════════════════════

@st.dialog("자동차 보험 갱신", width="medium")
def show_renewal_confirmation(
    policy_id: str,
    agent_id: str,
    customer_name: str = ""
):
    """
    갱신 확인 다이얼로그
    
    Args:
        policy_id: 증권 ID
        agent_id: 설계사 ID
        customer_name: 고객 이름
    """
    st.markdown(
        f"<div style='font-size:0.95rem;color:#374151;line-height:1.7;margin-bottom:16px;'>"
        f"<b>{customer_name}</b>님의 자동차 보험을 갱신하시겠습니까?"
        f"</div>",
        unsafe_allow_html=True
    )
    
    st.info(
        "💡 갱신 처리 시 차년도 계약이 자동으로 생성되고, "
        "새로운 만기 알림 일정이 자동으로 배치됩니다."
    )
    
    # 갱신일 선택
    from crm_date_picker import render_single_date_picker
    
    renewal_date = render_single_date_picker(
        key=f"renewal_date_{policy_id}",
        default_date=datetime.date.today(),
        label="갱신일",
        min_date=datetime.date.today()
    )
    
    col1, col2 = st.columns(2, gap="medium")
    
    with col1:
        if st.button("취소", key=f"cancel_renewal_{policy_id}", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button(
            "갱신",
            key=f"confirm_renewal_{policy_id}",
            use_container_width=True,
            type="primary"
        ):
            # 갱신 실행
            from hq_policy_manager import auto_renew_policy
            
            new_policy_id = auto_renew_policy(
                policy_id=policy_id,
                agent_id=agent_id,
                renewal_date=renewal_date.strftime("%Y%m%d")
            )
            
            if new_policy_id:
                st.success(
                    f"✅ 차년도 계약이 자동으로 생성되었습니다. (새 증권 ID: {new_policy_id})\n\n"
                    f"💡 기존 증권의 미래 일정이 삭제되고, 새 증권에 대한 만기 알림이 자동으로 생성되었습니다."
                )
                
                # 세션 상태 업데이트
                st.session_state[f"policy_renewed_{policy_id}"] = True
                st.session_state[f"new_policy_id_{policy_id}"] = new_policy_id
                
                st.rerun()
            else:
                st.error("❌ 갱신 처리에 실패했습니다. 다시 시도해 주세요.")


# ══════════════════════════════════════════════════════════════════════════════
# [4] 통합 상태 제어 UI
# ══════════════════════════════════════════════════════════════════════════════

def render_policy_lifecycle_controls(
    policy_id: str,
    agent_id: str,
    customer_name: str = "",
    current_status: str = "정상",
    policy_category: str = "장기"
):
    """
    통합 계약 생애주기 제어 UI
    
    Args:
        policy_id: 증권 ID
        agent_id: 설계사 ID
        customer_name: 고객 이름
        current_status: 현재 상태
        policy_category: 보험 유형
    """
    # 상태 제어 버튼
    selected_action = render_policy_status_controls(
        policy_id=policy_id,
        agent_id=agent_id,
        current_status=current_status,
        policy_category=policy_category
    )
    
    # 액션 실행
    if selected_action:
        if selected_action == "갱신":
            # 갱신 확인 다이얼로그
            show_renewal_confirmation(
                policy_id=policy_id,
                agent_id=agent_id,
                customer_name=customer_name
            )
        else:
            # 상태 변경 확인 다이얼로그
            show_status_change_confirmation(
                policy_id=policy_id,
                agent_id=agent_id,
                new_status=selected_action,
                customer_name=customer_name
            )


# ══════════════════════════════════════════════════════════════════════════════
# [5] 계약 생애주기 통계 대시보드
# ══════════════════════════════════════════════════════════════════════════════

def render_policy_lifecycle_dashboard(agent_id: str):
    """
    계약 생애주기 통계 대시보드
    
    Args:
        agent_id: 설계사 ID
    """
    from hq_policy_manager import get_policy_lifecycle_statistics
    
    st.markdown(
        "<div style='font-size:1.2rem;font-weight:900;color:#1E3A8A;margin-bottom:16px;'>"
        "📊 계약 생애주기 통계</div>",
        unsafe_allow_html=True
    )
    
    stats = get_policy_lifecycle_statistics(agent_id)
    
    col1, col2, col3, col4 = st.columns(4, gap="medium")
    
    with col1:
        st.markdown(
            "<div style='background:#DCFCE7;border:1.5px solid #22C55E;border-radius:10px;padding:16px;text-align:center;'>"
            "<div style='font-size:.82rem;color:#64748B;margin-bottom:6px;'>정상 계약</div>"
            f"<div style='font-size:1.5rem;font-weight:900;color:#166534;'>{stats.get('active_policies', 0)}</div>"
            "<div style='font-size:.75rem;color:#64748B;margin-top:4px;'>건</div>"
            "</div>",
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            "<div style='background:#FEF3C7;border:1.5px solid #F59E0B;border-radius:10px;padding:16px;text-align:center;'>"
            "<div style='font-size:.82rem;color:#64748B;margin-bottom:6px;'>실효</div>"
            f"<div style='font-size:1.5rem;font-weight:900;color:#92400E;'>{stats.get('expired_policies', 0)}</div>"
            "<div style='font-size:.75rem;color:#64748B;margin-top:4px;'>건</div>"
            "</div>",
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            "<div style='background:#FEE2E2;border:1.5px solid #EF4444;border-radius:10px;padding:16px;text-align:center;'>"
            "<div style='font-size:.82rem;color:#64748B;margin-bottom:6px;'>해지</div>"
            f"<div style='font-size:1.5rem;font-weight:900;color:#991B1B;'>{stats.get('cancelled_policies', 0)}</div>"
            "<div style='font-size:.75rem;color:#64748B;margin-top:4px;'>건</div>"
            "</div>",
            unsafe_allow_html=True
        )
    
    with col4:
        st.markdown(
            "<div style='background:#DBEAFE;border:1.5px solid #3B82F6;border-radius:10px;padding:16px;text-align:center;'>"
            "<div style='font-size:.82rem;color:#64748B;margin-bottom:6px;'>갱신</div>"
            f"<div style='font-size:1.5rem;font-weight:900;color:#1E3A8A;'>{stats.get('renewed_policies', 0)}</div>"
            "<div style='font-size:.75rem;color:#64748B;margin-top:4px;'>건</div>"
            "</div>",
            unsafe_allow_html=True
        )
    
    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
    
    # 보험 유형별 통계
    col5, col6 = st.columns(2, gap="medium")
    
    with col5:
        st.markdown(
            "<div style='background:#E0E7FF;border:1.5px solid #6366F1;border-radius:10px;padding:16px;text-align:center;'>"
            "<div style='font-size:.82rem;color:#64748B;margin-bottom:6px;'>자동차 보험</div>"
            f"<div style='font-size:1.5rem;font-weight:900;color:#1E3A8A;'>{stats.get('car_insurance_count', 0)}</div>"
            "<div style='font-size:.75rem;color:#64748B;margin-top:4px;'>건</div>"
            "</div>",
            unsafe_allow_html=True
        )
    
    with col6:
        st.markdown(
            "<div style='background:#F3F4F6;border:1.5px solid #9CA3AF;border-radius:10px;padding:16px;text-align:center;'>"
            "<div style='font-size:.82rem;color:#64748B;margin-bottom:6px;'>장기 보험</div>"
            f"<div style='font-size:1.5rem;font-weight:900;color:#374151;'>{stats.get('long_term_count', 0)}</div>"
            "<div style='font-size:.75rem;color:#64748B;margin-top:4px;'>건</div>"
            "</div>",
            unsafe_allow_html=True
        )


# ══════════════════════════════════════════════════════════════════════════════
# [6] 사용 예시
# ══════════════════════════════════════════════════════════════════════════════

"""
## 사용 예시

### 1. Step 7 보험 3버킷 카드에 상태 제어 버튼 추가

```python
from crm_policy_status_ui import render_policy_lifecycle_controls

# 보험 3버킷 카드 렌더링 시
def render_policy_card(policy_data):
    policy_id = policy_data.get("policy_id")
    agent_id = st.session_state.get("crm_user_id")
    customer_name = policy_data.get("customer_name", "")
    current_status = policy_data.get("status", "정상")
    policy_category = policy_data.get("policy_category", "장기")
    
    # 기존 카드 내용 렌더링
    st.markdown(f"### {policy_data.get('product_name')}")
    st.markdown(f"만기일: {policy_data.get('expiry_date')}")
    
    # 상태 제어 버튼 추가
    render_policy_lifecycle_controls(
        policy_id=policy_id,
        agent_id=agent_id,
        customer_name=customer_name,
        current_status=current_status,
        policy_category=policy_category
    )
```

### 2. HQ 통계 화면에 생애주기 대시보드 추가

```python
from crm_policy_status_ui import render_policy_lifecycle_dashboard

# HQ 통계 화면
if st.session_state.get("hq_spa_screen") == "policy_stats":
    agent_id = st.session_state.get("hq_user_id")
    
    if agent_id:
        render_policy_lifecycle_dashboard(agent_id)
```

## 데이터 흐름

### 해지 처리

```
[Step 7] 보험 3버킷 카드에서 [일반해지] 버튼 클릭
  ↓
show_status_change_confirmation() 다이얼로그 표시
  ↓
사용자가 변경 사유 입력 후 [확인] 클릭
  ↓
update_policy_status(new_status="해지")
  ↓
gk_policies.update({status: "해지"})
  ↓
gk_policy_status_history.insert({
    old_status: "정상",
    new_status: "해지",
    reason: "고객 요청"
})
  ↓
auto_clean_future_schedules()
  ↓
해당 증권과 연결된 미래 일정 삭제
  ↓
"상태가 '해지'로 변경되었습니다. 관련된 미래 일정 3건이 함께 삭제되었습니다." 메시지 표시
  ↓
st.rerun()
```

### 자동차 보험 갱신

```
[Step 7] 보험 3버킷 카드에서 [갱신] 버튼 클릭
  ↓
show_renewal_confirmation() 다이얼로그 표시
  ↓
사용자가 갱신일 선택 후 [갱신] 클릭
  ↓
auto_renew_policy()
  ↓
기존 증권 정보 조회
  ↓
차년도 만기일 계산 (갱신일 + 1년)
  ↓
gk_policies.insert({
    expiry_date: "20271201",
    status: "정상"
})
  ↓
기존 증권 상태 변경 (status: "갱신")
  ↓
기존 증권 미래 일정 삭제
  ↓
새 증권에 대한 만기 알림 스케줄 생성
  ↓
"차년도 계약이 자동으로 생성되었습니다." 메시지 표시
  ↓
st.rerun()
```
"""
