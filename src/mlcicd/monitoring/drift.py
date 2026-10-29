"""Data drift check: compare reference (training) data with current data using Evidently."""

import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml
from evidently.metric_preset import DataDriftPreset
from evidently.report import Report

from mlcicd.data.load import load

REPORT_DIR = Path("reports")
SHIFT_COLUMN = "sepal_length"


def load_reference() -> pd.DataFrame:
    """Training data used as the drift baseline."""
    return load()


def load_current(shift: float = 0.0) -> pd.DataFrame:
    """Simulated production data: the reference with one feature shifted by `shift`."""
    df = load_reference()
    if shift:
        df[SHIFT_COLUMN] += shift
    return df


def build_report(ref: pd.DataFrame, cur: pd.DataFrame) -> Report:
    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=ref, current_data=cur)
    return report


def drift_share(report: Report) -> float:
    """Share of drifted columns, read from the DatasetDriftMetric entry of the report."""
    for entry in report.as_dict()["metrics"]:
        if entry["metric"] == "DatasetDriftMetric":
            return float(entry["result"]["share_of_drifted_columns"])
    raise ValueError("DatasetDriftMetric not found in Evidently report")


def detect_drift(
    ref: pd.DataFrame, cur: pd.DataFrame, threshold: float
) -> tuple[bool, float, Report]:
    """Return (drifted, share_of_drifted_columns, report). Drifted when share > threshold."""
    report = build_report(ref, cur)
    share = drift_share(report)
    return share > threshold, share, report


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect data drift vs. the training data.")
    parser.add_argument(
        "--shift", type=float, default=0.0, help=f"Add this to {SHIFT_COLUMN} to simulate drift."
    )
    args = parser.parse_args()

    params = yaml.safe_load(Path("params.yaml").read_text())
    threshold = params["drift"]["threshold"]

    drifted, share, report = detect_drift(load_reference(), load_current(args.shift), threshold)

    REPORT_DIR.mkdir(exist_ok=True)
    report.save_html(str(REPORT_DIR / "drift.html"))
    report.save_json(str(REPORT_DIR / "drift.json"))

    print(f"Drifted columns: {share:.2f} (threshold {threshold})")
    if drifted:
        print("DRIFT DETECTED")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
