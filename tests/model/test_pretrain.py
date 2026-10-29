import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from mlcicd.features.build import build_features


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
def test_features_are_model_ready(get_sample_dataframe, get_feature_columns):
    # Arrange
    df = get_sample_dataframe

    # Act
    X, y = build_features(df)

    # Assert
    for f in get_feature_columns:
        assert pd.api.types.is_float_dtype(X[f])

    assert pd.api.types.is_integer_dtype(y)


@pytest.mark.model
def test_build_features_no_nan_in_output(get_sample_dataframe):
    # Arrange
    df = get_sample_dataframe

    # Act
    X, y = build_features(df)

    # Assert
    assert not X.isna().any().any()
    assert not y.isna().any()


@pytest.mark.model
def test_pipeline_overfits_single_batch(get_sample_dataframe):
    # Arrange
    df = get_sample_dataframe
    X, y = build_features(df)

    # Act
    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(random_state=42)),
        ]
    )
    pipeline.fit(X, y)

    # Assert
    assert pipeline.score(X, y) >= 0.9
