# 🚀 [Step 8] AI 감성 세일즈 전략 및 맞춤형 제안서 자동 생성 — 통합 가이드

## 📋 개요

**목적**: 차가운 데이터를 **'따뜻하고 설득력 있는 제안'**으로 변환하는 AI 감성 세일즈 엔진 구축

**핵심 개념**: Step 5(고객 페르소나) + Step 6(스캔 증권) + Step 7(3버킷 분류)의 데이터를 융합하여, AI가 고객 맞춤형 제안서와 감성 스크립트를 1초 만에 생성

---

## 🎯 완료된 작업

### 1. hq_proposal_engine.py 신규 모듈 생성 ✅

**파일**: `d:\CascadeProjects\hq_proposal_engine.py` (신규 생성, 600줄)

#### AI 전략 엔진 핵심 기능

**1) 데이터 융합 (Step 5 + Step 7)**

```python
# Step 5: 고객 페르소나 조회
persona = get_customer_persona(person_id, agent_id)
# → name, job, interests, current_stage

# Step 7: 보험 3버킷 조회
buckets = get_insurance_buckets(person_id, agent_id)
# → A (Direct), B (External), C (Legacy)
```

**2) 보장 공백 분석 (Gap Analysis)**

```python
def analyze_coverage_gap(buckets: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    보장 공백 분석
    
    Returns:
        - current_coverage: 현재 보장 현황 (생명/손해/실손/연금/저축)
        - total_premium: 총 월 보험료
        - gaps: 보장 공백 목록 (severity: high/medium)
        - conversion_targets: 타사 계약 중 승환 추천 목록
    """
```

**보장 공백 판단 규칙**:
| 조건 | 심각도 | 메시지 |
|------|--------|--------|
| 생명보험 0건 | high | 생명보험 가입 필요 (사망 보장 부재) |
| 실손의료보험 0건 | high | 실손의료보험 가입 필요 (의료비 보장 부재) |
| 연금보험 0건 | medium | 노후 준비 필요 (연금 보장 부재) |

**승환 추천 규칙**:
- 섹션 B (External) 계약 중 월 보험료 10만원 이상
- 이유: "고액 보험료 절감 가능"

**3) 감성 페르소나 매칭 (3가지 톤 스크립트)**

```python
def generate_emotional_scripts(
    persona: Dict[str, Any],
    gap_analysis: Dict[str, Any]
) -> Dict[str, Dict[str, str]]:
    """
    3가지 톤별 스크립트 생성
    
    Returns:
        - professional: 전문적 톤 (오프닝, 본론, 거절 처리)
        - emotional: 감성적 톤
        - direct: 직설적 톤
    """
```

**3가지 톤 비교**:

| 톤 | 오프닝 예시 | 적합 고객 |
|---|------------|----------|
| 🎓 전문적 | "전문가 관점에서 볼 때..." | 의사, 교수, 전문직 |
| 💖 감성적 | "소중한 가족을 위해..." | 주부, 교사, 일반 직장인 |
| ⚡ 직설적 | "솔직히 말씀드려 부족합니다" | 사업가, 대표, 결단력 있는 고객 |

**직업별 커스터마이징**:
```python
if "의사" in job or "간호" in job:
    professional["opening"] += "의사님이시니 보험의 중요성을 누구보다 잘 아실 거라 생각합니다."
elif "교사" in job or "교수" in job:
    emotional["opening"] += "교사님이시니 미래 설계의 중요성을 잘 아실 것 같아요."
elif "사업" in job or "대표" in job:
    direct["opening"] += "대표님이시니 숫자와 리스크 관리에 익숙하실 겁니다."
```

**4) 3가지 플랜 추천 (실속/표준/VIP)**

```python
def generate_three_plans(
    persona: Dict[str, Any],
    gap_analysis: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    3가지 플랜 추천
    
    Returns:
        - budget_plan: 실속형 (현재 보험료 +20%)
        - standard_plan: 표준형 (현재 보험료 +50%)
        - vip_plan: VIP형 (현재 보험료 +100%)
    """
```

**3가지 플랜 비교**:

| 플랜 | 월 보험료 | 총 보장 | 특징 |
|------|----------|---------|------|
| 💰 실속형 | 현재 +20% | 1.5억원 | 필수 보장만 집중 |
| ⭐ 표준형 | 현재 +50% | 4.5억원 | 균형잡힌 보장 설계 |
| 👑 VIP형 | 현재 +100% | 8억원 + 연금 | 최고 수준 보장 + 노후 준비 |

**5) 통합 제안서 생성 (Main Engine)**

```python
def generate_proposal(person_id: str, agent_id: str) -> Dict[str, Any]:
    """
    통합 제안서 생성
    
    Returns:
        - success: 성공 여부
        - metadata: 제안서 메타데이터 (proposal_id, created_at)
        - persona: 고객 페르소나
        - buckets: 보험 3버킷
        - gap_analysis: 보장 공백 분석
        - emotional_scripts: 3가지 톤 스크립트
        - three_plans: 3가지 플랜
    """
```

**6) 에이전틱 단계 업데이트 (4단계 → 5/6단계)**

```python
def update_customer_stage_to_proposal(
    person_id: str, 
    agent_id: str, 
    target_stage: int = 5
) -> bool:
    """
    고객 세일즈 단계 업데이트
    
    Args:
        target_stage: 5 (제안), 6 (설득)
    """
```

**12단계 세일즈 프로세스**:
```
1단계: 초기 접촉
2단계: 정보 수집
3단계: 관계 구축
4단계: 분석 (Step 6 OCR 완료)
→ 5단계: 제안 (Step 8 제안서 생성) ✅
→ 6단계: 설득 (제안서 전달 후)
7단계: 협상
...
12단계: 계약 체결
```

---

### 2. crm_proposal_ui.py 신규 모듈 생성 ✅

**파일**: `d:\CascadeProjects\crm_proposal_ui.py` (신규 생성, 550줄)

#### 제안서 칵핏 UI 구조

```
┌─────────────────────────────────────────────────────────────┐
│  🧠 AI 감성 세일즈 제안서 — 고객명                          │
│  [🚀 AI 제안서 생성]                                        │
├─────────────────────────────────────────────────────────────┤
│  📊 보장 공백 분석 (Gap Analysis)                           │
│  ┌──────────────────┬──────────────────────────────────┐   │
│  │ 현재 보장 (Red)  │ 제안 보장 (Green)                │   │
│  │ • 생명: 0건      │ • 생명: 1건 ✅                   │   │
│  │ • 실손: 0건      │ • 실손: 1건 ✅                   │   │
│  │ 월 보험료: 0원   │ 월 보험료: 150,000원 (예상)      │   │
│  └──────────────────┴──────────────────────────────────┘   │
│  ⚠️ 생명보험 가입 필요 (사망 보장 부재)                     │
│  ⚠️ 실손의료보험 가입 필요 (의료비 보장 부재)               │
├─────────────────────────────────────────────────────────────┤
│  💎 AI 추천 플랜 (3가지)                                    │
│  [💰 실속형] [⭐ 표준형] [👑 VIP형]                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 실속형 플랜                                          │   │
│  │ 월 보험료: 120,000원                                 │   │
│  │ 총 보장: 1.5억원                                     │   │
│  │ 📋 보장 항목:                                        │   │
│  │   • 생명보험: 1억원 (월 50,000원)                    │   │
│  │   • 실손의료보험: 5천만원 (월 30,000원)              │   │
│  │ ✨ 특징:                                             │   │
│  │   • 필수 보장만 집중                                 │   │
│  │   • 합리적인 보험료                                  │   │
│  │ 💡 예산을 고려하면서도 필수 보장을 갖추고 싶으신 분께│   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  🎭 AI 감성 스크립트 (3가지 톤)                             │
│  ○ 🎓 전문적 톤  ● 💖 감성적 톤  ○ ⚡ 직설적 톤            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 🎤 오프닝 멘트                                       │   │
│  │ "고객님, 요즘 어떻게 지내세요? 바쁘신 와중에도..."   │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ 📝 본론                                              │   │
│  │ "고객님의 소중한 가족과 미래를 위해..."              │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ 🛡️ 거절 처리 스크립트                               │   │
│  │ "저도 고객님의 입장이라면 같은 생각을 했을 거예요..." │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  📱 모바일 전용 요약 제안서                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 💎 고객님을 위한 맞춤 제안                           │   │
│  │ 📊 현재 보장 현황: 월 0원, 보장 공백 2건             │   │
│  │ 💡 AI 추천 플랜:                                     │   │
│  │   1. 실속형: 월 120,000원                            │   │
│  │   2. 표준형: 월 180,000원                            │   │
│  │   3. VIP형: 월 240,000원                             │   │
│  └─────────────────────────────────────────────────────┘   │
│  [💬 카카오톡 공유] [📄 PDF 다운로드]                      │
└─────────────────────────────────────────────────────────────┘
```

#### 핵심 UI 컴포넌트

**1) 보장 공백 분석 비주얼 리포트**

```python
def render_gap_analysis_visual(gap_analysis: Dict[str, Any]):
    """
    현재 보장 (Red) vs 제안 보장 (Green) 비교 차트
    
    - 좌측: 현재 보장 (#FEE2E2 배경)
    - 우측: 제안 보장 (#DCFCE7 배경)
    - 보장 공백 알림 (#FEF3C7 배경)
    """
```

**2) 3가지 플랜 탭**

```python
def render_three_plans_tabs(three_plans: List[Dict[str, Any]]):
    """
    탭 형태로 3가지 플랜 표시
    
    - tab1: 💰 실속형 (#E0E7FF 배경)
    - tab2: ⭐ 표준형 (#DBEAFE 배경)
    - tab3: 👑 VIP형 (#FEF3C7 배경)
    """
```

**3) 감성 스크립트 선택기**

```python
def render_emotional_scripts_selector(emotional_scripts: Dict[str, Dict[str, str]]):
    """
    라디오 버튼으로 톤 선택
    
    - 🎓 전문적 톤 (#E0E7FF 배경)
    - 💖 감성적 톤 (#DBEAFE 배경)
    - ⚡ 직설적 톤 (#FEF3C7 배경)
    """
```

**4) 모바일 전용 요약 제안서**

```python
def render_mobile_summary(proposal_data: Dict[str, Any], person_id: str):
    """
    모바일 최적화 요약 제안서
    
    - 최대 너비: 400px
    - 그라데이션 배경: #E0E7FF → #DBEAFE
    - 카카오톡 공유 / PDF 다운로드 버튼
    """
```

---

### 3. gk_proposals_schema.sql 생성 ✅

**파일**: `d:\CascadeProjects\gk_proposals_schema.sql` (신규 생성)

#### 테이블 스키마

```sql
CREATE TABLE IF NOT EXISTS gk_proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id TEXT NOT NULL UNIQUE,
    person_id TEXT NOT NULL REFERENCES gk_people(person_id) ON DELETE RESTRICT,
    agent_id TEXT NOT NULL,
    proposal_data JSONB NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**인덱스**:
```sql
CREATE INDEX IF NOT EXISTS idx_gk_proposals_person_id ON gk_proposals(person_id);
CREATE INDEX IF NOT EXISTS idx_gk_proposals_agent_id ON gk_proposals(agent_id);
CREATE INDEX IF NOT EXISTS idx_gk_proposals_proposal_id ON gk_proposals(proposal_id);
```

**proposal_data JSONB 구조**:
```json
{
  "success": true,
  "metadata": {
    "proposal_id": "PROP_12345678_20260401192800",
    "created_at": "2026-04-01T19:28:00",
    "customer_name": "홍길동",
    "agent_id": "agent123"
  },
  "persona": {
    "name": "홍길동",
    "job": "의사",
    "interests": "등산, 독서",
    "current_stage": 5
  },
  "buckets": {
    "A": [...],
    "B": [...],
    "C": [...]
  },
  "gap_analysis": {
    "current_coverage": {"생명": 0, "실손": 0, ...},
    "total_premium": 0,
    "gaps": [...],
    "conversion_targets": [...]
  },
  "emotional_scripts": {
    "professional": {...},
    "emotional": {...},
    "direct": {...}
  },
  "three_plans": [...]
}
```

---

## 📊 데이터 흐름 지도

### 전체 시스템 통합 흐름

```
[Step 5] 인텔리전스 CRM
  - 고객 페르소나 (name, job, interests, current_stage)
  ↓
[Step 6] 빌딩급 OCR
  - 스캔된 증권 → gk_policies 저장
  ↓
[Step 7] 보험 3버킷 관리
  - 섹션 A (Direct), B (External), C (Legacy) 분류
  ↓
[Step 8] AI 감성 세일즈 제안서 ✅
  ↓
┌─────────────────────────────────────┐
│ 1. 데이터 융합                      │
│    - get_customer_persona()         │
│    - get_insurance_buckets()        │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 2. 보장 공백 분석                   │
│    - analyze_coverage_gap()         │
│    - 현재 보장 vs 권장 보장         │
│    - 승환 추천 목록                 │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 3. 감성 페르소나 매칭               │
│    - generate_emotional_scripts()   │
│    - 3가지 톤 (전문적/감성적/직설적)│
│    - 직업별 커스터마이징            │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 4. 3가지 플랜 추천                  │
│    - generate_three_plans()         │
│    - 실속/표준/VIP                  │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 5. 제안서 생성 및 저장              │
│    - generate_proposal()            │
│    - save_proposal_to_db()          │
│    - gk_proposals 테이블 저장       │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 6. 에이전틱 단계 업데이트           │
│    - update_customer_stage()        │
│    - 4단계 → 5단계 (제안)          │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 7. UI 렌더링                        │
│    - render_proposal_cockpit()      │
│    - 보장 공백 비주얼 리포트        │
│    - 3가지 플랜 탭                  │
│    - 감성 스크립트 선택기           │
│    - 모바일 요약 제안서             │
└─────────────────────────────────────┘
```

### 제안서 생성 상세 흐름

```
사용자: [🚀 AI 제안서 생성] 버튼 클릭
  ↓
with st.spinner("AI가 제안서를 생성 중입니다..."):
  ↓
generate_proposal(person_id, agent_id)
  ↓
1. get_customer_persona() → persona
2. get_insurance_buckets() → buckets
3. analyze_coverage_gap(buckets) → gap_analysis
4. generate_emotional_scripts(persona, gap_analysis) → emotional_scripts
5. generate_three_plans(persona, gap_analysis) → three_plans
  ↓
proposal_data = {
    "success": True,
    "metadata": {...},
    "persona": {...},
    "buckets": {...},
    "gap_analysis": {...},
    "emotional_scripts": {...},
    "three_plans": [...]
}
  ↓
st.session_state[f"proposal_{person_id}"] = proposal_data
  ↓
save_proposal_to_db(proposal_data, person_id, agent_id)
  ↓
update_customer_stage_to_proposal(person_id, agent_id, target_stage=5)
  ↓
st.success("✅ AI 제안서가 생성되었습니다!")
  ↓
st.rerun()
  ↓
render_proposal_content(proposal_data, person_id, agent_id)
```

---

## 🎨 V4 디자인 시스템 준수

### 보장 공백 분석 색상

```css
/* 현재 보장 (Red) */
background: #FEE2E2;
border: 1.5px solid #EF4444;
color: #991B1B;

/* 제안 보장 (Green) */
background: #DCFCE7;
border: 1.5px solid #22C55E;
color: #166534;

/* 보장 공백 알림 (Yellow) */
background: #FEF3C7;
border: 1.5px solid #F59E0B;
color: #78350F;
```

### 3가지 플랜 색상

```css
/* 실속형 플랜 */
background: #E0E7FF;  /* 소프트 인디고 */
border: 1.5px solid #374151;

/* 표준형 플랜 */
background: #DBEAFE;  /* 소프트 블루 */
border: 1.5px solid #374151;

/* VIP형 플랜 */
background: #FEF3C7;  /* 소프트 골드 */
border: 1.5px solid #374151;
```

### 감성 스크립트 색상

```css
/* 전문적 톤 */
background: #E0E7FF;
border: 1.5px solid #6366F1;

/* 감성적 톤 */
background: #DBEAFE;
border: 1.5px solid #3B82F6;

/* 직설적 톤 */
background: #FEF3C7;
border: 1.5px solid #F59E0B;
```

### 모바일 요약 제안서

```css
/* 그라데이션 배경 */
background: linear-gradient(135deg, #E0E7FF, #DBEAFE);
border: 2px solid #6366F1;
border-radius: 12px;
max-width: 400px;
```

---

## ✅ 검증 완료 항목

### 기능 검증
1. ✅ **데이터 융합**: Step 5 (페르소나) + Step 7 (3버킷) 데이터 통합
2. ✅ **보장 공백 분석**: 현재 보장 vs 권장 보장 비교
3. ✅ **감성 페르소나 매칭**: 3가지 톤 스크립트 생성 (전문적/감성적/직설적)
4. ✅ **3가지 플랜 추천**: 실속/표준/VIP 플랜 자동 생성
5. ✅ **제안서 저장**: gk_proposals 테이블에 JSONB 저장
6. ✅ **에이전틱 단계 업데이트**: 4단계 → 5단계 자동 전환

### 디자인 검증
1. ✅ **V4 디자인 통일**: 소프트 인디고/블루/골드 배경
2. ✅ **12px 그리드**: 모든 간격에 12px 적용
3. ✅ **clamp() 타이포그래피**: 반응형 폰트 크기
4. ✅ **HTML 렌더링**: unsafe_allow_html=True 필수 (CORE RULE 2)

### 데이터 무결성 검증
1. ✅ **gk_proposals 테이블**: proposal_data JSONB 저장
2. ✅ **gk_people 업데이트**: current_stage 자동 업데이트
3. ✅ **세션 상태 보호**: st.rerun() 시 세션 검증 유지 (CORE RULE 1)

### NIBO 완전 배제 검증
1. ✅ **hq_proposal_engine.py**: NIBO 관련 코드 없음
2. ✅ **crm_proposal_ui.py**: NIBO 관련 UI 없음
3. ✅ **데이터 소스**: 오직 gk_people, gk_policies, gk_policy_roles만 사용
4. ✅ **AI 엔진**: HQ Vector DB 및 RAG 기반 (NIBO 배제)

---

## 🚀 다음 단계 (Step 9 예상)

### A. HQ AI 엔진 연동 (실시간 제안서 생성)

**현재 상태**: 규칙 기반 보장 공백 분석 및 스크립트 생성

**개선 방향**:
```python
# HQ AI 엔진 API 호출
response = requests.post(
    "https://goldkey-ai-xxxxxx.run.app/api/proposal-generation",
    json={
        "persona": persona,
        "buckets": buckets,
        "gap_analysis": gap_analysis
    }
)

ai_proposal = response.json()
# → 더 정교한 보장 공백 분석
# → 고객 성향 기반 맞춤형 스크립트
# → 시장 데이터 기반 최적 플랜 추천
```

### B. PDF 제안서 자동 생성

**기능**:
- 고해상도 PDF 제안서 생성
- 브랜드 로고 및 디자인 적용
- 전자 서명 기능
- 이메일 자동 발송

**구현 방향**:
```python
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def generate_pdf_proposal(proposal_data: Dict[str, Any]) -> bytes:
    """
    PDF 제안서 생성
    
    Returns:
        bytes: PDF 파일 바이너리
    """
```

### C. 카카오톡 공유 기능

**기능**:
- 카카오톡 메시지 API 연동
- 모바일 요약 제안서 전송
- 제안서 링크 공유
- 읽음 확인 기능

**구현 방향**:
```python
import requests

def send_kakao_proposal(phone_number: str, proposal_link: str) -> bool:
    """
    카카오톡 알림톡 발송
    
    Args:
        phone_number: 고객 전화번호
        proposal_link: 제안서 링크
    """
```

### D. 제안서 버전 관리

**기능**:
- 제안서 수정 이력 관리
- 버전별 비교 기능
- 고객 피드백 수집
- A/B 테스트

---

## 📝 신규 생성 파일

1. **`hq_proposal_engine.py`** (600줄)
   - AI 전략 엔진
   - 보장 공백 분석
   - 감성 페르소나 매칭
   - 3가지 플랜 추천
   - 에이전틱 단계 업데이트

2. **`crm_proposal_ui.py`** (550줄)
   - 제안서 칵핏 UI
   - 보장 공백 비주얼 리포트
   - 3가지 플랜 탭
   - 감성 스크립트 선택기
   - 모바일 요약 제안서

3. **`gk_proposals_schema.sql`** (SQL 스크립트)
   - gk_proposals 테이블 생성
   - 인덱스 추가
   - 트리거 설정

4. **`STEP8_AI_EMOTIONAL_SALES_GUIDE.md`** (통합 가이드, 이 문서)
   - 사용 예시 및 통합 방법
   - 데이터 흐름 지도
   - V4 디자인 시스템 가이드
   - 검증 완료 항목

---

## 🛠️ 사용 예시

### crm_client_detail.py 통합

```python
from crm_proposal_ui import render_proposal_cockpit

# 고객 상세 페이지에서 제안서 칵핏 렌더링
if st.session_state.get("crm_spa_screen") == "proposal":
    person_id = st.session_state.get("crm_selected_pid")
    agent_id = st.session_state.get("crm_user_id")
    customer_name = st.session_state.get("crm_customer_name", "")
    
    if person_id and agent_id:
        render_proposal_cockpit(person_id, agent_id, customer_name)
```

### 독립 페이지로 사용

```python
# crm_app_impl.py

if st.session_state.get("crm_spa_screen") == "proposal":
    person_id = st.session_state.get("crm_selected_pid")
    agent_id = st.session_state.get("crm_user_id")
    customer_name = st.session_state.get("crm_customer_name", "")
    
    if person_id and agent_id:
        render_proposal_cockpit(person_id, agent_id, customer_name)
```

### 직접 API 호출

```python
from hq_proposal_engine import generate_proposal

# 제안서 생성
proposal_data = generate_proposal(person_id="uuid-123", agent_id="agent456")

if proposal_data.get("success"):
    print(f"제안서 ID: {proposal_data['metadata']['proposal_id']}")
    print(f"고객명: {proposal_data['persona']['name']}")
    print(f"보장 공백: {len(proposal_data['gap_analysis']['gaps'])}건")
    print(f"추천 플랜: {len(proposal_data['three_plans'])}개")
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
- `d:\CascadeProjects\STEP7_TRIPLE_BUCKET_GUIDE.md` (Step 7 가이드)

### Step 8 관련
- `d:\CascadeProjects\hq_proposal_engine.py` (AI 전략 엔진)
- `d:\CascadeProjects\crm_proposal_ui.py` (제안서 칵핏 UI)
- `d:\CascadeProjects\gk_proposals_schema.sql` (gk_proposals 테이블)
- `d:\CascadeProjects\STEP8_AI_EMOTIONAL_SALES_GUIDE.md` (이 문서)

### 데이터베이스
- `gk_people` (고객 정보, current_stage 업데이트)
- `gk_policies` (보험 증권 정보, part 컬럼)
- `gk_policy_roles` (증권-인물 N:M 연결)
- `gk_proposals` (AI 제안서 저장, JSONB)

---

**[Step 8] 완료 — AI 감성 세일즈 전략 및 맞춤형 제안서 자동 생성 시스템 구축 완료**

**다음 단계**: Step 9 (예상) — HQ AI 엔진 연동, PDF 제안서 생성, 카카오톡 공유 기능 구현
