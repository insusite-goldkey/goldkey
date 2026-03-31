# Phase 5 RAG 기능 Cloud Run 배포 요약

**배포 시작**: 2026-03-30 21:50  
**배포 상태**: 🔄 진행 중

---

## 📦 배포 중인 내용

### 1. RAG 엔진 통합 코드
- ✅ `hq_backend/engines/rag_engine.py` — RAG 검색 엔진
- ✅ `hq_backend/core/rag_ingestion.py` — 임베딩 파이프라인
- ✅ `blocks/crm_ai_chat_block.py` — CRM AI 채팅 블록
- ✅ `crm_app_impl.py` — RAG 채팅 통합 (Line 112, 1998-2001)

### 2. Docker 이미지
- **Dockerfile**: `Dockerfile.crm`
- **빌드 설정**: `cloudbuild_crm.yaml`
- **이미지 태그**: `v20260330-2150`
- **레지스트리**: `asia-northeast3-docker.pkg.dev/gen-lang-client-0777682955/goldkey/goldkey-crm`

### 3. Cloud Run 서비스
- **서비스명**: `goldkey-crm`
- **리전**: `asia-northeast3`
- **운영 URL**: https://goldkey-crm-817097913199.asia-northeast3.run.app
- **메모리**: 1Gi
- **CPU**: 1
- **최소 인스턴스**: 0
- **최대 인스턴스**: 3

---

## 🔐 환경변수 설정 필요

배포 완료 후 다음 환경변수를 Cloud Run에 설정해야 RAG 기능이 작동합니다:

| 환경변수 | 설명 | 필수 |
|---------|------|------|
| `OPENAI_API_KEY` | OpenAI API 키 (임베딩) | ✅ |
| `GEMINI_API_KEY` | Gemini API 키 (답변 생성) | ✅ |
| `SUPABASE_URL` | Supabase 프로젝트 URL | ✅ |
| `SUPABASE_SERVICE_KEY` | Supabase 서비스 role 키 | ✅ |

### 설정 방법

**방법 1: PowerShell 스크립트**
```powershell
cd d:\CascadeProjects
powershell -ExecutionPolicy Bypass -File "set_crm_env_vars.ps1"
```

**방법 2: gcloud CLI**
```powershell
gcloud run services update goldkey-crm `
    --region asia-northeast3 `
    --project gen-lang-client-0777682955 `
    --update-env-vars "OPENAI_API_KEY=sk-proj-xxxxx,GEMINI_API_KEY=AIzaSyxxxxx,SUPABASE_URL=https://xxxxx.supabase.co,SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." `
    --quiet
```

**방법 3: Google Cloud Console**
1. https://console.cloud.google.com/run/detail/asia-northeast3/goldkey-crm 접속
2. "편집 및 새 버전 배포" 클릭
3. "변수 및 보안 비밀" 섹션에서 환경변수 4개 추가
4. "배포" 클릭

---

## ✅ 배포 완료 후 검증 절차

### 1. 배포 상태 확인
```powershell
cd d:\CascadeProjects
powershell -ExecutionPolicy Bypass -File "verify_crm_deployment.ps1"
```

**검증 항목**:
- ✅ Cloud Run 서비스 상태 (Ready)
- ✅ 배포 URL 확인
- ✅ 환경변수 4개 설정 확인
- ✅ HTTP 200 응답 확인
- ✅ RAG 엔진 초기화 로그 확인

### 2. 웹 브라우저 테스트
**URL**: https://goldkey-crm-817097913199.asia-northeast3.run.app

**확인 사항**:
1. ✅ CRM 앱 정상 로드
2. ✅ 로그인 화면 표시
3. ✅ 로그인 후 고객 목록 화면
4. ✅ **"🤖 AI 상담 채팅 (RAG 전문 지식 검색)"** 섹션 표시
5. ✅ 카테고리 선택 드롭다운
6. ✅ 질문 입력창 및 전송 버튼

### 3. RAG 기능 테스트

**테스트 질문 1**: "법인 임원 퇴직금 세무 처리 방법은?"
- 카테고리: 법인컨설팅
- 예상: 법인 상담 자료에서 답변 + 출처 표시

**테스트 질문 2**: "공장 화재보험 120% 가입 룰이 뭔가요?"
- 카테고리: 화재보험
- 예상: 화재보험 자료에서 답변 + 출처 표시

**테스트 질문 3**: "건물소유자 배상책임보험 가입 대상은?"
- 카테고리: 배상책임
- 예상: 배상책임 자료에서 답변 + 출처 표시

---

## 📊 RAG 지식 베이스 (Supabase)

| 카테고리 | 청크 수 | 문서 | 페이지 |
|---------|---------|------|--------|
| 법인컨설팅 | 167개 | 법인 상담 자료 통합본 2022.09..pdf | 80 |
| 배상책임 | 72개 | 건물소유점유자 배상책임 및 특종배상책임.pdf | 30 |
| 화재보험 | 93개 | 개인.법인 화재및 특종보험 통합 자료.pdf | 41 |
| **합계** | **332개** | **3개 문서** | **151** |

**벡터 DB 상태**:
- ✅ Supabase pgvector 확장 활성화
- ✅ IVFFlat 인덱스 구축 완료
- ✅ OpenAI text-embedding-3-small (1536차원)
- ✅ 코사인 유사도 검색 (threshold=0.7)

---

## 🔍 로그 확인 (문제 발생 시)

```powershell
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=goldkey-crm" `
    --project gen-lang-client-0777682955 `
    --limit 50 `
    --format "table(timestamp,severity,textPayload)"
```

**주요 확인 로그**:
- ✅ `RAG 엔진 초기화 완료`
- ✅ `환경변수 로드 성공`
- ❌ `환경변수 미설정: OPENAI_API_KEY` (오류)
- ❌ `RAG 엔진 초기화 실패` (오류)

---

## 📁 생성된 파일

1. **`PHASE5_CLOUD_RUN_DEPLOYMENT_GUIDE.md`** — 상세 배포 가이드
2. **`set_crm_env_vars.ps1`** — 환경변수 설정 스크립트
3. **`verify_crm_deployment.ps1`** — 배포 검증 스크립트
4. **`PHASE5_CRM_RAG_INTEGRATION_REPORT.md`** — 로컬 통합 완료 보고서
5. **`PHASE5_DEPLOYMENT_SUMMARY.md`** — 배포 요약 (현재 파일)

---

## 🎯 다음 단계

### 배포 완료 대기 중
현재 Cloud Build가 Docker 이미지를 빌드하고 있습니다 (약 5-10분 소요).

### 배포 완료 후
1. **환경변수 설정** (방법 1, 2, 또는 3 중 선택)
2. **배포 검증** (`verify_crm_deployment.ps1` 실행)
3. **웹 브라우저 테스트** (운영 URL 접속)
4. **RAG 기능 테스트** (3개 질문으로 검증)

---

**작성일**: 2026-03-30  
**작성자**: Windsurf Cascade AI  
**Phase**: Phase 5 Cloud Run 배포 진행 중
