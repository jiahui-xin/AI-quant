(function () {
  const payload = window.TASK2_DATA;
  const companies = payload.companies || [{ summary: payload.summary, records: payload.records }];
  let activeIndex = 0;

  const bollinger = echarts.init(document.getElementById("bollingerChart"));
  const rsi = echarts.init(document.getElementById("rsiChart"));
  const macd = echarts.init(document.getElementById("macdChart"));
  const kdj = echarts.init(document.getElementById("kdjChart"));
  const charts = [bollinger, rsi, macd, kdj];

  function current() {
    return companies[activeIndex];
  }

  function fmtDate(value) {
    if (typeof value === "string" && value.includes("-")) return value;
    return `${String(value).slice(0, 4)}-${String(value).slice(4, 6)}-${String(value).slice(6, 8)}`;
  }

  function num(value, digits = 2) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
    return Number(value).toFixed(digits);
  }

  function signed(value) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
    return `${Number(value) > 0 ? "+" : ""}${Number(value).toFixed(2)}%`;
  }

  function renderControls() {
    const container = document.getElementById("task2CompanyControls");
    container.innerHTML = companies.map((item, index) => `
      <button class="seg ${index === activeIndex ? "active" : ""}" data-index="${index}">${item.summary.stock}</button>
    `).join("");
    container.querySelectorAll("button").forEach((button) => {
      button.addEventListener("click", () => {
        activeIndex = Number(button.dataset.index);
        renderAll();
      });
    });
  }

  function renderMetrics() {
    const { summary } = current();
    const latest = summary.latest;
    const missingTotal = Object.values(summary.missing).reduce((sum, value) => sum + Number(value), 0);
    document.getElementById("task2MetricGrid").innerHTML = `
      <article class="metric-card">
        <div class="metric-top"><h3>${summary.stock}</h3><span class="badge">${summary.code}</span></div>
        <div class="metric-list">
          <div class="metric-line"><span>开始日期</span><strong>${summary.start_date}</strong></div>
          <div class="metric-line"><span>结束日期</span><strong>${summary.end_date}</strong></div>
          <div class="metric-line"><span>交易日数量</span><strong>${summary.rows}</strong></div>
        </div>
      </article>
      <article class="metric-card">
        <div class="metric-top"><h3>缺失值</h3><span class="badge">Quality</span></div>
        <div class="metric-list">
          <div class="metric-line"><span>总缺失值</span><strong>${missingTotal}</strong></div>
          <div class="metric-line"><span>字段数量</span><strong>${Object.keys(summary.missing).length}</strong></div>
          <div class="metric-line"><span>诊断结论</span><strong class="positive">可直接计算</strong></div>
        </div>
      </article>
      <article class="metric-card">
        <div class="metric-top"><h3>最新指标</h3><span class="badge">${latest.date}</span></div>
        <div class="metric-list">
          <div class="metric-line"><span>收盘价</span><strong>${num(latest.close)}</strong></div>
          <div class="metric-line"><span>RSI(14)</span><strong>${num(latest.rsi14)}</strong></div>
          <div class="metric-line"><span>KDJ J</span><strong>${num(latest.kdj_j)}</strong></div>
        </div>
      </article>
      <article class="metric-card">
        <div class="metric-top"><h3>区间表现</h3><span class="badge">Return</span></div>
        <div class="metric-list">
          <div class="metric-line"><span>区间收益</span><strong class="${summary.return_pct >= 0 ? "positive" : "negative"}">${signed(summary.return_pct)}</strong></div>
          <div class="metric-line"><span>最低收盘价</span><strong>${num(summary.description.close.min)}</strong></div>
          <div class="metric-line"><span>最高收盘价</span><strong>${num(summary.description.close.max)}</strong></div>
        </div>
      </article>
    `;
  }

  function renderTable() {
    const { summary } = current();
    const rows = [
      ["open", "开盘价"],
      ["high", "最高价"],
      ["low", "最低价"],
      ["close", "收盘价"],
      ["vol", "成交量"],
      ["amount", "成交额"],
      ["pct_chg", "涨跌幅"]
    ];
    document.getElementById("descTable").innerHTML = `
      <thead><tr><th>指标</th><th>均值</th><th>标准差</th><th>最小值</th><th>中位数</th><th>最大值</th></tr></thead>
      <tbody>
        ${rows.map(([key, label]) => {
          const item = summary.description[key];
          return `<tr><td>${label}</td><td>${num(item.mean)}</td><td>${num(item.std)}</td><td>${num(item.min)}</td><td>${num(item["50%"])}</td><td>${num(item.max)}</td></tr>`;
        }).join("")}
      </tbody>
    `;
  }

  function dates(records) {
    return records.map((row) => fmtDate(row.trade_date));
  }

  function renderCharts() {
    const { summary, records } = current();
    const latest = summary.latest;
    const x = dates(records);

    document.getElementById("bbTitle").textContent = `图1 ${summary.stock}收盘价与布林带`;

    bollinger.setOption({
      color: ["#006d77", "#334155", "#b7791f"],
      tooltip: { trigger: "axis" },
      legend: { top: 0 },
      grid: { left: 48, right: 28, top: 54, bottom: 44 },
      xAxis: { type: "category", data: x, boundaryGap: false },
      yAxis: { type: "value", name: "价格", scale: true },
      series: [
        { name: "收盘价", type: "line", showSymbol: false, smooth: true, data: records.map((row) => row.close), lineStyle: { width: 2 } },
        { name: "20日中轨", type: "line", showSymbol: false, smooth: true, data: records.map((row) => row.bb_mid), lineStyle: { width: 1.5 } },
        { name: "上轨", type: "line", showSymbol: false, smooth: true, data: records.map((row) => row.bb_upper), lineStyle: { width: 1.2 } },
        { name: "下轨", type: "line", showSymbol: false, smooth: true, data: records.map((row) => row.bb_lower), lineStyle: { width: 1.2 } }
      ]
    }, true);

    rsi.setOption({
      color: ["#2563eb", "#b91c1c", "#15803d"],
      tooltip: { trigger: "axis" },
      legend: { top: 0 },
      grid: { left: 42, right: 24, top: 50, bottom: 38 },
      xAxis: { type: "category", data: x, boundaryGap: false },
      yAxis: { type: "value", min: 0, max: 100 },
      series: [
        { name: "RSI(14)", type: "line", showSymbol: false, data: records.map((row) => row.rsi14) },
        { name: "70", type: "line", showSymbol: false, data: records.map(() => 70), lineStyle: { type: "dashed" } },
        { name: "30", type: "line", showSymbol: false, data: records.map(() => 30), lineStyle: { type: "dashed" } }
      ]
    }, true);

    macd.setOption({
      color: ["#1d4ed8", "#b45309"],
      tooltip: { trigger: "axis" },
      legend: { top: 0 },
      grid: { left: 46, right: 24, top: 50, bottom: 38 },
      xAxis: { type: "category", data: x, boundaryGap: false },
      yAxis: { type: "value", scale: true },
      series: [
        { name: "MACD柱", type: "bar", data: records.map((row) => row.macd_hist), itemStyle: { color: (p) => p.value >= 0 ? "rgba(185,28,28,.55)" : "rgba(21,128,61,.55)" } },
        { name: "DIF", type: "line", showSymbol: false, data: records.map((row) => row.macd) },
        { name: "DEA", type: "line", showSymbol: false, data: records.map((row) => row.macd_signal) }
      ]
    }, true);

    kdj.setOption({
      color: ["#006d77", "#2563eb", "#b45309"],
      tooltip: { trigger: "axis" },
      legend: { top: 0 },
      grid: { left: 42, right: 24, top: 50, bottom: 38 },
      xAxis: { type: "category", data: x, boundaryGap: false },
      yAxis: { type: "value", scale: true },
      series: [
        { name: "K", type: "line", showSymbol: false, data: records.map((row) => row.kdj_k) },
        { name: "D", type: "line", showSymbol: false, data: records.map((row) => row.kdj_d) },
        { name: "J", type: "line", showSymbol: false, data: records.map((row) => row.kdj_j) }
      ]
    }, true);

    document.getElementById("bbCaption").textContent = `${summary.stock}最新收盘价 ${num(latest.close)}，布林带上轨 ${num(latest.bb_upper)}、中轨 ${num(latest.bb_mid)}、下轨 ${num(latest.bb_lower)}。`;
    document.getElementById("rsiCaption").textContent = `${summary.stock}最新 RSI(14) 为 ${num(latest.rsi14)}，用于观察近期动量是否偏热或偏冷。`;
    document.getElementById("macdCaption").textContent = `${summary.stock}最新 DIF 为 ${num(latest.macd, 4)}，DEA 为 ${num(latest.macd_signal, 4)}，MACD柱为 ${num(latest.macd_hist, 4)}。`;
    document.getElementById("kdjCaption").textContent = `${summary.stock}最新 K=${num(latest.kdj_k)}，D=${num(latest.kdj_d)}，J=${num(latest.kdj_j)}；KDJ 是本次扩展计算指标。`;
  }

  function resizeAll() {
    charts.forEach((chart) => chart.resize());
  }

  function renderAll() {
    renderControls();
    renderMetrics();
    renderTable();
    renderCharts();
    setTimeout(resizeAll, 60);
  }

  window.addEventListener("resize", resizeAll);
  if ("ResizeObserver" in window) {
    const observer = new ResizeObserver(resizeAll);
    document.querySelectorAll(".chart").forEach((node) => observer.observe(node));
  }

  renderAll();
  setTimeout(resizeAll, 300);
})();
