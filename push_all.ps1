# push_all.ps1 - Auto deploy to GitHub (origin) + HuggingFace Space (hf)
# Retries up to 3 times on failure, verifies HEAD sync, polls HF build status.
#
# Usage:
#   .\push_all.ps1 "commit message"
#   .\push_all.ps1 "commit message" -SkipCommit   # skip git commit step
#   .\push_all.ps1 "commit message" -SkipHFCheck  # skip HF build polling
# ---------------------------------------------------------------------------
param(
    [string]$msg        = "update",
    [switch]$SkipCommit,
    [switch]$SkipHFCheck
)

Set-Location "D:\CascadeProjects"

$MAX_RETRY    = 3
$RETRY_WAIT   = 15    # seconds between retries
$HF_POLL_SEC  = 20    # seconds between build status checks
$HF_POLL_MAX  = 30    # max polls (20s x 30 = 10 min max)
$HF_SPACE_URL = "https://huggingface.co/spaces/goldkey-rich/goldkey-ai"
$HF_API_URL   = "https://huggingface.co/api/spaces/goldkey-rich/goldkey-ai"

function Log-Ok  { param($t) Write-Host "  [OK]  $t" -ForegroundColor Green  }
function Log-Err { param($t) Write-Host "  [ERR] $t" -ForegroundColor Red    }
function Log-Inf { param($t) Write-Host "  [..] $t"  -ForegroundColor Cyan   }
function Log-Wrn { param($t) Write-Host "  [!!] $t"  -ForegroundColor Yellow }
function Log-Step { param($n,$t) Write-Host "`n[$n] $t" -ForegroundColor White }

# Push to a remote with retry
function Push-Remote {
    param([string]$remote)
    for ($i = 1; $i -le $MAX_RETRY; $i++) {
        Log-Inf "Pushing to $remote (attempt $i / $MAX_RETRY)..."
        $out  = git push $remote main 2>&1
        $hasError = $null -ne ($out | Where-Object { $_ -match "^error:|^fatal:" })
        if (-not $hasError) {
            Log-Ok "Push to $remote succeeded"
            return $true
        }
        Log-Err "Push to $remote FAILED:"
        $out | Where-Object { $_ -match "error:|fatal:|rejected" } |
            ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
        if ($i -lt $MAX_RETRY) {
            Log-Wrn "Retry in $RETRY_WAIT sec..."
            Start-Sleep -Seconds $RETRY_WAIT
        }
    }
    Log-Err "Push to $remote failed after $MAX_RETRY attempts"
    return $false
}

# Verify local HEAD matches remote HEAD
function Test-Sync {
    param([string]$remote)
    $localHead  = git rev-parse HEAD
    $remoteHead = (git ls-remote $remote main 2>$null) -split "\s+" | Select-Object -First 1
    if ($localHead -eq $remoteHead) {
        Log-Ok "$remote HEAD matches local ($($localHead.Substring(0,7)))"
        return $true
    }
    $rShort = if ($remoteHead.Length -ge 7) { $remoteHead.Substring(0,7) } else { $remoteHead }
    Log-Err "$remote HEAD mismatch: local=$($localHead.Substring(0,7)) remote=$rShort"
    return $false
}

# Poll HF Space build status until RUNNING/SLEEPING/ERROR
function Wait-HFBuild {
    Log-Inf "Polling HF Space build status... ($HF_SPACE_URL)"
    $prev = ""
    for ($p = 1; $p -le $HF_POLL_MAX; $p++) {
        try {
            $resp  = Invoke-RestMethod -Uri $HF_API_URL -TimeoutSec 10 -ErrorAction Stop
            $stage = $resp.runtime.stage
        } catch {
            $stage = "API_ERROR"
        }
        if ($stage -ne $prev) {
            $ts = Get-Date -Format "HH:mm:ss"
            if ($stage -eq "BUILDING") {
                Log-Inf "[$ts] Building... ($p/$HF_POLL_MAX)"
            } elseif ($stage -eq "RUNNING") {
                Log-Ok  "[$ts] App is RUNNING"
                return $true
            } elseif ($stage -eq "SLEEPING") {
                Log-Wrn "[$ts] App SLEEPING (will wake on first request)"
                return $true
            } elseif ($stage -eq "STOPPED") {
                Log-Wrn "[$ts] App STOPPED - possible build failure"
            } elseif ($stage -eq "ERROR") {
                Log-Err "[$ts] Build ERROR - check HF Space logs: $HF_SPACE_URL"
                return $false
            } else {
                Log-Inf "[$ts] Stage: $stage"
            }
            $prev = $stage
        }
        if ($stage -eq "RUNNING" -or $stage -eq "SLEEPING") { return $true }
        if ($stage -eq "ERROR") { return $false }
        Start-Sleep -Seconds $HF_POLL_SEC
    }
    Log-Wrn "Polling timeout - check manually: $HF_SPACE_URL"
    return $false
}

# ===========================================================================
Write-Host "`n===========================================================" -ForegroundColor Cyan
Write-Host "  GoldKey AI - Auto Deploy (GitHub + HuggingFace Space)"      -ForegroundColor Cyan
Write-Host "===========================================================`n" -ForegroundColor Cyan

# STEP 1: Commit
Log-Step "1/4" "Commit"
if (-not $SkipCommit) {
    git add -A
    $dirty = git status --porcelain
    if (-not $dirty) {
        Log-Inf "Nothing to commit - skipping"
    } else {
        git commit -m $msg
        if ($LASTEXITCODE -ne 0) { Log-Err "Commit failed"; exit 1 }
        Log-Ok "Committed: $msg"
    }
} else {
    Log-Inf "SkipCommit flag set - skipping commit"
}
$hash = git rev-parse --short HEAD
Log-Inf "HEAD: $hash"

# STEP 2: Push origin (GitHub)
Log-Step "2/4" "Push -> GitHub (origin)"
$originOk = Push-Remote "origin"

# STEP 3: Push hf (HuggingFace)
Log-Step "3/4" "Push -> HuggingFace Space (hf)"
$hfOk = Push-Remote "hf"

# STEP 4: Verify sync
Log-Step "4/4" "Verify remote HEAD sync"
$originSync = Test-Sync "origin"
$hfSync     = Test-Sync "hf"

# Summary
Write-Host "`n===========================================================" -ForegroundColor Cyan
Write-Host "  Deploy Summary"                                               -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Cyan
$oStatus = if ($originOk -and $originSync) { "[OK]" } else { "[FAIL]" }
$hStatus = if ($hfOk     -and $hfSync)     { "[OK]" } else { "[FAIL]" }
Write-Host "  GitHub  (origin) : $oStatus"
Write-Host "  HF Space   (hf)  : $hStatus"
Write-Host "  Commit hash      : $hash"

if (-not $SkipHFCheck -and $hfOk) {
    Write-Host ""
    Wait-HFBuild | Out-Null
}

if ($originOk -and $hfOk -and $originSync -and $hfSync) {
    Write-Host "`n  [SUCCESS] Both remotes up to date! App: https://goldkey-rich-goldkey-ai.hf.space" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n  [FAILED] Some steps failed - review errors above" -ForegroundColor Yellow
    exit 1
}
