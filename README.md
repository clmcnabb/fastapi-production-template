# FastAPI Production Template (ML-ready)

Production-oriented FastAPI starter focused on architecture clarity, API versioning, auth, migrations, testing, and an ML-serving stub.

## What this repo demonstrates

- Clean architecture with separated API, service, and DB layers
- JWT auth with password hashing
- SQLAlchemy 2.0 + Alembic migrations
- Dockerized local development with Postgres
- ML inference endpoint with model preload at startup
- Health and readiness endpoints for deployment targets

## Architecture

- `app/api`: Versioned API routers and request handlers (thin controllers)
- `app/services`: Business logic (user auth and prediction)
- `app/db`: SQLAlchemy models, base metadata, and DB sessions
- `app/core`: Centralized settings, security, and logging config
- `app/ml`: Model loading and serialized dummy model

### Why this layout

- Service layer keeps route handlers lean and testable.
- Versioned API routing (`/api/v1`) reduces breaking-change risk.
- Dependency injection keeps auth and DB concerns reusable.
- Centralized settings enforce environment discipline.

## Quickstart (Local, using uv)

1. Create environment and install dependencies:

```bash
uv sync --extra dev
```

2. Create a local model file:

```bash
uv run python scripts/create_dummy_model.py
```

3. Copy environment file and edit if needed:

```bash
cp .env.example .env
```

4. Run API:

```bash
uv run uvicorn app.main:app --reload
```

5. Run migrations:

```bash
uv run alembic upgrade head
```

## Quickstart (Docker)

1. Copy env file:

```bash
cp .env.example .env
```

2. Build and start services:

```bash
docker compose up --build
```

3. Run migrations:

```bash
docker compose exec api alembic upgrade head
```

## Endpoints

- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`
- `POST /api/v1/auth/login`
- `POST /api/v1/users/`
- `GET /api/v1/users/me`
- `POST /api/v1/predict/`

## Environment variables

See `.env.example`:

- `ENVIRONMENT` (`local`/`staging`/`prod`)
- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `LOG_LEVEL`
- `MODEL_PATH`

## Deployment notes (AWS/Azure)

- Deploy as a container image behind a load balancer.
- Provide all env vars from your secret/config service.
- Use `/api/v1/health/live` and `/api/v1/health/ready` for probe checks.
- Route application logs to your platform log collector.

## Performance notes

- Model is preloaded at app startup to reduce first-request latency.
- SQLAlchemy engine uses `pool_pre_ping=True` for stale connection handling.
- Request middleware emits request duration and request ID.

## Project decisions and trade-offs

- Tests use in-memory SQLite for speed; production targets Postgres.
- Access tokens only (no refresh token flow) to keep template focused.
- Dummy model is intentionally simple to emphasize serving pattern.

## Common commands

```bash
make lint
make format
make typecheck
make test
```
