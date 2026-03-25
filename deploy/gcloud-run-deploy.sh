#!/usr/bin/env bash
# GCP Cloud Run 배포 스크립트 (bash / Cloud Shell / WSL)
# 사용 전: PROJECT_ID, REGION, Artifact Registry 저장소명, 이미지 태그를 확인하세요.
set -euo pipefail

# ── 사용자 설정 ─────────────────────────────────────────
PROJECT_ID="${PROJECT_ID:-gen-lang-client-0777682955}"
REGION="${REGION:-asia-northeast3}"
AR_REPO="${AR_REPO:-goldkey-run}"
# 배포 후 서비스 URL (Cloud Run 콘솔에서 확인하거나 아래처럼 고정 도메인 사용)
HQ_URL="${HQ_URL:-https://goldkey-ai-817097913199.asia-northeast3.run.app}"
CRM_URL="${CRM_URL:-https://goldkey-crm-817097913199.asia-northeast3.run.app}"
# CRM↔HQ API 브리지 공유 비밀 (양쪽 동일 값)
BRIDGE_SECRET="${GK_ANALYSIS_BRIDGE_SECRET:-change-me-in-production}"
SUPABASE_URL="${SUPABASE_URL:-}"
SUPABASE_SERVICE_ROLE_KEY="${SUPABASE_SERVICE_ROLE_KEY:-${SUPABASE_KEY:-}}"
ENCRYPTION_KEY="${ENCRYPTION_KEY:-gk_token_secret_2026}"
HEAD_API_USER_ID="${HEAD_API_USER_ID:-ADMIN_MASTER}"
CORS_ALLOW_ORIGINS="${CORS_ALLOW_ORIGINS:-http://localhost:8501,http://localhost:8502}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
echo "Project: $PROJECT_ID  Region: $REGION"

gcloud config set project "$PROJECT_ID"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --project "$PROJECT_ID"

gcloud artifacts repositories describe "$AR_REPO" --location="$REGION" --project "$PROJECT_ID" >/dev/null 2>&1 \
  || gcloud artifacts repositories create "$AR_REPO" \
       --repository-format=docker \
       --location="$REGION" \
       --description="Goldkey Cloud Run images"

IMAGE_BASE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}"

# ── 빌드 & 푸시 ─────────────────────────────────────────
echo ">>> Building HQ (goldkey-ai)..."
gcloud builds submit \
  --project "$PROJECT_ID" \
  --config=deploy/cloudbuild-hq.yaml \
  --substitutions=_IMAGE="${IMAGE_BASE}/goldkey-ai:latest"

echo ">>> Building CRM (goldkey-crm)..."
gcloud builds submit \
  --project "$PROJECT_ID" \
  --config=deploy/cloudbuild-crm.yaml \
  --substitutions=_IMAGE="${IMAGE_BASE}/goldkey-crm:latest"

# ── Cloud Run 배포 ─────────────────────────────────────
echo ">>> Deploy HQ service: goldkey-ai"
gcloud run deploy goldkey-ai \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --image "${IMAGE_BASE}/goldkey-ai:latest" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --max-instances 10 \
  --set-env-vars "HQ_APP_URL=${HQ_URL},CRM_APP_URL=${CRM_URL},GK_ANALYSIS_BRIDGE_SECRET=${BRIDGE_SECRET},SUPABASE_URL=${SUPABASE_URL},SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY},ENCRYPTION_KEY=${ENCRYPTION_KEY},HEAD_API_USER_ID=${HEAD_API_USER_ID},HEAD_API_URL=http://127.0.0.1:18080,CORS_ALLOW_ORIGINS=${CORS_ALLOW_ORIGINS}"

echo ">>> Deploy CRM service: goldkey-crm"
gcloud run deploy goldkey-crm \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --image "${IMAGE_BASE}/goldkey-crm:latest" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --max-instances 10 \
  --set-env-vars "HQ_APP_URL=${HQ_URL},CRM_APP_URL=${CRM_URL},HQ_API_URL=${HQ_URL}/api/v1,GK_ANALYSIS_BRIDGE_SECRET=${BRIDGE_SECRET},HEAD_API_URL=${HQ_URL}/api"

echo "Done. URLs (배포 후 실제 URL이 다르면 위 서비스에 --update-env-vars 로 맞추세요):"
echo "  HQ:  ${HQ_URL}"
echo "  CRM: ${CRM_URL}"
