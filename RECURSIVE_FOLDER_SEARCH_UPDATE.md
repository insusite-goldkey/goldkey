# 재귀 폴더 검색 및 folder_path 메타데이터 업데이트

**작성일**: 2026-03-30  
**업데이트**: Phase 5 고도화 - 하위 폴더 지원

---

## ✅ 업데이트 완료 내역

### 1. 데이터베이스 스키마 업데이트

**파일**: `d:\CascadeProjects\hq_backend\knowledge_base\schema\update_schema_v2.sql`

**추가된 컬럼**:
- `folder_path TEXT` — 파일이 위치한 폴더 경로 (상대 경로)

**추가된 인덱스**:
- `idx_gk_knowledge_folder_path` — 폴더 경로 기반 검색 최적화

### 2. RAG 파이프라인 업데이트

**파일**: `d:\CascadeProjects\hq_backend\core\rag_ingestion_v2.py`

**주요 변경 사항**:

#### A. 재귀 폴더 검색 (이미 구현됨)
```python
# Line 511: glob 패턴으로 재귀 검색
pdf_files = list(source_path.glob("**/*.pdf"))
```
- `**/*.pdf` 패턴으로 모든 하위 폴더의 PDF 파일 자동 검색
- 폴더 깊이 제한 없음

#### B. folder_path 메타데이터 추출 및 저장
```python
# source_root 기준 상대 경로 계산
if source_root:
    try:
        folder_path = str(file_path.parent.relative_to(Path(source_root)))
    except ValueError:
        folder_path = str(file_path.parent)
else:
    folder_path = str(file_path.parent)
```

**예시**:
- 파일: `source_docs/2026/법인/법인_상담_자료.pdf`
- source_root: `source_docs`
- folder_path: `2026/법인` (상대 경로)

#### C. 폴더별 통계 출력
```python
if folder_stats:
    print("📁 폴더별 통계:")
    for folder, count in sorted(folder_stats.items()):
        print(f"  {folder}: {count}개")
```

---

## 🗂️ 폴더 구조 예시

### Before (기존)
```
source_docs/
├── 법인 상담 자료 통합본 2022.09..pdf
├── 건물소유점유자 배상책임 및 특종배상책임.pdf
└── 개인.법인 화재및 특종보험 통합 자료.pdf
```

### After (권장)
```
source_docs/
├── 2026/
│   ├── 법인/
│   │   ├── 법인_상담_자료_v1.0.pdf
│   │   └── 법인_세무_가이드.pdf
│   ├── 배상책임/
│   │   └── 건물소유자_배상책임.pdf
│   └── 화재보험/
│       └── 화재보험_통합자료.pdf
├── 2025/
│   └── 약관/
│       └── 자동차보험_표준약관.pdf
└── archive/
    └── old_documents.pdf
```

---

## 🚀 사용 방법

### 1. Supabase 스키마 업데이트 (필수)

**Supabase SQL Editor에서 실행**:
```sql
-- folder_path 컬럼 추가
ALTER TABLE gk_knowledge_base ADD COLUMN IF NOT EXISTS folder_path TEXT;

-- 폴더 경로 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_gk_knowledge_folder_path 
ON gk_knowledge_base (folder_path);
```

또는 전체 스키마 업데이트:
```sql
-- d:\CascadeProjects\hq_backend\knowledge_base\schema\update_schema_v2.sql 실행
```

### 2. 폴더 구조 정리

**날짜별 정리**:
```
source_docs/
├── 2026/
├── 2025/
└── 2024/
```

**주제별 정리**:
```
source_docs/
├── 법인컨설팅/
├── 배상책임/
├── 화재보험/
├── 약관/
└── 판례/
```

**날짜 + 주제별 정리** (권장):
```
source_docs/
├── 2026/
│   ├── 법인/
│   ├── 배상책임/
│   └── 화재보험/
└── 2025/
    ├── 약관/
    └── 판례/
```

### 3. RAG 파이프라인 실행

```powershell
cd d:\CascadeProjects
python run_intelligent_rag.py
```

**실행 결과 예시**:
```
================================================================================
📁 디렉토리 일괄 처리 시작
================================================================================
디렉토리: hq_backend\knowledge_base\source_docs
PDF 파일 수: 15개
================================================================================

🚀 지능형 RAG 임베딩 파이프라인 시작
문서: source_docs\2026\법인\법인_상담_자료.pdf
📊 파일 메타데이터 추출 중...
  파일 해시: 2da09a0a09485268...
  파일 크기: 687,202 bytes
  폴더 경로: 2026\법인
  문서 날짜: 2026-03-30
  버전: v1.0

================================================================================
✅ 지능형 RAG 임베딩 파이프라인 완료
================================================================================
총 파일 수: 15개
  ✅ 새 파일 추가 완료: 5개
  ⏭️ 기존 파일 유지 (중복 제외): 10개
  ❌ 실패: 0개
================================================================================

📊 카테고리별 통계:
  법인: 2개
  배상책임: 1개
  화재보험: 2개

📁 폴더별 통계:
  2026\법인: 2개
  2026\배상책임: 1개
  2026\화재보험: 2개
```

---

## 🔍 폴더 경로 기반 검색

### Supabase에서 폴더별 검색

```sql
-- 특정 폴더의 문서만 검색
SELECT document_name, folder_path, created_at
FROM gk_knowledge_base
WHERE folder_path = '2026/법인'
ORDER BY created_at DESC;

-- 특정 연도의 모든 문서 검색
SELECT document_name, folder_path, created_at
FROM gk_knowledge_base
WHERE folder_path LIKE '2026/%'
ORDER BY created_at DESC;

-- 폴더별 청크 수 통계
SELECT 
    folder_path,
    COUNT(*) AS chunk_count,
    COUNT(DISTINCT document_name) AS document_count
FROM gk_knowledge_base
GROUP BY folder_path
ORDER BY chunk_count DESC;
```

### Python에서 폴더별 검색

```python
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 특정 폴더의 문서 검색
result = supabase.table("gk_knowledge_base") \
    .select("document_name, folder_path, created_at") \
    .eq("folder_path", "2026/법인") \
    .execute()

# 특정 연도의 모든 문서 검색
result = supabase.table("gk_knowledge_base") \
    .select("document_name, folder_path, created_at") \
    .like("folder_path", "2026/%") \
    .execute()
```

---

## 📊 주요 개선 사항

| 항목 | Before | After |
|------|--------|-------|
| 폴더 검색 | ✅ 재귀 검색 지원 (`**/*.pdf`) | ✅ 동일 (이미 구현됨) |
| 폴더 정보 저장 | ❌ 없음 | ✅ `folder_path` 메타데이터 저장 |
| 폴더별 통계 | ❌ 없음 | ✅ 실행 보고서에 폴더별 통계 포함 |
| 폴더별 검색 | ❌ 불가능 | ✅ SQL/Python으로 폴더별 검색 가능 |

---

## 🎯 사용 시나리오

### 시나리오 1: 연도별 문서 관리
```
source_docs/
├── 2026/  (최신 문서)
├── 2025/  (작년 문서)
└── 2024/  (2년 전 문서)
```

**장점**:
- 연도별로 문서 버전 관리
- 최신 문서만 선택적으로 검색 가능
- 오래된 문서 아카이빙 용이

### 시나리오 2: 주제별 문서 관리
```
source_docs/
├── 법인컨설팅/
├── 배상책임/
├── 화재보험/
├── 약관/
└── 판례/
```

**장점**:
- 주제별로 문서 분류
- 특정 주제만 선택적으로 검색 가능
- 카테고리 자동 분류 정확도 향상

### 시나리오 3: 하이브리드 (날짜 + 주제)
```
source_docs/
├── 2026/
│   ├── 법인/
│   ├── 배상책임/
│   └── 화재보험/
└── 2025/
    ├── 약관/
    └── 판례/
```

**장점**:
- 연도별 + 주제별 이중 분류
- 최신 문서 + 특정 주제 조합 검색 가능
- 가장 체계적인 문서 관리

---

## 📋 체크리스트

### 스키마 업데이트
- [ ] Supabase SQL Editor 접속
- [ ] `update_schema_v2.sql` 실행
- [ ] `folder_path` 컬럼 추가 확인
- [ ] `idx_gk_knowledge_folder_path` 인덱스 확인

### 폴더 구조 정리
- [ ] source_docs 폴더 백업
- [ ] 날짜별/주제별 하위 폴더 생성
- [ ] PDF 파일 이동 (수동 또는 스크립트)

### RAG 파이프라인 실행
- [ ] `python run_intelligent_rag.py` 실행
- [ ] 폴더별 통계 확인
- [ ] 보고서 JSON 파일 확인

### 검증
- [ ] Supabase에서 folder_path 데이터 확인
- [ ] 폴더별 검색 쿼리 테스트
- [ ] CRM 앱에서 RAG 기능 테스트

---

## 🎉 결론

**재귀 폴더 검색 및 folder_path 메타데이터 저장 기능이 추가되었습니다!**

### 핵심 기능
- ✅ **재귀 폴더 검색**: `**/*.pdf` 패턴으로 모든 하위 폴더 자동 검색
- ✅ **folder_path 저장**: 파일이 위치한 폴더 경로를 메타데이터로 저장
- ✅ **폴더별 통계**: 실행 보고서에 폴더별 처리 현황 포함
- ✅ **폴더별 검색**: SQL/Python으로 특정 폴더의 문서만 검색 가능

### 다음 단계
1. **Supabase 스키마 업데이트** (`folder_path` 컬럼 추가)
2. **폴더 구조 정리** (날짜별/주제별 하위 폴더 생성)
3. **RAG 파이프라인 실행** (`python run_intelligent_rag.py`)

---

**작성일**: 2026-03-30  
**작성자**: Windsurf Cascade AI  
**Phase**: Phase 5 고도화 - 재귀 폴더 검색 지원
