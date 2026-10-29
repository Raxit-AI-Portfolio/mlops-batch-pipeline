import pytest

from mlcicd.training.evaluate import find_regressions


@pytest.mark.regression
def test_metrics_not_regressed_vs_baseline():
    # Arrange
    metrics = {"accuracy": 0.97, "precision_macro": 0.96, "recall_macro": 0.97, "f1_macro": 0.96}
    baseline = {"accuracy": 1.0, "precision_macro": 1.0, "recall_macro": 1.0, "f1_macro": 1.0}
    tolerance = 0.05

    # Act
    regressions = find_regressions(metrics, baseline, tolerance)

    # Assert
    assert regressions == []


@pytest.mark.regression
def test_metrics_below_tolerance_flagged_as_regression():
    # Arrange
    metrics = {"accuracy": 0.90, "precision_macro": 1.0, "recall_macro": 1.0, "f1_macro": 1.0}
    baseline = {"accuracy": 1.0, "precision_macro": 1.0, "recall_macro": 1.0, "f1_macro": 1.0}
    tolerance = 0.02

    # Act
    regressions = find_regressions(metrics, baseline, tolerance)

    # Assert
    assert len(regressions) == 1
    assert "accuracy" in regressions[0]


@pytest.mark.regression
def test_metrics_within_tolerance_not_flagged():
    # Arrange
    metrics = {"accuracy": 0.99}
    baseline = {"accuracy": 1.0}
    tolerance = 0.02

    # Act
    regressions = find_regressions(metrics, baseline, tolerance)

    # Assert
    assert regressions == []
