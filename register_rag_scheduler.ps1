# ==============================================================================
# RAG Auto Ingestion Task Scheduler Registration Script
# Automatically processes new PDFs in source_docs folder at midnight daily
# 
# Usage: Run PowerShell as Administrator, then execute:
#   powershell -ExecutionPolicy Bypass -File "register_rag_scheduler.ps1"
#
# Created: 2026-03-30
# ==============================================================================

Write-Host ""
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host " RAG Auto Ingestion Task Scheduler Registration" -ForegroundColor Cyan
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host ""

# 관리자 권한 확인
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script requires Administrator privileges." -ForegroundColor Red
    Write-Host ""
    Write-Host "Solution:" -ForegroundColor Yellow
    Write-Host "  1. Run PowerShell as Administrator" -ForegroundColor Yellow
    Write-Host "  2. Execute the following command:" -ForegroundColor Yellow
    Write-Host "     powershell -ExecutionPolicy Bypass -File `"register_rag_scheduler.ps1`"" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host "Administrator privileges confirmed." -ForegroundColor Green
Write-Host ""

# 작업 이름
$taskName = "GoldKey_RAG_Auto_Ingestion"

# 기존 작업 확인
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "WARNING: Task already exists: $taskName" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Do you want to delete and re-register? (Y/N): " -NoNewline
    $response = Read-Host
    
    if ($response -eq "Y" -or $response -eq "y") {
        Write-Host ""
        Write-Host "Deleting existing task..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        Write-Host "Existing task deleted successfully." -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "Task registration cancelled." -ForegroundColor Red
        Write-Host ""
        exit 0
    }
}

# XML 파일 경로
$xmlPath = Join-Path $PSScriptRoot "RAG_Auto_Ingestion_Task.xml"

if (-not (Test-Path $xmlPath)) {
    Write-Host "ERROR: XML file not found: $xmlPath" -ForegroundColor Red
    Write-Host ""
    exit 1
}

Write-Host "XML file confirmed: $xmlPath" -ForegroundColor Green
Write-Host ""

# Register task
Write-Host "Registering task scheduler..." -ForegroundColor Cyan
Write-Host ""

try {
    Register-ScheduledTask -Xml (Get-Content $xmlPath | Out-String) -TaskName $taskName -Force
    
    Write-Host "===============================================================================" -ForegroundColor Green
    Write-Host " Task Scheduler Registration Complete!" -ForegroundColor Green
    Write-Host "===============================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Name: $taskName" -ForegroundColor White
    Write-Host "Schedule: Daily at midnight (00:00)" -ForegroundColor White
    Write-Host "Command: python run_intelligent_rag.py" -ForegroundColor White
    Write-Host "Working Directory: d:\CascadeProjects" -ForegroundColor White
    Write-Host ""
    Write-Host "Key Settings:" -ForegroundColor Cyan
    Write-Host "  - Run whether user is logged on or not" -ForegroundColor White
    Write-Host "  - Wake computer to run (WakeToRun)" -ForegroundColor White
    Write-Host "  - Run on battery power" -ForegroundColor White
    Write-Host "  - Run only if network is available" -ForegroundColor White
    Write-Host "  - Maximum execution time: 2 hours" -ForegroundColor White
    Write-Host ""
    
    # 작업 상태 확인
    $task = Get-ScheduledTask -TaskName $taskName
    $taskInfo = Get-ScheduledTaskInfo -TaskName $taskName
    
    Write-Host "Task Status:" -ForegroundColor Cyan
    Write-Host "  State: $($task.State)" -ForegroundColor White
    Write-Host "  Last Run: $($taskInfo.LastRunTime)" -ForegroundColor White
    Write-Host "  Next Run: $($taskInfo.NextRunTime)" -ForegroundColor White
    Write-Host ""
    
    Write-Host "===============================================================================" -ForegroundColor Cyan
    Write-Host " Task Scheduler Management Commands" -ForegroundColor Cyan
    Write-Host "===============================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Open Task Scheduler:" -ForegroundColor Yellow
    Write-Host "   taskschd.msc" -ForegroundColor White
    Write-Host ""
    Write-Host "2. Run Task Manually (Test):" -ForegroundColor Yellow
    Write-Host "   Start-ScheduledTask -TaskName `"$taskName`"" -ForegroundColor White
    Write-Host ""
    Write-Host "3. Disable Task:" -ForegroundColor Yellow
    Write-Host "   Disable-ScheduledTask -TaskName `"$taskName`"" -ForegroundColor White
    Write-Host ""
    Write-Host "4. Enable Task:" -ForegroundColor Yellow
    Write-Host "   Enable-ScheduledTask -TaskName `"$taskName`"" -ForegroundColor White
    Write-Host ""
    Write-Host "5. Delete Task:" -ForegroundColor Yellow
    Write-Host "   Unregister-ScheduledTask -TaskName `"$taskName`" -Confirm:`$false" -ForegroundColor White
    Write-Host ""
    Write-Host "6. Check Task Status:" -ForegroundColor Yellow
    Write-Host "   Get-ScheduledTask -TaskName `"$taskName`" | Format-List *" -ForegroundColor White
    Write-Host ""
    Write-Host "7. Check Task History:" -ForegroundColor Yellow
    Write-Host "   Get-ScheduledTaskInfo -TaskName `"$taskName`"" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host "ERROR: Task registration failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Error Message:" -ForegroundColor Yellow
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    exit 1
}

Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host " Next Steps" -ForegroundColor Cyan
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Test with manual execution:" -ForegroundColor Yellow
Write-Host "   Start-ScheduledTask -TaskName `"$taskName`"" -ForegroundColor White
Write-Host ""
Write-Host "2. Check execution logs:" -ForegroundColor Yellow
Write-Host "   Task Scheduler -> $taskName -> History tab" -ForegroundColor White
Write-Host ""
Write-Host "3. Add new PDFs to source_docs folder and verify auto-processing" -ForegroundColor Yellow
Write-Host ""
Write-Host "4. Check RAG ingestion reports:" -ForegroundColor Yellow
Write-Host '   d:\CascadeProjects\RAG_INGESTION_REPORT_*.json' -ForegroundColor White
Write-Host ""
