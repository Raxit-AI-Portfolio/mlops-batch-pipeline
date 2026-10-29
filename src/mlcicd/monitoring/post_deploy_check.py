import sys
import time

import mlflow
import requests
from mlflow import MlflowClient
from prometheus_client.parser import text_string_to_metric_families

import mlcicd.config as cf

MODEL_NAME = "IrisClassifier"
ATTEMPTS, DELAY_S = 12, 10


def expected_version() -> int:
    mlflow.set_tracking_uri(cf.MLFLOW_TRACKING_URI)
    versions = MlflowClient().search_model_versions(f"name='{MODEL_NAME}'")
    if not versions:
        raise RuntimeError(f"No registered versions found for model '{MODEL_NAME}'.")
    return max(int(v.version) for v in versions)


def served_version(app_url: str) -> int:
    text = requests.get(f"{app_url}/metrics", timeout=10).text
    samples = [
        s
        for family in text_string_to_metric_families(text)
        if family.name == "model_version"
        for s in family.samples
    ]
    return int(samples[0].value)


def main() -> int:
    expected = expected_version()
    for attempt in range(1, ATTEMPTS + 1):
        try:
            served = served_version(cf.APP_URL)
            if served == expected:
                print(f"OK: serving model_version={served} matches registry")
                return 0
            print(f"[{attempt}/{ATTEMPTS}] serving {served}, registry has {expected}")
        except (requests.RequestException, IndexError, ValueError) as e:
            print(f"[{attempt}/{ATTEMPTS}] check failed: {e}")
        time.sleep(DELAY_S)
    print(f"FAIL: could not confirm model_version={expected} at {cf.APP_URL}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
