# Campus Lost&Found — Backend (ЛР №2)

Базовая настройка сервера и маршрутизация (скелет без бизнес-логики) на **FastAPI**. Без Docker/Redis/тестов.

## Быстрый старт

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
# Открыть http://localhost:8000/docs
```

## Структура

```
app/
  api/v1/routers/
    auth.py         # /api/v1/auth/*
    items.py        # /api/v1/items/*
    status.py       # /api/v1/statuses
    media.py        # /api/v1/media/*
    search.py       # /api/v1/search/*
    chat.py         # /api/v1/chat/ws (WebSocket)
    health.py       # /api/v1/health
  core/config.py    # настройки из .env
  schemas/          # Pydantic-схемы
  models/           # модели БД (позже)
  services/         # доменная логика (позже)
  db/               # подключение к БД/миграции
migrations/         # Alembic
scripts/
```

## GitHub (обязательно)

```bash
git init
git add .
git commit -m "ЛР2: сервер и базовая маршрутизация (скелет, без Docker/Redis/тестов)"
git branch -M main
git remote add origin https://github.com/USERNAME/campus-lostfound-backend.git
git push -u origin main
```
