from datetime import timedelta

from feast import Field, FeatureView, FileSource
from feast.types import Float32

from entities import iris_entity

iris_source = FileSource(
    path="data/iris_features.parquet",
    timestamp_field="event_timestamp",
)

iris_features_view = FeatureView(
    name="iris_features",
    entities=[iris_entity],
    ttl=timedelta(days=3650),
    schema=[
        Field(name="sepal_length", dtype=Float32),
        Field(name="sepal_width", dtype=Float32),
        Field(name="petal_length", dtype=Float32),
        Field(name="petal_width", dtype=Float32),
    ],
    online=True,
    source=iris_source,
)
