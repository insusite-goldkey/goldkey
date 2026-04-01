"""
crm_date_picker.py — 반응형 듀얼 캘린더 피커
[GP-STEP11] Goldkey AI Masters 2026

보험 기간 입력용 듀얼 캘린더 피커:
- 시작일/종료일 각각 선택
- V4 디자인 시스템 준수
- 12px 그리드 및 파스텔톤 테마
- 반응형 레이아웃 (flex-wrap)
"""
from __future__ import annotations
import re, json, datetime
from typing import Optional, Dict, Any, Tuple
import streamlit as st

# ══════════════════════════════════════════════════════════════════════════════
# [1] 듀얼 캘린더 피커 (Dual Calendar Picker)
# ══════════════════════════════════════════════════════════════════════════════

def render_dual_date_picker(
    key_prefix: str = "date_picker",
    default_start: Optional[datetime.date] = None,
    default_end: Optional[datetime.date] = None,
    label_start: str = "시작일",
    label_end: str = "종료일"
) -> Tuple[Optional[datetime.date], Optional[datetime.date]]:
    """
    듀얼 캘린더 피커 (시작일/종료일 각각 선택)
    
    Args:
        key_prefix: 세션 키 접두사
        default_start: 기본 시작일
        default_end: 기본 종료일
        label_start: 시작일 라벨
        label_end: 종료일 라벨
    
    Returns:
        Tuple[date, date]: (시작일, 종료일)
    """
    # 기본값 설정
    if default_start is None:
        default_start = datetime.date.today()
    
    if default_end is None:
        default_end = default_start + datetime.timedelta(days=365)
    
    # V4 디자인 시스템 CSS
    st.markdown(
        """
        <style>
        .dual-date-picker-container {
            background: #F3F4F6;
            border: 1.5px solid #9CA3AF;
            border-radius: 10px;
            padding: 16px;
            margin-bottom: 16px;
        }
        .dual-date-picker-title {
            font-size: 0.88rem;
            font-weight: 700;
            color: #374151;
            margin-bottom: 12px;
        }
        .dual-date-picker-row {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            align-items: flex-start;
        }
        .dual-date-picker-col {
            flex: 1 1 calc(50% - 6px);
            min-width: 200px;
        }
        @media (max-width: 768px) {
            .dual-date-picker-col {
                flex: 1 1 100%;
                min-width: 100%;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # 컨테이너 시작
    st.markdown(
        "<div class='dual-date-picker-container'>"
        "<div class='dual-date-picker-title'>📅 보험 기간 선택</div>"
        "<div class='dual-date-picker-row'>",
        unsafe_allow_html=True
    )
    
    col1, col2 = st.columns(2, gap="medium")
    
    with col1:
        start_date = st.date_input(
            label_start,
            value=default_start,
            key=f"{key_prefix}_start_date",
            format="YYYY-MM-DD"
        )
    
    with col2:
        end_date = st.date_input(
            label_end,
            value=default_end,
            key=f"{key_prefix}_end_date",
            format="YYYY-MM-DD"
        )
    
    # 컨테이너 종료
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    # 유효성 검증
    if start_date and end_date:
        if start_date > end_date:
            st.error("❌ 시작일은 종료일보다 이전이어야 합니다.")
            return None, None
        
        # 기간 계산
        duration = (end_date - start_date).days
        
        st.markdown(
            f"<div style='background:#DBEAFE;border:1.5px solid #3B82F6;border-radius:8px;"
            f"padding:10px;margin-top:8px;font-size:0.82rem;color:#1E3A8A;'>"
            f"📊 보험 기간: <b>{duration}일</b> (약 {duration // 30}개월)</div>",
            unsafe_allow_html=True
        )
    
    return start_date, end_date


# ══════════════════════════════════════════════════════════════════════════════
# [2] 단일 날짜 피커 (Single Date Picker)
# ══════════════════════════════════════════════════════════════════════════════

def render_single_date_picker(
    key: str = "date_picker",
    default_date: Optional[datetime.date] = None,
    label: str = "날짜 선택",
    min_date: Optional[datetime.date] = None,
    max_date: Optional[datetime.date] = None
) -> Optional[datetime.date]:
    """
    단일 날짜 피커
    
    Args:
        key: 세션 키
        default_date: 기본 날짜
        label: 라벨
        min_date: 최소 날짜
        max_date: 최대 날짜
    
    Returns:
        date: 선택된 날짜
    """
    if default_date is None:
        default_date = datetime.date.today()
    
    selected_date = st.date_input(
        label,
        value=default_date,
        key=key,
        min_value=min_date,
        max_value=max_date,
        format="YYYY-MM-DD"
    )
    
    return selected_date


# ══════════════════════════════════════════════════════════════════════════════
# [3] 보험 기간 입력 폼 (Insurance Period Form)
# ══════════════════════════════════════════════════════════════════════════════

def render_insurance_period_form(
    key_prefix: str = "insurance_period",
    policy_category: str = "장기"
) -> Dict[str, Any]:
    """
    보험 기간 입력 폼
    
    Args:
        key_prefix: 세션 키 접두사
        policy_category: 보험 유형 (장기, 자동차, 연간소멸식, 특종)
    
    Returns:
        dict: 입력된 기간 정보
    """
    st.markdown(
        "<div style='font-size:1.05rem;font-weight:900;color:#1E3A8A;margin-bottom:12px;'>"
        "📅 보험 기간 입력</div>",
        unsafe_allow_html=True
    )
    
    # 보험 유형별 기본 기간 설정
    today = datetime.date.today()
    
    if policy_category == "자동차":
        # 자동차 보험: 1년
        default_end = today + datetime.timedelta(days=365)
    elif policy_category == "연간소멸식":
        # 연간소멸식: 1년
        default_end = today + datetime.timedelta(days=365)
    elif policy_category == "특종":
        # 특종: 1년
        default_end = today + datetime.timedelta(days=365)
    else:
        # 장기: 10년
        default_end = today + datetime.timedelta(days=3650)
    
    # 듀얼 캘린더 피커
    start_date, end_date = render_dual_date_picker(
        key_prefix=key_prefix,
        default_start=today,
        default_end=default_end,
        label_start="계약 시작일",
        label_end="만기일"
    )
    
    if not start_date or not end_date:
        return {}
    
    # 기간 정보 반환
    return {
        "start_date": start_date.strftime("%Y%m%d"),
        "end_date": end_date.strftime("%Y%m%d"),
        "duration_days": (end_date - start_date).days,
        "duration_months": (end_date - start_date).days // 30
    }


# ══════════════════════════════════════════════════════════════════════════════
# [4] 날짜 범위 선택기 (Date Range Selector)
# ══════════════════════════════════════════════════════════════════════════════

def render_date_range_selector(
    key_prefix: str = "date_range",
    preset_ranges: bool = True
) -> Tuple[Optional[datetime.date], Optional[datetime.date]]:
    """
    날짜 범위 선택기 (프리셋 옵션 포함)
    
    Args:
        key_prefix: 세션 키 접두사
        preset_ranges: 프리셋 범위 표시 여부
    
    Returns:
        Tuple[date, date]: (시작일, 종료일)
    """
    if preset_ranges:
        st.markdown(
            "<div style='font-size:0.85rem;font-weight:700;color:#64748B;margin-bottom:8px;'>"
            "빠른 선택</div>",
            unsafe_allow_html=True
        )
        
        # 프리셋 범위 버튼
        col1, col2, col3, col4 = st.columns(4, gap="small")
        
        today = datetime.date.today()
        
        with col1:
            if st.button("오늘", key=f"{key_prefix}_today", use_container_width=True):
                st.session_state[f"{key_prefix}_start"] = today
                st.session_state[f"{key_prefix}_end"] = today
        
        with col2:
            if st.button("이번 주", key=f"{key_prefix}_this_week", use_container_width=True):
                start_of_week = today - datetime.timedelta(days=today.weekday())
                st.session_state[f"{key_prefix}_start"] = start_of_week
                st.session_state[f"{key_prefix}_end"] = start_of_week + datetime.timedelta(days=6)
        
        with col3:
            if st.button("이번 달", key=f"{key_prefix}_this_month", use_container_width=True):
                start_of_month = today.replace(day=1)
                st.session_state[f"{key_prefix}_start"] = start_of_month
                st.session_state[f"{key_prefix}_end"] = today
        
        with col4:
            if st.button("올해", key=f"{key_prefix}_this_year", use_container_width=True):
                start_of_year = today.replace(month=1, day=1)
                st.session_state[f"{key_prefix}_start"] = start_of_year
                st.session_state[f"{key_prefix}_end"] = today
        
        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
    
    # 기본값 설정
    default_start = st.session_state.get(f"{key_prefix}_start", datetime.date.today())
    default_end = st.session_state.get(f"{key_prefix}_end", datetime.date.today())
    
    # 듀얼 캘린더 피커
    start_date, end_date = render_dual_date_picker(
        key_prefix=key_prefix,
        default_start=default_start,
        default_end=default_end,
        label_start="시작일",
        label_end="종료일"
    )
    
    return start_date, end_date


# ══════════════════════════════════════════════════════════════════════════════
# [5] 사용 예시
# ══════════════════════════════════════════════════════════════════════════════

"""
## 사용 예시

### 1. 듀얼 캘린더 피커 (기본)

```python
from crm_date_picker import render_dual_date_picker

# 보험 기간 입력
start_date, end_date = render_dual_date_picker(
    key_prefix="policy_period",
    default_start=datetime.date(2026, 4, 1),
    default_end=datetime.date(2027, 4, 1),
    label_start="계약 시작일",
    label_end="만기일"
)

if start_date and end_date:
    print(f"계약 기간: {start_date} ~ {end_date}")
```

### 2. 보험 기간 입력 폼

```python
from crm_date_picker import render_insurance_period_form

# 자동차 보험 기간 입력
period_info = render_insurance_period_form(
    key_prefix="car_insurance",
    policy_category="자동차"
)

if period_info:
    print(f"시작일: {period_info['start_date']}")
    print(f"종료일: {period_info['end_date']}")
    print(f"기간: {period_info['duration_months']}개월")
```

### 3. 날짜 범위 선택기 (프리셋 포함)

```python
from crm_date_picker import render_date_range_selector

# 일정 검색용 날짜 범위 선택
start_date, end_date = render_date_range_selector(
    key_prefix="schedule_range",
    preset_ranges=True
)

if start_date and end_date:
    # 해당 기간의 일정 조회
    schedules = search_schedules(start_date, end_date)
```

### 4. 단일 날짜 피커

```python
from crm_date_picker import render_single_date_picker

# 계약일 선택
contract_date = render_single_date_picker(
    key="contract_date",
    default_date=datetime.date.today(),
    label="계약일",
    min_date=datetime.date(2020, 1, 1),
    max_date=datetime.date.today()
)

if contract_date:
    print(f"계약일: {contract_date}")
```

## Step 7 보험 3버킷 통합

```python
from crm_date_picker import render_insurance_period_form
from hq_policy_manager import auto_schedule_expiry_reminder

# 보험 3버킷 UI에서 신규 계약 입력 시
if st.session_state.get("crm_spa_screen") == "policy_bucket":
    # 보험 기간 입력
    period_info = render_insurance_period_form(
        key_prefix="new_policy",
        policy_category="자동차"
    )
    
    if period_info:
        # 계약 저장
        policy_data = {
            "contract_date": period_info["start_date"],
            "expiry_date": period_info["end_date"],
            "status": "정상",
            "policy_category": "자동차"
        }
        
        # DB 저장
        policy_id = save_policy(policy_data)
        
        # 만기 알림 스케줄 자동 생성
        auto_schedule_expiry_reminder(
            policy_id=policy_id,
            person_id=person_id,
            agent_id=agent_id,
            customer_name=customer_name,
            expiry_date=period_info["end_date"],
            policy_category="자동차",
            status="정상"
        )
```

## 디자인 시스템

### V4 파스텔톤 테마

```css
/* 컨테이너 */
background: #F3F4F6;
border: 1.5px solid #9CA3AF;
border-radius: 10px;

/* 기간 정보 박스 */
background: #DBEAFE;
border: 1.5px solid #3B82F6;
color: #1E3A8A;

/* 12px 그리드 */
gap: 12px;
padding: 16px;
margin-bottom: 16px;
```

### 반응형 레이아웃

```css
/* 데스크톱 */
.dual-date-picker-col {
    flex: 1 1 calc(50% - 6px);
    min-width: 200px;
}

/* 모바일 */
@media (max-width: 768px) {
    .dual-date-picker-col {
        flex: 1 1 100%;
        min-width: 100%;
    }
}
```
"""
