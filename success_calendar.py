"""
success_calendar.py — 석세스 캘린더 (Outlook Style + Quick Links)
[GP-STEP4] Goldkey AI Masters 2026

아웃룩 스타일의 정밀한 캘린더 시스템:
- 연도/월 선택 모달
- 고객 퀵링크 (@) 자동완성
- 해시태그 (#) 필터링
- 반복 일정 시스템
- 심리적 컬러 코딩 (12단계 세일즈 프로세스 기반)
- HQ 브리핑 실시간 동기화
"""
from __future__ import annotations
import re, json, datetime
from typing import Optional
import streamlit as st

# ══════════════════════════════════════════════════════════════════════════════
# [1] 12단계 세일즈 프로세스 기반 심리적 컬러 코딩
# ══════════════════════════════════════════════════════════════════════════════

SALES_PROCESS_COLORS = {
    # 1~3단계: 초기 접촉 및 정보 수집 → 블루 계열
    "step_1_3": {
        "name": "초기 접촉·정보 수집",
        "color": "#DBEAFE",  # 소프트 블루
        "border": "#3B82F6",
        "stages": ["초기 접촉", "니즈 파악", "정보 수집"],
        "keywords": ["초기", "접촉", "명함", "소개", "니즈", "질문", "정보", "스캔", "수집"]
    },
    # 4~6단계: 분석 및 제안 → 퍼플 계열
    "step_4_6": {
        "name": "분석·제안",
        "color": "#E9D5FF",  # 소프트 퍼플
        "border": "#A855F7",
        "stages": ["분석 진행", "리포트 작성", "1차 제안"],
        "keywords": ["분석", "리포트", "보고서", "제안", "설계", "견적"]
    },
    # 7~9단계: 협상 및 계약 준비 → 옐로우 계열
    "step_7_9": {
        "name": "협상·계약 준비",
        "color": "#FEF9C3",  # 소프트 옐로우
        "border": "#F59E0B",
        "stages": ["이의 처리", "2차 제안", "계약 준비"],
        "keywords": ["이의", "FAQ", "수정", "협상", "계약", "준비", "청약"]
    },
    # 10단계: 계약 체결 → 민트 그린
    "step_10": {
        "name": "계약 체결",
        "color": "#DCFCE7",  # 민트 그린
        "border": "#22C55E",
        "stages": ["계약 체결"],
        "keywords": ["계약", "체결", "서명", "완료"]
    },
    # 11~12단계: 사후 관리 및 재계약 → 그린 계열
    "step_11_12": {
        "name": "사후 관리·재계약",
        "color": "#F0FDF4",  # 소프트 그린
        "border": "#22C55E",
        "stages": ["사후 관리", "재계약·추천"],
        "keywords": ["사후", "관리", "캘린더", "알림", "재계약", "추천", "네트워크"]
    },
    # 긴급/정체: 3일 이상 정체된 고객 → 코랄
    "urgent": {
        "name": "긴급·정체",
        "color": "#FEE2E2",  # 코랄
        "border": "#EF4444",
        "stages": ["긴급", "정체"],
        "keywords": ["긴급", "정체", "stuck", "지연", "미응답"]
    }
}

def detect_stage_color(title: str, memo: str, category: str = "") -> dict:
    """
    일정 제목과 메모에서 키워드를 추출하여 12단계 세일즈 프로세스 기반 컬러를 자동 배정
    
    Returns:
        dict: {"color": "#DBEAFE", "border": "#3B82F6", "stage_name": "초기 접촉·정보 수집"}
    """
    text = (title + " " + memo).lower()
    
    # 긴급/정체 우선 체크
    if any(kw in text for kw in SALES_PROCESS_COLORS["urgent"]["keywords"]):
        return {
            "color": SALES_PROCESS_COLORS["urgent"]["color"],
            "border": SALES_PROCESS_COLORS["urgent"]["border"],
            "stage_name": SALES_PROCESS_COLORS["urgent"]["name"]
        }
    
    # 10단계 (계약 체결) 체크
    if any(kw in text for kw in SALES_PROCESS_COLORS["step_10"]["keywords"]):
        return {
            "color": SALES_PROCESS_COLORS["step_10"]["color"],
            "border": SALES_PROCESS_COLORS["step_10"]["border"],
            "stage_name": SALES_PROCESS_COLORS["step_10"]["name"]
        }
    
    # 11~12단계 체크
    if any(kw in text for kw in SALES_PROCESS_COLORS["step_11_12"]["keywords"]):
        return {
            "color": SALES_PROCESS_COLORS["step_11_12"]["color"],
            "border": SALES_PROCESS_COLORS["step_11_12"]["border"],
            "stage_name": SALES_PROCESS_COLORS["step_11_12"]["name"]
        }
    
    # 7~9단계 체크
    if any(kw in text for kw in SALES_PROCESS_COLORS["step_7_9"]["keywords"]):
        return {
            "color": SALES_PROCESS_COLORS["step_7_9"]["color"],
            "border": SALES_PROCESS_COLORS["step_7_9"]["border"],
            "stage_name": SALES_PROCESS_COLORS["step_7_9"]["name"]
        }
    
    # 4~6단계 체크
    if any(kw in text for kw in SALES_PROCESS_COLORS["step_4_6"]["keywords"]):
        return {
            "color": SALES_PROCESS_COLORS["step_4_6"]["color"],
            "border": SALES_PROCESS_COLORS["step_4_6"]["border"],
            "stage_name": SALES_PROCESS_COLORS["step_4_6"]["name"]
        }
    
    # 1~3단계 (기본값)
    return {
        "color": SALES_PROCESS_COLORS["step_1_3"]["color"],
        "border": SALES_PROCESS_COLORS["step_1_3"]["border"],
        "stage_name": SALES_PROCESS_COLORS["step_1_3"]["name"]
    }


# ══════════════════════════════════════════════════════════════════════════════
# [2] 고객 퀵링크 (@) 자동완성 시스템
# ══════════════════════════════════════════════════════════════════════════════

def search_customers_by_name(agent_id: str, query: str, limit: int = 10) -> list[dict]:
    """
    gk_people 테이블에서 고객 이름 검색 (@ 자동완성용)
    
    Args:
        agent_id: 설계사 ID
        query: 검색 쿼리 (예: "홍길")
        limit: 최대 결과 수
    
    Returns:
        list[dict]: [{"person_id": "uuid", "name": "홍길동", "birth_date": "1990-01-01"}, ...]
    """
    try:
        from db_utils import _get_sb
        sb = _get_sb()
        if not sb or not query.strip():
            return []
        
        # ilike 검색 (대소문자 무시)
        result = (
            sb.table("gk_people")
            .select("person_id, name, birth_date, contact")
            .eq("agent_id", agent_id)
            .eq("is_deleted", False)
            .ilike("name", f"%{query.strip()}%")
            .order("name")
            .limit(limit)
            .execute()
        )
        
        return result.data or []
    except Exception:
        return []


def render_customer_quick_link_selector(agent_id: str, key_prefix: str = "cal") -> Optional[dict]:
    """
    고객 퀵링크 선택 UI 렌더링
    
    Returns:
        dict: {"person_id": "uuid", "name": "홍길동"} 또는 None
    """
    st.markdown(
        "<div style='font-size:.82rem;font-weight:700;color:#374151;margin-bottom:4px;'>"
        "👤 고객 찾기 (@ 퀵링크)</div>",
        unsafe_allow_html=True
    )
    
    _search_key = f"{key_prefix}_customer_search"
    _search_query = st.text_input(
        "고객 이름 검색",
        key=_search_key,
        placeholder="예: 홍길동",
        label_visibility="collapsed"
    )
    
    if _search_query and len(_search_query) >= 1:
        customers = search_customers_by_name(agent_id, _search_query, limit=8)
        
        if customers:
            st.markdown(
                "<div style='font-size:.75rem;color:#64748b;margin:4px 0;'>"
                f"🔍 {len(customers)}명 검색됨 — 클릭하여 선택</div>",
                unsafe_allow_html=True
            )
            
            for idx, cust in enumerate(customers):
                cust_name = cust.get("name", "")
                cust_id = cust.get("person_id", "")
                birth_date = cust.get("birth_date", "")
                
                if st.button(
                    f"@{cust_name} ({birth_date[:10] if birth_date else '생년월일 미등록'})",
                    key=f"{key_prefix}_cust_sel_{idx}_{cust_id}",
                    use_container_width=True
                ):
                    return {"person_id": cust_id, "name": cust_name}
        else:
            st.caption("검색 결과가 없습니다.")
    
    return None


# ══════════════════════════════════════════════════════════════════════════════
# [3] 연도/월 선택 모달
# ══════════════════════════════════════════════════════════════════════════════

@st.dialog("📅 연도/월 선택", width="small")
def show_year_month_picker(current_year: int, current_month: int):
    """
    연도/월 선택 모달 다이얼로그
    
    Args:
        current_year: 현재 연도
        current_month: 현재 월
    """
    st.markdown(
        "<div style='font-size:.88rem;color:#475569;margin-bottom:12px;'>"
        "이동할 연도와 월을 선택하세요.</div>",
        unsafe_allow_html=True
    )
    
    # 연도 선택 (현재 연도 ±5년)
    year_options = list(range(current_year - 5, current_year + 6))
    selected_year = st.selectbox(
        "연도",
        options=year_options,
        index=year_options.index(current_year) if current_year in year_options else 5,
        key="year_picker_select"
    )
    
    # 월 선택
    month_options = list(range(1, 13))
    selected_month = st.selectbox(
        "월",
        options=month_options,
        format_func=lambda m: f"{m}월",
        index=current_month - 1,
        key="month_picker_select"
    )
    
    # 이동 버튼
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ 이동", key="year_month_confirm", use_container_width=True):
            st.session_state["current_month"] = f"{selected_year:04d}-{selected_month:02d}"
            st.rerun()
    with col2:
        if st.button("취소", key="year_month_cancel", use_container_width=True):
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# [4] HQ 브리핑 동기화 확인
# ══════════════════════════════════════════════════════════════════════════════

def sync_schedule_to_hq_briefing(agent_id: str, schedule_data: dict) -> bool:
    """
    일정 저장 시 HQ 브리핑 시스템에 동기화
    
    Note:
        calendar_engine.py의 cal_save() 함수가 이미 gk_schedules 테이블에 저장하므로,
        hq_briefing.py의 get_daily_briefing()이 자동으로 최신 데이터를 조회합니다.
        
        추가 동기화 로직이 필요한 경우 여기에 구현하세요.
    
    Args:
        agent_id: 설계사 ID
        schedule_data: 일정 데이터
    
    Returns:
        bool: 동기화 성공 여부
    """
    # calendar_engine.py의 cal_save()가 이미 gk_schedules에 저장
    # hq_briefing.py의 get_daily_briefing()이 자동으로 조회
    # 추가 동기화 불필요 (이미 구현됨)
    return True


# ══════════════════════════════════════════════════════════════════════════════
# [5] 에이젠틱 추천 시스템
# ══════════════════════════════════════════════════════════════════════════════

def get_agentic_recurrence_suggestion(customer_name: str, current_stage: int) -> str:
    """
    고객의 현재 단계에 따라 에이젠틱한 반복 일정 추천
    
    Args:
        customer_name: 고객 이름
        current_stage: 현재 세일즈 단계 (1~12)
    
    Returns:
        str: 추천 메시지
    """
    suggestions = {
        1: f"💡 추천: {customer_name} 고객님과의 초기 접촉 후 3일 뒤 재연락 일정을 추가하세요.",
        2: f"💡 추천: 니즈 파악 후 매주 화요일 정기 상담 일정을 설정하세요.",
        3: f"💡 추천: 정보 수집 완료 후 분석 결과 공유를 위한 주간 미팅을 설정하세요.",
        4: f"💡 추천: 분석 진행 중 — 매주 금요일 진행 상황 체크 일정을 추가하세요.",
        5: f"💡 추천: 리포트 작성 후 고객 피드백 수집을 위한 주간 일정을 설정하세요.",
        6: f"💡 추천: 1차 제안 후 3일 뒤 고객 반응 확인 일정을 추가하세요.",
        7: f"💡 추천: 이의 처리 중 — 매주 수요일 FAQ 공유 및 재설명 일정을 설정하세요.",
        8: f"💡 추천: 2차 제안 준비 중 — 수정 설계안 완성 후 즉시 미팅 일정을 추가하세요.",
        9: f"💡 추천: 계약 준비 중 — 청약서 작성 지원을 위한 대면 미팅 일정을 설정하세요.",
        10: f"💡 추천: 계약 체결 완료! 🎉 사후 관리를 위한 월간 정기 점검 일정을 추가하세요.",
        11: f"💡 추천: 사후 관리 중 — 매월 1일 고객 만족도 체크 일정을 설정하세요.",
        12: f"💡 추천: 재계약 시즌! 매년 계약 갱신일 1개월 전 알림 일정을 추가하세요."
    }
    
    return suggestions.get(current_stage, f"💡 추천: {customer_name} 고객님과의 정기 상담 일정을 설정하세요.")


# ══════════════════════════════════════════════════════════════════════════════
# [6] 석세스 캘린더 통합 가이드
# ══════════════════════════════════════════════════════════════════════════════

def render_success_calendar_guide():
    """
    석세스 캘린더 사용 가이드 렌더링
    """
    st.markdown("""
<div style='background:linear-gradient(135deg,#EFF6FF 0%,#DBEAFE 100%);
  border:1.5px solid #93C5FD;border-radius:12px;padding:16px;margin:12px 0;'>
  <div style='font-size:1.05rem;font-weight:900;color:#1E3A8A;margin-bottom:10px;'>
    🚀 석세스 캘린더 (Outlook Style + Quick Links)
  </div>
  <div style='font-size:.85rem;color:#1E40AF;line-height:1.7;'>
    <b>✨ 핵심 기능:</b><br>
    • <b>연도/월 선택 모달</b>: 상단 "2026년 4월" 텍스트 클릭 → 연도/월 빠른 이동<br>
    • <b>고객 퀵링크 (@)</b>: 일정 입력 시 고객 이름 검색 → @홍길동 태그 자동 삽입<br>
    • <b>해시태그 (#)</b>: #암보험, #계약, #긴급 등 태그로 일정 필터링<br>
    • <b>반복 일정</b>: 매일/매주/매월/매년 반복 설정 + "체결 시까지 매주 화요일" 추천<br>
    • <b>심리적 컬러 코딩</b>: 12단계 세일즈 프로세스 기반 자동 색상 배정<br>
    • <b>HQ 브리핑 동기화</b>: 일정 저장 즉시 "오늘의 브리핑"에 반영
  </div>
</div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# [7] 사용 예시
# ══════════════════════════════════════════════════════════════════════════════

"""
## 사용 예시 (calendar_engine.py 통합)

```python
from success_calendar import (
    detect_stage_color,
    search_customers_by_name,
    render_customer_quick_link_selector,
    show_year_month_picker,
    get_agentic_recurrence_suggestion,
    render_success_calendar_guide
)

# 1. 석세스 캘린더 가이드 표시
render_success_calendar_guide()

# 2. 연도/월 선택 모달 (상단 "2026년 4월" 클릭 시)
if st.button("2026년 4월", key="year_month_btn"):
    show_year_month_picker(2026, 4)

# 3. 고객 퀵링크 선택
selected_customer = render_customer_quick_link_selector(agent_id="user123")
if selected_customer:
    st.success(f"@{selected_customer['name']} 선택됨!")

# 4. 심리적 컬러 코딩 (일정 저장 시)
color_info = detect_stage_color(
    title="홍길동 고객 계약 체결",
    memo="#계약 #서명 완료",
    category="consult"
)
# → {"color": "#DCFCE7", "border": "#22C55E", "stage_name": "계약 체결"}

# 5. 에이젠틱 추천
suggestion = get_agentic_recurrence_suggestion("홍길동", current_stage=10)
st.info(suggestion)
# → "💡 추천: 계약 체결 완료! 🎉 사후 관리를 위한 월간 정기 점검 일정을 추가하세요."
```

## calendar_engine.py 통합 포인트

### A. 연도/월 선택 모달 추가 (line ~704)
```python
# 기존: st.markdown(f"<div>...</div>", unsafe_allow_html=True)
# 수정: 클릭 가능한 버튼으로 변경
if st.button(f"{year}년 {month}월", key="cal_year_month_btn", use_container_width=True):
    from success_calendar import show_year_month_picker
    show_year_month_picker(year, month)
```

### B. 고객 퀵링크 UI 추가 (_render_event_form 함수 내)
```python
# 기존 고객 선택 selectbox 위에 추가
from success_calendar import render_customer_quick_link_selector

selected_quick = render_customer_quick_link_selector(agent_id, key_prefix="cal_form")
if selected_quick:
    # 자동으로 고객 필드 채우기
    st.session_state["_cal_quick_customer"] = selected_quick
```

### C. 심리적 컬러 코딩 (JS 캘린더 HTML 빌더 내)
```python
from success_calendar import detect_stage_color

# 각 이벤트에 컬러 정보 추가
for ev in _evs:
    color_info = detect_stage_color(
        title=ev.get("title", ""),
        memo=ev.get("memo", ""),
        category=ev.get("category", "")
    )
    ev["stage_color"] = color_info["color"]
    ev["stage_border"] = color_info["border"]
    ev["stage_name"] = color_info["stage_name"]
```

### D. 에이젠틱 추천 (되풀이 패널 내)
```python
from success_calendar import get_agentic_recurrence_suggestion

# 고객 선택 시 추천 메시지 표시
if _f_cust and _f_cust != "— 선택 안 함 —":
    # 고객의 현재 단계 조회 (gk_people.current_stage)
    current_stage = 4  # 예시
    suggestion = get_agentic_recurrence_suggestion(_f_cust, current_stage)
    st.info(suggestion)
```
"""
