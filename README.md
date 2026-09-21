# Experiment Analytics Dashboard

实验数据可视化与分析平台，目标是将实验结果导入后，按照 workload、policy、cache size 等条件进行筛选、指标计算、baseline 对比和交互式可视化。

## 项目状态

当前已完成 Phase 0 和 Phase 1：

| 阶段 | 状态 | 结果 |
|---|---|---|
| Phase 0：环境与项目初始化 | 已完成 | Python 虚拟环境、依赖、最小 Streamlit 页面和首次 Git 提交 |
| Phase 1：运行并阅读参考项目 | 已完成 | 运行官方 A/B Testing 示例，完成代码路径和数据流阅读笔记 |
| Phase 2：数据读取、检查和清洗 | 下一步 | 建立自己的 CSV/XLSX 读取和数据质量检查层 |

详细阅读记录见：[phase1_reading_notes.md](phase1_reading_notes.md)

## 当前可运行内容

目前应用是 Phase 0 的最小页面，用于验证开发环境和 Streamlit 启动流程。数据上传、清洗、指标计算和图表功能将在后续阶段逐步加入。

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
- Plotly：后续交互式图表；
- openpyxl：后续 Excel 文件读写。

`.venv/`、缓存文件、SQLite 数据库和敏感配置不会提交到 Git。

## 项目结构

```text
experiment-analytics-dashboard/
├── app.py                         # 当前 Streamlit 入口
├── requirements.txt               # 运行依赖
├── README.md                      # 项目说明
├── phase1_reading_notes.md        # Phase 1 参考项目阅读笔记
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

项目后续推荐使用长表格式，每行代表一个实验条件下的一条结果。核心字段计划包括：

```text
experiment_id, workload, policy, cache_size_kb, run_id,
instructions, cycles, accesses, misses, hits,
ipc, mpki, miss_rate, hit_rate, execution_time_ms
```

基本约定：

- `cache_size_kb` 使用 KB；
- `execution_time_ms` 使用毫秒；
- `miss_rate` 和 `hit_rate` 内部使用 0–1；
- `ipc` 越高通常越好；
- `mpki`、`miss_rate` 和执行时间通常越低越好；
- baseline 必须匹配相同 workload、cache size 和实验条件。

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
