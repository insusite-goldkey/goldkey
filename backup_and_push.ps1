# backup_and_push.ps1 — 백업 생성 + 최신 2개 유지 + GitHub & HF Space 동시 push
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

# 3. avatar.png 로컬 파일이 있으면 git에서 제거 (HF Space 바이너리 충돌 방지)
Set-Location $proj
$avatarPath = Join-Path $proj "avatar.png"
if (Test-Path $avatarPath) {
    Remove-Item $avatarPath -Force
    Write-Host "avatar.png 로컬 파일 삭제 완료"
}
$tracked = git ls-files avatar.png 2>$null
if ($tracked) {
    git rm --cached avatar.png --ignore-unmatch 2>$null
    Write-Host "avatar.png git 트래킹 제거 완료"
}

# 4. git add / commit
git add -A
$msg = "update: " + (Get-Date -Format "yyyy-MM-dd HH:mm") + " 자동 커밋"
git commit -m $msg

# 5. GitHub push (--force-with-lease: 로컬 커밋이 remote보다 뒤처지면 push 중단 — 수동 작업 보호)
git push origin main --force-with-lease
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ GitHub push 완료"
} else {
    # remote에 새 커밋 있으면 pull 후 재시도
    Write-Host "⚠️ push 실패 — remote 최신화 후 재시도 중..."
    git pull origin main --rebase
    git push origin main --force-with-lease
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ GitHub push 완료 (재시도 성공)"
    } else {
        Write-Host "⚠️ GitHub push 최종 실패 (exit code: $LASTEXITCODE) — 수동 확인 필요"
    }
}

# 6. HuggingFace Space push
git push hf main --force
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ HuggingFace Space push 완료"
    Write-Host "🔗 앱 확인: https://huggingface.co/spaces/goldkey-rich/goldkey-ai"
} else {
    Write-Host "⚠️ HF Space push 실패 (exit code: $LASTEXITCODE)"
}

# 7. 바탕화면 단축아이콘 자동 업데이트 (마지막 커밋 시간 반영)
powershell -ExecutionPolicy Bypass -File "$proj\update_shortcut.ps1"
