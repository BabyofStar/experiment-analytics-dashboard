# Experiment Analytics Dashboard

实验数据可视化与分析平台，目标是将实验结果导入后，按照 workload、policy、cache size 等条件进行筛选、指标计算、baseline 对比和交互式可视化。

## 项目状态

当前已完成 Phase 0、Phase 1、Phase 2、Phase 3 和 Phase 4：

| 阶段 | 状态 | 结果 |
|---|---|---|
| Phase 0：环境与项目初始化 | 已完成 | Python 虚拟环境、依赖、最小 Streamlit 页面和首次 Git 提交 |
| Phase 1：运行并阅读参考项目 | 已完成 | 运行官方 A/B Testing 示例，完成代码路径和数据流阅读笔记 |
| Phase 2：数据读取、检查和清洗 | 已完成 | 完成 CSV/XLSX 读取、列名标准化、类型转换和数据质量检查 |
| Phase 3：MVP Dashboard | 已完成 | 完成 workload、policy 和 cache size 筛选、KPI 卡片和基础图表 |
| Phase 4：指标与 baseline 对比 | 已完成 | 完成 baseline 匹配、方向性改进率和多次 run 的均值、标准差、样本数汇总 |
| Phase 5：工程化 | 已完成 | 已加入测试、日志、SQLite 分析快照和 CSV 导出 |

详细阅读记录见：[phase1_reading_notes.md](phase1_reading_notes.md)

Phase 2–5 的实现记录见：[phase2_to_phase5_implementation_notes.md](phase2_to_phase5_implementation_notes.md)

## 当前可运行内容

目前应用已经支持上传 CSV/XLSX 文件，或在未上传文件时自动使用 `data/sample_experiment.csv`。页面支持中文和 English 切换，会展示数据质量摘要，并支持按 workload、policy 和 cache size 筛选，计算核心 KPI、显示基础图表、汇总多次 run，并匹配 baseline 计算改进率。上传区域提供 [experiment_data_template.csv](data/experiment_data_template.csv) 下载按钮，方便使用者直接填写自己的数据；页面还支持下载筛选数据、run 汇总和 baseline 对比 CSV，保存当前分析快照到 SQLite，并显示最近保存记录。各分析模块均提供用途和指标方向说明。Streamlit 开发菜单已隐藏，因此 Deploy、Rerun 和 Clear cache 等功能不再显示；Print、Record screen 和主题选项仍属于框架工具栏。

### 分析结果如何理解

- **筛选条件**：选择 workload、policy 和 cache size 后，下面的 KPI、图表、run 汇总和 baseline 对比都会基于当前筛选结果重新计算。
- **KPI 卡片**：展示当前筛选结果的整体均值。通常 IPC 越高越好，MPKI、Miss Rate 和执行时间越低越好。
- **基础图表**：按策略、工作负载和缓存大小展示均值，用于快速观察不同实验条件的差异和趋势。
- **多次运行汇总**：相同实验条件下的多次 run 会合并展示均值、标准差和样本数；标准差越大，说明重复运行结果波动越明显。
- **Baseline 对比**：在相同 `experiment_id`、`workload` 和 `cache_size_kb` 下匹配 `policy=baseline`，再按照指标的优劣方向计算改进率；没有匹配 baseline 时不会计算改进率。

## 环境要求

- Windows
- Python 3.12+
- Git
- PowerShell

## 安装和运行

在项目根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

启动应用：

```powershell
streamlit run app.py
```

如果 PowerShell 中找不到 `streamlit`，使用虚拟环境的 Python 直接启动：

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

浏览器打开终端显示的本地地址，通常是 `http://localhost:8501`。

## 当前依赖

运行依赖记录在 [requirements.txt](requirements.txt) 中：

- Streamlit：Web 应用和交互控件；
- Pandas：CSV/Excel 和表格数据处理；
- NumPy：数值计算；
- Plotly：交互式图表；
- openpyxl：后续 Excel 文件读写。
- pytest：数据读取和指标计算自动化测试。

`.venv/`、缓存文件、SQLite 数据库和敏感配置不会提交到 Git。

## 项目结构

```text
experiment-analytics-dashboard/
├── app.py                         # 当前 Streamlit 入口
├── requirements.txt               # 运行依赖
├── README.md                      # 项目说明
├── phase1_reading_notes.md        # Phase 1 参考项目阅读笔记
├── phase2_to_phase5_implementation_notes.md # Phase 2–5 实现记录
├── data/
│   ├── sample_experiment.csv      # Phase 2 示例实验数据
│   └── experiment_data_template.csv # 可复制填写的数据模板
├── src/
│   ├── __init__.py
│   ├── data_loader.py             # 数据读取、标准化和质量检查
│   ├── metrics.py                 # 多次 run 汇总和 baseline 改进率
│   ├── export.py                  # CSV 导出
│   ├── logging_config.py          # 轮转日志配置
│   └── storage.py                 # SQLite 分析快照存储
├── tests/
│   ├── test_data_loader.py        # 数据读取和质量检查测试
│   ├── test_metrics.py            # 汇总和 baseline 对比测试
│   ├── test_export.py             # CSV 导出测试
│   ├── test_logging.py            # 日志测试
│   └── test_storage.py            # SQLite 存储测试
├── .streamlit/
│   └── config.toml                # 隐藏 Streamlit 开发菜单
├── .gitignore                     # 忽略虚拟环境、缓存和本地数据
├── .venv/                         # 本地虚拟环境，不提交
└── reference/                     # 本地参考项目，不提交
    └── streamlit-example-ab-testing/
        ├── streamlit_app.py       # 参考项目入口
        ├── Website_Results.csv    # 参考项目示例数据
        └── .venv/                 # 参考项目独立虚拟环境
```

## Phase 1 参考项目

参考项目是官方 [Streamlit A/B Testing App](https://github.com/streamlit/example-app-ab-testing)。它支持上传实验结果 CSV，选择 A/B 分组列和结果列，并展示转化率、提升率、p-value、z-score 和柱状图。

本地运行参考项目：

```powershell
cd reference\streamlit-example-ab-testing
.\.venv\Scripts\Activate.ps1
streamlit run streamlit_app.py
```

参考项目的原始依赖较旧，在 Python 3.12 下无法直接安装。因此本地参考环境使用了兼容版本，原始参考代码和 `requirements.txt` 未修改。

## 目标数据格式

应用使用“长表”格式：每一行代表一个实验条件的一次 run。可以直接复制并填写模板：[experiment_data_template.csv](data/experiment_data_template.csv)。已有的完整示例见 [sample_experiment.csv](data/sample_experiment.csv)。

### 文件要求

- 支持 `.csv` 和 `.xlsx`；CSV 建议使用 UTF-8 编码，第一行必须是列名；XLSX 默认读取第一个工作表。
- 不要在数据表中混入合计行、说明文字或单位字符串，例如 `32 KB`、`1,000,000`；数值应填写为 `32`、`1000000`。
- 推荐使用下面的标准列名。读取器会处理常见空格、大小写和部分别名，但标准列名最稳定。

### 必需字段

| 字段 | 类型/单位 | 含义 |
| --- | --- | --- |
| `experiment_id` | 文本 | 实验批次或实验名称 |
| `workload` | 文本 | 工作负载名称，例如 `matrix`、`graph` |
| `policy` | 文本 | 策略名称；基线策略请使用 `baseline` |
| `cache_size_kb` | 数值，KB，> 0 | Cache 大小 |
| `run_id` | 文本 | 重复运行编号，例如 `run_01` |
| `instructions` | 非负数，条数 | 指令数 |
| `cycles` | 非负数，cycle 数 | 周期数 |
| `accesses` | 非负数，次数 | Cache 访问次数 |
| `misses` | 非负数，次数 | Cache miss 次数 |
| `hits` | 非负数，次数 | Cache hit 次数 |
| `ipc` | 非负数 | Instructions per cycle |
| `mpki` | 非负数 | 每千条指令的 miss 数 |
| `miss_rate` | 0–1 | Miss 比率，例如 20% 填 `0.20` |
| `hit_rate` | 0–1 | Hit 比率，例如 80% 填 `0.80` |
| `execution_time_ms` | 非负数，毫秒 | 执行时间 |

### 数据约束和填写规则

- 必须满足 `misses + hits = accesses`，且 `miss_rate + hit_rate` 应约等于 `1`。
- 同一组 `experiment_id`、`workload`、`policy`、`cache_size_kb` 可以有多次 run；每次 run 修改 `run_id`，并填写该次实际测量值。
- baseline 对比会在相同 `experiment_id`、`workload` 和 `cache_size_kb` 下匹配 `policy=baseline`。如果找不到匹配 baseline，页面会提示且改进率留空。
- `ipc` 和 `hit_rate` 通常越高越好；`mpki`、`miss_rate` 和 `execution_time_ms` 通常越低越好。
- `cache_size_kb` 使用 KB，`execution_time_ms` 使用毫秒；不要把单位写进单元格。

模板中包含 2 个 baseline run 和 2 个 `lru` run，可用于验证多次 run 的均值、标准差、样本数和 baseline 改进率。

## 后续路线图

### Phase 2：数据读取、检查和清洗

- 创建示例 CSV；
- 实现 CSV/XLSX 读取；
- 统一列名和数据类型；
- 检查必需列、缺失值、重复行和数值范围；
- 在页面展示数据质量摘要。

### Phase 3：MVP Dashboard

- 文件上传；
- workload、policy 和 cache size 筛选；
- 原始数据预览；
- KPI 卡片；
- 基本柱状图和趋势图；
- 筛选结果 CSV 下载。

### Phase 4：指标与 baseline 对比

- IPC、MPKI、Miss Rate、Hit Rate；
- higher-is-better 和 lower-is-better 改进率；
- baseline 匹配规则；
- 多次 run 的均值、标准差和样本数；
- 热力图和退化案例识别。

### Phase 5 及以后：工程化

- 拆分 `src/` 模块；
- 增加 pytest 测试；
- 增加日志和异常处理；
- 增加 SQLite 存储；
- 增加导出、Docker 和 GitHub Actions；
- 接入论文或真实实验数据。

## Git 工作流

每完成一个可验证的小功能就提交一次，提交信息保持单一主题，例如：

```text
chore: initialize Streamlit project
docs: add Phase 1 reference notes
feat: add CSV loader
feat: validate required columns
feat: add baseline improvement calculation
```

提交前检查：

- 页面能够启动；
- 相关测试通过；
- 没有提交 `.venv`、密钥或大体积原始数据；
- README 与实际运行方式一致；
- commit 能清楚说明这次改动的目的。
