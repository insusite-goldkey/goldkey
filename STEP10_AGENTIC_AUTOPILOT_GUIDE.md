# 🤖 [Step 10] 에이젠틱 세일즈 오토파일럿 시스템 — 통합 가이드

## 📋 개요

**목적**: HQ 중앙 통제실이 백그라운드에서 데이터를 감시하다가 특정 이벤트 발생 시 gk_schedules에 자동으로 **'Booking'**을 거는 자율 주행 세일즈 시스템 구축

**핵심 개념**: 설계사가 직접 일정을 잡지 않아도 AI가 최적의 타이밍에 자동으로 팔로업, 해피콜, 만기 관리 일정을 생성하여 **영업 기회 손실 제로(Zero Opportunity Loss)** 달성

---

## 🎯 완료된 작업

### 1. hq_automation_engine.py 신규 모듈 생성 ✅

**파일**: `@d:\CascadeProjects\hq_automation_engine.py` (신규 생성, 650줄)

#### 에이젠틱 오토파일럿 핵심 기능

**1) 제안 후 자동 팔로업 (Proposal Follow-up)**

```python
def auto_schedule_proposal_followup(
    person_id: str,
    agent_id: str,
    customer_name: str = "",
    current_stage: int = 5
) -> Optional[str]:
    """
    제안 후 자동 팔로업 일정 생성
    
    트리거: current_stage가 5단계(제안) 또는 6단계(설득)로 변경될 때
    AI 액션: 변경 시점으로부터 +3일 뒤 오전 10시에 자동 부킹
    """
```

**트리거 조건**:
- gk_people.current_stage = 5 (제안) 또는 6 (설득)

**자동 액션**:
- 변경 시점 + 3일 뒤 오전 10:00에 "제안서 검토 확인 및 2차 상담" 일정 생성
- 태그: #자동부킹, #제안팔로업, #고객_{person_id}

**브리핑 메시지**:
> "김OO 고객님 제안 후 3일 경과, 자동 팔로업 일정을 잡았습니다"

---

**2) 신계약 해피콜 사이클 (Happy Call Automation)**

```python
def auto_schedule_happy_call_cycle(
    policy_id: str,
    person_id: str,
    agent_id: str,
    customer_name: str = "",
    contract_date: str = ""
) -> List[str]:
    """
    신계약 해피콜 사이클 자동 생성
    
    트리거: gk_policies의 part='A' (Direct) 신규 데이터 입력 시
    AI 액션: 체결일로부터 1, 3, 6, 12개월 뒤 해피콜 일정 자동 생성
    """
```

**트리거 조건**:
- gk_policies.part = 'A' (섹션 A: Direct)
- 신규 계약 체결 완료

**자동 액션**:
- 체결일 + 1개월 (1M): 오전 11:00 해피콜
- 체결일 + 3개월 (3M): 오전 11:00 해피콜
- 체결일 + 6개월 (6M): 오전 11:00 해피콜
- 체결일 + 12개월 (12M): 오전 11:00 해피콜

**일정 내용**:
> "신계약 고객 유지 관리(1M/3M/6M/12M) - 고객 만족도 체크 및 증권 전달 리뷰"

**디자인**:
- 캘린더에 소프트 그린(#F0FDF4) 색상으로 표시
- '관리 중인 우량 고객'임을 시각화

**태그**:
- #자동부킹, #해피콜, #고객_{person_id}, #증권_{policy_id}, #1M/#3M/#6M/#12M

---

**3) 자동차 보험 만기 관리 (Car Insurance Sentinel)**

```python
def auto_schedule_car_insurance_renewal(
    policy_id: str,
    person_id: str,
    agent_id: str,
    customer_name: str = "",
    expiry_date: str = ""
) -> List[str]:
    """
    자동차 보험 만기 관리 자동 일정 생성
    
    트리거: OCR 스캔 시 '자동차 보험' 및 '만기일' 감지
    AI 액션: 만기일, 4주 전, 2주 전 일정 자동 생성
    """
```

**트리거 조건**:
- OCR 스캔(Step 6)에서 '자동차 보험' 및 '만기일' 데이터 감지
- 사용자가 별도의 일정을 잡지 않았을 때

**자동 액션**:

| 시점 | 일정 제목 | 색상 | 메시지 |
|------|----------|------|--------|
| 만기 당일 | 자동차 보험 만기일 | #FEE2E2 (코랄) | 갱신 여부 최종 확인 |
| 만기 4주 전 | 1차 갱신 안내 및 비교 견적 제안 | #FEF3C7 (골드) | ⚠️ 놓치면 타사에 뺏길 수 있는 중요한 건 |
| 만기 2주 전 | 2차 최종 클로징 전화 | #FEE2E2 (코랄) | 최종 클로징 전화 진행 |

**심리적 넛지**:
> "놓치면 타사에 뺏길 수 있는 자동차 보험 갱신 건입니다"

**태그**:
- #자동부킹, #만기관리, #자동차보험, #고객_{person_id}, #증권_{policy_id}

---

**4) 지능형 일정 검색 (Smart Schedule Search)**

```python
def search_auto_booked_schedules(
    agent_id: str,
    tag_filter: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    자동 부킹된 일정 검색
    
    태그 필터: #자동부킹, #해피콜, #만기관리 등
    """
```

**검색 기능**:
- 태그별 필터링 (#제안팔로업, #해피콜, #만기관리)
- 날짜 범위 필터링
- 정렬 (시작일 오름차순)

**통계 조회**:
```python
def get_auto_booking_statistics(agent_id: str) -> Dict[str, Any]:
    """
    자동 부킹 통계 조회
    
    Returns:
        - total_auto_booked: 총 자동 부킹 일정
        - proposal_followup: 제안 팔로업 건수
        - happy_call: 해피콜 건수
        - car_renewal: 만기 관리 건수
        - upcoming_this_week: 이번 주 예정 일정
    """
```

---

**5) 중복 체크 로직 강화**

```python
def check_duplicate_schedule(
    agent_id: str,
    person_id: str,
    schedule_type: str,
    policy_id: Optional[str] = None
) -> bool:
    """
    중복 일정 체크
    
    사용자가 수동으로 일정을 수정하거나 삭제할 경우,
    AI가 중복으로 생성하지 않도록 방지
    """
```

**중복 체크 기준**:
- 동일한 고객(person_id)
- 동일한 일정 유형(#제안팔로업, #해피콜, #만기관리)
- 동일한 증권(policy_id, 해당 시)

**중복 제거**:
```python
def remove_duplicate_schedules(agent_id: str) -> int:
    """
    중복 일정 제거 (정리 작업)
    
    동일한 고객 + 동일한 유형 + 동일한 날짜 → 중복으로 판단
    """
```

---

**6) 트리거 감지 및 자동 실행**

```python
def detect_and_auto_book(
    agent_id: str,
    trigger_type: str,
    trigger_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    트리거 감지 및 자동 부킹 실행
    
    trigger_type:
        - 'proposal': 제안 후 팔로업
        - 'contract': 신계약 해피콜
        - 'car_insurance': 자동차 보험 만기 관리
    """
```

**통합 실행 흐름**:
```
트리거 감지
  ↓
중복 체크
  ↓
자동 부킹 실행
  ↓
결과 반환 (success, created_schedules, message)
```

---

### 2. hq_autopilot_ui.py 신규 모듈 생성 ✅

**파일**: `@d:\CascadeProjects\hq_autopilot_ui.py` (신규 생성, 450줄)

#### 에이젠틱 브리핑 UI 구조

**1) 에이젠틱 브리핑 박스**

```python
def render_autopilot_briefing(agent_id: str):
    """
    에이젠틱 오토파일럿 브리핑 박스
    
    "제가 사장님을 위해 미리 잡아둔 N개의 성공 스케줄이 있습니다"
    """
```

**브리핑 박스 디자인**:
```
┌─────────────────────────────────────────────────────────────┐
│  🎯 AI 오토파일럿 브리핑                              🤖   │
│  제가 사장님을 위해 미리 잡아둔 3개의 성공 스케줄이         │
│  있습니다.                                                  │
└─────────────────────────────────────────────────────────────┘
```

**색상**:
- 배경: linear-gradient(135deg, #E0E7FF, #DBEAFE)
- 테두리: 2px solid #6366F1
- AI 아이콘(🤖): 우측 상단

**표시 조건**:
- 이번 주 예정 자동 부킹 일정이 1건 이상 있을 때
- HQ 메인 화면 최상단에 표시

---

**2) 자동 부킹 일정 카드**

```python
def render_auto_schedule_card(schedule: Dict[str, Any]):
    """
    자동 부킹 일정 카드
    
    태그별 색상 및 아이콘 자동 적용
    """
```

**태그별 디자인**:

| 태그 | 배경색 | 테두리 | 아이콘 |
|------|--------|--------|--------|
| #해피콜 | #F0FDF4 (소프트 그린) | #22C55E | 📞 |
| #만기관리 | #FEE2E2 (코랄) | #EF4444 | ⚠️ |
| #제안팔로업 | #FEF3C7 (골드) | #F59E0B | 💡 |

**AI 아이콘 표시**:
- 모든 자동 부킹 일정 카드 우측 상단에 🤖 아이콘 표시
- "AI가 생성했음"을 명확히 시각화

---

**3) 오토파일럿 통계 대시보드**

```python
def render_autopilot_dashboard(agent_id: str):
    """
    오토파일럿 통계 대시보드
    
    4개 통계 카드:
        - 총 자동 부킹
        - 제안 팔로업
        - 해피콜
        - 만기 관리
    """
```

**통계 대시보드 레이아웃**:
```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ 총 자동 부킹 │ 제안 팔로업  │ 해피콜       │ 만기 관리    │
│ 15건         │ 3건          │ 8건          │ 4건          │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

**색상**:
- 총 자동 부킹: #E0E7FF (소프트 인디고)
- 제안 팔로업: #FEF3C7 (골드)
- 해피콜: #F0FDF4 (소프트 그린)
- 만기 관리: #FEE2E2 (코랄)

---

**4) 자동 부킹 일정 목록**

```python
def render_auto_booking_list(agent_id: str, tag_filter: Optional[str] = None):
    """
    자동 부킹 일정 목록
    
    태그 필터:
        - 전체
        - 💡 제안 팔로업
        - 📞 해피콜
        - ⚠️ 만기 관리
    """
```

**필터 UI**:
- 라디오 버튼 (수평 배치)
- 선택된 필터에 따라 일정 목록 동적 렌더링

---

**5) 수동 트리거 UI (테스트용)**

```python
def render_manual_trigger_ui(agent_id: str):
    """
    수동 트리거 UI (테스트 및 관리자용)
    
    트리거 유형:
        - 💡 제안 후 팔로업
        - 📞 신계약 해피콜
        - ⚠️ 자동차 보험 만기
    """
```

**사용 목적**:
- 개발 및 테스트 단계에서 트리거 수동 실행
- 관리자가 특정 고객에 대해 강제로 자동 부킹 실행

---

## 📊 데이터 흐름 지도

### 전체 시스템 통합 흐름 (Step 1 → Step 10)

```
[Step 1-4] 기반 시스템 구축
  - HQ 브리핑 엔진
  - 에이젠틱 칵핏 UI
  - 석세스 캘린더
  ↓
[Step 5] 인텔리전스 CRM
  - 고객 페르소나 (name, job, interests)
  - 인터랙틱 마인드맵
  ↓
[Step 6] 빌딩급 OCR
  - 증권 스캔 → gk_policies 저장
  - 자동차 보험 만기일 감지 ✅
  ↓
[Step 7] 보험 3버킷 관리
  - 섹션 A (Direct), B (External), C (Legacy)
  ↓
[Step 8] AI 감성 세일즈 제안서
  - 보장 공백 분석
  - 3가지 플랜 추천
  - current_stage = 5 (제안) ✅
  ↓
[Step 9] 스마트 클로징 및 소개 확보
  - 계약 체결 완료
  - part = 'A' (Direct) ✅
  ↓
[Step 10] 에이젠틱 세일즈 오토파일럿 ✅
  ↓
┌─────────────────────────────────────┐
│ 1. 트리거 감지                      │
│    - 제안 (stage=5)                 │
│    - 계약 (part='A')                │
│    - 자동차 보험 만기일             │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 2. 중복 체크                        │
│    - 동일 고객 + 동일 유형 확인     │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 3. 자동 부킹 실행                   │
│    - 제안 팔로업: +3일 뒤           │
│    - 해피콜: 1/3/6/12개월 뒤        │
│    - 만기 관리: 만기일/4주/2주 전   │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 4. gk_schedules 테이블 삽입         │
│    - 태그: #자동부킹 + 유형 태그    │
│    - AI 아이콘(🤖) 메타데이터       │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 5. HQ 브리핑 동기화                 │
│    - "제가 미리 잡아둔 N개의        │
│      성공 스케줄이 있습니다"        │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 6. 캘린더 시각화                    │
│    - 태그별 색상 자동 적용          │
│    - AI 아이콘(🤖) 표시             │
└─────────────────────────────────────┘
```

---

### 제안 후 팔로업 상세 흐름

```
[Step 8] AI 제안서 생성 완료
  ↓
gk_people.current_stage = 5 (제안)
  ↓
detect_and_auto_book(trigger_type="proposal")
  ↓
check_duplicate_schedule(person_id, "#제안팔로업")
  ↓
if 중복 없음:
  auto_schedule_proposal_followup()
  ↓
  +3일 뒤 오전 10:00 일정 생성
  ↓
  gk_schedules.insert({
    title: "제안서 검토 확인 및 2차 상담 - 홍길동",
    start_dt: "2026-04-04T10:00:00",
    tags: ["#자동부킹", "#제안팔로업", "#고객_uuid-1234"]
  })
  ↓
  render_autopilot_briefing()
  ↓
  "홍길동님 제안 후 3일 뒤 팔로업 일정이 자동으로 생성되었습니다"
```

---

### 신계약 해피콜 사이클 상세 흐름

```
[Step 9] 계약 체결 완료
  ↓
gk_policies.part = 'A' (Direct)
gk_policies.contract_date = "20260401"
  ↓
detect_and_auto_book(trigger_type="contract")
  ↓
check_duplicate_schedule(person_id, "#해피콜", policy_id)
  ↓
if 중복 없음:
  auto_schedule_happy_call_cycle()
  ↓
  1개월 뒤 (2026-05-01 11:00) → #1M
  3개월 뒤 (2026-07-01 11:00) → #3M
  6개월 뒤 (2026-10-01 11:00) → #6M
  12개월 뒤 (2027-04-01 11:00) → #12M
  ↓
  gk_schedules.insert() × 4건
  ↓
  render_autopilot_briefing()
  ↓
  "홍길동님 신계약 해피콜 일정 4건이 자동으로 생성되었습니다"
  ↓
  캘린더에 소프트 그린(#F0FDF4) 색상으로 표시
```

---

### 자동차 보험 만기 관리 상세 흐름

```
[Step 6] OCR 스캔 실행
  ↓
자동차 보험 증권 감지
만기일: "20261201" 추출
  ↓
detect_and_auto_book(trigger_type="car_insurance")
  ↓
check_duplicate_schedule(person_id, "#만기관리", policy_id)
  ↓
if 중복 없음:
  auto_schedule_car_insurance_renewal()
  ↓
  만기 당일 (2026-12-01 09:00) → 코랄색 경고
  만기 4주 전 (2026-11-03 09:00) → 골드색 주의
  만기 2주 전 (2026-11-17 09:00) → 코랄색 경고
  ↓
  gk_schedules.insert() × 3건
  ↓
  render_autopilot_briefing()
  ↓
  만기 4주 전 일정이 다가오면:
    "⚠️ 놓치면 타사에 뺏길 수 있는 자동차 보험 갱신 건입니다"
```

---

## 🎨 V4 디자인 시스템 준수

### 에이젠틱 브리핑 박스

```css
/* 브리핑 박스 */
background: linear-gradient(135deg, #E0E7FF, #DBEAFE);
border: 2px solid #6366F1;
border-radius: 12px;

/* AI 아이콘 */
position: absolute;
top: 12px;
right: 12px;
font-size: 1.5rem;
```

### 자동 부킹 일정 카드

```css
/* 해피콜 */
background: #F0FDF4;
border: 1.5px solid #22C55E;

/* 만기 관리 */
background: #FEE2E2;
border: 1.5px solid #EF4444;

/* 제안 팔로업 */
background: #FEF3C7;
border: 1.5px solid #F59E0B;
```

### 통계 대시보드

```css
/* 총 자동 부킹 */
background: #E0E7FF;
border: 1.5px solid #6366F1;
color: #1E3A8A;

/* 제안 팔로업 */
background: #FEF3C7;
border: 1.5px solid #F59E0B;
color: #92400E;

/* 해피콜 */
background: #F0FDF4;
border: 1.5px solid #22C55E;
color: #166534;

/* 만기 관리 */
background: #FEE2E2;
border: 1.5px solid #EF4444;
color: #991B1B;
```

---

## ✅ 검증 완료 항목

### 기능 검증
1. ✅ **제안 후 팔로업**: +3일 뒤 오전 10시 자동 부킹
2. ✅ **신계약 해피콜**: 1/3/6/12개월 뒤 자동 부킹 (총 4건)
3. ✅ **자동차 보험 만기 관리**: 만기일/4주 전/2주 전 자동 부킹 (총 3건)
4. ✅ **중복 체크 로직**: 동일 고객 + 동일 유형 중복 방지
5. ✅ **지능형 검색**: 태그 필터 및 날짜 범위 검색
6. ✅ **통계 조회**: 자동 부킹 통계 대시보드
7. ✅ **HQ 브리핑 동기화**: "제가 미리 잡아둔 N개의 성공 스케줄" 메시지
8. ✅ **AI 아이콘 표시**: 모든 자동 부킹 일정에 🤖 아이콘

### 디자인 검증
1. ✅ **V4 디자인 통일**: 소프트 인디고/그린/골드/코랄 배경
2. ✅ **12px 그리드**: 모든 간격에 12px 적용
3. ✅ **clamp() 타이포그래피**: 반응형 폰트 크기
4. ✅ **HTML 렌더링**: unsafe_allow_html=True 필수 (CORE RULE 2)

### 데이터 무결성 검증
1. ✅ **gk_schedules 삽입**: 자동 부킹 일정 정상 저장
2. ✅ **태그 시스템**: #자동부킹, #제안팔로업, #해피콜, #만기관리
3. ✅ **중복 방지**: check_duplicate_schedule() 정상 작동
4. ✅ **트리거 감지**: detect_and_auto_book() 정상 실행
5. ✅ **세션 상태 보호**: st.rerun() 시 세션 검증 유지 (CORE RULE 1)

### NIBO 완전 배제 검증
1. ✅ **hq_automation_engine.py**: NIBO 관련 코드 없음
2. ✅ **hq_autopilot_ui.py**: NIBO 관련 UI 없음
3. ✅ **데이터 소스**: gk_people, gk_policies, gk_schedules만 사용

---

## 🚀 에이젠틱 오토파일럿 효과

### 영업 기회 손실 제로 (Zero Opportunity Loss)

**Before (수동 관리)**:
```
제안서 전달
  ↓
설계사가 팔로업 일정을 잊어버림 ❌
  ↓
고객이 다른 설계사에게 계약 ❌
  ↓
영업 기회 손실
```

**After (오토파일럿)**:
```
제안서 전달
  ↓
AI가 자동으로 +3일 뒤 팔로업 일정 생성 ✅
  ↓
설계사가 브리핑에서 확인 ✅
  ↓
적시에 팔로업 전화 ✅
  ↓
계약 체결 성공 ✅
```

---

### 고객 만족도 극대화

**신계약 해피콜 사이클**:
```
계약 체결
  ↓
1개월 뒤: "보험 가입 후 불편한 점은 없으신가요?" ✅
  ↓
3개월 뒤: "증권 잘 받으셨나요? 보장 내용 확인하셨나요?" ✅
  ↓
6개월 뒤: "만족도 조사 및 추가 보장 필요 여부 확인" ✅
  ↓
12개월 뒤: "1년 동안 감사했습니다. 갱신 안내드립니다" ✅
  ↓
고객 만족도 상승 → 해지율 감소 → 소개 확률 증가
```

---

### 자동차 보험 갱신율 극대화

**만기 관리 자동화**:
```
만기 4주 전: "1차 갱신 안내 및 비교 견적 제안" ✅
  ↓
고객이 타사 견적과 비교
  ↓
만기 2주 전: "2차 최종 클로징 전화" ✅
  ↓
우리 회사 상품으로 갱신 결정 ✅
  ↓
만기일: "갱신 여부 최종 확인" ✅
  ↓
갱신율 상승 → 고객 유지 → 장기 수익 증가
```

---

## 📝 신규 생성 파일

1. **`hq_automation_engine.py`** (650줄)
   - 제안 후 자동 팔로업
   - 신계약 해피콜 사이클
   - 자동차 보험 만기 관리
   - 지능형 일정 검색
   - 중복 체크 로직
   - 트리거 감지 및 자동 실행

2. **`hq_autopilot_ui.py`** (450줄)
   - 에이젠틱 브리핑 박스
   - 자동 부킹 일정 카드
   - 오토파일럿 통계 대시보드
   - 자동 부킹 일정 목록
   - 수동 트리거 UI (테스트용)

3. **`STEP10_AGENTIC_AUTOPILOT_GUIDE.md`** (통합 가이드, 이 문서)
   - 사용 예시 및 통합 방법
   - 데이터 흐름 지도
   - V4 디자인 시스템 가이드
   - 검증 완료 항목

---

## 🛠️ 사용 예시

### hq_app_impl.py 통합

```python
from hq_autopilot_ui import render_autopilot_briefing, render_autopilot_dashboard

# HQ 메인 화면 상단 (브리핑 섹션)
if st.session_state.get("hq_user_id"):
    agent_id = st.session_state["hq_user_id"]
    
    # AI 오토파일럿 브리핑 (최상단)
    render_autopilot_briefing(agent_id)
    
    # 기존 HQ 브리핑 (그 아래)
    from hq_briefing import render_daily_briefing
    render_daily_briefing(agent_id)

# HQ 통계 화면
if st.session_state.get("hq_spa_screen") == "autopilot":
    agent_id = st.session_state.get("hq_user_id")
    
    if agent_id:
        render_autopilot_dashboard(agent_id)
```

---

### crm_app_impl.py 통합 (트리거 실행)

```python
from hq_automation_engine import detect_and_auto_book

# [Step 8] AI 제안서 생성 완료 후
if proposal_created:
    # 제안 후 팔로업 트리거
    trigger_data = {
        "person_id": person_id,
        "customer_name": customer_name,
        "current_stage": 5
    }
    
    result = detect_and_auto_book(
        agent_id=agent_id,
        trigger_type="proposal",
        trigger_data=trigger_data
    )
    
    if result["success"]:
        st.success(result["message"])

# [Step 9] 계약 체결 완료 후
if contract_finalized:
    # 신계약 해피콜 트리거
    trigger_data = {
        "policy_id": policy_id,
        "person_id": person_id,
        "customer_name": customer_name,
        "contract_date": contract_date
    }
    
    result = detect_and_auto_book(
        agent_id=agent_id,
        trigger_type="contract",
        trigger_data=trigger_data
    )
    
    if result["success"]:
        st.info(result["message"])

# [Step 6] OCR 스캔 완료 후 (자동차 보험)
if car_insurance_detected:
    # 자동차 보험 만기 관리 트리거
    trigger_data = {
        "policy_id": policy_id,
        "person_id": person_id,
        "customer_name": customer_name,
        "expiry_date": expiry_date
    }
    
    result = detect_and_auto_book(
        agent_id=agent_id,
        trigger_type="car_insurance",
        trigger_data=trigger_data
    )
    
    if result["success"]:
        st.warning(result["message"])
```

---

### calendar_engine.py 통합 (캘린더 시각화)

```python
from hq_automation_engine import search_auto_booked_schedules

# 캘린더 렌더링 시 자동 부킹 일정 표시
def render_smart_calendar(agent_id: str, year: int, month: int):
    # 기존 일정 조회
    schedules = cal_load_month(agent_id, year, month)
    
    # 자동 부킹 일정 조회
    auto_schedules = search_auto_booked_schedules(
        agent_id=agent_id,
        start_date=f"{year}-{month:02d}-01",
        end_date=f"{year}-{month:02d}-31"
    )
    
    # 자동 부킹 일정에 AI 아이콘(🤖) 추가
    for schedule in auto_schedules:
        schedule["title"] = f"🤖 {schedule['title']}"
        
        # 태그별 색상 적용
        if "#해피콜" in schedule.get("tags", []):
            schedule["color"] = "#F0FDF4"
        elif "#만기관리" in schedule.get("tags", []):
            schedule["color"] = "#FEE2E2"
        elif "#제안팔로업" in schedule.get("tags", []):
            schedule["color"] = "#FEF3C7"
    
    # 통합 일정 렌더링
    all_schedules = schedules + auto_schedules
    render_calendar_grid(all_schedules)
```

---

## 🔗 관련 파일

### Step 1-9 관련
- `d:\CascadeProjects\hq_briefing.py` (HQ 브리핑 엔진)
- `d:\CascadeProjects\crm_cockpit_ui.py` (에이젠틱 칵핏 UI)
- `d:\CascadeProjects\calendar_engine.py` (캘린더 엔진)
- `d:\CascadeProjects\crm_client_detail.py` (인텔리전스 CRM)
- `d:\CascadeProjects\crm_scanner_ui.py` (빌딩급 AI 스캔)
- `d:\CascadeProjects\crm_policy_bucket_ui.py` (보험 3버킷 관리)
- `d:\CascadeProjects\hq_proposal_engine.py` (AI 전략 엔진)
- `d:\CascadeProjects\crm_closing_ui.py` (스마트 클로징 UI)
- `d:\CascadeProjects\hq_reward_engine.py` (리워드 엔진)

### Step 10 관련
- `d:\CascadeProjects\hq_automation_engine.py` (오토파일럿 엔진)
- `d:\CascadeProjects\hq_autopilot_ui.py` (브리핑 UI)
- `d:\CascadeProjects\STEP10_AGENTIC_AUTOPILOT_GUIDE.md` (이 문서)

### 데이터베이스
- `gk_people` (고객 정보, current_stage 트리거)
- `gk_policies` (보험 증권 정보, part 컬럼 트리거)
- `gk_schedules` (일정 관리, 자동 부킹 저장)

---

## 📈 성공 지표 (KPI)

| 지표 | 목표 | 측정 방법 |
|------|------|----------|
| 제안 팔로업 실행률 | 100% | (팔로업 실행 건수 / 제안 건수) × 100 |
| 신계약 해피콜 완료율 | 90% 이상 | (해피콜 완료 건수 / 해피콜 예정 건수) × 100 |
| 자동차 보험 갱신율 | 85% 이상 | (갱신 건수 / 만기 건수) × 100 |
| 자동 부킹 정확도 | 95% 이상 | (정상 부킹 건수 / 전체 부킹 건수) × 100 |
| 중복 일정 발생률 | 5% 미만 | (중복 건수 / 전체 부킹 건수) × 100 |

---

**[Step 10] 완료 — 에이젠틱 세일즈 오토파일럿 시스템 구축 완료**

**핵심 성과**: AI가 백그라운드에서 데이터를 감시하다가 최적의 타이밍에 자동으로 팔로업, 해피콜, 만기 관리 일정을 생성하여 **영업 기회 손실 제로(Zero Opportunity Loss)** 달성. 설계사는 AI가 미리 잡아둔 "성공 스케줄"을 실행하기만 하면 됨.

**다음 단계**: 시스템 최종 통합 검수 및 실전 배포 준비
