# Phase 1 参考项目阅读笔记

## 1. 参考项目

- 项目：Streamlit 官方 `example-app-ab-testing`
- GitHub：https://github.com/streamlit/example-app-ab-testing
- 本地目录：`reference/streamlit-example-ab-testing/`
- 入口文件：`streamlit_app.py`
- 运行命令：`python -m streamlit run streamlit_app.py`
- 本地验证：Streamlit 启动成功，`http://localhost:8503` 返回 HTTP 200

这个项目与本项目的主题比较接近：它接收实验结果 CSV，比较 A/B 两组，并计算转化率、提升率和显著性。

## 2. 依赖情况

参考项目的 `requirements.txt` 使用了较旧的固定版本：

- streamlit 1.16.0
- numpy 1.19.5
- pandas 1.2.5
- scipy 1.6.2
- altair 4.1.0

在 Python 3.12 下直接安装失败，主要原因是旧版 NumPy 没有适合当前环境的构建包。原始 `requirements.txt` 没有修改；为了运行参考项目，在独立 `.venv` 中安装了兼容的新版本。

这说明参考仓库的代码和依赖版本需要分开看：代码可以学习，但不能假定教程项目的依赖仍适用于当前 Python 版本。

## 3. 数据来源和结构

项目支持两种数据来源：

1. 用户通过 `st.file_uploader` 上传 CSV；
2. 默认使用仓库中的 `Website_Results.csv`。

示例数据统计：

- 行数：1451
- 列：`variant`、`converted`、`length_of_stay`、`revenue`
- 实验组：A、B
- A 组样本数：721，转化数：20
- B 组样本数：730，转化数：37

项目假定 A/B 列有两个组，并且结果列可以直接求和。这是一个适合示例的简化假设，不能直接当作本项目实验数据的通用校验规则。

## 4. 页面区域

### 区域一：数据输入和预览

- 上传 CSV 文件；
- 选择是否使用示例文件；
- 使用 `pd.read_csv` 读取数据；
- 使用 `st.dataframe(df.head())` 展示前几行。

### 区域二：分析参数表单

- 选择 A/B 分组列；
- 选择 B 组方向；
- 选择结果列；
- 选择单侧或双侧假设检验；
- 调整显著性水平 alpha；
- 点击提交按钮。

### 区域三：结果展示

- Delta：两组转化率差值；
- Significant?：是否显著；
- A/B 转化率柱状图；
- Converted、Total、% Converted 表格；
- p-value、z-score、uplift 指标表。

## 5. 一次筛选/选择操作的代码路径

以选择 A/B 列和结果列为例：

```text
用户选择 A/B column
  ↓
读取该列的两个 unique 值
  ↓
确定 control 和 treatment
  ↓
统计两组 visitors
  ↓
用户选择 Result column
  ↓
按 A/B 列 groupby，并对结果列求和
  ↓
得到 conversions_a 和 conversions_b
  ↓
calculate_significance()
  ↓
写入 st.session_state
  ↓
显示指标、表格和 Altair 图表
```

对应代码位置大致为：

- 数据读取：`streamlit_app.py:273–291`
- 表单和选择器：`streamlit_app.py:297–351`
- 分组统计：`streamlit_app.py:387–395`
- 指标计算：`streamlit_app.py:221–260`
- 图表函数：`streamlit_app.py:151–179`
- 结果展示：`streamlit_app.py:375–431`

## 6. 指标和图表实现

纯计算函数包括：

- `conversion_rate`：转化数 / 访问数；
- `lift`：B 组相对 A 组的提升率；
- `std_err`：转化率标准误；
- `z_score`：两组差异的标准化统计量；
- `p_value`：根据单侧或双侧假设计算 p 值；
- `significance`：比较 p 值和 alpha。

`plot_chart(df)` 接收一个包含 `Group` 和 `Conversion` 列的 DataFrame，返回交互式 Altair 柱状图。图表函数与页面调用分开，这一点可以借鉴到本项目的 `charts.py`。

## 7. 缓存和状态

本项目没有检测到 `st.cache_data` 或 `st.cache_resource`。它使用 `st.session_state` 保存中间统计结果，例如 conversion rate、uplift、z-score 和 p-value。

对本项目而言：文件读取和清洗结果适合考虑 `st.cache_data`；筛选条件和当前页面交互状态则应单独管理，不能混为一谈。

## 8. 可以借鉴的部分

- 使用 `st.file_uploader` 导入实验 CSV；
- 先用 `st.dataframe` 预览数据；
- 使用 `st.form` 将多个筛选条件一次提交；
- 使用 `st.columns` 和 `st.metric` 展示关键指标；
- 将图表封装成接收 DataFrame 的函数；
- 对统计结果同时展示数值表和图表；
- 用清晰的指标命名解释分析结果。

## 9. 暂时不直接复制的部分

- 整个应用把页面、计算和数据读取都写在一个文件中；
- 没有通用的必需列检查、类型检查和范围校验；
- 默认只处理两个实验组；
- 默认结果列可以直接求和，不适合直接套用到 IPC、MPKI 等指标；
- 依赖版本过旧；
- 页面加载了远程图片，增加了运行时网络依赖；
- 没有针对指标函数的自动测试。

## 10. 对本项目的启发

下一阶段可以借鉴它的最小数据应用流程：

```text
上传文件
  → 预览 DataFrame
  → 选择分析维度
  → 计算派生指标
  → 展示 KPI、表格和图表
```

但本项目需要额外加入 workload、policy、cache size、单位和 baseline 匹配规则，并把数据读取、清洗、指标计算和图表逐步拆到独立模块中。

## 11. 当前限制和结论

参考项目已经成功启动并通过 HTTP 访问验证。Streamlit 的自动化脚本测试因页面加载远程图片在默认 3 秒内超时，因此没有把该测试当作项目失败；入口文件语法检查通过，实际 Streamlit 服务返回 200。

Phase 1 的学习目标已满足：已运行参考项目、阅读 README 和入口文件、识别数据来源、页面区域、指标函数、图表函数及一次选择操作的代码路径。
