import pytest
from fastapi.testclient import TestClient

BASE_URL = "/api/v1/blood-pressure"
MEASURED_AT = "2024-01-15T10:00:00"


@pytest.fixture
def record(client: TestClient) -> dict:
    response = client.post(BASE_URL + "/", json={"systolic": 120, "diastolic": 80, "measured_at": MEASURED_AT})
    return response.json()


def test_create(client: TestClient):
    response = client.post(BASE_URL + "/", json={"systolic": 120, "diastolic": 80, "measured_at": MEASURED_AT})
    assert response.status_code == 201
    data = response.json()
    assert data["systolic"] == 120
    assert data["diastolic"] == 80
    assert data["id"] is not None


def test_create_with_optional_fields(client: TestClient):
    response = client.post(
        BASE_URL + "/",
        json={"systolic": 120, "diastolic": 80, "pulse": 72, "notes": "after rest", "measured_at": MEASURED_AT},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["pulse"] == 72
    assert data["notes"] == "after rest"


def test_list_empty(client: TestClient):
    response = client.get(BASE_URL + "/")
    assert response.status_code == 200
    assert response.json() == []


def test_list(client: TestClient, record: dict):
    client.post(BASE_URL + "/", json={"systolic": 130, "diastolic": 85, "measured_at": MEASURED_AT})
    response = client.get(BASE_URL + "/")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get(client: TestClient, record: dict):
    response = client.get(f"{BASE_URL}/{record['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == record["id"]


def test_get_not_found(client: TestClient):
    response = client.get(f"{BASE_URL}/999")
    assert response.status_code == 404


def test_update(client: TestClient, record: dict):
    response = client.put(f"{BASE_URL}/{record['id']}", json={"systolic": 125})
    assert response.status_code == 200
    assert response.json()["systolic"] == 125
    assert response.json()["diastolic"] == 80


def test_update_not_found(client: TestClient):
    response = client.put(f"{BASE_URL}/999", json={"systolic": 125})
    assert response.status_code == 404


def test_delete(client: TestClient, record: dict):
    response = client.delete(f"{BASE_URL}/{record['id']}")
    assert response.status_code == 204
    assert client.get(f"{BASE_URL}/{record['id']}").status_code == 404


def test_delete_not_found(client: TestClient):
    response = client.delete(f"{BASE_URL}/999")
    assert response.status_code == 404
