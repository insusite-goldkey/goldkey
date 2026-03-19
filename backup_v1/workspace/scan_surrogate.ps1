# scan_surrogate.ps1 — PowerShell로 surrogate/UTF-8 오류 위치 탐지
$files = @(
    "D:\CascadeProjects\app.py",
    "D:\CascadeProjects\.streamlit\secrets.toml",
    "D:\CascadeProjects\workspace\insurance_bot.py"
)

foreach ($path in $files) {
    Write-Host "`n=== 스캔: $path ===" -ForegroundColor Cyan
    if (-not (Test-Path $path)) { Write-Host "  파일 없음"; continue }

    # 바이트 레벨 읽기
    $bytes = [System.IO.File]::ReadAllBytes($path)
    $enc = [System.Text.UTF8Encoding]::new($false, $true)  # throwOnInvalidBytes=true

    try {
        $null = $enc.GetString($bytes)
        Write-Host "  [UTF-8] 정상 ($($bytes.Length) bytes)" -ForegroundColor Green
    } catch {
        Write-Host "  [UTF-8 오류] $($_.Exception.Message)" -ForegroundColor Red
        # 오류 위치 근처 바이트 출력
        for ($i = 0; $i -lt $bytes.Length; $i++) {
            $b = $bytes[$i]
            # surrogate 범위: ED A0 80 ~ ED BF BF (UTF-16 surrogate를 잘못 UTF-8로 인코딩)
            if ($b -eq 0xED -and $i+2 -lt $bytes.Length) {
                $b2 = $bytes[$i+1]
                if ($b2 -ge 0xA0 -and $b2 -le 0xBF) {
                    Write-Host "  [surrogate 바이트] 위치=$i, 바이트: $($bytes[$i..($i+2)] | ForEach-Object { $_.ToString('X2') } | Join-String -Separator ' ')" -ForegroundColor Yellow
                    # 앞뒤 텍스트 컨텍스트 (안전하게 디코딩)
                    $start = [Math]::Max(0, $i-80)
                    $ctx_bytes = $bytes[$start..([Math]::Min($bytes.Length-1, $i+80))]
                    $ctx = [System.Text.Encoding]::UTF8.GetString(
                        ($ctx_bytes | ForEach-Object { if ($_ -ge 0x80 -and $_ -le 0xBF) { 0x3F } else { $_ } })
                    )
                    Write-Host "  문맥: ...$ctx..." -ForegroundColor Gray
                }
            }
        }
    }
}
Write-Host "`n=== 스캔 완료 ===" -ForegroundColor Cyan
