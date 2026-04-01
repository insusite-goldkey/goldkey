"""
crm_policy_bucket_ui.py — 지능형 보험 3버킷(Triple-Bucket) 관리 시스템
[GP-STEP7] Goldkey AI Masters 2026

보험 3버킷 관리 시스템:
- 섹션 A (Direct): 설계사 직접 관리 계약 (part='A')
- 섹션 B (External): 타사/타인 설계사 계약 (part='B')
- 섹션 C (Legacy): 해지/승환 과거 계약 (part='C')
- 유기적 데이터 이동 로직 (Migration Engine)
"""
from __future__ import annotations
import re, json, datetime
from typing import Optional, Dict, Any, List
import streamlit as st

# ══════════════════════════════════════════════════════════════════════════════
# [1] 데이터 레이어 — gk_policies 조회 및 part 업데이트
# ══════════════════════════════════════════════════════════════════════════════

def _get_sb():
    """Supabase 클라이언트 가져오기"""
    try:
        from db_utils import _get_sb as _sb
        return _sb()
    except Exception:
        return None


def get_policies_by_bucket(
    person_id: str,
    agent_id: str,
    part: str = "A"
) -> List[Dict[str, Any]]:
    """
    버킷별 보험 계약 조회
    
    Args:
        person_id: 고객 UUID
        agent_id: 설계사 ID
        part: 버킷 구분 ('A', 'B', 'C')
    
    Returns:
        list: 보험 계약 목록
    """
    try:
        sb = _get_sb()
        if not sb:
            return []
        
        # gk_policy_roles를 통해 person_id와 연결된 증권 조회
        # part 필드가 없으므로 gk_policies에 part 컬럼 추가 필요
        # 임시로 source 필드를 활용하거나 별도 컬럼 추가 권장
        
        # gk_policy_roles 조인 조회
        result = (
            sb.table("gk_policy_roles")
            .select("*, gk_policies!inner(*)")
            .eq("person_id", person_id)
            .eq("agent_id", agent_id)
            .eq("is_deleted", False)
            .execute()
        )
        
        policies = []
        for role_data in (result.data or []):
            policy = role_data.get("gk_policies") or {}
            
            # part 필드 확인 (없으면 기본값 'A')
            policy_part = policy.get("part", "A")
            
            if policy_part == part:
                policies.append({
                    "policy_id": policy.get("id"),
                    "policy_number": policy.get("policy_number", ""),
                    "insurance_company": policy.get("insurance_company", ""),
                    "product_name": policy.get("product_name", ""),
                    "premium": policy.get("premium", 0),
                    "contract_date": policy.get("contract_date", ""),
                    "expiry_date": policy.get("expiry_date", ""),
                    "part": policy_part,
                    "role": role_data.get("role", ""),
                    "role_id": role_data.get("role_id", "")
                })
        
        return policies
    except Exception:
        return []


def migrate_policy_to_bucket(
    policy_id: str,
    agent_id: str,
    target_part: str = "C"
) -> bool:
    """
    보험 계약을 다른 버킷으로 이동 (part 업데이트)
    
    Args:
        policy_id: 증권 UUID
        agent_id: 설계사 ID
        target_part: 목표 버킷 ('A', 'B', 'C')
    
    Returns:
        bool: 성공 여부
    """
    try:
        sb = _get_sb()
        if not sb:
            return False
        
        # gk_policies 테이블의 part 컬럼 업데이트
        result = (
            sb.table("gk_policies")
            .update({"part": target_part})
            .eq("id", policy_id)
            .eq("agent_id", agent_id)
            .execute()
        )
        
        return bool(result.data)
    except Exception:
        return False


def get_ai_policy_summary(policy_data: Dict[str, Any]) -> str:
    """
    AI 기반 보험 계약 특이사항 요약
    
    Args:
        policy_data: 보험 계약 정보
    
    Returns:
        str: AI 요약 텍스트
    """
    # TODO: HQ AI 엔진 연동
    # 현재는 규칙 기반 요약
    
    expiry_date = policy_data.get("expiry_date", "")
    premium = policy_data.get("premium", 0)
    
    summary_parts = []
    
    # 만기 임박 체크
    if expiry_date:
        try:
            from datetime import datetime, timedelta
            expiry_dt = datetime.strptime(expiry_date[:8], "%Y%m%d")
            today = datetime.now()
            days_left = (expiry_dt - today).days
            
            if 0 < days_left <= 90:
                summary_parts.append(f"⚠️ 만기 {days_left}일 전")
            elif days_left <= 0:
                summary_parts.append("⛔ 만기 도래")
        except Exception:
            pass
    
    # 고액 보험료 체크
    if premium and float(premium) >= 500000:
        summary_parts.append("💰 고액 보험료 (50만원 이상)")
    
    # 기본 메시지
    if not summary_parts:
        summary_parts.append("✅ 정상 유지 중")
    
    return " · ".join(summary_parts)


# ══════════════════════════════════════════════════════════════════════════════
# [2] 고밀도 정책 카드 디자인 (12px Grid)
# ══════════════════════════════════════════════════════════════════════════════

def render_policy_card(
    policy_data: Dict[str, Any],
    bucket_type: str,
    person_id: str,
    agent_id: str
):
    """
    고밀도 정책 카드 렌더링
    
    Args:
        policy_data: 보험 계약 정보
        bucket_type: 버킷 구분 ('A', 'B', 'C')
        person_id: 고객 UUID
        agent_id: 설계사 ID
    """
    policy_id = policy_data.get("policy_id", "")
    policy_number = policy_data.get("policy_number", "미등록")
    insurance_company = policy_data.get("insurance_company", "보험사 미상")
    product_name = policy_data.get("product_name", "상품명 미상")
    premium = policy_data.get("premium", 0)
    role = policy_data.get("role", "")
    
    # 버킷별 배경색
    bucket_colors = {
        "A": "#E0E7FF",  # 소프트 인디고
        "B": "#F9FAFB",  # 소프트 그레이
        "C": "#FEE2E2"   # 소프트 코랄
    }
    
    bg_color = bucket_colors.get(bucket_type, "#F3F4F6")
    
    # AI 요약
    ai_summary = get_ai_policy_summary(policy_data)
    
    # 카드 HTML
    card_html = f"""
    <div style='background:{bg_color};border:1px solid #374151;border-radius:10px;
    padding:12px;margin-bottom:12px;transition:all 0.3s ease;'>
        <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;'>
            <div style='font-size:clamp(0.88rem,2vw,0.95rem);font-weight:900;color:#1E3A8A;'>
                {insurance_company}
            </div>
            <div style='font-size:clamp(0.72rem,1.8vw,0.78rem);color:#64748B;'>
                {role}
            </div>
        </div>
        
        <div style='font-size:clamp(0.82rem,1.9vw,0.88rem);color:#374151;margin-bottom:6px;'>
            {product_name}
        </div>
        
        <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;'>
            <div style='font-size:clamp(0.78rem,1.85vw,0.85rem);font-weight:700;color:#1E3A8A;'>
                월 {int(premium):,}원
            </div>
            <div style='font-size:clamp(0.72rem,1.8vw,0.78rem);color:#64748B;'>
                증권번호: {policy_number[:10]}...
            </div>
        </div>
        
        <div style='background:rgba(255,255,255,0.5);border-radius:6px;padding:6px 8px;
        font-size:clamp(0.72rem,1.8vw,0.78rem);color:#475569;margin-bottom:8px;'>
            {ai_summary}
        </div>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)
    
    # 버튼 영역 (섹션 A, B만 표시)
    if bucket_type in ["A", "B"]:
        col1, col2 = st.columns(2, gap="small")
        
        with col1:
            if st.button(
                "🔄 승환",
                key=f"convert_{policy_id}",
                use_container_width=True,
                help="이 계약을 승환하여 Legacy로 이동"
            ):
                if migrate_policy_to_bucket(policy_id, agent_id, "C"):
                    st.success("✅ 승환 처리되었습니다.")
                    st.rerun()
                else:
                    st.error("❌ 승환 처리에 실패했습니다.")
        
        with col2:
            if st.button(
                "❌ 해지",
                key=f"cancel_{policy_id}",
                use_container_width=True,
                help="이 계약을 해지하여 Legacy로 이동"
            ):
                if migrate_policy_to_bucket(policy_id, agent_id, "C"):
                    st.success("✅ 해지 처리되었습니다.")
                    st.rerun()
                else:
                    st.error("❌ 해지 처리에 실패했습니다.")


# ══════════════════════════════════════════════════════════════════════════════
# [3] 3분할 버킷 레이아웃
# ══════════════════════════════════════════════════════════════════════════════

def render_bucket_section(
    bucket_type: str,
    bucket_title: str,
    bucket_description: str,
    policies: List[Dict[str, Any]],
    person_id: str,
    agent_id: str
):
    """
    버킷 섹션 렌더링
    
    Args:
        bucket_type: 버킷 구분 ('A', 'B', 'C')
        bucket_title: 버킷 제목
        bucket_description: 버킷 설명
        policies: 보험 계약 목록
        person_id: 고객 UUID
        agent_id: 설계사 ID
    """
    st.markdown(
        f"<div style='font-size:1.05rem;font-weight:900;color:#1E3A8A;margin-bottom:8px;'>"
        f"{bucket_title}</div>",
        unsafe_allow_html=True
    )
    
    st.markdown(
        f"<div style='font-size:0.78rem;color:#64748B;margin-bottom:12px;'>"
        f"{bucket_description}</div>",
        unsafe_allow_html=True
    )
    
    if not policies:
        st.info(f"등록된 계약이 없습니다.")
        return
    
    # 정책 카드 렌더링
    for policy in policies:
        render_policy_card(policy, bucket_type, person_id, agent_id)


# ══════════════════════════════════════════════════════════════════════════════
# [4] 메인 렌더링 함수 — 3분할 반응형 레이아웃
# ══════════════════════════════════════════════════════════════════════════════

def render_policy_bucket_system(person_id: str, agent_id: str, customer_name: str = ""):
    """
    지능형 보험 3버킷 관리 시스템 메인 렌더링
    
    Args:
        person_id: 고객 UUID
        agent_id: 설계사 ID
        customer_name: 고객 이름
    """
    st.markdown(
        f"<div style='font-size:1.2rem;font-weight:900;color:#1E3A8A;margin-bottom:16px;'>"
        f"💳 보험 3버킷 관리 시스템 — {customer_name}</div>",
        unsafe_allow_html=True
    )
    
    # 3분할 반응형 레이아웃 CSS
    st.markdown("""
    <style>
    /* 3분할 버킷 레이아웃 — 태블릿 가로: 3열, 모바일: 1열 스택 */
    .gp-bucket-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        margin-bottom: 12px;
    }
    
    @media (max-width: 1024px) {
        .gp-bucket-grid {
            grid-template-columns: 1fr;
        }
    }
    
    /* 버킷 블록 공통 스타일 */
    .gp-bucket-block {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 14px;
        min-height: 300px;
    }
    
    /* 카드 이동 애니메이션 */
    @keyframes card-migrate {
        0% {
            opacity: 1;
            transform: translateX(0);
        }
        50% {
            opacity: 0.3;
            transform: translateX(20px);
        }
        100% {
            opacity: 0;
            transform: translateX(40px);
        }
    }
    
    .card-migrating {
        animation: card-migrate 0.5s ease-out forwards;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 데이터 조회
    policies_a = get_policies_by_bucket(person_id, agent_id, "A")
    policies_b = get_policies_by_bucket(person_id, agent_id, "B")
    policies_c = get_policies_by_bucket(person_id, agent_id, "C")
    
    # 3분할 레이아웃
    col1, col2, col3 = st.columns(3, gap="medium")
    
    with col1:
        # 섹션 A (Direct): 설계사 직접 관리 계약
        st.markdown("<div class='gp-bucket-block'>", unsafe_allow_html=True)
        render_bucket_section(
            bucket_type="A",
            bucket_title="🟦 섹션 A (Direct)",
            bucket_description="설계사가 직접 관리하는 계약",
            policies=policies_a,
            person_id=person_id,
            agent_id=agent_id
        )
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        # 섹션 B (External): 타사/타인 설계사 계약
        st.markdown("<div class='gp-bucket-block'>", unsafe_allow_html=True)
        render_bucket_section(
            bucket_type="B",
            bucket_title="⬜ 섹션 B (External)",
            bucket_description="타사/타인 설계사가 가입한 계약",
            policies=policies_b,
            person_id=person_id,
            agent_id=agent_id
        )
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        # 섹션 C (Legacy): 해지/승환 과거 계약
        st.markdown("<div class='gp-bucket-block'>", unsafe_allow_html=True)
        render_bucket_section(
            bucket_type="C",
            bucket_title="🟥 섹션 C (Legacy)",
            bucket_description="해지 또는 승환된 과거 계약",
            policies=policies_c,
            person_id=person_id,
            agent_id=agent_id
        )
        st.markdown("</div>", unsafe_allow_html=True)
    
    # 통계 요약
    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    
    total_a = len(policies_a)
    total_b = len(policies_b)
    total_c = len(policies_c)
    
    premium_a = sum(float(p.get("premium", 0) or 0) for p in policies_a)
    premium_b = sum(float(p.get("premium", 0) or 0) for p in policies_b)
    premium_c = sum(float(p.get("premium", 0) or 0) for p in policies_c)
    
    st.markdown(
        f"<div style='background:linear-gradient(135deg,#F0FDF4,#DCFCE7);"
        f"border:1.5px solid #22C55E;border-radius:10px;padding:12px;'>"
        f"<div style='font-size:.88rem;font-weight:700;color:#166534;margin-bottom:6px;'>"
        f"📊 보험 포트폴리오 요약</div>"
        f"<div style='display:flex;justify-content:space-between;font-size:.78rem;color:#14532D;'>"
        f"<div>Direct: {total_a}건 ({int(premium_a):,}원)</div>"
        f"<div>External: {total_b}건 ({int(premium_b):,}원)</div>"
        f"<div>Legacy: {total_c}건 ({int(premium_c):,}원)</div>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True
    )


# ══════════════════════════════════════════════════════════════════════════════
# [5] gk_policies 테이블 part 컬럼 추가 SQL
# ══════════════════════════════════════════════════════════════════════════════

"""
## gk_policies 테이블 확장 (part 컬럼 추가)

```sql
-- part 컬럼 추가 (A: Direct, B: External, C: Legacy)
ALTER TABLE gk_policies ADD COLUMN IF NOT EXISTS part TEXT DEFAULT 'A'
    CHECK (part IN ('A', 'B', 'C'));

-- 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_gk_policies_part ON gk_policies(part);

-- 주석 추가
COMMENT ON COLUMN gk_policies.part IS '보험 버킷 구분 (A: Direct, B: External, C: Legacy)';
```

## 사용 예시 (crm_client_detail.py 통합)

```python
from crm_policy_bucket_ui import render_policy_bucket_system

# 고객 상세 페이지 하단에 3버킷 시스템 렌더링
if st.session_state.get("crm_spa_mode") == "customer":
    person_id = st.session_state.get("crm_selected_pid")
    agent_id = st.session_state.get("crm_user_id")
    customer_name = st.session_state.get("crm_customer_name", "")
    
    if person_id and agent_id:
        # 고객 상세 정보 (Step 5)
        render_client_detail_page(person_id, agent_id)
        
        # 보험 3버킷 시스템 (Step 7)
        st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
        render_policy_bucket_system(person_id, agent_id, customer_name)
```

## 데이터 흐름

```
사용자: [해지] 버튼 클릭
  ↓
migrate_policy_to_bucket(policy_id, agent_id, "C")
  ↓
gk_policies 테이블 UPDATE:
  - part = 'C'
  ↓
st.rerun() → 화면 새로고침
  ↓
get_policies_by_bucket(person_id, agent_id, "C")
  ↓
섹션 C (Legacy)에 카드 표시
```
"""
