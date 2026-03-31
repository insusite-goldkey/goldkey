# Version Control & Hot-Swap 가이드

**작성일**: 2026-03-31  
**목적**: 구버전 카탈로그 데이터 격리 및 과거 자료 혼입 방지

---

## 🎯 핵심 개념

### Hot-Swap이란?
새로운 버전의 카탈로그가 업로드될 때, 구버전 데이터를 물리적으로 삭제하지 않고 논리적으로 격리하여 RAG 검색 대상에서 제외하는 기술

### 원칙
1. ✅ **물리적 삭제 금지** - 데이터 보존 (롤백 가능)
2. ✅ **논리적 격리** - `is_active` 플래그 사용
3. ✅ **검색 필터 강제** - `is_active=true`만 검색
4. ✅ **버전 이력 유지** - 모든 버전 추적 가능

---

## 📂 생성된 파일 목록

### 1. SQL 스키마 마이그레이션
**파일**: `hq_backend/knowledge_base/schema/add_version_control.sql`

**주요 변경사항**:
- ✅ `is_active` 컬럼 추가 (기본값: true)
- ✅ `version_date` 컬럼 추가 (버전 날짜)
- ✅ `archived_at` 컬럼 추가 (아카이브 시점)
- ✅ 인덱스 생성 (검색 성능 최적화)
- ✅ `search_knowledge_base` 함수 업데이트 (is_active 필터)
- ✅ `archive_old_versions` 함수 생성 (Hot-Swap)
- ✅ `get_version_statistics` 함수 생성
- ✅ `get_active_versions` 함수 생성

### 2. Version Control Service
**파일**: `hq_backend/services/version_control_service.py`

**핵심 기능**:
- ✅ 구버전 데이터 아카이브 (Hot-Swap)
- ✅ 활성 버전 조회
- ✅ 버전 통계 조회
- ✅ 버전 복원 (롤백)
- ✅ 보험사별 버전 관리

### 3. Chat API 업데이트
**파일**: `hq_backend/api/chat_routes.py` (수정됨)

**변경사항**:
- ✅ `search_knowledge_base` 함수에 `is_active` 필터 적용
- ✅ 보험사 및 기준연월 필터 추가

### 4. 테스트 코드
**파일**: `hq_backend/tests/test_version_control.py`

---

## 🔄 Hot-Swap 작동 원리

### 시나리오: 삼성생명 2026년 3월 카탈로그 업로드

#### STEP 1: 새 버전 업로드
```python
# 2026년 3월 카탈로그 PDF 업로드
processor = InsuranceDocumentProcessor()
chunks = processor.process_pdf("삼성생명_2026년03월_상품카탈로그.pdf")

# Supabase에 저장 (is_active=true, version_date=2026-03-31)
for chunk in chunks:
    supabase.table("gk_knowledge_base").insert({
        "content": chunk["content"],
        "company": "삼성생명",
        "reference_date": "2026-03",
        "is_active": True,
        "version_date": "2026-03-31"
    }).execute()
```

#### STEP 2: 구버전 아카이브 (Hot-Swap)
```python
from hq_backend.services.version_control_service import VersionControlService

service = VersionControlService()

# 삼성생명 2026년 3월 이전 버전을 is_active=false로 변경
result = service.archive_old_versions(
    company="삼성생명",
    reference_date="2026-03"
)

print(f"아카이브: {result.archived_count}개")
# 출력: 아카이브: 150개 (2026년 2월 버전)
```

#### STEP 3: RAG 검색 (활성 버전만)
```python
# 검색 시 is_active=true만 자동 필터링
search_results = search_knowledge_base(
    query_embedding=embedding,
    top_k=5
)

# 결과: 2026년 3월 버전만 반환
# 2026년 2월 버전은 검색되지 않음 (is_active=false)
```

---

## 🗄️ 데이터베이스 스키마

### gk_knowledge_base 테이블 (업데이트)

```sql
CREATE TABLE gk_knowledge_base (
    id BIGSERIAL PRIMARY KEY,
    document_name TEXT,
    document_category TEXT,
    chunk_index INT,
    content TEXT,
    content_length INT,
    embedding VECTOR(1536),
    company TEXT,
    reference_date TEXT,
    
    -- 버전 관리 컬럼 (신규)
    is_active BOOLEAN DEFAULT true,
    version_date DATE DEFAULT CURRENT_DATE,
    archived_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_gk_knowledge_base_is_active ON gk_knowledge_base(is_active);
CREATE INDEX idx_gk_knowledge_base_company_date_active 
    ON gk_knowledge_base(company, reference_date, is_active);
```

---

## 🚀 사용 방법

### 1. SQL 마이그레이션 실행
```bash
# Supabase SQL Editor에서 실행
psql -h your-supabase-host -U postgres -d postgres -f hq_backend/knowledge_base/schema/add_version_control.sql
```

### 2. 새 버전 업로드 후 Hot-Swap
```python
from hq_backend.services.version_control_service import VersionControlService

service = VersionControlService()

# 구버전 아카이브
result = service.archive_old_versions(
    company="삼성생명",
    reference_date="2026-03"
)

print(f"✅ 아카이브 완료: {result.archived_count}개")
print(f"📄 문서: {result.archived_documents}")
```

### 3. 활성 버전 조회
```python
# 현재 활성화된 모든 버전 조회
active_versions = service.get_active_versions()

for version in active_versions:
    print(f"{version.company} - {version.reference_date}")
    print(f"  문서: {version.document_count}개")
    print(f"  Chunk: {version.chunk_count}개")
```

### 4. 버전 통계 조회
```python
# 활성 + 아카이브 모든 버전 통계
all_versions = service.get_version_statistics()

for version in all_versions:
    status = "활성" if version.is_active else "아카이브"
    print(f"{status} | {version.company} - {version.reference_date}")
```

### 5. 버전 복원 (롤백)
```python
# 아카이브된 버전을 다시 활성화
restored = service.restore_version(
    company="삼성생명",
    reference_date="2026-02"
)

print(f"✅ 복원 완료: {restored}개")
```

---

## 📊 버전 관리 시나리오

### 시나리오 1: 월별 카탈로그 업데이트

```python
# 1. 2026년 3월 카탈로그 업로드
upload_catalog("삼성생명_2026년03월_상품카탈로그.pdf")

# 2. 구버전 아카이브 (자동)
service.archive_old_versions("삼성생명", "2026-03")

# 3. 검색 테스트
results = search_knowledge_base(query_embedding)
# 결과: 2026년 3월 버전만 반환
```

### 시나리오 2: 긴급 롤백

```python
# 1. 문제 발견 (2026년 3월 버전에 오류)
# 2. 긴급 롤백
service.restore_version("삼성생명", "2026-02")

# 3. 2026년 3월 버전 비활성화
service.deactivate_all_versions("삼성생명")

# 4. 수정 후 재업로드
upload_catalog("삼성생명_2026년03월_상품카탈로그_수정본.pdf")
```

### 시나리오 3: 보험사별 버전 관리

```python
# 삼성생명 모든 버전 조회
samsung_versions = service.get_version_by_company("삼성생명")

for version in samsung_versions:
    status = "✅" if version.is_active else "📦"
    print(f"{status} {version.reference_date}: {version.chunk_count}개")

# 출력:
# ✅ 2026-03: 150개
# 📦 2026-02: 145개
# 📦 2026-01: 140개
```

---

## 🔍 SQL 쿼리 예시

### 활성 버전만 조회
```sql
SELECT 
    company,
    reference_date,
    COUNT(*) as chunk_count
FROM gk_knowledge_base
WHERE is_active = true
GROUP BY company, reference_date
ORDER BY company, reference_date DESC;
```

### 아카이브 버전 조회
```sql
SELECT 
    company,
    reference_date,
    archived_at,
    COUNT(*) as chunk_count
FROM gk_knowledge_base
WHERE is_active = false
GROUP BY company, reference_date, archived_at
ORDER BY archived_at DESC;
```

### 버전 이력 조회
```sql
SELECT 
    company,
    reference_date,
    is_active,
    version_date,
    COUNT(*) as chunk_count
FROM gk_knowledge_base
WHERE company = '삼성생명'
GROUP BY company, reference_date, is_active, version_date
ORDER BY reference_date DESC;
```

---

## 🧪 테스트 실행

### Version Control Service 테스트
```bash
python hq_backend/services/version_control_service.py
```

### Version Control 테스트 스위트
```bash
python hq_backend/tests/test_version_control.py
```

### 예상 출력
```
======================================================================
🧪 Version Control Service 테스트 스위트
   구버전 카탈로그 데이터 격리 및 Hot-Swap 검증
======================================================================

======================================================================
📊 버전 통계 조회 테스트
======================================================================

총 버전 수: 5개

버전 목록:
  ✅ 활성 | 삼성생명 - 2026-03
         문서: 1개, Chunk: 150개
  📦 아카이브 | 삼성생명 - 2026-02
         문서: 1개, Chunk: 145개

✅ 버전 통계 조회 테스트 통과

======================================================================
🎉 모든 테스트 통과
======================================================================

✅ Version Control Service가 정상적으로 작동합니다
✅ Hot-Swap 로직 검증 완료
✅ 구버전 격리 원칙 확인
✅ 과거 자료 혼입 방지 준비 완료
```

---

## ⚠️ 주의사항

### 1. 물리적 삭제 금지
- ❌ `DELETE FROM gk_knowledge_base` 절대 금지
- ✅ `UPDATE gk_knowledge_base SET is_active=false` 사용

### 2. 검색 필터 강제 적용
- 모든 RAG 검색 쿼리에 `is_active=true` 필터 필수
- Supabase RPC 함수 내부에서 자동 적용

### 3. 버전 날짜 관리
- `reference_date`: 카탈로그 기준연월 (YYYY-MM)
- `version_date`: 실제 업로드 날짜 (YYYY-MM-DD)
- 두 날짜를 혼동하지 않도록 주의

### 4. 아카이브 전 확인
- 아카이브 전 활성 버전 목록 확인
- 실수로 최신 버전을 아카이브하지 않도록 주의

---

## 📈 성능 최적화

### 인덱스 활용
```sql
-- is_active 인덱스로 빠른 필터링
CREATE INDEX idx_gk_knowledge_base_is_active ON gk_knowledge_base(is_active);

-- 복합 인덱스로 보험사+날짜 검색 최적화
CREATE INDEX idx_gk_knowledge_base_company_date_active 
    ON gk_knowledge_base(company, reference_date, is_active);
```

### 쿼리 최적화
```sql
-- ✅ 좋은 예: 인덱스 활용
SELECT * FROM gk_knowledge_base 
WHERE is_active = true 
  AND company = '삼성생명'
ORDER BY reference_date DESC;

-- ❌ 나쁜 예: 인덱스 미활용
SELECT * FROM gk_knowledge_base 
WHERE is_active IS NOT false;  -- 인덱스 사용 불가
```

---

## 🔗 관련 문서

- `hq_backend/knowledge_base/schema/gk_knowledge_base.sql`: 기본 스키마
- `hq_backend/services/document_processor.py`: 문서 전처리
- `hq_backend/api/chat_routes.py`: Chat API
- `GCS_SYNC_AND_TRIGGER_GUIDE.md`: GCS 동기화 가이드
- `QUERY_EXPANSION_INTEGRATION_GUIDE.md`: Query Expansion 가이드

---

## 💡 Best Practices

### 1. 정기적인 버전 정리
```python
# 6개월 이상 된 아카이브 버전 확인
old_versions = [
    v for v in service.get_version_statistics()
    if not v.is_active and v.version_date < six_months_ago
]

# 필요시 물리적 삭제 (신중하게)
# (일반적으로 권장하지 않음)
```

### 2. 버전 이력 모니터링
```python
# 주기적으로 버전 요약 확인
service.print_version_summary()

# 이상 징후 감지
# - 활성 버전이 너무 많은 경우
# - 동일 보험사에 여러 활성 버전이 있는 경우
```

### 3. 롤백 계획 수립
```python
# 새 버전 배포 전 롤백 계획 수립
# 1. 현재 활성 버전 백업
# 2. 새 버전 배포
# 3. 문제 발생 시 즉시 롤백
```

---

**작성자**: Goldkey AI Masters 프로젝트 팀  
**버전**: 1.0  
**최종 업데이트**: 2026-03-31
