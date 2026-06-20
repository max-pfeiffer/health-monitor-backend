import json
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.blood_pressure import BloodPressure
from tests.conftest import TEST_USER_ID_2

BASE_URL = "/api/v1/blood-pressure"
MEASURED_AT = "2024-01-15T10:00:00"


def _json_file(payload) -> dict:
    return {"file": ("data.json", json.dumps(payload), "application/json")}


@pytest.fixture
def record(client: TestClient) -> dict:
    response = client.post(
        BASE_URL + "/",
        json={"systolic": 120, "diastolic": 80, "measured_at": MEASURED_AT},
    )
    return response.json()


def test_create(client: TestClient):
    response = client.post(
        BASE_URL + "/",
        json={"systolic": 120, "diastolic": 80, "measured_at": MEASURED_AT},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["systolic"] == 120
    assert data["diastolic"] == 80
    assert data["id"] is not None


def test_create_with_optional_fields(client: TestClient):
    response = client.post(
        BASE_URL + "/",
        json={
            "systolic": 120,
            "diastolic": 80,
            "pulse": 72,
            "notes": "after rest",
            "measured_at": MEASURED_AT,
        },
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
    client.post(
        BASE_URL + "/",
        json={
            "systolic": 130,
            "diastolic": 85,
            "measured_at": "2024-01-16T10:00:00",
        },
    )
    response = client.get(BASE_URL + "/")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_create_duplicate_measured_at(client: TestClient, record: dict):
    response = client.post(
        BASE_URL + "/",
        json={"systolic": 130, "diastolic": 85, "measured_at": MEASURED_AT},
    )
    assert response.status_code == 409


def test_update_conflicts_with_existing(client: TestClient, record: dict):
    other = client.post(
        BASE_URL + "/",
        json={
            "systolic": 130,
            "diastolic": 85,
            "measured_at": "2024-02-01T10:00:00",
        },
    ).json()
    response = client.put(
        f"{BASE_URL}/{other['id']}",
        json={"measured_at": MEASURED_AT},
    )
    assert response.status_code == 409


def test_update_same_measured_at_allowed(client: TestClient, record: dict):
    response = client.put(
        f"{BASE_URL}/{record['id']}",
        json={"systolic": 125, "measured_at": MEASURED_AT},
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
        BASE_URL + "/",
        json={"systolic": 120, "diastolic": 80, "measured_at": "2024-03-01T10:00:00"},
    )
    client.post(
        BASE_URL + "/",
        json={"systolic": 130, "diastolic": 85, "measured_at": "2024-06-01T10:00:00"},
    )
    response = client.get(
        f"{BASE_URL}/chart?start=2024-04-01T00:00:00&end=2024-12-31T23:59:59"
    )
    assert response.status_code == 200
    assert b"<svg" in response.content


def test_chart_with_systolic_top(client: TestClient, record: dict):
    response = client.get(f"{BASE_URL}/chart?systolic_top=135")
    assert response.status_code == 200
    assert b"<svg" in response.content


def test_chart_with_diastolic_top(client: TestClient, record: dict):
    response = client.get(f"{BASE_URL}/chart?diastolic_top=85")
    assert response.status_code == 200
    assert b"<svg" in response.content


def test_chart_hide_systolic(client: TestClient, record: dict):
    response = client.get(f"{BASE_URL}/chart?show_systolic=false")
    assert response.status_code == 200
    assert b"<svg" in response.content


def test_chart_hide_diastolic(client: TestClient, record: dict):
    response = client.get(f"{BASE_URL}/chart?show_diastolic=false")
    assert response.status_code == 200
    assert b"<svg" in response.content


def test_chart_hide_pulse(client: TestClient, record: dict):
    response = client.get(f"{BASE_URL}/chart?show_pulse=false")
    assert response.status_code == 200
    assert b"<svg" in response.content


def test_chart_dark_theme(client: TestClient, record: dict):
    response = client.get(f"{BASE_URL}/chart?theme=dark")
    assert response.status_code == 200
    assert b"<svg" in response.content


def test_chart_invalid_theme(client: TestClient):
    assert client.get(f"{BASE_URL}/chart?theme=neon").status_code == 422


def test_chart_start_after_end(client: TestClient):
    response = client.get(
        f"{BASE_URL}/chart?start=2024-12-31T00:00:00&end=2024-01-01T00:00:00"
    )
    assert response.status_code == 422
    # Conforms to FastAPI's structured 422 payload (a list of error objects),
    # not a plain string detail.
    detail = response.json()["detail"]
    assert isinstance(detail, list)
    assert detail[0]["type"] == "value_error"
    assert detail[0]["loc"] == ["query", "end"]


def test_chart_systolic_top_out_of_range(client: TestClient):
    assert client.get(f"{BASE_URL}/chart?systolic_top=500").status_code == 422
    assert client.get(f"{BASE_URL}/chart?systolic_top=-1").status_code == 422


def test_chart_cache_headers(client: TestClient, record: dict):
    response = client.get(f"{BASE_URL}/chart")
    assert response.headers["cache-control"] == "private, max-age=3600"
    assert response.headers["etag"]


def test_chart_etag_not_modified(client: TestClient, record: dict):
    first = client.get(f"{BASE_URL}/chart")
    etag = first.headers["etag"]
    second = client.get(f"{BASE_URL}/chart", headers={"If-None-Match": etag})
    assert second.status_code == 304
    assert second.headers["etag"] == etag
    assert not second.content


def test_chart_etag_changes_with_new_data(client: TestClient, record: dict):
    etag = client.get(f"{BASE_URL}/chart").headers["etag"]
    client.post(
        BASE_URL + "/",
        json={"systolic": 118, "diastolic": 78, "measured_at": "2024-02-01T10:00:00"},
    )
    assert client.get(f"{BASE_URL}/chart").headers["etag"] != etag


def test_import(client: TestClient):
    payload = [
        {
            "systolic": 120,
            "diastolic": 80,
            "pulse": 72,
            "measured_at": "2024-01-10T08:00:00",
        },
        {"systolic": 125, "diastolic": 82, "measured_at": "2024-01-11T08:00:00"},
        {
            "systolic": 118,
            "diastolic": 78,
            "pulse": 68,
            "notes": "after rest",
            "measured_at": "2024-01-12T08:00:00",
        },
    ]
    response = client.post(BASE_URL + "/import", files=_json_file(payload))
    assert response.status_code == 201
    assert response.content == b""

    listed = client.get(BASE_URL + "/").json()
    assert len(listed) == 3
    by_systolic = {record["systolic"]: record for record in listed}
    assert by_systolic[120]["pulse"] == 72
    assert by_systolic[118]["notes"] == "after rest"


def test_import_persists_to_db(client: TestClient):
    payload = [
        {"systolic": 120, "diastolic": 80, "measured_at": "2024-02-01T09:00:00"},
        {"systolic": 130, "diastolic": 85, "measured_at": "2024-02-02T09:00:00"},
    ]
    client.post(BASE_URL + "/import", files=_json_file(payload))
    response = client.get(BASE_URL + "/")
    assert len(response.json()) == 2


def test_import_internal_duplicate(client: TestClient):
    payload = [
        {"systolic": 120, "diastolic": 80, "measured_at": "2024-03-01T08:00:00"},
        {"systolic": 125, "diastolic": 82, "measured_at": "2024-03-01T08:00:00"},
    ]
    response = client.post(BASE_URL + "/import", files=_json_file(payload))
    assert response.status_code == 409
    assert client.get(BASE_URL + "/").json() == []


def test_import_conflicts_with_existing(client: TestClient, record: dict):
    payload = [
        {"systolic": 130, "diastolic": 85, "measured_at": MEASURED_AT},
        {"systolic": 118, "diastolic": 78, "measured_at": "2024-04-01T08:00:00"},
    ]
    response = client.post(BASE_URL + "/import", files=_json_file(payload))
    assert response.status_code == 409
    assert len(client.get(BASE_URL + "/").json()) == 1


def test_import_invalid_data(client: TestClient):
    payload = [
        {"systolic": 120, "diastolic": 80, "measured_at": "2024-01-10T08:00:00"},
        {
            "systolic": "not-a-number",
            "diastolic": 80,
            "measured_at": "2024-01-11T08:00:00",
        },
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
    payload = {"systolic": 120, "diastolic": 80, "measured_at": MEASURED_AT}
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


def test_unauthenticated(client_no_auth: TestClient):
    assert client_no_auth.get(BASE_URL + "/").status_code == 401
    assert client_no_auth.post(BASE_URL + "/", json={}).status_code == 401
    assert client_no_auth.get(f"{BASE_URL}/1").status_code == 401
    assert client_no_auth.put(f"{BASE_URL}/1", json={}).status_code == 401
    assert client_no_auth.delete(f"{BASE_URL}/1").status_code == 401
    assert client_no_auth.get(f"{BASE_URL}/chart").status_code == 401
    assert client_no_auth.post(BASE_URL + "/import").status_code == 401


def test_user_isolation(client: TestClient, session: Session, record: dict):
    other = BloodPressure(
        user_id=TEST_USER_ID_2,
        systolic=140,
        diastolic=90,
        measured_at=datetime(2024, 5, 1, 10, 0, 0),
    )
    session.add(other)
    session.commit()
    session.refresh(other)

    # list only shows current user's records
    listed = client.get(BASE_URL + "/").json()
    assert all(r["id"] != other.id for r in listed)
    assert len(listed) == 1

    # get returns 404 for another user's record
    assert client.get(f"{BASE_URL}/{other.id}").status_code == 404

    # update returns 404 for another user's record
    assert (
        client.put(f"{BASE_URL}/{other.id}", json={"systolic": 150}).status_code == 404
    )

    # delete returns 404 for another user's record
    assert client.delete(f"{BASE_URL}/{other.id}").status_code == 404
