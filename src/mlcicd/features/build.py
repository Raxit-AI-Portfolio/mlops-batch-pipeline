from pandas import DataFrame

SPECIES_MAPPING = {"setosa": 0, "versicolor": 1, "virginica": 2}
FEATURE_COLUMNS = ["sepal_length", "sepal_width", "petal_length", "petal_width"]


def build_features(df: DataFrame):
    X = df[FEATURE_COLUMNS]
    y = df["species"].map(SPECIES_MAPPING)

    return X, y
