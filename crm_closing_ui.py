"""
crm_closing_ui.py — 스마트 클로징 및 전자 서명 UI
[GP-STEP9] Goldkey AI Masters 2026

스마트 클로징 모듈:
- 전자 서명 시뮬레이션 (9~10단계: 체결)
- 민트색 폭죽 애니메이션 (성취감 극대화)
- 버킷 자동 업데이트 (섹션 A로 이동)
- 에이전틱 단계 업데이트 (5단계 → 10단계)
"""
from __future__ import annotations
import re, json, datetime
from typing import Optional, Dict, Any, List
import streamlit as st

# ══════════════════════════════════════════════════════════════════════════════
# [1] 데이터 레이어 — 계약 체결 처리
# ══════════════════════════════════════════════════════════════════════════════

def _get_sb():
    """Supabase 클라이언트 가져오기"""
    try:
        from db_utils import _get_sb as _sb
        return _sb()
    except Exception:
        return None


def finalize_contract(
    policy_id: str,
    person_id: str,
    agent_id: str,
    signature_data: str = ""
) -> bool:
    """
    계약 체결 완료 처리
    
    Args:
        policy_id: 증권 UUID
        person_id: 고객 UUID
        agent_id: 설계사 ID
        signature_data: 전자 서명 데이터 (base64)
    
    Returns:
        bool: 성공 여부
    """
    try:
        sb = _get_sb()
        if not sb:
            return False
        
        # 1. gk_policies 업데이트 (part='A', status='ACTIVE')
        policy_result = (
            sb.table("gk_policies")
            .update({
                "part": "A",  # 섹션 A (Direct)로 이동
                "contract_date": datetime.datetime.now().strftime("%Y%m%d"),
                "updated_at": datetime.datetime.now().isoformat()
            })
            .eq("id", policy_id)
            .eq("agent_id", agent_id)
            .execute()
        )
        
        if not policy_result.data:
            return False
        
        # 2. gk_people 업데이트 (current_stage=10: 체결 완료)
        people_result = (
            sb.table("gk_people")
            .update({
                "current_stage": 10,
                "last_contact": datetime.datetime.now().isoformat()
            })
            .eq("person_id", person_id)
            .eq("agent_id", agent_id)
            .execute()
        )
        
        # 3. 전자 서명 데이터 저장 (선택 사항)
        if signature_data:
            # TODO: GCS에 서명 이미지 저장
            pass
        
        return bool(people_result.data)
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# [2] 전자 서명 시뮬레이션 UI
# ══════════════════════════════════════════════════════════════════════════════

def render_signature_pad():
    """
    전자 서명 패드 UI (시뮬레이션)
    
    실제 구현 시 streamlit-drawable-canvas 또는 JavaScript 기반 서명 패드 사용
    """
    st.markdown(
        "<div style='font-size:1.05rem;font-weight:900;color:#1E3A8A;margin-bottom:12px;'>"
        "✍️ 전자 서명</div>",
        unsafe_allow_html=True
    )
    
    # 서명 패드 시뮬레이션 (실제로는 canvas 사용)
    st.markdown(
        "<div style='background:#FFFFFF;border:2px dashed #6366F1;border-radius:10px;"
        "padding:60px 20px;text-align:center;margin-bottom:12px;'>"
        "<div style='font-size:.88rem;color:#64748B;'>서명 영역</div>"
        "<div style='font-size:.75rem;color:#94A3B8;margin-top:8px;'>"
        "실제 구현 시 터치/마우스로 서명 가능</div>"
        "</div>",
        unsafe_allow_html=True
    )
    
    # 서명 확인 체크박스
    signature_confirmed = st.checkbox(
        "✅ 위 내용을 확인하였으며, 전자 서명에 동의합니다.",
        key="signature_confirmed"
    )
    
    return signature_confirmed


# ══════════════════════════════════════════════════════════════════════════════
# [3] 폭죽 애니메이션 (민트색)
# ══════════════════════════════════════════════════════════════════════════════

def render_celebration_animation():
    """
    계약 체결 완료 시 민트색 폭죽 애니메이션
    """
    celebration_html = """
    <style>
    @keyframes confetti-fall {
        0% {
            transform: translateY(-100vh) rotate(0deg);
            opacity: 1;
        }
        100% {
            transform: translateY(100vh) rotate(720deg);
            opacity: 0;
        }
    }
    
    .confetti {
        position: fixed;
        width: 10px;
        height: 10px;
        background: #DCFCE7;
        animation: confetti-fall 3s linear infinite;
        z-index: 9999;
    }
    
    .confetti:nth-child(2n) {
        background: #A7F3D0;
        animation-delay: 0.2s;
    }
    
    .confetti:nth-child(3n) {
        background: #6EE7B7;
        animation-delay: 0.4s;
    }
    
    .confetti:nth-child(4n) {
        background: #34D399;
        animation-delay: 0.6s;
    }
    
    .celebration-message {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: linear-gradient(135deg, #DCFCE7, #A7F3D0);
        border: 3px solid #22C55E;
        border-radius: 20px;
        padding: 40px 60px;
        text-align: center;
        z-index: 10000;
        animation: celebration-bounce 0.6s ease-out;
    }
    
    @keyframes celebration-bounce {
        0% {
            transform: translate(-50%, -50%) scale(0);
        }
        50% {
            transform: translate(-50%, -50%) scale(1.1);
        }
        100% {
            transform: translate(-50%, -50%) scale(1);
        }
    }
    </style>
    
    <div class="celebration-message">
        <div style='font-size:3rem;margin-bottom:16px;'>🎉</div>
        <div style='font-size:1.5rem;font-weight:900;color:#166534;margin-bottom:12px;'>
            계약 체결 완료!
        </div>
        <div style='font-size:1rem;color:#14532D;'>
            축하합니다! 성공적으로 계약이 체결되었습니다.
        </div>
    </div>
    
    <div class="confetti" style="left: 10%;"></div>
    <div class="confetti" style="left: 20%;"></div>
    <div class="confetti" style="left: 30%;"></div>
    <div class="confetti" style="left: 40%;"></div>
    <div class="confetti" style="left: 50%;"></div>
    <div class="confetti" style="left: 60%;"></div>
    <div class="confetti" style="left: 70%;"></div>
    <div class="confetti" style="left: 80%;"></div>
    <div class="confetti" style="left: 90%;"></div>
    """
    
    st.markdown(celebration_html, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# [4] 스마트 클로징 메인 UI
# ══════════════════════════════════════════════════════════════════════════════

def render_smart_closing(
    person_id: str,
    agent_id: str,
    customer_name: str = "",
    proposal_data: Optional[Dict[str, Any]] = None
):
    """
    스마트 클로징 메인 UI
    
    Args:
        person_id: 고객 UUID
        agent_id: 설계사 ID
        customer_name: 고객 이름
        proposal_data: 제안서 데이터 (Step 8)
    """
    st.markdown(
        f"<div style='font-size:1.2rem;font-weight:900;color:#1E3A8A;margin-bottom:16px;'>"
        f"🏆 스마트 클로징 — {customer_name}</div>",
        unsafe_allow_html=True
    )
    
    # 체결 완료 여부 확인
    if st.session_state.get(f"closing_completed_{person_id}"):
        render_celebration_animation()
        
        st.markdown("<div style='margin-top:80px;'></div>", unsafe_allow_html=True)
        
        st.success("✅ 계약이 성공적으로 체결되었습니다!")
        
        # 다음 단계 안내
        st.markdown(
            "<div style='background:#E0E7FF;border:1.5px solid #6366F1;border-radius:10px;"
            "padding:16px;margin-top:16px;'>"
            "<div style='font-size:.88rem;font-weight:700;color:#1E3A8A;margin-bottom:8px;'>"
            "🎯 다음 단계</div>"
            "<div style='font-size:.78rem;color:#374151;line-height:1.7;'>"
            "• 고객 만족도 확인<br>"
            "• 사후 관리 일정 등록<br>"
            "• 소개 요청 (Step 9 리워드 시스템)"
            "</div>"
            "</div>",
            unsafe_allow_html=True
        )
        
        if st.button("🎁 소개 요청하기", key=f"request_referral_{person_id}", use_container_width=True):
            st.session_state[f"show_referral_request_{person_id}"] = True
            st.rerun()
        
        return
    
    # 제안서 요약
    if proposal_data and proposal_data.get("success"):
        render_proposal_summary(proposal_data)
    
    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
    
    # 최종 확인 사항
    render_final_checklist()
    
    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
    
    # 전자 서명 패드
    signature_confirmed = render_signature_pad()
    
    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
    
    # 체결 버튼
    col1, col2 = st.columns([2, 1], gap="medium")
    
    with col1:
        if st.button(
            "🎉 계약 체결 완료",
            key=f"finalize_contract_{person_id}",
            disabled=not signature_confirmed,
            use_container_width=True,
            type="primary"
        ):
            # 계약 체결 처리
            # 실제로는 proposal_data에서 선택된 플랜의 policy_id를 사용
            policy_id = "temp-policy-id"  # TODO: 실제 policy_id 사용
            
            if finalize_contract(policy_id, person_id, agent_id):
                st.session_state[f"closing_completed_{person_id}"] = True
                st.rerun()
            else:
                st.error("❌ 계약 체결 처리에 실패했습니다.")
    
    with col2:
        if st.button("← 뒤로", key=f"back_from_closing_{person_id}", use_container_width=True):
            st.session_state.pop(f"show_closing_{person_id}", None)
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# [5] 제안서 요약
# ══════════════════════════════════════════════════════════════════════════════

def render_proposal_summary(proposal_data: Dict[str, Any]):
    """
    제안서 요약 (최종 확인용)
    
    Args:
        proposal_data: 제안서 데이터
    """
    st.markdown(
        "<div style='font-size:1.05rem;font-weight:900;color:#1E3A8A;margin-bottom:12px;'>"
        "📋 제안서 요약</div>",
        unsafe_allow_html=True
    )
    
    # 선택된 플랜 (기본값: 표준형)
    selected_plan = proposal_data.get("three_plans", [])[1] if len(proposal_data.get("three_plans", [])) > 1 else {}
    
    if not selected_plan:
        st.warning("제안서 데이터가 없습니다.")
        return
    
    plan_type = selected_plan.get("plan_type", "")
    monthly_premium = selected_plan.get("monthly_premium", 0)
    total_coverage = selected_plan.get("total_coverage", "")
    
    st.markdown(
        f"<div style='background:#E0E7FF;border:1.5px solid #6366F1;border-radius:10px;padding:16px;'>"
        f"<div style='font-size:.88rem;font-weight:700;color:#1E3A8A;margin-bottom:8px;'>"
        f"선택 플랜: {plan_type}형</div>"
        f"<div style='font-size:.82rem;color:#374151;margin-bottom:4px;'>"
        f"월 보험료: {monthly_premium:,}원</div>"
        f"<div style='font-size:.82rem;color:#374151;'>"
        f"총 보장: {total_coverage}</div>"
        f"</div>",
        unsafe_allow_html=True
    )


# ══════════════════════════════════════════════════════════════════════════════
# [6] 최종 확인 체크리스트
# ══════════════════════════════════════════════════════════════════════════════

def render_final_checklist():
    """
    계약 체결 전 최종 확인 체크리스트
    """
    st.markdown(
        "<div style='font-size:1.05rem;font-weight:900;color:#1E3A8A;margin-bottom:12px;'>"
        "✅ 최종 확인 사항</div>",
        unsafe_allow_html=True
    )
    
    checklist_items = [
        "보험 상품 내용 및 보장 범위 확인",
        "월 보험료 및 납입 기간 확인",
        "계약자 및 피보험자 정보 확인",
        "약관 및 중요 사항 설명 청취",
        "청약 철회권 안내 확인"
    ]
    
    for idx, item in enumerate(checklist_items):
        st.checkbox(
            item,
            key=f"checklist_{idx}",
            value=False
        )


# ══════════════════════════════════════════════════════════════════════════════
# [7] 사용 예시
# ══════════════════════════════════════════════════════════════════════════════

"""
## 사용 예시 (crm_app_impl.py 통합)

```python
from crm_closing_ui import render_smart_closing

# 스마트 클로징 화면
if st.session_state.get("crm_spa_screen") == "closing":
    person_id = st.session_state.get("crm_selected_pid")
    agent_id = st.session_state.get("crm_user_id")
    customer_name = st.session_state.get("crm_customer_name", "")
    proposal_data = st.session_state.get(f"proposal_{person_id}")
    
    if person_id and agent_id:
        render_smart_closing(person_id, agent_id, customer_name, proposal_data)
```

## 데이터 흐름

```
사용자: [🎉 계약 체결 완료] 버튼 클릭
  ↓
finalize_contract(policy_id, person_id, agent_id)
  ↓
1. gk_policies 업데이트:
   - part = 'A' (섹션 A로 이동)
   - contract_date = 오늘 날짜
  ↓
2. gk_people 업데이트:
   - current_stage = 10 (체결 완료)
   - last_contact = 현재 시각
  ↓
3. 세션 상태 업데이트:
   - closing_completed_{person_id} = True
  ↓
st.rerun()
  ↓
render_celebration_animation() → 민트색 폭죽 🎉
  ↓
다음 단계 안내:
  - 고객 만족도 확인
  - 사후 관리 일정 등록
  - 소개 요청 (리워드 시스템)
```
"""
