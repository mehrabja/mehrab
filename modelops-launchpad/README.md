# ModelOps Launchpad

[![ModelOps Launchpad CI](https://github.com/mehrabja/mehrab/actions/workflows/modelops-ci.yml/badge.svg?branch=main)](https://github.com/mehrabja/mehrab/actions/workflows/modelops-ci.yml)

<p align="center">
  <img src="https://img.shields.io/badge/MLOps-REPRODUCIBLE%20TRAINING-8B5CF6?style=for-the-badge" alt="Reproducible training" />
  <img src="https://img.shields.io/badge/DEPLOYMENT-DOCKER-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker deployment" />
  <img src="https://img.shields.io/badge/OBSERVABILITY-PROMETHEUS-0891B2?style=for-the-badge" alt="Prometheus metrics" />
</p>

A compact end-to-end ML delivery template: deterministic training, a versioned model artifact, FastAPI inference, health/readiness checks, Prometheus metrics, Docker, Compose, tests, and CI.

## Included

- Deterministic synthetic classification dataset generated with scikit-learn.
- RandomForest training with fixed seeds and held-out accuracy metadata.
- Model bundle containing the estimator, version, labels, and feature schema.
- FastAPI `POST /v1/predict`, `GET /healthz`, `GET /readyz`, and `GET /metrics`.
- Prometheus-compatible request counter and latency histogram.
- Non-root Docker runtime, read-only root filesystem, dropped Linux capabilities, and `no-new-privileges`.
- Pytest API checks and a GitHub Actions test/build workflow.

## Run locally

Requires Python 3.11 or newer.

```bash
cd modelops-launchpad
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

python scripts/train.py --output-dir artifacts
uvicorn app.main:app --reload
```

API docs: http://127.0.0.1:8000/docs

## Predict

```bash
curl -X POST http://127.0.0.1:8000/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"features":[0.2,-0.1,1.3,0.7]}'
```

The response contains the predicted class, class probabilities, model version, and feature names.

## Hands-on HTTP demo

After training the model and starting Uvicorn using the commands above, open [examples/demo.http](./examples/demo.http) in VS Code with the REST Client extension. It exercises liveness, readiness, prediction, and Prometheus metrics. The prediction endpoint requires exactly four finite numeric features and returns the class, probabilities, model version, and feature names.

The training dataset is synthetic. Its reported accuracy is an engineering smoke-test metric, not evidence of real-world predictive performance.

## Run with Compose

```bash
docker compose up --build
```

The API is exposed on port 8000. Compose uses a non-root process, read-only root filesystem, dropped Linux capabilities, and a readiness health check.

## Tests and metrics

```bash
pytest -q
curl http://127.0.0.1:8000/metrics
```

The metrics endpoint exposes request totals and a duration histogram by method and route. Tracing, drift monitoring, alert rules, model registry integration, and deployment promotion are not yet implemented.

## Architecture

```text
Synthetic dataset -> Training script -> model.joblib + metadata.json
                                      |
                                      v
                              FastAPI inference
                        /healthz /readyz /v1/predict
                                      |
                                      v
                             /metrics -> scraper
                                      |
                         Docker / Compose / GitHub CI
```

## Production hardening checklist

- [ ] Add authentication, authorization, quotas, and request-size limits.
- [ ] Store artifacts in a signed model registry and verify provenance at startup.
- [ ] Add structured logs and OpenTelemetry traces.
- [ ] Add model-quality, drift, and data-quality monitoring.
- [ ] Add deployment promotion, rollback, and environment-specific configuration.
- [ ] Add vulnerability scanning and image signing to the release pipeline.

The included data is synthetic and intended for engineering demonstrations, not medical, financial, or other real-world decisions. Only load trusted joblib artifacts.

Mehrab Jalilian · [GitHub](https://github.com/mehrabja)
