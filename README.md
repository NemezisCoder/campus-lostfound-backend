# Campus Lost&Found — Backend

FastAPI backend for Campus Lost&Found with REST API, Socket.IO, SQLAlchemy, Alembic migrations, PostgreSQL, and S3-compatible object storage support.

## Local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
# For pure local SQLite-style development, set DB_INIT_ON_STARTUP=true and DATABASE_URL accordingly.
uvicorn app.main:app --reload
# Open http://localhost:8000/docs
```


## Where to keep local keys

Do **not** put real keys into `.env.example`, `docker-compose.yml`, `README.md`, or `app/core/config.py`. Those files are tracked by git and may be changed by pull requests.

Keep real local values in `.env` at the repository root:

```bash
cp .env.example .env
# edit .env and put your real SECRET_KEY, OPENWEATHER_API_KEY, POSTGRES_PASSWORD, S3_SECRET_KEY, etc.
```

The `.env` file is ignored by git, so pulling or merging this PR should not overwrite it. Extra local env files such as `.env.local`, `.env.production.local`, or `.env.backup` are ignored too. If you previously stored real keys in `.env.example`, copy them into `.env` before switching branches or merging.

For an external backup outside the repository, you can run:

```bash
mkdir -p ~/campus-secrets-backup
cp .env ~/campus-secrets-backup/campus-lostfound-backend.env
```

## Container deployment shape

The compose stack is deployment-oriented and starts these services:

- `nginx` — public reverse proxy on port `80`.
- `frontend` — prebuilt frontend image, configured through `FRONTEND_IMAGE`.
- `backend` — FastAPI/Socket.IO backend image, configured through `BACKEND_IMAGE`.
- `db` — PostgreSQL with a readiness healthcheck.
- `minio` — S3-compatible storage, exposed only on loopback ports `9010` and `9011` for local testing.
- `minio-init` — one-shot bucket creation job, gated on MinIO health.
- `migrate` — one-shot `alembic upgrade head` job, gated on PostgreSQL health.

```bash
cp .env.example .env
# Adjust SECRET_KEY, POSTGRES_PASSWORD, S3_SECRET_KEY, BACKEND_IMAGE, and FRONTEND_IMAGE.
docker compose up --build
```

The backend container runs on port `8000`; Nginx proxies `/api/`, `/socket.io/`, `/robots.txt`, and `/sitemap.xml` to it. In the compose deployment path, database schema changes are applied by the `migrate` service, so `DB_INIT_ON_STARTUP=false` is the intended setting.

## Health checks

- `GET /api/v1/health` is a lightweight liveness endpoint.
- `GET /api/v1/health/ready` verifies database connectivity and, when `S3_ENABLED=true`, MinIO/S3 bucket access.

## Tests and checks

```bash
pip install -r requirements-dev.txt
python -m ruff check app tests
python -m pytest
```

## Project structure

```text
app/
  api/v1/routers/
    auth.py         # /api/v1/auth/*
    items.py        # /api/v1/items/*
    status.py       # /api/v1/statuses
    media.py        # /api/v1/media/*
    search.py       # /api/v1/search/*
    chat.py         # /api/v1/chat/*
    health.py       # /api/v1/health and /api/v1/health/ready
  core/config.py    # settings from environment/.env
  schemas/          # Pydantic schemas
  db/               # SQLAlchemy models, sessions, local init helper
  services/         # storage, weather, upload validation
alembic/            # Alembic migrations
nginx/              # reverse proxy config
```
