# Phase 5 RAG 기능 배포 최종 체크리스트

**배포 시작**: 2026-03-30 21:50  
**배포 상태**: 🔄 Cloud Build 진행 중 (Build ID: 8a0d432d-6e4a-438e-8709-942ee7ddc9fe)

---

## ✅ 배포 완료 후 즉시 실행할 작업

### 1단계: 배포 상태 확인

```powershell
# 빌드 상태 확인
gcloud builds list --project gen-lang-client-0777682955 --limit 1 --format "table(id,status,createTime,duration)"

# 예상 출력: STATUS = SUCCESS
```

### 2단계: 환경변수 설정 (필수)

**방법 A: 대화형 스크립트 (권장)**
```powershell
cd d:\CascadeProjects
powershell -ExecutionPolicy Bypass -File "set_crm_env_vars.ps1"
```

**방법 B: 직접 명령어**
```powershell
# .env 파일에서 값을 복사하여 아래 명령어 실행
gcloud run services update goldkey-crm `
    --region asia-northeast3 `
    --project gen-lang-client-0777682955 `
    --update-env-vars "OPENAI_API_KEY=sk-proj-xxxxx,GEMINI_API_KEY=AIzaSyxxxxx,SUPABASE_URL=https://xxxxx.supabase.co,SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." `
    --quiet
```

**방법 C: Google Cloud Console**
1. https://console.cloud.google.com/run/detail/asia-northeast3/goldkey-crm 접속
2. "편집 및 새 버전 배포" 클릭
3. "변수 및 보안 비밀" → 환경변수 4개 추가:
   - `OPENAI_API_KEY`
   - `GEMINI_API_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_KEY`
4. "배포" 클릭

### 3단계: 배포 검증

```powershell
cd d:\CascadeProjects
powershell -ExecutionPolicy Bypass -File "verify_crm_deployment.ps1"
```

**검증 항목**:
- ✅ Cloud Run 서비스 Ready 상태
- ✅ 배포 URL 확인
- ✅ 환경변수 4개 설정 확인
- ✅ HTTP 200 응답
- ✅ RAG 엔진 초기화 로그

### 4단계: 웹 브라우저 테스트

**URL**: https://goldkey-crm-817097913199.asia-northeast3.run.app

**확인 사항**:
1. CRM 앱 정상 로드
2. 로그인 화면 표시
3. 로그인 후 고객 목록 화면
4. **"🤖 AI 상담 채팅 (RAG 전문 지식 검색)"** 섹션 표시
5. 카테고리 선택 드롭다운 (전체/법인컨설팅/배상책임/화재보험)
6. 질문 입력창 및 전송 버튼

### 5단계: RAG 기능 테스트

**테스트 1**: "법인 임원 퇴직금 세무 처리 방법은?"
- 카테고리: 법인컨설팅
- 예상: 법인 상담 자료에서 답변 + 출처 (문서명 + 페이지)

**테스트 2**: "공장 화재보험 120% 가입 룰이 뭔가요?"
- 카테고리: 화재보험
- 예상: 화재보험 자료에서 답변 + 출처

**테스트 3**: "건물소유자 배상책임보험 가입 대상은?"
- 카테고리: 배상책임
- 예상: 배상책임 자료에서 답변 + 출처

---

## 🔍 문제 해결

### 문제 1: 환경변수 누락

**증상**: "❌ 환경변수 미설정: OPENAI_API_KEY"

**해결**:
1. `set_crm_env_vars.ps1` 실행
2. 또는 Cloud Console에서 수동 설정
3. 환경변수 설정 후 서비스 자동 재시작 (약 30초)

### 문제 2: RAG 엔진 초기화 실패

**증상**: "❌ RAG 엔진 초기화 실패"

**해결**:
1. 환경변수 값 확인 (로컬 .env 파일과 비교)
2. Supabase API 키 유효성 확인
3. OpenAI API 키 활성화 상태 확인
4. Cloud Run 로그 확인:
   ```powershell
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=goldkey-crm" `
       --project gen-lang-client-0777682955 `
       --limit 50
   ```

### 문제 3: HTTP 500 오류

**증상**: 웹 브라우저에서 "Internal Server Error"

**해결**:
1. Cloud Run 로그 확인 (위 명령어)
2. 환경변수 누락 여부 확인
3. Python 패키지 의존성 오류 확인
4. 필요 시 재배포:
   ```powershell
   cd d:\CascadeProjects
   powershell -ExecutionPolicy Bypass -File "deploy_crm.ps1"
   ```

---

## 📊 배포 내용 요약

### 변경된 파일
- ✅ `crm_app_impl.py` (Line 112, 1998-2001)
- ✅ `blocks/crm_ai_chat_block.py` (신규 생성)
- ✅ `hq_backend/engines/rag_engine.py` (기존)
- ✅ `hq_backend/core/rag_ingestion.py` (기존)

### Docker 이미지
- **이미지**: `asia-northeast3-docker.pkg.dev/gen-lang-client-0777682955/goldkey/goldkey-crm:v20260330-2150`
- **Dockerfile**: `Dockerfile.crm`
- **빌드 설정**: `cloudbuild_crm.yaml`

### Cloud Run 설정
- **서비스명**: goldkey-crm
- **리전**: asia-northeast3
- **메모리**: 1Gi
- **CPU**: 1
- **최소 인스턴스**: 0
- **최대 인스턴스**: 3
- **포트**: 8080

### RAG 지식 베이스
- **총 청크 수**: 332개
- **법인컨설팅**: 167개
- **배상책임**: 72개
- **화재보험**: 93개
- **벡터 DB**: Supabase pgvector
- **임베딩 모델**: OpenAI text-embedding-3-small (1536차원)
- **생성 모델**: Gemini 1.5 Pro (temperature=0.0)

---

## 📁 생성된 파일 목록

1. **`PHASE5_CLOUD_RUN_DEPLOYMENT_GUIDE.md`** — 상세 배포 가이드
2. **`PHASE5_DEPLOYMENT_SUMMARY.md`** — 배포 요약
3. **`PHASE5_FINAL_DEPLOYMENT_CHECKLIST.md`** — 최종 체크리스트 (현재 파일)
4. **`set_crm_env_vars.ps1`** — 환경변수 설정 스크립트
5. **`verify_crm_deployment.ps1`** — 배포 검증 스크립트
6. **`deploy_crm_with_env.ps1`** — 환경변수 포함 배포 스크립트
7. **`PHASE5_CRM_RAG_INTEGRATION_REPORT.md`** — 로컬 통합 완료 보고서
8. **`blocks/crm_ai_chat_block.py`** — RAG 채팅 블록

---

## 🎯 최종 목표

**운영 서버 https://goldkey-crm-817097913199.asia-northeast3.run.app 에서 332개 전문 지식 조각을 활용한 AI 상담 채팅이 정상 작동하는지 확인**

### 성공 기준
- ✅ 환경변수 4개 설정 완료
- ✅ RAG 엔진 초기화 성공
- ✅ AI 상담 채팅 UI 정상 표시
- ✅ 3개 테스트 질문 모두 정확한 답변 + 출처 표시
- ✅ 신뢰도 표시 (벡터 유사도 기반)
- ✅ 로컬 환경과 동일한 성능 (응답 시간 3~8초)

---

**작성일**: 2026-03-30  
**작성자**: Windsurf Cascade AI  
**Phase**: Phase 5 Cloud Run 배포 최종 체크리스트
