# deploy_crm.ps1 — [CRM 앱] goldkey-crm Cloud Run 전용 배포 스크립트
# 실행: powershell -ExecutionPolicy Bypass -File "D:\CascadeProjects\deploy_crm.ps1"
# ─────────────────────────────────────────────────────────────────────────────
# [3대 명칭 규칙]
#   [HQ 앱]  : app.py        → GCP 서비스: goldkey-ai  → backup_and_push.ps1
#   [CRM 앱] : crm_app.py    → GCP 서비스: goldkey-crm → deploy_crm.ps1 (현재 파일)
#   [공통]   : shared_components.py 등
# ─────────────────────────────────────────────────────────────────────────────

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
$PSDefaultParameterValues['Invoke-WebRequest:UseBasicParsing'] = $true

$proj      = "D:\CascadeProjects"
$project   = "gen-lang-client-0777682955"
$region    = "asia-northeast3"
$service   = "goldkey-crm"
$tag       = "v" + (Get-Date -Format "yyyyMMdd-HHmm")
$registry  = "$region-docker.pkg.dev/$project/goldkey/$service"
$image     = "${registry}:${tag}"

Set-Location $proj

Write-Host "=========================================="
Write-Host " [CRM 앱] Cloud Run 배포 시작"
Write-Host " 서비스명 : $service"
Write-Host " 이미지   : $image"
Write-Host " 리전     : $region"
Write-Host "=========================================="

# 1. Artifact Registry 저장소 존재 확인 (없으면 자동 생성)
Write-Host "`n[1/4] Artifact Registry 저장소 확인..."
$repoExists = gcloud artifacts repositories describe goldkey `
    --location=$region --project=$project 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  저장소 없음 → 자동 생성 중..."
    gcloud artifacts repositories create goldkey `
        --repository-format=docker `
        --location=$region `
        --project=$project `
        --description="Goldkey AI Docker images"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Artifact Registry 생성 실패"; exit 1
    }
    Write-Host "  ✅ 저장소 생성 완료"
} else {
    Write-Host "  ✅ 저장소 확인 완료"
}

# 2. Docker 이미지 빌드 (cloudbuild_crm.yaml + Dockerfile.crm 사용)
Write-Host "`n[2/4] 이미지 빌드 시작 (cloudbuild_crm.yaml → Dockerfile.crm)..."
gcloud builds submit `
    --config cloudbuild_crm.yaml `
    --substitutions "_IMAGE=$image" `
    --project $project `
    .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 이미지 빌드 실패 (exit code: $LASTEXITCODE)"; exit 1
}
Write-Host "✅ 이미지 빌드 완료: $image"

# 3. Cloud Run 배포
Write-Host "`n[3/4] Cloud Run 배포 시작..."
gcloud run deploy $service `
    --image $image `
    --region $region `
    --platform managed `
    --allow-unauthenticated `
    --memory 1Gi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 3 `
    --port 8080 `
    --project $project `
    --service-account "817097913199-compute@developer.gserviceaccount.com" `
    --set-env-vars "GK_APP_ID=crm" `
    --timeout 300 `
    --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Cloud Run 배포 실패 (exit code: $LASTEXITCODE)"; exit 1
}
Write-Host "✅ Cloud Run 배포 완료"

# 4. 배포 후 URL 확인 및 HTTP 응답 체크
Write-Host "`n[4/4] 배포 URL 확인..."
$serviceUrl = gcloud run services describe $service `
    --region $region `
    --project $project `
    --format "value(status.url)" 2>&1

Write-Host ""
Write-Host "=========================================="
Write-Host " ✅ [CRM 앱] 배포 완료!"
Write-Host " 🔗 CRM URL : $serviceUrl"
Write-Host " 🔗 HQ URL  : https://goldkey-ai-817097913199.asia-northeast3.run.app"
Write-Host "=========================================="

Start-Sleep -Seconds 15
$statusCode = & curl.exe -s -o NUL -w "%{http_code}" --max-time 30 "$serviceUrl" 2>$null
if ($statusCode -eq "200") {
    Write-Host "✅ CRM 앱 응답 정상 (HTTP 200)"
} else {
    Write-Host "⚠️ CRM 앱 응답: HTTP $statusCode (앱 시작 중이거나 네트워크 지연)"
}
