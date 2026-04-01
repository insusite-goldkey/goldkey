# 🚀 [Step 7] 지능형 보험 3버킷(Triple-Bucket) 관리 시스템 — 통합 가이드

## 📋 개요

**목적**: 보험 계약을 성격에 따라 3개의 영역으로 분리하고, 버튼 하나로 계약 상태를 이동시키는 **지능형 자산 관리 인터페이스** 구축

**핵심 개념**: Step 6의 "빌딩급 OCR"이 **'데이터 입력'**을 자동화했다면, Step 7은 그 데이터를 **'전략적으로 분류하고 관리'**하는 시스템

---

## 🎯 완료된 작업

### 1. crm_policy_bucket_ui.py 신규 모듈 생성 ✅

**파일**: `d:\CascadeProjects\crm_policy_bucket_ui.py` (신규 생성, 550줄)

#### 3분할 버킷 레이아웃

**버킷 구조**:
```
┌─────────────────────────────────────────────────────────────┐
│  💳 보험 3버킷 관리 시스템 — 고객명                          │
├──────────────┬──────────────────┬──────────────────────────┤
│ 섹션 A       │ 섹션 B           │ 섹션 C                   │
│ 🟦 Direct    │ ⬜ External      │ 🟥 Legacy                │
│              │                  │                          │
│ 설계사 직접  │ 타사/타인        │ 해지/승환                │
│ 관리 계약    │ 설계사 계약      │ 과거 계약                │
│              │                  │                          │
│ [정책 카드]  │ [정책 카드]      │ [정책 카드]              │
│ [정책 카드]  │ [정책 카드]      │ [정책 카드]              │
│              │                  │                          │
│ [🔄 승환]    │ [🔄 승환]        │ (버튼 없음)              │
│ [❌ 해지]    │ [❌ 해지]        │                          │
└──────────────┴──────────────────┴──────────────────────────┘
│  📊 보험 포트폴리오 요약                                     │
│  Direct: 3건 (450,000원) | External: 2건 (300,000원)       │
│  Legacy: 1건 (150,000원)                                    │
└─────────────────────────────────────────────────────────────┘
```

**반응형 규칙**:
- **태블릿 가로 (1024px+)**: 3열 그리드 (좌-중-우)
- **모바일 (1024px-)**: 1열 스택 (위-아래 Flow)

**버킷별 배경색** (V4 디자인 시스템):
| 버킷 | 배경색 | 용도 |
|------|--------|------|
| A (Direct) | #E0E7FF (소프트 인디고) | 설계사 직접 관리 |
| B (External) | #F9FAFB (소프트 그레이) | 타사/타인 설계사 |
| C (Legacy) | #FEE2E2 (소프트 코랄) | 해지/승환 과거 |

---

### 2. 고밀도 정책 카드 디자인 (12px Grid) ✅

**`render_policy_card()` 함수**

#### 카드 구조

```
┌─────────────────────────────────────────┐
│ 삼성생명                    피보험자     │  ← 보험사 / 역할
├─────────────────────────────────────────┤
│ 삼성생명 암보험                         │  ← 상품명
├─────────────────────────────────────────┤
│ 월 150,000원      증권번호: 1234567...  │  ← 보험료 / 증권번호
├─────────────────────────────────────────┤
│ ✅ 정상 유지 중                         │  ← AI 요약
├─────────────────────────────────────────┤
│ [🔄 승환]  [❌ 해지]                    │  ← 액션 버튼
└─────────────────────────────────────────┘
```

#### 12px 그리드 적용

**CSS 구현**:
```css
padding: 12px;
margin-bottom: 12px;
gap: 12px;
```

**clamp() 반응형 타이포그래피**:
```css
font-size: clamp(0.88rem, 2vw, 0.95rem);      /* 보험사명 */
font-size: clamp(0.82rem, 1.9vw, 0.88rem);    /* 상품명 */
font-size: clamp(0.78rem, 1.85vw, 0.85rem);   /* 보험료 */
font-size: clamp(0.72rem, 1.8vw, 0.78rem);    /* 증권번호 */
```

**1px 실선 테두리**:
```css
border: 1px solid #374151;
```

---

### 3. 유기적 데이터 이동 로직 (Migration Engine) ✅

**`migrate_policy_to_bucket()` 함수**

#### 데이터 흐름

```
사용자: [해지] 버튼 클릭
  ↓
migrate_policy_to_bucket(policy_id, agent_id, "C")
  ↓
gk_policies 테이블 UPDATE:
  UPDATE gk_policies
  SET part = 'C'
  WHERE id = policy_id
    AND agent_id = agent_id;
  ↓
st.success("✅ 해지 처리되었습니다.")
  ↓
st.rerun() → 화면 새로고침
  ↓
get_policies_by_bucket(person_id, agent_id, "C")
  ↓
섹션 C (Legacy)에 카드 표시
```

#### 이동 애니메이션 (CSS)

```css
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
```

**사용자 경험**:
1. [해지] 버튼 클릭
2. 카드가 오른쪽으로 슬라이드하며 페이드아웃 (0.5초)
3. 화면 새로고침
4. 섹션 C (Legacy)에 카드 나타남

---

### 4. AI 요약 및 비고란 ✅

**`get_ai_policy_summary()` 함수**

#### 규칙 기반 요약 (현재 구현)

**체크 항목**:
1. **만기 임박**: 만기일까지 90일 이내
2. **만기 도래**: 만기일 경과
3. **고액 보험료**: 월 50만원 이상

**요약 메시지 예시**:
| 상황 | 메시지 |
|------|--------|
| 만기 30일 전 | ⚠️ 만기 30일 전 |
| 만기 도래 | ⛔ 만기 도래 |
| 고액 보험료 | 💰 고액 보험료 (50만원 이상) |
| 정상 | ✅ 정상 유지 중 |

#### AI 기반 요약 (향후 구현)

**HQ AI 엔진 연동 예정**:
```python
# TODO: HQ AI 엔진 연동
response = requests.post(
    "https://goldkey-ai-xxxxxx.run.app/api/policy-summary",
    json={
        "policy_id": policy_id,
        "policy_data": policy_data,
        "customer_data": customer_data
    }
)

ai_summary = response.json().get("summary", "")
# → "보장 중복 확인됨 (암진단비 3건)"
# → "납입 만기 임박 (2026-06-30)"
# → "재계약 추천 (현재 상품 대비 보험료 20% 절감 가능)"
```

---

### 5. 반응형 대응 (태블릿 3열, 모바일 1열 스택) ✅

**CSS 그리드 시스템**:

```css
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
```

**Streamlit 컬럼 사용**:
```python
col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    # 섹션 A (Direct)
    render_bucket_section("A", ...)

with col2:
    # 섹션 B (External)
    render_bucket_section("B", ...)

with col3:
    # 섹션 C (Legacy)
    render_bucket_section("C", ...)
```

**반응형 동작**:
- **데스크톱 (1920px)**: 3열 나란히 배치
- **태블릿 가로 (1024px)**: 3열 유지
- **태블릿 세로 (768px)**: 1열 스택 (위→아래)
- **모바일 (375px)**: 1열 스택 (위→아래)

---

## 📊 데이터 흐름 지도

### 전체 시스템 통합 흐름

```
[Step 5] 인텔리전스 CRM 고객 상세 페이지
  ↓
[Step 6] 빌딩급 AI 스캔 모듈
  - OCR 자동 추출
  - gk_policies 테이블 저장
  - part = 'A' (기본값)
  ↓
[Step 7] 보험 3버킷 관리 시스템
  ↓
┌─────────────────────────────────────┐
│ 1. 버킷별 데이터 조회               │
│    - get_policies_by_bucket()       │
│    - part='A', 'B', 'C' 필터링      │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 2. 3분할 레이아웃 렌더링            │
│    - 섹션 A (Direct)                │
│    - 섹션 B (External)              │
│    - 섹션 C (Legacy)                │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 3. 정책 카드 렌더링                 │
│    - render_policy_card()           │
│    - AI 요약 표시                   │
│    - [승환]/[해지] 버튼             │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 4. 버튼 클릭 → 데이터 이동          │
│    - migrate_policy_to_bucket()     │
│    - gk_policies.part 업데이트      │
│    - st.rerun() → 화면 새로고침     │
└─────────────────────────────────────┘
```

### 데이터 이동 상세 흐름

```
초기 상태:
  - 섹션 A: 3건
  - 섹션 B: 2건
  - 섹션 C: 0건
  ↓
사용자: 섹션 A의 "삼성생명 암보험" [해지] 클릭
  ↓
migrate_policy_to_bucket(policy_id, agent_id, "C")
  ↓
SQL 실행:
  UPDATE gk_policies
  SET part = 'C'
  WHERE id = 'uuid-policy-123'
    AND agent_id = 'agent456';
  ↓
st.success("✅ 해지 처리되었습니다.")
  ↓
st.rerun()
  ↓
화면 새로고침:
  - 섹션 A: 2건 (삼성생명 암보험 제거)
  - 섹션 B: 2건 (변화 없음)
  - 섹션 C: 1건 (삼성생명 암보험 추가)
```

---

## 🗄️ 데이터베이스 확장

### gk_policies 테이블 확장 SQL ✅

**파일**: `d:\CascadeProjects\gk_policies_part_extension.sql` (신규 생성)

#### 추가된 컬럼

```sql
-- part 컬럼 추가 (A: Direct, B: External, C: Legacy)
ALTER TABLE gk_policies ADD COLUMN IF NOT EXISTS part TEXT DEFAULT 'A'
    CHECK (part IN ('A', 'B', 'C'));
```

#### 인덱스 추가

```sql
CREATE INDEX IF NOT EXISTS idx_gk_policies_part ON gk_policies(part);
```

#### 기존 데이터 마이그레이션

```sql
-- 기존 데이터 모두 A로 초기화
UPDATE gk_policies
SET part = 'A'
WHERE part IS NULL;
```

**실행 방법**:
1. Supabase SQL Editor 접속
2. `gk_policies_part_extension.sql` 파일 내용 복사
3. SQL Editor에 붙여넣기
4. "Run" 버튼 클릭

---

## 🎨 V4 디자인 시스템 준수

### 버킷별 배경색

```css
/* 섹션 A (Direct) */
background: #E0E7FF;  /* 소프트 인디고 */

/* 섹션 B (External) */
background: #F9FAFB;  /* 소프트 그레이 */

/* 섹션 C (Legacy) */
background: #FEE2E2;  /* 소프트 코랄 */
```

### 정책 카드 스타일

```css
/* 카드 기본 */
background: {버킷별 배경색};
border: 1px solid #374151;
border-radius: 10px;
padding: 12px;
margin-bottom: 12px;
transition: all 0.3s ease;

/* 보험사명 */
font-size: clamp(0.88rem, 2vw, 0.95rem);
font-weight: 900;
color: #1E3A8A;

/* 상품명 */
font-size: clamp(0.82rem, 1.9vw, 0.88rem);
color: #374151;

/* 보험료 */
font-size: clamp(0.78rem, 1.85vw, 0.85rem);
font-weight: 700;
color: #1E3A8A;

/* AI 요약 */
background: rgba(255, 255, 255, 0.5);
border-radius: 6px;
padding: 6px 8px;
font-size: clamp(0.72rem, 1.8vw, 0.78rem);
color: #475569;
```

### 통계 요약 카드

```css
background: linear-gradient(135deg, #F0FDF4, #DCFCE7);  /* 민트 그린 */
border: 1.5px solid #22C55E;
border-radius: 10px;
padding: 12px;
```

---

## ✅ 검증 완료 항목

### 기능 검증
1. ✅ **3분할 버킷 레이아웃**: 태블릿 3열, 모바일 1열 스택
2. ✅ **고밀도 정책 카드**: 12px 그리드 + clamp() 타이포그래피
3. ✅ **유기적 데이터 이동**: [승환]/[해지] 버튼 → part 업데이트
4. ✅ **AI 요약 표시**: 만기 임박, 고액 보험료 체크
5. ✅ **통계 요약**: 버킷별 건수 및 보험료 합계
6. ✅ **이동 애니메이션**: CSS card-migrate 애니메이션

### 디자인 검증
1. ✅ **V4 디자인 통일**: 소프트 인디고/그레이/코랄 배경
2. ✅ **12px 그리드**: 모든 간격에 12px 적용
3. ✅ **1px 실선 테두리**: #374151 색상
4. ✅ **clamp() 타이포그래피**: 반응형 폰트 크기
5. ✅ **HTML 렌더링**: unsafe_allow_html=True 필수 (CORE RULE 2)

### 데이터 무결성 검증
1. ✅ **gk_policies part 컬럼**: 'A', 'B', 'C' CHECK 제약
2. ✅ **gk_policy_roles 조인**: person_id 기반 증권 조회
3. ✅ **Soft Delete 준수**: is_deleted=False 필터링
4. ✅ **세션 상태 보호**: st.rerun() 시 세션 검증 유지 (CORE RULE 1)

---

## 🚀 다음 단계 (Step 8 예상)

### A. HQ AI 엔진 연동 (정책 요약)

**현재 상태**: 규칙 기반 요약만 구현

**개선 방향**:
```python
# HQ AI 엔진 API 호출
response = requests.post(
    "https://goldkey-ai-xxxxxx.run.app/api/policy-summary",
    json={
        "policy_id": policy_id,
        "policy_data": policy_data,
        "customer_data": customer_data,
        "related_policies": related_policies
    }
)

ai_summary = response.json().get("summary", "")
# → "보장 중복 확인됨 (암진단비 3건, 총 6천만원)"
# → "재계약 추천 (현재 상품 대비 보험료 20% 절감 가능)"
```

### B. 버킷 간 드래그 앤 드롭

**기능**:
- 정책 카드를 드래그하여 다른 버킷으로 이동
- 드롭 시 자동으로 part 업데이트
- 실시간 애니메이션

**구현 방향**:
- Streamlit Draggable 컴포넌트 사용
- 또는 JavaScript 기반 커스텀 컴포넌트

### C. 버킷별 필터링 및 정렬

**기능**:
- 보험사별 필터링
- 보험료 높은 순/낮은 순 정렬
- 만기일 임박 순 정렬
- 검색 기능 (상품명, 증권번호)

### D. 일괄 처리 기능

**기능**:
- 여러 계약 선택 (체크박스)
- 일괄 승환/해지
- 일괄 버킷 이동
- 진행률 표시

---

## 📝 신규 생성 파일

1. **`crm_policy_bucket_ui.py`** (550줄)
   - 3분할 버킷 레이아웃
   - 고밀도 정책 카드 디자인
   - 유기적 데이터 이동 로직
   - AI 요약 및 비고란
   - 반응형 대응

2. **`gk_policies_part_extension.sql`** (SQL 스크립트)
   - part 컬럼 추가 ('A', 'B', 'C')
   - 인덱스 추가
   - 기존 데이터 마이그레이션

3. **`STEP7_TRIPLE_BUCKET_GUIDE.md`** (통합 가이드, 이 문서)
   - 사용 예시 및 통합 방법
   - 데이터 흐름 지도
   - V4 디자인 시스템 가이드
   - 검증 완료 항목

---

## 🛠️ 사용 예시

### crm_client_detail.py 통합

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

### 독립 페이지로 사용

```python
# crm_app_impl.py

if st.session_state.get("crm_spa_screen") == "policy_bucket":
    person_id = st.session_state.get("crm_selected_pid")
    agent_id = st.session_state.get("crm_user_id")
    customer_name = st.session_state.get("crm_customer_name", "")
    
    if person_id and agent_id:
        render_policy_bucket_system(person_id, agent_id, customer_name)
```

---

## 🔗 관련 파일

### Step 5 관련
- `d:\CascadeProjects\crm_client_detail.py` (인텔리전스 CRM 고객 상세)
- `d:\CascadeProjects\gk_people_extension.sql` (gk_people 테이블 확장)
- `d:\CascadeProjects\STEP5_INTELLIGENCE_CRM_GUIDE.md` (Step 5 가이드)

### Step 6 관련
- `d:\CascadeProjects\crm_scanner_ui.py` (빌딩급 AI 스캔 모듈)
- `d:\CascadeProjects\loading_skeleton.py` (로딩 스켈레톤 UI)
- `d:\CascadeProjects\STEP6_BUILDING_GRADE_OCR_GUIDE.md` (Step 6 가이드)

### Step 7 관련
- `d:\CascadeProjects\crm_policy_bucket_ui.py` (보험 3버킷 관리 시스템)
- `d:\CascadeProjects\gk_policies_part_extension.sql` (gk_policies 테이블 확장)
- `d:\CascadeProjects\STEP7_TRIPLE_BUCKET_GUIDE.md` (이 문서)

### 데이터베이스
- `gk_policies` (보험 증권 정보, part 컬럼 추가)
- `gk_policy_roles` (증권-인물 N:M 연결)
- `gk_people` (고객 정보)

---

**[Step 7] 완료 — 지능형 보험 3버킷(Triple-Bucket) 관리 시스템 구축 완료**

**다음 단계**: Step 8 (예상) — HQ AI 엔진 연동 및 드래그 앤 드롭 기능 구현
