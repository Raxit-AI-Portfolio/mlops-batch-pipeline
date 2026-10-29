import numpy as np
import pandas as pd
import pytest

from mlcicd.monitoring.drift import detect_drift

pytestmark = pytest.mark.unit


@pytest.fixture
def reference() -> pd.DataFrame:
    rng = np.random.default_rng(0)
    return pd.DataFrame(
        {
            "sepal_length": rng.normal(5.8, 0.8, 150),
            "sepal_width": rng.normal(3.0, 0.4, 150),
            "petal_length": rng.normal(3.7, 1.7, 150),
            "petal_width": rng.normal(1.2, 0.7, 150),
        }
    )


def test_no_drift_on_identical_data(reference):
    drifted, share, _ = detect_drift(reference, reference.copy(), threshold=0.1)
    assert not drifted
    assert share == 0.0


def test_drift_on_shifted_column(reference):
    current = reference.copy()
    current["sepal_length"] += 5.0
    drifted, share, _ = detect_drift(reference, current, threshold=0.1)
    assert drifted
    assert share == pytest.approx(0.25)


def test_threshold_controls_verdict(reference):
    current = reference.copy()
    current["sepal_length"] += 5.0
    drifted, _, _ = detect_drift(reference, current, threshold=0.5)
    assert not drifted
