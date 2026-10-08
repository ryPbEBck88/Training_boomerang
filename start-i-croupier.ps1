# Запуск тренажёров на https://i-croupier.quiethouse.crazedns.ru
# Двойной клик или:  powershell -ExecutionPolicy Bypass -File .\start-i-croupier.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "==> Папка: $PWD" -ForegroundColor Cyan

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git не найден. Установите Git for Windows."
}
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker не найден. Запустите Docker Desktop и подождите, пока он станет зелёным."
}

Write-Host "==> Обновляю ветку cursor/docker-home-deploy-b2fe ..." -ForegroundColor Cyan
git fetch origin
git checkout cursor/docker-home-deploy-b2fe
git pull origin cursor/docker-home-deploy-b2fe

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "==> Создан .env из .env.example" -ForegroundColor Yellow
    Write-Host "    При необходимости укажите ACME_EMAIL в .env" -ForegroundColor Yellow
}

Write-Host "==> Останавливаю старый стек (если был) ..." -ForegroundColor Cyan
docker compose down 2>$null

Write-Host "==> Собираю и запускаю i-croupier (web + caddy) ..." -ForegroundColor Cyan
docker compose up -d --build

Write-Host ""
Write-Host "==> Готово. В Docker Desktop должен быть проект: i-croupier" -ForegroundColor Green
Write-Host "    Локально:  http://localhost   (или https://i-croupier.quiethouse.crazedns.ru с улицы)" -ForegroundColor Green
Write-Host ""
docker compose ps
Write-Host ""
Write-Host "Логи: docker compose logs -f web caddy" -ForegroundColor DarkGray
pause
