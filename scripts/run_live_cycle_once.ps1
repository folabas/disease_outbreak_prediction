Param([string]c:\Users\user\Documents\PersonalProject\disease_outbreak_prediction)
Set-Location -Path c:\Users\user\Documents\PersonalProject\disease_outbreak_prediction
c:\Users\user\Documents\PersonalProject\disease_outbreak_prediction\reports\production = Join-Path c:\Users\user\Documents\PersonalProject\disease_outbreak_prediction "reports\production"
if (!(Test-Path c:\Users\user\Documents\PersonalProject\disease_outbreak_prediction\reports\production)) { New-Item -ItemType Directory -Path c:\Users\user\Documents\PersonalProject\disease_outbreak_prediction\reports\production | Out-Null }
c:\Users\user\Documents\PersonalProject\disease_outbreak_prediction\reports\production\live_cycle_log.txt = Join-Path c:\Users\user\Documents\PersonalProject\disease_outbreak_prediction\reports\production "live_cycle_log.txt"
Write-Output "
==== 2025-11-09T09:52:21.0511383+00:00 ====" | Add-Content c:\Users\user\Documents\PersonalProject\disease_outbreak_prediction\reports\production\live_cycle_log.txt
 = "cat"
& "python" "live_data\run_live_cycle.py" --mode realtime 2>&1 | Tee-Object -FilePath c:\Users\user\Documents\PersonalProject\disease_outbreak_prediction\reports\production\live_cycle_log.txt -Append | Out-Null
