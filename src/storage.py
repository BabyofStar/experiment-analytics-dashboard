"""SQLite persistence for saved dashboard analysis snapshots."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3

import pandas as pd


DEFAULT_DB_PATH = Path(__file__).parents[1] / "data" / "experiment_analytics.sqlite3"


def _connect(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS analysis_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_name TEXT NOT NULL,
            language TEXT NOT NULL,
            baseline_policy TEXT NOT NULL,
            selected_workloads TEXT NOT NULL,
            selected_policies TEXT NOT NULL,
            selected_cache_sizes TEXT NOT NULL,
            filtered_row_count INTEGER NOT NULL,
            average_ipc REAL,
            average_mpki REAL,
            average_miss_rate REAL,
            average_execution_time_ms REAL
        )
        """
    )
    connection.commit()
    return connection


def save_analysis_run(
    db_path: str | Path = DEFAULT_DB_PATH,
    *,
    source_name: str,
    language: str,
    baseline_policy: str,
    selected_workloads: list[str],
    selected_policies: list[str],
    selected_cache_sizes: list[int],
    filtered_row_count: int,
    average_ipc: float,
    average_mpki: float,
    average_miss_rate: float,
    average_execution_time_ms: float,
) -> int:
    """Persist the current selections and KPI values and return its id."""

    with _connect(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO analysis_runs (
                created_at, source_name, language, baseline_policy,
                selected_workloads, selected_policies, selected_cache_sizes,
                filtered_row_count, average_ipc, average_mpki,
                average_miss_rate, average_execution_time_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
                source_name,
                language,
                baseline_policy,
                json.dumps(selected_workloads, ensure_ascii=False),
                json.dumps(selected_policies, ensure_ascii=False),
                json.dumps(selected_cache_sizes),
                int(filtered_row_count),
                float(average_ipc),
                float(average_mpki),
                float(average_miss_rate),
                float(average_execution_time_ms),
            ),
        )
        return int(cursor.lastrowid)


def fetch_recent_analysis_runs(
    db_path: str | Path = DEFAULT_DB_PATH,
    limit: int = 10,
) -> pd.DataFrame:
    """Return the most recent saved analysis snapshots."""

    safe_limit = max(1, min(int(limit), 100))
    with _connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT id, created_at, source_name, language, baseline_policy,
                   selected_workloads, selected_policies, selected_cache_sizes,
                   filtered_row_count, average_ipc, average_mpki,
                   average_miss_rate, average_execution_time_ms
            FROM analysis_runs
            ORDER BY id DESC
            LIMIT ?
            """,
            (safe_limit,),
        ).fetchall()

    return pd.DataFrame([dict(row) for row in rows])
