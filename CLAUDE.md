# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Python backend service for health monitoring. The project is in early development — no application code exists yet.

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

Unit tests need to cover:
- all api endpoints
- database operations