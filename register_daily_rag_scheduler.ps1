# -*- coding: utf-8 -*-
<#
.SYNOPSIS
    Windows Task Scheduler 등록 스크립트 - RAG 자동화 매일 자정 실행

.DESCRIPTION
    run_daily_rag_automation.py를 매일 00:00에 자동 실행하도록 Windows 작업 스케줄러에 등록

.NOTES
    작성일: 2026-03-31
    실행 권한: 관리자 권한 필요
#>

# 관리자 권한 확인
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "❌ 관리자 권한이 필요합니다." -ForegroundColor Red
    Write-Host "PowerShell을 관리자 권한으로 실행한 후 다시 시도하세요." -ForegroundColor Yellow
    exit 1
}

Write-Host "="*80 -ForegroundColor Cyan
Write-Host "🤖 RAG 자동화 스케줄러 등록" -ForegroundColor Cyan
Write-Host "="*80 -ForegroundColor Cyan

# 경로 설정
$projectRoot = "D:\CascadeProjects"
$pythonExe = "C:\Users\insus\AppData\Local\Programs\Python\Python312\python.exe"
$scriptPath = Join-Path $projectRoot "run_daily_rag_automation.py"
$logDir = Join-Path $projectRoot "hq_backend\knowledge_base\logs"
$logFile = Join-Path $logDir "rag_automation_$(Get-Date -Format 'yyyyMMdd').log"

# 로그 디렉토리 생성
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    Write-Host "✅ 로그 디렉토리 생성: $logDir" -ForegroundColor Green
}

# Python 실행 파일 확인
if (-not (Test-Path $pythonExe)) {
    Write-Host "❌ Python 실행 파일을 찾을 수 없습니다: $pythonExe" -ForegroundColor Red
    exit 1
}

# 스크립트 파일 확인
if (-not (Test-Path $scriptPath)) {
    Write-Host "❌ RAG 자동화 스크립트를 찾을 수 없습니다: $scriptPath" -ForegroundColor Red
    exit 1
}

Write-Host "`n📋 설정 정보:" -ForegroundColor Yellow
Write-Host "  Python: $pythonExe" -ForegroundColor White
Write-Host "  스크립트: $scriptPath" -ForegroundColor White
Write-Host "  로그 디렉토리: $logDir" -ForegroundColor White
Write-Host "  실행 시간: 매일 00:00 (자정)" -ForegroundColor White

# 작업 스케줄러 등록
$taskName = "GoldKey_RAG_Daily_Automation"
$taskDescription = "Goldkey AI Masters 2026 - RAG 자동화 (매일 자정 실행)"

Write-Host "`n🔧 작업 스케줄러 등록 중..." -ForegroundColor Yellow

try {
    # 기존 작업 삭제 (있을 경우)
    $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "  ⚠️  기존 작업 발견 - 삭제 후 재등록" -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    }

    # 작업 액션 정의 (Python 스크립트 실행)
    $action = New-ScheduledTaskAction `
        -Execute $pythonExe `
        -Argument "`"$scriptPath`"" `
        -WorkingDirectory $projectRoot

    # 트리거 정의 (매일 00:00)
    $trigger = New-ScheduledTaskTrigger -Daily -At "00:00"

    # 작업 설정
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Hours 2)

    # 작업 주체 (현재 사용자)
    $principal = New-ScheduledTaskPrincipal `
        -UserId $env:USERNAME `
        -LogonType Interactive `
        -RunLevel Highest

    # 작업 등록
    Register-ScheduledTask `
        -TaskName $taskName `
        -Description $taskDescription `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Force | Out-Null

    Write-Host "`n✅ 작업 스케줄러 등록 완료!" -ForegroundColor Green
    Write-Host "="*80 -ForegroundColor Cyan

    # 등록된 작업 정보 출력
    $registeredTask = Get-ScheduledTask -TaskName $taskName
    Write-Host "`n📊 등록된 작업 정보:" -ForegroundColor Yellow
    Write-Host "  작업 이름: $($registeredTask.TaskName)" -ForegroundColor White
    Write-Host "  상태: $($registeredTask.State)" -ForegroundColor White
    Write-Host "  다음 실행: $(($registeredTask | Get-ScheduledTaskInfo).NextRunTime)" -ForegroundColor White

    # 수동 실행 테스트 옵션
    Write-Host "`n💡 수동 실행 테스트:" -ForegroundColor Yellow
    Write-Host "  Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor Cyan

    # 작업 확인 명령
    Write-Host "`n💡 작업 확인:" -ForegroundColor Yellow
    Write-Host "  Get-ScheduledTask -TaskName '$taskName' | Get-ScheduledTaskInfo" -ForegroundColor Cyan

    # 로그 확인 명령
    Write-Host "`n💡 로그 확인:" -ForegroundColor Yellow
    Write-Host "  Get-Content '$logFile'" -ForegroundColor Cyan

    Write-Host "`n="*80 -ForegroundColor Cyan
    Write-Host "🎉 RAG 자동화 스케줄러 등록 완료!" -ForegroundColor Green
    Write-Host "="*80 -ForegroundColor Cyan

} catch {
    Write-Host "`n❌ 작업 스케줄러 등록 실패" -ForegroundColor Red
    Write-Host "오류: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 즉시 테스트 실행 여부 확인
Write-Host "`n❓ 지금 바로 테스트 실행하시겠습니까? (Y/N): " -NoNewline -ForegroundColor Yellow
$response = Read-Host

if ($response -eq "Y" -or $response -eq "y") {
    Write-Host "`n🚀 테스트 실행 중..." -ForegroundColor Yellow
    Start-ScheduledTask -TaskName $taskName
    Start-Sleep -Seconds 2
    
    Write-Host "`n📊 실행 상태 확인:" -ForegroundColor Yellow
    Get-ScheduledTask -TaskName $taskName | Get-ScheduledTaskInfo | Format-List
    
    Write-Host "`n💡 로그 파일 위치: $logFile" -ForegroundColor Cyan
} else {
    Write-Host "`n✅ 스케줄러 등록만 완료되었습니다." -ForegroundColor Green
    Write-Host "   다음 자동 실행: 내일 00:00 (자정)" -ForegroundColor White
}

Write-Host "`n"
