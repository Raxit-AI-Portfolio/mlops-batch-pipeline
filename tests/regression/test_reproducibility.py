import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
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


@pytest.mark.regression
def test_train_is_reproducible_given_same_seed(get_sample_dataframe):
    # Arrange
    df = get_sample_dataframe
    X, y = build_features(df)
    RANDOM_STATE = 42
    TEST_SIZE = 0.3

    X_train1, X_test1, y_train1, y_test1 = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    X_train2, X_test2, y_train2, y_test2 = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )

    pipeline1 = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(random_state=RANDOM_STATE)),
        ]
    )
    pipeline2 = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(random_state=RANDOM_STATE)),
        ]
    )

    # Act
    pipeline1.fit(X_train1, y_train1)
    predictions1 = pipeline1.predict(X_test1)
    accuracy1 = accuracy_score(y_test1, predictions1)
    # average='macro' required for multi-class
    precision1 = precision_score(y_test1, predictions1, average="macro")
    recall1 = recall_score(y_test1, predictions1, average="macro")
    f1_metrics1 = f1_score(y_test1, predictions1, average="macro")

    pipeline2.fit(X_train2, y_train2)
    predictions2 = pipeline2.predict(X_test2)
    accuracy2 = accuracy_score(y_test2, predictions2)
    precision2 = precision_score(y_test2, predictions2, average="macro")
    recall2 = recall_score(y_test2, predictions2, average="macro")
    f1_metrics2 = f1_score(y_test2, predictions2, average="macro")

    # Assert
    pd.testing.assert_frame_equal(X_train1, X_train2)
    pd.testing.assert_frame_equal(X_test1, X_test2)

    assert accuracy1 == accuracy2
    assert precision1 == precision2
    assert recall1 == recall2
    assert f1_metrics1 == f1_metrics2
