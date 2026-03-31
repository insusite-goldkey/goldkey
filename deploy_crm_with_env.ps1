# deploy_crm_with_env.ps1 — 환경변수 포함 CRM 앱 배포 스크립트
# 실행: powershell -ExecutionPolicy Bypass -File "deploy_crm_with_env.ps1"
# ─────────────────────────────────────────────────────────────────────────────
# [Phase 5] RAG 기능 포함 배포 + 환경변수 자동 설정
# ─────────────────────────────────────────────────────────────────────────────

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

Write-Host "=========================================="
Write-Host " [CRM 앱] 환경변수 포함 배포"
Write-Host "=========================================="

# ── 환경변수 입력 ──────────────────────────────────────────────────────────
Write-Host "`n[1/3] 환경변수 입력 (로컬 .env 파일에서 복사)`n"

$OPENAI_API_KEY = Read-Host "OPENAI_API_KEY"
$GEMINI_API_KEY = Read-Host "GEMINI_API_KEY"
$SUPABASE_URL = Read-Host "SUPABASE_URL"
$SUPABASE_SERVICE_KEY = Read-Host "SUPABASE_SERVICE_KEY"

if ([string]::IsNullOrWhiteSpace($OPENAI_API_KEY) -or 
    [string]::IsNullOrWhiteSpace($GEMINI_API_KEY) -or 
    [string]::IsNullOrWhiteSpace($SUPABASE_URL) -or 
    [string]::IsNullOrWhiteSpace($SUPABASE_SERVICE_KEY)) {
    Write-Host "❌ 환경변수가 모두 입력되지 않았습니다."
    exit 1
}

# ── Cloud Run 환경변수 설정 ───────────────────────────────────────────────
Write-Host "`n[2/3] Cloud Run 환경변수 설정 중..."

gcloud run services update goldkey-crm `
    --region asia-northeast3 `
    --project gen-lang-client-0777682955 `
    --update-env-vars "OPENAI_API_KEY=$OPENAI_API_KEY,GEMINI_API_KEY=$GEMINI_API_KEY,SUPABASE_URL=$SUPABASE_URL,SUPABASE_SERVICE_KEY=$SUPABASE_SERVICE_KEY" `
    --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 환경변수 설정 실패"
    exit 1
}

Write-Host "✅ 환경변수 설정 완료"

# ── 배포 검증 ─────────────────────────────────────────────────────────────
Write-Host "`n[3/3] 배포 검증 중..."

Start-Sleep -Seconds 10

$serviceUrl = gcloud run services describe goldkey-crm `
    --region asia-northeast3 `
    --project gen-lang-client-0777682955 `
    --format "value(status.url)" 2>&1

Write-Host ""
Write-Host "=========================================="
Write-Host " ✅ 배포 완료!"
Write-Host " 🔗 URL: $serviceUrl"
Write-Host "=========================================="
Write-Host ""
Write-Host "다음 단계:"
Write-Host "  1. 브라우저에서 접속: $serviceUrl"
Write-Host "  2. 로그인 후 'AI 상담 채팅' 섹션 확인"
Write-Host "  3. RAG 기능 테스트"
Write-Host ""
