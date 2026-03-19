# auto_rebuild_hf.ps1
# HF Space가 최신 코드를 반영하지 않을 때 강제 재빌드
# Windows 작업 스케줄러에 등록하여 매일 오전 9시 자동 실행
# ---------------------------------------------------------------------------
# 수동 실행: .\auto_rebuild_hf.ps1
# ---------------------------------------------------------------------------

Set-Location "D:\CascadeProjects"

$LOG_FILE     = "D:\CascadeProjects\auto_rebuild.log"
$HF_API_URL   = "https://huggingface.co/api/spaces/goldkey-rich/goldkey-ai"
$HF_SPACE_URL = "https://huggingface.co/spaces/goldkey-rich/goldkey-ai"
$MAX_RETRY    = 5
$RETRY_WAIT   = 20   # seconds
$HF_POLL_SEC  = 20
$HF_POLL_MAX  = 30

function Log {
    param($msg, $color = "White")
    $ts  = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] $msg"
    Write-Host $line -ForegroundColor $color
    Add-Content -Path $LOG_FILE -Value $line
}

# ── HF Space 현재 빌드 상태 조회 ───────────────────────────────────────────
function Get-HFStage {
    try {
        $resp = Invoke-RestMethod -Uri $HF_API_URL -TimeoutSec 10 -ErrorAction Stop
        return $resp.runtime.stage
    } catch {
        return "API_ERROR"
    }
}

# ── HF push (재시도 포함) ────────────────────────────────────────────────────
function Push-HF {
    for ($i = 1; $i -le $MAX_RETRY; $i++) {
        Log "HF push 시도 $i / $MAX_RETRY ..."
        $out      = git push hf main 2>&1
        $outStr   = $out -join "`n"
        $hasError = $outStr -match "^error:|^fatal:|rejected"
        # "Everything up-to-date" 도 성공으로 처리
        if (-not $hasError) {
            Log "HF push 성공" "Green"
            return $true
        }
        Log "HF push 실패: $outStr" "Red"
        if ($i -lt $MAX_RETRY) {
            Log "  ${RETRY_WAIT}초 후 재시도..." "Yellow"
            Start-Sleep -Seconds $RETRY_WAIT
        }
    }
    Log "HF push ${MAX_RETRY}회 모두 실패" "Red"
    return $false
}

# ── HF Space 빌드 완료 대기 ──────────────────────────────────────────────────
function Wait-HFRunning {
    Log "HF Space 빌드 상태 polling 시작..."
    $prev = ""
    for ($p = 1; $p -le $HF_POLL_MAX; $p++) {
        $stage = Get-HFStage
        if ($stage -ne $prev) {
            Log "  Stage: $stage ($p/$HF_POLL_MAX)"
            $prev = $stage
        }
        if ($stage -eq "RUNNING" -or $stage -eq "SLEEPING") {
            Log "앱 정상 실행 중 (RUNNING/SLEEPING)" "Green"
            return $true
        }
        if ($stage -eq "ERROR") {
            Log "빌드 오류 — HF Space 로그 확인: $HF_SPACE_URL" "Red"
            return $false
        }
        Start-Sleep -Seconds $HF_POLL_SEC
    }
    Log "Polling 타임아웃 — 수동 확인: $HF_SPACE_URL" "Yellow"
    return $false
}

# ── HEAD 동기화 확인 ────────────────────────────────────────────────────────
function Test-HFSync {
    $localHead  = git rev-parse HEAD
    $remoteHead = (git ls-remote hf main 2>$null) -split "\s+" | Select-Object -First 1
    if ($localHead -eq $remoteHead) {
        Log "HF HEAD 일치: $($localHead.Substring(0,7))" "Green"
        return $true
    }
    $rShort = if ($remoteHead -and $remoteHead.Length -ge 7) { $remoteHead.Substring(0,7) } else { "???" }
    Log "HF HEAD 불일치: local=$($localHead.Substring(0,7)) remote=$rShort" "Red"
    return $false
}

# ===========================================================================
Log "====== GoldKey HF 자동 강제 재빌드 시작 ======"

# STEP 1: 현재 HF 상태 확인
$stage = Get-HFStage
Log "현재 HF Stage: $stage"

# STEP 2: 로컬 ↔ HF HEAD 비교
$synced = Test-HFSync

if ($synced -and $stage -eq "RUNNING") {
    # 코드는 같고 앱도 실행 중 → 빈 커밋으로 강제 재빌드
    Log "코드 동기화됨 + RUNNING → 빈 커밋으로 강제 재빌드 트리거"
    $ts2 = Get-Date -Format "yyyyMMdd-HHmm"
    git commit --allow-empty -m "chore: auto force-rebuild $ts2" | Out-Null
}

# STEP 3: HF push
$pushOk = Push-HF

if (-not $pushOk) {
    Log "push 실패 → 종료" "Red"
    exit 1
}

# STEP 4: 빌드 완료 대기
$runOk = Wait-HFRunning

if ($runOk) {
    Log "====== 완료: 앱 정상 실행 중 ======" "Green"
    Log "URL: https://goldkey-rich-goldkey-ai.hf.space" "Green"
    exit 0
} else {
    Log "====== 경고: 빌드 결과 확인 필요 ======" "Yellow"
    exit 1
}
