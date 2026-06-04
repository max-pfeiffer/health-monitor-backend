[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![codecov](https://codecov.io/gh/max-pfeiffer/health-monitor-backend/graph/badge.svg?token=0FVFqJBroP)](https://codecov.io/gh/max-pfeiffer/health-monitor-backend)
[![Unit Tests](https://github.com/max-pfeiffer/health-monitor-backend/actions/workflows/tests.yml/badge.svg)](https://github.com/max-pfeiffer/health-monitor-backend/actions/workflows/tests.yml)
[![Release](https://github.com/max-pfeiffer/health-monitor-backend/actions/workflows/release.yml/badge.svg)](https://github.com/max-pfeiffer/health-monitor-backend/actions/workflows/release.yml)

# Health Monitor Backend

## Development

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- PostgreSQL (production only — tests use SQLite)

### Setup

```bash
uv sync
pre-commit install
cp .env.example .env
```

Edit `.env` and set `DATABASE_URL` to your local PostgreSQL connection string, or leave it as-is to use SQLite during development.

### Run migrations

```bash
uv run alembic upgrade head
```

### Start the dev server

```bash
uv run uvicorn app.main:app --reload
```

API is available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Run tests

```bash
uv run pytest
```

Tests run against SQLite and do not require a running PostgreSQL instance.

### Lint and format

```bash
uv run ruff check .
uv run ruff format .
```
