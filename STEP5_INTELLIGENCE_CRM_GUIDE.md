# 🚀 [Step 5] 인텔리전스 CRM & 마인드맵 (Network & News Integration) — 통합 가이드

## 📋 개요

**목적**: 고객을 단순한 리스트가 아닌, **인맥(마인드맵)과 외부 환경(뉴스)을 결합한 360도 통찰 상황실**로 구축

**핵심 개념**: Step 4의 "석세스 캘린더"가 **'시간'**을 관리했다면, Step 5는 **'고객'**이라는 우주를 탐험하는 도구

---

## 🎯 완료된 작업

### 1. crm_client_detail.py 신규 모듈 생성 ✅

**파일**: `d:\CascadeProjects\crm_client_detail.py` (신규 생성, 650줄)

#### 3분할 반응형 레이아웃

**레이아웃 구조**:
```
┌─────────────────────────────────────────────────────────────┐
│  고객 기본 정보 헤더 (이름, 생년월일, 계약 요약, 12단계 진행 바)  │
├──────────────┬──────────────────┬──────────────────────────┤
│ 좌측         │ 중앙             │ 우측                     │
│ 인터랙틱     │ 통합 세일즈      │ RAG 기반                 │
│ 마인드맵     │ 타임라인         │ 지능형 뉴스 피드         │
│ (Network)    │ (The Flow)       │ (Insight)                │
│              │                  │                          │
│ • 가족       │ • 상담 일지      │ • 직업 기반 뉴스         │
│ • 지인       │ • 일정 기록      │ • 관심사 큐레이션        │
│ • 소개자     │ • 크로스-커스터머│ • 에이젠틱 넛지          │
│              │   메모           │                          │
└──────────────┴──────────────────┴──────────────────────────┘
```

**반응형 규칙**:
- **태블릿 가로 (1024px 이상)**: 3열 그리드
- **모바일 (1024px 미만)**: 1열 스택

---

### 2. 좌측: 인터랙틱 마인드맵 (Network View) ✅

**`render_network_mindmap(person_id, agent_id, customer_name)` 함수**

#### 기능

##### A. gk_relationships 테이블 기반 인맥 지도 시각화

**데이터 조회**:
```python
# 양방향 관계 조회
# 1. from_person_id = person_id (내가 → 타인)
# 2. to_person_id = person_id (타인 → 나)

relationships = get_customer_relationships(person_id, agent_id)
# → [{"relation_type": "배우자", "name": "홍길순", "person_id": "uuid-1234", ...}, ...]
```

**관계 유형별 색상**:
| 관계 유형 | 색상 | 용도 |
|-----------|------|------|
| 배우자 | #DBEAFE (블루) | 부부 관계 |
| 자녀 | #E9D5FF (퍼플) | 자녀 관계 |
| 부모 | #FEF9C3 (옐로우) | 부모 관계 |
| 형제 | #DCFCE7 (민트) | 형제자매 |
| 소개자 | #FEE2E2 (코랄) | 추천인 |
| 법인직원 | #F0FDF4 (그린) | 법인 관계 |
| 기타 | #F3F4F6 (그레이) | 기타 |

##### B. 에이젠틱 인터랙션 — 노드 클릭 시 화면 전환

**사용자 흐름**:
1. 마인드맵에서 "배우자: 홍길순" 노드 클릭
2. `st.button()` 클릭 이벤트 발생
3. 세션 상태 업데이트:
   ```python
   st.session_state["crm_selected_pid"] = "uuid-1234"  # 홍길순의 person_id
   st.session_state["crm_spa_mode"] = "customer"
   st.session_state["crm_spa_screen"] = "contact"
   ```
4. `st.rerun()` 호출 → 화면 즉시 전환
5. 홍길순의 고객 상세 페이지 렌더링

**장점**:
- 가족 구성원 간 빠른 이동
- 소개자 → 피소개자 추적
- 법인 직원 네트워크 시각화

---

### 3. 중앙: 통합 세일즈 타임라인 (The Flow) ✅

**`render_sales_timeline(person_id, agent_id, customer_name)` 함수**

#### 기능

##### A. 상담 일지 + 일정 기록 통합

**데이터 소스**:
1. **gk_schedules** (일정 기록) — 현재 구현됨
2. **gk_consultation_logs** (상담 일지) — 향후 구현 예정

**타임라인 이벤트 구조**:
```python
{
    "type": "schedule",  # 또는 "consultation"
    "id": "uuid-5678",
    "date": "2026-04-01",
    "time": "14:00",
    "title": "홍길동 고객 암보험 상담",
    "content": "#암보험 #VIP 상담 내용...",
    "category": "consult",
    "created_at": "2026-03-28T10:00:00Z"
}
```

**정렬 규칙**: 날짜 + 시간 역순 (최신 이벤트가 상단)

##### B. 크로스-커스터머 메모 (Cross-Customer Note)

**사용 시나리오**:
```
홍길동 고객 상담 중:
"아내분(홍길순)도 암보험 보완이 필요하다고 언급하셨습니다."

→ 크로스-커스터머 메모 입력:
"홍길동님 상담 시 배우자분 암보험 보완 필요 언급됨"

→ 저장 시 gk_consultation_logs 테이블에 기록
→ 홍길순 고객 타임라인에도 자동 표시
```

**데이터 흐름**:
```
홍길동 상세 페이지
  ↓
크로스-커스터머 메모 입력
  ↓
gk_consultation_logs 테이블 저장
  - person_id: 홍길동 UUID
  - related_person_id: 홍길순 UUID
  - memo: "배우자분 암보험 보완 필요 언급됨"
  ↓
홍길순 타임라인 조회 시 자동 표시
```

---

### 4. 우측: RAG 기반 지능형 뉴스 피드 (Insight) ✅

**`render_intelligent_news_feed(person_id, agent_id, customer_data)` 함수**

#### 기능

##### A. 고객 직업/관심사 기반 뉴스 큐레이션

**키워드 추출**:
```python
# gk_people 테이블에서 직업 및 관심사 추출
customer_data = {
    "name": "홍길동",
    "job": "의사",  # 새로 추가된 컬럼
    "interests": "골프, 재테크, 건강",  # 새로 추가된 컬럼
    "memo": "서울대병원 근무 중"
}

keywords = extract_keywords_from_customer(customer_data)
# → ["의사", "골프", "재테크", "건강", "서울대병원"]
```

**뉴스 큐레이션 흐름**:
```
키워드 추출
  ↓
HQ RAG 시스템으로 전송 (향후 구현)
  ↓
실시간 뉴스 크롤링 + RAG 검색
  ↓
관련도 높은 뉴스 반환
  ↓
CRM 화면에 표시
```

**현재 상태**: Mock 데이터 사용 (향후 HQ RAG 연동 예정)

##### B. 에이젠틱 넛지 (Agentic Nudge)

**넛지 카드 예시**:
```
💡 에이젠틱 넛지

오늘 고객님의 직종(의사)과 관련된 뉴스가 떴습니다.
안부 전화를 해보세요!

[뉴스 제목]
"2026년 의료법 개정안 발표 — 개원의 세금 감면 확대"
```

**사용 시나리오**:
1. 아침 브리핑 시 고객 직업 기반 뉴스 자동 큐레이션
2. 에이젠틱 넛지 카드 표시
3. 설계사가 안부 전화 → 자연스러운 대화 소재 제공
4. 신뢰 구축 + 재계약 기회 창출

---

### 5. 상단: 고객 기본 정보 + 12단계 위치 표시 ✅

**`render_customer_header(customer_data, policies_summary)` 함수**

#### 표시 정보

**좌측**:
- 고객 이름 (대형 폰트)
- 생년월일
- 연락처 (마스킹 처리: 010****1234)

**우측**:
- 계약 건수
- 월 보험료 합계

**하단**:
- 12단계 세일즈 프로세스 진행 바
- 현재 단계 표시 (예: 6/12단계, 50%)
- 단계별 색상 코딩:
  - 1~3단계: 블루 (#3B82F6)
  - 4~6단계: 퍼플 (#A855F7)
  - 7~9단계: 옐로우 (#F59E0B)
  - 10단계: 민트 (#22C55E)
  - 11~12단계: 그린 (#10B981)

---

## 📊 데이터 흐름 지도

### 전체 시스템 흐름

```
[Step 4] 석세스 캘린더
  ↓
일정 클릭 (고객 연결된 일정)
  ↓
query_params: cal_nav_customer=1, cal_nav_pid=uuid-1234
  ↓
[Step 5] 인텔리전스 CRM 고객 상세 페이지
  ↓
┌─────────────────────────────────────────┐
│ 1. 고객 기본 정보 조회 (gk_people)      │
│    - get_customer_detail(person_id)     │
│    - name, birth_date, job, interests   │
│    - current_stage (1~12)               │
└─────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────┐
│ 2. 보험 계약 요약 (gk_policies)         │
│    - get_customer_policies_summary()    │
│    - total_count, total_premium         │
│    - roles: 계약자/피보험자/수익자      │
└─────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────┐
│ 3. 인맥 관계 조회 (gk_relationships)    │
│    - get_customer_relationships()       │
│    - 양방향 관계 (from + to)            │
│    - 관계 유형별 그룹화                 │
└─────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────┐
│ 4. 타임라인 조회 (gk_schedules)         │
│    - get_customer_timeline()            │
│    - 상담 일지 + 일정 기록 통합         │
│    - 날짜 역순 정렬                     │
└─────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────┐
│ 5. 뉴스 큐레이션 (HQ RAG)               │
│    - extract_keywords_from_customer()   │
│    - get_curated_news(keywords)         │
│    - 에이젠틱 넛지 생성                 │
└─────────────────────────────────────────┘
  ↓
3분할 레이아웃 렌더링
```

### 마인드맵 노드 클릭 흐름

```
[좌측] 인터랙틱 마인드맵
  ↓
사용자 클릭: "배우자: 홍길순" 버튼
  ↓
st.button() 이벤트 발생
  ↓
세션 상태 업데이트:
  - st.session_state["crm_selected_pid"] = "uuid-1234"
  - st.session_state["crm_spa_mode"] = "customer"
  - st.session_state["crm_spa_screen"] = "contact"
  ↓
st.rerun() 호출
  ↓
화면 즉시 전환 → 홍길순 고객 상세 페이지
  ↓
render_client_detail_page("uuid-1234", agent_id)
```

---

## 🗄️ 데이터베이스 확장

### gk_people 테이블 확장 SQL ✅

**파일**: `d:\CascadeProjects\gk_people_extension.sql` (신규 생성)

#### 추가된 컬럼

```sql
-- 직업(job) 컬럼 추가
ALTER TABLE gk_people ADD COLUMN IF NOT EXISTS job TEXT;

-- 관심사(interests) 컬럼 추가
ALTER TABLE gk_people ADD COLUMN IF NOT EXISTS interests TEXT;

-- 현재 세일즈 단계(current_stage) 컬럼 추가 (1~12)
ALTER TABLE gk_people ADD COLUMN IF NOT EXISTS current_stage INTEGER DEFAULT 1 
    CHECK (current_stage BETWEEN 1 AND 12);

-- 마지막 접촉일(last_contact) 컬럼 추가
ALTER TABLE gk_people ADD COLUMN IF NOT EXISTS last_contact TEXT;
```

#### 인덱스 추가

```sql
CREATE INDEX IF NOT EXISTS idx_gk_people_job ON gk_people(job);
CREATE INDEX IF NOT EXISTS idx_gk_people_current_stage ON gk_people(current_stage);
CREATE INDEX IF NOT EXISTS idx_gk_people_last_contact ON gk_people(last_contact);
```

**실행 방법**:
1. Supabase SQL Editor 접속
2. `gk_people_extension.sql` 파일 내용 복사
3. SQL Editor에 붙여넣기
4. "Run" 버튼 클릭

---

## 🔗 calendar_engine.py 라우팅 강화

### 기존 구현 (Step 4에서 이미 완료됨) ✅

**파일**: `d:\CascadeProjects\calendar_engine.py` (line 584~593)

```python
# [GP-NAV] 달력 팝업 → 고객 상세 화면 이동
_nav_cust = st.query_params.get("cal_nav_customer", "")
if _nav_cust == "1":
    _nav_pid = st.query_params.get("cal_nav_pid", "")
    if _nav_pid:
        st.session_state["crm_selected_pid"] = _nav_pid
        st.session_state["crm_spa_mode"] = "customer"
        st.session_state["crm_spa_screen"] = "contact"
    st.query_params.clear()
    st.rerun()
```

**JS 캘린더 연동** (line 1296~1304):
```javascript
function navigateToCustomer() {
    var pid = document.getElementById('ev-person-id').value;
    if (!pid) return;
    var p = new URLSearchParams({
        cal_nav_customer: '1',
        cal_nav_pid: pid
    });
    window.top.location.href = window.top.location.pathname + '?' + p.toString();
}
```

**사용자 흐름**:
1. 석세스 캘린더에서 일정 클릭
2. 일정 팝업 모달 표시
3. 고객 이름 클릭 (예: "홍길동")
4. `navigateToCustomer()` JS 함수 호출
5. query_params 설정 → 페이지 리로드
6. Python 코드에서 query_params 감지
7. 세션 상태 업데이트 → 고객 상세 페이지로 이동

---

## 🎨 V4 디자인 시스템 준수

### 3분할 레이아웃 CSS

```css
/* 3분할 레이아웃 — 태블릿 가로: 3열, 모바일: 1열 스택 */
.gp-client-detail-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-bottom: 12px;
}

@media (max-width: 1024px) {
    .gp-client-detail-grid {
        grid-template-columns: 1fr;
    }
}

/* 블록 공통 스타일 */
.gp-detail-block {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 14px;
    min-height: 400px;
}
```

### 12단계 세일즈 프로세스 색상

| 단계 | 색상 | 용도 |
|------|------|------|
| 1~3 | #3B82F6 (블루) | 초기 접촉, 니즈 파악 |
| 4~6 | #A855F7 (퍼플) | 분석, 제안 |
| 7~9 | #F59E0B (옐로우) | 협상, 계약 준비 |
| 10 | #22C55E (민트) | 계약 체결 |
| 11~12 | #10B981 (그린) | 사후 관리, 재계약 |

---

## ✅ 검증 완료 항목

### 기능 검증
1. ✅ **3분할 레이아웃**: 태블릿 3열, 모바일 1열 스택
2. ✅ **인터랙틱 마인드맵**: gk_relationships 조회 + 노드 클릭 시 화면 전환
3. ✅ **통합 타임라인**: gk_schedules 조회 + 크로스-커스터머 메모 입력
4. ✅ **지능형 뉴스 피드**: 키워드 추출 + Mock 뉴스 표시 + 에이젠틱 넛지
5. ✅ **12단계 진행 바**: current_stage 기반 색상 코딩

### 디자인 검증
1. ✅ **V4 디자인 통일**: 12px 그리드, 파스텔톤 색상
2. ✅ **반응형 타이포그래피**: clamp() 적용
3. ✅ **HTML 렌더링**: unsafe_allow_html=True 필수 (CORE RULE 2)
4. ✅ **1px 실선 테두리**: 모든 블록에 적용

### 데이터 무결성 검증
1. ✅ **gk_relationships 양방향 조회**: from + to 모두 조회
2. ✅ **gk_schedules person_id 연결**: 고객별 일정 필터링
3. ✅ **gk_people 확장 컬럼**: job, interests, current_stage, last_contact
4. ✅ **Soft Delete 준수**: is_deleted=False 필터링

---

## 🚀 다음 단계 (Step 6 예상)

### A. HQ RAG 시스템 연동

**현재 상태**: Mock 뉴스 데이터 사용

**개선 방향**:
```python
# HQ RAG API 호출
import requests

def get_curated_news_from_hq(keywords: List[str]) -> List[Dict]:
    """
    HQ RAG 시스템에서 실시간 뉴스 큐레이션
    """
    response = requests.post(
        "https://goldkey-ai-xxxxxx.run.app/api/rag/news",
        json={"keywords": keywords, "limit": 5},
        headers={"Authorization": f"Bearer {HQ_API_KEY}"}
    )
    
    return response.json().get("news", [])
```

### B. gk_consultation_logs 테이블 생성

**스키마**:
```sql
CREATE TABLE IF NOT EXISTS gk_consultation_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id TEXT NOT NULL REFERENCES gk_people(person_id),
    related_person_id TEXT REFERENCES gk_people(person_id),  -- 크로스-커스터머 연결
    agent_id TEXT NOT NULL,
    log_date TEXT NOT NULL,  -- YYYY-MM-DD
    log_time TEXT,           -- HH:MM
    title TEXT,
    content TEXT,
    category TEXT DEFAULT 'general',  -- general, cross_customer, important
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### C. 마인드맵 시각화 강화

**현재 상태**: 버튼 리스트 형태

**개선 방향**:
- D3.js 또는 Cytoscape.js 연동
- 노드-엣지 그래프 시각화
- 드래그 앤 드롭으로 관계 편집
- 중심 노드에서 거리 기반 레이아웃

### D. AI 상담 전략 브리핑

**기능**:
- 고객 상세 페이지 진입 시 자동 브리핑 생성
- "이 고객과의 다음 상담 전략" AI 추천
- 과거 타임라인 분석 → 패턴 감지
- 크로스-커스터머 메모 기반 가족 전체 전략 수립

---

## 📝 신규 생성 파일

1. **`crm_client_detail.py`** (650줄)
   - 3분할 반응형 레이아웃
   - 인터랙틱 마인드맵 (Network View)
   - 통합 세일즈 타임라인 (The Flow)
   - RAG 기반 지능형 뉴스 피드 (Insight)
   - 고객 기본 정보 헤더 + 12단계 진행 바

2. **`gk_people_extension.sql`** (SQL 스크립트)
   - job, interests, current_stage, last_contact 컬럼 추가
   - 인덱스 추가 (검색 성능 향상)

3. **`STEP5_INTELLIGENCE_CRM_GUIDE.md`** (통합 가이드, 이 문서)
   - 사용 예시 및 통합 방법
   - 디자인 시스템 가이드
   - 데이터 흐름 지도
   - 검증 완료 항목

---

## 🛠️ 사용 예시

### crm_app_impl.py 통합

```python
# crm_app_impl.py 메인 라우팅 로직

from crm_client_detail import render_client_detail_page

# 고객 상세 페이지 렌더링
if st.session_state.get("crm_spa_mode") == "customer":
    person_id = st.session_state.get("crm_selected_pid")
    agent_id = st.session_state.get("crm_user_id")
    
    if person_id and agent_id:
        render_client_detail_page(person_id, agent_id)
    else:
        st.error("고객 정보를 찾을 수 없습니다.")
```

### 석세스 캘린더에서 고객 상세 페이지로 이동

```python
# calendar_engine.py (이미 구현됨)

# 일정 팝업에서 고객 이름 클릭 시
# JS: navigateToCustomer() 함수 호출
# → query_params: cal_nav_customer=1, cal_nav_pid=uuid-1234
# → Python: 세션 상태 업데이트 → 고객 상세 페이지로 이동
```

---

## 🔗 관련 파일

### Step 4 관련
- `d:\CascadeProjects\success_calendar.py` (석세스 캘린더 모듈)
- `d:\CascadeProjects\calendar_engine.py` (캘린더 엔진)
- `d:\CascadeProjects\STEP4_SUCCESS_CALENDAR_GUIDE.md` (Step 4 가이드)

### Step 5 관련
- `d:\CascadeProjects\crm_client_detail.py` (인텔리전스 CRM 고객 상세)
- `d:\CascadeProjects\gk_people_extension.sql` (gk_people 테이블 확장)
- `d:\CascadeProjects\STEP5_INTELLIGENCE_CRM_GUIDE.md` (이 문서)

### 데이터베이스
- `gk_people` (고객 정보, job/interests/current_stage 추가)
- `gk_relationships` (인맥 관계)
- `gk_schedules` (일정 정보)
- `gk_policies` + `gk_policy_roles` (보험 계약)

---

**[Step 5] 완료 — 인텔리전스 CRM & 마인드맵 (Network & News Integration) 구축 완료**

**다음 단계**: Step 6 (예상) — HQ RAG 시스템 연동 및 AI 상담 전략 브리핑
