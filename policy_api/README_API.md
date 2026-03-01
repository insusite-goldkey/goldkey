# 골드키 약관 RAG 업로드 API

보험사 공시실에서 Chrome Extension이 가로챈 약관 PDF를 수신하여
Google Cloud Storage에 업로드하고 RAG 파이프라인으로 인제스트합니다.

## 파일 구조

```
policy_api/
├── main.py              # FastAPI 앱 진입점
├── gcs_uploader.py      # GCS 업로드 로직
├── rag_ingest.py        # RAG 인제스천 파이프라인 뼈대
├── requirements_api.txt # Python 패키지 목록
└── env.example          # 환경변수 예시 → .env 로 복사해서 사용
```

## 설치 및 실행

```bash
# 1. 패키지 설치
pip install -r requirements_api.txt

# 2. 환경변수 설정
cp env.example .env
# .env 파일을 열어 API_KEY, GCS_BUCKET, GCS_KEY_PATH 등 입력

# 3. 서버 실행 (개발)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 4. 서버 실행 (프로덕션)
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | /health | 헬스체크 |
| POST | /api/upload-policy | 약관 PDF 수신 → GCS 업로드 |
| GET | /docs | Swagger UI (자동 생성) |

### POST /api/upload-policy

**Headers:**
- `X-API-Key`: 환경변수 `API_KEY` 값과 일치해야 함

**Form Data:**
- `file`: PDF 파일 (required)
- `source_url`: 원본 URL (optional)
- `insurer`: 보험사명 (optional, 예: 삼성화재)
- `doc_type`: 문서 유형 (optional, 기본값: 보험약관)

**응답 예시:**
```json
{
  "success": true,
  "message": "'samsung_life_policy.pdf' 업로드 완료",
  "gcs_uri": "gs://goldkey-policy-rag/policies/2026/03/01/a1b2c3d4_samsung_life_policy.pdf",
  "blob_name": "policies/2026/03/01/a1b2c3d4_samsung_life_policy.pdf",
  "size_bytes": 204800,
  "source_url": "https://www.samsunglife.com/...",
  "insurer": "삼성생명",
  "rag": { "success": true, "chunks_indexed": 0, "message": "..." }
}
```

## GCS 설정

1. GCP 콘솔에서 서비스 계정 생성 후 `Storage Object Admin` 권한 부여
2. JSON 키 다운로드 → `GCS_KEY_PATH`에 경로 지정
3. Cloud Run 배포 시 ADC 자동 인증 → `GCS_KEY_PATH` 불필요

## RAG 인제스트 활성화

`rag_ingest.py` 내 TODO 주석을 참고하여 원하는 방식을 선택합니다:
- **LangChain + Supabase pgvector**: 현재 앱과 동일한 벡터 DB 사용
- **직접 연동**: `app.py`의 `_rag_db_add_document` 함수를 공통 모듈로 분리 후 호출
