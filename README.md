# Experiment Analytics Dashboard

实验数据可视化与分析平台。

## 当前阶段

Phase 0：完成 Python 虚拟环境、基础依赖和最小 Streamlit 页面。

## 环境要求

- Python 3.12+
- Git
- Windows PowerShell

## 安装

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 运行

```powershell
python -m streamlit run app.py
```

浏览器打开 Streamlit 显示的本地地址即可查看页面。

## 当前状态

- [x] 最小 Streamlit 入口
- [x] 基础运行依赖清单
- [x] README 和 Git 忽略规则
- [ ] 数据读取与清洗
- [ ] 交互式图表
- [ ] baseline 对比
