# 이달의 상품 섹터 통합 가이드

**작성일**: 2026-03-31  
**목적**: 보험 리플릿 자동 처리 및 프론트엔드 MonthlyProductSector 구현

---

## 🎯 시스템 개요

### 핵심 기능
1. **백엔드 자동화**: 보험사 리플릿 폴더 자동 생성 + SHA-256 중복 방지
2. **LLM 추출**: 이달의 핵심 판매포인트 자동 추출
3. **프론트엔드 UI**: 파스텔톤 박스 + 검은 테두리 + 구분선

### 데이터 흐름
```
[리플릿 업로드]
    ↓
[폴더 자동 생성] (보험사 리플릿_{YYYY}년_{MM}월_{보험사명})
    ↓
[SHA-256 해시 검증] (중복 방지)
    ↓
[PDF 텍스트 추출] (보안 필터 적용)
    ↓
[LLM 마케팅 포인트 추출] (GPT-4)
    ↓
[Supabase 저장] (insurance_marketing_points)
    ↓
[프론트엔드 표시] (MonthlyProductSector)
```

---

## 📂 생성된 파일 목록

### 백엔드 서비스
1. `hq_backend/utils/folder_manager.py` - 폴더 자동 생성 (수정됨)
2. `hq_backend/services/document_hash_validator.py` - SHA-256 중복 검증
3. `hq_backend/services/marketing_point_extractor.py` - LLM 마케팅 포인트 추출

### API
4. `hq_backend/api/monthly_product_api.py` - 이달의 상품 API

### 데이터베이스 스키마
5. `hq_backend/knowledge_base/schema/document_hashes.sql` - 문서 해시 테이블
6. `hq_backend/knowledge_base/schema/insurance_marketing_points.sql` - 마케팅 포인트 테이블
7. `hq_backend/knowledge_base/schema/leaflet_processing_logs.sql` - 처리 로그 테이블

### 프론트엔드
8. `blocks/monthly_product_sector_block.py` - MonthlyProductSector 컴포넌트

### 문서
9. `MONTHLY_PRODUCT_SECTOR_INTEGRATION_GUIDE.md` - 통합 가이드 (본 문서)

---

## 🗄️ 데이터베이스 스키마

### 1. document_hashes (문서 해시)
```sql
CREATE TABLE document_hashes (
    id BIGSERIAL PRIMARY KEY,
    file_hash TEXT NOT NULL UNIQUE,  -- SHA-256 해시
    file_name TEXT NOT NULL,
    file_path TEXT,
    company TEXT,
    reference_date TEXT,
    registered_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2. insurance_marketing_points (마케팅 포인트)
```sql
CREATE TABLE insurance_marketing_points (
    id BIGSERIAL PRIMARY KEY,
    company TEXT NOT NULL,
    company_type TEXT NOT NULL CHECK (company_type IN ('손해보험', '생명보험')),
    marketing_point TEXT NOT NULL,
    reference_year INT NOT NULL,
    reference_month INT NOT NULL,
    priority INT DEFAULT 0,
    extracted_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3. leaflet_processing_logs (처리 로그)
```sql
CREATE TABLE leaflet_processing_logs (
    id BIGSERIAL PRIMARY KEY,
    company TEXT NOT NULL,
    year INT NOT NULL,
    month INT NOT NULL,
    file_hash TEXT,
    points_extracted INT DEFAULT 0,
    status TEXT CHECK (status IN ('success', 'failed', 'duplicate')),
    processed_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 🚀 사용 방법

### 1. SQL 마이그레이션 실행
```sql
-- Supabase SQL Editor에서 순서대로 실행
\i hq_backend/knowledge_base/schema/document_hashes.sql
\i hq_backend/knowledge_base/schema/insurance_marketing_points.sql
\i hq_backend/knowledge_base/schema/leaflet_processing_logs.sql
```

### 2. 백엔드 API 실행
```bash
cd hq_backend/api
uvicorn monthly_product_api:app --reload --port 8080
```

### 3. 리플릿 업로드 (API)
```bash
curl -X POST http://localhost:8080/monthly-product/process-leaflet \
  -F "file=@삼성생명_2026년03월_리플릿.pdf" \
  -F "company=삼성생명" \
  -F "year=2026" \
  -F "month=3"
```

**응답**:
```json
{
  "status": "accepted",
  "message": "리플릿 처리가 백그라운드에서 시작되었습니다.",
  "company": "삼성생명",
  "year": 2026,
  "month": 3,
  "file_name": "삼성생명_2026년03월_리플릿.pdf"
}
```

### 4. 이달의 상품 조회 (API)
```bash
curl http://localhost:8080/monthly-product/?year=2026&month=3
```

**응답**:
```json
{
  "year": 2026,
  "month": 3,
  "non_life_insurance": [
    {
      "company": "삼성화재",
      "company_type": "손해보험",
      "marketing_point": "암 진단 시 최대 5천만원 보장",
      "priority": 10
    }
  ],
  "life_insurance": [
    {
      "company": "삼성생명",
      "company_type": "생명보험",
      "marketing_point": "월 보험료 30% 할인 이벤트 (3월 한정)",
      "priority": 8
    }
  ],
  "total_count": 10
}
```

### 5. 프론트엔드 통합 (Streamlit)

#### hq_app_impl.py 또는 메인 화면에 추가
```python
from blocks.monthly_product_sector_block import render_monthly_product_sector_simple

# 메인 섹션에 추가
st.title("goldkey_Ai_masters2026")

# 이달의 상품 섹터 박스
render_monthly_product_sector_simple()

# 기존 콘텐츠...
```

---

## 🎨 UI 디자인 가이드

### 디자인 시스템
- ✅ **배경색**: #F0F4FF (밝은 파스텔 블루)
- ✅ **외곽선**: 2px solid #000000 (검은색)
- ✅ **구분선**: 1px solid #E5E7EB (연한 회색)
- ✅ **반응형**: word-wrap: break-word, max-width: 100%
- ✅ **스크롤**: max-height: 500px, overflow-y: auto

### 노출 로직
- ✅ **손해보험**: 최대 7개 우선 노출
- ✅ **생명보험**: 최대 3개 노출
- ✅ **초기 표시**: 10줄
- ✅ **추가 내용**: 내부 스크롤

### 구분선 적용
```css
.sector-item {
    padding: 12px 0;
    border-bottom: 1px solid #E5E7EB;  /* 연한 구분선 */
}

.sector-item:last-child {
    border-bottom: none;  /* 마지막 항목은 구분선 없음 */
}
```

---

## 🔧 백엔드 처리 로직

### 1. 폴더 자동 생성
```python
from hq_backend.utils.folder_manager import FolderManager

manager = FolderManager()
folder_path = manager.create_insurance_leaflet_folder(
    company_name="삼성생명",
    year=2026,
    month=3
)
# 결과: source_docs/보험사 리플릿_2026년_03월_삼성생명/
```

### 2. SHA-256 중복 검증
```python
from hq_backend.services.document_hash_validator import DocumentHashValidator

validator = DocumentHashValidator()
result = validator.validate_and_register(
    file_path="삼성생명_2026년03월_리플릿.pdf",
    company="삼성생명",
    reference_date="2026-03"
)

if result["is_duplicate"]:
    print("⚠️ 중복 문서입니다. 임베딩을 건너뜁니다.")
else:
    print("✅ 신규 문서입니다. 임베딩을 진행합니다.")
```

### 3. LLM 마케팅 포인트 추출
```python
from hq_backend.services.marketing_point_extractor import MarketingPointExtractor

extractor = MarketingPointExtractor()
result = extractor.process_leaflet(
    text=leaflet_text,
    company="삼성생명",
    year=2026,
    month=3,
    max_points=3
)

if result["success"]:
    print(f"✅ 추출 완료: {result['points']}")
    # ['암 진단 시 최대 5천만원 보장', '월 보험료 30% 할인', ...]
```

---

## 📊 처리 프로세스 (4단계)

### STEP 1: 중복 검증
```
🔒 [1/4] 중복 검증 중...
✅ 신규 문서 등록: 삼성생명_2026년03월_리플릿.pdf
```

### STEP 2: PDF 텍스트 추출
```
📄 [2/4] PDF 텍스트 추출 중...
🔒 보안 필터: 5개 PII 감지 및 마스킹 완료
✅ 텍스트 추출 완료: 15,234자
```

### STEP 3: LLM 마케팅 포인트 추출
```
🤖 [3/4] LLM 마케팅 포인트 추출 중...
✅ 3개 포인트 추출 완료
   1. 암 진단 시 최대 5천만원 보장
   2. 월 보험료 30% 할인 이벤트 (3월 한정)
   3. 가입 즉시 건강검진 무료 쿠폰 제공
```

### STEP 4: 로그 기록
```
📝 [4/4] 로그 기록 중...
✅ 로그 기록 완료

🎉 리플릿 처리 완료
```

---

## 🧪 테스트 실행

### 1. 폴더 관리자 테스트
```bash
python hq_backend/utils/folder_manager.py
```

### 2. 문서 해시 검증 테스트
```bash
python hq_backend/services/document_hash_validator.py
```

### 3. 마케팅 포인트 추출 테스트
```bash
python hq_backend/services/marketing_point_extractor.py
```

### 4. MonthlyProductSector 컴포넌트 테스트
```bash
streamlit run blocks/monthly_product_sector_block.py
```

---

## ⚠️ 무결성 원칙 검증

### 1. 데이터 중복 방지 ✅
- SHA-256 해시로 동일 파일 자동 감지
- document_hashes 테이블에 UNIQUE 제약
- 중복 시 임베딩 건너뜀

### 2. 벡터 DB 오염 방지 ✅
- 중복 문서는 gk_knowledge_base에 저장되지 않음
- 파일 해시 검증 → 통과 시에만 임베딩 진행

### 3. 보안 필터 적용 ✅
- PDF 텍스트 추출 후 즉시 PII 마스킹
- 개인정보 보호법 준수

### 4. 로그 기록 ✅
- 모든 처리 이력을 leaflet_processing_logs에 기록
- 성공/실패/중복 상태 추적

---

## 📈 프론트엔드 렌더링 예시

### 화면 구성
```
┌─────────────────────────────────────────────────────┐
│  📊 이달의 상품 (2026년 3월)                          │
├─────────────────────────────────────────────────────┤
│  삼성화재 [손해보험]                                  │
│    암 진단 시 최대 5천만원 보장                       │
├─────────────────────────────────────────────────────┤  ← 연한 구분선
│  현대해상 [손해보험]                                  │
│    자동차보험 30% 할인 (3월 한정)                     │
├─────────────────────────────────────────────────────┤
│  DB손해보험 [손해보험]                                │
│    실손의료비 최대 5천만원 보장                       │
├─────────────────────────────────────────────────────┤
│  ...                                                 │
├─────────────────────────────────────────────────────┤
│  삼성생명 [생명보험]                                  │
│    월 보험료 30% 할인 이벤트 (3월 한정)               │
├─────────────────────────────────────────────────────┤
│  손해보험 7개 · 생명보험 3개 · 총 10개 포인트         │
└─────────────────────────────────────────────────────┘
```

### CSS 적용 확인
- ✅ 배경색: #F0F4FF (파스텔 블루)
- ✅ 외곽선: 2px solid #000000 (검은색)
- ✅ 구분선: 1px solid #E5E7EB (연한 회색)
- ✅ 스크롤: max-height: 500px
- ✅ 반응형: word-wrap, max-width

---

## 🔗 관련 문서

- `hq_backend/knowledge_base/README_FOLDER_STRUCTURE.md` - 폴더 구조 가이드
- `GCS_SYNC_AND_TRIGGER_GUIDE.md` - GCS 동기화
- `QUERY_EXPANSION_INTEGRATION_GUIDE.md` - Query Expansion
- `VERSION_CONTROL_HOT_SWAP_GUIDE.md` - Version Control

---

## 💡 활용 시나리오

### 시나리오 1: 매월 초 리플릿 일괄 업로드

```bash
# 1. 3월 리플릿 폴더 생성
mkdir -p "source_docs/보험사 리플릿_2026년_03월_삼성생명"
mkdir -p "source_docs/보험사 리플릿_2026년_03월_현대해상"

# 2. PDF 파일 복사
cp 삼성생명_리플릿.pdf "source_docs/보험사 리플릿_2026년_03월_삼성생명/"
cp 현대해상_리플릿.pdf "source_docs/보험사 리플릿_2026년_03월_현대해상/"

# 3. API로 일괄 처리
for company in 삼성생명 현대해상 DB손해보험; do
    curl -X POST http://localhost:8080/monthly-product/process-leaflet \
      -F "file=@${company}_리플릿.pdf" \
      -F "company=${company}" \
      -F "year=2026" \
      -F "month=3"
done

# 4. 프론트엔드 자동 갱신
# → MonthlyProductSector가 자동으로 최신 데이터 표시
```

### 시나리오 2: 중복 업로드 방지

```python
# 동일 파일 재업로드 시
validator = DocumentHashValidator()
result = validator.validate_and_register(
    file_path="삼성생명_2026년03월_리플릿.pdf",
    company="삼성생명",
    reference_date="2026-03"
)

# 결과
{
    "is_duplicate": True,
    "file_hash": "a1b2c3d4...",
    "message": "⚠️ 중복 문서 감지: 삼성생명_2026년03월_리플릿.pdf"
}

# → 임베딩 건너뜀, 벡터 DB 오염 방지
```

---

## 🎯 최종 체크리스트

### 백엔드
- ✅ 폴더 자동 생성 (보험사 리플릿_{YYYY}년_{MM}월_{보험사명})
- ✅ SHA-256 해시 중복 검증
- ✅ LLM 마케팅 포인트 추출
- ✅ Supabase 저장 (insurance_marketing_points)
- ✅ 로그 기록 (leaflet_processing_logs)

### 프론트엔드
- ✅ 파스텔톤 배경 (#F0F4FF)
- ✅ 2px 검은 테두리
- ✅ 연한 구분선 (1px #E5E7EB)
- ✅ 손해보험 7개 우선
- ✅ 생명보험 3개
- ✅ 초기 10줄 노출
- ✅ 내부 스크롤 (overflow-y: auto)
- ✅ unsafe_allow_html=True 적용

### 무결성
- ✅ 데이터 중복 방지
- ✅ 벡터 DB 오염 방지
- ✅ 보안 필터 적용
- ✅ 로그 기록

---

**작성자**: GoldkeyAImasters2026 프로젝트 팀  
**버전**: 1.0  
**최종 업데이트**: 2026-03-31
