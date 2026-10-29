from pathlib import Path

import pandas as pd
from sklearn.datasets import load_iris

RAW_PATH = Path("data/raw/iris.csv")


def load(path: Path = RAW_PATH) -> pd.DataFrame:
    return pd.read_csv(path).drop_duplicates().reset_index(drop=True)


def generate_raw(path: Path = RAW_PATH) -> None:
    iris = load_iris()

    columns = [name.replace(" (cm)", "").replace(" ", "_") for name in iris.feature_names]
    df = pd.DataFrame(data=iris.data, columns=columns)
    df["species"] = [iris.target_names[t] for t in iris.target]

    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


if __name__ == "__main__":
    if not RAW_PATH.is_file():
        generate_raw(RAW_PATH)
    print(load(RAW_PATH).head())
