import sys
from pathlib import Path

from pandas import DataFrame
from pandera import Check, Column, DataFrameSchema
from pandera.errors import SchemaError

from mlcicd.data.load import load

RAW_PATH = Path("data/raw/iris.csv")
ALLOWED_SPECIES = ["setosa", "versicolor", "virginica"]

iris_schema = DataFrameSchema(
    {
        "sepal_length": Column(float, nullable=False, checks=Check.between(0.0, 10.0)),
        "sepal_width": Column(float, nullable=False, checks=Check.between(0.0, 10.0)),
        "petal_length": Column(float, nullable=False, checks=Check.between(0.0, 10.0)),
        "petal_width": Column(float, nullable=False, checks=Check.between(0.0, 10.0)),
        "species": Column(str, nullable=False, checks=Check.isin(ALLOWED_SPECIES)),
    },
    checks=Check(lambda df: ~df.duplicated().any(), error="duplicate rows found"),
)


def validate(df: DataFrame):
    return iris_schema.validate(df)


if __name__ == "__main__":
    try:
        df = load(RAW_PATH)
        validate(df)

        print("Schema validation passed.")
        sys.exit(0)
    except SchemaError:
        print("Schema validation error.")
        sys.exit(1)
