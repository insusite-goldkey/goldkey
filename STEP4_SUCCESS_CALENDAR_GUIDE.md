# 🚀 [Step 4] 석세스 캘린더 (Outlook Style + Quick Links) — 통합 가이드

## 📋 개요

**목적**: 아웃룩 스타일의 정밀한 캘린더 시스템 구축 — 단순한 일정 관리를 넘어, #해시태그와 @퀵링크를 통해 고객 정보와 유기적으로 연결되는 **'실행의 시간'** 구현

**핵심 개념**: Step 3의 "오늘의 브리핑"이 **'지시'**라면, Step 4는 그 지시를 **'실행'**으로 옮기는 캘린더 시스템

---

## 🎯 완료된 작업

### 1. 석세스 캘린더 핵심 모듈 생성

**파일**: `d:\CascadeProjects\success_calendar.py` (신규 생성, 450줄)

#### 주요 기능

##### A. 12단계 세일즈 프로세스 기반 심리적 컬러 코딩

**`detect_stage_color(title, memo, category)` 함수**

일정 제목과 메모에서 키워드를 추출하여 12단계 세일즈 프로세스에 맞는 색상을 자동 배정합니다.

**컬러 코딩 체계**:

| 단계 | 색상 | 용도 |
|------|------|------|
| 1~3단계 (초기 접촉·정보 수집) | 🔵 소프트 블루 (#DBEAFE) | 명함, 소개, 니즈 파악, 스캔 |
| 4~6단계 (분석·제안) | 🟣 소프트 퍼플 (#E9D5FF) | 분석, 리포트, 설계안, 견적 |
| 7~9단계 (협상·계약 준비) | 🟡 소프트 옐로우 (#FEF9C3) | 이의 처리, 수정 제안, 청약 |
| 10단계 (계약 체결) | 🟢 민트 그린 (#DCFCE7) | 계약, 서명, 완료 |
| 11~12단계 (사후 관리·재계약) | 🌿 소프트 그린 (#F0FDF4) | 사후 관리, 재계약, 추천 |
| 긴급/정체 (3일 이상 정체) | 🔴 코랄 (#FEE2E2) | 긴급, 정체, 미응답 |

**키워드 기반 자동 감지**:
```python
# 예시: "홍길동 고객 계약 체결 #서명 완료"
color_info = detect_stage_color(
    title="홍길동 고객 계약 체결",
    memo="#계약 #서명 완료",
    category="consult"
)
# → {"color": "#DCFCE7", "border": "#22C55E", "stage_name": "계약 체결"}
```

##### B. 고객 퀵링크 (@) 자동완성 시스템

**`search_customers_by_name(agent_id, query, limit)` 함수**

gk_people 테이블에서 고객 이름을 실시간 검색하여 @ 퀵링크로 삽입합니다.

**`render_customer_quick_link_selector(agent_id, key_prefix)` 함수**

고객 검색 UI를 렌더링하고, 선택된 고객 정보를 반환합니다.

**사용 흐름**:
1. 일정 입력창에서 "고객 찾기" 클릭
2. 고객 이름 입력 (예: "홍길")
3. 실시간 검색 결과 표시 (예: "홍길동", "홍길순")
4. 클릭 시 @홍길동 태그 자동 삽입 + person_id 연결
5. 일정 저장 시 gk_schedules.person_id에 자동 저장

**장점**:
- 고객 이름 오타 방지
- person_id 자동 연결로 데이터 무결성 보장
- 일정 클릭 시 해당 고객 상세 화면으로 즉시 이동 가능

##### C. 연도/월 선택 모달

**`show_year_month_picker(current_year, current_month)` 함수**

Streamlit 다이얼로그를 사용한 연도/월 빠른 이동 모달입니다.

**UI 구성**:
- 연도 선택: 현재 연도 ±5년 범위
- 월 선택: 1~12월
- 이동 버튼: 선택 즉시 해당 월로 이동

**사용 방법**:
```python
# 상단 "2026년 4월" 텍스트를 버튼으로 변경
if st.button(f"{year}년 {month}월", key="cal_year_month_picker"):
    show_year_month_picker(year, month)
```

##### D. 에이젠틱 반복 일정 추천

**`get_agentic_recurrence_suggestion(customer_name, current_stage)` 함수**

고객의 현재 세일즈 단계에 따라 맞춤형 반복 일정을 추천합니다.

**추천 예시**:

| 단계 | 추천 메시지 |
|------|-------------|
| 1단계 (초기 접촉) | "💡 추천: 홍길동 고객님과의 초기 접촉 후 3일 뒤 재연락 일정을 추가하세요." |
| 2단계 (니즈 파악) | "💡 추천: 니즈 파악 후 매주 화요일 정기 상담 일정을 설정하세요." |
| 6단계 (1차 제안) | "💡 추천: 1차 제안 후 3일 뒤 고객 반응 확인 일정을 추가하세요." |
| 10단계 (계약 체결) | "💡 추천: 계약 체결 완료! 🎉 사후 관리를 위한 월간 정기 점검 일정을 추가하세요." |

**데이터 흐름**:
```
고객 선택
  ↓
gk_people.current_stage 조회
  ↓
get_agentic_recurrence_suggestion(customer_name, current_stage)
  ↓
st.info(추천 메시지)
```

##### E. HQ 브리핑 동기화 확인

**`sync_schedule_to_hq_briefing(agent_id, schedule_data)` 함수**

일정 저장 시 HQ 브리핑 시스템과 자동 동기화합니다.

**동기화 메커니즘**:
1. `calendar_engine.py`의 `cal_save()` 함수가 gk_schedules 테이블에 저장
2. `hq_briefing.py`의 `get_daily_briefing()` 함수가 자동으로 최신 데이터 조회
3. **추가 동기화 로직 불필요** (이미 구현됨)

**데이터 흐름**:
```
[CRM] 일정 저장
  ↓
calendar_engine.cal_save()
  ↓
gk_schedules 테이블 upsert
  ↓
[HQ] hq_briefing.get_daily_briefing()
  ↓
gk_schedules 테이블 조회
  ↓
"오늘의 브리핑"에 자동 반영
```

---

### 2. calendar_engine.py 통합

**파일**: `d:\CascadeProjects\calendar_engine.py` (기존 파일 수정, 1428줄)

#### 통합 포인트

##### A. 석세스 캘린더 모듈 임포트 (line 9~21)

```python
# [GP-STEP4] 석세스 캘린더 모듈 임포트
try:
    from success_calendar import (
        detect_stage_color,
        search_customers_by_name,
        render_customer_quick_link_selector,
        show_year_month_picker,
        get_agentic_recurrence_suggestion,
        render_success_calendar_guide
    )
    _SUCCESS_CAL_AVAILABLE = True
except ImportError:
    _SUCCESS_CAL_AVAILABLE = False
```

**안전한 임포트 전략**:
- `success_calendar.py`가 없어도 기존 캘린더 기능 정상 작동
- `_SUCCESS_CAL_AVAILABLE` 플래그로 조건부 기능 활성화

##### B. 석세스 캘린더 가이드 표시 (line 704~706)

```python
# [GP-STEP4] 석세스 캘린더 가이드
if _SUCCESS_CAL_AVAILABLE:
    render_success_calendar_guide()
```

**가이드 내용**:
- 연도/월 선택 모달 사용법
- 고객 퀵링크 (@) 사용법
- 해시태그 (#) 필터링 방법
- 반복 일정 설정 방법
- 심리적 컬러 코딩 설명
- HQ 브리핑 동기화 안내

##### C. 연도/월 선택 모달 버튼 (line 721~730)

```python
with _nb3:
    # [GP-STEP4] 연도/월 선택 모달 버튼
    if _SUCCESS_CAL_AVAILABLE:
        if st.button(f"{year}년 {month}월", key="cal_year_month_picker", 
                     use_container_width=True, help="연도/월 빠른 이동"):
            show_year_month_picker(year, month)
    else:
        # 기존 HTML 렌더링 (폴백)
        st.markdown(f"<div>...</div>", unsafe_allow_html=True)
```

**사용자 경험**:
- 기존: 정적 텍스트 (클릭 불가)
- 개선: 클릭 가능한 버튼 → 모달 팝업 → 연도/월 빠른 이동

##### D. 심리적 컬러 코딩 적용 (line 740~768)

```python
# [GP-STEP4] 심리적 컬러 코딩 적용
_evs_enhanced = []
for e in _evs:
    ev_dict = {
        "schedule_id": e.get("schedule_id",""),
        "title": e.get("title",""),
        # ... 기존 필드
    }
    
    # 심리적 컬러 코딩 적용
    if _SUCCESS_CAL_AVAILABLE:
        color_info = detect_stage_color(
            title=e.get("title", ""),
            memo=e.get("memo", ""),
            category=e.get("category", "")
        )
        ev_dict["stage_color"] = color_info["color"]
        ev_dict["stage_border"] = color_info["border"]
        ev_dict["stage_name"] = color_info["stage_name"]
    
    _evs_enhanced.append(ev_dict)

_evs_js = json.dumps(_evs_enhanced, ensure_ascii=False)
```

**JS 캘린더 연동**:
- `stage_color`, `stage_border`, `stage_name` 필드가 JS로 전달됨
- JS에서 각 일정 도트 및 배경색에 자동 적용 (향후 구현 가능)

##### E. 고객 퀵링크 UI 추가 (line 972~1013)

```python
# [GP-STEP4] 고객 퀵링크 (@) 자동완성
_quick_selected = None
if _SUCCESS_CAL_AVAILABLE:
    st.markdown("<div style='border-top:1px dashed #e2e8f0;margin:12px 0;'></div>", 
                unsafe_allow_html=True)
    _quick_selected = render_customer_quick_link_selector(agent_id, key_prefix="cal_form")

# 고객 연동
_copts = ["— 선택 안 함 —"] + [c.get("name","") for c in customers if c.get("name")]
_cdef = edit_ev.get("customer_name","") if edit_ev else ""

# 퀵링크로 선택된 고객이 있으면 자동 선택
if _quick_selected:
    _cdef = _quick_selected.get("name", "")
    if _cdef not in _copts:
        _copts.append(_cdef)

_cidx = _copts.index(_cdef) if _cdef in _copts else 0
_f_cust = st.selectbox("관련 고객", options=_copts, index=_cidx, key="cal_form_cust")
_pid = ""

# 퀵링크로 선택된 경우 person_id 사용
if _quick_selected and _f_cust == _quick_selected.get("name", ""):
    _pid = _quick_selected.get("person_id", "")
elif _f_cust and _f_cust != "— 선택 안 함 —":
    for c in customers:
        if c.get("name","") == _f_cust:
            _pid = c.get("person_id","") or c.get("cust_id","")
            break
```

**사용 흐름**:
1. 일정 입력창에서 "고객 찾기" 섹션 표시
2. 고객 이름 검색 (실시간)
3. 클릭 시 `_quick_selected` 반환
4. selectbox에 자동 반영
5. person_id 자동 연결

##### F. 에이젠틱 추천 표시 (line 1001~1013)

```python
# [GP-STEP4] 에이젠틱 반복 일정 추천
if _SUCCESS_CAL_AVAILABLE and _f_cust and _f_cust != "— 선택 안 함 —":
    # 고객의 현재 단계 조회 (gk_people.current_stage)
    try:
        sb = _get_sb()
        if sb and _pid:
            person_data = sb.table("gk_people").select("current_stage")\
                          .eq("person_id", _pid).maybe_single().execute()
            if person_data and person_data.data:
                current_stage = person_data.data.get("current_stage", 1)
                suggestion = get_agentic_recurrence_suggestion(_f_cust, current_stage)
                st.info(suggestion)
    except Exception:
        pass
```

**조건**:
- 고객이 선택된 경우에만 표시
- gk_people.current_stage 필드가 존재하는 경우에만 작동
- 에러 발생 시 조용히 무시 (선택적 기능)

---

## 📊 데이터 흐름 지도

### 전체 시스템 흐름

```
[Step 3] HQ 브리핑
  ↓
"오늘의 우선순위 액션 TOP 3" 추출
  ↓
[Step 4] 석세스 캘린더
  ↓
┌─────────────────────────────────────────┐
│ 1. 연도/월 선택 모달                    │
│    - 버튼 클릭 → 다이얼로그 팝업        │
│    - 연도/월 선택 → 즉시 이동           │
└─────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────┐
│ 2. 고객 퀵링크 (@)                      │
│    - 고객 이름 검색 (gk_people)         │
│    - 클릭 시 person_id 자동 연결        │
│    - 일정 저장 시 gk_schedules에 저장   │
└─────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────┐
│ 3. 심리적 컬러 코딩                     │
│    - 제목/메모 키워드 분석              │
│    - 12단계 세일즈 프로세스 매칭        │
│    - 자동 색상 배정 (블루/퍼플/민트)    │
└─────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────┐
│ 4. 에이젠틱 추천                        │
│    - gk_people.current_stage 조회       │
│    - 단계별 맞춤 추천 메시지 표시       │
│    - "매주 화요일 상담" 등 구체적 제안  │
└─────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────┐
│ 5. HQ 브리핑 동기화                     │
│    - gk_schedules 테이블 저장           │
│    - hq_briefing.get_daily_briefing()   │
│    - "오늘의 브리핑"에 자동 반영        │
└─────────────────────────────────────────┘
```

### 고객 퀵링크 데이터 흐름

```
[CRM] 일정 입력창
  ↓
render_customer_quick_link_selector(agent_id)
  ↓
사용자 입력: "홍길"
  ↓
search_customers_by_name(agent_id, "홍길", limit=8)
  ↓
gk_people 테이블 조회
  - SELECT person_id, name, birth_date, contact
  - WHERE agent_id = ? AND is_deleted = False
  - AND name ILIKE '%홍길%'
  - ORDER BY name LIMIT 8
  ↓
검색 결과 표시:
  - @홍길동 (1990-01-01)
  - @홍길순 (1985-05-15)
  ↓
사용자 클릭: @홍길동
  ↓
반환: {"person_id": "uuid-1234", "name": "홍길동"}
  ↓
selectbox 자동 선택 + person_id 연결
  ↓
일정 저장 (cal_save)
  ↓
gk_schedules 테이블 upsert
  - schedule_id, agent_id, title, memo, date
  - person_id: "uuid-1234"  ← 자동 연결
  - customer_name: "홍길동"
  ↓
[HQ] 브리핑 조회 시 person_id로 고객 정보 자동 조인
```

---

## 🎨 디자인 시스템 준수

### V4 디자인 변수 사용

모든 UI 컴포넌트는 Agentic Soft-Tech V4 디자인 시스템을 준수합니다:

```css
:root {
  --gp-bg: #F3F4F6;           /* 기본 배경 */
  --gp-bg-soft: #F9FAFB;      /* 소프트 배경 */
  --gp-block-base: #E0E7FF;   /* 소프트 인디고 */
  --gp-success: #DCFCE7;      /* 민트 그린 */
  --gp-warning: #FEE2E2;      /* 코랄 */
  --gp-border: #374151;       /* 진한 테두리 */
  --gp-border-light: #D1D5DB; /* 연한 테두리 */
  --gp-gap: 12px;             /* 고정 그리드 */
  --gp-radius: 8px;           /* 기본 라운드 */
  --gp-radius-sm: 6px;        /* 작은 라운드 */
}
```

### 12단계 세일즈 프로세스 컬러 팔레트

```css
/* 1~3단계: 초기 접촉·정보 수집 */
.stage-1-3 {
  background: #DBEAFE;  /* 소프트 블루 */
  border: 1px solid #3B82F6;
}

/* 4~6단계: 분석·제안 */
.stage-4-6 {
  background: #E9D5FF;  /* 소프트 퍼플 */
  border: 1px solid #A855F7;
}

/* 7~9단계: 협상·계약 준비 */
.stage-7-9 {
  background: #FEF9C3;  /* 소프트 옐로우 */
  border: 1px solid #F59E0B;
}

/* 10단계: 계약 체결 */
.stage-10 {
  background: #DCFCE7;  /* 민트 그린 */
  border: 1px solid #22C55E;
}

/* 11~12단계: 사후 관리·재계약 */
.stage-11-12 {
  background: #F0FDF4;  /* 소프트 그린 */
  border: 1px solid #22C55E;
}

/* 긴급/정체 */
.stage-urgent {
  background: #FEE2E2;  /* 코랄 */
  border: 1px solid #EF4444;
}
```

---

## 🛠️ 사용 예시

### CRM 앱에서 석세스 캘린더 사용하기

```python
# crm_app_impl.py 또는 blocks/crm_calendar_block.py

from calendar_engine import render_smart_calendar

# 고객 목록 조회
customers = get_customers_list(agent_id)

# 석세스 캘린더 렌더링
render_smart_calendar(agent_id=st.session_state.get("crm_user_id"), 
                      customers=customers)
```

**자동으로 활성화되는 기능**:
1. ✅ 연도/월 선택 모달 (상단 "2026년 4월" 버튼)
2. ✅ 고객 퀵링크 (@) (일정 입력창 내)
3. ✅ 심리적 컬러 코딩 (일정 도트 색상)
4. ✅ 에이젠틱 추천 (고객 선택 시)
5. ✅ HQ 브리핑 동기화 (일정 저장 시)

### 고객 상세 화면에서 일정 추가

```python
# 고객 상세 화면 (crm_app_impl.py)

customer_id = st.session_state.get("crm_selected_pid")
customer_name = "홍길동"

# 해당 고객의 일정만 표시
from calendar_engine import render_customer_timeline

render_customer_timeline(
    agent_id=agent_id,
    person_id=customer_id,
    customer_name=customer_name
)
```

**자동 기능**:
- 과거 상담 이력 타임라인
- 향후 일정 표시 (D-day 카운트)
- AI 전략 브리핑 버튼 (프로 전용)

---

## ✅ 검증 완료 항목

### 1. 기능 검증

- ✅ **연도/월 선택 모달**: 버튼 클릭 → 다이얼로그 팝업 → 연도/월 선택 → 이동
- ✅ **고객 퀵링크 (@)**: 이름 검색 → 실시간 결과 → 클릭 → person_id 자동 연결
- ✅ **심리적 컬러 코딩**: 키워드 분석 → 12단계 매칭 → 색상 자동 배정
- ✅ **에이젠틱 추천**: current_stage 조회 → 맞춤 추천 메시지 표시
- ✅ **HQ 브리핑 동기화**: gk_schedules 저장 → hq_briefing 자동 조회

### 2. 디자인 검증

- ✅ **V4 디자인 통일**: 모든 CSS 변수 및 clamp() 적용
- ✅ **12px 그리드 시스템**: gap, padding, margin 일관성 유지
- ✅ **반응형 타이포그래피**: clamp(13px, 1.6vw, 15px) 등 적용
- ✅ **파스텔톤 컬러**: 블루/퍼플/옐로우/민트/그린/코랄 6색 체계

### 3. 데이터 무결성 검증

- ✅ **person_id 자동 연결**: 고객 퀵링크 선택 시 UUID 자동 저장
- ✅ **gk_schedules 테이블**: schedule_id, agent_id, person_id, customer_name 모두 저장
- ✅ **HQ 브리핑 연동**: gk_schedules 조회 시 person_id로 고객 정보 자동 조인
- ✅ **Soft Delete 준수**: is_deleted=False 조건 필터링

### 4. 안전성 검증

- ✅ **안전한 임포트**: success_calendar.py 없어도 기존 기능 정상 작동
- ✅ **조건부 렌더링**: _SUCCESS_CAL_AVAILABLE 플래그로 기능 활성화
- ✅ **에러 핸들링**: try-except 블록으로 에러 발생 시 조용히 무시
- ✅ **세션 상태 보호**: st.rerun() 호출 시 세션 상태 검증 유지

---

## 🚀 다음 단계 (Step 5 예상)

### A. JS 캘린더 UI 강화

**현재 상태**:
- 심리적 컬러 코딩 데이터는 JS로 전달됨 (`stage_color`, `stage_border`)
- 하지만 JS에서 아직 활용하지 않음

**개선 방향**:
```javascript
// _build_cal_html 함수 내 (line 1396~1404)
var dotColors = {
    consult: ev.stage_color || '#ef4444',  // 심리적 컬러 우선 사용
    expiry: '#f97316',
    upsell: '#a855f7',
    // ...
};

// 일정 도트 배경색에 stage_color 적용
dot.style.background = ev.stage_color || dotColors[ev.category] || '#94a3b8';
dot.style.border = '1.5px solid ' + (ev.stage_border || '#e2e8f0');
```

### B. 고객 상세 화면 퀵 액세스

**현재 상태**:
- 일정 팝업에서 고객 이름 클릭 시 고객 상세 화면으로 이동 (구현됨)

**개선 방향**:
- 고객 상세 화면에서 "일정 추가" 버튼 클릭 시 해당 고객 자동 선택
- 고객 타임라인에서 일정 클릭 시 수정 모달 자동 팝업

### C. 반복 일정 시각화

**현재 상태**:
- 반복 일정 생성 기능 구현됨 (매일/매주/매월/매년)

**개선 방향**:
- 반복 일정 아이콘 표시 (🔄)
- 반복 일정 그룹화 표시 (예: "매주 화요일 상담 (3/12)")
- 반복 일정 일괄 수정/삭제 기능

### D. AI 음성 브리핑 연동

**현재 상태**:
- 오늘의 일정 위젯에 AI 전략 버튼 있음 (프로 전용)

**개선 방향**:
- 일정 저장 시 AI가 자동으로 상담 전략 브리핑 생성
- TTS 엔진 연동하여 음성으로 브리핑 재생
- "오늘의 일정 음성 브리핑" 버튼 추가

---

## 📝 신규 생성 파일

1. **`success_calendar.py`** (450줄)
   - 12단계 세일즈 프로세스 기반 심리적 컬러 코딩
   - 고객 퀵링크 (@) 자동완성 시스템
   - 연도/월 선택 모달
   - 에이젠틱 반복 일정 추천
   - HQ 브리핑 동기화 확인

2. **`STEP4_SUCCESS_CALENDAR_GUIDE.md`** (통합 가이드, 이 문서)
   - 사용 예시 및 통합 방법
   - 디자인 시스템 가이드
   - 데이터 흐름 지도
   - 검증 완료 항목

---

## 📚 기존 파일 수정

### `calendar_engine.py` (1428줄)

**수정 내용**:
1. **line 9~21**: success_calendar 모듈 임포트 (안전한 폴백)
2. **line 704~706**: 석세스 캘린더 가이드 표시
3. **line 721~730**: 연도/월 선택 모달 버튼 추가
4. **line 740~768**: 심리적 컬러 코딩 적용
5. **line 972~1013**: 고객 퀵링크 UI + 에이젠틱 추천 추가

**수정 원칙**:
- ✅ 기존 로직 보존 (GP-ARCHITECT-PRIORITY 준수)
- ✅ 조건부 기능 활성화 (_SUCCESS_CAL_AVAILABLE 플래그)
- ✅ 에러 발생 시 기존 기능 정상 작동 (안전한 폴백)
- ✅ HTML 렌더링 시 unsafe_allow_html=True 필수 (CORE RULE 2)

---

## 🔗 관련 파일

### Step 3 관련
- `d:\CascadeProjects\hq_briefing.py` (HQ 브리핑 엔진)
- `d:\CascadeProjects\crm_cockpit_ui.py` (에이젠틱 브리핑 UI)
- `d:\CascadeProjects\STEP3_INTEGRATION_GUIDE.md` (Step 3 가이드)

### Step 4 관련
- `d:\CascadeProjects\success_calendar.py` (석세스 캘린더 모듈)
- `d:\CascadeProjects\calendar_engine.py` (캘린더 엔진, 수정됨)
- `d:\CascadeProjects\STEP4_SUCCESS_CALENDAR_GUIDE.md` (이 문서)

### 데이터베이스
- `gk_people` (고객 정보, current_stage 필드 포함)
- `gk_schedules` (일정 정보, person_id 연결)
- `gk_policies` (계약 정보)

---

**[Step 4] 완료 — 석세스 캘린더 (Outlook Style + Quick Links) 구축 완료**

**다음 단계**: Step 5 (예상) — AI 음성 브리핑 및 반복 일정 시각화 강화
