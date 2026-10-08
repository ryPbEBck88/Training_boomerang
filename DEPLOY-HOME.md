# Запуск Training Boomerang на домашнем ПК (Docker)

Сайт поднимается в Docker на вашем компьютере и отдаётся наружу по адресу:

**https://i-croupier.quiethouse.crazedns.ru**

> Последний коммит на `main` сейчас от **июня 2026** — это нормально: более новых коммитов в репозитории нет. Скачивание «4 месяца назад» = актуальный код.

## 1. Что поставить на ПК

1. [Docker Desktop](https://www.docker.com/products/docker-desktop/) для Windows  
2. Git  
3. На роутере: **проброс портов 80 и 443** на IP вашего ПК в локальной сети  

## 2. Скачать свежий код

```powershell
cd %USERPROFILE%\Documents
git clone https://github.com/ryPbEBck88/Training_boomerang.git
cd Training_boomerang
git checkout main
git pull origin main
```

Если папка уже есть и «старая»:

```powershell
cd Training_boomerang
git fetch origin
git checkout main
git reset --hard origin/main
```

## 3. Настроить `.env`

```powershell
copy .env.example .env
notepad .env
```

Минимум для QuietHouse DDNS:

```env
DEBUG=0
ALLOWED_HOSTS=i-croupier.quiethouse.crazedns.ru,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://i-croupier.quiethouse.crazedns.ru
SITE_ADDRESS=i-croupier.quiethouse.crazedns.ru
ACME_EMAIL=ваш@email.ru
```

В панели QuietHouse / CrazyDNS создайте (или проверьте) хост **`i-croupier`** в зоне **`quiethouse.crazedns.ru`**, чтобы A-запись указывала на **белый IP** дома.

## 4. Запуск

Только локально (без домена, порт 8000):

```powershell
docker compose --profile local up -d --build
```

Открыть: http://localhost:8000

С интернетом через Caddy (HTTPS на 80/443):

```powershell
docker compose up -d --build
```

Логи:

```powershell
docker compose logs -f web caddy
```

Остановка:

```powershell
docker compose down
```

## 5. Проверка

1. С телефона (мобильный интернет, не Wi‑Fi дома): https://i-croupier.quiethouse.crazedns.ru  
2. Если сертификат не выдался — смотрите `docker compose logs caddy` (часто не открыты 80/443 или DNS ещё не указывает на дом)  
3. База SQLite лежит в папке проекта (`db.sqlite3`) — не удаляйте её при обновлении  

## 6. Обновление сайта с GitHub

```powershell
cd Training_boomerang
git pull origin main
docker compose up -d --build
```

## Частые проблемы

| Симптом | Что проверить |
|---|---|
| `DisallowedHost` | Имя в браузере есть в `ALLOWED_HOSTS` |
| CSRF / 403 на формах | То же имя с `https://` в `CSRF_TRUSTED_ORIGINS` |
| Сайт не открывается с улицы | Проброс 80/443, белый IP, DDNS обновил IP |
| «Старый код» | `git log -1` — на main последний коммит June 2026 |
