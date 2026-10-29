import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest
from feast import FeatureStore
from feast.infra.offline_stores.dask import DaskOfflineStoreConfig
from feast.infra.online_stores.sqlite import SqliteOnlineStoreConfig
from feast.repo_config import RepoConfig

REPO_ROOT = Path(__file__).resolve().parents[2]
FEATURE_REPO = REPO_ROOT / "feature_repo"
sys.path.insert(0, str(FEATURE_REPO))

from entities import iris_entity  # noqa: E402
from feature_views import iris_features_view  # noqa: E402
import main as feature_main  # noqa: E402

FEATURE_REFS = ["iris_features:sepal_length", "iris_features:sepal_width"]


@pytest.mark.feast
def test_online_offline_parity(monkeypatch):
    """Values materialized into the online store must match the offline source exactly."""
    feature_main.generate_feature_data()

    # Run from feature_repo so the FileSource's relative "data/..." path resolves,
    # and so the registry/online-store paths stay relative (Feast's registry path
    # parsing treats a Windows drive letter like "C:\..." as a URI scheme).
    monkeypatch.chdir(FEATURE_REPO)

    repo_config = RepoConfig(
        project="test_iris",
        provider="local",
        registry="data/test_registry.db",
        online_store=SqliteOnlineStoreConfig(path="data/test_online.db"),
        offline_store=DaskOfflineStoreConfig(),
        entity_key_serialization_version=2,
    )
    store = FeatureStore(config=repo_config)
    store.apply([iris_entity, iris_features_view])
    store.materialize_incremental(datetime.now(timezone.utc))

    entity_df = pd.DataFrame(
        {
            "iris_id": [0, 1, 2],
            "event_timestamp": [datetime.now(timezone.utc)] * 3,
        }
    )

    offline_df = store.get_historical_features(
        entity_df=entity_df, features=FEATURE_REFS
    ).to_df()
    online_df = store.get_online_features(
        features=FEATURE_REFS,
        entity_rows=[{"iris_id": iid} for iid in entity_df["iris_id"]],
    ).to_df()

    merged = offline_df.merge(online_df, on="iris_id", suffixes=("_offline", "_online"))
    for col in ["sepal_length", "sepal_width"]:
        assert (merged[f"{col}_offline"] - merged[f"{col}_online"]).abs().max() < 1e-6
