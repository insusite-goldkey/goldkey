# [ABSOLUTE DIRECTIVE] Knowledge Base Embedding & Deduplication Protocol

**작성일**: 2026-03-31  
**버전**: 1.0  
**적용 범위**: 모든 RAG 인제스트 스크립트

---

## 🏛️ 최상위 전역 규칙 (Global Rule)

이 지침은 RAG 데이터베이스의 무결성을 지키기 위한 **최상위 전역 규칙**이다. AI(Windsurf)는 `D:\CascadeProjects\hq_backend\knowledge_base\source_docs` 및 모든 지식 베이스 임베딩 관련 코드를 작성하거나 수정할 때, 아래의 **[해시 기반 중복 차단 파이프라인]**을 예외 없이 절대 이행 및 유지해야 한다.

---

## 1️⃣ Zero-Duplication (내용 기반 절대 검증)

### 원칙
- **단순 파일명 비교를 엄격히 금지**
- 문서 스캔 시 반드시 파일의 **'실제 내용(Text Content)'**을 읽어 **SHA-256 해시(Hash)** 값을 추출하여 고유 식별자로 사용

### 구현
```python
def calculate_file_hash(file_path: str) -> str:
    """파일의 SHA-256 해시 계산 (내용 기반 고유 식별자)"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
```

### 효과
- 파일명이 다르더라도 내용이 같으면 중복으로 간주
- 파일명 변경에 영향받지 않는 안정적인 중복 검사

---

## 2️⃣ State Tracking (상태의 영구 보존)

### 원칙
- 성공적으로 Vector DB에 적재된 문서의 해시값과 메타데이터는 `embedding_history.json` (또는 지정된 로컬 Tracking DB)에 **반드시 영구 기록하고 추적**

### 히스토리 파일 구조
```json
{
  "documents": [
    {
      "file_hash": "abc123def456...",
      "file_name": "230630_자동차사고 과실비율 인정기준_최종.pdf",
      "file_path": "static/230630_자동차사고 과실비율 인정기준_최종.pdf",
      "ingested_at": "2026-03-31T17:00:00",
      "chunk_count": 500,
      "scenario_count": 350,
      "category": "traffic_accident_fault_ratio",
      "description": "자동차사고 과실비율 인정기준 (2023년 개정판)"
    }
  ]
}
```

### 구현
```python
def load_embedding_history() -> Dict:
    """임베딩 히스토리 로드 (State Tracking)"""
    history_path = Path(HISTORY_FILE)
    if history_path.exists():
        with open(history_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"documents": []}

def save_embedding_history(history: Dict):
    """임베딩 히스토리 저장 (영구 보존)"""
    history_path = Path(HISTORY_FILE)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
```

---

## 3️⃣ Skip & Upsert (토큰 및 리소스 방어)

### [Absolute Skip] 중복 차단

**원칙**:
- 디렉토리 스캔 시 파일의 해시값이 히스토리 DB에 이미 존재한다면, **LLM 및 임베딩 API 호출을 원천 차단**하고 해당 파일을 즉시 건너뛰기
- `[Skipped]` 중복 자료 제외 시스템 로그 **의무 출력**

**구현**:
```python
def check_document_exists(file_hash: str, history: Dict) -> Optional[Dict]:
    """문서 중복 검사 (Zero-Duplication)"""
    for doc in history.get("documents", []):
        if doc.get("file_hash") == file_hash:
            return doc
    return None

# 사용 예시
existing_doc = check_document_exists(file_hash, history)
if existing_doc:
    print(f"   ⏭️  [Skipped] 중복 자료 제외")
    print(f"   📅 기존 인제스트 일시: {existing_doc.get('ingested_at')}")
    print(f"   📦 기존 청크 수: {existing_doc.get('chunk_count')}")
    print(f"   ✅ 임베딩 비용 절감 완료 (토큰 및 리소스 방어)")
    return  # 임베딩 API 호출 원천 차단
```

### [Smart Upsert] 문서 업데이트

**원칙**:
- 파일명은 동일하나 해시값이 변경된 경우(문서 업데이트), Vector DB 내 기존 청크(Chunks)를 파기하고 새로운 데이터를 덮어쓰기(Upsert)

**구현**:
```python
def delete_existing_chunks(file_hash: str) -> int:
    """기존 청크 삭제 (Smart Upsert)"""
    try:
        result = supabase.table("gk_knowledge_base").delete().eq(
            "file_hash", file_hash
        ).execute()
        deleted_count = len(result.data) if result.data else 0
        return deleted_count
    except Exception as e:
        print(f"⚠️ 기존 청크 삭제 실패: {e}")
        return 0
```

---

## 4️⃣ Execution Constraint (실행 통제 원칙)

### 목적
- **임베딩 비용 낭비**와 **RAG의 시야 협착**을 막는 것이 이 규칙의 목적

### 원칙
- 임베딩 로직이 호출되기 **'직전 단계(Pre-flight)'**에서 이 필터링이 **100% 작동**하도록 아키텍처를 방어
- 이 로직을 우회하거나 삭제하는 어떠한 코드 수정도 **거부**

### 구현 (Pre-flight 필터링)
```python
def ingest_pdf_file(file_info: dict, base_path: str = "d:/CascadeProjects"):
    """
    PDF 파일을 읽어 Supabase gk_knowledge_base에 저장
    [ABSOLUTE DIRECTIVE] 해시 기반 중복 차단 파이프라인 적용
    """
    # ═══════════════════════════════════════════════════════════════════
    # [PRE-FLIGHT] 해시 기반 중복 차단 (Zero-Duplication)
    # ═══════════════════════════════════════════════════════════════════
    
    # 1. 히스토리 로드
    history = load_embedding_history()
    
    # 2. 파일 해시 계산 (내용 기반 고유 식별자)
    file_hash = calculate_file_hash(file_path)
    
    # 3. 중복 검사
    existing_doc = check_document_exists(file_hash, history)
    
    if existing_doc:
        # [Absolute Skip] 중복 문서 발견 → 임베딩 API 호출 원천 차단
        print(f"   ⏭️  [Skipped] 중복 자료 제외")
        return  # ← 임베딩 생성 코드 실행 전 즉시 종료
    
    # 신규 문서만 여기서부터 처리
    print(f"   ✨ 신규 문서 감지 → 임베딩 생성 시작")
    # ... 임베딩 생성 로직 ...
```

---

## 📋 적용 체크리스트

### 모든 RAG 인제스트 스크립트는 다음을 준수해야 함:

- [ ] ✅ `calculate_file_hash()` 함수로 SHA-256 해시 계산
- [ ] ✅ `load_embedding_history()` 함수로 히스토리 로드
- [ ] ✅ `check_document_exists()` 함수로 중복 검사
- [ ] ✅ 중복 발견 시 `[Skipped]` 로그 출력 및 즉시 종료
- [ ] ✅ 신규 문서만 임베딩 생성
- [ ] ✅ `save_embedding_history()` 함수로 히스토리 영구 기록
- [ ] ✅ 임베딩 API 호출 **직전**에 Pre-flight 필터링 작동

---

## 📁 적용 파일

### 현재 적용 완료 (2026-03-31)
1. ✅ `run_car_accident_rag_ingest.py` - 교통사고 과실비율 인정기준
2. ✅ `hq_backend/core/rag_ingestion_v2.py` - 지능형 RAG 파이프라인 (코어 엔진)
3. ✅ `run_fire_insurance_rag_ingest.py` - 법인화재보험 130% 플랜
4. ✅ `run_demographics_rag_ingest.py` - 인구통계학적 지능

### 적용 범위
- **모든 RAG 인제스트 스크립트**: Pre-flight 필터링 100% 작동
- **모든 임베딩 생성 코드**: OpenAI API 호출 전 해시 검증 필수
- **공통 히스토리 파일**: `hq_backend/knowledge_base/embedding_history.json`

---

## 🚫 금지 사항

### 절대 금지
1. ❌ 단순 파일명 비교로 중복 검사
2. ❌ 히스토리 파일 없이 임베딩 생성
3. ❌ Pre-flight 필터링 우회
4. ❌ `[Skipped]` 로그 생략
5. ❌ 이 프로토콜을 삭제하거나 수정하는 코드 변경

### 위반 시 조치
- 즉시 롤백
- 설계자에게 보고
- 프로토콜 준수 코드로 재작성

---

## 📊 효과 측정

### 임베딩 비용 절감
- 중복 문서 재처리 방지 → **OpenAI API 비용 절감**
- 불필요한 Vector DB 저장 방지 → **Supabase 스토리지 절감**

### RAG 품질 향상
- 중복 청크 제거 → **검색 정확도 향상**
- 시야 협착 방지 → **다양한 문서 커버리지 확보**

### 운영 효율성
- 히스토리 추적 → **인제스트 이력 투명성**
- Smart Upsert → **문서 업데이트 자동화**

---

## 🔗 관련 규칙

- [GP-ARCHITECT-PRIORITY] 설계자 우선 원칙
- [GLOBAL POLICY: STRICT CODE PERSISTENCE]
- [GP-SEC-GCS] GCS 저장 시 3대 보안 규정

---

**서명**: Windsurf Cascade AI Assistant  
**날짜**: 2026-03-31  
**버전**: v1.0  
**상태**: ✅ 영구 적용
