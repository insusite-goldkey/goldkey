# Phase 5 RAG 기능 Cloud Run 배포 가이드

**배포일시**: 2026-03-30  
**대상 서비스**: goldkey-crm (CRM 앱)  
**운영 URL**: https://goldkey-crm-817097913199.asia-northeast3.run.app

---

## 🔐 Step 1: Cloud Run 환경변수 설정

### 필수 환경변수 (4개)

RAG 엔진 작동을 위해 다음 환경변수를 Cloud Run에 설정해야 합니다:

| 환경변수 | 설명 | 로컬 .env 파일 참조 |
|---------|------|-------------------|
| `OPENAI_API_KEY` | OpenAI API 키 (임베딩 생성) | ✅ |
| `GEMINI_API_KEY` | Gemini API 키 (답변 생성) | ✅ |
| `SUPABASE_URL` | Supabase 프로젝트 URL | ✅ |
| `SUPABASE_SERVICE_KEY` | Supabase 서비스 role 키 | ✅ |

---

## 📋 방법 1: Google Cloud Console (웹 UI)

### 1-1. Cloud Run 서비스 페이지 접속
```
https://console.cloud.google.com/run/detail/asia-northeast3/goldkey-crm
```

### 1-2. 환경변수 편집
1. **"편집 및 새 버전 배포"** 버튼 클릭
2. **"컨테이너" 탭** → **"변수 및 보안 비밀" 섹션** 확장
3. **"환경변수 추가"** 클릭

### 1-3. 환경변수 입력

**OPENAI_API_KEY**:
- 이름: `OPENAI_API_KEY`
- 값: `sk-proj-xxxxx` (로컬 .env 파일에서 복사)

**GEMINI_API_KEY**:
- 이름: `GEMINI_API_KEY`
- 값: `AIzaSyxxxxx` (로컬 .env 파일에서 복사)

**SUPABASE_URL**:
- 이름: `SUPABASE_URL`
- 값: `https://xxxxx.supabase.co` (로컬 .env 파일에서 복사)

**SUPABASE_SERVICE_KEY**:
- 이름: `SUPABASE_SERVICE_KEY`
- 값: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (로컬 .env 파일에서 복사)

### 1-4. 저장 및 배포
- **"배포"** 버튼 클릭
- 새 버전이 자동으로 배포됨 (약 2~3분 소요)

---

## 🖥️ 방법 2: gcloud CLI (명령어)

### 2-1. 환경변수 일괄 설정

**PowerShell 스크립트** (`set_crm_env_vars.ps1`):

```powershell
# set_crm_env_vars.ps1
# 실행: powershell -ExecutionPolicy Bypass -File "set_crm_env_vars.ps1"

# .env 파일에서 환경변수 읽기 (수동으로 값 입력)
$OPENAI_API_KEY = "sk-proj-xxxxx"  # 로컬 .env 파일에서 복사
$GEMINI_API_KEY = "AIzaSyxxxxx"    # 로컬 .env 파일에서 복사
$SUPABASE_URL = "https://xxxxx.supabase.co"  # 로컬 .env 파일에서 복사
$SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # 로컬 .env 파일에서 복사

# Cloud Run 환경변수 설정
gcloud run services update goldkey-crm `
    --region asia-northeast3 `
    --project gen-lang-client-0777682955 `
    --update-env-vars "OPENAI_API_KEY=$OPENAI_API_KEY,GEMINI_API_KEY=$GEMINI_API_KEY,SUPABASE_URL=$SUPABASE_URL,SUPABASE_SERVICE_KEY=$SUPABASE_SERVICE_KEY" `
    --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Cloud Run 환경변수 설정 완료"
} else {
    Write-Host "❌ 환경변수 설정 실패"
}
```

### 2-2. 실행 방법

1. **스크립트 파일 생성**:
   - 위 내용을 `d:\CascadeProjects\set_crm_env_vars.ps1`로 저장
   - `$OPENAI_API_KEY`, `$GEMINI_API_KEY`, `$SUPABASE_URL`, `$SUPABASE_SERVICE_KEY` 값을 로컬 `.env` 파일에서 복사하여 교체

2. **스크립트 실행**:
   ```powershell
   cd d:\CascadeProjects
   powershell -ExecutionPolicy Bypass -File "set_crm_env_vars.ps1"
   ```

---

## 🚀 Step 2: Docker 빌드 및 Cloud Run 배포

### 2-1. 배포 스크립트 실행

**기존 배포 스크립트 사용**:
```powershell
cd d:\CascadeProjects
powershell -ExecutionPolicy Bypass -File "deploy_crm.ps1"
```

**배포 과정**:
1. ✅ Artifact Registry 저장소 확인
2. ✅ Docker 이미지 빌드 (`Dockerfile.crm` 사용)
3. ✅ Cloud Run 배포 (goldkey-crm 서비스)
4. ✅ 배포 URL 확인 및 HTTP 응답 체크

**예상 소요 시간**: 5~10분

---

## 📦 Step 3: 배포 내용 확인

### 3-1. 포함된 파일

**RAG 관련 파일**:
- ✅ `hq_backend/engines/rag_engine.py` — RAG 검색 엔진
- ✅ `hq_backend/core/rag_ingestion.py` — 임베딩 파이프라인
- ✅ `blocks/crm_ai_chat_block.py` — CRM AI 채팅 블록
- ✅ `crm_app_impl.py` — RAG 채팅 통합 (Line 112, 1998-2001)

**환경변수 로드**:
- ✅ `python-dotenv` 라이브러리 (requirements.txt 포함)
- ✅ `.env` 파일 로드 로직 (`crm_ai_chat_block.py` Line 38-40)

**Supabase 벡터 DB**:
- ✅ 332개 청크 (법인컨설팅 167개, 배상책임 72개, 화재보험 93개)
- ✅ pgvector 확장 활성화
- ✅ IVFFlat 인덱스 구축 완료

---

## 🧪 Step 4: 배포 후 검증

### 4-1. Cloud Run 서비스 상태 확인

**gcloud 명령어**:
```powershell
gcloud run services describe goldkey-crm `
    --region asia-northeast3 `
    --project gen-lang-client-0777682955 `
    --format "value(status.url,status.conditions)"
```

**예상 출력**:
```
https://goldkey-crm-817097913199.asia-northeast3.run.app
Ready: True
```

### 4-2. 환경변수 확인

**gcloud 명령어**:
```powershell
gcloud run services describe goldkey-crm `
    --region asia-northeast3 `
    --project gen-lang-client-0777682955 `
    --format "yaml(spec.template.spec.containers[0].env)"
```

**확인 항목**:
- ✅ `OPENAI_API_KEY` 존재
- ✅ `GEMINI_API_KEY` 존재
- ✅ `SUPABASE_URL` 존재
- ✅ `SUPABASE_SERVICE_KEY` 존재

### 4-3. 웹 브라우저 접속 테스트

**URL**: https://goldkey-crm-817097913199.asia-northeast3.run.app

**확인 사항**:
1. ✅ CRM 앱 정상 로드
2. ✅ 로그인 화면 표시
3. ✅ 로그인 후 고객 목록 화면 표시
4. ✅ **"🤖 AI 상담 채팅 (RAG 전문 지식 검색)"** 섹션 표시
5. ✅ 카테고리 선택 드롭다운 (전체/법인컨설팅/배상책임/화재보험)
6. ✅ 질문 입력창 및 전송 버튼

### 4-4. RAG 기능 테스트

**테스트 질문 1**: "법인 임원 퇴직금 세무 처리 방법은?"
- **카테고리**: 법인컨설팅
- **예상 결과**: 법인 상담 자료에서 관련 내용 추출 + 출처 표시

**테스트 질문 2**: "공장 화재보험 120% 가입 룰이 뭔가요?"
- **카테고리**: 화재보험
- **예상 결과**: 화재보험 자료에서 120% 룰 설명 + 출처 표시

**테스트 질문 3**: "건물소유자 배상책임보험 가입 대상은?"
- **카테고리**: 배상책임
- **예상 결과**: 배상책임 자료에서 가입 대상 설명 + 출처 표시

---

## 🔍 Step 5: 로그 확인 (문제 발생 시)

### 5-1. Cloud Run 로그 확인

**gcloud 명령어**:
```powershell
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=goldkey-crm" `
    --project gen-lang-client-0777682955 `
    --limit 50 `
    --format "table(timestamp,severity,textPayload)"
```

### 5-2. 주요 확인 항목

**RAG 엔진 초기화 로그**:
```
✅ RAG 엔진 초기화 완료
```

**환경변수 로드 로그**:
```
✅ 환경변수 로드 성공
```

**오류 로그 예시**:
```
❌ 환경변수 미설정: OPENAI_API_KEY
❌ RAG 엔진 초기화 실패: ...
```

---

## 📊 Step 6: 성능 모니터링

### 6-1. Cloud Run 메트릭 확인

**Cloud Console**:
```
https://console.cloud.google.com/run/detail/asia-northeast3/goldkey-crm/metrics
```

**확인 항목**:
- ✅ 요청 수 (Requests)
- ✅ 응답 시간 (Latency)
- ✅ 오류율 (Error rate)
- ✅ 인스턴스 수 (Instance count)

### 6-2. 예상 성능 지표

| 항목 | 로컬 (localhost:8502) | Cloud Run |
|------|----------------------|-----------|
| RAG 엔진 초기화 | ~2초 | ~2초 |
| 질문 임베딩 생성 | ~0.5초 | ~0.5초 |
| 벡터 검색 | ~0.3초 | ~0.3초 |
| Gemini 답변 생성 | ~2~5초 | ~2~5초 |
| **총 응답 시간** | **~3~8초** | **~3~8초** |

---

## 🛠️ 트러블슈팅

### 문제 1: RAG 엔진 초기화 실패

**증상**:
```
❌ RAG 엔진 초기화 실패: 환경변수 미설정
```

**해결**:
1. Cloud Run 환경변수 설정 확인 (Step 1)
2. 환경변수 값이 올바른지 확인 (로컬 .env 파일과 비교)
3. Cloud Run 서비스 재배포

### 문제 2: Supabase 연결 실패

**증상**:
```
❌ Supabase 연결 실패: Invalid API key
```

**해결**:
1. `SUPABASE_URL` 확인 (https://xxxxx.supabase.co 형식)
2. `SUPABASE_SERVICE_KEY` 확인 (eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... 형식)
3. Supabase 대시보드에서 새 API 키 발급 (Legacy 키 비활성화 문제)

### 문제 3: OpenAI API 오류

**증상**:
```
❌ 임베딩 생성 실패: Error code: 401 - Incorrect API key
```

**해결**:
1. `OPENAI_API_KEY` 확인 (sk-proj- 또는 sk- 로 시작)
2. OpenAI 대시보드에서 API 키 활성화 상태 확인
3. 크레딧 잔액 확인 ($10 충전 확인)

### 문제 4: Gemini API 오류

**증상**:
```
❌ 답변 생성 실패: Gemini API error
```

**해결**:
1. `GEMINI_API_KEY` 확인 (AIzaSy 로 시작)
2. Google AI Studio에서 API 키 활성화 상태 확인
3. Gemini 1.5 Pro 모델 사용 가능 여부 확인

---

## 📋 체크리스트

### 배포 전
- [ ] 로컬 .env 파일 확인 (4개 환경변수)
- [ ] Cloud Run 환경변수 설정 (방법 1 또는 2)
- [ ] 최신 코드 커밋 (crm_app_impl.py, crm_ai_chat_block.py)

### 배포 중
- [ ] deploy_crm.ps1 실행
- [ ] Docker 이미지 빌드 성공
- [ ] Cloud Run 배포 성공
- [ ] HTTP 200 응답 확인

### 배포 후
- [ ] 웹 브라우저 접속 테스트
- [ ] AI 상담 채팅 섹션 표시 확인
- [ ] RAG 기능 테스트 (3개 질문)
- [ ] 로그 확인 (오류 없음)
- [ ] 성능 모니터링 (응답 시간 정상)

---

## 🎯 결론

**Phase 5 RAG 기능을 Cloud Run 운영 서버에 배포하는 전체 과정**:

1. ✅ **환경변수 설정**: Cloud Console 또는 gcloud CLI
2. ✅ **Docker 빌드 및 배포**: deploy_crm.ps1 실행
3. ✅ **배포 검증**: 웹 브라우저 + RAG 기능 테스트
4. ✅ **로그 확인**: Cloud Run 로그 모니터링
5. ✅ **성능 모니터링**: Cloud Run 메트릭 확인

**배포 완료 후 운영 URL에서 332개 전문 지식 조각을 활용한 AI 상담 채팅을 사용할 수 있습니다!** 🚀

---

**작성일**: 2026-03-30  
**작성자**: Windsurf Cascade AI  
**Phase**: Phase 5 Cloud Run 배포 가이드
