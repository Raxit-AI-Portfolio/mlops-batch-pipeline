from pathlib import Path

import numpy as np
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from mlcicd.data.load import load
from mlcicd.features.build import build_features


@pytest.fixture
def load_data():
    RAW_PATH = Path("data/raw/iris.csv")
    return load(RAW_PATH)


@pytest.mark.model
def test_predicted_probabilities_are_reasonably_calibrated(load_data):
    # Arrange
    df = load_data
    X, y = build_features(df)
    RANDOM_STATE = 42
    TEST_SIZE = 0.3

    X_train1, X_test1, y_train1, y_test1 = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )

    pipeline1 = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(random_state=RANDOM_STATE)),
        ]
    )

    # Act
    pipeline1.fit(X_train1, y_train1)
    probabilities1 = pipeline1.predict_proba(X_test1)

    # Assert
    y_pred_npa = np.array(probabilities1)

    for i in range(0, 3):
        class_mask = y_test1 == i
        y_true_binary = class_mask.astype(int)
        y_pred_class_i = y_pred_npa[:, i]

        brier_score = brier_score_loss(y_true_binary, y_pred_class_i)

        assert brier_score < 0.1
