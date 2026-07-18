# AI-quant｜量化交易课程任务站点

<p align="center">
  <a href="#中文说明">中文</a> ·
  <a href="#english-version">English</a> ·
  <a href="https://jiahui-xin.github.io/AI-quant/">在线站点 / Live Site</a>
</p>

---

## 中文说明

本仓库用于管理北大光华商业分析（BA）工作坊的量化交易课程任务。项目围绕创新药代表公司，依次完成行情数据引擎、数据诊断与技术指标、双均线策略和回测、海龟交易法则、AI 交易引擎中的分类型机器学习，以及机器学习选股策略（季度 Top 30），并通过统一网页入口展示每个 TASK 的报告、代码、数据与交互图表。

### 已完成任务

| 任务 | 内容 | 主要成果 |
| --- | --- | --- |
| TASK1 | 从零搭建量化交易数据引擎 | Tushare 数据抓取、日线 CSV、行情与公司对比看板 |
| TASK2 | 数据诊断与交易指标构造 | 缺失值诊断、RSI、MACD、布林带、KDJ |
| TASK3 | 双均线交易策略与回测 | 金叉与死叉、MA50/200、滞后信号、交易成本、MDD、夏普比率 |
| TASK4 | 海龟交易法则实战 | 高低点通道、ATR、2ATR 止损、严格时序回测、参数比较 |
| TASK5 | AI 交易引擎与分类机器学习 | 决策树、随机森林、混淆矩阵、AUC、ROC 曲线、特征重要性 |
| TASK6 | 智能决策者：ML 选股与季度 Top 30 策略 | 4 模型（LR / Logr / DT / RF）、EW + PW 组合、夏普、信息比率、超额胜率 |

### 仓库结构

```text
AI-quant/
├── index.html                 # 课程任务总入口
├── task1.html ~ task6.html    # 各 TASK 展示页面
├── requirements.txt           # Python 依赖清单（pip install -r requirements.txt）
├── TASK1/                     # TASK1 PDF 与 Python 源码
├── TASK2/                     # TASK2 PDF、Python 源码与指标结果
├── TASK3/                     # TASK3 PDF、Python 源码、图表与回测结果
├── TASK4/                     # TASK4 PDF、Python 源码、图表与海龟回测结果
├── TASK5/                     # TASK5 PDF、Python 源码、ROC/混淆矩阵图与结果 CSV
├── TASK6/                     # TASK6 PDF、Python 源码、4 张图表、4 个模型 .pkl 与结果 CSV
├── material/                  # 课程数据集（CSV，上传 GitHub）；课件截图已 gitignore
└── assets/                    # 共享样式、前端脚本和原始行情数据
```

每个任务的提交物放在对应的 `TASKN/` 目录；跨任务复用的行情数据与网页资源放在 `assets/`。首页任务卡片由 `assets/tasks.js` 统一管理。`material/` 目录下的 CSV 数据集上传 GitHub（保证代码拉取后可直接运行），而 `material/taskN/` 课件截图子目录已在 `.gitignore` 中排除。`__pycache__/` 由 Python 自动生成，同样已排除，无需手动管理。

### 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/jiahui-xin/AI-quant.git
cd AI-quant

# 2. 安装 Python 依赖（Python >= 3.10）
pip install -r requirements.txt

# 3. 运行任意 TASK（会自动读取 material/ 下的 CSV 并重新生成图表、CSV 与 PDF）
python TASK3/task3_moving_average_strategy.py
python TASK4/task4_turtle_strategy.py
python TASK5/task5_classification_models.py
python TASK6/task6_ml_stock_selection.py
```

> TASK1 仅使用标准库，无需额外依赖；TASK2 仅依赖 numpy + pandas。
> PDF 报告生成需要系统中文字体 SimSun。

### 新增后续任务

1. 新建 `TASKN/`，保存 PDF、Python 源码、图表和结果文件。
2. 新建 `taskN.html`，沿用现有任务页的导航和页面结构。
3. 如需独立交互逻辑，在 `assets/` 下新增 `taskN_app.js`。
4. 在 `assets/tasks.js` 中增加任务配置，首页将自动生成 TASKN 卡片。
5. 在已有任务页面的顶部导航中增加 TASKN 入口。

> 本项目仅用于课程研究与学习，不构成投资建议。

---

## English Version

This repository contains quantitative-trading coursework for the PKU Guanghua Business Analysis workshop. Using representative innovative-pharma companies as the research sample, the project progresses from a market-data engine to data diagnostics, technical indicators, a moving-average crossover strategy, Turtle Trading, classification machine learning, and a ML-based quarterly Top 30 stock selection strategy. A unified website presents the report, source code, datasets, and interactive charts for every task.

### Completed Tasks

| Task | Topic | Main Deliverables |
| --- | --- | --- |
| TASK1 | Building a quantitative market-data engine | Tushare data collection, daily CSV files, price and company-comparison dashboards |
| TASK2 | Data diagnostics and trading indicators | Missing-value diagnostics, RSI, MACD, Bollinger Bands, and KDJ |
| TASK3 | Moving-average strategy and backtesting | Golden/death crosses, MA50/200, lagged signals, trading costs, MDD, and Sharpe ratio |
| TASK4 | Turtle Trading strategy | Price channels, ATR, 2ATR stop loss, strict-timing backtest, and parameter comparison |
| TASK5 | AI trading engine with classification ML | Decision Tree, Random Forest, Confusion Matrix, AUC, ROC curves, and feature importance |
| TASK6 | Smart decision maker: ML stock selection with quarterly Top 30 | 4 models (LR / Logr / DT / RF), EW + PW portfolios, Sharpe, information ratio, excess win rate |

### Repository Structure

```text
AI-quant/
├── index.html                 # Course-task portal
├── task1.html ~ task6.html    # Per-task dashboards
├── requirements.txt           # Python dependencies (pip install -r requirements.txt)
├── TASK1/                     # TASK1 PDF and Python source
├── TASK2/                     # TASK2 PDF, Python source, and indicator results
├── TASK3/                     # TASK3 PDF, Python source, figures, and backtest results
├── TASK4/                     # TASK4 PDF, Python source, figures, and Turtle backtest results
├── TASK5/                     # TASK5 PDF, Python source, ROC/confusion-matrix figures, and result CSVs
├── TASK6/                     # TASK6 PDF, Python source, 4 figures, 4 trained models, and result CSVs
├── material/                  # Course datasets (CSV, uploaded); lecture screenshots are gitignored
└── assets/                    # Shared styles, frontend scripts, and raw market data
```

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/jiahui-xin/AI-quant.git
cd AI-quant

# 2. Install Python dependencies (Python >= 3.10)
pip install -r requirements.txt

# 3. Run any TASK (auto-reads CSVs under material/ and regenerates figures, CSVs, and PDFs)
python TASK3/task3_moving_average_strategy.py
python TASK4/task4_turtle_strategy.py
python TASK5/task5_classification_models.py
python TASK6/task6_ml_stock_selection.py
```

> TASK1 uses only the standard library; TASK2 needs only numpy + pandas.
> PDF generation requires the SimSun font installed on the system.

Task-specific deliverables belong in their corresponding `TASKN/` directories. Shared market data and website assets remain under `assets/`. The homepage task cards are managed centrally in `assets/tasks.js`. The `material/` directory holds course raw data and lecture screenshots and is excluded from GitHub via `.gitignore`.

### Adding Future Tasks

1. Create `TASKN/` for its PDF, Python source, figures, and result files.
2. Create `taskN.html` using the existing task-page navigation and layout.
3. Add `assets/taskN_app.js` when task-specific interaction is required.
4. Add one task entry to `assets/tasks.js`; the homepage will generate the TASKN card automatically.
5. Add TASKN to the navigation bar on the existing task pages.

> This project is for coursework and educational research only. It is not investment advice.
