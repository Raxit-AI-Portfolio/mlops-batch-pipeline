import json
from pathlib import Path

import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from mlcicd.data.load import load
from mlcicd.features.build import SPECIES_MAPPING, build_features


@pytest.mark.regression
def test_golden_set_predictions_stable():
    # Arrange
    golden_json_path = Path("tests/fixtures/golden_set.json")

    with open(golden_json_path, "r") as file:
        golden_rows = json.load(file)

    df = load()
    X_train, y_train = build_features(df)

    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(random_state=42)),
        ]
    )

    # Act
    pipeline.fit(X_train, y_train)

    golden_X = pd.DataFrame([row["features"] for row in golden_rows], columns=X_train.columns)
    predictions = pipeline.predict(golden_X)

    # Assert
    for row, prediction in zip(golden_rows, predictions):
        expected = SPECIES_MAPPING[row["expected_species"]]
        assert (
            prediction == expected
        ), f"{row['features']} expected {row['expected_species']}, got label {prediction}"
