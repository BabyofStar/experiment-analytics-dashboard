"""Run aggregation and baseline comparisons for experiment results."""

from __future__ import annotations

import numpy as np
import pandas as pd


GROUP_COLUMNS = ["experiment_id", "workload", "policy", "cache_size_kb"]
MATCH_COLUMNS = ["experiment_id", "workload", "cache_size_kb"]
METRIC_COLUMNS = [
    "ipc",
    "mpki",
    "miss_rate",
    "hit_rate",
    "execution_time_ms",
]
HIGHER_IS_BETTER = {"ipc", "hit_rate"}
LOWER_IS_BETTER = {"mpki", "miss_rate", "execution_time_ms"}


def summarize_runs(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Aggregate each policy/cache/workload group across its run records."""

    aggregations: dict[str, tuple[str, str]] = {
        "run_count": ("run_id", "nunique"),
    }
    for metric in METRIC_COLUMNS:
        aggregations[f"{metric}_mean"] = (metric, "mean")
        aggregations[f"{metric}_std"] = (metric, "std")
        aggregations[f"{metric}_count"] = (metric, "count")

    summary = (
        dataframe.groupby(GROUP_COLUMNS, dropna=False)
        .agg(**aggregations)
        .reset_index()
        .sort_values(["experiment_id", "workload", "cache_size_kb", "policy"])
        .reset_index(drop=True)
    )
    return summary


def build_baseline_comparison(
    dataframe: pd.DataFrame,
    baseline_policy: str = "baseline",
) -> pd.DataFrame:
    """Match each group to its baseline and calculate directional improvements."""

    summary = summarize_runs(dataframe)
    baseline = summary[summary["policy"] == baseline_policy].copy()
    baseline_columns = MATCH_COLUMNS + ["run_count"]
    baseline_columns += [f"{metric}_mean" for metric in METRIC_COLUMNS]
    baseline = baseline[baseline_columns].rename(
        columns={
            "run_count": "baseline_run_count",
            **{
                f"{metric}_mean": f"baseline_{metric}_mean"
                for metric in METRIC_COLUMNS
            },
        }
    )

    comparison = summary.merge(baseline, on=MATCH_COLUMNS, how="left")
    comparison["baseline_policy"] = baseline_policy
    comparison["baseline_matched"] = comparison["baseline_run_count"].notna()

    for metric in METRIC_COLUMNS:
        baseline_value = comparison[f"baseline_{metric}_mean"]
        current_value = comparison[f"{metric}_mean"]
        denominator = baseline_value.abs()
        if metric in HIGHER_IS_BETTER:
            improvement = (current_value - baseline_value) / denominator * 100
        elif metric in LOWER_IS_BETTER:
            improvement = (baseline_value - current_value) / denominator * 100
        else:
            raise ValueError(f"No improvement direction configured for {metric}")

        comparison[f"{metric}_improvement_pct"] = improvement.where(
            comparison["baseline_matched"] & denominator.ne(0), np.nan
        )

    return comparison.sort_values(
        ["experiment_id", "workload", "cache_size_kb", "policy"]
    ).reset_index(drop=True)


def comparison_to_long(comparison: pd.DataFrame) -> pd.DataFrame:
    """Return one row per group and metric for a readable comparison table."""

    rows: list[dict[str, object]] = []
    for _, record in comparison.iterrows():
        for metric in METRIC_COLUMNS:
            rows.append(
                {
                    "experiment_id": record["experiment_id"],
                    "workload": record["workload"],
                    "cache_size_kb": record["cache_size_kb"],
                    "policy": record["policy"],
                    "metric": metric,
                    "run_count": record["run_count"],
                    "baseline_policy": record["baseline_policy"],
                    "baseline_run_count": record["baseline_run_count"],
                    "baseline_matched": record["baseline_matched"],
                    "current_mean": record[f"{metric}_mean"],
                    "baseline_mean": record[f"baseline_{metric}_mean"],
                    "improvement_pct": record[f"{metric}_improvement_pct"],
                }
            )
    return pd.DataFrame(rows)
