import mlflow
from mlflow import MlflowClient
from mlflow.pyfunc import load_model

import mlcicd.config as cf

mlflow.set_tracking_uri(cf.MLFLOW_TRACKING_URI)

MODEL_NAME = "IrisClassifier"


def get_model_version() -> str:
    client = MlflowClient()
    versions = client.search_model_versions(f"name='{MODEL_NAME}'")

    if not versions:
        raise RuntimeError(f"No registered versions found for model '{MODEL_NAME}'.")

    latest = max(versions, key=lambda v: int(v.version))
    return latest.version


def load_model_from_registry(version: str):
    return load_model(f"models:/{MODEL_NAME}/{version}")
