# Goldkey — 매일 저장소 스냅샷 (git bundle, 작업 트리 변경 없음)
# 작업 스케줄러: 매일 1회 이 스크립트 경로로 실행 등록
# 수동 실행:  powershell -ExecutionPolicy Bypass -File scripts\daily_repo_snapshot.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $Root ".git"))) {
    Write-Error "Not a git repository: $Root"
    exit 1
}
Set-Location $Root
$snapDir = Join-Path $Root ".snapshots"
New-Item -ItemType Directory -Force -Path $snapDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$bundle = Join-Path $snapDir "CascadeProjects_$stamp.bundle"
git bundle create $bundle --all
if ($LASTEXITCODE -ne 0) {
    Write-Error "git bundle failed"
    exit $LASTEXITCODE
}
# 오래된 번들 보관 개수 제한 (최근 14개만 유지)
Get-ChildItem $snapDir -Filter "CascadeProjects_*.bundle" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -Skip 14 |
    Remove-Item -Force -ErrorAction SilentlyContinue
Write-Host "[OK] Snapshot: $bundle"
