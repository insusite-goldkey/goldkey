# D:\CascadeProjects 1시간 단위 자동 백업 스크립트
# 작업 스케줄러에 등록하여 사용

$sourceDir = "D:\CascadeProjects"
$backupDir = "D:\CascadeProjects\backups"
$timestamp = Get-Date -Format "yyyyMMdd_HHmm"

# 백업 폴더 없으면 생성
if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir | Out-Null
}

# 백업할 파일 목록 (.py, .toml, .env, .txt)
$files = Get-ChildItem -Path $sourceDir -File | Where-Object {
    $_.Extension -in @(".py", ".toml", ".env", ".txt", ".bat", ".ps1")
}

foreach ($file in $files) {
    $destName = "$($file.BaseName)_$timestamp$($file.Extension)"
    Copy-Item -Path $file.FullName -Destination "$backupDir\$destName"
}

# 7일 이상 된 백업 자동 삭제
Get-ChildItem -Path $backupDir -File | Where-Object {
    $_.LastWriteTime -lt (Get-Date).AddDays(-7)
} | Remove-Item -Force

Write-Host "[$timestamp] 백업 완료: $($files.Count)개 파일" -ForegroundColor Green
