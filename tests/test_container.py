import base64
import json
import socket
import time
from pathlib import Path

import httpx2
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt as jose_jwt
from python_on_whales import DockerClient
from python_on_whales.utils import run as pow_run
from sqlalchemy import create_engine
from sqlmodel import SQLModel
from testcontainers.core.container import DockerContainer
from testcontainers.core.network import Network
from testcontainers.core.waiting_utils import wait_for_logs
from testcontainers.postgres import PostgresContainer
from testcontainers.registry import DockerRegistryContainer

from scripts.build import build_image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGE_TAG = "health-monitor-backend:test"
POSTGRES_ALIAS = "db"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _int_to_base64url(n: int) -> str:
    length = (n.bit_length() + 7) // 8
    return base64.urlsafe_b64encode(n.to_bytes(length, "big")).rstrip(b"=").decode()


@pytest.fixture(scope="module")
def test_auth():
    """Returns (jwks_json_str, bearer_token) for a throwaway RSA key pair."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub_nums = private_key.public_key().public_numbers()

    jwks = {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "alg": "RS256",
                "kid": "test-key-1",
                "n": _int_to_base64url(pub_nums.n),
                "e": _int_to_base64url(pub_nums.e),
            }
        ]
    }

    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()

    token = jose_jwt.encode(
        {"sub": "container-test-user", "exp": int(time.time()) + 3600},
        private_key_pem,
        algorithm="RS256",
        headers={"kid": "test-key-1"},
    )

    return json.dumps(jwks), token


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
def app_container(
    built_image: str, network, postgres: PostgresContainer, schema, test_auth
):
    jwks_json, _ = test_auth
    user = postgres.username
    password = postgres.password
    dbname = postgres.dbname
    internal_url = (
        f"postgresql+psycopg2://{user}:{password}@{POSTGRES_ALIAS}:5432/{dbname}"
    )

    host_port = _free_port()
    container = (
        DockerContainer(built_image)
        .with_network(network)
        .with_env("DATABASE_URL", internal_url)
        .with_env("KEYCLOAK_JWKS_JSON", jwks_json)
        .with_bind_ports(8000, host_port)
        .with_command("health-monitor-backend")
    )
    with container as running:
        wait_for_logs(running, "Uvicorn running on", timeout=60)
        base_url = f"http://{running.get_container_host_ip()}:{host_port}"
        yield base_url


def test_build_produces_image(built_image: str):
    assert built_image == IMAGE_TAG


def test_root_redirects_to_docs(app_container: str):
    response = httpx2.get(f"{app_container}/", follow_redirects=False, timeout=10)
    assert response.status_code == 307
    assert response.headers["location"].endswith("/docs")


def test_docs_endpoint(app_container: str):
    response = httpx2.get(f"{app_container}/docs", timeout=10)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_blood_pressure_crud(app_container: str, test_auth):
    _, token = test_auth
    headers = {"Authorization": f"Bearer {token}"}
    base = f"{app_container}/api/v1/blood-pressure"

    create = httpx2.post(
        f"{base}/",
        json={"systolic": 120, "diastolic": 80, "measured_at": "2024-01-15T10:00:00"},
        headers=headers,
        timeout=10,
    )
    assert create.status_code == 201
    record = create.json()
    record_id = record["id"]

    get = httpx2.get(f"{base}/{record_id}", headers=headers, timeout=10)
    assert get.status_code == 200
    assert get.json()["systolic"] == 120

    delete = httpx2.delete(f"{base}/{record_id}", headers=headers, timeout=10)
    assert delete.status_code == 204


def test_blood_glucose_create(app_container: str, test_auth):
    _, token = test_auth
    response = httpx2.post(
        f"{app_container}/api/v1/blood-glucose/",
        json={"value": "5.4", "measured_at": "2024-01-15T10:00:00"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    assert response.status_code == 201
    assert response.json()["id"] is not None


def test_ketones_create(app_container: str, test_auth):
    _, token = test_auth
    response = httpx2.post(
        f"{app_container}/api/v1/ketones/",
        json={"value": "1.2", "measured_at": "2024-01-15T10:00:00"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    assert response.status_code == 201
    assert response.json()["id"] is not None


def test_blood_pressure_chart(app_container: str, test_auth):
    _, token = test_auth
    response = httpx2.get(
        f"{app_container}/api/v1/blood-pressure/chart",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert b"<svg" in response.content


@pytest.fixture(scope="module")
def registry():
    with DockerRegistryContainer() as reg:
        yield reg.get_registry()


def test_push_image_to_registry(built_image: str, registry: str):
    repo = "health-monitor-backend"
    push_tag = f"{registry}/{repo}:push-test"

    podman = DockerClient(client_call=["podman"])
    podman.tag(built_image, push_tag)

    # podman defaults to HTTPS when talking to a registry; the testcontainers
    # registry:2 only speaks plain HTTP. python-on-whales' high-level push()
    # doesn't expose --tls-verify, so build the command via its Command/run
    # helpers — same library, lower-level entry point.
    pow_run(podman.docker_cmd + ["push", "--tls-verify=false", push_tag])

    response = httpx2.get(f"http://{registry}/v2/{repo}/tags/list", timeout=10)
    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == repo
    assert "push-test" in payload["tags"]
