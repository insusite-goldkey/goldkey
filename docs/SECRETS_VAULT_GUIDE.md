# 🔐 [GP-VAULT] 금고 고정 배치표 — Goldkey AI Masters 2026
> **최상위 보안 운영 원칙 (SOP). 절대 삭제·변경 금지)**  
> 마지막 갱신: 2026-03-25

---

## 원칙: 시점(Timing)에 따른 2원 분리 원칙

| 시점 | 금고 | 도구 | 역할 |
|------|------|------|------|
| **배포(Deploy)** | 📂 금고 1 | GitHub Actions Secrets | 지휘관(Cloud Run)을 새로 임명·교체할 때 쓰는 통행증 |
| **실행(Runtime)** | 📂 금고 2 | Cloud Run 환경 변수 | 지휘관이 현장에서 꺼내 쓰는 실무 도구 |
| **내장(Built-in)** | 📂 금고 3 | Supabase RLS + GCS IAM | 창고·메모리 자체의 내장 잠금장치 |

---

## 📂 금고 1: 비서의 주머니 (GitHub Actions Secrets)

> `github.com/insusite-goldkey/goldkey` → Settings → Secrets and variables → Actions

| Key | 용도 | 필수 여부 | 비고 |
|-----|------|-----------|------|
| `GCP_SA_KEY` | GCP 서비스 계정 JSON — Cloud 성문 마스터키 | ✅ 필수 | 없으면 auth 단계 실패 |
| `GEMINI_API_KEY` | Gemini TTS/AI — 배포 시 Cloud Run에 주입 | ✅ 필수 | |
| `SUPABASE_URL` | Supabase DB URL — 배포 시 Cloud Run에 주입 | ✅ 필수 | |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase 서비스 롤 키 | ✅ 필수 | |
| `ENCRYPTION_KEY` | HMAC/Fernet 암호화 마스터키 | ✅ 필수 | |
| `ADMIN_CODE` | 관리자 로그인 코드 | ✅ 필수 | |
| `MASTER_CODE` | 마스터 로그인 코드 | ✅ 필수 | |
| `GCS_BUCKET_NAME` | GCS 영구 창고 버킷명 | ✅ 필수 | |
| `KAKAO_REST_API_KEY` | 카카오 REST API 키 | ✅ 필수 | |
| `KAKAO_API_KEY` | 카카오 JS API 키 | ✅ 필수 | |
| `KAKAO_SENDER_KEY` | 카카오 알림톡 발신 프로파일 키 | ✅ 필수 | |
| `SMS_API_KEY` | SMS API 키 | ✅ 필수 | |
| `SMS_API_SECRET` | SMS API 시크릿 | ✅ 필수 | |
| `SMS_SENDER_NUM` | SMS 발신 번호 | ✅ 필수 | |
| `FINLIFE_API_KEY` | 금융생활정보 API 키 | ⚡ 권장 | |
| `HEAD_API_URL` | head_api 서비스 주소 | ⚡ 권장 | 기본값: `http://127.0.0.1:18080` |
| `HEAD_API_USER_ID` | head_api 인증 ID | 선택 | 기본값: `ADMIN_MASTER` |
| `CORS_ALLOW_ORIGINS` | CORS 허용 오리진 | 선택 | 기본값: localhost |
| `KAKAO_REDIRECT_URI` | 카카오 OAuth 리다이렉트 URI | 선택 | 기본값: Cloud Run URL |
| `KAKAO_TEMPLATE_ID` | 카카오 알림톡 템플릿 ID | 선택 | 기본값: `goldkey_report_v1` |
| `MASTER_CODE` | 마스터 코드 | 선택 | 기본값: `kgagold6803` |

> ⚠️ **린터 경고 규칙 (SOP)**: `HEAD_API_URL` 등 일부 시크릿에 대해 IDE 린터가 "Context access might be invalid" 경고를 표시하는 것은 IDE가 GitHub Secrets의 실제 존재 여부를 정적으로 알 수 없기 때문이다. **금고 1에 값만 정확히 들어있다면 경고는 무시한다.**

---

## 📂 금고 2: 지휘관의 서랍 (Cloud Run 환경 변수)

> Cloud Run → `goldkey-ai` 서비스 → 환경 변수 탭  
> `deploy-cloudrun.yml`의 `--set-env-vars`로 자동 주입됨

### ✅ Vault 2 현황 대조표 (코드 참조 변수 vs 주입 여부)

| 변수명 | 사용 파일 | deploy-cloudrun.yml 주입 | 상태 |
|--------|-----------|--------------------------|------|
| `GEMINI_API_KEY` | hq_app_impl.py | ✅ 주입 | 정상 |
| `GOOGLE_API_KEY` | hq_app_impl.py | ❌ 누락 | `GEMINI_API_KEY`와 동일값 권장 |
| `SUPABASE_URL` | hq, crm, shared, db_utils | ✅ 주입 | 정상 |
| `SUPABASE_SERVICE_ROLE_KEY` | hq, crm, shared, db_utils | ✅ 주입 | 정상 |
| `SUPABASE_KEY` | shared_components.py | ❌ 누락 | `SUPABASE_SERVICE_ROLE_KEY` 폴백 |
| `ENCRYPTION_KEY` | hq, crm, shared, db_utils | ✅ 주입 | 정상 |
| `FERNET_KEY` | shared, crm_app_impl | ❌ 누락 | `ENCRYPTION_KEY` 자동 파생 (OK) |
| `ADMIN_CODE` | hq, crm, shared | ✅ 주입 | 정상 |
| `MASTER_CODE` | hq, crm, shared | ✅ 주입 | 정상 |
| `MASTER_NAME` | hq, shared | ❌ 누락 | 기본값 `이세윤` (OK) |
| `CRM_ADMIN_PW_HASH` | crm, shared | ❌ 누락 | `ADMIN_CODE` SHA-256 자동 파생 (OK) |
| `ADMIN_KEY` | hq_app_impl.py | ❌ 누락 | 운영 시 설정 권장 |
| `ADMIN_NOTIFY_PHONE` | shared_components.py | ❌ 누락 | 선택 (비상 알림) |
| `GCS_BUCKET_NAME` | hq, shared | ✅ 주입 | 정상 |
| `GCS_CACHE_BUCKET` | hq_app_impl.py | ❌ 누락 | `GCS_BUCKET_NAME` 폴백 (OK) |
| `STORAGE_BUCKET` | shared_components.py | ❌ 누락 | `gk-files` 기본값 |
| `HEAD_API_URL` | shared_components.py | ✅ 주입 | 정상 |
| `HQ_APP_URL` | shared_components.py | ❌ 누락 | `localhost:8501` 기본값 |
| `CRM_APP_URL` | shared_components.py | ❌ 누락 | `localhost:8502` 기본값 |
| `CRM_URL` | crm_app_impl.py | ❌ 누락 | `CRM_APP_URL` 폴백 |
| `HQ_API_URL` | shared_components.py | ❌ 누락 | `HQ_APP_URL/api/v1` 파생 |
| `GK_ANALYSIS_BRIDGE_SECRET` | shared_components.py | ❌ 누락 | 선택 (브리지 인증) |
| `FINLIFE_API_KEY` | hq_app_impl.py | ✅ 주입 | 정상 |
| `FSS_API_KEY` | hq_app_impl.py | ❌ 누락 | 기본값 `ae6f53ce` (공개키) |
| `HIRA_API_KEY` | hq_app_impl.py | ❌ 누락 | 심평원 API — 운영 시 설정 필요 |
| `KOSIS_API_KEY` | hq_app_impl.py | ❌ 누락 | 국가통계포털 — 운영 시 설정 필요 |
| `ONC_API_KEY` | hq_app_impl.py | ❌ 누락 | 항암제 API — 운영 시 설정 필요 |
| `LAW_API_OC` | hq_app_impl.py | ❌ 누락 | 기본값 `goldkey` (OK) |
| `KAKAO_REST_API_KEY` | hq_app_impl.py | ✅ 주입 | 정상 |
| `KAKAO_API_KEY` | hq_app_impl.py | ✅ 주입 | 정상 |
| `KAKAO_SENDER_KEY` | hq_app_impl.py | ✅ 주입 | 정상 |
| `KAKAO_TEMPLATE_ID` | hq_app_impl.py | ✅ 주입 | 정상 |
| `KAKAO_REDIRECT_URI` | hq_app_impl.py | ✅ 주입 | 정상 |
| `SMS_API_KEY` | hq_app_impl.py | ✅ 주입 | 정상 |
| `SMS_API_SECRET` | hq_app_impl.py | ✅ 주입 | 정상 |
| `SMS_SENDER_NUM` | hq_app_impl.py | ✅ 주입 | 정상 |
| `MS_CLIENT_ID` | crm_app_impl.py | ❌ 누락 | MS OAuth — 사용 시 설정 |
| `MS_CLIENT_SECRET` | crm_app_impl.py | ❌ 누락 | MS OAuth — 사용 시 설정 |
| `MS_TENANT_ID` | crm_app_impl.py | ❌ 누락 | 기본값 `common` |
| `MS_REDIRECT_URI` | crm_app_impl.py | ❌ 누락 | `CRM_APP_URL` 파생 |
| `APPLE_CALDAV_URL` | crm_app_impl.py | ❌ 누락 | Apple Calendar — 선택 |
| `CORS_ALLOW_ORIGINS` | hq_app_impl.py | ✅ 주입 | 정상 |

### 🚨 즉시 보완 권장 (누락 + 기본값 없거나 보안상 중요)

| 우선순위 | 변수명 | 이유 |
|----------|--------|------|
| 🔴 긴급 | `GOOGLE_API_KEY` | `GEMINI_API_KEY`와 동일값으로 추가 필요 |
| 🔴 긴급 | `HIRA_API_KEY` | 심평원 API 기능 작동 불가 |
| 🔴 긴급 | `KOSIS_API_KEY` | KOSIS 통계 기능 작동 불가 |
| 🟡 권장 | `HQ_APP_URL` | Cloud Run URL로 설정 (SSO 정상 작동) |
| 🟡 권장 | `CRM_APP_URL` | Cloud Run CRM URL (SSO 정상 작동) |
| 🟡 권장 | `ADMIN_KEY` | 관리자 접근 제어 강화 |
| 🟢 선택 | `ONC_API_KEY` | 항암제 검색 기능 |
| 🟢 선택 | `MS_CLIENT_ID/SECRET` | MS 캘린더 연동 시 |

---

## 📂 금고 3: 창고·메모리 내장 보안 (Built-in Auth)

| 서비스 | 보안 방식 | 설정 위치 |
|--------|-----------|-----------|
| **Supabase** | RLS (Row Level Security) — `agent_id` 기준 행 격리 | Supabase 대시보드 → Authentication → Policies |
| **GCS** | IAM — Cloud Run 서비스 계정(`817097913199-compute@`) 전용 쓰기 권한 | GCP Console → IAM & Admin |
| **Supabase Storage** | 버킷 정책 — 인증 사용자만 접근 | Supabase → Storage → Policies |

---

## ✅ 최종 검토 결과 요약

```
[금고 1] GitHub Secrets
  ├─ GCP_SA_KEY          : ⚠️ 수동 확인 필요 (없으면 CI/CD 전체 실패)
  ├─ 핵심 19개 시크릿    : deploy-cloudrun.yml에 정의됨
  └─ 판정: 파이프라인 정상 동작 중이면 OK

[금고 2] Cloud Run 환경 변수
  ├─ 주입 완료(✅): 19개
  ├─ 누락·기본값 있음(⚪): 18개 → 즉각 장애 없음
  └─ 누락·즉시 보완 필요(🔴): 3개 (GOOGLE_API_KEY, HIRA_API_KEY, KOSIS_API_KEY)

[금고 3] 내장 보안
  └─ Supabase RLS + GCS IAM → 별도 코드 변경 없음
```

---

## Cascade 운영 규칙 (이 가이드 적용 방법)

1. **새 환경변수 추가 시**: 반드시 Vault 1(GitHub Secrets) + Vault 2(deploy-cloudrun.yml `--set-env-vars`) 동시 등록.
2. **코드에서 `get_env_secret()` 호출 시**: 이 문서에 해당 키를 즉시 추가.
3. **배포 실패 시 1순위 체크**: Vault 1의 `GCP_SA_KEY` 존재 여부.
4. **런타임 오류 시 1순위 체크**: Vault 2의 해당 키 누락 여부.
