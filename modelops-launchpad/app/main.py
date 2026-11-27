from __future__ import annotations

import math
import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import joblib
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field, field_validator

BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)


class PredictRequest(BaseModel):
    features: list[float] = Field(min_length=4, max_length=4)

    @field_validator("features")
    @classmethod
    def features_must_be_finite(cls, values: list[float]) -> list[float]:
        if any(not math.isfinite(value) for value in values):
            raise ValueError("features must contain only finite numbers")
        return values


def _load_bundle(model_path: str | Path) -> dict[str, Any] | None:
    path = Path(model_path)
    if not path.is_file():
        return None
    bundle = joblib.load(path)
    if not isinstance(bundle, dict) or "model" not in bundle:
        raise RuntimeError("model artifact has an invalid structure")
    required = {"model_version", "labels", "feature_names"}
    if not required.issubset(bundle):
        raise RuntimeError("model artifact is missing required metadata")
    return bundle


def create_app(model_path: str | Path | None = None) -> FastAPI:
    selected_path = model_path or os.getenv("MODEL_PATH", "artifacts/model.joblib")
    bundle = _load_bundle(selected_path)
    api = FastAPI(
        title="ModelOps Launchpad",
        version="0.1.0",
        description="A reproducible ML inference service with health, readiness, and metrics endpoints.",
    )
    api.state.model_bundle = bundle
    api.state.request_counts = defaultdict(int)
    api.state.duration_sums = defaultdict(float)
    api.state.duration_buckets = defaultdict(lambda: [0] * len(BUCKETS))

    @api.middleware("http")
    async def collect_metrics(request: Request, call_next):
        started = time.perf_counter()
        method, path = request.method, request.url.path
        try:
            return await call_next(request)
        finally:
            elapsed = time.perf_counter() - started
            key = (method, path)
            api.state.request_counts[key] += 1
            api.state.duration_sums[key] += elapsed
            for index, bound in enumerate(BUCKETS):
                if elapsed <= bound:
                    api.state.duration_buckets[key][index] += 1

    @api.get("/healthz", tags=["operations"])
    def healthz():
        return {"status": "ok", "service": "modelops-launchpad"}

    @api.get("/readyz", tags=["operations"])
    def readyz():
        active = api.state.model_bundle
        if active is None:
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "reason": "model artifact is not loaded"},
            )
        return {"status": "ready", "model_version": active["model_version"]}

    @api.post("/v1/predict", tags=["inference"])
    def predict(payload: PredictRequest):
        active = api.state.model_bundle
        if active is None:
            raise HTTPException(status_code=503, detail="model is not ready")
        model = active["model"]
        prediction = int(model.predict([payload.features])[0])
        probabilities = model.predict_proba([payload.features])[0].tolist()
        if prediction < 0 or prediction >= len(active["labels"]):
            raise HTTPException(status_code=500, detail="model returned an unknown class")
        return {
            "prediction": prediction,
            "label": active["labels"][prediction],
            "probabilities": [round(float(value), 6) for value in probabilities],
            "model_version": active["model_version"],
            "feature_names": active["feature_names"],
        }

    @api.get("/metrics", response_class=PlainTextResponse, tags=["operations"])
    def metrics():
        lines = [
            "# HELP modelops_http_requests_total Total HTTP requests handled.",
            "# TYPE modelops_http_requests_total counter",
            "# HELP modelops_http_request_duration_seconds Request duration in seconds.",
            "# TYPE modelops_http_request_duration_seconds histogram",
        ]
        for (method, path), count in sorted(api.state.request_counts.items()):
            safe_path = path.replace('"', "")
            labels = f'method="{method}",path="{safe_path}"'
            lines.append(f"modelops_http_requests_total{{{labels}}} {count}")
            counts = api.state.duration_buckets[(method, path)]
            for index, bound in enumerate(BUCKETS):
                lines.append(
                    f'modelops_http_request_duration_seconds_bucket{{{labels},le="{bound}"}} {counts[index]}'
                )
            lines.append(
                f'modelops_http_request_duration_seconds_bucket{{{labels},le="+Inf"}} {count}'
            )
            lines.append(
                f"modelops_http_request_duration_seconds_sum{{{labels}}} "
                f"{api.state.duration_sums[(method, path)]:.9f}"
            )
            lines.append(f"modelops_http_request_duration_seconds_count{{{labels}}} {count}")
        return "\n".join(lines) + "\n"

    return api


app = create_app()
