"""Builds the Feast offline source parquet from the DVC-tracked iris.csv.

Iris has no natural entity key or timestamp, so this assigns a row-index
`iris_id` and a current `event_timestamp` -- enough for the train/serve
skew demo in Phase 9 (tests/feast/test_skew.py).
"""

from datetime import datetime, timezone
from pathlib import Path

from mlcicd.data.load import load

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = REPO_ROOT / "data" / "raw" / "iris.csv"
OUT_PATH = Path(__file__).resolve().parent / "data" / "iris_features.parquet"


def generate_feature_data() -> None:
    df = load(RAW_PATH).reset_index().rename(columns={"index": "iris_id"})
    df["event_timestamp"] = datetime.now(timezone.utc)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_PATH, index=False)


if __name__ == "__main__":
    generate_feature_data()
