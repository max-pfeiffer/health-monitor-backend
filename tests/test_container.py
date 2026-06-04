import socket
from pathlib import Path

import pytest
import requests
from sqlalchemy import create_engine
from sqlmodel import SQLModel
from testcontainers.core.container import DockerContainer
from testcontainers.core.network import Network
from testcontainers.core.waiting_utils import wait_for_logs
from testcontainers.postgres import PostgresContainer

from scripts.build import build_image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGE_TAG = "health-monitor-backend:test"
POSTGRES_ALIAS = "db"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def built_image() -> str:
    return build_image(
        tag=IMAGE_TAG,
        containerfile=PROJECT_ROOT / "Containerfile",
        context=PROJECT_ROOT,
    )


@pytest.fixture(scope="module")
def network():
    with Network() as net:
        yield net


@pytest.fixture(scope="module")
def postgres(network):
    container = (
        PostgresContainer("postgres:16-alpine", driver="psycopg2")
        .with_network(network)
        .with_network_aliases(POSTGRES_ALIAS)
    )
    with container as pg:
        yield pg


@pytest.fixture(scope="module")
def schema(postgres: PostgresContainer):
    engine = create_engine(postgres.get_connection_url())
    SQLModel.metadata.create_all(engine)
    engine.dispose()


@pytest.fixture(scope="module")
def app_container(built_image: str, network, postgres: PostgresContainer, schema):
    user = postgres.username
    password = postgres.password
    dbname = postgres.dbname
    internal_url = f"postgresql+psycopg2://{user}:{password}@{POSTGRES_ALIAS}:5432/{dbname}"

    host_port = _free_port()
    container = (
        DockerContainer(built_image)
        .with_network(network)
        .with_env("DATABASE_URL", internal_url)
        .with_bind_ports(8000, host_port)
    )
    with container as running:
        wait_for_logs(running, "Uvicorn running on", timeout=60)
        base_url = f"http://{running.get_container_host_ip()}:{host_port}"
        yield base_url


def test_build_produces_image(built_image: str):
    assert built_image == IMAGE_TAG


def test_root_redirects_to_docs(app_container: str):
    response = requests.get(f"{app_container}/", allow_redirects=False, timeout=10)
    assert response.status_code == 307
    assert response.headers["location"].endswith("/docs")


def test_docs_endpoint(app_container: str):
    response = requests.get(f"{app_container}/docs", timeout=10)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_blood_pressure_crud(app_container: str):
    base = f"{app_container}/api/v1/blood-pressure"

    create = requests.post(
        f"{base}/",
        json={"systolic": 120, "diastolic": 80, "measured_at": "2024-01-15T10:00:00"},
        timeout=10,
    )
    assert create.status_code == 201
    record = create.json()
    record_id = record["id"]

    get = requests.get(f"{base}/{record_id}", timeout=10)
    assert get.status_code == 200
    assert get.json()["systolic"] == 120

    delete = requests.delete(f"{base}/{record_id}", timeout=10)
    assert delete.status_code == 204


def test_blood_glucose_create(app_container: str):
    response = requests.post(
        f"{app_container}/api/v1/blood-glucose/",
        json={"value": "5.4", "measured_at": "2024-01-15T10:00:00"},
        timeout=10,
    )
    assert response.status_code == 201
    assert response.json()["id"] is not None


def test_ketones_create(app_container: str):
    response = requests.post(
        f"{app_container}/api/v1/ketones/",
        json={"value": "1.2", "measured_at": "2024-01-15T10:00:00"},
        timeout=10,
    )
    assert response.status_code == 201
    assert response.json()["id"] is not None


def test_blood_pressure_chart(app_container: str):
    response = requests.get(f"{app_container}/api/v1/blood-pressure/chart", timeout=10)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert b"<svg" in response.content
