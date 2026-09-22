# Phase 2–5 实现记录

## 1. 记录范围

本文整理本项目从 Phase 2 到 Phase 5 的实现过程、数据约定、页面功能、分析逻辑、验证结果和当前使用方式，作为 `phase1_reading_notes.md` 之后的开发记录。

## 2. 阶段进度

| 阶段 | 主要内容 | 状态 |
|---|---|---|
| Phase 2 | CSV/XLSX 读取、列名标准化、类型转换和数据质量检查 | 已完成 |
| Phase 3 | workload、policy、cache size 筛选，KPI 卡片和基础图表 | 已完成 |
| Phase 4 | baseline 匹配、方向性改进率、多次 run 汇总 | 已完成 |
| Phase 5 | 测试、日志、SQLite 分析快照、CSV 导出和界面说明 | 已完成 |

## 3. 数据读取和质量检查

核心实现位于 `src/data_loader.py`，页面入口位于 `app.py`。

数据加载流程如下：

```text
上传 CSV/XLSX
  → 读取第一个工作表或 CSV
  → 标准化列名和已知别名
  → 转换文本列与数值列类型
  → 检查必需列、缺失值、重复行和数值范围
  → 检查 misses + hits = accesses
  → 检查 miss_rate + hit_rate ≈ 1
  → 通过后进入筛选和分析
```

支持的输入类型：

- `.csv`：建议使用 UTF-8 编码，第一行必须是表头；
- `.xlsx`：默认读取第一个工作表；
- 未上传文件时，自动使用 `data/sample_experiment.csv`。

如果数据存在错误，页面会暂停筛选和图表分析，并显示具体质量问题；警告不会阻止分析，但会提示使用者确认。

## 4. 数据格式和模板

项目使用长表格式，每一行代表一个实验条件的一次 run。标准字段为：

```text
experiment_id, workload, policy, cache_size_kb, run_id,
instructions, cycles, accesses, misses, hits,
ipc, mpki, miss_rate, hit_rate, execution_time_ms
```

字段要求：

- `experiment_id`、`workload`、`policy`、`run_id` 为文本；
- `cache_size_kb` 使用 KB 且必须大于 0；
- `instructions`、`cycles`、`accesses`、`misses`、`hits` 为非负数；
- `ipc`、`mpki` 和 `execution_time_ms` 为非负数；
- `miss_rate` 和 `hit_rate` 使用 0–1，例如 20% 应填写为 `0.20`；
- `misses + hits` 必须等于 `accesses`；
- `miss_rate + hit_rate` 应约等于 `1`；
- 不要把 `32 KB`、`1,000,000` 等带单位或千位分隔符的文本直接填入数值字段。

模板文件为 [data/experiment_data_template.csv](data/experiment_data_template.csv)，其中包含 2 次 baseline run 和 2 次 `lru` run，可用于验证多次运行汇总和 baseline 对比。页面上传区域也提供了模板下载按钮。

## 5. Phase 3 页面功能

用户可以在侧边栏选择：

- 一个或多个 workload；
- 一个或多个 policy；
- 一个或多个 cache size；
- 用于比较的 baseline policy。

筛选结果会驱动后续所有分析。页面提供四个基础 KPI：

- 平均 IPC；
- 平均 MPKI；
- 平均 Miss Rate；
- 平均执行时间。

基础图表包括：

1. 按策略和工作负载比较平均执行时间的柱状图；
2. 按工作负载和策略比较平均 IPC 的柱状图；
3. 按缓存大小和策略展示平均 MPKI 趋势的折线图。

页面在 KPI 和图表附近增加了说明文字，帮助使用者理解当前筛选范围、均值含义和指标优劣方向。

## 6. Phase 4 指标分析

### 6.1 多次 run 汇总

`src/metrics.py` 使用以下字段作为一个实验条件的分组键：

```text
experiment_id, workload, policy, cache_size_kb
```

每组结果会计算：

- run 数量；
- IPC、MPKI、Miss Rate、Hit Rate 和执行时间的均值；
- 上述指标的标准差；
- 每个指标的有效样本数。

均值用于表示典型表现，标准差用于观察重复运行的波动，样本数用于确认统计结果是否有足够的有效数据。

### 6.2 Baseline 匹配

baseline 使用以下字段进行匹配：

```text
experiment_id, workload, cache_size_kb
```

默认策略名称是 `baseline`，也可以在页面中选择其他策略作为基准。只有在相同实验、工作负载和缓存大小下找到 baseline 时，才会计算改进率；找不到匹配项时，页面显示提示，改进率留空。

### 6.3 改进率方向

- IPC、Hit Rate：数值越高越好；
- MPKI、Miss Rate、Execution Time：数值越低越好。

因此改进率不是所有指标都使用同一个减法方向，而是根据指标的优劣方向计算。结果表会同时展示当前均值、baseline 均值、样本数、是否匹配以及改进率。

## 7. Phase 5 工程化功能

当前代码按职责拆分为：

- `src/data_loader.py`：读取、标准化、类型转换和质量检查；
- `src/metrics.py`：run 汇总、baseline 匹配和改进率；
- `src/export.py`：生成 UTF-8 BOM CSV 下载内容；
- `src/logging_config.py`：配置轮转日志；
- `src/storage.py`：保存和读取 SQLite 分析快照。

页面支持下载：

- 当前筛选数据；
- 多次 run 汇总；
- baseline 对比结果；
- 示例数据模板。

保存分析时会记录数据源、语言、baseline 策略、筛选条件、筛选行数和主要 KPI。SQLite 数据库和日志文件不会提交到 Git。

## 8. 双语界面和使用说明

页面侧边栏提供中文和 English 两种语言。以下内容已做双语覆盖：

- 上传提示、文件格式要求和示例表头；
- 筛选条件和 baseline 选择说明；
- KPI、图表、run 汇总和 baseline 对比解释；
- 数据质量问题、导出结果和保存记录。

上传区域的问号帮助中包含完整 15 列示例表头；上传框下方提供简短的格式要求和模板下载按钮。

## 9. 验证结果

当前验证命令：

```powershell
.\.venv\Scripts\python.exe -m py_compile app.py
.\.venv\Scripts\python.exe -m pytest -q
```

最近一次测试结果：

```text
10 passed
```

模板数据通过项目质量检查：

```text
shape: (4, 15)
error_count: 0
warning_count: 0
```

## 10. Git 保存记录

本阶段主要功能曾提交到本地 Git：

```text
b337520 feat: complete experiment analytics dashboard
```

推送 GitHub 时曾因本机未配置 GitHub SSH 公钥而失败，错误为 `Permission denied (publickey)`。在 GitHub SSH 认证配置完成后，可在 Git Bash 中使用：

```bash
cd /c/Users/18870/Desktop/experiment-analytics-dashboard
git push origin main
```

## 11. 后续可选工作

- 使用真实实验数据验证字段和指标定义；
- 增加热力图、退化案例列表和更多筛选维度；
- 增加端到端页面测试；
- 配置 GitHub Actions 自动运行测试；
- 根据真实数据规模评估缓存和更大数据文件的读取性能。
