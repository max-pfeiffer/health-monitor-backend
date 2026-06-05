import json

import pytest
from fastapi.testclient import TestClient

BASE_URL = "/api/v1/blood-glucose"
MEASURED_AT = "2024-01-15T10:00:00"


def _json_file(payload) -> dict:
    return {"file": ("data.json", json.dumps(payload), "application/json")}


@pytest.fixture
def record(client: TestClient) -> dict:
    response = client.post(
        BASE_URL + "/", json={"value": "5.60", "measured_at": MEASURED_AT}
    )
    return response.json()


def test_create(client: TestClient):
    response = client.post(
        BASE_URL + "/", json={"value": "5.60", "measured_at": MEASURED_AT}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["value"] == "5.60"


def test_create_with_notes(client: TestClient):
    response = client.post(
        BASE_URL + "/",
        json={"value": "7.20", "notes": "after meal", "measured_at": MEASURED_AT},
    )
    assert response.status_code == 201
    assert response.json()["notes"] == "after meal"


def test_list_empty(client: TestClient):
    response = client.get(BASE_URL + "/")
    assert response.status_code == 200
    assert response.json() == []


def test_list(client: TestClient, record: dict):
    client.post(
        BASE_URL + "/",
        json={"value": "6.10", "measured_at": "2024-01-16T10:00:00"},
    )
    response = client.get(BASE_URL + "/")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_create_duplicate_measured_at(client: TestClient, record: dict):
    response = client.post(
        BASE_URL + "/", json={"value": "6.10", "measured_at": MEASURED_AT}
    )
    assert response.status_code == 409


def test_update_conflicts_with_existing(client: TestClient, record: dict):
    other = client.post(
        BASE_URL + "/",
        json={"value": "6.10", "measured_at": "2024-02-01T10:00:00"},
    ).json()
    response = client.put(
        f"{BASE_URL}/{other['id']}", json={"measured_at": MEASURED_AT}
    )
    assert response.status_code == 409


def test_update_same_measured_at_allowed(client: TestClient, record: dict):
    response = client.put(
        f"{BASE_URL}/{record['id']}",
        json={"value": "6.50", "measured_at": MEASURED_AT},
    )
    assert response.status_code == 200


def test_get(client: TestClient, record: dict):
    response = client.get(f"{BASE_URL}/{record['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == record["id"]


def test_get_not_found(client: TestClient):
    response = client.get(f"{BASE_URL}/999")
    assert response.status_code == 404


def test_update(client: TestClient, record: dict):
    response = client.put(f"{BASE_URL}/{record['id']}", json={"value": "6.50"})
    assert response.status_code == 200
    assert response.json()["value"] == "6.50"


def test_update_not_found(client: TestClient):
    response = client.put(f"{BASE_URL}/999", json={"value": "6.50"})
    assert response.status_code == 404


def test_delete(client: TestClient, record: dict):
    response = client.delete(f"{BASE_URL}/{record['id']}")
    assert response.status_code == 204
    assert client.get(f"{BASE_URL}/{record['id']}").status_code == 404


def test_delete_not_found(client: TestClient):
    response = client.delete(f"{BASE_URL}/999")
    assert response.status_code == 404


def test_chart_empty(client: TestClient):
    response = client.get(f"{BASE_URL}/chart")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert b"<svg" in response.content


def test_chart_with_data(client: TestClient, record: dict):
    response = client.get(f"{BASE_URL}/chart")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert b"<svg" in response.content


def test_chart_with_time_range(client: TestClient, record: dict):
    response = client.get(
        f"{BASE_URL}/chart?start=2024-01-01T00:00:00&end=2024-12-31T23:59:59"
    )
    assert response.status_code == 200
    assert b"<svg" in response.content


def test_chart_time_range_filters_records(client: TestClient):
    client.post(
        BASE_URL + "/", json={"value": "5.60", "measured_at": "2024-03-01T10:00:00"}
    )
    client.post(
        BASE_URL + "/", json={"value": "6.10", "measured_at": "2024-06-01T10:00:00"}
    )
    response = client.get(
        f"{BASE_URL}/chart?start=2024-04-01T00:00:00&end=2024-12-31T23:59:59"
    )
    assert response.status_code == 200
    assert b"<svg" in response.content


def test_import(client: TestClient):
    payload = [
        {"value": "5.60", "measured_at": "2024-01-10T08:00:00"},
        {"value": "7.20", "notes": "after meal", "measured_at": "2024-01-11T12:00:00"},
        {"value": "4.80", "measured_at": "2024-01-12T07:00:00"},
    ]
    response = client.post(BASE_URL + "/import", files=_json_file(payload))
    assert response.status_code == 201
    assert response.content == b""

    listed = client.get(BASE_URL + "/").json()
    assert len(listed) == 3
    by_value = {record["value"]: record for record in listed}
    assert by_value["7.20"]["notes"] == "after meal"


def test_import_persists_to_db(client: TestClient):
    payload = [
        {"value": "5.60", "measured_at": "2024-02-01T08:00:00"},
        {"value": "6.10", "measured_at": "2024-02-02T08:00:00"},
    ]
    client.post(BASE_URL + "/import", files=_json_file(payload))
    response = client.get(BASE_URL + "/")
    assert len(response.json()) == 2


def test_import_internal_duplicate(client: TestClient):
    payload = [
        {"value": "5.60", "measured_at": "2024-03-01T08:00:00"},
        {"value": "6.10", "measured_at": "2024-03-01T08:00:00"},
    ]
    response = client.post(BASE_URL + "/import", files=_json_file(payload))
    assert response.status_code == 409
    assert client.get(BASE_URL + "/").json() == []


def test_import_conflicts_with_existing(client: TestClient, record: dict):
    payload = [
        {"value": "6.10", "measured_at": MEASURED_AT},
        {"value": "4.80", "measured_at": "2024-04-01T08:00:00"},
    ]
    response = client.post(BASE_URL + "/import", files=_json_file(payload))
    assert response.status_code == 409
    assert len(client.get(BASE_URL + "/").json()) == 1


def test_import_invalid_data(client: TestClient):
    payload = [
        {"value": "5.60", "measured_at": "2024-01-10T08:00:00"},
        {"value": "not-a-number", "measured_at": "2024-01-11T08:00:00"},
    ]
    response = client.post(BASE_URL + "/import", files=_json_file(payload))
    assert response.status_code == 422
    assert client.get(BASE_URL + "/").json() == []


def test_import_invalid_json(client: TestClient):
    response = client.post(
        BASE_URL + "/import",
        files={"file": ("data.json", b"not valid json", "application/json")},
    )
    assert response.status_code == 422
    assert client.get(BASE_URL + "/").json() == []


def test_import_not_a_list(client: TestClient):
    payload = {"value": "5.60", "measured_at": MEASURED_AT}
    response = client.post(BASE_URL + "/import", files=_json_file(payload))
    assert response.status_code == 422


def test_import_missing_file(client: TestClient):
    response = client.post(BASE_URL + "/import")
    assert response.status_code == 422


def test_import_empty_list(client: TestClient):
    response = client.post(BASE_URL + "/import", files=_json_file([]))
    assert response.status_code == 201
    assert response.content == b""
    assert client.get(BASE_URL + "/").json() == []
