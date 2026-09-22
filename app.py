from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data_loader import inspect_data_quality, load_experiment_data
from src.export import dataframe_to_csv_bytes
from src.logging_config import configure_logging
from src.metrics import (
    GROUP_COLUMNS,
    METRIC_COLUMNS,
    build_baseline_comparison,
    comparison_to_long,
    summarize_runs,
)
from src.storage import (
    DEFAULT_DB_PATH,
    fetch_recent_analysis_runs,
    save_analysis_run,
)


LOGGER = configure_logging()
LOGGER.info("Dashboard application initialized")


TRANSLATIONS = {
    "zh": {
        "app_name": "实验分析仪表盘",
        "page_title": "实验数据筛选与核心指标分析",
        "upload": "上传实验结果文件",
        "upload_help": (
            "支持 CSV 和 XLSX。第一行必须是表头，每行代表一次 run。\n\n"
            "示例表头：`experiment_id, workload, policy, cache_size_kb, run_id, "
            "instructions, cycles, accesses, misses, hits, ipc, mpki, miss_rate, "
            "hit_rate, execution_time_ms`\n\n"
            "比例字段使用 0–1，例如 0.20；misses + hits 必须等于 accesses。"
        ),
        "upload_requirements": (
            "格式要求：CSV（UTF-8）或 XLSX；首行为表头，每行一条 run；"
            "必需 15 列，比例字段使用 0–1，计数和执行时间填写数值。"
        ),
        "download_template": "下载示例数据模板",
        "download_template_help": "下载后可直接复制并替换为自己的实验结果。",
        "source": "当前数据源",
        "records": "记录数",
        "fields": "字段数",
        "missing_cells": "缺失单元格",
        "duplicate_rows": "重复行",
        "quality_pass": "数据质量检查通过，未发现缺失、重复或范围异常。",
        "quality_errors": "发现 {count} 项错误，请修正后再进行分析。",
        "quality_warnings": "发现 {count} 项警告，请确认是否符合预期。",
        "quality_issues": "数据质量问题",
        "load_failed": "数据读取失败：{error}",
        "analysis_stopped": "当前数据存在错误，已暂停筛选和图表分析。请先修正数据后重新上传。",
        "filters": "筛选条件",
        "filters_help": "先缩小工作负载、策略和缓存大小范围，下面的指标与图表都会基于筛选结果重新计算。",
        "exports": "导出结果",
        "download_filtered": "下载筛选数据 CSV",
        "download_summary": "下载 run 汇总 CSV",
        "download_baseline": "下载 Baseline 对比 CSV",
        "storage": "保存分析记录",
        "save_analysis": "保存当前分析",
        "save_success": "分析记录已保存，编号：{run_id}",
        "save_failed": "分析记录保存失败：{error}",
        "recent_runs": "最近保存的分析记录",
        "no_saved_runs": "还没有保存过分析记录。",
        "storage_failed": "读取历史分析记录失败：{error}",
        "saved_id": "编号",
        "saved_at": "保存时间",
        "saved_source": "数据源",
        "saved_rows": "筛选记录数",
        "baseline_policy": "基准策略",
        "baseline_help": "基准策略将按相同实验、工作负载和缓存大小匹配。",
        "run_summary": "多次运行汇总",
        "baseline_comparison": "Baseline 对比",
        "baseline_missing": "当前筛选结果中没有可匹配的 baseline。",
        "baseline_matched": "Baseline 已匹配",
        "baseline_runs": "Baseline 样本数",
        "mean": "均值",
        "std": "标准差",
        "sample_count": "样本数",
        "metric": "指标",
        "current_mean": "当前均值",
        "baseline_mean": "Baseline 均值",
        "improvement_pct": "改进率 (%)",
        "yes": "是",
        "no": "否",
        "workload": "工作负载",
        "policy": "策略",
        "cache_size": "缓存大小（KB）",
        "selected_results": "筛选结果",
        "selected_caption": "已筛选 {selected} / {total} 条记录。",
        "kpi_help": "KPI 使用当前筛选结果的整体均值；Miss Rate 越低通常越好，IPC 越高通常越好。",
        "no_matches": "当前筛选条件没有匹配记录，请至少选择一个工作负载、策略和缓存大小。",
        "avg_ipc": "平均 IPC",
        "avg_mpki": "平均 MPKI",
        "avg_miss_rate": "平均 Miss Rate",
        "avg_execution_time": "平均执行时间",
        "charts": "基础图表",
        "charts_help": "图表展示筛选结果的均值，用于快速比较策略、工作负载和缓存大小之间的趋势。",
        "execution_title": "按策略和工作负载统计的平均执行时间",
        "execution_time": "平均执行时间 (ms)",
        "ipc_title": "不同工作负载与策略的平均 IPC",
        "ipc": "平均 IPC",
        "mpki_title": "缓存大小与策略的平均 MPKI",
        "mpki": "平均 MPKI",
        "cache_size_axis": "缓存大小（KB）",
        "filtered_preview": "筛选后数据预览",
        "run_summary_help": "同一实验、工作负载、策略和缓存大小下的多次 run 会汇总为一行；均值反映典型表现，标准差反映波动，样本数表示有效 run 数。",
        "baseline_comparison_help": "改进率以选定的 baseline 为参照：IPC 和 Hit Rate 越高越好，MPKI、Miss Rate 和执行时间越低越好；没有匹配 baseline 时不会计算改进率。",
        "export_help": "可以下载当前筛选数据、run 汇总或 baseline 对比结果，便于留档和进一步分析。",
        "phase4_info": "Phase 4 已接入：多次运行汇总、Baseline 匹配和方向性改进率。",
        "issue_severity": "级别",
        "issue_check": "检查项",
        "issue_count": "数量",
        "issue_details": "详情",
    },
    "en": {
        "app_name": "Experiment Analytics Dashboard",
        "page_title": "Experiment Data Filters and Core Metrics",
        "upload": "Upload experiment result file",
        "upload_help": (
            "CSV and XLSX are supported. The first row must be the header, and each "
            "row represents one run.\n\n"
            "Example header: `experiment_id, workload, policy, cache_size_kb, run_id, "
            "instructions, cycles, accesses, misses, hits, ipc, mpki, miss_rate, "
            "hit_rate, execution_time_ms`\n\n"
            "Use 0–1 for rate fields, for example 0.20; misses + hits must equal accesses."
        ),
        "upload_requirements": (
            "Format requirements: CSV (UTF-8) or XLSX; the first row is the header "
            "and each row is one run; 15 required columns, numeric counters and "
            "execution time, with rate fields in the 0–1 range."
        ),
        "download_template": "Download example data template",
        "download_template_help": "Download it, then copy and replace the example values with your own results.",
        "source": "Current data source",
        "records": "Records",
        "fields": "Fields",
        "missing_cells": "Missing cells",
        "duplicate_rows": "Duplicate rows",
        "quality_pass": "Data quality check passed. No missing values, duplicates, or range issues were found.",
        "quality_errors": "Found {count} error(s). Fix them before analysis.",
        "quality_warnings": "Found {count} warning(s). Confirm that they are expected.",
        "quality_issues": "Data quality issues",
        "load_failed": "Data loading failed: {error}",
        "analysis_stopped": "Analysis is paused because the data contains errors. Fix the data and upload it again.",
        "filters": "Filters",
        "filters_help": "Narrow the workload, policy, and cache-size scope first. All metrics and charts below are recalculated from the filtered rows.",
        "exports": "Export results",
        "download_filtered": "Download filtered data CSV",
        "download_summary": "Download run summary CSV",
        "download_baseline": "Download baseline comparison CSV",
        "storage": "Save analysis",
        "save_analysis": "Save current analysis",
        "save_success": "Analysis saved with id {run_id}.",
        "save_failed": "Could not save the analysis: {error}",
        "recent_runs": "Recently saved analyses",
        "no_saved_runs": "No analyses have been saved yet.",
        "storage_failed": "Could not load saved analyses: {error}",
        "saved_id": "ID",
        "saved_at": "Saved at",
        "saved_source": "Data source",
        "saved_rows": "Filtered rows",
        "baseline_policy": "Baseline policy",
        "baseline_help": "The baseline is matched by experiment, workload, and cache size.",
        "run_summary": "Multi-run summary",
        "baseline_comparison": "Baseline comparison",
        "baseline_missing": "No matching baseline was found in the filtered results.",
        "baseline_matched": "Baseline matched",
        "baseline_runs": "Baseline samples",
        "mean": "Mean",
        "std": "Std. dev.",
        "sample_count": "Samples",
        "metric": "Metric",
        "current_mean": "Current mean",
        "baseline_mean": "Baseline mean",
        "improvement_pct": "Improvement (%)",
        "yes": "Yes",
        "no": "No",
        "workload": "Workload",
        "policy": "Policy",
        "cache_size": "Cache size (KB)",
        "selected_results": "Filtered results",
        "selected_caption": "Showing {selected} of {total} records.",
        "kpi_help": "KPIs are overall means for the current selection. Lower Miss Rate is usually better, while higher IPC is usually better.",
        "no_matches": "No records match the current filters. Select at least one workload, policy, and cache size.",
        "avg_ipc": "Average IPC",
        "avg_mpki": "Average MPKI",
        "avg_miss_rate": "Average Miss Rate",
        "avg_execution_time": "Average execution time",
        "charts": "Basic charts",
        "charts_help": "Charts show means for the filtered results to make differences and trends across policies, workloads, and cache sizes easier to compare.",
        "execution_title": "Average execution time by policy and workload",
        "execution_time": "Average execution time (ms)",
        "ipc_title": "Average IPC by workload and policy",
        "ipc": "Average IPC",
        "mpki_title": "Average MPKI by cache size and policy",
        "mpki": "Average MPKI",
        "cache_size_axis": "Cache size (KB)",
        "filtered_preview": "Filtered data preview",
        "run_summary_help": "Runs with the same experiment, workload, policy, and cache size are summarized into one row. Mean shows typical performance, standard deviation shows variation, and sample count shows valid runs.",
        "baseline_comparison_help": "Improvement is calculated against the selected baseline: higher IPC and Hit Rate are better; lower MPKI, Miss Rate, and execution time are better. No matching baseline means no improvement is reported.",
        "export_help": "Download the filtered data, run summary, or baseline comparison for record keeping and further analysis.",
        "phase4_info": "Phase 4: multi-run summaries, baseline matching, and directional improvement rates are enabled.",
        "issue_severity": "Severity",
        "issue_check": "Check",
        "issue_count": "Count",
        "issue_details": "Details",
    },
}


DISPLAY_COLUMNS = {
    "zh": {
        "experiment_id": "实验 ID",
        "workload": "工作负载",
        "policy": "策略",
        "cache_size_kb": "缓存大小（KB）",
        "run_id": "运行 ID",
        "instructions": "指令数",
        "cycles": "周期数",
        "accesses": "访问次数",
        "misses": "未命中次数",
        "hits": "命中次数",
        "ipc": "IPC",
        "mpki": "MPKI",
        "miss_rate": "未命中率",
        "hit_rate": "命中率",
        "execution_time_ms": "执行时间（毫秒）",
    },
    "en": {
        "experiment_id": "Experiment ID",
        "workload": "Workload",
        "policy": "Policy",
        "cache_size_kb": "Cache size (KB)",
        "run_id": "Run ID",
        "instructions": "Instructions",
        "cycles": "Cycles",
        "accesses": "Accesses",
        "misses": "Misses",
        "hits": "Hits",
        "ipc": "IPC",
        "mpki": "MPKI",
        "miss_rate": "Miss rate",
        "hit_rate": "Hit rate",
        "execution_time_ms": "Execution time (ms)",
    },
}


QUALITY_CHECKS = {
    "zh": {
        "required_columns": "必需列",
        "missing_values": "缺失值",
        "duplicate_rows": "重复行",
        "numeric_range": "数值范围",
        "rate_range": "比例范围",
        "counter_consistency": "计数一致性",
        "rate_consistency": "比例一致性",
    },
    "en": {
        "required_columns": "Required columns",
        "missing_values": "Missing values",
        "duplicate_rows": "Duplicate rows",
        "numeric_range": "Numeric range",
        "rate_range": "Rate range",
        "counter_consistency": "Counter consistency",
        "rate_consistency": "Rate consistency",
    },
}

SEVERITIES = {
    "zh": {"error": "错误", "warning": "警告"},
    "en": {"error": "Error", "warning": "Warning"},
}


def quality_issues_for_language(
    issues: list[dict[str, object]], language: str
) -> list[dict[str, object]]:
    """Keep shared checks while translating their display text."""

    english_details = {
        "required_columns": lambda issue: "Required columns are missing.",
        "missing_values": lambda issue: (
            f"Column contains {issue['count']} missing value(s)."
        ),
        "duplicate_rows": lambda issue: (
            f"Found {issue['count']} completely duplicated row(s)."
        ),
        "numeric_range": lambda issue: "A numeric value is outside the allowed range.",
        "rate_range": lambda issue: "Rate must be between 0 and 1.",
        "counter_consistency": lambda issue: "misses + hits must equal accesses.",
        "rate_consistency": lambda issue: "miss_rate + hit_rate should be close to 1.",
    }
    rows = []
    for issue in issues:
        details = (
            issue["details"]
            if language == "zh"
            else english_details.get(
                issue["check"], lambda current: str(current["details"])
            )(issue)
        )
        rows.append(
            {
                TRANSLATIONS[language]["issue_severity"]: SEVERITIES[language][
                    issue["severity"]
                ],
                TRANSLATIONS[language]["issue_check"]: QUALITY_CHECKS[language][
                    issue["check"]
                ],
                TRANSLATIONS[language]["issue_count"]: issue["count"],
                TRANSLATIONS[language]["issue_details"]: details,
            }
        )
    return rows


def localized_dataframe(dataframe, language: str):
    """Translate only display headers, keeping internal column names stable."""

    return dataframe.rename(columns=DISPLAY_COLUMNS[language])


METRIC_LABELS = {
    "zh": {
        "ipc": "IPC",
        "mpki": "MPKI",
        "miss_rate": "未命中率",
        "hit_rate": "命中率",
        "execution_time_ms": "执行时间（毫秒）",
    },
    "en": {
        "ipc": "IPC",
        "mpki": "MPKI",
        "miss_rate": "Miss rate",
        "hit_rate": "Hit rate",
        "execution_time_ms": "Execution time (ms)",
    },
}


def localized_run_summary(summary: pd.DataFrame, language: str) -> pd.DataFrame:
    """Prepare the multi-run summary with readable bilingual headers."""

    columns = GROUP_COLUMNS + ["run_count"]
    rename = {column: DISPLAY_COLUMNS[language][column] for column in GROUP_COLUMNS}
    rename["run_count"] = TRANSLATIONS[language]["sample_count"]
    for metric in METRIC_COLUMNS:
        for suffix, label in (
            ("mean", TRANSLATIONS[language]["mean"]),
            ("std", TRANSLATIONS[language]["std"]),
        ):
            column = f"{metric}_{suffix}"
            columns.append(column)
            rename[column] = f"{METRIC_LABELS[language][metric]} {label}"
    return summary[columns].rename(columns=rename)


def localized_comparison_table(
    comparison: pd.DataFrame, language: str
) -> pd.DataFrame:
    """Prepare the baseline comparison table with translated headers and values."""

    columns = [
        "experiment_id",
        "workload",
        "cache_size_kb",
        "policy",
        "metric",
        "run_count",
        "baseline_policy",
        "baseline_run_count",
        "baseline_matched",
        "current_mean",
        "baseline_mean",
        "improvement_pct",
    ]
    rename = {
        "experiment_id": DISPLAY_COLUMNS[language]["experiment_id"],
        "workload": DISPLAY_COLUMNS[language]["workload"],
        "cache_size_kb": DISPLAY_COLUMNS[language]["cache_size_kb"],
        "policy": DISPLAY_COLUMNS[language]["policy"],
        "metric": TRANSLATIONS[language]["metric"],
        "run_count": TRANSLATIONS[language]["sample_count"],
        "baseline_policy": TRANSLATIONS[language]["baseline_policy"],
        "baseline_run_count": TRANSLATIONS[language]["baseline_runs"],
        "baseline_matched": TRANSLATIONS[language]["baseline_matched"],
        "current_mean": TRANSLATIONS[language]["current_mean"],
        "baseline_mean": TRANSLATIONS[language]["baseline_mean"],
        "improvement_pct": TRANSLATIONS[language]["improvement_pct"],
    }
    result = comparison[columns].rename(columns=rename).copy()
    metric_column = TRANSLATIONS[language]["metric"]
    result[metric_column] = result[metric_column].map(
        METRIC_LABELS[language]
    )
    matched_column = TRANSLATIONS[language]["baseline_matched"]
    result[matched_column] = result[matched_column].map(
        {True: TRANSLATIONS[language]["yes"], False: TRANSLATIONS[language]["no"]}
    )
    return result


def localized_recent_runs(
    recent_runs: pd.DataFrame, language: str
) -> pd.DataFrame:
    """Prepare saved analysis records for a compact bilingual history table."""

    columns = [
        "id",
        "created_at",
        "source_name",
        "baseline_policy",
        "filtered_row_count",
        "average_ipc",
        "average_mpki",
        "average_miss_rate",
        "average_execution_time_ms",
    ]
    rename = {
        "id": TRANSLATIONS[language]["saved_id"],
        "created_at": TRANSLATIONS[language]["saved_at"],
        "source_name": TRANSLATIONS[language]["saved_source"],
        "baseline_policy": TRANSLATIONS[language]["baseline_policy"],
        "filtered_row_count": TRANSLATIONS[language]["saved_rows"],
        "average_ipc": TRANSLATIONS[language]["avg_ipc"],
        "average_mpki": TRANSLATIONS[language]["avg_mpki"],
        "average_miss_rate": TRANSLATIONS[language]["avg_miss_rate"],
        "average_execution_time_ms": TRANSLATIONS[language]["avg_execution_time"],
    }
    return recent_runs[columns].rename(columns=rename)


st.set_page_config(
    page_title="Experiment Analytics Dashboard / 实验分析仪表盘",
    page_icon="📊",
    layout="wide",
)

selected_language = st.sidebar.selectbox(
    "语言 / Language",
    options=["中文", "English"],
    index=0,
)
language = "en" if selected_language == "English" else "zh"
text = TRANSLATIONS[language]

st.title(text["app_name"])
st.write(text["page_title"])

sample_path = Path(__file__).parent / "data" / "sample_experiment.csv"
template_path = Path(__file__).parent / "data" / "experiment_data_template.csv"
uploaded_file = st.file_uploader(
    text["upload"],
    type=["csv", "xlsx"],
    help=text["upload_help"],
)
upload_info_columns = st.columns([1, 3])
upload_info_columns[0].download_button(
    text["download_template"],
    data=template_path.read_bytes(),
    file_name="experiment_data_template.csv",
    mime="text/csv",
    help=text["download_template_help"],
)
upload_info_columns[1].caption(text["upload_requirements"])

source = uploaded_file if uploaded_file is not None else sample_path
source_label = (
    uploaded_file.name
    if uploaded_file is not None
    else "data/sample_experiment.csv"
)

try:
    dataframe = load_experiment_data(source)
    quality = inspect_data_quality(dataframe)
except Exception as error:
    LOGGER.exception("Data loading failed for %s", source_label)
    st.error(text["load_failed"].format(error=error))
    st.stop()

source_separator = "：" if language == "zh" else ": "
st.caption(f"{text['source']}{source_separator}{source_label}")

metric_columns = st.columns(4)
metric_columns[0].metric(text["records"], quality["row_count"])
metric_columns[1].metric(text["fields"], quality["column_count"])
metric_columns[2].metric(text["missing_cells"], quality["missing_cell_count"])
metric_columns[3].metric(text["duplicate_rows"], quality["duplicate_row_count"])

if quality["error_count"] == 0 and quality["warning_count"] == 0:
    st.success(text["quality_pass"])
else:
    if quality["error_count"]:
        st.error(text["quality_errors"].format(count=quality["error_count"]))
    if quality["warning_count"]:
        st.warning(text["quality_warnings"].format(count=quality["warning_count"]))

if quality["issues"]:
    st.subheader(text["quality_issues"])
    st.dataframe(
        quality_issues_for_language(quality["issues"], language),
        use_container_width=True,
        hide_index=True,
    )

if quality["error_count"]:
    st.warning(text["analysis_stopped"])
    st.subheader(text["filtered_preview"])
    st.dataframe(
        localized_dataframe(dataframe, language),
        use_container_width=True,
        hide_index=True,
    )
    st.stop()

st.sidebar.header(text["filters"])
st.sidebar.caption(text["filters_help"])
workload_options = sorted(dataframe["workload"].dropna().unique().tolist())
policy_options = sorted(dataframe["policy"].dropna().unique().tolist())
cache_size_options = sorted(
    int(value) for value in dataframe["cache_size_kb"].dropna().unique()
)

selected_workloads = st.sidebar.multiselect(
    text["workload"],
    options=workload_options,
    default=workload_options,
)
selected_policies = st.sidebar.multiselect(
    text["policy"],
    options=policy_options,
    default=policy_options,
)
selected_cache_sizes = st.sidebar.multiselect(
    text["cache_size"],
    options=cache_size_options,
    default=cache_size_options,
)
baseline_default_index = (
    policy_options.index("baseline") if "baseline" in policy_options else 0
)
baseline_policy = st.sidebar.selectbox(
    text["baseline_policy"],
    options=policy_options,
    index=baseline_default_index,
    help=text["baseline_help"],
)

filtered_dataframe = dataframe[
    dataframe["workload"].isin(selected_workloads)
    & dataframe["policy"].isin(selected_policies)
    & dataframe["cache_size_kb"].isin(selected_cache_sizes)
].copy()

st.subheader(text["selected_results"])
st.caption(
    text["selected_caption"].format(
        selected=len(filtered_dataframe), total=len(dataframe)
    )
)

if filtered_dataframe.empty:
    st.warning(text["no_matches"])
    st.stop()

average_ipc = filtered_dataframe["ipc"].mean()
average_mpki = filtered_dataframe["mpki"].mean()
average_miss_rate = filtered_dataframe["miss_rate"].mean()
average_execution_time = filtered_dataframe["execution_time_ms"].mean()

st.caption(text["kpi_help"])
kpi_columns = st.columns(4)
kpi_columns[0].metric(text["avg_ipc"], f"{average_ipc:.2f}")
kpi_columns[1].metric(text["avg_mpki"], f"{average_mpki:.2f}")
kpi_columns[2].metric(text["avg_miss_rate"], f"{average_miss_rate:.2%}")
kpi_columns[3].metric(text["avg_execution_time"], f"{average_execution_time:.2f} ms")

st.subheader(text["charts"])
st.caption(text["charts_help"])

execution_summary = (
    filtered_dataframe.groupby(["policy", "workload"], as_index=False)[
        "execution_time_ms"
    ]
    .mean()
)
execution_figure = px.bar(
    execution_summary,
    x="policy",
    y="execution_time_ms",
    color="workload",
    barmode="group",
    text_auto=".2f",
    labels={
        "policy": text["policy"],
        "workload": text["workload"],
        "execution_time_ms": text["execution_time"],
    },
    title=text["execution_title"],
)
execution_figure.update_layout(legend_title_text=text["workload"])
st.plotly_chart(execution_figure, use_container_width=True)

ipc_summary = filtered_dataframe.groupby(
    ["workload", "policy"], as_index=False
)["ipc"].mean()
ipc_figure = px.bar(
    ipc_summary,
    x="workload",
    y="ipc",
    color="policy",
    barmode="group",
    text_auto=".2f",
    labels={
        "workload": text["workload"],
        "policy": text["policy"],
        "ipc": text["ipc"],
    },
    title=text["ipc_title"],
)
ipc_figure.update_layout(legend_title_text=text["policy"])
st.plotly_chart(ipc_figure, use_container_width=True)

mpki_summary = (
    filtered_dataframe.groupby(["cache_size_kb", "policy"], as_index=False)["mpki"]
    .mean()
    .sort_values("cache_size_kb")
)
mpki_figure = px.line(
    mpki_summary,
    x="cache_size_kb",
    y="mpki",
    color="policy",
    markers=True,
    labels={
        "cache_size_kb": text["cache_size_axis"],
        "policy": text["policy"],
        "mpki": text["mpki"],
    },
    title=text["mpki_title"],
)
mpki_figure.update_layout(legend_title_text=text["policy"])
st.plotly_chart(mpki_figure, use_container_width=True)

run_summary = summarize_runs(filtered_dataframe)
st.subheader(text["run_summary"])
st.caption(text["run_summary_help"])
st.dataframe(
    localized_run_summary(run_summary, language),
    use_container_width=True,
    hide_index=True,
)

baseline_comparison = build_baseline_comparison(
    filtered_dataframe,
    baseline_policy=baseline_policy,
)
comparison_table = comparison_to_long(baseline_comparison)
st.subheader(text["baseline_comparison"])
st.caption(text["baseline_comparison_help"])
if not baseline_comparison["baseline_matched"].any():
    st.warning(text["baseline_missing"])
st.dataframe(
    localized_comparison_table(comparison_table, language),
    use_container_width=True,
    hide_index=True,
)

st.subheader(text["exports"])
st.caption(text["export_help"])
download_columns = st.columns(3)
download_columns[0].download_button(
    text["download_filtered"],
    data=dataframe_to_csv_bytes(filtered_dataframe),
    file_name="filtered_experiment_data.csv",
    mime="text/csv",
)
download_columns[1].download_button(
    text["download_summary"],
    data=dataframe_to_csv_bytes(localized_run_summary(run_summary, language)),
    file_name="run_summary.csv",
    mime="text/csv",
)
download_columns[2].download_button(
    text["download_baseline"],
    data=dataframe_to_csv_bytes(
        localized_comparison_table(comparison_table, language)
    ),
    file_name="baseline_comparison.csv",
    mime="text/csv",
)

st.subheader(text["storage"])
if st.button(text["save_analysis"]):
    try:
        saved_id = save_analysis_run(
            DEFAULT_DB_PATH,
            source_name=source_label,
            language=language,
            baseline_policy=baseline_policy,
            selected_workloads=selected_workloads,
            selected_policies=selected_policies,
            selected_cache_sizes=selected_cache_sizes,
            filtered_row_count=len(filtered_dataframe),
            average_ipc=average_ipc,
            average_mpki=average_mpki,
            average_miss_rate=average_miss_rate,
            average_execution_time_ms=average_execution_time,
        )
        LOGGER.info("Saved analysis snapshot id=%s source=%s", saved_id, source_label)
        st.success(text["save_success"].format(run_id=saved_id))
    except Exception as error:
        LOGGER.exception("Could not save analysis snapshot")
        st.error(text["save_failed"].format(error=error))

if DEFAULT_DB_PATH.exists():
    try:
        recent_runs = fetch_recent_analysis_runs(DEFAULT_DB_PATH)
        if recent_runs.empty:
            st.info(text["no_saved_runs"])
        else:
            st.caption(text["recent_runs"])
            st.dataframe(
                localized_recent_runs(recent_runs, language),
                use_container_width=True,
                hide_index=True,
            )
    except Exception as error:
        LOGGER.exception("Could not load recent analysis snapshots")
        st.error(text["storage_failed"].format(error=error))

st.subheader(text["filtered_preview"])
st.dataframe(
    localized_dataframe(filtered_dataframe, language),
    use_container_width=True,
    hide_index=True,
)

st.info(text["phase4_info"])
