# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Python backend service for health monitoring.

### Purpose

The application should capture and store the following health metrics:
- blood pressure
- blood glucose
- blood ketones

It provides REST API endpoints for storing the health metrics data. 
It also provides REST API endpoints which render diagrams for the health metrics as images.

Users log into the frontend application with Keycloak. The logged-in user can only do CRUD operations of his own data.

### Key Consumers

The application provides a REST API backend for frontend applications.
Frontend applications create, update, delete and read data using the REST API

### Deployment Environment

The application is running in a Container on Kubernetes.
The Kubernetes cluster is build with Talos Linux.
No cloud provider is used.
The application will run 24/7.

### Expected Integrations

- Data is stored in a database.
- Database: PostgreSQL
- Keycloak as identity provider

### Git Repository
- The git repository for this project is hosted on GitHub: https://github.com/max-pfeiffer/health-monitor-backend
- The default branch is main. main branch is protected.
- Features need to be created on branches with feature/* pattern
- Bug fixes need to be created on branches with bugfix/* pattern

#### GitHub Workflows
- Git pre-commit hooks are run using GitHub actions and locally when a new pull request is created or updated (local hooks + CI checks on PR)
- Unit test should be run always using GitHub actions when a new pull request is created or updated
- Releases are managed by `release-please` (`googleapis/release-please-action`, `python` release type, manifest mode via `release-please-config.json` + `.release-please-manifest.json`)
- On every push to main, release-please maintains an open "release PR" that accumulates the pending conventional commits and stages the next version bump in `pyproject.toml` plus the `CHANGELOG.md` update
- Merging that release PR is what cuts a release: release-please bumps `pyproject.toml`, updates `CHANGELOG.md`, pushes a semver tag (no `v` prefix, e.g. `0.9.0`), and creates the GitHub release with notes from the changelog
- If no commits since the last tag warrant a bump, no release PR is opened and nothing is released
- release-please runs under a GitHub App token so the tag it creates triggers the tag-based downstream workflows (`GITHUB_TOKEN`-created tags would not)
- On a release tag, the container image is built and pushed to Docker Hub, tagged with the release version and `latest`
- On a release tag, the OpenAPI specs are regenerated and a PR is opened against main with the updated `api_docs/`
- In GitHub Actions environment variable DOCKER_HUB_USERNAME is used as Docker Hub username
- In GitHub Actions environment variable DOCKER_HUB_TOKEN is used as Docker Hub password

## Architecture

### Project Structure
- `.github/` — GitHub workflows
- `app/` — main application package
- `app/main.py` — FastAPI app entry point
- `app/config.py` — settings via pydantic-settings (reads from `.env`)
- `app/database.py` — SQLAlchemy engine, session factory, `get_session` dependency
- `app/models/` — SQLModel table models (one file per health metric)
- `app/schemas/` — Pydantic request/response schemas (one file per health metric)
- `app/repositories/` — repository classes for atomic CRUD operations (one file per health metric)
- `app/diagrams/` — Matplotlib SVG rendering functions (one file per health metric)
- `app/routers/v1.py` — v1 API router (aggregates all metric routers under `/api/v1`)
- `app/routers/` — FastAPI routers (one file per health metric)
- `alembic/` — database migrations
- `tests/` — pytest tests
- `scripts/` — scripts used for CI/CD tasks (`build.py` builds/pushes the container image, `export_openapi.py` generates OpenAPI YAML specs)

### Code Structure
- Use Repository pattern for data CRUD operations
- Data CRUD operations need to be atomic
- Use SQLAlchemy context managers for database CRUD operations

### API Design
- The API is versioned, we have a separate router for each API version
- The root endpoint of the application forwards to the API docs
- REST endpoints follow `/api/v1/<resource>` naming
- Diagram endpoints return SVG images via `StreamingResponse` 
- Diagram endpoints should accept parameters for the time axis of the diagram. With parameters start and end time of the time axis can be specified.
- For each health metric an endpoint is created to import bulk data in JSON format. The import fails when any data fails validation.
- All API parameters or fields need to be provided in ISO 8601 format
- All API Endpoints must be documented completely in OpenAPI documentation which the FastAPI framework generates.

### CORS
- FastAPI's `CORSMiddleware` is configured in `app/main.py` and handles preflight `OPTIONS` requests
- Allowed origins are driven by env var `CORS_ALLOWED_ORIGINS` (comma-separated list); production points it at the real frontend URL
- Fixed config: `allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]`, `allow_headers=["Authorization", "Content-Type"]`, `allow_credentials=False`

### Authentication and Authorization
- All API endpoints require authentication with bearer tokens
- The user authenticated with the bearer token can do CRUD operations only with his own data
- A user cannot access another users data
- Tokens are RS256-signed JWTs issued by Keycloak; the app fetches the JWKS from `{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs`
- The `sub` claim is used as the user identity (`user_id`) for scoping all data access

### Database
- SQLModel models are the single source of truth for schema
- Use type Decimal for numeric values with decimal places
- All new models must be imported in `alembic/env.py`
- PostgreSQL, for unit tests testcontainers library is used to spin up the database

### Container Image

- The container image is build with Podman using a Python script. The script need to have a cli interface.
- Building and running the container is tested with Python libraries
- Use multiple stages in the containerfile to optimize image size
- The image is published on DockerHub: https://hub.docker.com/
- Image architectures: linux/amd64, linux/arm64

```
uv run python scripts/build.py --help    # see available commands
uv run python scripts/build.py build     # build image locally with Podman
uv run python scripts/build.py push      # push to DockerHub (requires podman login first)
```

### Tests

#### Unit tests
Coverage:
- all API endpoints
- database operations
- generating diagrams
- repositories

#### Slow tests
- Slow tests build and run the container image with Podman (`tests/test_container.py`). They are marked with `@pytest.mark.slow` (module-level `pytestmark`).
- The default test run excludes them via `addopts = "... -m 'not slow'"` in `pyproject.toml`; run them explicitly with `uv run pytest -m slow`.
- In CI they run in a dedicated workflow (`.github/workflows/container-tests.yaml`) in parallel with the unit-test workflow, but only on PRs that change `Containerfile`, `scripts/build.py`, or `tests/test_container.py`.

#### Local manual testing
- Podman compose is used for local manual testing
- Configuration: compose.yaml (starts PostgreSQL, Keycloak, runs migrations, starts the app on port 8000)
- Keycloak is preloaded from `compose/keycloak/realm.json` with realm `health-monitor`, client `health-monitor-swagger` (public, direct access grant), and user `tester`/`tester`
- Obtain a JWT for the seeded `tester` user with `uv run python scripts/get_token.py`, then paste it into the Swagger UI (`http://localhost:8000/docs`) Authorize dialog
- The Swagger UI `Authorize` button accepts a Bearer token (via the `HTTPBearer` security scheme) for trying out all endpoints

```
podman compose up                          # start the full stack (PostgreSQL + Keycloak + app)
podman compose down                        # stop and remove containers
uv run python scripts/get_token.py         # fetch a JWT for the tester user
```

## Stack

- Language: Python
- Deployment target: Kubernetes
- Package manager: uv
- Framework: FastAPI
- ORM: SQLAlchemy
- SQL database interaction in Python: SQLModel
- Database migrations: alembic
- Test runner: pytest
- Linter/formatter: Ruff (run via the pre-commit hook, not installed as a dependency)
- git pre-commit hooks: pre-commit
- Conventional commits: commitizen
- Container: Podman
- Container build: python-on-whales
- Container test: testcontainers
- CLI: click
- Diagram rendering: seaborn, matplotlib
- Authentication: bearer tokens from Keycloak IDP 

## Environment Variables
- `DATABASE_URL` — SQLAlchemy database URL (default: `postgresql+psycopg2://postgres:postgres@localhost:5432/health_monitor`)
- `KEYCLOAK_URL` — Keycloak base URL (default: `http://localhost:8080`)
- `KEYCLOAK_REALM` — Keycloak realm name (default: `health-monitor`)
- `KEYCLOAK_JWKS_JSON` — Optional: inline JWKS JSON string, bypasses fetching from Keycloak (used in container integration tests only)
- `CORS_ALLOWED_ORIGINS` — Comma-separated list of origins allowed by `CORSMiddleware` (default: `http://localhost:5173`)

Minimal `.env` for local development (defaults work if Keycloak runs on localhost):
```
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/health_monitor
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=health-monitor
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

## Adding a New Health Metric

Checklist when adding a new metric (e.g. `blood_oxygen`):

1. `app/models/<metric>.py` — SQLModel table model (import it in `alembic/env.py`)
2. `app/schemas/<metric>.py` — Pydantic request/response schemas
3. `app/repositories/<metric>.py` — repository class for CRUD operations
4. `app/diagrams/<metric>.py` — Matplotlib SVG rendering function
5. `app/routers/<metric>.py` — FastAPI router with all endpoints
6. `app/routers/v1.py` — register the new router
7. `uv run alembic revision --autogenerate -m "add <metric> table"` — generate migration
8. `tests/` — add tests covering all endpoints, repository, and diagram

## Conventions

### Git commits

- For git commit messages conventional commits specification is used: https://www.conventionalcommits.org/en/v1.0.0/#specification

### Setup
Development setup needs both the main and the dev dependencies. Production setup needs only the main dependencies (no pytest, pre-commit, testcontainers, etc.). Note: Ruff is not a project dependency at all — it is provided by the Ruff pre-commit hook, so it is never installed by `uv sync`.
```
uv sync                       # development: main + dev dependencies
uv sync --no-dev              # production: main dependencies only
uv run pre-commit install     # development only: install git pre-commit hooks
```

### Development
```
uv run uvicorn app.main:app --reload          # dev server at http://localhost:8000
uv run alembic upgrade head                   # apply migrations
uv run alembic revision --autogenerate -m ""  # generate migration from model changes
```

When adding a new SQLModel table model, import it in `alembic/env.py` so Alembic detects it during autogenerate.

### Testing
```
uv run pytest                                      # run unit tests (slow tests excluded by default)
uv run pytest tests/path/to/test.py::test_name    # run single test
uv run pytest -m slow                              # run only the slow container tests
uv run pytest -m ""                                # run everything, including slow tests
```

Tests spin up a PostgreSQL database using testcontainers library via conftest.py fixtures (`session`, `client`). Each test gets a fresh database — tables are created and dropped per test via the `setup_tables` autouse fixture.

### Linting
Ruff is **not** installed as a project dependency — it is run exclusively through the Ruff pre-commit hook (`astral-sh/ruff-pre-commit` in `.pre-commit-config.yaml`). `uv run ruff ...` will fail. Lint and format by running the hooks:
```
uv run pre-commit run ruff-check --all-files     # lint
uv run pre-commit run ruff-format --all-files    # format
uv run pre-commit run --all-files                # run all hooks (lint, format, commit checks)
```
Ruff's configuration still lives in `pyproject.toml` (`[tool.ruff]`); the hook reads it.

### Git pre-commit hooks
Hooks are defined in `.pre-commit-config.yaml` and enforced in CI by the `Code quality` workflow.
They run Ruff lint and format on staged files before every commit, and commitizen validates commit messages against the conventional commits specification.
Hooks need to be run locally after all code changes are made to ensure code is linted and formatted.
```
uv run pre-commit install                          # install pre-commit hooks once after cloning
uv run pre-commit install --hook-type commit-msg   # install commit-msg hook for conventional commits
uv run pre-commit run --all-files                  # run all hooks against the whole repo
uv run pre-commit autoupdate                       # update hook versions
uv run cz commit                                   # interactively craft a conventional commit
```
