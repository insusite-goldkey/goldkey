"""
hq_autopilot_ui.py — 에이젠틱 오토파일럿 브리핑 UI
[GP-STEP10] Goldkey AI Masters 2026

HQ 브리핑 섹션에 AI 자동 부킹 일정 표시:
- "제가 사장님을 위해 미리 잡아둔 성공 스케줄" 메시지
- 자동 부킹 통계 대시보드
- AI 아이콘(🤖) 표시
"""
from __future__ import annotations
import re, json, datetime
from typing import Optional, Dict, Any, List
import streamlit as st

# ══════════════════════════════════════════════════════════════════════════════
# [1] 에이젠틱 브리핑 박스 (AI Auto-Booking Briefing)
# ══════════════════════════════════════════════════════════════════════════════

def render_autopilot_briefing(agent_id: str):
    """
    에이젠틱 오토파일럿 브리핑 박스
    
    Args:
        agent_id: 설계사 ID
    """
    from hq_automation_engine import get_auto_booking_statistics, search_auto_booked_schedules
    
    # 통계 조회
    stats = get_auto_booking_statistics(agent_id)
    
    if stats.get("total_auto_booked", 0) == 0:
        return
    
    # 이번 주 예정 일정 조회
    today = datetime.datetime.now()
    week_end = today + datetime.timedelta(days=7)
    
    upcoming_schedules = search_auto_booked_schedules(
        agent_id=agent_id,
        start_date=today.isoformat(),
        end_date=week_end.isoformat()
    )
    
    upcoming_count = len(upcoming_schedules)
    
    if upcoming_count == 0:
        return
    
    # 브리핑 박스 렌더링
    st.markdown(
        f"<div style='background:linear-gradient(135deg,#E0E7FF,#DBEAFE);border:2px solid #6366F1;"
        f"border-radius:12px;padding:16px;margin-bottom:16px;position:relative;'>"
        f"<div style='position:absolute;top:12px;right:12px;font-size:1.5rem;'>🤖</div>"
        f"<div style='font-size:1.05rem;font-weight:900;color:#1E3A8A;margin-bottom:8px;'>"
        f"🎯 AI 오토파일럿 브리핑</div>"
        f"<div style='font-size:.88rem;color:#374151;line-height:1.7;'>"
        f"제가 사장님을 위해 미리 잡아둔 <b style='color:#6366F1;'>{upcoming_count}개의 성공 스케줄</b>이 있습니다."
        f"</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    # 이번 주 예정 일정 카드
    for schedule in upcoming_schedules[:3]:  # 최대 3개만 표시
        render_auto_schedule_card(schedule)


def render_auto_schedule_card(schedule: Dict[str, Any]):
    """
    자동 부킹 일정 카드
    
    Args:
        schedule: 일정 데이터
    """
    title = schedule.get("title", "")
    start_dt = schedule.get("start_dt", "")
    memo = schedule.get("memo", "")
    tags = schedule.get("tags", [])
    
    # 날짜 파싱
    try:
        start_datetime = datetime.datetime.fromisoformat(start_dt.replace("Z", "+00:00"))
        date_str = start_datetime.strftime("%m월 %d일 (%a)")
        time_str = start_datetime.strftime("%H:%M")
    except Exception:
        date_str = "날짜 미정"
        time_str = ""
    
    # 태그별 색상
    if "#해피콜" in tags:
        bg_color = "#F0FDF4"  # 소프트 그린
        border_color = "#22C55E"
        icon = "📞"
    elif "#만기관리" in tags:
        bg_color = "#FEE2E2"  # 코랄색
        border_color = "#EF4444"
        icon = "⚠️"
    elif "#제안팔로업" in tags:
        bg_color = "#FEF3C7"  # 골드색
        border_color = "#F59E0B"
        icon = "💡"
    else:
        bg_color = "#F3F4F6"
        border_color = "#9CA3AF"
        icon = "📅"
    
    # 카드 렌더링
    st.markdown(
        f"<div style='background:{bg_color};border:1.5px solid {border_color};"
        f"border-radius:10px;padding:12px;margin-bottom:12px;position:relative;'>"
        f"<div style='position:absolute;top:8px;right:8px;font-size:1rem;'>🤖</div>"
        f"<div style='font-size:.85rem;font-weight:700;color:#374151;margin-bottom:4px;'>"
        f"{icon} {title}</div>"
        f"<div style='font-size:.78rem;color:#64748B;margin-bottom:6px;'>"
        f"📅 {date_str} {time_str}</div>"
        f"<div style='font-size:.75rem;color:#64748B;line-height:1.6;'>"
        f"{memo[:80]}...</div>"
        f"</div>",
        unsafe_allow_html=True
    )


# ══════════════════════════════════════════════════════════════════════════════
# [2] 오토파일럿 통계 대시보드
# ══════════════════════════════════════════════════════════════════════════════

def render_autopilot_dashboard(agent_id: str):
    """
    오토파일럿 통계 대시보드
    
    Args:
        agent_id: 설계사 ID
    """
    from hq_automation_engine import get_auto_booking_statistics
    
    st.markdown(
        "<div style='font-size:1.2rem;font-weight:900;color:#1E3A8A;margin-bottom:16px;'>"
        "🤖 AI 오토파일럿 통계</div>",
        unsafe_allow_html=True
    )
    
    stats = get_auto_booking_statistics(agent_id)
    
    col1, col2, col3, col4 = st.columns(4, gap="medium")
    
    with col1:
        st.markdown(
            "<div style='background:#E0E7FF;border:1.5px solid #6366F1;border-radius:10px;padding:16px;text-align:center;'>"
            "<div style='font-size:.82rem;color:#64748B;margin-bottom:6px;'>총 자동 부킹</div>"
            f"<div style='font-size:1.5rem;font-weight:900;color:#1E3A8A;'>{stats.get('total_auto_booked', 0)}</div>"
            "<div style='font-size:.75rem;color:#64748B;margin-top:4px;'>건</div>"
            "</div>",
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            "<div style='background:#FEF3C7;border:1.5px solid #F59E0B;border-radius:10px;padding:16px;text-align:center;'>"
            "<div style='font-size:.82rem;color:#64748B;margin-bottom:6px;'>제안 팔로업</div>"
            f"<div style='font-size:1.5rem;font-weight:900;color:#92400E;'>{stats.get('proposal_followup', 0)}</div>"
            "<div style='font-size:.75rem;color:#64748B;margin-top:4px;'>건</div>"
            "</div>",
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            "<div style='background:#F0FDF4;border:1.5px solid #22C55E;border-radius:10px;padding:16px;text-align:center;'>"
            "<div style='font-size:.82rem;color:#64748B;margin-bottom:6px;'>해피콜</div>"
            f"<div style='font-size:1.5rem;font-weight:900;color:#166534;'>{stats.get('happy_call', 0)}</div>"
            "<div style='font-size:.75rem;color:#64748B;margin-top:4px;'>건</div>"
            "</div>",
            unsafe_allow_html=True
        )
    
    with col4:
        st.markdown(
            "<div style='background:#FEE2E2;border:1.5px solid #EF4444;border-radius:10px;padding:16px;text-align:center;'>"
            "<div style='font-size:.82rem;color:#64748B;margin-bottom:6px;'>만기 관리</div>"
            f"<div style='font-size:1.5rem;font-weight:900;color:#991B1B;'>{stats.get('car_renewal', 0)}</div>"
            "<div style='font-size:.75rem;color:#64748B;margin-top:4px;'>건</div>"
            "</div>",
            unsafe_allow_html=True
        )
    
    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
    
    # 이번 주 예정 일정
    upcoming_count = stats.get("upcoming_this_week", 0)
    
    if upcoming_count > 0:
        st.markdown(
            f"<div style='background:#DBEAFE;border:1.5px solid #3B82F6;border-radius:10px;padding:12px;'>"
            f"<div style='font-size:.88rem;font-weight:700;color:#1E3A8A;margin-bottom:4px;'>"
            f"📅 이번 주 예정 일정</div>"
            f"<div style='font-size:.82rem;color:#374151;'>"
            f"AI가 자동으로 잡아둔 일정 <b style='color:#3B82F6;'>{upcoming_count}건</b>이 이번 주에 예정되어 있습니다."
            f"</div>"
            f"</div>",
            unsafe_allow_html=True
        )


# ══════════════════════════════════════════════════════════════════════════════
# [3] 자동 부킹 일정 목록
# ══════════════════════════════════════════════════════════════════════════════

def render_auto_booking_list(agent_id: str, tag_filter: Optional[str] = None):
    """
    자동 부킹 일정 목록
    
    Args:
        agent_id: 설계사 ID
        tag_filter: 태그 필터 (선택)
    """
    from hq_automation_engine import search_auto_booked_schedules
    
    st.markdown(
        "<div style='font-size:1.05rem;font-weight:900;color:#1E3A8A;margin-bottom:12px;'>"
        "🤖 AI 자동 부킹 일정</div>",
        unsafe_allow_html=True
    )
    
    # 태그 필터 선택
    filter_options = {
        "all": "전체",
        "#제안팔로업": "💡 제안 팔로업",
        "#해피콜": "📞 해피콜",
        "#만기관리": "⚠️ 만기 관리"
    }
    
    selected_filter = st.radio(
        "필터",
        options=list(filter_options.keys()),
        format_func=lambda x: filter_options[x],
        horizontal=True,
        key="auto_booking_filter",
        label_visibility="collapsed"
    )
    
    # 일정 조회
    if selected_filter == "all":
        schedules = search_auto_booked_schedules(agent_id)
    else:
        schedules = search_auto_booked_schedules(agent_id, tag_filter=selected_filter)
    
    if not schedules:
        st.info("📭 자동 부킹된 일정이 없습니다.")
        return
    
    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    
    # 일정 카드 렌더링
    for schedule in schedules:
        render_auto_schedule_card(schedule)


# ══════════════════════════════════════════════════════════════════════════════
# [4] 수동 트리거 UI (테스트용)
# ══════════════════════════════════════════════════════════════════════════════

def render_manual_trigger_ui(agent_id: str):
    """
    수동 트리거 UI (테스트 및 관리자용)
    
    Args:
        agent_id: 설계사 ID
    """
    st.markdown(
        "<div style='font-size:1.05rem;font-weight:900;color:#1E3A8A;margin-bottom:12px;'>"
        "🔧 수동 트리거 (테스트용)</div>",
        unsafe_allow_html=True
    )
    
    trigger_type = st.selectbox(
        "트리거 유형",
        options=["proposal", "contract", "car_insurance"],
        format_func=lambda x: {
            "proposal": "💡 제안 후 팔로업",
            "contract": "📞 신계약 해피콜",
            "car_insurance": "⚠️ 자동차 보험 만기"
        }[x],
        key="manual_trigger_type"
    )
    
    with st.form(key="manual_trigger_form"):
        col1, col2 = st.columns(2, gap="medium")
        
        with col1:
            person_id = st.text_input("고객 UUID", key="manual_person_id")
            customer_name = st.text_input("고객 이름", key="manual_customer_name")
        
        with col2:
            if trigger_type in ["contract", "car_insurance"]:
                policy_id = st.text_input("증권 ID", key="manual_policy_id")
            
            if trigger_type == "contract":
                contract_date = st.text_input("계약일 (YYYYMMDD)", key="manual_contract_date")
            elif trigger_type == "car_insurance":
                expiry_date = st.text_input("만기일 (YYYYMMDD)", key="manual_expiry_date")
        
        submitted = st.form_submit_button("🚀 트리거 실행", use_container_width=True, type="primary")
        
        if submitted:
            from hq_automation_engine import detect_and_auto_book
            
            # 트리거 데이터 구성
            trigger_data = {
                "person_id": person_id,
                "customer_name": customer_name
            }
            
            if trigger_type == "proposal":
                trigger_data["current_stage"] = 5
            elif trigger_type == "contract":
                trigger_data["policy_id"] = policy_id
                trigger_data["contract_date"] = contract_date
            elif trigger_type == "car_insurance":
                trigger_data["policy_id"] = policy_id
                trigger_data["expiry_date"] = expiry_date
            
            # 트리거 실행
            result = detect_and_auto_book(agent_id, trigger_type, trigger_data)
            
            if result["success"]:
                st.success(f"✅ {result['message']}")
                st.info(f"💡 생성된 일정: {len(result['created_schedules'])}건")
                st.rerun()
            else:
                st.error(f"❌ {result['message']}")


# ══════════════════════════════════════════════════════════════════════════════
# [5] 사용 예시
# ══════════════════════════════════════════════════════════════════════════════

"""
## 사용 예시 (hq_app_impl.py 통합)

### 1. HQ 브리핑 섹션에 오토파일럿 브리핑 추가

```python
from hq_autopilot_ui import render_autopilot_briefing

# HQ 메인 화면 상단
if st.session_state.get("hq_user_id"):
    agent_id = st.session_state["hq_user_id"]
    
    # AI 오토파일럿 브리핑 (최상단)
    render_autopilot_briefing(agent_id)
    
    # 기존 HQ 브리핑 (그 아래)
    from hq_briefing import render_daily_briefing
    render_daily_briefing(agent_id)
```

### 2. 오토파일럿 통계 대시보드

```python
from hq_autopilot_ui import render_autopilot_dashboard

# HQ 통계 화면
if st.session_state.get("hq_spa_screen") == "autopilot":
    agent_id = st.session_state.get("hq_user_id")
    
    if agent_id:
        render_autopilot_dashboard(agent_id)
```

### 3. 자동 부킹 일정 목록

```python
from hq_autopilot_ui import render_auto_booking_list

# HQ 일정 관리 화면
if st.session_state.get("hq_spa_screen") == "schedules":
    agent_id = st.session_state.get("hq_user_id")
    
    if agent_id:
        render_auto_booking_list(agent_id)
```

### 4. 수동 트리거 UI (관리자)

```python
from hq_autopilot_ui import render_manual_trigger_ui

# HQ 관리자 화면
if st.session_state.get("hq_spa_screen") == "admin":
    agent_id = st.session_state.get("hq_user_id")
    
    if agent_id:
        render_manual_trigger_ui(agent_id)
```

## 데이터 흐름

```
[Step 8] AI 제안서 생성
  ↓
gk_people.current_stage = 5 (제안)
  ↓
hq_automation_engine.detect_and_auto_book(trigger_type="proposal")
  ↓
+3일 뒤 오전 10시 팔로업 일정 자동 생성
  ↓
hq_autopilot_ui.render_autopilot_briefing()
  ↓
"제가 사장님을 위해 미리 잡아둔 1개의 성공 스케줄이 있습니다" 표시
  ↓
설계사가 일정 확인 및 실행
```

```
[Step 9] 계약 체결 완료
  ↓
gk_policies.part = 'A' (Direct)
  ↓
hq_automation_engine.detect_and_auto_book(trigger_type="contract")
  ↓
1, 3, 6, 12개월 뒤 해피콜 일정 자동 생성 (총 4건)
  ↓
hq_autopilot_ui.render_autopilot_briefing()
  ↓
"제가 사장님을 위해 미리 잡아둔 4개의 성공 스케줄이 있습니다" 표시
  ↓
캘린더에 소프트 그린(#F0FDF4) 색상으로 표시
```

```
[Step 6] OCR 스캔 (자동차 보험)
  ↓
자동차 보험 + 만기일 감지
  ↓
hq_automation_engine.detect_and_auto_book(trigger_type="car_insurance")
  ↓
만기일, 4주 전, 2주 전 일정 자동 생성 (총 3건)
  ↓
hq_autopilot_ui.render_autopilot_briefing()
  ↓
만기 4주 전 일정이 다가오면 코랄색(#FEE2E2) 경고
  ↓
"놓치면 타사에 뺏길 수 있는 자동차 보험 갱신 건입니다" 브리핑
```
"""
