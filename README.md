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
- **Authentication** — all endpoints require an RS256 JWT bearer token issued by Keycloak; users can only access their own data (scoped by the `sub` claim)
- **CORS** — FastAPI's `CORSMiddleware` handles preflight `OPTIONS` requests; allowed origins are driven by `CORS_ALLOWED_ORIGINS` so production can point at the real frontend URL

## Stack

| Concern | Tool |
|---|---|
| Language | Python 3.14+ |
| Framework | [FastAPI](https://fastapi.tiangolo.com/) |
| ORM | [SQLModel](https://sqlmodel.tiangolo.com/) + SQLAlchemy |
| Database | PostgreSQL |
| Migrations | Alembic |
| Diagrams | seaborn + matplotlib |
| Authentication | Keycloak (RS256 JWT bearer tokens) |
| Tests | pytest + [testcontainers](https://testcontainers.com/) (real PostgreSQL) |
| Package manager | [uv](https://docs.astral.sh/uv/) |
| Container | Podman + [python-on-whales](https://gabrieldemarmiesse.github.io/python-on-whales/) |
| Deployment | Kubernetes (Talos Linux) |

## Project structure

```
app/
├── main.py              # FastAPI app entry point
├── config.py            # pydantic-settings (reads from .env)
├── database.py          # SQLAlchemy engine, session factory, get_session dependency
├── auth.py              # Keycloak JWT verification and user_id extraction
├── models/              # SQLModel table models (one file per metric)
├── schemas/             # Pydantic request/response schemas (one file per metric)
├── repositories/        # Repository classes for atomic CRUD operations
├── diagrams/            # Matplotlib SVG rendering functions
└── routers/
    ├── v1.py            # Aggregates all metric routers under /api/v1
    ├── blood_pressure.py
    ├── blood_glucose.py
    └── ketones.py

alembic/                 # Database migrations
api_docs/                # Released OpenAPI YAML specs (one per release × API version)
compose/keycloak/        # Pre-seeded Keycloak realm for local manual testing
scripts/
├── build.py             # Podman image build/push CLI (python-on-whales)
├── export_openapi.py    # Regenerate api_docs/ from every git tag
└── get_token.py         # Fetch a JWT for the seeded tester user
tests/                   # pytest suite (testcontainers spins up PostgreSQL)
```

## Development

### Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Podman](https://podman.io/) — required for tests (testcontainers spins up a real PostgreSQL) and for local manual testing via `podman compose`
- PostgreSQL — only when running the app outside of `podman compose`

### Setup

Install dependencies. Pick one of the following depending on what you need:

```bash
uv sync             # development: installs main + dev dependencies (pytest, ruff, pre-commit, testcontainers, …)
uv sync --no-dev    # production: installs only the main dependencies needed to run the app
```

Then, for a development checkout, install the git hooks and seed the env file:

```bash
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg   # commitizen check on commit messages
cp .env.example .env
```

Edit `.env` and point `DATABASE_URL` at your PostgreSQL instance. The full set of environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg2://postgres:postgres@localhost:5432/health_monitor` | SQLAlchemy database URL |
| `KEYCLOAK_URL` | `http://localhost:8080` | Keycloak base URL (JWKS is fetched from here) |
| `KEYCLOAK_REALM` | `health-monitor` | Keycloak realm name |
| `KEYCLOAK_JWKS_JSON` | _(unset)_ | Optional inline JWKS JSON — bypasses fetching from Keycloak. Used in container integration tests only. |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | Comma-separated list of origins permitted by the CORS middleware (e.g. `https://app.example.com,https://admin.example.com`). |

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
uv run pytest                                       # run all tests
uv run pytest tests/path/to/test.py::test_name      # run a single test
```

Tests use [testcontainers](https://testcontainers.com/) to spin up a real PostgreSQL container — Podman (or Docker) must be running. Each test gets a fresh database; tables are created and dropped per test via the autouse `setup_tables` fixture. Coverage is reported automatically (`--cov=app`) via `pyproject.toml`.

### Lint and format

```bash
uv run ruff check .
uv run ruff format .
```

### Generate API docs

OpenAPI YAML specs for every released version live in `api_docs/` and are regenerated automatically on each new release tag (the release workflow opens a PR with the updated `api_docs/`). To regenerate them manually:

```bash
uv run python scripts/export_openapi.py                       # write to api_docs/
uv run python scripts/export_openapi.py --output-dir /tmp/out # custom output directory
```

The script iterates over every git tag, checks each one out into a temporary worktree, imports the FastAPI app, and writes one YAML file per API version (e.g. `health-monitor-backend_0.5.0_api_v1.yaml`). Make sure all release tags are fetched locally (`git fetch --tags`) before running.

### Build the container image

The Podman build is driven by a click CLI in `scripts/build.py`:

```bash
uv run python scripts/build.py --help                          # see all options
uv run python scripts/build.py                                 # build with default tag (health-monitor-backend:latest)
uv run python scripts/build.py -t health-monitor-backend:dev   # custom tag
uv run python scripts/build.py --push                          # build and push (requires prior `podman login`)
```

The release workflow builds and pushes the image to Docker Hub (`docker.io/$DOCKER_HUB_USERNAME/health-monitor-backend`) on every release, tagged with the release version and `latest`.

### Running with Podman Compose

`compose.yaml` starts the full local stack: PostgreSQL 17, a Keycloak instance preloaded with a `health-monitor` realm and a tester user, the database-migrations job, and the application container.

**Prerequisites:** [Podman](https://podman.io/) with the `podman-compose` plugin (or the standalone `podman compose` command).

Build and start everything:

```bash
podman compose up --build
```

Once the stack is up:

- API: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`
- Keycloak: `http://localhost:8080` (admin console: `admin` / `admin`)

#### Authenticate against the API

The realm import (`compose/keycloak/realm.json`) pre-creates:

| Field | Value |
|---|---|
| Realm | `health-monitor` |
| Client | `health-monitor-swagger` (public, direct access grant) |
| User | `tester` / `tester` |

Fetch a JWT for the `tester` user:

```bash
uv run python scripts/get_token.py            # prints the token to stdout
uv run python scripts/get_token.py | pbcopy   # macOS: copy to clipboard
```

Then open `http://localhost:8000/docs`, click **Authorize**, paste the token into the `HTTPBearer` field, and use **Try it out** on any endpoint.

To target a different user or client, pass `--username`, `--password`, or `--client-id`. Run `uv run python scripts/get_token.py --help` for all options.

#### Stop the stack

```bash
podman compose down       # stop containers (PostgreSQL volume preserved)
podman compose down -v    # also remove the PostgreSQL volume
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

## Release process

Releases are fully automated by the `Release` GitHub workflow, which runs on every merge to `main`:

1. **commitizen** (`cz bump`) inspects the conventional commits since the last tag and determines the next semver version. If no commits warrant a bump, the workflow exits without releasing.
2. `pyproject.toml` and `CHANGELOG.md` are updated, committed, and pushed back to `main` along with a new semver tag.
3. A GitHub release is created from the tag, with release notes generated from the changelog.
4. The container image is built and pushed to Docker Hub, tagged with the release version and `latest`.
5. `scripts/export_openapi.py` regenerates the OpenAPI specs and opens a PR against `main` with the updated `api_docs/`.

Commits must follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification — the `commit-msg` pre-commit hook enforces this locally, and CI re-checks on every PR.

Branch naming convention:

- `feature/*` — new features
- `bugfix/*` — bug fixes
