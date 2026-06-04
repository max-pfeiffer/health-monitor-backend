from fastapi.testclient import TestClient


def test_root_redirects_to_docs(client: TestClient):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/docs"
