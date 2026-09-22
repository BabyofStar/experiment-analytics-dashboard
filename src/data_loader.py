"""Loading, normalization, and quality checks for experiment result files."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re
from typing import BinaryIO

import pandas as pd


REQUIRED_COLUMNS = [
    "experiment_id",
    "workload",
    "policy",
    "cache_size_kb",
    "run_id",
    "instructions",
    "cycles",
    "accesses",
    "misses",
    "hits",
    "ipc",
    "mpki",
    "miss_rate",
    "hit_rate",
    "execution_time_ms",
]

TEXT_COLUMNS = ["experiment_id", "workload", "policy", "run_id"]
NUMERIC_COLUMNS = [column for column in REQUIRED_COLUMNS if column not in TEXT_COLUMNS]

COLUMN_ALIASES = {
    "experiment": "experiment_id",
    "experimentid": "experiment_id",
    "cache_size": "cache_size_kb",
    "cache_size_kbytes": "cache_size_kb",
    "cache_kb": "cache_size_kb",
    "run": "run_id",
    "execution_time": "execution_time_ms",
    "execution_time_milliseconds": "execution_time_ms",
}


def _normalize_column_name(name: object) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", str(name).strip().lower())
    normalized = normalized.strip("_")
    return COLUMN_ALIASES.get(normalized, normalized)


def normalize_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with stable snake_case column names and known aliases."""

    normalized_names = [_normalize_column_name(column) for column in dataframe.columns]
    if len(normalized_names) != len(set(normalized_names)):
        duplicates = sorted(
            {
                name
                for name in normalized_names
                if normalized_names.count(name) > 1
            }
        )
        raise ValueError(
            "列名标准化后出现重复列：" + ", ".join(duplicates)
        )

    result = dataframe.copy()
    result.columns = normalized_names
    return result


def coerce_types(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Convert text and metric columns to predictable pandas dtypes."""

    result = dataframe.copy()
    for column in TEXT_COLUMNS:
        if column in result.columns:
            result[column] = result[column].astype("string").str.strip()
    for column in NUMERIC_COLUMNS:
        if column in result.columns:
            result[column] = pd.to_numeric(result[column], errors="coerce")
    return result


def prepare_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Normalize headers and coerce values without silently dropping records."""

    return coerce_types(normalize_columns(dataframe))


def load_experiment_data(source: str | Path | BinaryIO | object) -> pd.DataFrame:
    """Load CSV/XLSX data from a path or a Streamlit UploadedFile-like object."""

    source_name = str(getattr(source, "name", source)).lower()
    suffix = Path(source_name).suffix.lower()

    if hasattr(source, "read") and not isinstance(source, (str, Path)):
        source.seek(0)
        content = source.read()
        source.seek(0)
        file_source = BytesIO(content) if isinstance(content, bytes) else content
    else:
        file_source = source

    if suffix == ".xlsx":
        dataframe = pd.read_excel(file_source)
    elif suffix == ".csv" or not suffix:
        dataframe = pd.read_csv(file_source)
    else:
        raise ValueError("仅支持 CSV 或 XLSX 文件。")

    return prepare_dataframe(dataframe)


def inspect_data_quality(dataframe: pd.DataFrame) -> dict:
    """Return concise, machine-readable quality checks for the dashboard."""

    issues: list[dict[str, object]] = []
    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in dataframe.columns
    ]
    if missing_columns:
        issues.append(
            {
                "severity": "error",
                "check": "required_columns",
                "count": len(missing_columns),
                "details": "缺少：" + ", ".join(missing_columns),
            }
        )

    missing_values = dataframe.isna().sum()
    missing_values = missing_values[missing_values > 0]
    for column, count in missing_values.items():
        issues.append(
            {
                "severity": "error",
                "check": "missing_values",
                "count": int(count),
                "details": f"列 {column} 存在 {int(count)} 个缺失值",
            }
        )

    duplicate_rows = int(dataframe.duplicated().sum())
    if duplicate_rows:
        issues.append(
            {
                "severity": "warning",
                "check": "duplicate_rows",
                "count": duplicate_rows,
                "details": f"发现 {duplicate_rows} 行完全重复记录",
            }
        )

    non_negative_columns = [
        "instructions",
        "cycles",
        "accesses",
        "misses",
        "hits",
        "ipc",
        "mpki",
        "execution_time_ms",
    ]
    for column in non_negative_columns:
        if column in dataframe.columns:
            invalid_count = int((dataframe[column] < 0).fillna(False).sum())
            if invalid_count:
                issues.append(
                    {
                        "severity": "error",
                        "check": "numeric_range",
                        "count": invalid_count,
                        "details": f"列 {column} 不能为负数",
                    }
                )

    if "cache_size_kb" in dataframe.columns:
        invalid_count = int((dataframe["cache_size_kb"] <= 0).fillna(False).sum())
        if invalid_count:
            issues.append(
                {
                    "severity": "error",
                    "check": "numeric_range",
                    "count": invalid_count,
                    "details": "cache_size_kb 必须大于 0",
                }
            )

    for column in ["miss_rate", "hit_rate"]:
        if column in dataframe.columns:
            invalid_count = int(
                ((dataframe[column] < 0) | (dataframe[column] > 1))
                .fillna(False)
                .sum()
            )
            if invalid_count:
                issues.append(
                    {
                        "severity": "error",
                        "check": "rate_range",
                        "count": invalid_count,
                        "details": f"列 {column} 必须位于 0 到 1 之间",
                    }
                )

    required_for_consistency = {"accesses", "misses", "hits"}
    if required_for_consistency.issubset(dataframe.columns):
        valid_rows = dataframe[list(required_for_consistency)].notna().all(axis=1)
        mismatch = (
            (dataframe["misses"] + dataframe["hits"] - dataframe["accesses"]).abs()
            > 1e-9
        ) & valid_rows
        mismatch_count = int(mismatch.sum())
        if mismatch_count:
            issues.append(
                {
                    "severity": "error",
                    "check": "counter_consistency",
                    "count": mismatch_count,
                    "details": "misses + hits 必须等于 accesses",
                }
            )

    required_for_rates = {"miss_rate", "hit_rate"}
    if required_for_rates.issubset(dataframe.columns):
        valid_rows = dataframe[list(required_for_rates)].notna().all(axis=1)
        mismatch = (
            (dataframe["miss_rate"] + dataframe["hit_rate"] - 1).abs() > 1e-6
        ) & valid_rows
        mismatch_count = int(mismatch.sum())
        if mismatch_count:
            issues.append(
                {
                    "severity": "warning",
                    "check": "rate_consistency",
                    "count": mismatch_count,
                    "details": "miss_rate + hit_rate 应接近 1",
                }
            )

    return {
        "row_count": int(len(dataframe)),
        "column_count": int(len(dataframe.columns)),
        "missing_cell_count": int(dataframe.isna().sum().sum()),
        "duplicate_row_count": duplicate_rows,
        "issues": issues,
        "error_count": sum(issue["severity"] == "error" for issue in issues),
        "warning_count": sum(issue["severity"] == "warning" for issue in issues),
    }
