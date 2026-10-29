import json
from pathlib import Path

import mlflow
import mlflow.sklearn
import yaml
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import mlcicd.config as cf
import mlcicd.data.load as ld
import mlcicd.features.build as bl

RAW_PATH = Path("data/raw/iris.csv")

df = ld.load(RAW_PATH)
X, y = bl.build_features(df)

with open("params.yaml", "r") as file:
    params = yaml.safe_load(file)

TEST_SIZE = params.get("train", {}).get("test_size", 0.3)
RANDOM_STATE = params.get("train", {}).get("random_state", 42)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
)

pipeline = Pipeline(
    [
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(random_state=RANDOM_STATE)),
    ]
)

pipeline.fit(X_train, y_train)

predictions = pipeline.predict(X_test)

accuracy = accuracy_score(y_test, predictions)
# average='macro' required for multi-class
precision = precision_score(y_test, predictions, average="macro")
recall = recall_score(y_test, predictions, average="macro")
f1_metrics = f1_score(y_test, predictions, average="macro")

metrics = {
    "accuracy": accuracy,
    "precision_macro": precision,
    "recall_macro": recall,
    "f1_macro": f1_metrics,
}

mlflow.set_tracking_uri(cf.MLFLOW_TRACKING_URI)
mlflow.set_experiment("iris-classifier")

with mlflow.start_run() as run:
    # Log individual hyperparameters from the classifier step
    mlflow.log_param("test_size", TEST_SIZE)
    mlflow.log_param("random_state", RANDOM_STATE)
    mlflow.log_param("model_type", "LogisticRegression")

    # Log all calculated metrics at once
    mlflow.log_metrics(metrics)

    # Log the entire pipeline object as an artifact
    mlflow.sklearn.log_model(sk_model=pipeline, artifact_path="sklearn-pipeline-model")

Path("metrics.json").write_text(json.dumps(metrics, indent=2))
