# verify_crm_deployment.ps1 — CRM 앱 배포 검증 스크립트
# 실행: powershell -ExecutionPolicy Bypass -File "verify_crm_deployment.ps1"
# ─────────────────────────────────────────────────────────────────────────────
# [Phase 5] RAG 기능 배포 후 검증
# ─────────────────────────────────────────────────────────────────────────────

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

$service = "goldkey-crm"
$region = "asia-northeast3"
$project = "gen-lang-client-0777682955"
$expectedUrl = "https://goldkey-crm-817097913199.asia-northeast3.run.app"

Write-Host "=========================================="
Write-Host " [CRM 앱] 배포 검증"
Write-Host "=========================================="

# ── 1. Cloud Run 서비스 상태 확인 ──────────────────────────────────────────
Write-Host "`n[1/5] Cloud Run 서비스 상태 확인..."

$serviceStatus = gcloud run services describe $service `
    --region $region `
    --project $project `
    --format "value(status.conditions[0].status)" 2>&1

if ($LASTEXITCODE -eq 0 -and $serviceStatus -eq "True") {
    Write-Host "  ✅ 서비스 상태: Ready"
} else {
    Write-Host "  ❌ 서비스 상태: Not Ready"
    Write-Host "  상태: $serviceStatus"
}

# ── 2. 배포 URL 확인 ──────────────────────────────────────────────────────
Write-Host "`n[2/5] 배포 URL 확인..."

$actualUrl = gcloud run services describe $service `
    --region $region `
    --project $project `
    --format "value(status.url)" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ 배포 URL: $actualUrl"
    if ($actualUrl -eq $expectedUrl) {
        Write-Host "  ✅ URL 일치"
    } else {
        Write-Host "  ⚠️ URL 불일치 (예상: $expectedUrl)"
    }
} else {
    Write-Host "  ❌ URL 조회 실패"
}

# ── 3. 환경변수 확인 ──────────────────────────────────────────────────────
Write-Host "`n[3/5] 환경변수 확인..."

$envVars = gcloud run services describe $service `
    --region $region `
    --project $project `
    --format "json(spec.template.spec.containers[0].env)" 2>&1 | ConvertFrom-Json

$requiredEnvVars = @("OPENAI_API_KEY", "GEMINI_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_KEY")
$envVarNames = $envVars.spec.template.spec.containers[0].env | ForEach-Object { $_.name }

$missingVars = @()
foreach ($varName in $requiredEnvVars) {
    if ($envVarNames -contains $varName) {
        Write-Host "  ✅ ${varName} - 설정됨"
    } else {
        Write-Host "  ❌ ${varName} - 누락"
        $missingVars += $varName
    }
}

if ($missingVars.Count -gt 0) {
    Write-Host "`n  ⚠️ 누락된 환경변수가 있습니다. RAG 기능이 작동하지 않을 수 있습니다."
    Write-Host "  누락된 변수: $($missingVars -join ', ')"
    Write-Host "  해결 방법: set_crm_env_vars.ps1 실행 또는 Cloud Console에서 수동 설정"
}

# ── 4. HTTP 응답 확인 ──────────────────────────────────────────────────────
Write-Host "`n[4/5] HTTP 응답 확인..."

Start-Sleep -Seconds 5
$statusCode = & curl.exe -s -o NUL -w "%{http_code}" --max-time 30 "$actualUrl" 2>$null

if ($statusCode -eq "200") {
    Write-Host "  ✅ HTTP 응답: 200 OK"
} elseif ($statusCode -eq "000") {
    Write-Host "  ⚠️ HTTP 응답: 타임아웃 (앱 시작 중일 수 있음)"
} else {
    Write-Host "  ⚠️ HTTP 응답: $statusCode"
}

# ── 5. 최근 로그 확인 (RAG 엔진 초기화 여부) ────────────────────────────────
Write-Host "`n[5/5] 최근 로그 확인 (RAG 엔진 초기화)..."

$logs = gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$service" `
    --project $project `
    --limit 20 `
    --format "value(textPayload)" 2>&1

if ($LASTEXITCODE -eq 0) {
    $ragInitFound = $false
    $ragErrorFound = $false
    
    foreach ($log in $logs) {
        if ($log -match "RAG.*초기화.*완료|RAG.*engine.*ready") {
            $ragInitFound = $true
        }
        if ($log -match "RAG.*초기화.*실패|RAG.*engine.*failed|환경변수.*미설정") {
            $ragErrorFound = $true
            Write-Host "  ❌ RAG 엔진 오류 발견: $log"
        }
    }
    
    if ($ragInitFound) {
        Write-Host "  ✅ RAG 엔진 초기화 확인됨"
    } elseif ($ragErrorFound) {
        Write-Host "  ❌ RAG 엔진 초기화 실패"
    } else {
        Write-Host "  ⚠️ RAG 엔진 초기화 로그 없음 (아직 실행되지 않았을 수 있음)"
    }
} else {
    Write-Host "  ⚠️ 로그 조회 실패"
}

# ── 최종 결과 ─────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "=========================================="
Write-Host " 검증 완료"
Write-Host "=========================================="
Write-Host ""

if ($missingVars.Count -gt 0) {
    Write-Host "⚠️ 환경변수 누락으로 인해 RAG 기능이 작동하지 않을 수 있습니다."
    Write-Host ""
    Write-Host "다음 단계:"
    Write-Host "  1. set_crm_env_vars.ps1 실행하여 환경변수 설정"
    Write-Host "  2. 또는 Cloud Console에서 수동 설정:"
    Write-Host "     https://console.cloud.google.com/run/detail/${region}/${service}"
    Write-Host ""
} else {
    Write-Host "✅ 모든 환경변수가 설정되어 있습니다."
    Write-Host ""
    Write-Host "다음 단계:"
    Write-Host "  1. 브라우저에서 접속: $actualUrl"
    Write-Host "  2. 로그인 후 'AI 상담 채팅' 섹션 확인"
    Write-Host "  3. RAG 기능 테스트 (예: '법인 임원 퇴직금 세무 처리 방법은?')"
    Write-Host ""
}
