# Start trainers stack "i-croupier" in Docker Desktop.
# Does NOT stop other Docker projects (transfer, etc.).
# Run:  powershell -ExecutionPolicy Bypass -File .\start-i-croupier.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "==> Folder: $PWD" -ForegroundColor Cyan

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git not found. Install Git for Windows."
}
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker not found. Start Docker Desktop and wait until it is running."
}

Write-Host "==> Update branch cursor/docker-home-deploy-b2fe ..." -ForegroundColor Cyan
git fetch origin
git checkout cursor/docker-home-deploy-b2fe
git pull origin cursor/docker-home-deploy-b2fe

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "==> Created .env from .env.example" -ForegroundColor Yellow
    Write-Host "    Edit ACME_EMAIL / TRANSFER_* in .env if needed" -ForegroundColor Yellow
}

Write-Host "==> Recreate only this project (name: i-croupier), other stacks stay up ..." -ForegroundColor Cyan
docker compose up -d --build --remove-orphans

Write-Host ""
Write-Host "==> Done. Docker Desktop project: i-croupier" -ForegroundColor Green
Write-Host "    Trainers:  https://i-croupier.quiethouse.crazedns.ru" -ForegroundColor Green
Write-Host "    Local:     http://127.0.0.1:8000" -ForegroundColor Green
Write-Host ""
docker compose ps
Write-Host ""
Write-Host "Logs: docker compose logs -f web caddy" -ForegroundColor DarkGray
pause
