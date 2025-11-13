$ErrorActionPreference = 'Continue'

Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'uvicorn' } | ForEach-Object { Stop-Process -Id $_.Id -Force }
Get-Process -Name node -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'vite' } | ForEach-Object { Stop-Process -Id $_.Id -Force }
Get-Process -Name npm -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'vite' } | ForEach-Object { Stop-Process -Id $_.Id -Force }

Start-Process -FilePath "powershell" -ArgumentList "-NoExit","-Command","cd c:\Users\user\Documents\PersonalProject\disease_outbreak_prediction\backend; python -m uvicorn app.main:app --reload --port 8000"

Start-Process -FilePath "powershell" -ArgumentList "-NoExit","-Command","cd c:\Users\user\Documents\PersonalProject\disease_outbreak_prediction\web\outbreakiq; $env:VITE_API_BASE_URL='http://localhost:8000/api/v1'; npm run dev"