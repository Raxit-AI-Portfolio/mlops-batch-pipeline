import math

import pandas as pd
import pytest

from mlcicd.features.build import build_features


def get_rows():
    return [
        [5.1, 3.5, 1.4, 0.2, "setosa"],
        [4.9, 3.0, 1.4, 0.2, "setosa"],
        [7.0, 3.2, 4.7, 1.4, "versicolor"],
        [6.4, 3.2, 4.5, 1.5, "versicolor"],
        [6.3, 3.3, 6.0, 2.5, "virginica"],
        [5.8, 2.7, 5.1, 1.9, "virginica"],
    ]


def get_columns():
    return ["sepal_length", "sepal_width", "petal_length", "petal_width", "species"]


def get_feature_columns():
    return ["sepal_length", "sepal_width", "petal_length", "petal_width"]


def get_sample_dataframe():
    # Define rows as a list of lists
    rows = get_rows()
    columns = get_columns()
    return pd.DataFrame(rows, columns=columns)


@pytest.mark.unit
def test_build_features_returns_expected_columns():
    # Arrange
    df = get_sample_dataframe()

    # Act
    X, y = build_features(df)

    # Assert
    assert set(X.columns.tolist()).issubset(set(get_columns()))
    assert y.name == "species"


@pytest.mark.unit
def test_build_features_maps_species_to_correct_labels():
    # Arrange
    df = get_sample_dataframe()
    SPECIES_MAPPING = {"setosa": 0, "versicolor": 1, "virginica": 2}

    # Act
    X, y = build_features(df)

    # Assert
    assert set(y.unique().tolist()).issubset(set(SPECIES_MAPPING.values()))


@pytest.mark.unit
def test_build_features_preserves_row_count():
    # Arrange
    df = get_sample_dataframe()

    # Act
    X, y = build_features(df)

    # Assert
    assert len(X) == len(get_rows())
    assert len(y) == len(get_rows())


@pytest.mark.unit
def test_build_features_unknown_species_maps_to_nan():
    # Arrange
    df = get_sample_dataframe()
    df.loc[len(df)] = [5.1, 3.5, 1.4, 0.2, "setosa-a"]

    # Act
    X, y = build_features(df)

    # Assert
    assert math.isnan(y.iloc[-1])


@pytest.mark.unit
def test_build_features_x_y_index_alignment():
    # Arrange
    df = get_sample_dataframe()
    SPECIES_MAPPING = {"setosa": 0, "versicolor": 1, "virginica": 2}

    # Act
    X, y = build_features(df)

    # Assert
    for f in get_feature_columns():
        assert df[f].iloc[-1] == X[f].iloc[-1]

    assert y.iloc[-1] == SPECIES_MAPPING[df["species"].iloc[-1]]
