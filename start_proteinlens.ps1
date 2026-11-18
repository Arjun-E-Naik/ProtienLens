Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Launching ProteinLens-OS (IIIT Nagpur Institutional Edition)" -ForegroundColor Green
Write-Host " Backend API : http://localhost:8000  (Swagger: /docs)" -ForegroundColor Yellow
Write-Host " Frontend UI : http://localhost:3000" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan

$RootDir = $PSScriptRoot
$VenvPython = Join-Path (Split-Path $RootDir -Parent) ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    $VenvPython = "python"
}

$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"

Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$BackendDir'; & '$VenvPython' -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
Start-Sleep -Seconds 3
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$FrontendDir'; npm run dev"
