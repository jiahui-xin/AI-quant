# AI-quant｜量化交易课程任务站点

<p align="center">
  <a href="#中文说明">中文</a> ·
  <a href="#english-version">English</a> ·
  <a href="https://jiahui-xin.github.io/AI-quant/">在线站点 / Live Site</a>
</p>

---

## 中文说明

本仓库用于管理北大光华商业分析（BA）工作坊的量化交易课程任务。项目围绕创新药代表公司，依次完成行情数据引擎、数据诊断与技术指标、双均线策略和回测，并通过统一网页入口展示每个 TASK 的报告、代码、数据与交互图表。

### 已完成任务

| 任务 | 内容 | 主要成果 |
| --- | --- | --- |
| TASK1 | 从零搭建量化交易数据引擎 | Tushare 数据抓取、日线 CSV、行情与公司对比看板 |
| TASK2 | 数据诊断与交易指标构造 | 缺失值诊断、RSI、MACD、布林带、KDJ |
| TASK3 | 双均线交易策略与回测 | 金叉与死叉、模拟交易、MDD、夏普比率、参数比较 |

### 仓库结构

```text
AI-quant/
├── index.html                 # 课程任务总入口
├── task1.html                 # TASK1 展示页面
├── task2.html                 # TASK2 展示页面
├── task3.html                 # TASK3 展示页面
├── TASK1/                     # TASK1 PDF 与 Python 源码
├── TASK2/                     # TASK2 PDF、Python 源码与指标结果
├── TASK3/                     # TASK3 PDF、Python 源码、图表与回测结果
└── assets/                    # 共享样式、前端脚本和原始行情数据
```

每个任务的提交物放在对应的 `TASKN/` 目录；跨任务复用的行情数据与网页资源放在 `assets/`。首页任务卡片由 `assets/tasks.js` 统一管理。

### 新增后续任务

1. 新建 `TASK4/`，保存 PDF、Python 源码、图表和结果文件。
2. 新建 `task4.html`，沿用现有任务页的导航和页面结构。
3. 如需独立交互逻辑，在 `assets/` 下新增 `task4_app.js`。
4. 在 `assets/tasks.js` 中增加任务配置，首页将自动生成 TASK4 卡片。
5. 在已有任务页面的顶部导航中增加 TASK4 入口。

> 本项目仅用于课程研究与学习，不构成投资建议。

---

## English Version

This repository contains quantitative-trading coursework for the PKU Guanghua Business Analysis workshop. Using representative innovative-pharma companies as the research sample, the project progresses from a market-data engine to data diagnostics, technical indicators, a moving-average crossover strategy, and backtesting. A unified website presents the report, source code, datasets, and interactive charts for every task.

### Completed Tasks

| Task | Topic | Main Deliverables |
| --- | --- | --- |
| TASK1 | Building a quantitative market-data engine | Tushare data collection, daily CSV files, price and company-comparison dashboards |
| TASK2 | Data diagnostics and trading indicators | Missing-value diagnostics, RSI, MACD, Bollinger Bands, and KDJ |
| TASK3 | Moving-average strategy and backtesting | Golden/death crosses, simulated trading, MDD, Sharpe ratio, and parameter comparison |

### Repository Structure

```text
AI-quant/
├── index.html                 # Course-task portal
├── task1.html                 # TASK1 dashboard
├── task2.html                 # TASK2 dashboard
├── task3.html                 # TASK3 dashboard
├── TASK1/                     # TASK1 PDF and Python source
├── TASK2/                     # TASK2 PDF, Python source, and indicator results
├── TASK3/                     # TASK3 PDF, Python source, figures, and backtest results
└── assets/                    # Shared styles, frontend scripts, and raw market data
```

Task-specific deliverables belong in their corresponding `TASKN/` directories. Shared market data and website assets remain under `assets/`. The homepage task cards are managed centrally in `assets/tasks.js`.

### Adding Future Tasks

1. Create `TASK4/` for its PDF, Python source, figures, and result files.
2. Create `task4.html` using the existing task-page navigation and layout.
3. Add `assets/task4_app.js` when task-specific interaction is required.
4. Add one task entry to `assets/tasks.js`; the homepage will generate the TASK4 card automatically.
5. Add TASK4 to the navigation bar on the existing task pages.

> This project is for coursework and educational research only. It is not investment advice.
