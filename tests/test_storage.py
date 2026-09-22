from pathlib import Path

from src.storage import fetch_recent_analysis_runs, save_analysis_run


def test_save_and_fetch_analysis_snapshot(tmp_path: Path):
    database_path = tmp_path / "analysis.sqlite3"

    run_id = save_analysis_run(
        database_path,
        source_name="sample_experiment.csv",
        language="zh",
        baseline_policy="baseline",
        selected_workloads=["matrix"],
        selected_policies=["baseline", "lru"],
        selected_cache_sizes=[32, 64],
        filtered_row_count=8,
        average_ipc=2.05,
        average_mpki=28.0,
        average_miss_rate=0.14,
        average_execution_time_ms=11.5,
    )

    recent = fetch_recent_analysis_runs(database_path)

    assert run_id == 1
    assert len(recent) == 1
    assert recent.loc[0, "baseline_policy"] == "baseline"
    assert recent.loc[0, "filtered_row_count"] == 8
