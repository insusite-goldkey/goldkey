# push_all.ps1 — origin(GitHub) + hf(HuggingFace Space) 동시 push
# 사용법: .\push_all.ps1 "커밋 메시지"
param([string]$msg = "update")

Set-Location "D:\CascadeProjects"

git add -A
git commit -m $msg
if ($LASTEXITCODE -ne 0) { Write-Host "변경사항 없음 또는 커밋 실패"; exit 0 }

Write-Host "▶ GitHub push..."
git push origin main
Write-Host "▶ HuggingFace Space push..."
git push hf main
Write-Host "✅ 양쪽 push 완료"
