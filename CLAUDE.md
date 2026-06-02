# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Python backend service for health monitoring.

### Purpose

The application should capture and store the following health metrics:
- blood pressure
- blood glucose
- ketones

It provides REST API endpoints for storing the health metrics data. 
It also provides REST API endpoints which render diagrams for the health metrics as images.

### Key Consumers

The application provides a REST API backend for frontend applications.
Frontend applications create, update, delete and read data using the REST API

### Deployment Environment

The application is running in a Container on Kubernetes.
The Kubernetes cluster is build with Talos Linux.
No cloud provider is used.
The application will run 24/7.

### Expected Integrations

Data is stored in a database.
Different types of databases need to be supported: SQLite, PostgreSQL
SQLite is only used for testing purposes.


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
- Container: Docker
- Diagram rendering: Matplotlib

## Conventions

### Setup
```
uv sync                   # install all dependencies including dev
uv sync --no-dev          # production dependencies only
pre-commit install        # install git hooks
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

Tests use SQLite (`test.db`) via conftest.py fixtures (`session`, `client`). Each test gets a fresh database — tables are created and dropped per test via the `setup_tables` autouse fixture.

### Linting
```
uv run ruff check .    # lint
uv run ruff format .   # format
```

### Unit tests need to cover
- all API endpoints
- database operations