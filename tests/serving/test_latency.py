import statistics
import time

import numpy as np
import pytest
import yaml
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import IrisFeatures, PredictResponse

client = TestClient(app)

with open("params.yaml", "r") as file:
    params = yaml.safe_load(file)

BUDGET_MS = params.get("serving", {}).get("p95_latency_ms", 200)
NUM_CALLS = 100


@pytest.mark.serving
def test_api_p95_latency():
    latencies = []

    for _ in range(NUM_CALLS):
        start_time = time.perf_counter()
        sl, sw, pl, pw = np.random.uniform(0, 10, size=4)

        # Arrange
        iris_features = IrisFeatures(
            sepal_length=sl, sepal_width=sw, petal_length=pl, petal_width=pw
        )

        # Act
        response = client.post("/predict", json=iris_features.model_dump())

        # Assert
        PredictResponse(**response.json())
        end_time = time.perf_counter()

        # Duration in ms to match BUDGET_MS
        latencies.append((end_time - start_time) * 1000)

    # method="inclusive" matches standard percentiles (e.g., numpy)
    p95_latency = statistics.quantiles(latencies, n=100, method="inclusive")[94]
    avg_latency = statistics.mean(latencies)
    max_latency = max(latencies)

    assert p95_latency < BUDGET_MS, (
        f"p95={p95_latency:.1f}ms avg={avg_latency:.1f}ms max={max_latency:.1f}ms "
        f"budget={BUDGET_MS}ms"
    )
