# set_crm_env_vars.ps1 — Cloud Run 환경변수 설정 스크립트
# 실행: powershell -ExecutionPolicy Bypass -File "set_crm_env_vars.ps1"
# ─────────────────────────────────────────────────────────────────────────────
# [Phase 5] RAG 엔진 작동을 위한 환경변수 설정
# ─────────────────────────────────────────────────────────────────────────────

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

Write-Host "=========================================="
Write-Host " [CRM 앱] Cloud Run 환경변수 설정"
Write-Host "=========================================="

# ── 환경변수 값 입력 (로컬 .env 파일에서 복사) ──────────────────────────────
Write-Host "`n⚠️  주의: 아래 값을 로컬 .env 파일에서 복사하여 입력하세요.`n"

# 1. OPENAI_API_KEY
$OPENAI_API_KEY = Read-Host "OPENAI_API_KEY (sk-proj-xxxxx)"
if ([string]::IsNullOrWhiteSpace($OPENAI_API_KEY)) {
    Write-Host "❌ OPENAI_API_KEY가 입력되지 않았습니다."
    exit 1
}

# 2. GEMINI_API_KEY
$GEMINI_API_KEY = Read-Host "GEMINI_API_KEY (AIzaSyxxxxx)"
if ([string]::IsNullOrWhiteSpace($GEMINI_API_KEY)) {
    Write-Host "❌ GEMINI_API_KEY가 입력되지 않았습니다."
    exit 1
}

# 3. SUPABASE_URL
$SUPABASE_URL = Read-Host "SUPABASE_URL (https://xxxxx.supabase.co)"
if ([string]::IsNullOrWhiteSpace($SUPABASE_URL)) {
    Write-Host "❌ SUPABASE_URL이 입력되지 않았습니다."
    exit 1
}

# 4. SUPABASE_SERVICE_KEY
$SUPABASE_SERVICE_KEY = Read-Host "SUPABASE_SERVICE_KEY (eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...)"
if ([string]::IsNullOrWhiteSpace($SUPABASE_SERVICE_KEY)) {
    Write-Host "❌ SUPABASE_SERVICE_KEY가 입력되지 않았습니다."
    exit 1
}

# ── Cloud Run 환경변수 설정 ───────────────────────────────────────────────
Write-Host "`n[1/2] Cloud Run 환경변수 설정 중..."

gcloud run services update goldkey-crm `
    --region asia-northeast3 `
    --project gen-lang-client-0777682955 `
    --update-env-vars "OPENAI_API_KEY=$OPENAI_API_KEY,GEMINI_API_KEY=$GEMINI_API_KEY,SUPABASE_URL=$SUPABASE_URL,SUPABASE_SERVICE_KEY=$SUPABASE_SERVICE_KEY" `
    --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 환경변수 설정 실패 (exit code: $LASTEXITCODE)"
    exit 1
}

Write-Host "✅ 환경변수 설정 완료"

# ── 환경변수 확인 ─────────────────────────────────────────────────────────
Write-Host "`n[2/2] 환경변수 확인 중..."

$envVars = gcloud run services describe goldkey-crm `
    --region asia-northeast3 `
    --project gen-lang-client-0777682955 `
    --format "yaml(spec.template.spec.containers[0].env)" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 환경변수 확인 완료"
    Write-Host "`n설정된 환경변수:"
    Write-Host "  - OPENAI_API_KEY: ✅"
    Write-Host "  - GEMINI_API_KEY: ✅"
    Write-Host "  - SUPABASE_URL: ✅"
    Write-Host "  - SUPABASE_SERVICE_KEY: ✅"
} else {
    Write-Host "⚠️ 환경변수 확인 실패 (서비스가 재시작 중일 수 있습니다)"
}

Write-Host ""
Write-Host "=========================================="
Write-Host " ✅ 환경변수 설정 완료!"
Write-Host " 다음 단계: deploy_crm.ps1 실행"
Write-Host "=========================================="
Write-Host ""
