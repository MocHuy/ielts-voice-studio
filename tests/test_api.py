from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_health_and_home() -> None:
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/").status_code == 200


def test_parse_sample() -> None:
    response = client.post("/api/parse", json={"text": "Original: I are ready.\nCorrected: I am ready."})
    assert response.status_code == 200
    assert len(response.json()["cards"]) == 2


def test_parse_empty_rejected() -> None:
    assert client.post("/api/parse", json={"text": "  "}).status_code == 422
