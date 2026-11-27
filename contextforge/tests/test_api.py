from fastapi.testclient import TestClient

from app.main import create_app


def client_for(tmp_path):
    return TestClient(create_app(str(tmp_path / "context.db")))


def test_health(tmp_path):
    response = client_for(tmp_path).get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ingest_retrieve_and_cite(tmp_path, monkeypatch):
    monkeypatch.delenv("LLM_MODEL", raising=False)
    client = client_for(tmp_path)
    stored = client.post("/v1/documents", json={
        "source": "incident-runbook.md",
        "text": "Incident response starts with triage. Preserve logs, scope affected systems, "
                "record a timeline, then coordinate containment and recovery.",
    })
    assert stored.status_code == 200
    assert stored.json()["chunks"] == 1

    response = client.post("/v1/query", json={
        "question": "How does incident response start?", "k": 3
    })
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "extractive"
    assert body["sources"][0]["id"] == "S1"
    assert "triage" in body["answer"].lower()


def test_empty_store_returns_no_context(tmp_path):
    response = client_for(tmp_path).post(
        "/v1/query", json={"question": "What is the answer?", "k": 2}
    )
    assert response.status_code == 200
    assert response.json()["mode"] == "no_context"


def test_document_input_is_validated(tmp_path):
    response = client_for(tmp_path).post(
        "/v1/documents", json={"source": "", "text": "x"}
    )
    assert response.status_code == 422
