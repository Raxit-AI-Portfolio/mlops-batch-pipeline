import mlflow

import mlcicd.config as cf

mlflow.set_tracking_uri(cf.MLFLOW_TRACKING_URI)

runs = mlflow.search_runs(
    experiment_names=["iris-classifier"],
    order_by=["start_time DESC"],
    max_results=1,
)

if runs.empty:
    raise RuntimeError("No runs found in experiment 'iris-classifier' to register.")

recent_run_id = runs.iloc[0]["run_id"]

mlflow.register_model(f"runs:/{recent_run_id}/sklearn-pipeline-model", "IrisClassifier")
