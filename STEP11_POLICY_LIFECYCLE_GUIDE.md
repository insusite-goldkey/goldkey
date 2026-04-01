# 🏛️ [Step 11] 에이젠틱 계약 생애주기 및 스케줄 통제 시스템 — 통합 가이드

## 📋 개요

**목적**: 계약의 생애주기(생성→정상→해지/실효/갱신)를 AI가 자동으로 감시하고, 상태 변경 시 연관된 모든 스케줄을 지능적으로 관리하여 **설계사의 캘린더가 지저분해지는 것을 방지**

**핵심 개념**: 
- **상태 감시**: 계약 상태가 '정상'일 때만 만기 알림 스케줄 자동 생성
- **오토-클린**: 해지/실효/철회 시 미래 일정 자동 삭제
- **자동 갱신**: 자동차 보험 갱신 시 차년도 계약 자동 생성 및 스케줄 재배치

---

## 🎯 완료된 작업

### 1. gk_policies_status_extension.sql 생성 ✅

**파일**: `@d:\CascadeProjects\gk_policies_status_extension.sql` (신규 생성)

#### 데이터베이스 스키마 확장

**status 컬럼 추가 (계약 상태)**
```sql
ALTER TABLE gk_policies 
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT '정상' 
CHECK (status IN ('정상', '실효', '해지', '철회', '갱신'));
```

**상태 값 정의**:
| 상태 | 설명 | 색상 |
|------|------|------|
| 정상 | 활성 계약 | #DCFCE7 (민트) |
| 실효 | 보험료 미납으로 인한 실효 | #FEF3C7 (골드) |
| 해지 | 계약 종료 | #FEE2E2 (코랄) |
| 철회 | 청약 철회 | #E5E7EB (그레이) |
| 갱신 | 갱신 완료 | #DBEAFE (블루) |

---

**policy_category 컬럼 추가 (보험 유형)**
```sql
ALTER TABLE gk_policies 
ADD COLUMN IF NOT EXISTS policy_category TEXT DEFAULT '장기' 
CHECK (policy_category IN ('장기', '자동차', '연간소멸식', '특종'));
```

**보험 유형별 만기 알림 로직**:
| 유형 | 만기 알림 | 설명 |
|------|----------|------|
| 장기 | 1개월 전 | 종신보험, 건강보험 등 |
| 자동차 | 4주 전, 2주 전 (총 2건) | 자동차보험 |
| 연간소멸식 | 1개월 전 | 1년 만기 상품 |
| 특종 | 1개월 전 | 화재보험, 배상책임보험 등 |

---

**인덱스 추가 (검색 최적화)**
```sql
CREATE INDEX IF NOT EXISTS idx_gk_policies_status ON gk_policies(status);
CREATE INDEX IF NOT EXISTS idx_gk_policies_category ON gk_policies(policy_category);
CREATE INDEX IF NOT EXISTS idx_gk_policies_status_category ON gk_policies(status, policy_category);
CREATE INDEX IF NOT EXISTS idx_gk_policies_expiry_date ON gk_policies(expiry_date);
```

---

**계약 상태 변경 이력 테이블**
```sql
CREATE TABLE IF NOT EXISTS gk_policy_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    old_status TEXT,
    new_status TEXT NOT NULL,
    reason TEXT,
    changed_by TEXT,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**이력 추적 목적**:
- 해지/실효 사유 기록
- 갱신 이력 추적
- 감사 및 분석

---

### 2. hq_policy_manager.py 신규 모듈 생성 ✅

**파일**: `@d:\CascadeProjects\hq_policy_manager.py` (신규 생성, 650줄)

#### 지능형 계약 생애주기 관리자

**1) 만기 알림 스케줄 자동 생성**

```python
def auto_schedule_expiry_reminder(
    policy_id: str,
    person_id: str,
    agent_id: str,
    customer_name: str = "",
    expiry_date: str = "",
    policy_category: str = "장기",
    status: str = "정상"
) -> List[str]:
    """
    만기 알림 스케줄 자동 생성
    
    트리거: status = '정상'인 계약 생성 시
    """
```

**자동 액션**:

**장기/연간소멸식/특종**:
```
만기 1개월 전 (30일 전) 오전 10:00
  ↓
gk_schedules.insert({
    title: "{policy_category} 보험 만기 1개월 전 안내 - {customer_name}",
    category: "만기알림",
    tags: ["#자동부킹", "#만기알림", "#고객_{person_id}", "#증권_{policy_id}"]
})
```

**자동차 보험**:
```
만기 4주 전 (28일 전) 오전 10:00
  ↓
gk_schedules.insert({
    title: "자동차 보험 만기 4주 전 안내 - {customer_name}",
    memo: "갱신 안내 및 비교 견적 제안",
    color: "#FEF3C7"  // 골드색
})

만기 2주 전 (14일 전) 오전 10:00
  ↓
gk_schedules.insert({
    title: "자동차 보험 만기 2주 전 최종 안내 - {customer_name}",
    memo: "최종 갱신 확인",
    color: "#FEE2E2"  // 코랄색
})
```

---

**2) 오토-클린 (Auto-Clean): 미래 일정 자동 삭제**

```python
def auto_clean_future_schedules(
    policy_id: str,
    agent_id: str,
    new_status: str
) -> int:
    """
    계약 상태 변경 시 미래 일정 자동 삭제
    
    트리거: status가 '해지', '실효', '철회'로 변경될 때
    """
```

**자동 액션**:
```
상태 변경 (정상 → 해지/실효/철회)
  ↓
gk_schedules 조회:
  - agent_id 일치
  - tags에 "#자동부킹" 포함
  - tags에 "#증권_{policy_id}" 포함
  - start_dt >= 현재 시각 (미래 일정만)
  - is_deleted = False
  ↓
해당 일정 Hard Delete
  ↓
삭제된 일정 개수 반환
```

**효과**:
- 설계사의 캘린더가 지저분해지는 것을 방지
- 이미 해지된 계약에 대한 불필요한 알림 제거

---

**3) 자동차 보험 자동 갱신**

```python
def auto_renew_policy(
    policy_id: str,
    agent_id: str,
    renewal_date: str = ""
) -> Optional[str]:
    """
    자동차 보험 자동 갱신
    
    트리거: 만기 전 갱신 입력 시
    """
```

**자동 액션**:
```
갱신 요청
  ↓
기존 증권 정보 조회
  ↓
차년도 만기일 계산 (갱신일 + 365일)
  ↓
gk_policies.insert({
    contract_date: renewal_date,
    expiry_date: new_expiry_date,
    status: "정상",
    policy_category: "자동차"
})
  ↓
기존 증권 상태 변경 (status: "갱신")
  ↓
기존 증권 미래 일정 삭제 (auto_clean_future_schedules)
  ↓
새 증권에 대한 만기 알림 스케줄 생성 (auto_schedule_expiry_reminder)
  ↓
새 증권 ID 반환
```

---

**4) 계약 상태 변경 통합 함수**

```python
def update_policy_status(
    policy_id: str,
    agent_id: str,
    new_status: str,
    reason: str = "",
    changed_by: str = ""
) -> Dict[str, Any]:
    """
    계약 상태 변경 통합 함수
    """
```

**처리 흐름**:
```
1. 기존 상태 조회
2. 상태 변경 (gk_policies.update)
3. 이력 저장 (gk_policy_status_history.insert)
4. 해지/실효/철회 시 미래 일정 자동 삭제
5. 결과 반환 (success, old_status, new_status, deleted_schedules, message)
```

---

**5) 계약 생애주기 통계**

```python
def get_policy_lifecycle_statistics(agent_id: str) -> Dict[str, Any]:
    """
    계약 생애주기 통계 조회
    """
```

**통계 항목**:
- total_policies: 총 계약 건수
- active_policies: 정상 계약
- expired_policies: 실효 계약
- cancelled_policies: 해지 계약
- renewed_policies: 갱신 계약
- car_insurance_count: 자동차 보험
- long_term_count: 장기 보험

---

### 3. crm_date_picker.py 신규 모듈 생성 ✅

**파일**: `@d:\CascadeProjects\crm_date_picker.py` (신규 생성, 450줄)

#### 반응형 듀얼 캘린더 피커

**1) 듀얼 캘린더 피커 (Dual Calendar Picker)**

```python
def render_dual_date_picker(
    key_prefix: str = "date_picker",
    default_start: Optional[datetime.date] = None,
    default_end: Optional[datetime.date] = None,
    label_start: str = "시작일",
    label_end: str = "종료일"
) -> Tuple[Optional[datetime.date], Optional[datetime.date]]:
    """
    듀얼 캘린더 피커 (시작일/종료일 각각 선택)
    """
```

**UI 구조**:
```
┌─────────────────────────────────────────────────────────────┐
│  📅 보험 기간 선택                                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┬──────────────────────┐            │
│  │ 시작일               │ 종료일               │            │
│  │ [2026-04-01]         │ [2027-04-01]         │            │
│  └──────────────────────┴──────────────────────┘            │
│                                                             │
│  📊 보험 기간: 365일 (약 12개월)                            │
└─────────────────────────────────────────────────────────────┘
```

**V4 디자인 시스템**:
```css
.dual-date-picker-container {
    background: #F3F4F6;
    border: 1.5px solid #9CA3AF;
    border-radius: 10px;
    padding: 16px;
}

.dual-date-picker-row {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
}

.dual-date-picker-col {
    flex: 1 1 calc(50% - 6px);
    min-width: 200px;
}

@media (max-width: 768px) {
    .dual-date-picker-col {
        flex: 1 1 100%;
    }
}
```

---

**2) 보험 기간 입력 폼**

```python
def render_insurance_period_form(
    key_prefix: str = "insurance_period",
    policy_category: str = "장기"
) -> Dict[str, Any]:
    """
    보험 기간 입력 폼
    
    보험 유형별 기본 기간 자동 설정
    """
```

**보험 유형별 기본 기간**:
| 유형 | 기본 기간 |
|------|----------|
| 장기 | 10년 (3650일) |
| 자동차 | 1년 (365일) |
| 연간소멸식 | 1년 (365일) |
| 특종 | 1년 (365일) |

---

**3) 날짜 범위 선택기 (프리셋 포함)**

```python
def render_date_range_selector(
    key_prefix: str = "date_range",
    preset_ranges: bool = True
) -> Tuple[Optional[datetime.date], Optional[datetime.date]]:
    """
    날짜 범위 선택기 (프리셋 옵션 포함)
    """
```

**프리셋 범위**:
- 오늘
- 이번 주
- 이번 달
- 올해

---

### 4. crm_policy_status_ui.py 신규 모듈 생성 ✅

**파일**: `@d:\CascadeProjects\crm_policy_status_ui.py` (신규 생성, 550줄)

#### 에이젠틱 상태 제어 버튼 UI

**1) 상태 제어 버튼 그룹**

```python
def render_policy_status_controls(
    policy_id: str,
    agent_id: str,
    current_status: str = "정상",
    policy_category: str = "장기"
) -> Optional[str]:
    """
    계약 상태 제어 버튼 그룹
    """
```

**버튼 구성**:
```
┌─────────────────────────────────────────────────────────────┐
│  ⚙️ 계약 상태 관리                                          │
├─────────────────────────────────────────────────────────────┤
│  현재 상태: 정상                                            │
├─────────────────────────────────────────────────────────────┤
│  [🔄 승환해지] [⚠️ 실효해지] [❌ 일반해지]                  │
│                                                             │
│  [🔄 갱신] (자동차 보험만)                                  │
└─────────────────────────────────────────────────────────────┘
```

---

**2) 상태 변경 확인 다이얼로그**

```python
@st.dialog("계약 상태 변경 확인", width="medium")
def show_status_change_confirmation(
    policy_id: str,
    agent_id: str,
    new_status: str,
    customer_name: str = ""
):
    """
    상태 변경 확인 다이얼로그
    """
```

**다이얼로그 구조**:
```
┌─────────────────────────────────────────────────────────────┐
│  계약 상태 변경 확인                                        │
├─────────────────────────────────────────────────────────────┤
│  홍길동님의 계약을 해지 상태로 변경하시겠습니까?            │
│                                                             │
│  ⚠️ 해지 처리 시 해당 계약과 연결된 모든 미래 일정이       │
│     자동으로 삭제됩니다.                                    │
│                                                             │
│  변경 사유 (선택):                                          │
│  [고객 요청, 타사 전환, 보험료 부담 등]                     │
│                                                             │
│  [취소]                    [확인]                           │
└─────────────────────────────────────────────────────────────┘
```

---

**3) 갱신 확인 다이얼로그**

```python
@st.dialog("자동차 보험 갱신", width="medium")
def show_renewal_confirmation(
    policy_id: str,
    agent_id: str,
    customer_name: str = ""
):
    """
    갱신 확인 다이얼로그
    """
```

**다이얼로그 구조**:
```
┌─────────────────────────────────────────────────────────────┐
│  자동차 보험 갱신                                           │
├─────────────────────────────────────────────────────────────┤
│  홍길동님의 자동차 보험을 갱신하시겠습니까?                 │
│                                                             │
│  💡 갱신 처리 시 차년도 계약이 자동으로 생성되고,           │
│     새로운 만기 알림 일정이 자동으로 배치됩니다.            │
│                                                             │
│  갱신일:                                                    │
│  [2026-12-01]                                               │
│                                                             │
│  [취소]                    [갱신]                           │
└─────────────────────────────────────────────────────────────┘
```

---

**4) 계약 생애주기 통계 대시보드**

```python
def render_policy_lifecycle_dashboard(agent_id: str):
    """
    계약 생애주기 통계 대시보드
    """
```

**대시보드 레이아웃**:
```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ 정상 계약    │ 실효         │ 해지         │ 갱신         │
│ 15건         │ 2건          │ 5건          │ 3건          │
└──────────────┴──────────────┴──────────────┴──────────────┘

┌──────────────────────────┬──────────────────────────┐
│ 자동차 보험              │ 장기 보험                │
│ 8건                      │ 12건                     │
└──────────────────────────┴──────────────────────────┘
```

---

## 📊 데이터 흐름 지도

### 전체 시스템 통합 흐름 (Step 1 → Step 11)

```
[Step 1-10] 기반 시스템 구축
  - HQ 브리핑 엔진
  - 에이젠틱 칵핏 UI
  - 석세스 캘린더
  - 인텔리전스 CRM
  - 빌딩급 OCR
  - 보험 3버킷 관리
  - AI 감성 세일즈 제안서
  - 스마트 클로징 및 소개 확보
  - 에이젠틱 세일즈 오토파일럿
  ↓
[Step 11] 에이젠틱 계약 생애주기 및 스케줄 통제 ✅
  ↓
┌─────────────────────────────────────┐
│ 1. 계약 생성 (status='정상')        │
│    - gk_policies.insert()           │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 2. 만기 알림 스케줄 자동 생성       │
│    - auto_schedule_expiry_reminder()│
│    - 장기: 1개월 전                 │
│    - 자동차: 4주 전, 2주 전         │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 3. 계약 상태 변경 (해지/실효)       │
│    - update_policy_status()         │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 4. 미래 일정 자동 삭제              │
│    - auto_clean_future_schedules()  │
│    - Hard Delete                    │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 5. 자동차 보험 갱신                 │
│    - auto_renew_policy()            │
│    - 차년도 계약 자동 생성          │
│    - 새 만기 알림 스케줄 생성       │
└─────────────────────────────────────┘
```

---

### 계약 생성 → 만기 알림 자동 부킹

```
[Step 7] 보험 3버킷에 신규 계약 입력
  ↓
crm_date_picker.render_insurance_period_form()
  ↓
사용자가 시작일/종료일 선택
  ↓
gk_policies.insert({
    contract_date: "20260401",
    expiry_date: "20270401",
    status: "정상",
    policy_category: "장기"
})
  ↓
auto_schedule_expiry_reminder()
  ↓
만기 1개월 전 (2027-03-01 10:00) 일정 생성
  ↓
gk_schedules.insert({
    title: "장기 보험 만기 1개월 전 안내 - 홍길동",
    category: "만기알림",
    tags: ["#자동부킹", "#만기알림", "#고객_uuid-1234", "#증권_policy-5678"]
})
```

---

### 계약 해지 → 미래 일정 자동 삭제

```
[Step 7] 보험 3버킷 카드에서 [일반해지] 버튼 클릭
  ↓
crm_policy_status_ui.render_policy_status_controls()
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
gk_schedules 조회:
  - tags에 "#증권_policy-5678" 포함
  - start_dt >= 현재 시각 (미래 일정만)
  ↓
해당 일정 Hard Delete (3건)
  ↓
"상태가 '해지'로 변경되었습니다. 관련된 미래 일정 3건이 함께 삭제되었습니다." 메시지 표시
  ↓
st.rerun()
```

---

### 자동차 보험 갱신 → 차년도 계약 자동 생성

```
[Step 7] 보험 3버킷 카드에서 [갱신] 버튼 클릭
  ↓
show_renewal_confirmation() 다이얼로그 표시
  ↓
사용자가 갱신일 선택 (2026-12-01)
  ↓
auto_renew_policy()
  ↓
기존 증권 정보 조회
  ↓
차년도 만기일 계산 (2026-12-01 + 365일 = 2027-12-01)
  ↓
gk_policies.insert({
    contract_date: "20261201",
    expiry_date: "20271201",
    status: "정상",
    policy_category: "자동차"
})
  ↓
기존 증권 상태 변경 (status: "갱신")
  ↓
기존 증권 미래 일정 삭제 (auto_clean_future_schedules)
  ↓
새 증권에 대한 만기 알림 스케줄 생성:
  - 2027-11-03 10:00 (4주 전)
  - 2027-11-17 10:00 (2주 전)
  ↓
"차년도 계약이 자동으로 생성되었습니다. (새 증권 ID: policy-9999)" 메시지 표시
  ↓
st.rerun()
```

---

## 🎨 V4 디자인 시스템 준수

### 듀얼 캘린더 피커

```css
/* 컨테이너 */
background: #F3F4F6;
border: 1.5px solid #9CA3AF;
border-radius: 10px;
padding: 16px;

/* 기간 정보 박스 */
background: #DBEAFE;
border: 1.5px solid #3B82F6;
color: #1E3A8A;

/* 12px 그리드 */
gap: 12px;
```

### 상태 제어 버튼

```css
/* 현재 상태 표시 */
정상: background: #DCFCE7;
실효: background: #FEF3C7;
해지: background: #FEE2E2;
철회: background: #E5E7EB;
갱신: background: #DBEAFE;
```

### 생애주기 통계 대시보드

```css
/* 정상 계약 */
background: #DCFCE7;
border: 1.5px solid #22C55E;
color: #166534;

/* 실효 */
background: #FEF3C7;
border: 1.5px solid #F59E0B;
color: #92400E;

/* 해지 */
background: #FEE2E2;
border: 1.5px solid #EF4444;
color: #991B1B;

/* 갱신 */
background: #DBEAFE;
border: 1.5px solid #3B82F6;
color: #1E3A8A;
```

---

## ✅ 검증 완료 항목

### 기능 검증
1. ✅ **만기 알림 자동 생성**: 장기 1개월 전, 자동차 4주/2주 전
2. ✅ **오토-클린**: 해지/실효/철회 시 미래 일정 자동 삭제
3. ✅ **자동 갱신**: 차년도 계약 자동 생성 및 스케줄 재배치
4. ✅ **상태 변경 이력**: gk_policy_status_history 테이블 기록
5. ✅ **듀얼 캘린더 피커**: 시작일/종료일 각각 선택
6. ✅ **상태 제어 버튼**: 승환해지/실효해지/일반해지/갱신
7. ✅ **생애주기 통계**: 정상/실효/해지/갱신 건수 조회

### 디자인 검증
1. ✅ **V4 디자인 통일**: 소프트 인디고/그린/골드/코랄 배경
2. ✅ **12px 그리드**: 모든 간격 적용
3. ✅ **반응형 레이아웃**: flex-wrap 적용
4. ✅ **HTML 렌더링**: unsafe_allow_html=True (CORE RULE 2)

### 데이터 무결성 검증
1. ✅ **gk_policies 확장**: status, policy_category 컬럼 추가
2. ✅ **인덱스 최적화**: status, category, expiry_date 인덱스
3. ✅ **이력 추적**: gk_policy_status_history 테이블
4. ✅ **중복 방지**: 동일 증권에 대한 중복 스케줄 생성 방지
5. ✅ **세션 상태 보호**: st.rerun() 시 세션 검증 유지 (CORE RULE 1)

### NIBO 완전 배제 검증
1. ✅ **모든 신규 모듈**: NIBO 관련 코드 없음
2. ✅ **데이터 소스**: gk_policies, gk_schedules, gk_policy_status_history만 사용

---

## 📝 신규 생성 파일

1. **`gk_policies_status_extension.sql`** - 스키마 확장
2. **`hq_policy_manager.py`** (650줄) - 생애주기 관리자
3. **`crm_date_picker.py`** (450줄) - 듀얼 캘린더 피커
4. **`crm_policy_status_ui.py`** (550줄) - 상태 제어 UI
5. **`STEP11_POLICY_LIFECYCLE_GUIDE.md`** - 통합 가이드 (이 문서)

---

## 🛠️ 사용 예시

### Step 7 보험 3버킷 통합

```python
from crm_date_picker import render_insurance_period_form
from crm_policy_status_ui import render_policy_lifecycle_controls
from hq_policy_manager import auto_schedule_expiry_reminder

# 신규 계약 입력 시
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

# 기존 계약 카드에 상태 제어 버튼 추가
for policy in policies:
    render_policy_lifecycle_controls(
        policy_id=policy["policy_id"],
        agent_id=agent_id,
        customer_name=policy["customer_name"],
        current_status=policy["status"],
        policy_category=policy["policy_category"]
    )
```

---

## 🔗 관련 파일

### Step 1-10 관련
- `d:\CascadeProjects\hq_briefing.py` (HQ 브리핑 엔진)
- `d:\CascadeProjects\calendar_engine.py` (캘린더 엔진)
- `d:\CascadeProjects\crm_policy_bucket_ui.py` (보험 3버킷 관리)
- `d:\CascadeProjects\hq_automation_engine.py` (오토파일럿 엔진)

### Step 11 관련
- `d:\CascadeProjects\gk_policies_status_extension.sql` (스키마 확장)
- `d:\CascadeProjects\hq_policy_manager.py` (생애주기 관리자)
- `d:\CascadeProjects\crm_date_picker.py` (듀얼 캘린더 피커)
- `d:\CascadeProjects\crm_policy_status_ui.py` (상태 제어 UI)
- `d:\CascadeProjects\STEP11_POLICY_LIFECYCLE_GUIDE.md` (이 문서)

### 데이터베이스
- `gk_policies` (보험 증권 정보, status, policy_category 컬럼)
- `gk_policy_status_history` (계약 상태 변경 이력)
- `gk_schedules` (일정 관리, 만기 알림 자동 부킹)

---

## 📈 성공 지표 (KPI)

| 지표 | 목표 | 측정 방법 |
|------|------|----------|
| 만기 알림 자동 생성률 | 100% | (자동 생성 건수 / 신규 계약 건수) × 100 |
| 해지 시 일정 정리율 | 100% | (자동 삭제 건수 / 해지 건수) × 100 |
| 자동차 보험 갱신율 | 90% 이상 | (갱신 건수 / 만기 건수) × 100 |
| 캘린더 정확도 | 95% 이상 | (유효 일정 건수 / 전체 일정 건수) × 100 |

---

**[Step 11] 완료 — 에이젠틱 계약 생애주기 및 스케줄 통제 시스템 구축 완료**

**핵심 성과**: AI가 계약의 생애주기를 자동으로 감시하고, 상태 변경 시 연관된 모든 스케줄을 지능적으로 관리하여 **설계사의 캘린더가 항상 깔끔하고 정확하게 유지**됨. 해지된 계약에 대한 불필요한 알림이 자동으로 제거되고, 자동차 보험 갱신 시 차년도 계약이 자동으로 생성되어 **완벽한 계약 생애주기 관리** 달성.

**다음 단계**: 시스템 최종 통합 검수 및 실전 배포 준비
