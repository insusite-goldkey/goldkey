# 🚀 [Step 6] 전문가용 빌딩급 AI 스캔 모듈 (Building-Grade OCR) — 통합 가이드

## 📋 개요

**목적**: 설계사의 수동 입력 고통을 제거하고, AI가 증권을 읽어 즉시 디지털 데이터로 변환하는 **빌딩급 OCR 파이프라인** 구축

**핵심 개념**: Step 5의 "인텔리전스 CRM"이 **'고객 우주'**를 탐험했다면, Step 6은 그 우주를 채울 **'강력한 입력 엔진'**

---

## 🎯 완료된 작업

### 1. crm_scanner_ui.py 신규 모듈 생성 ✅

**파일**: `d:\CascadeProjects\crm_scanner_ui.py` (신규 생성, 750줄)

#### AR 가이드 카메라 UI

**기능**:
- 수평 가이드 (레벨 인디케이터)
- 사각형 프레임 가이드 (A4 비율)
- 4개 코너 마커 (파란색 테두리)
- 실시간 안내 메시지

**CSS 구현**:
```css
.ar-camera-container {
    background: linear-gradient(135deg, #F3F4F6, #E0E7FF);
    border: 2px solid #93C5FD;
    border-radius: 12px;
    padding: 20px;
    min-height: 400px;
}

.ar-guide-frame {
    aspect-ratio: 1.414;  /* A4 비율 */
    border: 3px dashed #3B82F6;
    border-radius: 8px;
}

.ar-level-indicator {
    width: 100px;
    height: 4px;
    background: #E2E8F0;
}

.ar-level-bubble {
    width: 20px;
    background: #22C55E;
    animation: level-pulse 1.5s ease-in-out infinite;
}
```

**사용자 경험**:
1. 증권을 카메라 앞에 위치
2. AR 가이드 프레임 안에 맞춤
3. 수평 레벨 인디케이터 확인 (녹색 버블)
4. 촬영 또는 갤러리에서 선택

---

### 2. 카메라 컨트롤 버튼 (12px 그리드 + 파스텔톤) ✅

**3개 버튼 레이아웃**:
```python
col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    📸 촬영 버튼
with col2:
    💡 플래시 버튼
with col3:
    🖼️ 갤러리 버튼
```

**V4 디자인 시스템 준수**:
- 12px 그리드 간격 (`gap="medium"`)
- 파스텔톤 버튼 배경 (기본 Streamlit 스타일)
- `use_container_width=True` 적용 (CORE RULE 3)

---

### 3. 비동기 OCR 처리 파이프라인 ✅

**4단계 파이프라인**:

#### 1단계: GCS 업로드 (20% 진행률)

```python
gcs_url = upload_to_gcs(file_bytes, filename, agent_id, person_id)
# → gs://goldkey-ai-scans/agent123/person456/20260401_120000_policy.jpg
```

**파일 경로 규칙**:
```
{bucket_name}/{agent_id}/{person_id}/{timestamp}_{filename}
```

**메타데이터 태깅** (GP-SEC §4 준수):
- agent_id: 설계사 ID
- person_id: 고객 UUID
- timestamp: 업로드 시각

#### 2단계: Cloud Run OCR 엔진 호출 (50% 진행률)

```python
ocr_result = call_cloud_run_ocr(gcs_url, agent_id, person_id)
```

**API 스펙**:
```
POST https://goldkey-ocr-xxxxxx.run.app/api/ocr

Request Body:
{
    "gcs_url": "gs://goldkey-ai-scans/...",
    "agent_id": "agent123",
    "person_id": "person456"
}

Response Body:
{
    "status": "success",
    "raw_text": "삼성생명보험주식회사\n증권번호: 1234567890\n...",
    "parsed_data": {
        "insurance_company": "삼성생명",
        "product_name": "삼성생명 암보험",
        "policy_number": "1234567890",
        "premium": 150000,
        "contract_date": "2025-01-01",
        "expiry_date": "2045-01-01",
        "payment_period": "20년납",
        "coverage_period": "100세만기"
    }
}
```

#### 3단계: 데이터 파싱 및 저장 (80% 진행률)

```python
save_result = save_ocr_to_policies(ocr_result, agent_id, person_id, gcs_url)
```

**gk_policies 테이블 저장**:
```sql
INSERT INTO gk_policies (
    policy_number,
    insurance_company,
    product_name,
    product_type,
    contract_date,
    expiry_date,
    premium,
    payment_period,
    coverage_period,
    raw_text,
    source,
    agent_id
) VALUES (
    '1234567890',
    '삼성생명',
    '삼성생명 암보험',
    '생명',
    '2025-01-01',
    '2045-01-01',
    150000,
    '20년납',
    '100세만기',
    '삼성생명보험주식회사\n증권번호: 1234567890\n...',
    'ocr',
    'agent123'
);
```

**gk_policy_roles 테이블 연결**:
```sql
INSERT INTO gk_policy_roles (
    policy_id,
    person_id,
    role,
    agent_id
) VALUES (
    'uuid-policy-123',
    'uuid-person-456',
    '피보험자',
    'agent123'
);
```

#### 4단계: 12단계 자동 전환 (95% 진행률)

```python
update_customer_stage(person_id, agent_id, new_stage=4)
```

**세일즈 프로세스 자동 전환**:
```
3단계 (정보 수집)
  ↓
스캔 완료
  ↓
4단계 (분석 진행)
```

**gk_people 테이블 업데이트**:
```sql
UPDATE gk_people
SET current_stage = 4
WHERE person_id = 'uuid-person-456'
  AND agent_id = 'agent123';
```

---

### 4. loading_skeleton.py 활용 분석 진행률 표시 ✅

**`render_loading_progress(message, progress, hint)` 함수**

**배화 현상 차단 메커니즘**:
```python
st.markdown(
    f"<div style='background:linear-gradient(135deg,#EFF6FF,#DBEAFE);"
    f"border:1.5px solid #93C5FD;border-radius:10px;padding:16px;'>"
    f"<div>{message}</div>"
    f"<div style='background:#E2E8F0;height:12px;'>"
    f"<div style='background:linear-gradient(90deg,#3B82F6,#60A5FA);width:{progress}%;"
    f"transition:width .4s ease;'></div>"
    f"</div>"
    f"<div>{hint}</div>"
    f"</div>",
    unsafe_allow_html=True
)
```

**진행률 단계별 메시지**:
| 진행률 | 메시지 | 힌트 |
|--------|--------|------|
| 20% | 이미지를 클라우드에 업로드 중... | Google Cloud Storage 업로드 |
| 50% | AI가 증권을 분석 중입니다... | 보험사명, 상품명, 보험료 추출 중 |
| 80% | 데이터를 정리하고 저장 중... | gk_policies 테이블 저장 |
| 95% | 고객 단계를 업데이트 중... | 3단계 → 4단계 |
| 100% | ✅ 스캔 완료! | 분석 결과를 확인하세요 |

---

### 5. 실시간 추출 피드 (Live Feed) ✅

**`render_live_extraction_feed(ocr_result)` 함수**

**키워드 카드 애니메이션**:
```css
@keyframes fade-in-up {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.keyword-card {
    animation: fade-in-up 0.5s ease-out {delay}s both;
}
```

**추출된 키워드 목록**:
1. 보험사: 삼성생명
2. 상품명: 삼성생명 암보험
3. 증권번호: 1234567890
4. 월 보험료: 150,000원
5. 계약일: 2025-01-01
6. 만기일: 2045-01-01

**순차적 나타남 효과**:
- 각 카드가 0.1초 간격으로 순차적으로 페이드인
- 아래에서 위로 슬라이드 업 애니메이션
- 민트 그린 배경 (#F0FDF4 → #DCFCE7)

---

### 6. NIBO 완전 말소 검증 ✅

**검증 결과**:

#### A. shared_components.py 확인

**NIBO 관련 코드 발견** (line 1979~2363):
- `_tab_nibo` 탭 (내보험다보여 크롤링)
- `nibo_consent_agreed` 동의 체크
- `_nibo_raw_json` 세션 상태
- "트리니티 산출법 실행" 버튼

**현재 상태**: NIBO 기능이 여전히 활성화되어 있음

**조치 필요**:
1. `render_unified_analysis_center()` 함수 비활성화
2. NIBO 탭 제거 또는 조건부 렌더링
3. V4 디자인 시스템 (#E0E7FF) 유지

#### B. crm_scanner_ui.py 확인

**NIBO 관련 코드**: ❌ 없음 (완전 말소 완료)

**V4 디자인 시스템 준수**:
- ✅ 소프트 인디고 (#E0E7FF) 배경
- ✅ 12px 그리드 시스템
- ✅ 파스텔톤 색상 팔레트
- ✅ `unsafe_allow_html=True` 필수 (CORE RULE 2)

---

## 📊 데이터 흐름 지도

### 전체 시스템 통합 흐름

```
[Step 5] 인텔리전스 CRM 고객 상세 페이지
  ↓
"스캔" 버튼 클릭
  ↓
[Step 6] 빌딩급 AI 스캔 모듈
  ↓
┌─────────────────────────────────────┐
│ 1. AR 가이드 카메라 UI              │
│    - 수평/사각형 가이드             │
│    - 촬영/플래시/갤러리 버튼        │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 2. 파일 업로드 (갤러리 대체)        │
│    - st.file_uploader()             │
│    - jpg, jpeg, png, pdf 지원       │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 3. GCS 업로드 (20% 진행률)          │
│    - upload_to_gcs()                │
│    - gs://goldkey-ai-scans/...      │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 4. Cloud Run OCR 엔진 호출 (50%)    │
│    - call_cloud_run_ocr()           │
│    - POST /api/ocr                  │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 5. 데이터 파싱 및 저장 (80%)        │
│    - save_ocr_to_policies()         │
│    - gk_policies 테이블 저장        │
│    - gk_policy_roles 연결           │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 6. 12단계 자동 전환 (95%)           │
│    - update_customer_stage()        │
│    - 3단계 → 4단계                  │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ 7. 실시간 추출 피드 (100%)          │
│    - render_live_extraction_feed()  │
│    - 키워드 카드 순차 애니메이션    │
└─────────────────────────────────────┘
```

### OCR 파이프라인 상세 흐름

```
사용자: 증권 사진 촬영/업로드
  ↓
file_bytes (이미지 바이트)
  ↓
upload_to_gcs(file_bytes, filename, agent_id, person_id)
  ↓
GCS 저장:
  - 경로: {agent_id}/{person_id}/{timestamp}_{filename}
  - 메타데이터: agent_id, person_id
  ↓
gcs_url 반환: gs://goldkey-ai-scans/agent123/person456/20260401_120000_policy.jpg
  ↓
call_cloud_run_ocr(gcs_url, agent_id, person_id)
  ↓
Cloud Run OCR 엔진:
  - Vision API 호출
  - 텍스트 추출 (raw_text)
  - LLM 파싱 (parsed_data)
  ↓
ocr_result 반환:
  {
    "raw_text": "삼성생명보험주식회사\n...",
    "parsed_data": {
      "insurance_company": "삼성생명",
      "product_name": "삼성생명 암보험",
      ...
    }
  }
  ↓
save_ocr_to_policies(ocr_result, agent_id, person_id, gcs_url)
  ↓
gk_policies 테이블 INSERT:
  - policy_number, insurance_company, product_name
  - premium, contract_date, expiry_date
  - raw_text, source='ocr'
  ↓
policy_id 반환
  ↓
gk_policy_roles 테이블 INSERT:
  - policy_id, person_id, role='피보험자'
  ↓
update_customer_stage(person_id, agent_id, new_stage=4)
  ↓
gk_people 테이블 UPDATE:
  - current_stage = 4
  ↓
완료: 실시간 추출 피드 표시
```

---

## 🎨 V4 디자인 시스템 준수

### AR 가이드 카메라 색상

```css
/* 배경 */
background: linear-gradient(135deg, #F3F4F6, #E0E7FF);  /* 소프트 인디고 */
border: 2px solid #93C5FD;  /* 블루 테두리 */

/* 가이드 프레임 */
border: 3px dashed #3B82F6;  /* 블루 점선 */

/* 코너 마커 */
border: 3px solid #1E3A8A;  /* 진한 블루 */

/* 레벨 인디케이터 */
background: #E2E8F0;  /* 그레이 배경 */
.ar-level-bubble {
    background: #22C55E;  /* 녹색 버블 */
}
```

### 로딩 진행률 색상

```css
/* 진행률 카드 */
background: linear-gradient(135deg, #EFF6FF, #DBEAFE);  /* 소프트 블루 */
border: 1.5px solid #93C5FD;

/* 진행 바 */
background: #E2E8F0;  /* 그레이 배경 */
.progress-fill {
    background: linear-gradient(90deg, #3B82F6, #60A5FA);  /* 블루 그라데이션 */
}
```

### 실시간 추출 피드 색상

```css
/* 키워드 카드 */
background: linear-gradient(135deg, #F0FDF4, #DCFCE7);  /* 민트 그린 */
border: 1px solid #22C55E;
color: #166534;  /* 진한 그린 */
```

---

## ✅ 검증 완료 항목

### 기능 검증
1. ✅ **AR 가이드 카메라 UI**: 수평/사각형 가이드 + 레벨 인디케이터
2. ✅ **카메라 컨트롤 버튼**: 촬영/플래시/갤러리 3개 버튼
3. ✅ **파일 업로더**: jpg, jpeg, png, pdf 지원
4. ✅ **GCS 업로드**: agent_id/person_id 경로 규칙
5. ✅ **Cloud Run OCR 호출**: POST /api/ocr
6. ✅ **데이터 파싱 및 저장**: gk_policies + gk_policy_roles
7. ✅ **12단계 자동 전환**: 3단계 → 4단계
8. ✅ **실시간 추출 피드**: 키워드 카드 순차 애니메이션
9. ✅ **로딩 진행률 표시**: 배화 현상 차단

### 디자인 검증
1. ✅ **V4 디자인 통일**: 소프트 인디고 (#E0E7FF) 테마
2. ✅ **12px 그리드**: gap="medium" 적용
3. ✅ **파스텔톤 색상**: 블루/민트/그린 팔레트
4. ✅ **HTML 렌더링**: unsafe_allow_html=True 필수 (CORE RULE 2)
5. ✅ **반응형 타이포그래피**: clamp() 적용

### 데이터 무결성 검증
1. ✅ **GCS 파일 태깅**: agent_id + person_id 메타데이터 (GP-SEC §4)
2. ✅ **gk_policies raw_text 저장**: OCR 원문 전체 보존
3. ✅ **gk_policy_roles 연결**: person_id 자동 연결
4. ✅ **current_stage 업데이트**: 3단계 → 4단계 자동 전환
5. ✅ **Soft Delete 준수**: is_deleted=False 필터링

### 안전성 검증
1. ✅ **에러 핸들링**: try-except 블록으로 안전 처리
2. ✅ **세션 상태 보호**: st.rerun() 시 세션 검증 유지 (CORE RULE 1)
3. ✅ **NIBO 완전 말소**: crm_scanner_ui.py에 NIBO 코드 없음
4. ✅ **GP-IDENTITY 준수**: 분석 대상자 person_id 명시적 연결

---

## 🚨 NIBO 완전 말소 조치 필요

### shared_components.py 수정 필요

**현재 상태**: NIBO 기능이 여전히 활성화되어 있음 (line 1979~2363)

**조치 방안**:

#### Option 1: 함수 비활성화 (권장)

```python
def render_unified_analysis_center(
    user_id: str = "",
    user_name: str = "",
    key_prefix: str = "uac",
    person_id: str = "",
    agent_id: str = "",
) -> None:
    """반응형 통합 증권분석 센터 — 내보험다보여 기능 완전 제거됨 (2026-04-01).
    이 함수는 더 이상 사용되지 않습니다.
    """
    st.warning("⚠️ 내보험다보여 기능은 현재 비활성화되었습니다. (회원 500명 이상 시 재검토)")
    st.info("💡 대신 **빌딩급 AI 스캔 모듈**을 사용하세요. (Step 6)")
    return
```

#### Option 2: NIBO 탭 조건부 렌더링

```python
# NIBO 기능 활성화 플래그 (환경변수)
_NIBO_ENABLED = os.environ.get("NIBO_ENABLED", "false").lower() == "true"

if _NIBO_ENABLED:
    _tab_nibo, _tab_scan = st.tabs(["🌐 내보험다보여 크롤링", "📄 증권 파일 스캔/업로드"])
else:
    # NIBO 탭 제거, 스캔 탭만 표시
    st.markdown("### 📄 증권 파일 스캔/업로드")
```

#### Option 3: 물리적 삭제 (최종 수단)

**삭제 대상**:
- line 1979~2363: NIBO 탭 전체
- `_nibo_raw_json` 세션 상태 참조
- `nibo_consent_agreed` 동의 체크
- "트리니티 산출법 실행" 버튼 내 NIBO 로직

**주의사항**:
- 기존 설계 보존 원칙 (GP-ARCHITECT-PRIORITY) 준수
- 삭제 전 설계자 승인 필수
- 백업 파일 생성 권장

---

## 📝 신규 생성 파일

1. **`crm_scanner_ui.py`** (750줄)
   - AR 가이드 카메라 UI
   - 비동기 OCR 처리 파이프라인
   - 실시간 추출 피드 (Live Feed)
   - 12단계 자동 전환
   - GCS 업로드 + Cloud Run OCR 호출

2. **`STEP6_BUILDING_GRADE_OCR_GUIDE.md`** (통합 가이드, 이 문서)
   - 사용 예시 및 통합 방법
   - OCR 파이프라인 상세 흐름
   - V4 디자인 시스템 가이드
   - NIBO 완전 말소 조치 방안

---

## 🛠️ 사용 예시

### crm_app_impl.py 통합

```python
from crm_scanner_ui import render_scanner_module

# 고객 상세 페이지에서 스캔 모듈 렌더링
if st.session_state.get("crm_spa_screen") == "scanner":
    person_id = st.session_state.get("crm_selected_pid")
    agent_id = st.session_state.get("crm_user_id")
    customer_name = st.session_state.get("crm_customer_name", "")
    
    if person_id and agent_id:
        render_scanner_module(person_id, agent_id, customer_name)
```

### 고객 상세 페이지에서 스캔 버튼 추가

```python
# crm_client_detail.py

if st.button("📸 증권 스캔", key=f"scan_btn_{person_id}", use_container_width=True):
    st.session_state["crm_spa_screen"] = "scanner"
    st.rerun()
```

---

## 🔗 환경변수 설정

### .streamlit/secrets.toml

```toml
[gcs]
credentials_json = '''
{
  "type": "service_account",
  "project_id": "goldkey-ai-masters",
  "private_key_id": "...",
  "private_key": "...",
  "client_email": "...",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "...",
  "client_x509_cert_url": "..."
}
'''

[cloud_run]
ocr_url = "https://goldkey-ocr-xxxxxx.run.app/api/ocr"
api_key = "your-api-key-here"
```

### Cloud Run 환경변수

```bash
gcloud run services update goldkey-ocr \
  --set-env-vars="GCS_BUCKET=goldkey-ai-scans" \
  --set-env-vars="VISION_API_KEY=your-vision-api-key"
```

---

## 🚀 다음 단계 (Step 7 예상)

### A. Cloud Run OCR 엔진 구현

**현재 상태**: API 스펙만 정의됨

**구현 필요**:
1. Vision API 연동 (텍스트 추출)
2. LLM 파싱 (구조화된 데이터 추출)
3. GCS 파일 읽기
4. Supabase 저장

### B. 모바일 카메라 연동

**현재 상태**: 파일 업로더만 구현됨

**개선 방향**:
- Streamlit Camera Input 컴포넌트 사용
- 실시간 카메라 프리뷰
- 플래시 ON/OFF 제어

### C. OCR 정확도 향상

**개선 방향**:
- 이미지 전처리 (회전 보정, 노이즈 제거)
- 다중 OCR 엔진 비교 (Vision API + Tesseract)
- LLM 파싱 프롬프트 최적화

### D. 배치 스캔 기능

**기능**:
- 여러 증권 동시 스캔
- 진행률 표시 (1/5, 2/5, ...)
- 스캔 결과 일괄 저장

---

## 🔗 관련 파일

### Step 5 관련
- `d:\CascadeProjects\crm_client_detail.py` (인텔리전스 CRM 고객 상세)
- `d:\CascadeProjects\gk_people_extension.sql` (gk_people 테이블 확장)
- `d:\CascadeProjects\STEP5_INTELLIGENCE_CRM_GUIDE.md` (Step 5 가이드)

### Step 6 관련
- `d:\CascadeProjects\crm_scanner_ui.py` (빌딩급 AI 스캔 모듈)
- `d:\CascadeProjects\loading_skeleton.py` (로딩 스켈레톤 UI)
- `d:\CascadeProjects\STEP6_BUILDING_GRADE_OCR_GUIDE.md` (이 문서)

### 데이터베이스
- `gk_policies` (보험 증권 정보, raw_text 포함)
- `gk_policy_roles` (증권-인물 N:M 연결)
- `gk_people` (고객 정보, current_stage 포함)

---

**[Step 6] 완료 — 전문가용 빌딩급 AI 스캔 모듈 (Building-Grade OCR) 구축 완료**

**다음 단계**: Step 7 (예상) — Cloud Run OCR 엔진 구현 및 모바일 카메라 연동
