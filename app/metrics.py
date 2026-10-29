from prometheus_client import Gauge

model_version_gauge = Gauge("model_version", "Registry version of the model currently served")


def set_model_version(version: str) -> None:
    model_version_gauge.set(int(version))
