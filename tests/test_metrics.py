from pathlib import Path

import numpy as np

from src.data_loader import load_experiment_data
from src.metrics import (
    build_baseline_comparison,
    comparison_to_long,
    summarize_runs,
)


SAMPLE_PATH = Path(__file__).parents[1] / "data" / "sample_experiment.csv"


def sample_dataframe():
    return load_experiment_data(SAMPLE_PATH)


def test_summarize_runs_calculates_mean_std_and_sample_count():
    summary = summarize_runs(sample_dataframe())
    row = summary[
        (summary["workload"] == "matrix")
        & (summary["policy"] == "lru")
        & (summary["cache_size_kb"] == 32)
    ].iloc[0]

    assert len(summary) == 8
    assert row["run_count"] == 2
    assert row["ipc_count"] == 2
    assert row["ipc_mean"] == 2.12
    assert np.isclose(row["ipc_std"], np.std([2.13, 2.11], ddof=1))


def test_baseline_comparison_uses_directional_improvement_rates():
    comparison = build_baseline_comparison(sample_dataframe())
    row = comparison[
        (comparison["workload"] == "matrix")
        & (comparison["policy"] == "lru")
        & (comparison["cache_size_kb"] == 32)
    ].iloc[0]

    assert bool(row["baseline_matched"]) is True
    assert row["baseline_run_count"] == 2
    assert row["ipc_improvement_pct"] > 0
    assert row["mpki_improvement_pct"] > 0
    assert row["miss_rate_improvement_pct"] > 0
    assert row["execution_time_ms_improvement_pct"] > 0


def test_missing_baseline_leaves_improvement_unavailable():
    dataframe = sample_dataframe()
    only_lru = dataframe[dataframe["policy"] == "lru"]

    comparison = build_baseline_comparison(only_lru, baseline_policy="baseline")

    assert not comparison["baseline_matched"].any()
    assert comparison["ipc_improvement_pct"].isna().all()


def test_comparison_to_long_has_one_row_per_metric():
    comparison = build_baseline_comparison(sample_dataframe())
    detail = comparison_to_long(comparison)

    assert len(detail) == len(comparison) * 5
    assert set(detail["metric"]) == {
        "ipc",
        "mpki",
        "miss_rate",
        "hit_rate",
        "execution_time_ms",
    }
