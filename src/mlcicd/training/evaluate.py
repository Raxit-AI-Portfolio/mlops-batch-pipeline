import json
import sys
from pathlib import Path

import yaml


def find_regressions(metrics: dict, baseline: dict, tolerance: float) -> list[str]:
    regressions = []
    for k, v in metrics.items():
        baseline_value = baseline.get(k, 0)

        if v < baseline_value - tolerance:
            regressions.append(f"{k}: {v} < baseline {baseline_value} - tolerance {tolerance}")

    return regressions


if __name__ == "__main__":
    with open("metrics.json", "r") as file:
        metrics_dict = json.load(file)

    baselines_path = Path("baselines/metrics_baseline.json")

    with open(baselines_path, "r") as file:
        metrics_baseline_dict = json.load(file)

    with open("params.yaml", "r") as file:
        params = yaml.safe_load(file)

    TOLERANCE = params.get("evaluate", {}).get("tolerance", 0.02)

    regressions = find_regressions(metrics_dict, metrics_baseline_dict, TOLERANCE)

    if regressions:
        print("Evaluation FAILED, regression detected:")
        for r in regressions:
            print(f"  {r}")
        sys.exit(1)

    print("Evaluation passed, no regression beyond tolerance.")
    sys.exit(0)
