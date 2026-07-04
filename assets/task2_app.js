(function () {
  const payload = window.TASK2_DATA;
  const summary = payload.summary;
  const records = payload.records;
  const latest = summary.latest;

  function fmtDate(value) {
    if (typeof value === "string" && value.includes("-")) return value;
    return `${String(value).slice(0, 4)}-${String(value).slice(4, 6)}-${String(value).slice(6, 8)}`;
  }

  function num(value, digits = 2) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
    return Number(value).toFixed(digits);
  }

  function renderMetrics() {
    const missingTotal = Object.values(summary.missing).reduce((sum, value) => sum + Number(value), 0);
    document.getElementById("task2MetricGrid").innerHTML = `
      <article class="metric-card">
        <div class="metric-top"><h3>样本区间</h3><span class="badge">日线</span></div>
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
        <div class="metric-top"><h3>波动观察</h3><span class="badge">Close</span></div>
        <div class="metric-list">
          <div class="metric-line"><span>收盘价均值</span><strong>${num(summary.description.close.mean)}</strong></div>
          <div class="metric-line"><span>最低收盘价</span><strong>${num(summary.description.close.min)}</strong></div>
          <div class="metric-line"><span>最高收盘价</span><strong>${num(summary.description.close.max)}</strong></div>
        </div>
      </article>
    `;
  }

  function renderTable() {
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

  function dates() {
    return records.map((row) => fmtDate(row.trade_date));
  }

  function resizeAll(charts) {
    charts.forEach((chart) => chart.resize());
  }

  function renderCharts() {
    const x = dates();
    const bollinger = echarts.init(document.getElementById("bollingerChart"));
    const rsi = echarts.init(document.getElementById("rsiChart"));
    const macd = echarts.init(document.getElementById("macdChart"));
    const kdj = echarts.init(document.getElementById("kdjChart"));
    const charts = [bollinger, rsi, macd, kdj];

    bollinger.setOption({
      color: ["#006d77", "#334155", "#b7791f"],
      tooltip: { trigger: "axis" },
      legend: { top: 0 },
      grid: { left: 48, right: 28, top: 54, bottom: 44 },
      xAxis: { type: "category", data: x, boundaryGap: false },
      yAxis: { type: "value", name: "价格", scale: true },
      series: [
        { name: "收盘价", type: "line", showSymbol: false, smooth: true, data: records.map((r) => r.close), lineStyle: { width: 2 } },
        { name: "20日中轨", type: "line", showSymbol: false, smooth: true, data: records.map((r) => r.bb_mid), lineStyle: { width: 1.5 } },
        { name: "上轨", type: "line", showSymbol: false, smooth: true, data: records.map((r) => r.bb_upper), lineStyle: { width: 1.2 } },
        { name: "下轨", type: "line", showSymbol: false, smooth: true, data: records.map((r) => r.bb_lower), lineStyle: { width: 1.2 } }
      ]
    });

    rsi.setOption({
      color: ["#2563eb", "#b91c1c", "#15803d"],
      tooltip: { trigger: "axis" },
      legend: { top: 0 },
      grid: { left: 42, right: 24, top: 50, bottom: 38 },
      xAxis: { type: "category", data: x, boundaryGap: false },
      yAxis: { type: "value", min: 0, max: 100 },
      series: [
        { name: "RSI(14)", type: "line", showSymbol: false, data: records.map((r) => r.rsi14) },
        { name: "70", type: "line", showSymbol: false, data: records.map(() => 70), lineStyle: { type: "dashed" } },
        { name: "30", type: "line", showSymbol: false, data: records.map(() => 30), lineStyle: { type: "dashed" } }
      ]
    });

    macd.setOption({
      color: ["#1d4ed8", "#b45309"],
      tooltip: { trigger: "axis" },
      legend: { top: 0 },
      grid: { left: 46, right: 24, top: 50, bottom: 38 },
      xAxis: { type: "category", data: x, boundaryGap: false },
      yAxis: { type: "value", scale: true },
      series: [
        { name: "MACD柱", type: "bar", data: records.map((r) => r.macd_hist), itemStyle: { color: (p) => p.value >= 0 ? "rgba(185,28,28,.55)" : "rgba(21,128,61,.55)" } },
        { name: "DIF", type: "line", showSymbol: false, data: records.map((r) => r.macd) },
        { name: "DEA", type: "line", showSymbol: false, data: records.map((r) => r.macd_signal) }
      ]
    });

    kdj.setOption({
      color: ["#006d77", "#2563eb", "#b45309"],
      tooltip: { trigger: "axis" },
      legend: { top: 0 },
      grid: { left: 42, right: 24, top: 50, bottom: 38 },
      xAxis: { type: "category", data: x, boundaryGap: false },
      yAxis: { type: "value", scale: true },
      series: [
        { name: "K", type: "line", showSymbol: false, data: records.map((r) => r.kdj_k) },
        { name: "D", type: "line", showSymbol: false, data: records.map((r) => r.kdj_d) },
        { name: "J", type: "line", showSymbol: false, data: records.map((r) => r.kdj_j) }
      ]
    });

    document.getElementById("bbCaption").textContent = `最新收盘价 ${num(latest.close)}，接近布林带上轨 ${num(latest.bb_upper)}，短期反弹较强但需关注上轨附近波动。`;
    document.getElementById("rsiCaption").textContent = `最新 RSI(14) 为 ${num(latest.rsi14)}，处于 50 以上但未超过 70，显示近期动能改善但未到典型超买阈值。`;
    document.getElementById("macdCaption").textContent = `最新 DIF 为 ${num(latest.macd, 4)}，DEA 为 ${num(latest.macd_signal, 4)}，柱状图为正，趋势动能偏正。`;
    document.getElementById("kdjCaption").textContent = `最新 K=${num(latest.kdj_k)}，D=${num(latest.kdj_d)}，J=${num(latest.kdj_j)}，J 值高于 80，短线偏热。`;

    window.addEventListener("resize", () => resizeAll(charts));
    if ("ResizeObserver" in window) {
      const observer = new ResizeObserver(() => resizeAll(charts));
      document.querySelectorAll(".chart").forEach((node) => observer.observe(node));
    }
    setTimeout(() => resizeAll(charts), 100);
    setTimeout(() => resizeAll(charts), 500);
  }

  renderMetrics();
  renderTable();
  renderCharts();
})();
