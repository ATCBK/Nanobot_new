
$ErrorActionPreference = "Stop"

Write-Host "Starting Nanobot Gateway..." -ForegroundColor Green

while ($true) {
    try {
        python -m nanobot gateway
    }
    catch {
        Write-Host "Nanobot crashed! Restarting in 5 seconds..." -ForegroundColor Red
        Start-Sleep -Seconds 5
    }
}
