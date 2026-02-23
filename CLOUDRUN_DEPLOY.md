# Cloud Run 배포 가이드 — Goldkey AI Master

## 사전 준비 (1회만)

### 1. GCP CLI 설치 확인
```powershell
gcloud --version
```
없으면: https://cloud.google.com/sdk/docs/install

### 2. GCP 로그인
```powershell
gcloud auth login
gcloud config set project [YOUR_PROJECT_ID]
```

### 3. 필요한 API 활성화
```powershell
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

---

## 배포 방법 (회원 급증 시 실행)

### 방법 A: 소스 직접 배포 (가장 간단 — Docker 빌드 불필요)
```powershell
gcloud run deploy goldkey-ai `
  --source . `
  --region asia-northeast3 `
  --platform managed `
  --allow-unauthenticated `
  --memory 2Gi `
  --cpu 2 `
  --min-instances 1 `
  --max-instances 10 `
  --port 8080 `
  --set-env-vars "GEMINI_API_KEY=YOUR_KEY,SUPABASE_URL=YOUR_URL,SUPABASE_SERVICE_ROLE_KEY=YOUR_KEY,ADMIN_CODE=kgagold6803"
```

### 방법 B: Docker 빌드 후 배포
```powershell
# 1. 빌드
docker build -t gcr.io/[PROJECT_ID]/goldkey-ai .

# 2. 푸시
docker push gcr.io/[PROJECT_ID]/goldkey-ai

# 3. 배포
gcloud run deploy goldkey-ai `
  --image gcr.io/[PROJECT_ID]/goldkey-ai `
  --region asia-northeast3 `
  --platform managed `
  --allow-unauthenticated `
  --memory 2Gi `
  --cpu 2 `
  --min-instances 1 `
  --max-instances 10 `
  --port 8080
```

---

## 환경변수 설정 (HF Secrets와 동일하게)

| 변수명 | 값 |
|---|---|
| `GEMINI_API_KEY` | Gemini API 키 |
| `SUPABASE_URL` | https://idfzizqidhnpzbqioqqo.supabase.co |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase 서비스 롤 키 |
| `ADMIN_CODE` | kgagold6803 |

GCP 콘솔에서 설정:
> Cloud Run → goldkey-ai → 편집 → 변수 및 보안 비밀 탭

---

## 배포 후 확인

```powershell
# 서비스 URL 확인
gcloud run services describe goldkey-ai --region asia-northeast3 --format="value(status.url)"

# 로그 확인
gcloud run services logs read goldkey-ai --region asia-northeast3
```

---

## HF Spaces와 병행 운영

- **HF Spaces URL**: https://huggingface.co/spaces/goldkey-rich/goldkey-ai (현재 운영 중)
- **Cloud Run URL**: https://goldkey-ai-xxxx-an.a.run.app (배포 후 발급)
- 두 서버 모두 **동일한 Supabase DB/버킷** 공유 사용
- 트래픽 분산 또는 Cloud Run으로 완전 전환 선택 가능

---

## 비용 예상 (Cloud Run 서울 리전)

| 사용량 | 예상 비용 |
|---|---|
| 월 100명 · 하루 1시간 | ~$1~3/월 |
| 월 500명 · 하루 4시간 | ~$10~20/월 |
| min-instances=0 설정 시 | 접속 없으면 $0 |

> min-instances=1 설정 시 콜드스타트 없음 (응답 빠름), 소액 상시 과금

---

## 커스텀 도메인 연결 (플레이스토어 등록 시 필요)

```powershell
gcloud run domain-mappings create `
  --service goldkey-ai `
  --domain goldkey.co.kr `
  --region asia-northeast3
```

DNS: 도메인 업체에서 CNAME → ghs.googlehosted.com 설정

---

*최종 작성일: 2026-02-23 | 담당: 이세윤 / 010-3074-2616*
