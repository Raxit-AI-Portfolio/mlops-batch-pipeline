import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import SPECIES_LABELS, IrisFeatures, PredictResponse

client = TestClient(app)


@pytest.mark.serving
def test_predict_ok():
    # Arrange
    iris_features = IrisFeatures(
        sepal_length=5.0, sepal_width=3.6, petal_length=1.4, petal_width=0.2
    )

    # Act
    response = client.post("/predict", json=iris_features.model_dump())

    # Assert
    prediction = PredictResponse(**response.json())
    assert response.status_code == 200
    assert prediction.species_id in SPECIES_LABELS.keys()
    assert prediction.species in SPECIES_LABELS.values()


@pytest.mark.serving
def test_predict_invalid_payload_rejected():
    # sepal_length is negative, outside the schema's [0.0, 10.0] bound
    payload = {"sepal_length": -1.0, "sepal_width": 3.6, "petal_length": 1.4, "petal_width": 0.2}

    response = client.post("/predict", json=payload)

    assert response.status_code == 422


@pytest.mark.serving
def test_metrics_exposes_model_version():
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "model_version" in response.text


@pytest.mark.serving
def test_model_loaded_from_registry_not_local_path(monkeypatch):
    captured_uri = {}

    def fake_load_model(uri):
        captured_uri["value"] = uri
        return "fake-model"

    monkeypatch.setattr("app.model_loader.load_model", fake_load_model)

    from app.model_loader import load_model_from_registry

    load_model_from_registry("3")

    assert captured_uri["value"].startswith("models:/")
