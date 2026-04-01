# 🏆 [Step 9] 스마트 클로징 및 리워드 기반 소개 확보 시스템 (The Success Loop) — 통합 가이드

## 📋 개요

**목적**: 제안된 상품을 **'체결'**하고, 만족한 고객으로부터 **'소개'**를 받아 다음 세일즈로 연결되는 선순환 구조 완성

**핵심 개념**: 복잡한 계약 행정을 AI가 보조하고, 고객에게 **리워드(보상)**를 제안하여 자연스럽게 인맥 네트워크를 확장하는 **The Success Loop** 구축

---

## 🎯 완료된 작업

### 1. crm_closing_ui.py 신규 모듈 생성 ✅

**파일**: `@d:\CascadeProjects\crm_closing_ui.py` (신규 생성, 350줄)

#### 스마트 클로징 핵심 기능

**1) 전자 서명 시뮬레이션**

```python
def render_signature_pad():
    """
    전자 서명 패드 UI (시뮬레이션)
    
    실제 구현 시 streamlit-drawable-canvas 또는 JavaScript 기반 서명 패드 사용
    """
```

**서명 패드 UI**:
- 2px dashed #6366F1 테두리
- 흰색 배경 (#FFFFFF)
- 중앙 정렬 텍스트 안내
- 서명 확인 체크박스

**2) 민트색 폭죽 애니메이션 (성취감 극대화)**

```python
def render_celebration_animation():
    """
    계약 체결 완료 시 민트색 폭죽 애니메이션
    """
```

**애니메이션 효과**:
- 민트색 계열 (#DCFCE7, #A7F3D0, #6EE7B7, #34D399)
- CSS @keyframes confetti-fall (3초 애니메이션)
- 중앙 축하 메시지 (celebration-bounce 효과)
- 9개의 폭죽 파티클 (화면 전체 분산)

**3) 버킷 자동 업데이트**

```python
def finalize_contract(policy_id: str, person_id: str, agent_id: str, signature_data: str = "") -> bool:
    """
    계약 체결 완료 처리
    
    1. gk_policies 업데이트 (part='A', status='ACTIVE')
    2. gk_people 업데이트 (current_stage=10: 체결 완료)
    3. 전자 서명 데이터 저장 (선택 사항)
    """
```

**데이터 업데이트**:
| 테이블 | 업데이트 필드 | 값 |
|--------|--------------|-----|
| gk_policies | part | 'A' (섹션 A: Direct로 이동) |
| gk_policies | contract_date | 오늘 날짜 (YYYYMMDD) |
| gk_people | current_stage | 10 (체결 완료) |
| gk_people | last_contact | 현재 시각 (ISO 8601) |

**4) 최종 확인 체크리스트**

```python
def render_final_checklist():
    """
    계약 체결 전 최종 확인 체크리스트
    """
```

**체크리스트 항목**:
- ✅ 보험 상품 내용 및 보장 범위 확인
- ✅ 월 보험료 및 납입 기간 확인
- ✅ 계약자 및 피보험자 정보 확인
- ✅ 약관 및 중요 사항 설명 청취
- ✅ 청약 철회권 안내 확인

---

### 2. hq_reward_engine.py 신규 모듈 생성 ✅

**파일**: `@d:\CascadeProjects\hq_reward_engine.py` (신규 생성, 450줄)

#### 리워드 및 소개 엔진 핵심 기능

**1) 리워드 시스템**

```python
def create_reward(
    person_id: str,
    agent_id: str,
    reward_type: str,
    reward_amount: int,
    reason: str = ""
) -> bool:
    """
    리워드 생성
    
    Args:
        reward_type: 'point', 'gift', 'discount'
        reward_amount: 리워드 금액/포인트
        reason: 리워드 사유
    """
```

**리워드 유형**:
| 유형 | 설명 | 예시 |
|------|------|------|
| point | 포인트 적립 | 10,000 포인트 |
| gift | 기프티콘 | 스타벅스 아메리카노 |
| discount | 할인 혜택 | 다음 계약 10% 할인 |

**2) AI 기반 소개 요청 타이밍 분석**

```python
def analyze_referral_timing(person_id: str, agent_id: str) -> Dict[str, Any]:
    """
    AI 기반 소개 요청 최적 타이밍 분석
    
    Returns:
        - ready: 소개 요청 가능 여부
        - reason: 판단 이유
        - score: 타이밍 점수 (0-100)
        - optimal: 최적 타이밍 여부
    """
```

**타이밍 판단 규칙**:

| 조건 | 점수 | 상태 | 설명 |
|------|------|------|------|
| 계약 체결 전 (stage < 10) | 0 | ❌ 불가 | 체결 완료 후 요청 |
| 체결 후 1~3일 | 100 | ✅ 최적 | 만족도 최고 시기 |
| 체결 후 4~7일 | 70 | ✅ 양호 | 소개 요청 가능 |
| 체결 후 8일 이상 | 30 | ⚠️ 주의 | 사후 관리 먼저 |

**3) 소개 요청 멘트 생성 (3가지 톤)**

```python
def generate_referral_scripts(customer_name: str, job: str = "") -> Dict[str, Dict[str, str]]:
    """
    소개 요청 멘트 생성 (3가지 톤)
    
    Returns:
        - gratitude: 감사 기반 톤
        - value: 가치 제안 톤
        - direct: 직접 요청 톤
    """
```

**3가지 톤 비교**:

| 톤 | 특징 | 적합 고객 | 예시 |
|---|------|----------|------|
| 🙏 감사 기반 | "함께해 주셔서 감사합니다" | 주부, 교사, 일반 직장인 | "덕분에 소중한 미래를 준비할 수 있게 되었습니다" |
| 💎 가치 제안 | "합리적이고 좋은 선택" | 전문직, 공무원 | "같은 혜택과 전문적인 상담을 제공해 드리겠습니다" |
| 🎯 직접 요청 | "한 가지 부탁드려도 될까요?" | 사업가, 대표 | "최선을 다해 상담해 드리겠습니다" |

**직업별 커스터마이징**:
```python
if "의사" in job or "간호" in job:
    gratitude["request"] += "특히 의사님 동료분들께 도움이 될 것 같습니다."
elif "교사" in job or "교수" in job:
    value["request"] += "교사님 동료분들께도 좋은 정보가 될 것입니다."
elif "사업" in job or "대표" in job:
    direct["request"] += "대표님 네트워크에 계신 분들께도 도움이 될 것입니다."
```

**4) 네트워크 확장 자동화**

```python
def auto_connect_referral_network(
    referrer_id: str,
    referee_name: str,
    referee_contact: str,
    agent_id: str
) -> Optional[str]:
    """
    소개받은 신규 고객 자동 등록 및 네트워크 연결
    
    1. gk_people에 신규 고객 생성 (current_stage=1)
    2. gk_relationships에 '소개자' 관계 추가
    3. gk_rewards에 리워드 부여 (10,000 포인트)
    """
```

**자동화 프로세스**:
```
신규 고객 정보 입력
  ↓
gk_people 테이블에 신규 레코드 생성
  - name: 피소개자 이름
  - contact: 피소개자 연락처
  - current_stage: 1 (초기 접촉)
  ↓
gk_relationships 테이블에 관계 추가
  - from_person_id: 소개자 UUID
  - to_person_id: 피소개자 UUID
  - relation_type: '소개자'
  ↓
gk_rewards 테이블에 리워드 부여
  - person_id: 소개자 UUID
  - reward_type: 'point'
  - reward_amount: 10000
  - reason: '신규 고객 소개'
  ↓
Step 5 마인드맵에 '소개자' 라인 자동 표시
```

**5) 에이전틱 단계 업데이트**

```python
def update_customer_stage_to_referral(person_id: str, agent_id: str, target_stage: int = 12) -> bool:
    """
    고객 세일즈 단계 업데이트 (소개 완료)
    
    Args:
        target_stage: 11 (사후관리), 12 (소개 완료)
    """
```

**12단계 세일즈 프로세스**:
```
1단계: 초기 접촉
2단계: 정보 수집
3단계: 관계 구축
4단계: 분석
5단계: 제안
6단계: 설득
7단계: 협상
8단계: 재제안
9단계: 최종 확인
10단계: 체결 완료 ✅
11단계: 사후 관리
12단계: 소개 완료 ✅ (The Success Loop 완성)
```

---

### 3. gk_rewards_schema.sql 생성 ✅

**파일**: `@d:\CascadeProjects\gk_rewards_schema.sql` (신규 생성)

#### 테이블 스키마

```sql
CREATE TABLE IF NOT EXISTS gk_rewards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reward_id TEXT NOT NULL UNIQUE DEFAULT gen_random_uuid()::TEXT,
    person_id TEXT NOT NULL REFERENCES gk_people(person_id),
    agent_id TEXT NOT NULL,
    reward_type TEXT NOT NULL CHECK (reward_type IN ('point', 'gift', 'discount')),
    reward_amount INTEGER NOT NULL DEFAULT 0,
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'redeemed', 'expired')),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    redeemed_at TIMESTAMPTZ
);
```

**필드 설명**:
| 필드 | 타입 | 설명 |
|------|------|------|
| reward_type | TEXT | 리워드 유형 (point/gift/discount) |
| reward_amount | INTEGER | 리워드 금액/포인트 |
| reason | TEXT | 리워드 사유 |
| status | TEXT | 상태 (pending/approved/redeemed/expired) |
| redeemed_at | TIMESTAMPTZ | 사용 일시 |

---

### 4. crm_referral_ui.py 신규 모듈 생성 ✅

**파일**: `@d:\CascadeProjects\crm_referral_ui.py` (신규 생성, 350줄)

#### 소개 요청 UI 구조

```
┌─────────────────────────────────────────────────────────────┐
│  🎁 소개 요청 — 고객명                                      │
├─────────────────────────────────────────────────────────────┤
│  ✅ 계약 체결 직후 만족도가 높은 시기입니다.                │
│  지금이 소개 요청 최적 타이밍입니다!                        │
│                                                             │
│  소개 요청 타이밍 점수: 100/100                             │
│  [██████████████████████████████████████████████] 100%      │
├─────────────────────────────────────────────────────────────┤
│  💬 AI 소개 요청 멘트 (3가지 톤)                            │
│  ○ 🙏 감사 기반 톤  ● 💎 가치 제안 톤  ○ 🎯 직접 요청 톤  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 🎤 오프닝                                            │   │
│  │ "고객님께서 이번에 선택하신 보험 상품이..."          │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ 🎁 소개 요청                                         │   │
│  │ "주변 분들도 고객님처럼 현명한 선택을..."            │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ 🎉 인센티브 안내                                     │   │
│  │ "소개해 주신 분과 소개받으신 분 모두에게..."         │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  👤 소개받은 신규 고객 등록                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 이름: [홍길동]          연락처: [010-1234-5678]      │   │
│  │ 소개 메모 (선택):                                    │   │
│  │ [홍길동님이 소개해 주신 분입니다.]                   │   │
│  │                                                      │   │
│  │ [✅ 신규 고객 등록 및 소개자 연결]                   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**리워드 대시보드**:
```
┌─────────────────────────────────────────────────────────────┐
│  🏆 나의 리워드 현황                                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┬──────────────┬──────────────┐            │
│  │ 총 포인트    │ 받은 기프티콘│ 소개 성공    │            │
│  │ 50,000 P     │ 5개          │ 3건          │            │
│  └──────────────┴──────────────┴──────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

---

### 5. session_optimizer.py 신규 모듈 생성 ✅

**파일**: `@d:\CascadeProjects\session_optimizer.py` (신규 생성, 350줄)

#### 세션 최적화 핵심 기능

**1) 12단계 완료 고객 세션 정리**

```python
def cleanup_completed_customer_session(person_id: str) -> int:
    """
    12단계 완료 고객의 임시 세션 데이터 정리
    
    정리 대상:
    - proposal_{person_id}
    - closing_completed_{person_id}
    - referral_completed_{person_id}
    - signature_confirmed
    - checklist_*
    """
```

**2) 전역 임시 세션 정리**

```python
def cleanup_all_temporary_sessions() -> Dict[str, int]:
    """
    모든 임시 세션 데이터 정리 (전역 최적화)
    
    정리 패턴:
    - _temp_*
    - _cache_*
    - _loading_*
    - _pending_*
    """
```

**3) 세션 건강도 모니터링**

```python
def monitor_session_health() -> Dict[str, Any]:
    """
    세션 상태 건강도 모니터링
    
    Returns:
        - health_score: 건강도 점수 (0-100)
        - status: excellent/good/fair/poor
        - needs_cleanup: 정리 필요 여부
    """
```

**건강도 판정 기준**:
| 점수 | 상태 | 색상 | 조치 |
|------|------|------|------|
| 80-100 | 우수 | #22C55E | 정상 |
| 60-79 | 양호 | #3B82F6 | 정상 |
| 40-59 | 보통 | #F59E0B | 정리 권장 |
| 0-39 | 나쁨 | #EF4444 | 즉시 정리 필요 |

**4) 자동 세션 정리 (백그라운드)**

```python
def auto_cleanup_sessions(agent_id: str) -> Dict[str, Any]:
    """
    자동 세션 정리 (백그라운드 작업)
    
    1. 12단계 완료 고객 목록 조회
    2. 각 고객별 임시 세션 정리
    3. 전역 임시 세션 정리
    """
```

---

## 📊 데이터 흐름 지도

### 전체 시스템 통합 흐름 (Step 1 → Step 9)

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
  ↓
[Step 7] 보험 3버킷 관리
  - 섹션 A (Direct), B (External), C (Legacy)
  ↓
[Step 8] AI 감성 세일즈 제안서
  - 보장 공백 분석
  - 3가지 플랜 추천
  - 감성 스크립트 생성
  ↓
[Step 9] 스마트 클로징 및 소개 확보 ✅
  ↓
┌─────────────────────────────────────┐
│ 1. 스마트 클로징                    │
│    - 전자 서명 시뮬레이션           │
│    - 최종 확인 체크리스트           │
│    - 계약 체결 완료                 │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 2. 버킷 자동 업데이트               │
│    - gk_policies.part = 'A'         │
│    - gk_people.current_stage = 10   │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 3. 민트색 폭죽 애니메이션 🎉       │
│    - 성취감 극대화                  │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 4. 소개 요청 타이밍 분석            │
│    - AI 기반 최적 타이밍 판단       │
│    - 타이밍 점수 (0-100)            │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 5. 소개 요청 멘트 생성              │
│    - 3가지 톤 (감사/가치/직접)      │
│    - 직업별 커스터마이징            │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 6. 신규 고객 자동 등록              │
│    - gk_people 생성                 │
│    - gk_relationships 연결          │
│    - gk_rewards 부여                │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 7. 에이전틱 단계 업데이트           │
│    - current_stage = 12 (소개 완료) │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 8. 세션 최적화                      │
│    - 임시 데이터 정리               │
│    - 메모리 최적화                  │
└─────────────────────────────────────┘
  ↓
[The Success Loop 완성] 🔄
  - 신규 고객 → Step 1부터 재시작
  - 소개자 → 리워드 적립
  - 설계사 → 네트워크 확장
```

### 스마트 클로징 상세 흐름

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

### 소개 요청 상세 흐름

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
  성공 메시지 표시:
    - "✅ {referee_name}님이 신규 고객으로 등록되었습니다!"
    - "💡 {referrer_name}님께 10,000 포인트가 적립되었습니다."
    - "🔗 Step 5 마인드맵에 소개자 라인이 자동으로 연결되었습니다."
  ↓
st.rerun()
```

---

## 🎨 V4 디자인 시스템 준수

### 스마트 클로징 색상

```css
/* 전자 서명 패드 */
background: #FFFFFF;
border: 2px dashed #6366F1;

/* 민트색 폭죽 애니메이션 */
confetti-colors: #DCFCE7, #A7F3D0, #6EE7B7, #34D399;

/* 축하 메시지 */
background: linear-gradient(135deg, #DCFCE7, #A7F3D0);
border: 3px solid #22C55E;

/* 최종 확인 체크리스트 */
background: #F3F4F6;
border: 1.5px solid #9CA3AF;
```

### 소개 요청 색상

```css
/* 타이밍 점수 바 */
background: linear-gradient(90deg, #22C55E, #10B981);

/* 감사 기반 톤 */
background: #E0E7FF;
border: 1.5px solid #6366F1;

/* 가치 제안 톤 */
background: #DBEAFE;
border: 1.5px solid #3B82F6;

/* 직접 요청 톤 */
background: #DCFCE7;
border: 1.5px solid #22C55E;
```

### 리워드 대시보드 색상

```css
/* 총 포인트 */
background: #E0E7FF;
border: 1.5px solid #6366F1;
color: #1E3A8A;

/* 받은 기프티콘 */
background: #DCFCE7;
border: 1.5px solid #22C55E;
color: #166534;

/* 소개 성공 */
background: #FEF3C7;
border: 1.5px solid #F59E0B;
color: #92400E;
```

---

## ✅ 검증 완료 항목

### 기능 검증
1. ✅ **스마트 클로징**: 전자 서명 시뮬레이션 + 체결 완료 처리
2. ✅ **버킷 자동 업데이트**: 섹션 A로 이동 + 상태 ACTIVE
3. ✅ **민트색 폭죽 애니메이션**: CSS @keyframes 활용
4. ✅ **소개 요청 타이밍 분석**: AI 기반 최적 타이밍 판단
5. ✅ **3가지 톤 멘트 생성**: 감사/가치/직접 + 직업별 커스터마이징
6. ✅ **네트워크 자동 확장**: gk_relationships 연결 + 마인드맵 표시
7. ✅ **리워드 시스템**: gk_rewards 테이블 + 포인트 적립
8. ✅ **세션 최적화**: 12단계 완료 시 임시 데이터 정리

### 디자인 검증
1. ✅ **V4 디자인 통일**: 소프트 인디고/민트/골드 배경
2. ✅ **12px 그리드**: 모든 간격에 12px 적용
3. ✅ **clamp() 타이포그래피**: 반응형 폰트 크기
4. ✅ **HTML 렌더링**: unsafe_allow_html=True 필수 (CORE RULE 2)

### 데이터 무결성 검증
1. ✅ **gk_policies 업데이트**: part='A', contract_date 자동 설정
2. ✅ **gk_people 업데이트**: current_stage=10/12 자동 업데이트
3. ✅ **gk_relationships 연결**: '소개자' 관계 자동 추가
4. ✅ **gk_rewards 부여**: 소개 성공 시 10,000 포인트 적립
5. ✅ **세션 상태 보호**: st.rerun() 시 세션 검증 유지 (CORE RULE 1)

### NIBO 완전 배제 검증
1. ✅ **crm_closing_ui.py**: NIBO 관련 코드 없음
2. ✅ **hq_reward_engine.py**: NIBO 관련 코드 없음
3. ✅ **crm_referral_ui.py**: NIBO 관련 UI 없음
4. ✅ **session_optimizer.py**: NIBO 관련 세션 키 없음
5. ✅ **데이터 소스**: 오직 gk_people, gk_policies, gk_relationships, gk_rewards만 사용

---

## 🚀 The Success Loop (선순환 구조)

### 완성된 선순환 흐름

```
┌─────────────────────────────────────────────────────────────┐
│                    The Success Loop                         │
│                                                             │
│  1. 초기 접촉 (Step 1-4)                                    │
│     ↓                                                       │
│  2. 고객 분석 (Step 5-6)                                    │
│     ↓                                                       │
│  3. 제안서 생성 (Step 8)                                    │
│     ↓                                                       │
│  4. 계약 체결 (Step 9 클로징) ✅                            │
│     ↓                                                       │
│  5. 소개 요청 (Step 9 리워드) ✅                            │
│     ↓                                                       │
│  6. 신규 고객 등록 → 1번으로 돌아가기 🔄                   │
│                                                             │
│  [설계사 혜택]                                              │
│  - 네트워크 자동 확장                                       │
│  - 리워드 포인트 적립                                       │
│  - 마인드맵 자동 업데이트                                   │
│                                                             │
│  [고객 혜택]                                                │
│  - 소개 보상 (포인트/기프티콘)                              │
│  - 지인에게 좋은 정보 제공                                  │
│  - 신뢰 관계 강화                                           │
└─────────────────────────────────────────────────────────────┘
```

### 성공 지표 (KPI)

| 지표 | 목표 | 측정 방법 |
|------|------|----------|
| 계약 체결률 | 70% 이상 | (체결 건수 / 제안 건수) × 100 |
| 소개 성공률 | 30% 이상 | (소개 건수 / 체결 건수) × 100 |
| 평균 소개 타이밍 | 3일 이내 | 체결일 - 소개 요청일 |
| 리워드 사용률 | 80% 이상 | (사용 건수 / 부여 건수) × 100 |
| 세션 건강도 | 80점 이상 | monitor_session_health() |

---

## 📝 신규 생성 파일

1. **`crm_closing_ui.py`** (350줄)
   - 전자 서명 시뮬레이션
   - 민트색 폭죽 애니메이션
   - 버킷 자동 업데이트
   - 최종 확인 체크리스트

2. **`hq_reward_engine.py`** (450줄)
   - 리워드 시스템
   - 소개 요청 타이밍 분석
   - 3가지 톤 멘트 생성
   - 네트워크 자동 확장

3. **`gk_rewards_schema.sql`** (SQL 스크립트)
   - gk_rewards 테이블 생성
   - 인덱스 및 트리거 설정

4. **`crm_referral_ui.py`** (350줄)
   - 소개 요청 UI
   - 신규 고객 등록 폼
   - 리워드 대시보드

5. **`session_optimizer.py`** (350줄)
   - 세션 정리 로직
   - 건강도 모니터링
   - 자동 최적화

6. **`STEP9_SMART_CLOSING_SUCCESS_LOOP_GUIDE.md`** (통합 가이드, 이 문서)
   - 사용 예시 및 통합 방법
   - 데이터 흐름 지도
   - V4 디자인 시스템 가이드
   - 검증 완료 항목

---

## 🛠️ 사용 예시

### crm_app_impl.py 통합

```python
from crm_closing_ui import render_smart_closing
from crm_referral_ui import render_referral_request, render_reward_dashboard

# 스마트 클로징 화면
if st.session_state.get("crm_spa_screen") == "closing":
    person_id = st.session_state.get("crm_selected_pid")
    agent_id = st.session_state.get("crm_user_id")
    customer_name = st.session_state.get("crm_customer_name", "")
    proposal_data = st.session_state.get(f"proposal_{person_id}")
    
    if person_id and agent_id:
        render_smart_closing(person_id, agent_id, customer_name, proposal_data)

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

### 세션 최적화 통합

```python
from session_optimizer import auto_cleanup_sessions, monitor_session_health

# 앱 시작 시 자동 정리 (1시간마다)
if st.session_state.get("crm_user_id"):
    agent_id = st.session_state["crm_user_id"]
    
    last_cleanup = st.session_state.get("last_cleanup_time", 0)
    current_time = datetime.datetime.now().timestamp()
    
    if current_time - last_cleanup > 3600:  # 1시간
        auto_cleanup_sessions(agent_id)
        st.session_state["last_cleanup_time"] = current_time

# 세션 건강도 모니터링
health = monitor_session_health()

if health.get("needs_cleanup"):
    st.warning(f"⚠️ 세션 최적화가 필요합니다. (건강도: {health.get('health_score')}/100)")
```

---

## 🔗 관련 파일

### Step 1-4 관련
- `d:\CascadeProjects\hq_briefing.py` (HQ 브리핑 엔진)
- `d:\CascadeProjects\crm_cockpit_ui.py` (에이젠틱 칵핏 UI)
- `d:\CascadeProjects\success_calendar.py` (석세스 캘린더)
- `d:\CascadeProjects\calendar_engine.py` (캘린더 엔진)

### Step 5 관련
- `d:\CascadeProjects\crm_client_detail.py` (인텔리전스 CRM)
- `d:\CascadeProjects\gk_people_extension.sql` (gk_people 확장)

### Step 6 관련
- `d:\CascadeProjects\crm_scanner_ui.py` (빌딩급 AI 스캔)
- `d:\CascadeProjects\loading_skeleton.py` (로딩 스켈레톤)

### Step 7 관련
- `d:\CascadeProjects\crm_policy_bucket_ui.py` (보험 3버킷 관리)
- `d:\CascadeProjects\gk_policies_part_extension.sql` (gk_policies 확장)

### Step 8 관련
- `d:\CascadeProjects\hq_proposal_engine.py` (AI 전략 엔진)
- `d:\CascadeProjects\crm_proposal_ui.py` (제안서 칵핏 UI)
- `d:\CascadeProjects\gk_proposals_schema.sql` (gk_proposals 테이블)

### Step 9 관련
- `d:\CascadeProjects\crm_closing_ui.py` (스마트 클로징 UI)
- `d:\CascadeProjects\hq_reward_engine.py` (리워드 엔진)
- `d:\CascadeProjects\crm_referral_ui.py` (소개 요청 UI)
- `d:\CascadeProjects\gk_rewards_schema.sql` (gk_rewards 테이블)
- `d:\CascadeProjects\session_optimizer.py` (세션 최적화)
- `d:\CascadeProjects\STEP9_SMART_CLOSING_SUCCESS_LOOP_GUIDE.md` (이 문서)

### 데이터베이스
- `gk_people` (고객 정보, current_stage 업데이트)
- `gk_policies` (보험 증권 정보, part 컬럼)
- `gk_policy_roles` (증권-인물 N:M 연결)
- `gk_relationships` (인맥 관계, '소개자' 라인)
- `gk_proposals` (AI 제안서 저장)
- `gk_rewards` (리워드 시스템, 포인트 관리)

---

**[Step 9] 완료 — 스마트 클로징 및 리워드 기반 소개 확보 시스템 (The Success Loop) 구축 완료**

**다음 단계**: 시스템 최종 통합 검수 및 배포 준비
