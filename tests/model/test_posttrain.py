import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from mlcicd.features.build import SPECIES_MAPPING, build_features


@pytest.fixture
def get_rows():
    return [
        [5.1, 3.5, 1.4, 0.2, "setosa"],
        [4.9, 3.0, 1.4, 0.2, "setosa"],
        [4.6, 3.1, 1.5, 0.2, "setosa"],
        [5.0, 3.6, 1.4, 0.2, "setosa"],
        [5.4, 3.9, 1.7, 0.4, "setosa"],
        [7.0, 3.2, 4.7, 1.4, "versicolor"],
        [6.4, 3.2, 4.5, 1.5, "versicolor"],
        [6.5, 2.8, 4.6, 1.5, "versicolor"],
        [5.7, 2.8, 4.5, 1.3, "versicolor"],
        [6.3, 3.3, 4.7, 1.6, "versicolor"],
        [6.3, 3.3, 6.0, 2.5, "virginica"],
        [5.8, 2.7, 5.1, 1.9, "virginica"],
        [6.5, 3.0, 5.2, 2.0, "virginica"],
        [6.2, 3.4, 5.4, 2.3, "virginica"],
        [5.9, 3.0, 5.1, 1.8, "virginica"],
    ]


@pytest.fixture
def get_columns():
    return ["sepal_length", "sepal_width", "petal_length", "petal_width", "species"]


@pytest.fixture
def get_feature_columns():
    return ["sepal_length", "sepal_width", "petal_length", "petal_width"]


@pytest.fixture
def get_sample_dataframe(get_rows, get_columns):
    # Define rows as a list of lists
    rows = get_rows
    columns = get_columns
    return pd.DataFrame(rows, columns=columns)


@pytest.mark.model
def test_prediction_invariant_to_irrelevant_perturbation(get_sample_dataframe, get_feature_columns):
    # Arrange
    df = get_sample_dataframe
    X, y = build_features(df)

    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(random_state=42)),
        ]
    )
    pipeline.fit(X, y)

    test_row = [7.4, 2.8, 6.1, 1.9]
    perturbation_row = [7.4 + 1e-6, 2.8, 6.1, 1.9]

    # Act
    prediction_before = pipeline.predict([test_row])
    prediction_after = pipeline.predict([perturbation_row])

    # Assert
    assert prediction_before[0] == prediction_after[0]


@pytest.mark.model
def test_directional_expectation_on_feature_change(get_sample_dataframe):
    # Arrange
    df = get_sample_dataframe
    X, y = build_features(df)

    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(random_state=42)),
        ]
    )
    virginica_id = SPECIES_MAPPING["virginica"]

    versicolor_row = [6.0, 2.7, 5.1, 1.6]
    versicolor_fc_row = [6.0, 2.7, 5.1 + 1.0, 1.6]

    # Act
    pipeline.fit(X, y)
    prob_before = pipeline.predict_proba([versicolor_row])[0, virginica_id]
    prob_after = pipeline.predict_proba([versicolor_fc_row])[0, virginica_id]

    # Assert
    assert prob_after > prob_before


@pytest.mark.model
def test_slice_metrics_per_species(get_sample_dataframe):
    # Arrange
    df = get_sample_dataframe
    X, y = build_features(df)

    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(random_state=42)),
        ]
    )

    # Act
    pipeline.fit(X, y)

    # Assert
    y_pred = pipeline.predict(X)
    overall_accuracy = accuracy_score(y, y_pred)

    y_npa = np.array(y)
    y_pred_npa = np.array(y_pred)

    for i in range(0, 3):
        class_mask = y == i
        y_filtered = y_npa[class_mask]
        y_pred_filtered = y_pred_npa[class_mask]

        # 3. Calculate accuracy on the filtered subset
        class_accuracy = accuracy_score(y_filtered, y_pred_filtered)

        assert class_accuracy >= overall_accuracy
