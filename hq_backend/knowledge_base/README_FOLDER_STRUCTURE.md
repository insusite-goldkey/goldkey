# RAG Knowledge Base 폴더 구조 가이드

**작성일**: 2026-03-31  
**목적**: source_docs 경로 정규화 및 YYYY/MM/ 계층 구조 관리

---

## 📂 폴더 구조

```
hq_backend/knowledge_base/
├── source_docs/              # 정규화된 소스 문서 경로 (source_docs_ 아님)
│   ├── 2026/
│   │   ├── 01/              # 2026년 1월 문서
│   │   ├── 02/              # 2026년 2월 문서
│   │   ├── 03/              # 2026년 3월 문서
│   │   └── ...
│   ├── 2027/
│   │   └── ...
│   └── [기타 문서]           # 월별 분류되지 않은 레거시 문서
├── schema/                   # Supabase 스키마 정의
│   ├── gk_knowledge_base.sql
│   └── update_schema_v2.sql
└── static/                   # 정적 파일 (이미지, PDF 등)
```

---

## 🛠️ 폴더 관리 유틸리티

### FolderManager 클래스

**위치**: `hq_backend/utils/folder_manager.py`

**주요 기능**:
- 연도/월별 폴더 자동 생성
- 파일 이동/복사 (월별 분류)
- 폴더 통계 조회
- 빈 폴더 정리

### 사용 예시

```python
from hq_backend.utils.folder_manager import FolderManager

# 초기화
manager = FolderManager()

# 현재 월 폴더 생성
current_folder = manager.get_current_month_folder()
print(current_folder)  # .../source_docs/2026/03/

# 특정 월 폴더 생성
jan_2026 = manager.create_month_folder(2026, 1)

# 파일을 현재 월 폴더로 이동
new_path = manager.move_file_to_month_folder("document.pdf")

# 폴더 통계 조회
stats = manager.get_folder_stats(2026, 3)
print(f"파일 수: {stats['file_count']}")
print(f"총 크기: {stats['total_size_mb']}MB")
```

---

## ⚙️ RAG 설정 파일

### RAGConfig 클래스

**위치**: `hq_backend/config/rag_config.py`

**주요 경로**:
- `SOURCE_DOCS_PATH`: `hq_backend/knowledge_base/source_docs`
- `SCHEMA_PATH`: `hq_backend/knowledge_base/schema`
- `STATIC_PATH`: `hq_backend/knowledge_base/static`

### 사용 예시

```python
from hq_backend.config.rag_config import RAGConfig, get_current_month_path

# 현재 월 경로
current_path = get_current_month_path()

# 특정 월 경로
jan_path = RAGConfig.get_month_path(2026, 1)

# 모든 마크다운 파일 조회
md_files = RAGConfig.get_all_document_files(extensions=['.md'])
```

---

## 📋 경로 정규화 내역

### 변경 전
```
hq_backend/knowledge_base/source_docs_/  ❌ (언더바 포함)
```

### 변경 후
```
hq_backend/knowledge_base/source_docs/   ✅ (정규화됨)
```

**변경 사유**:
- 디렉토리 명칭 표준화
- 언더바(_) 제거로 가독성 향상
- 계층적 폴더 구조 (YYYY/MM/) 도입

---

## 🔄 RAG 인제스트 스크립트 통합

### 기존 스크립트
- `run_fire_insurance_rag_ingest.py`
- `run_car_accident_rag_ingest.py`
- `run_demographics_rag_ingest.py`
- `run_intelligent_rag.py`

### 권장 사항
새로운 문서를 추가할 때는 `FolderManager`를 사용하여 자동으로 월별 폴더에 저장:

```python
from hq_backend.utils.folder_manager import FolderManager

manager = FolderManager()

# 새 문서를 현재 월 폴더로 복사
new_doc_path = manager.copy_file_to_month_folder(
    "new_document.md",
    year=2026,
    month=3
)

# RAG 인제스트 실행
# ... (기존 로직)
```

---

## 📊 월별 문서 관리 전략

### 1. 신규 문서
- 모든 신규 문서는 **현재 연도/월 폴더**에 저장
- `FolderManager.copy_file_to_month_folder()` 사용

### 2. 레거시 문서
- 기존 문서는 `source_docs/` 루트에 유지
- 필요 시 수동으로 월별 폴더로 이동

### 3. 업데이트된 문서
- 업데이트 시점의 연도/월 폴더에 새 버전 저장
- 원본은 유지 (버전 관리)

### 4. 폴더 정리
- 주기적으로 `cleanup_empty_folders()` 실행
- 빈 폴더 자동 삭제

---

## 🚀 실행 방법

### 폴더 구조 테스트
```bash
python hq_backend/utils/folder_manager.py
```

### 출력 예시
```
============================================================
RAG Knowledge Base 폴더 구조 관리 유틸리티
============================================================

✅ 기본 경로: D:\CascadeProjects\hq_backend\knowledge_base\source_docs
✅ 현재 월 폴더 생성: D:\CascadeProjects\hq_backend\knowledge_base\source_docs\2026\03
✅ 2026년 1월 폴더 생성: D:\CascadeProjects\hq_backend\knowledge_base\source_docs\2026\01
✅ 2026년 2월 폴더 생성: D:\CascadeProjects\hq_backend\knowledge_base\source_docs\2026\02

📊 존재하는 연도: [2026]
📊 2026년 월 목록: [1, 2, 3]

📂 전체 폴더 수: 3
  - 2026년 01월: 0개 파일, 0.0MB
  - 2026년 02월: 0개 파일, 0.0MB
  - 2026년 03월: 0개 파일, 0.0MB

============================================================
✅ 폴더 구조 관리 유틸리티 테스트 완료
============================================================
```

---

## 📚 관련 문서

- `hq_backend/utils/folder_manager.py`: 폴더 관리 유틸리티
- `hq_backend/config/rag_config.py`: RAG 설정 파일
- `run_demographics_rag_ingest.py`: 인구통계학적 지능 RAG 인제스트
- `DEMOGRAPHICS_INTELLIGENCE_IMPLEMENTATION_REPORT.md`: 구현 보고서

---

## ⚠️ 주의사항

### 경로 하드코딩 금지
❌ **잘못된 예시**:
```python
path = "D:/CascadeProjects/hq_backend/knowledge_base/source_docs_"
```

✅ **올바른 예시**:
```python
from hq_backend.config.rag_config import get_source_docs_path
path = get_source_docs_path()
```

### 언더바(_) 사용 금지
- `source_docs_` ❌
- `source_docs` ✅

### 월별 폴더 명명 규칙
- `01`, `02`, `03`, ... (2자리 숫자, 0 패딩 필수)
- `1`, `2`, `3` ❌ (0 패딩 없음)

---

**작성자**: Goldkey AI Masters 프로젝트 팀  
**버전**: 1.0  
**최종 업데이트**: 2026-03-31
