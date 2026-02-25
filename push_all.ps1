# push_all.ps1 — origin(GitHub) + hf(HuggingFace Space) 자동 push
# ─ push 실패 시 최대 3회 재시도
# ─ push 완료 후 양쪽 remote HEAD 일치 여부 검증
# ─ HuggingFace Space 빌드 상태 polling (완료까지 대기)
#
# 사용법:
#   .\push_all.ps1 "커밋 메시지"
#   .\push_all.ps1 "커밋 메시지" -SkipCommit    # 이미 커밋된 경우
#   .\push_all.ps1 "커밋 메시지" -SkipHFCheck   # HF 빌드 polling 생략
# ---------------------------------------------------------------------------
param(
    [string]$msg        = "update",
    [switch]$SkipCommit,
    [switch]$SkipHFCheck
)

Set-Location "D:\CascadeProjects"

$MAX_RETRY      = 3
$HF_POLL_SEC    = 20     # 빌드 상태 확인 간격(초)
$HF_POLL_MAX    = 30     # 최대 polling 횟수 (20초×30 = 최대 10분 대기)
$HF_SPACE_URL   = "https://huggingface.co/spaces/goldkey-rich/goldkey-ai"
$HF_API_URL     = "https://huggingface.co/api/spaces/goldkey-rich/goldkey-ai"

# ── 색상 출력 헬퍼 ──────────────────────────────────────────────────────────
function Write-Ok  { param($t) Write-Host "  ✅ $t" -ForegroundColor Green  }
function Write-Err { param($t) Write-Host "  ❌ $t" -ForegroundColor Red    }
function Write-Inf { param($t) Write-Host "  ℹ️  $t" -ForegroundColor Cyan   }
function Write-Wrn { param($t) Write-Host "  ⚠️  $t" -ForegroundColor Yellow }

# ── 단계 표시 ───────────────────────────────────────────────────────────────
function Write-Step { param($n,$t) Write-Host "`n[$n] $t" -ForegroundColor White }

# ── push 함수 (재시도 포함) ─────────────────────────────────────────────────
function Push-Remote {
    param([string]$remote)

    for ($i = 1; $i -le $MAX_RETRY; $i++) {
        Write-Inf "push $remote (시도 $i/$MAX_RETRY)..."
        $out = git push $remote main 2>&1
        $code = $LASTEXITCODE

        # git push는 성공해도 stderr에 출력 → 실제 실패 판단은 "error:" 포함 여부
        $hasError = ($out | Where-Object { $_ -match "^error:|^fatal:" }) -ne $null

        if ($code -eq 0 -or -not $hasError) {
            Write-Ok "$remote push 완료"
            return $true
        }

        Write-Err "$remote push 실패:"
        $out | Where-Object { $_ -match "error:|fatal:|rejected" } | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }

        if ($i -lt $MAX_RETRY) {
            Write-Wrn "${i}회 실패 → ${HF_POLL_SEC}초 후 재시도..."
            Start-Sleep -Seconds $HF_POLL_SEC
        }
    }

    Write-Err "$remote push $MAX_RETRY 회 모두 실패"
    return $false
}

# ── remote HEAD 검증 ────────────────────────────────────────────────────────
function Test-RemoteSync {
    param([string]$remote)

    $localHead  = git rev-parse HEAD
    $remoteHead = git ls-remote $remote main 2>$null | ForEach-Object { ($_ -split "\s+")[0] }

    if ($localHead -eq $remoteHead) {
        Write-Ok "$remote HEAD 일치 ($($localHead.Substring(0,7)))"
        return $true
    } else {
        Write-Err "$remote HEAD 불일치! local=$($localHead.Substring(0,7)) remote=$($remoteHead.Substring(0,[Math]::Min(7,$remoteHead.Length)))"
        return $false
    }
}

# ── HF Space 빌드 polling ────────────────────────────────────────────────────
function Wait-HFBuild {
    Write-Inf "HuggingFace Space 빌드 상태 polling 시작..."
    Write-Inf "Space URL: $HF_SPACE_URL"

    $prevStatus = ""
    for ($p = 1; $p -le $HF_POLL_MAX; $p++) {
        try {
            $resp = Invoke-RestMethod -Uri $HF_API_URL -TimeoutSec 10 -ErrorAction Stop
            $stage = $resp.runtime.stage
        } catch {
            $stage = "API_ERROR"
        }

        if ($stage -ne $prevStatus) {
            $ts = Get-Date -Format "HH:mm:ss"
            switch ($stage) {
                "BUILDING"  { Write-Inf "[$ts] 🔨 빌드 중... ($p/$HF_POLL_MAX)" }
                "RUNNING"   { Write-Ok  "[$ts] 🟢 빌드 완료 — 앱 정상 실행 중"; return $true }
                "STOPPED"   { Write-Wrn "[$ts] 🔴 앱 STOPPED 상태 (빌드 실패 가능성)" }
                "SLEEPING"  { Write-Wrn "[$ts] 💤 앱 SLEEPING — 접속하면 자동 재시작됩니다"; return $true }
                "ERROR"     { Write-Err "[$ts] ❌ 빌드 에러 — HF Space 로그를 확인하세요: $HF_SPACE_URL"; return $false }
                "API_ERROR" { Write-Wrn "[$ts] HF API 응답 없음 (네트워크 확인)" }
                default     { Write-Inf "[$ts] 상태: $stage" }
            }
            $prevStatus = $stage
        }

        if ($stage -eq "RUNNING" -or $stage -eq "SLEEPING") { return $true }
        if ($stage -eq "ERROR")  { return $false }

        Start-Sleep -Seconds $HF_POLL_SEC
    }

    Write-Wrn "최대 polling 횟수 초과 — HF Space를 직접 확인하세요: $HF_SPACE_URL"
    return $false
}

# ════════════════════════════════════════════════════════════════════════════
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  GoldKey AI — 자동 배포 스크립트 (origin + HuggingFace Space)" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Cyan

# ── STEP 1: commit ──────────────────────────────────────────────────────────
Write-Step "1/4" "커밋"
if (-not $SkipCommit) {
    git add -A
    $status = git status --porcelain
    if (-not $status) {
        Write-Inf "변경사항 없음 — commit 건너뜀"
    } else {
        git commit -m $msg
        if ($LASTEXITCODE -ne 0) {
            Write-Err "커밋 실패"; exit 1
        }
        Write-Ok "커밋 완료: $msg"
    }
} else {
    Write-Inf "-SkipCommit 플래그 — commit 건너뜀"
}

$commitHash = git rev-parse --short HEAD
Write-Inf "현재 HEAD: $commitHash"

# ── STEP 2: origin(GitHub) push ────────────────────────────────────────────
Write-Step "2/4" "GitHub(origin) push"
$originOk = Push-Remote "origin"

# ── STEP 3: hf(HuggingFace) push ───────────────────────────────────────────
Write-Step "3/4" "HuggingFace Space(hf) push"
$hfOk = Push-Remote "hf"

# ── STEP 4: 동기화 검증 ────────────────────────────────────────────────────
Write-Step "4/4" "Remote 동기화 검증"
$originSync = Test-RemoteSync "origin"
$hfSync     = Test-RemoteSync "hf"

# ── 결과 요약 ──────────────────────────────────────────────────────────────
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  배포 결과 요약" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ("  GitHub  (origin) : " + $(if ($originOk -and $originSync) { "✅ 완료" } else { "❌ 실패" }))
Write-Host ("  HF Space  (hf)   : " + $(if ($hfOk    -and $hfSync)     { "✅ 완료" } else { "❌ 실패" }))
Write-Host ("  커밋 해시         : $commitHash")

if (-not $SkipHFCheck -and $hfOk) {
    Write-Host ""
    Wait-HFBuild | Out-Null
}

if ($originOk -and $hfOk -and $originSync -and $hfSync) {
    Write-Host "`n  🎉 양쪽 배포 완료! 앱 주소: https://goldkey-rich-goldkey-ai.hf.space" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n  ⚠️  일부 실패 — 위 오류 내용을 확인하세요." -ForegroundColor Yellow
    exit 1
}
