"""
crm_referral_ui.py — 소개 요청 및 네트워크 확장 UI
[GP-STEP9] Goldkey AI Masters 2026

소개 요청 UI:
- AI 기반 최적 타이밍 분석
- 3가지 톤 소개 요청 멘트
- 신규 고객 자동 등록
- 마인드맵 자동 연결
"""
from __future__ import annotations
import re, json, datetime
from typing import Optional, Dict, Any
import streamlit as st

# ══════════════════════════════════════════════════════════════════════════════
# [1] 소개 요청 메인 UI
# ══════════════════════════════════════════════════════════════════════════════

def render_referral_request(
    person_id: str,
    agent_id: str,
    customer_name: str = ""
):
    """
    소개 요청 메인 UI
    
    Args:
        person_id: 고객 UUID
        agent_id: 설계사 ID
        customer_name: 고객 이름
    """
    from hq_reward_engine import analyze_referral_timing, generate_referral_scripts
    
    st.markdown(
        f"<div style='font-size:1.2rem;font-weight:900;color:#1E3A8A;margin-bottom:16px;'>"
        f"🎁 소개 요청 — {customer_name}</div>",
        unsafe_allow_html=True
    )
    
    # 1. 소개 요청 타이밍 분석
    timing = analyze_referral_timing(person_id, agent_id)
    
    if not timing.get("ready"):
        st.warning(f"⚠️ {timing.get('reason', '소개 요청 불가')}")
        return
    
    # 타이밍 점수 표시
    score = timing.get("score", 0)
    optimal = timing.get("optimal", False)
    
    if optimal:
        st.success(f"✅ {timing.get('reason', '최적 타이밍입니다!')}")
    else:
        st.info(f"💡 {timing.get('reason', '소개 요청 가능합니다.')}")
    
    # 타이밍 점수 바
    st.markdown(
        f"<div style='background:#F3F4F6;border-radius:10px;padding:12px;margin-bottom:16px;'>"
        f"<div style='font-size:.82rem;font-weight:700;color:#374151;margin-bottom:6px;'>"
        f"소개 요청 타이밍 점수: {score}/100</div>"
        f"<div style='background:#E5E7EB;border-radius:6px;height:12px;overflow:hidden;'>"
        f"<div style='background:linear-gradient(90deg,#22C55E,#10B981);height:100%;width:{score}%;'></div>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
    
    # 2. 소개 요청 멘트 (3가지 톤)
    try:
        from db_utils import _get_sb
        sb = _get_sb()
        if sb:
            customer = (
                sb.table("gk_people")
                .select("job")
                .eq("person_id", person_id)
                .eq("agent_id", agent_id)
                .maybe_single()
                .execute()
            )
            job = customer.data.get("job", "") if customer and customer.data else ""
        else:
            job = ""
    except Exception:
        job = ""
    
    scripts = generate_referral_scripts(customer_name, job)
    
    render_referral_scripts_selector(scripts)
    
    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
    
    # 3. 신규 고객 등록 폼
    render_new_customer_form(person_id, agent_id, customer_name)


# ══════════════════════════════════════════════════════════════════════════════
# [2] 소개 요청 멘트 선택기
# ══════════════════════════════════════════════════════════════════════════════

def render_referral_scripts_selector(scripts: Dict[str, Dict[str, str]]):
    """
    소개 요청 멘트 선택기 (3가지 톤)
    
    Args:
        scripts: 3가지 톤별 소개 요청 멘트
    """
    st.markdown(
        "<div style='font-size:1.05rem;font-weight:900;color:#1E3A8A;margin-bottom:12px;'>"
        "💬 AI 소개 요청 멘트 (3가지 톤)</div>",
        unsafe_allow_html=True
    )
    
    # 톤 선택
    tone_options = {
        "gratitude": "🙏 감사 기반 톤",
        "value": "💎 가치 제안 톤",
        "direct": "🎯 직접 요청 톤"
    }
    
    selected_tone = st.radio(
        "톤 선택",
        options=list(tone_options.keys()),
        format_func=lambda x: tone_options[x],
        horizontal=True,
        key="referral_tone_selector",
        label_visibility="collapsed"
    )
    
    # 선택된 톤의 멘트 표시
    script = scripts.get(selected_tone, {})
    
    if not script:
        return
    
    st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
    
    # 오프닝
    st.markdown(
        "<div style='background:#E0E7FF;border:1.5px solid #6366F1;border-radius:10px;padding:12px;margin-bottom:12px;'>"
        "<div style='font-size:.82rem;font-weight:700;color:#1E3A8A;margin-bottom:6px;'>🎤 오프닝</div>"
        f"<div style='font-size:.78rem;color:#374151;line-height:1.7;'>{script.get('opening', '')}</div>"
        "</div>",
        unsafe_allow_html=True
    )
    
    # 소개 요청
    st.markdown(
        "<div style='background:#DBEAFE;border:1.5px solid #3B82F6;border-radius:10px;padding:12px;margin-bottom:12px;'>"
        "<div style='font-size:.82rem;font-weight:700;color:#1E3A8A;margin-bottom:6px;'>🎁 소개 요청</div>"
        f"<div style='font-size:.78rem;color:#374151;line-height:1.7;'>{script.get('request', '')}</div>"
        "</div>",
        unsafe_allow_html=True
    )
    
    # 인센티브 안내
    st.markdown(
        "<div style='background:#DCFCE7;border:1.5px solid #22C55E;border-radius:10px;padding:12px;'>"
        "<div style='font-size:.82rem;font-weight:700;color:#166534;margin-bottom:6px;'>🎉 인센티브 안내</div>"
        f"<div style='font-size:.78rem;color:#14532D;line-height:1.7;'>{script.get('incentive', '')}</div>"
        "</div>",
        unsafe_allow_html=True
    )


# ══════════════════════════════════════════════════════════════════════════════
# [3] 신규 고객 등록 폼
# ══════════════════════════════════════════════════════════════════════════════

def render_new_customer_form(referrer_id: str, agent_id: str, referrer_name: str):
    """
    신규 고객 등록 폼 (소개받은 고객)
    
    Args:
        referrer_id: 소개자 UUID
        agent_id: 설계사 ID
        referrer_name: 소개자 이름
    """
    st.markdown(
        "<div style='font-size:1.05rem;font-weight:900;color:#1E3A8A;margin-bottom:12px;'>"
        "👤 소개받은 신규 고객 등록</div>",
        unsafe_allow_html=True
    )
    
    with st.form(key=f"new_customer_form_{referrer_id}"):
        col1, col2 = st.columns(2, gap="medium")
        
        with col1:
            referee_name = st.text_input(
                "이름",
                key=f"referee_name_{referrer_id}",
                placeholder="홍길동"
            )
        
        with col2:
            referee_contact = st.text_input(
                "연락처",
                key=f"referee_contact_{referrer_id}",
                placeholder="010-1234-5678"
            )
        
        referral_note = st.text_area(
            "소개 메모 (선택)",
            key=f"referral_note_{referrer_id}",
            placeholder=f"{referrer_name}님이 소개해 주신 분입니다.",
            height=80
        )
        
        submitted = st.form_submit_button(
            "✅ 신규 고객 등록 및 소개자 연결",
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            if not referee_name or not referee_contact:
                st.error("❌ 이름과 연락처를 모두 입력해 주세요.")
            else:
                # 신규 고객 등록 및 네트워크 연결
                from hq_reward_engine import auto_connect_referral_network, update_customer_stage_to_referral
                
                referee_id = auto_connect_referral_network(
                    referrer_id=referrer_id,
                    referee_name=referee_name,
                    referee_contact=referee_contact,
                    agent_id=agent_id
                )
                
                if referee_id:
                    # 소개자 단계 업데이트 (10단계 → 12단계)
                    update_customer_stage_to_referral(referrer_id, agent_id, target_stage=12)
                    
                    st.success(f"✅ {referee_name}님이 신규 고객으로 등록되었습니다!")
                    st.info(f"💡 {referrer_name}님께 10,000 포인트가 적립되었습니다.")
                    st.info(f"🔗 Step 5 마인드맵에 '{referrer_name} → {referee_name}' 소개자 라인이 자동으로 연결되었습니다.")
                    
                    # 세션 상태 업데이트
                    st.session_state[f"referral_completed_{referrer_id}"] = True
                    
                    st.rerun()
                else:
                    st.error("❌ 신규 고객 등록에 실패했습니다. 다시 시도해 주세요.")


# ══════════════════════════════════════════════════════════════════════════════
# [4] 리워드 현황 표시
# ══════════════════════════════════════════════════════════════════════════════

def render_reward_dashboard(agent_id: str):
    """
    설계사 리워드 현황 대시보드
    
    Args:
        agent_id: 설계사 ID
    """
    from hq_reward_engine import get_reward_statistics
    
    st.markdown(
        "<div style='font-size:1.2rem;font-weight:900;color:#1E3A8A;margin-bottom:16px;'>"
        "🏆 나의 리워드 현황</div>",
        unsafe_allow_html=True
    )
    
    stats = get_reward_statistics(agent_id)
    
    col1, col2, col3 = st.columns(3, gap="medium")
    
    with col1:
        st.markdown(
            "<div style='background:#E0E7FF;border:1.5px solid #6366F1;border-radius:10px;padding:16px;text-align:center;'>"
            "<div style='font-size:.82rem;color:#64748B;margin-bottom:6px;'>총 포인트</div>"
            f"<div style='font-size:1.5rem;font-weight:900;color:#1E3A8A;'>{stats.get('total_points', 0):,}</div>"
            "<div style='font-size:.75rem;color:#64748B;margin-top:4px;'>P</div>"
            "</div>",
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            "<div style='background:#DCFCE7;border:1.5px solid #22C55E;border-radius:10px;padding:16px;text-align:center;'>"
            "<div style='font-size:.82rem;color:#64748B;margin-bottom:6px;'>받은 기프티콘</div>"
            f"<div style='font-size:1.5rem;font-weight:900;color:#166534;'>{stats.get('total_gifts', 0)}</div>"
            "<div style='font-size:.75rem;color:#64748B;margin-top:4px;'>개</div>"
            "</div>",
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            "<div style='background:#FEF3C7;border:1.5px solid #F59E0B;border-radius:10px;padding:16px;text-align:center;'>"
            "<div style='font-size:.82rem;color:#64748B;margin-bottom:6px;'>소개 성공</div>"
            f"<div style='font-size:1.5rem;font-weight:900;color:#92400E;'>{stats.get('total_referrals', 0)}</div>"
            "<div style='font-size:.75rem;color:#64748B;margin-top:4px;'>건</div>"
            "</div>",
            unsafe_allow_html=True
        )


# ══════════════════════════════════════════════════════════════════════════════
# [5] 사용 예시
# ══════════════════════════════════════════════════════════════════════════════

"""
## 사용 예시 (crm_app_impl.py 통합)

```python
from crm_referral_ui import render_referral_request, render_reward_dashboard

# 소개 요청 화면
if st.session_state.get("crm_spa_screen") == "referral":
    person_id = st.session_state.get("crm_selected_pid")
    agent_id = st.session_state.get("crm_user_id")
    customer_name = st.session_state.get("crm_customer_name", "")
    
    if person_id and agent_id:
        render_referral_request(person_id, agent_id, customer_name)

# 리워드 대시보드
if st.session_state.get("crm_spa_screen") == "rewards":
    agent_id = st.session_state.get("crm_user_id")
    
    if agent_id:
        render_reward_dashboard(agent_id)
```

## 데이터 흐름

```
사용자: [🎁 소개 요청하기] 버튼 클릭
  ↓
analyze_referral_timing(person_id, agent_id)
  ↓
if ready:
  generate_referral_scripts(customer_name, job)
  ↓
  설계사가 3가지 톤 멘트 확인
  ↓
  신규 고객 정보 입력 (이름, 연락처)
  ↓
  [✅ 신규 고객 등록 및 소개자 연결] 버튼 클릭
  ↓
  auto_connect_referral_network(referrer_id, referee_name, referee_contact, agent_id)
  ↓
  1. gk_people에 신규 고객 생성 (current_stage=1)
  2. gk_relationships에 '소개자' 관계 추가
  3. gk_rewards에 리워드 부여 (10,000 포인트)
  ↓
  update_customer_stage_to_referral(referrer_id, agent_id, 12)
  ↓
  Step 5 마인드맵에 '소개자' 라인 자동 표시
  ↓
  성공 메시지 표시 + st.rerun()
```
"""
