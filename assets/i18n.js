(function () {
  const dict = {
    "首页": "Home",
    "TASK1": "TASK1",
    "TASK2": "TASK2",
    "TASK3": "TASK3",
    "TASK4": "TASK4",
    "PDF": "PDF",
    "智能看板": "Dashboard",
    "龙头矩阵": "Leaders",
    "研究卡片": "Reports",
    "AI-quant / TASK1": "AI-quant / TASK1",
    "AI-quant / TASK2": "AI-quant / TASK2",
    "北大光华商业分析（BA）工作坊——量化交易：AI大模型辅助的金融交易策略": "PKU Guanghua Business Analysis Workshop: Quant Trading Strategies Assisted by AI Models",
    "创新药量化研究作品集": "Innovative Pharma Quant Portfolio",
    "围绕创新药龙头企业，逐步搭建数据引擎、完成数据诊断、构造交易指标，并用网页看板管理每一次任务成果。": "A course portfolio focused on innovative pharma leaders: building a data engine, diagnosing data quality, constructing indicators, and managing each task with web dashboards.",
    "查看 TASK2 指标看板": "View TASK2 Indicator Dashboard",
    "回看 TASK1 数据引擎": "Review TASK1 Data Engine",
    "页面管理": "Page Management",
    "同一个 GitHub 仓库可以管理多个页面。当前首页负责导航，具体任务分别放在独立 HTML 页面中，数据、脚本和 PDF 统一放在 assets 与 downloads 目录下。": "One GitHub repository can manage multiple pages. This homepage is the navigation entry; each task has its own HTML page, while data, scripts, and PDFs live under assets and downloads.",
    "量化交易初体验：从零搭建数据引擎": "Quant Trading First Step: Building a Data Engine",
    "使用 Tushare 获取创新药代表公司的日线行情，构建 CSV 数据文件，并展示公司矩阵、K 线看板和行业对照图谱。": "Use Tushare to fetch daily prices for representative innovative pharma companies, build CSV data files, and present company matrices, K-line dashboards, and peer charts.",
    "进入 TASK1": "Open TASK1",
    "数据炼金术：数据诊断与构造交易指标": "Data Alchemy: Diagnostics and Trading Indicators",
    "对恒瑞医药已保存股价数据进行缺失值诊断、描述性统计，计算 RSI、MACD、布林带和 KDJ，并形成交互图表。": "Diagnose saved price data, compute descriptive statistics, calculate RSI, MACD, Bollinger Bands, and KDJ, and render interactive charts.",
    "进入 TASK2": "Open TASK2",
    "进入 TASK3": "Open TASK3",
    "进入 TASK4": "Open TASK4",
    "复刻传奇：海龟交易法则实战演练": "Recreating a Legend: Turtle Trading in Practice",
    "使用高低点通道、ATR 与 2ATR 止损构建海龟趋势策略，完成严格时序回测和跨股票参数比较。": "Build a Turtle trend strategy with price channels, ATR, and a 2ATR stop, then run strict-timing backtests and cross-stock parameter comparisons.",
    "查看 TASK4 海龟策略": "View TASK4 Turtle Strategy",
    "进入海龟实验室": "Open Turtle Lab",
    "海龟策略的四个核心环节": "Four Core Components of Turtle Trading",
    "海龟策略实验室": "Turtle Strategy Lab",
    "股票与通道参数比较": "Stock and Channel Comparison",
    "策略首秀：用均线交叉反映市场趋势变化": "Strategy Debut: Tracking Trends with Moving-Average Crossovers",
    "实现双均线金叉与死叉信号，完成模拟交易和回测，并比较不同股票、不同均线周期的收益与风险。": "Build golden-cross and death-cross signals, backtest simulated trades, and compare return and risk across stocks and moving-average windows.",
    "查看 TASK3 策略回测": "View TASK3 Backtest",
    "浏览全部任务": "Browse All Tasks",
    "用均线交叉捕捉市场趋势变化": "Capture Market Trends with Moving-Average Crossovers",
    "进入策略实验室": "Open Strategy Lab",
    "下载作业报告": "Download Report",
    "双均线策略与评价指标": "Moving-Average Strategy and Metrics",
    "策略实验室": "Strategy Lab",
    "选择股票": "Select Stock",
    "均线周期": "Moving-Average Windows",
    "股票与周期比较": "Stock and Window Comparison",
    "策略源码与回测结果": "Strategy Code and Backtest Results",
    "下载 PDF": "Download PDF",
    "作者：辛家辉": "Author: Jiahui Xin",
    "主题：创新药量化观察": "Theme: Innovative Pharma Quant Watch",
    "部署：GitHub Pages": "Deployment: GitHub Pages",
    "本页面仅供课程研究参考，不构成投资建议。": "For course research only. Not investment advice.",

    "用数据引擎观察创新药龙头企业": "Observe Innovative Pharma Leaders with a Data Engine",
    "聚焦恒瑞医药、百济神州、君实生物、复星医药，整合最近一年日线交易数据、收益波动、回撤和成交额变化，形成可复用的创新药公司量化观察页。": "Focus on Hengrui Pharma, BeiGene, Junshi Biosciences, and Fosun Pharma, integrating one year of daily trading data, returns, volatility, drawdowns, and turnover.",
    "进入看板": "Open Dashboard",
    "下载数据 JSON": "Download JSON",
    "创新药龙头智能看板": "Innovative Pharma Leader Dashboard",
    "参考单股 K 线看板的展示方式，将行情、技术指标、资金活跃度、公司定位和风险提示集中到一个可切换的研究面板。": "A switchable research dashboard combining price action, technical indicators, trading activity, company positioning, and risk notes.",
    "技术面快照": "Technical Snapshot",
    "创新药观察": "Pharma Thesis",
    "龙头矩阵": "Leader Matrix",
    "页面数据由 Tushare Pro 日线接口生成，时间范围为最近一年交易日。指标仅用于课堂研究和网页展示，不构成投资建议。": "Data are generated from Tushare Pro daily prices over the latest year. Indicators are for coursework and display only.",
    "行业对照图谱": "Peer Comparison",
    "上方图表比较四家公司收盘价归一化走势，下方图表展示单家公司每日收盘价与成交额变化。": "The upper chart compares normalized closing prices; the lower chart shows closing price and turnover for the selected company.",
    "以各公司样本期首个收盘价为 100，观察不同公司在同一时间窗口内的相对表现。": "Set each company's first closing price to 100 to compare relative performance.",
    "收盘价用于观察价格趋势，成交额用于辅助判断交易活跃度和资金关注变化。": "Closing price shows price trends; turnover helps assess trading activity and capital attention.",
    "参考报告门户的卡片式结构，每张卡片对应一家创新药公司，可下载该公司的 CSV 数据用于后续任务。": "Report cards correspond to each company and provide CSV downloads for later tasks.",
    "数据来源：Tushare Pro API": "Data source: Tushare Pro API",
    "可视化引擎：ECharts": "Visualization: ECharts",
    "生成时间：2026年7月4日": "Generated: July 4, 2026",
    "恒瑞医药": "Hengrui Pharma",
    "百济神州": "BeiGene",
    "君实生物": "Junshi Biosciences",
    "复星医药": "Fosun Pharma",
    "样本交易日": "Trading Days",
    "最新成交额": "Latest Turnover",
    "研究主线": "Research Thesis",
    "看多逻辑": "Bullish Thesis",
    "风险提示": "Risks",
    "区间收益": "Period Return",
    "期末收盘": "Ending Close",
    "最大回撤": "Max Drawdown",
    "日波动率": "Daily Volatility",
    "下载 CSV 数据": "Download CSV",

    "数据诊断与交易指标构造": "Data Diagnostics and Trading Indicator Construction",
    "以 TASK1 中的四家创新药相关企业为案例，检查缺失值、计算描述性统计量，并构造 RSI、MACD、布林带和 KDJ 指标。": "Using the four innovative pharma companies from TASK1, diagnose missing values, compute descriptive statistics, and construct RSI, MACD, Bollinger Bands, and KDJ.",
    "查看诊断结果": "View Diagnostics",
    "下载提交 PDF": "Download PDF",
    "数据质量诊断": "Data Quality Diagnostics",
    "数据来自 TASK1 已保存的四家公司日线 CSV。诊断重点包括样本区间、缺失值、收盘价分布、成交额和涨跌幅波动。": "Data come from the four daily CSV files saved in TASK1. Diagnostics cover sample range, missing values, closing price distribution, turnover, and daily return volatility.",
    "核心指标图谱": "Core Indicator Charts",
    "指标从趋势、动量、波动率和短期相对位置四个角度描述市场状态。技术指标不是单独的买卖结论，应与基本面、交易成本和风险控制结合使用。": "Indicators describe trend, momentum, volatility, and short-term relative position. They are not standalone trading decisions.",
    "收盘价与布林带": "Close Price and Bollinger Bands",
    "扩展指标 KDJ": "Extended Indicator: KDJ",
    "提交文件与数据": "Artifacts and Data",
    "PDF 文档、指标 CSV 与 Python 脚本均已保留，便于后续 TASK3 继续复用。": "The PDF, indicator CSV files, and Python script are preserved for reuse in TASK3.",
    "PDF 文档、原始日线 CSV 与前端数据均已保存，便于后续 TASK2 指标计算继续复用。": "The PDF, raw daily CSV files, and frontend data are saved for reuse in TASK2 indicator calculations.",
    "符合提交要求的 PDF 文档，包含数据诊断、指标计算方法、图表和解读。": "Submission-ready PDF including diagnostics, formulas, charts, and interpretation.",
    "新版 PDF 已与网页主题对齐，使用恒瑞医药真实日线数据和收盘价曲线图，不再使用占位图。": "The revised PDF now matches the website theme, using real Hengrui daily data and a real closing-price chart instead of a placeholder.",
    "原始股价数据": "Raw Price Data",
    "四家创新药相关公司的日线 CSV 保存在 assets 目录，TASK2 已在此基础上继续计算 RSI、MACD、布林带和 KDJ。": "Daily CSV files for the four innovative pharma companies are stored in assets; TASK2 reuses them to calculate RSI, MACD, Bollinger Bands, and KDJ.",
    "下载恒瑞 CSV": "Download Hengrui CSV",
    "指标数据": "Indicator Data",
    "页面图表由 `assets/task2_data.js` 提供，四家公司各自的 RSI、MACD、布林带和 KDJ 指标 CSV 已单独保存。": "Charts are powered by assets/task2_data.js; each company's RSI, MACD, Bollinger Bands, and KDJ CSV is saved separately.",
    "查看前端数据": "View Frontend Data",
    "下载恒瑞指标 CSV": "Download Hengrui CSV",
    "样本：四家创新药相关企业": "Sample: Four Innovative Pharma Companies",
    "指标：RSI / MACD / Bollinger Bands / KDJ": "Indicators: RSI / MACD / Bollinger Bands / KDJ",
    "样本区间": "Sample Range",
    "开始日期": "Start Date",
    "结束日期": "End Date",
    "交易日数量": "Trading Days",
    "缺失值": "Missing Values",
    "总缺失值": "Total Missing",
    "字段数量": "Field Count",
    "诊断结论": "Conclusion",
    "可直接计算": "Ready to Compute",
    "最新指标": "Latest Indicators",
    "收盘价": "Close",
    "区间表现": "Period Performance",
    "最低收盘价": "Lowest Close",
    "最高收盘价": "Highest Close",
    "指标": "Metric",
    "均值": "Mean",
    "标准差": "Std",
    "最小值": "Min",
    "中位数": "Median",
    "最大值": "Max",
    "开盘价": "Open",
    "最高价": "High",
    "最低价": "Low",
    "成交量": "Volume",
    "成交额": "Amount",
    "涨跌幅": "Pct Chg",
    "价格": "Price"
  };

  const originalText = new WeakMap();
  const originalAttrs = new WeakMap();
  let scheduled = false;
  let translating = false;

  function getLang() {
    return localStorage.getItem("aiq_lang") || "zh";
  }

  function setLang(lang) {
    localStorage.setItem("aiq_lang", lang);
    document.documentElement.lang = lang === "en" ? "en" : "zh-CN";
    translate();
  }

  function translateTextNode(node, lang) {
    if (!originalText.has(node)) originalText.set(node, node.nodeValue);
    const original = originalText.get(node);
    if (lang === "zh") {
      if (node.nodeValue !== original) node.nodeValue = original;
      return;
    }
    const trimmed = original.trim();
    if (!trimmed || !dict[trimmed]) return;
    const next = original.replace(trimmed, dict[trimmed]);
    if (node.nodeValue !== next) node.nodeValue = next;
  }

  function translateAttrs(element, lang) {
    ["title", "aria-label", "placeholder"].forEach((attr) => {
      if (!element.hasAttribute(attr)) return;
      if (!originalAttrs.has(element)) originalAttrs.set(element, {});
      const saved = originalAttrs.get(element);
      if (!saved[attr]) saved[attr] = element.getAttribute(attr);
      if (lang === "zh") {
        element.setAttribute(attr, saved[attr]);
      } else if (dict[saved[attr]]) {
        element.setAttribute(attr, dict[saved[attr]]);
      }
    });
  }

  function walk(root, lang) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        const parent = node.parentElement;
        if (!parent || ["SCRIPT", "STYLE", "NOSCRIPT"].includes(parent.tagName)) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => translateTextNode(node, lang));
    document.querySelectorAll("[title], [aria-label], [placeholder]").forEach((el) => translateAttrs(el, lang));
  }

  function ensureButton() {
    if (document.querySelector(".lang-toggle")) return;
    const nav = document.querySelector(".nav-links");
    if (!nav) return;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "lang-toggle";
    button.addEventListener("click", () => setLang(getLang() === "en" ? "zh" : "en"));
    nav.appendChild(button);
  }

  function translate() {
    if (translating) return;
    translating = true;
    ensureButton();
    const lang = getLang();
    document.documentElement.lang = lang === "en" ? "en" : "zh-CN";
    walk(document.body, lang);
    document.querySelectorAll(".lang-toggle").forEach((button) => {
      button.textContent = lang === "en" ? "中文" : "EN";
      button.setAttribute("aria-label", lang === "en" ? "Switch to Chinese" : "Switch to English");
    });
    translating = false;
  }

  function scheduleTranslate() {
    if (scheduled || getLang() !== "en") return;
    scheduled = true;
    window.requestAnimationFrame(() => {
      scheduled = false;
      translate();
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    translate();
    const observer = new MutationObserver(scheduleTranslate);
    observer.observe(document.body, { childList: true, subtree: true, characterData: true });
    document.addEventListener("click", () => {
      if (getLang() === "en") setTimeout(translate, 80);
    });
  });
})();
