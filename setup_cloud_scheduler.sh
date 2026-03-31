#!/bin/bash
# Cloud Scheduler 설정 스크립트 - RAG 자동화 매일 자정 실행
# 작성일: 2026-03-31

set -e

PROJECT_ID="gen-lang-client-0777682955"
REGION="asia-northeast3"
JOB_NAME="goldkey-rag-daily-automation"
SCHEDULE="0 0 * * *"  # 매일 00:00 (자정)
TIME_ZONE="Asia/Seoul"
SERVICE_URL="https://goldkey-ai-vje5ef5qka-du.a.run.app/api/rag/trigger"

echo "=================================="
echo "Cloud Scheduler 설정 시작"
echo "=================================="

# 1. Cloud Scheduler API 활성화
echo "1. Cloud Scheduler API 활성화 중..."
gcloud services enable cloudscheduler.googleapis.com --project=${PROJECT_ID}

# 2. 기존 작업 삭제 (있을 경우)
echo "2. 기존 작업 확인 및 삭제..."
if gcloud scheduler jobs describe ${JOB_NAME} --location=${REGION} --project=${PROJECT_ID} &>/dev/null; then
    echo "   기존 작업 발견 - 삭제 중..."
    gcloud scheduler jobs delete ${JOB_NAME} \
        --location=${REGION} \
        --project=${PROJECT_ID} \
        --quiet
    echo "   ✅ 기존 작업 삭제 완료"
else
    echo "   기존 작업 없음"
fi

# 3. 새 작업 생성
echo "3. 새 Cloud Scheduler 작업 생성 중..."
gcloud scheduler jobs create http ${JOB_NAME} \
    --location=${REGION} \
    --schedule="${SCHEDULE}" \
    --time-zone="${TIME_ZONE}" \
    --uri="${SERVICE_URL}" \
    --http-method=POST \
    --headers="Content-Type=application/json" \
    --message-body='{"trigger":"daily_automation","source":"cloud_scheduler"}' \
    --oidc-service-account-email="817097913199-compute@developer.gserviceaccount.com" \
    --project=${PROJECT_ID}

echo ""
echo "=================================="
echo "✅ Cloud Scheduler 설정 완료!"
echo "=================================="
echo "작업 이름: ${JOB_NAME}"
echo "실행 시간: 매일 00:00 (자정, 한국 시간)"
echo "대상 URL: ${SERVICE_URL}"
echo ""
echo "작업 확인:"
echo "  gcloud scheduler jobs describe ${JOB_NAME} --location=${REGION} --project=${PROJECT_ID}"
echo ""
echo "수동 실행 테스트:"
echo "  gcloud scheduler jobs run ${JOB_NAME} --location=${REGION} --project=${PROJECT_ID}"
echo ""
