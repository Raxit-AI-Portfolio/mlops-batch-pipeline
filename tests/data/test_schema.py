import pandas as pd
import pytest
from pandera.errors import SchemaError

from mlcicd.data.schema import validate


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


def assert_exception(df):
    with pytest.raises(SchemaError):
        validate(df)


@pytest.mark.data
def test_valid_dataframe_passes_schema():
    # Arrange
    df = get_sample_dataframe()

    # Act & Assert
    try:
        validate(df)
    except SchemaError:
        pytest.fail("Invalid Schema")


@pytest.mark.data
def test_null_value_fails_schema():
    # Arrange
    df = get_sample_dataframe()
    df.loc[len(df)] = [None, 3.5, 1.4, 0.2, "setosa"]

    # Act & Assert
    assert_exception(df)


@pytest.mark.data
def test_out_of_range_value_fails_schema():
    # Arrange
    df = get_sample_dataframe()
    df.loc[len(df)] = [12, 3.5, 1.4, 0.2, "setosa"]

    # Act & Assert
    assert_exception(df)


@pytest.mark.data
def test_invalid_species_fails_schema():
    # Arrange
    df = get_sample_dataframe()
    df.loc[len(df)] = [12, 3.5, 1.4, 0.2, "setosa-a"]

    # Act & Assert
    assert_exception(df)


@pytest.mark.data
def test_no_duplicate_rows():
    # Arrange
    df = get_sample_dataframe()
    df.loc[len(df)] = df.loc[len(df) - 1]

    # Act & Assert
    assert_exception(df)
