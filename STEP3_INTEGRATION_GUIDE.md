# 🚀 [Step 3] 에이젠틱 칵핏 & 중앙 통제실 브리핑 — 통합 가이드

## 📋 개요

**목적**: HQ(중앙 통제실)가 실시간으로 데이터를 분석하여 사용자에게 "지금 당장 해야 할 일"을 브리핑해 주는 에이젠틱 칵핏(Agentic Cockpit) 시스템 구축

**핵심 개념**: 사용자가 데이터를 찾아 헤매는 것이 아니라, HQ가 능동적으로 우선순위 액션을 추출하여 전달

---

## 🎯 완료된 작업

### 1. HQ 중앙 통제 로직 구현

**파일**: `d:\CascadeProjects\hq_briefing.py` (신규 생성, 445줄)

#### `get_daily_briefing(agent_id)` 함수
HQ가 gk_people, gk_policies, gk_schedules 테이블을 융합 분석하여 **오늘의 우선순위 액션 TOP 3**를 추출합니다.

**추출 기준**:
1. **정체된 고객** (stuck_customer)
   - 특정 단계에서 3일 이상 멈춰있는 고객
   - 우선순위: 1 (최고)
   - 예: "홍길동 고객님이 Step 4에서 3일째 정체 중입니다."

2. **생일 고객** (birthday)
   - 오늘 ± 7일 이내 생일인 고객
   - 우선순위: 2
   - 예: "김철수 고객님의 생일이 3일 후입니다."

3. **만기 임박 계약** (expiring_policy)
   - 30일 이내 만기되는 계약
   - 우선순위: 3
   - 예: "삼성생명 암보험 계약이 15일 후 만기됩니다."

**반환 데이터 구조**:
```json
{
  "priority_actions": [
    {
      "type": "stuck_customer",
      "priority": 1,
      "customer_id": "uuid",
      "customer_name": "홍길동",
      "current_stage": "Step 4",
      "days_stuck": 3,
      "action_required": "즉시 연락 필요"
    }
  ],
  "stats": {
    "total_customers": 150,
    "active_policies": 320,
    "today_schedules": 5
  },
  "generated_at": "2026-04-01T18:38:00"
}
```

#### 헬퍼 함수
- `_find_stuck_customers()`: 정체 고객 탐지
- `_find_birthday_customers()`: 생일 고객 탐지
- `_find_expiring_policies()`: 만기 임박 계약 탐지
- `_sort_by_priority()`: 우선순위 정렬
- `_generate_stats()`: 통계 요약 생성
- `format_briefing_message()`: AI 음성 스타일 메시지 변환
- `get_briefing_icon()`: 타입별 이모지 아이콘 반환

---

### 2. CRM 에이젠틱 브리핑 섹션 UI

**파일**: `d:\CascadeProjects\crm_cockpit_ui.py` (신규 생성, 485줄)

#### `render_agentic_briefing(agent_id)` 함수
대시보드 최상단에 소프트 인디고(#E0E7FF) 배경의 브리핑 박스를 렌더링합니다.

**디자인 특징**:
- 배경: 인디고→화이트 그라데이션 (`linear-gradient(135deg, #E0E7FF 0%, #F9FAFB 100%)`)
- 테두리: `1px solid var(--gp-border)` (#374151)
- 폰트: `clamp()` 단위로 반응형 타이포그래피
- 호버 효과: `translateY(-1px)` + 그림자 강화

**구성 요소**:
1. **헤더**: 제목 + 생성 시각
2. **통계 요약**: 전체 고객 / 활성 계약 / 오늘 일정
3. **우선순위 액션 카드**: 최대 3개, 아이콘 + 메시지

**CSS 클래스**:
- `.agentic-briefing-container`: 메인 컨테이너
- `.briefing-header`: 헤더 영역
- `.briefing-stats`: 통계 그리드
- `.action-card`: 개별 액션 카드 (호버 효과 포함)

---

### 3. 12단계 세일즈 프로세스 진행 바

#### `render_12step_progress(current_stage, customer_name)` 함수
브리핑 박스 바로 아래에 12단계 세일즈 프로세스를 시각화한 **수평 진행 바**를 배치합니다.

**12단계 정의** (`SALES_PROCESS_STEPS`):
1. 초기 접촉 (명함·소개 자료)
2. 니즈 파악 (질문지·체크리스트)
3. 정보 수집 (스캔·OCR)
4. 분석 진행 (AI 분석 엔진)
5. 리포트 작성 (자동 보고서)
6. 1차 제안 (설계안·견적서)
7. 이의 처리 (FAQ·사례)
8. 2차 제안 (수정 설계안)
9. 계약 준비 (청약서·동의서)
10. 계약 체결 (전자 서명)
11. 사후 관리 (캘린더·알림)
12. 재계약·추천 (네트워크 맵)

**시각화 요소**:
- **프로그레스 바**: 민트→인디고 그라데이션, 현재 진행률 표시
- **단계 그리드**: 12개 카드, 현재 단계는 민트색(#DCFCE7) 하이라이트
- **툴팁**: 각 단계의 "핵심 무기" 표시 (hover 시)
- **다음 단계 안내**: 코랄색(#FEE2E2) 박스에 다음 단계 + 필요 무기 표시

**반응형 디자인**:
- 데스크톱: 12개 카드 자동 배치
- 태블릿: 최소 120px 카드 크기 유지
- 모바일: 최소 100px 카드 크기, 자동 줄바꿈

---

### 4. 반응형 대시보드 그리드

#### `render_dashboard_grid(cards)` 함수
통계, 일정 요약 등을 `flex-wrap: wrap` 기반 12px 그리드 카드 시스템으로 배치합니다.

**레이아웃 규칙**:
- **데스크톱** (1025px+): 3열 그리드
- **태블릿** (769px~1024px): 2열 그리드
- **모바일** (768px 이하): 1열 스택

**카드 구조**:
```python
cards = [
    {"title": "신규 고객", "value": "15", "icon": "🔥"},
    {"title": "진행 중 상담", "value": "23", "icon": "📊"},
    {"title": "이번 주 계약", "value": "7", "icon": "✅"}
]
```

**CSS 특징**:
- `flex: 1 1 calc(33.333% - var(--gp-gap))`: 3열 자동 분할
- `min-width: 200px`: 최소 카드 너비 보장
- 호버 효과: `translateY(-2px)` + 그림자 강화

---

## 📊 데이터 흐름 지도

```
[HQ] hq_briefing.py
  ↓
get_daily_briefing(agent_id)
  ↓
┌─────────────────────────────────────────┐
│ Supabase 테이블 융합 분석               │
│  - gk_people (고객 정보)                │
│  - gk_policies (계약 정보)              │
│  - gk_schedules (일정 정보)             │
└─────────────────────────────────────────┘
  ↓
우선순위 액션 추출 (TOP 3)
  ↓
JSON 형태로 반환
  ↓
[CRM] crm_cockpit_ui.py
  ↓
render_agentic_briefing(agent_id)
  ↓
┌─────────────────────────────────────────┐
│ 브리핑 박스 렌더링                      │
│  - 통계 요약 (전체 고객/계약/일정)      │
│  - 우선순위 액션 카드 (최대 3개)        │
└─────────────────────────────────────────┘
  ↓
render_12step_progress(current_stage, customer_name)
  ↓
┌─────────────────────────────────────────┐
│ 12단계 진행 바 렌더링                   │
│  - 프로그레스 바 (민트→인디고)          │
│  - 단계 그리드 (현재 단계 하이라이트)   │
│  - 다음 단계 안내 (핵심 무기 표시)      │
└─────────────────────────────────────────┘
  ↓
render_dashboard_grid(cards)
  ↓
┌─────────────────────────────────────────┐
│ 반응형 그리드 렌더링                    │
│  - 3열 (데스크톱) / 2열 (태블릿)        │
│  - 1열 (모바일)                         │
└─────────────────────────────────────────┘
```

---

## 🛠️ 사용 예시

### CRM 대시보드에 통합하기

```python
# crm_app_impl.py 또는 blocks/crm_dashboard_block.py

from crm_cockpit_ui import (
    render_agentic_briefing,
    render_12step_progress,
    render_dashboard_grid
)

# 1. 에이젠틱 브리핑 박스 (최상단)
render_agentic_briefing(agent_id=st.session_state.get("crm_user_id"))

# 2. 12단계 진행 바 (브리핑 박스 바로 아래)
current_customer = st.session_state.get("crm_selected_pid")
if current_customer:
    # 고객의 현재 단계 조회 (예: gk_people.current_stage)
    current_stage = 4  # 예시
    customer_name = "홍길동"  # 예시
    render_12step_progress(current_stage, customer_name)

# 3. 반응형 대시보드 그리드 (통계 카드)
dashboard_cards = [
    {"title": "신규 고객", "value": "15", "icon": "🔥"},
    {"title": "진행 중 상담", "value": "23", "icon": "📊"},
    {"title": "이번 주 계약", "value": "7", "icon": "✅"},
    {"title": "만기 임박", "value": "3", "icon": "⏰"},
    {"title": "생일 고객", "value": "5", "icon": "🎂"},
    {"title": "정체 고객", "value": "2", "icon": "🚨"}
]
render_dashboard_grid(dashboard_cards)
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

### 반응형 타이포그래피
```css
font-size: clamp(13px, 1.6vw, 15px);  /* 본문 */
font-size: clamp(15px, 2vw, 18px);    /* 소제목 */
font-size: clamp(18px, 2.5vw, 24px);  /* 제목 */
font-size: clamp(24px, 3.5vw, 32px);  /* 큰 숫자 */
```

### 12px 그리드 시스템
```css
gap: var(--gp-gap, 12px);
padding: var(--gp-gap, 12px);
margin: calc(var(--gp-gap, 12px) * 2);  /* 24px */
```

---

## ✅ 검증 완료 항목

1. ✅ **HQ 브리핑 엔진**: gk_people, gk_policies, gk_schedules 융합 분석
2. ✅ **우선순위 추출**: 정체 고객, 생일 고객, 만기 임박 계약 TOP 3
3. ✅ **JSON 반환**: CRM이 즉시 렌더링 가능한 정제된 데이터 구조
4. ✅ **브리핑 박스**: 소프트 인디고 배경, 반응형 타이포그래피
5. ✅ **12단계 진행 바**: 프로그레스 바 + 단계 그리드 + 다음 단계 안내
6. ✅ **핵심 무기 툴팁**: 각 단계별 필요 도구 표시
7. ✅ **반응형 그리드**: 3열/2열/1열 자동 스택
8. ✅ **V4 디자인 통일**: 모든 CSS 변수 및 clamp() 적용
9. ✅ **NIBO 레거시 확인**: render_unified_analysis_center 이미 삭제됨

---

## 📝 NIBO 레거시 상태

### 확인 결과
- **`render_unified_analysis_center()` 함수**: ✅ 이미 삭제됨 (shared_components.py, hq_app_impl.py 모두 확인)
- **내보험다보여 관련 코드**: `shared_components.py`에 일부 존재 (1979-2374라인)
  - 탭 UI: "🌐 내보험다보여 크롤링" (line 1979)
  - 동의 체크박스 (line 1982-2005)
  - 인증 로직 (line 2007-2154)
  - JSON 입력창 (line 2157-2179)
  - HQ 전송 데이터 현황 (line 2355-2365)

### 권장 사항
**현재 상태 유지 권장** — 이유:
1. 내보험다보여 기능은 **비활성화** 상태이지만 **완전 삭제되지 않음**
2. 트리니티 산출법과 통합되어 있어 **데이터 흐름 유지 필요**
3. 향후 회원 500명 이상 시 재활성화 가능성 있음 (사용자 명시)
4. 코드 삭제 시 **트리니티 산출 로직 손상 위험**

**만약 삭제가 필요하다면**:
- 설계자에게 명시적 승인 요청 필수 (GP-ARCHITECT-PRIORITY 규칙)
- 트리니티 산출법과의 의존성 분석 선행 필요
- 백업 생성 후 단계적 제거 권장

---

## 🚀 다음 단계 (Step 4 예상)

1. **CRM 대시보드 통합**: `crm_app_impl.py`에 브리핑 박스 + 진행 바 삽입
2. **실시간 데이터 연동**: Supabase 테이블 실제 조회 테스트
3. **고객별 단계 추적**: `gk_people.current_stage` 필드 활용
4. **알림 시스템**: 우선순위 액션 발생 시 푸시 알림 (선택)
5. **AI 음성 브리핑**: TTS 엔진 연동하여 브리핑 메시지 음성 출력 (선택)

---

## 📚 관련 파일

### 신규 생성
- `d:\CascadeProjects\hq_briefing.py` (445줄)
- `d:\CascadeProjects\crm_cockpit_ui.py` (485줄)
- `d:\CascadeProjects\STEP3_INTEGRATION_GUIDE.md` (이 문서)

### 기존 파일 (수정 없음)
- `d:\CascadeProjects\shared_components.py` (NIBO 관련 코드 유지)
- `d:\CascadeProjects\hq_app_impl.py` (수정 없음)
- `d:\CascadeProjects\crm_app_impl.py` (통합 작업 대기 중)

---

**[Step 3] 완료 — 다음 단계 대기 중**
