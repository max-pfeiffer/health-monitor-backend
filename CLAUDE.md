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
- The default branch is main. This branch is protected.
- Features need to be created on branches with feature/* pattern
- Bug fixes need to be created on branches with bugfix/* pattern

#### GitHub Workflows
- Git pre-commit hooks are run using GitHub actions and locally when a new pull request is created or updated (local hooks + CI checks on PR)
- Unit test should be run always using GitHub actions when a new pull request is created or updated
- A new release on GitHub is created when the main branch is tagged with a semantic version
- Release notes are generated automatically
- When a new release is created using by tagging the main branch, the container image is build and pushed to Docker Hub
- The image is then tagged with the release tag version and also with latest tag
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
- Diagram endpoints should accept parameters for the time axis of the diagram (ISO 8601). With parameters start and end time of the time axis can be specified.
- For each health metric an endpoint is created to import bulk data in JSON format. The import fails when any data fails validation.

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

#### Local manual testing
- Podman compose is used for local manual testing
- Configuration: compose.yaml (starts PostgreSQL, runs migrations, starts the app on port 8000)
- The compose stack does not include Keycloak; run a separate Keycloak instance (default expected at `http://localhost:8080`) or set `KEYCLOAK_URL` to an existing instance
- Obtain a JWT via the Keycloak admin UI or `curl` against the token endpoint, then paste it into the Swagger UI (`http://localhost:8000/docs`) Authorize dialog
- The Swagger UI `Authorize` button accepts a Bearer token for trying out all endpoints

```
podman-compose up          # start the full stack
podman-compose down        # stop and remove containers
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
- Linter/formatter: Ruff
- git pre-commit hooks: pre-commit
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

Minimal `.env` for local development (defaults work if Keycloak runs on localhost):
```
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/health_monitor
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=health-monitor
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
Development setup needs both the main and the dev dependencies. Production setup needs only the main dependencies (no pytest, ruff, pre-commit, testcontainers, etc.).
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
uv run pytest                                      # run all tests
uv run pytest tests/path/to/test.py::test_name    # run single test
```

Tests spin up a PostgreSQL database using testcontainers library via conftest.py fixtures (`session`, `client`). Each test gets a fresh database — tables are created and dropped per test via the `setup_tables` autouse fixture.

### Linting
```
uv run ruff check .    # lint
uv run ruff format .   # format
```

### Git pre-commit hooks
Hooks are defined in `.pre-commit-config.yaml` and enforced in CI by the `Code quality` workflow. They run Ruff lint and format on staged files before every commit.
```
uv run pre-commit install              # install hooks once after cloning
uv run pre-commit run --all-files      # run all hooks against the whole repo
uv run pre-commit autoupdate           # update hook versions
```
