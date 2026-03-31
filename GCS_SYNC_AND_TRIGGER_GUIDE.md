# GCS 동기화 및 RAG 트리거 시스템 가이드

**작성일**: 2026-03-31  
**목적**: source_docs → GCS → Cloud Run → Supabase 자동 벡터화 파이프라인

---

## 🏗️ 시스템 아키텍처

```
[로컬 source_docs]
        ↓
   [GCS Sync Script]
        ↓
[GCS goldkey-knowledge-base 버킷]
        ↓
   [Cloud Storage Pub/Sub]
        ↓
[Cloud Run RAG Trigger API]
        ↓
   [BackgroundTasks]
        ↓
[Supabase gk_knowledge_base]
```

---

## 📂 생성된 파일 목록

### 1. GCS 동기화 서비스
**파일**: `hq_backend/services/gcs_sync_service.py`

**핵심 기능**:
- source_docs 폴더 모니터링
- 새로운 PDF 자동 감지 (SHA256 해시 기반 중복 방지)
- GCS goldkey-knowledge-base 버킷으로 자동 업로드
- 업로드 이력 관리 (gcs_upload_history.json)

### 2. RAG 트리거 API
**파일**: `hq_backend/api/rag_trigger_api.py`

**엔드포인트**:
- `GET /`: 루트 엔드포인트
- `GET /health`: 헬스 체크
- `POST /trigger/gcs-upload`: GCS 업로드 트리거
- `POST /trigger/manual`: 수동 트리거
- `POST /webhook/gcs`: GCS Pub/Sub Webhook

### 3. 배포 설정
- `hq_backend/api/requirements_api.txt`: Python 패키지 목록
- `hq_backend/api/Dockerfile.api`: Cloud Run 배포용 Dockerfile

---

## 🚀 사용 방법

### STEP 1: 로컬에서 GCS로 동기화

#### 수동 실행
```bash
python hq_backend/services/gcs_sync_service.py
```

#### Python 스크립트에서 사용
```python
from hq_backend.services.gcs_sync_service import GCSSyncService

# 동기화 서비스 초기화
sync_service = GCSSyncService()

# 새로운 파일 스캔 및 업로드
results = sync_service.scan_and_upload_new_files()

print(f"업로드: {len(results['uploaded'])}개")
print(f"건너뜀: {len(results['skipped'])}개")
print(f"실패: {len(results['failed'])}개")
```

#### 강제 업로드 (이력 무시)
```python
results = sync_service.scan_and_upload_new_files(force_upload=True)
```

---

### STEP 2: Cloud Run API 배포

#### 로컬 테스트
```bash
cd hq_backend/api
uvicorn rag_trigger_api:app --reload --port 8080
```

#### Docker 빌드
```bash
docker build -f hq_backend/api/Dockerfile.api -t goldkey-rag-trigger .
```

#### Cloud Run 배포
```bash
gcloud run deploy goldkey-rag-trigger \
  --source . \
  --region asia-northeast3 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=$OPENAI_API_KEY,SUPABASE_URL=$SUPABASE_URL,SUPABASE_SERVICE_KEY=$SUPABASE_SERVICE_KEY
```

---

### STEP 3: GCS Pub/Sub 트리거 설정

#### Cloud Storage 알림 생성
```bash
# Pub/Sub 토픽 생성
gcloud pubsub topics create goldkey-knowledge-base-uploads

# GCS 버킷에 알림 설정
gsutil notification create -t goldkey-knowledge-base-uploads \
  -f json \
  -e OBJECT_FINALIZE \
  gs://goldkey-knowledge-base
```

#### Cloud Run에 Pub/Sub 연결
```bash
gcloud run services update goldkey-rag-trigger \
  --region asia-northeast3 \
  --update-env-vars PUBSUB_TOPIC=goldkey-knowledge-base-uploads
```

---

## 📊 자동 벡터화 파이프라인

### 1. GCS 업로드 감지
- Cloud Storage가 새 파일 업로드 감지
- Pub/Sub 메시지 발행

### 2. Cloud Run API 트리거
- Pub/Sub 메시지 수신
- PDF 파일 여부 확인
- 백그라운드 작업 시작

### 3. 백그라운드 작업 (5단계)

#### [1/5] GCS에서 파일 다운로드
```python
storage_client = storage.Client()
bucket = storage_client.bucket("goldkey-knowledge-base")
blob = bucket.blob(file_path)
blob.download_to_filename(temp_file_path)
```

#### [2/5] 문서 전처리 및 Chunking
```python
processor = InsuranceDocumentProcessor(
    chunk_size=1000,
    chunk_overlap=150  # 15%
)
chunks = processor.process_pdf(temp_file_path)
```

#### [3/5] 임베딩 생성
```python
for chunk in chunks:
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=chunk["content"]
    )
    chunk["embedding"] = response.data[0].embedding
```

#### [4/5] Supabase에 저장
```python
for chunk in chunks:
    data = {
        "document_name": chunk.get("document_name"),
        "document_category": "보험카탈로그",
        "chunk_index": chunk.get("chunk_index"),
        "content": chunk.get("content"),
        "embedding": chunk.get("embedding"),
        "company": chunk.get("company"),
        "reference_date": chunk.get("reference_date"),
        "gcs_path": file_path
    }
    supabase.table("gk_knowledge_base").insert(data).execute()
```

#### [5/5] 임시 파일 정리
```python
os.remove(temp_file_path)
```

---

## 🔧 환경 변수 설정

### 로컬 개발 (.env)
```bash
OPENAI_API_KEY=your_openai_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_service_key
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### Cloud Run (환경 변수)
```bash
OPENAI_API_KEY=***
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=***
```

---

## 📡 API 사용 예시

### 헬스 체크
```bash
curl https://goldkey-rag-trigger-xxx.run.app/health
```

**응답**:
```json
{
  "status": "healthy",
  "timestamp": "2026-03-31T10:34:00.000Z"
}
```

### 수동 트리거
```bash
curl -X POST https://goldkey-rag-trigger-xxx.run.app/trigger/manual \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "2026/03/삼성생명_2026년03월_상품카탈로그.pdf",
    "force": false
  }'
```

**응답**:
```json
{
  "status": "accepted",
  "message": "벡터화 작업이 백그라운드에서 시작되었습니다.",
  "file": "2026/03/삼성생명_2026년03월_상품카탈로그.pdf"
}
```

---

## 🔍 모니터링 및 로그

### Cloud Run 로그 확인
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=goldkey-rag-trigger" \
  --limit 50 \
  --format json
```

### GCS 업로드 이력 확인
```python
from hq_backend.services.gcs_sync_service import GCSSyncService

sync_service = GCSSyncService()
history = sync_service.load_upload_history()

for file_key, info in history.items():
    print(f"{file_key}: {info['upload_time']}")
```

---

## ⚠️ 주의사항

### 1. GCS 버킷 권한
- Cloud Run 서비스 계정에 `roles/storage.objectViewer` 권한 필요
- Pub/Sub 토픽에 `roles/pubsub.publisher` 권한 필요

### 2. 중복 방지
- GCS Sync Service는 SHA256 해시로 중복 감지
- 동일 파일은 자동으로 건너뜀
- 강제 업로드 시 `force_upload=True` 사용

### 3. 비용 최적화
- 백그라운드 작업은 비동기로 실행 (Cloud Run 인스턴스 유지 시간 최소화)
- 임베딩 생성은 배치 처리 권장
- 임시 파일은 반드시 삭제

### 4. 에러 핸들링
- 모든 단계에서 try-except 블록 사용
- 실패 시 로그 기록 및 알림
- 재시도 로직 구현 권장

---

## 🎯 워크플로우 예시

### 시나리오: 새로운 보험 카탈로그 추가

#### 1. 로컬에 PDF 추가
```bash
# 파일 추가
cp 삼성생명_2026년03월_상품카탈로그.pdf \
   hq_backend/knowledge_base/source_docs/2026/03/
```

#### 2. GCS 동기화 실행
```bash
python hq_backend/services/gcs_sync_service.py
```

**출력**:
```
======================================================================
📤 GCS 동기화 시작
======================================================================

📊 총 1개 파일 발견
📤 업로드 중: 삼성생명_2026년03월_상품카탈로그.pdf
✅ 업로드 완료: 2026/03/삼성생명_2026년03월_상품카탈로그.pdf

======================================================================
📊 동기화 결과
======================================================================
✅ 업로드: 1개
⏭️  건너뜀: 0개
❌ 실패: 0개
```

#### 3. Cloud Run 자동 트리거
- GCS가 Pub/Sub 메시지 발행
- Cloud Run API가 메시지 수신
- 백그라운드 작업 시작

#### 4. 벡터화 작업 진행
```
======================================================================
🚀 벡터화 작업 시작
======================================================================
📦 버킷: goldkey-knowledge-base
📄 파일: 2026/03/삼성생명_2026년03월_상품카탈로그.pdf

📥 [1/5] GCS에서 파일 다운로드 중...
✅ 다운로드 완료

📄 [2/5] 문서 전처리 및 Chunking 중...
✅ Chunking 완료: 45개 Chunk 생성

🧠 [3/5] 임베딩 생성 중...
  진행률: 10/45 (22.2%)
  진행률: 20/45 (44.4%)
  진행률: 30/45 (66.7%)
  진행률: 40/45 (88.9%)
✅ 임베딩 생성 완료: 45개

💾 [4/5] Supabase에 저장 중...
  진행률: 10/45 (22.2%)
  진행률: 20/45 (44.4%)
  진행률: 30/45 (66.7%)
  진행률: 40/45 (88.9%)
✅ Supabase 저장 완료: 45개

🗑️  [5/5] 임시 파일 정리 중...
✅ 정리 완료

======================================================================
🎉 벡터화 작업 완료
======================================================================
📄 파일: 2026/03/삼성생명_2026년03월_상품카탈로그.pdf
📊 총 Chunk 수: 45
⏰ 완료 시간: 2026-03-31T10:45:23.456Z
```

#### 5. Supabase 확인
```sql
SELECT 
    document_name,
    company,
    reference_date,
    COUNT(*) as chunk_count
FROM gk_knowledge_base
WHERE document_name = '삼성생명_2026년03월_상품카탈로그.pdf'
GROUP BY document_name, company, reference_date;
```

---

## 📚 관련 문서

- `hq_backend/services/document_processor.py`: 문서 전처리 및 Chunking
- `hq_backend/config/rag_config.py`: RAG 설정
- `hq_backend/knowledge_base/README_FOLDER_STRUCTURE.md`: 폴더 구조 가이드
- `DEMOGRAPHICS_INTELLIGENCE_IMPLEMENTATION_REPORT.md`: 인구통계학적 지능 구현

---

**작성자**: Goldkey AI Masters 프로젝트 팀  
**버전**: 1.0  
**최종 업데이트**: 2026-03-31
