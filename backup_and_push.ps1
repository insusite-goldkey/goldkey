# backup_and_push.ps1 — 백업 생성 + 최신 2개 유지 + git push
$proj = "D:\CascadeProjects"
$dst  = Join-Path $proj ("app_backup_" + (Get-Date -Format "yyyyMMdd_HHmm") + ".py")

# 1. 백업 생성
Copy-Item (Join-Path $proj "app.py") $dst
Write-Host "백업 생성: $dst"

# 2. 최신 2개만 유지, 나머지 삭제
$backups = Get-ChildItem $proj -Filter "app_backup_*.py" | Sort-Object LastWriteTime -Descending
if ($backups.Count -gt 2) {
    $backups | Select-Object -Skip 2 | ForEach-Object {
        Remove-Item $_.FullName -Force
        Write-Host "삭제: $($_.Name)"
    }
}
Write-Host "유지 중인 백업: $(($backups | Select-Object -First 2).Name -join ', ')"

# 3. git add / commit / push
Set-Location $proj
git add -A
$msg = "update: " + (Get-Date -Format "yyyy-MM-dd HH:mm") + " 자동 커밋"
git commit -m $msg
git push origin main
Write-Host "GitHub push 완료"
