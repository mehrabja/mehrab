from fastapi.testclient import TestClient

from app.main import create_app
from scripts.train import train_model


def make_client(tmp_path):
    artifact_dir = tmp_path / "artifacts"
    train_model(artifact_dir)
    return TestClient(create_app(artifact_dir / "model.joblib"))


def test_health_and_readiness(tmp_path):
    client = make_client(tmp_path)
    assert client.get("/healthz").status_code == 200
    ready = client.get("/readyz")
    assert ready.status_code == 200
    assert ready.json()["model_version"] == "0.1.0"


def test_prediction_contract_and_histogram_metrics(tmp_path):
    client = make_client(tmp_path)
    response = client.post("/v1/predict", json={"features": [0.2, -0.1, 1.3, 0.7]})
    assert response.status_code == 200
    body = response.json()
    assert body["label"].startswith("class_")
    assert len(body["probabilities"]) == 3
    assert abs(sum(body["probabilities"]) - 1.0) < 1e-5
    assert body["model_version"] == "0.1.0"

    metrics = client.get("/metrics").text
    assert "modelops_http_request_duration_seconds_bucket" in metrics
    assert 'path="/v1/predict"' in metrics


def test_unready_service_returns_503(tmp_path):
    client = TestClient(create_app(tmp_path / "missing.joblib"))
    assert client.get("/readyz").status_code == 503


def test_non_finite_features_are_rejected(tmp_path):
    client = make_client(tmp_path)
    response = client.post(
        "/v1/predict",
        content='{"features":[0.1,0.2,NaN,0.4]}',
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422


def test_histogram_buckets_are_cumulative(tmp_path):
    client = make_client(tmp_path)
    client.get("/healthz")
    client.post("/v1/predict", json={"features": [0.2, -0.1, 1.3, 0.7]})
    metrics = client.get("/metrics").text
    bucket_lines = [
        line for line in metrics.splitlines()
        if 'path="/v1/predict"' in line and "_bucket{" in line and 'le="+Inf"' not in line
    ]
    counts = [int(line.rsplit(" ", 1)[1]) for line in bucket_lines]
    assert counts == sorted(counts)
    assert counts[-1] <= 1
