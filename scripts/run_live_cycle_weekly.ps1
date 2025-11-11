Param(
    [string]$RepoRoot = "$PSScriptRoot\..",
    [string]$PythonExe = "python",
    [string]$ScheduleName = "DiseaseOutbreakWeeklyRefresh",
    [string]$StartTime = "09:00",
    [string]$Day = "SUN"
)

Set-Location -Path $RepoRoot

$logDir = Join-Path $RepoRoot "reports\production"
if (!(Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$logPath = Join-Path $logDir "live_cycle_log.txt"

# Create a wrapper script that runs the live cycle and logs output
$runner = Join-Path $RepoRoot "scripts\run_live_cycle_once.ps1"
$runnerContent = @"
Param([string]$RepoRoot)
Set-Location -Path $RepoRoot
$logDir = Join-Path $RepoRoot "reports\production"
if (!(Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$logPath = Join-Path $logDir "live_cycle_log.txt"
Write-Output "`n==== $(Get-Date -Format o) ====" | Add-Content $logPath
$env:PAGER = "cat"
& "$PythonExe" "live_data\run_live_cycle.py" --mode realtime 2>&1 | Tee-Object -FilePath $logPath -Append | Out-Null
"@
Set-Content -Path $runner -Value $runnerContent -Encoding UTF8

# Create Windows Scheduled Task to run weekly
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$runner`" -RepoRoot `"$RepoRoot`""
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $Day -At $StartTime
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -Compatibility Win8 -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

try {
    Register-ScheduledTask -TaskName $ScheduleName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
    Write-Host "[SCHEDULED] $ScheduleName weekly on $Day at $StartTime"
}
catch {
    Write-Error "Failed to register scheduled task: $_"
}