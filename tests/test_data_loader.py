from pathlib import Path

import pandas as pd

from src.data_loader import (
    inspect_data_quality,
    load_experiment_data,
    normalize_columns,
    prepare_dataframe,
)


SAMPLE_PATH = Path(__file__).parents[1] / "data" / "sample_experiment.csv"


def test_sample_data_loads_cleanly():
    dataframe = load_experiment_data(SAMPLE_PATH)
    quality = inspect_data_quality(dataframe)

    assert dataframe.shape == (12, 15)
    assert quality["error_count"] == 0
    assert quality["warning_count"] == 0
    assert str(dataframe["experiment_id"].dtype) == "string"
    assert str(dataframe["execution_time_ms"].dtype) == "float64"


def test_column_aliases_and_numeric_values_are_normalized():
    raw = pd.DataFrame(
        {
            "Experiment ID": ["exp_1"],
            "Cache Size": ["32"],
            "Run": ["run_01"],
            "Execution Time": ["12.5"],
        }
    )

    normalized = prepare_dataframe(raw)

    assert list(normalized.columns) == [
        "experiment_id",
        "cache_size_kb",
        "run_id",
        "execution_time_ms",
    ]
    assert normalized.loc[0, "cache_size_kb"] == 32
    assert normalized.loc[0, "execution_time_ms"] == 12.5


def test_quality_check_reports_missing_values_and_invalid_rates():
    dataframe = pd.DataFrame(
        {
            "experiment_id": ["exp_1"],
            "workload": ["matrix"],
            "policy": ["baseline"],
            "cache_size_kb": [32],
            "run_id": ["run_01"],
            "instructions": [100],
            "cycles": [50],
            "accesses": [10],
            "misses": [2],
            "hits": [8],
            "ipc": [2.0],
            "mpki": [20.0],
            "miss_rate": [1.2],
            "hit_rate": [None],
            "execution_time_ms": [5.0],
        }
    )

    quality = inspect_data_quality(dataframe)
    checks = {issue["check"] for issue in quality["issues"]}

    assert quality["error_count"] >= 2
    assert "missing_values" in checks
    assert "rate_range" in checks
