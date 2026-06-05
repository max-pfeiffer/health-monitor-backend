[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![codecov](https://codecov.io/gh/max-pfeiffer/health-monitor-backend/graph/badge.svg?token=0FVFqJBroP)](https://codecov.io/gh/max-pfeiffer/health-monitor-backend)
[![Unit Tests](https://github.com/max-pfeiffer/health-monitor-backend/actions/workflows/tests.yml/badge.svg)](https://github.com/max-pfeiffer/health-monitor-backend/actions/workflows/tests.yml)
[![Code quality](https://github.com/max-pfeiffer/health-monitor-backend/actions/workflows/code-quality.yml/badge.svg)](https://github.com/max-pfeiffer/health-monitor-backend/actions/workflows/code-quality.yml)
[![Release](https://github.com/max-pfeiffer/health-monitor-backend/actions/workflows/release.yml/badge.svg)](https://github.com/max-pfeiffer/health-monitor-backend/actions/workflows/release.yml)

# Health Monitor Backend

A Python REST API backend for tracking personal health metrics. It stores measurements for blood pressure, blood glucose, and blood ketones, and renders time-series diagrams of each metric as SVG images.

## Features

- **Blood pressure** — record systolic, diastolic, and pulse readings
- **Blood glucose** — record glucose values in mmol/L
- **Blood ketones** — record ketone values in mmol/L
- **Diagrams** — each metric has a chart endpoint that returns an SVG line chart with optional time-range filtering
- **Bulk import** — JSON import endpoint for each metric
- **Versioned API** — all endpoints live under `/api/v1/`

## Stack

| Concern | Tool |
|---|---|
| Language | Python |
| Framework | [FastAPI](https://fastapi.tiangolo.com/) |
| ORM | [SQLModel](https://sqlmodel.tiangolo.com/) + SQLAlchemy |
| Database | PostgreSQL |
| Migrations | Alembic |
| Diagrams | seaborn + matplotlib |
| Package manager | [uv](https://docs.astral.sh/uv/) |
| Container | Podman |
| Deployment | Kubernetes |

## Development

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- PostgreSQL (production only — tests use SQLite)

### Setup

Install dependencies. Pick one of the following depending on what you need:

```bash
uv sync             # development: installs main + dev dependencies (pytest, ruff, pre-commit, testcontainers, …)
uv sync --no-dev    # production: installs only the main dependencies needed to run the app
```

Then, for a development checkout, install the git hooks and seed the env file:

```bash
uv run pre-commit install
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

### Running with Podman Compose

`compose.yaml` starts a PostgreSQL 17 database and the application container together. This is useful for running the full stack locally without a separate database setup.

**Prerequisites:** [Podman](https://podman.io/) with the `podman-compose` plugin (or the standalone `podman compose` command).

Build and start both services:

```bash
podman compose up --build
```

The app runs migrations automatically on startup. Once running:

- API: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`

Stop and remove containers (data volume is preserved):

```bash
podman compose down
```

To also remove the persistent database volume:

```bash
podman compose down -v
```

### Git pre-commit hooks

The project uses [pre-commit](https://pre-commit.com/) to run Ruff lint and format checks on staged files before every commit. The hooks are defined in `.pre-commit-config.yaml` and enforced in CI by the **Code quality** workflow.

Install the hooks once after cloning:

```bash
uv run pre-commit install
```

Run all hooks against the whole repository on demand:

```bash
uv run pre-commit run --all-files
```

Update hook versions:

```bash
uv run pre-commit autoupdate
```
