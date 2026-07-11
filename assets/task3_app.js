(function () {
  const companies = [
    { code: "600276_SH", name: "恒瑞医药" },
    { code: "688235_SH", name: "百济神州" },
    { code: "688180_SH", name: "君实生物" },
    { code: "600196_SH", name: "复星医药" }
  ];
  const periods = [[3, 10], [5, 15], [10, 30], [20, 60]];
  const fee = 0.001;
  let activeCompany = 0;
  let activePeriod = 1;
  let priceSets = [];
  let comparisonRows = [];

  const signalChart = echarts.init(document.getElementById("signalChart"));
  const navChart = echarts.init(document.getElementById("navChart"));
  const comparisonChart = echarts.init(document.getElementById("comparisonChart"));
  const charts = [signalChart, navChart, comparisonChart];

  function parseCsv(text) {
    const lines = text.trim().split(/\r?\n/);
    const headers = lines.shift().replace(/^\uFEFF/, "").split(",");
    return lines.map((line) => {
      const values = line.split(",");
      return Object.fromEntries(headers.map((header, index) => [header, values[index]]));
    });
  }

  function fmtDate(value) {
    const s = String(value);
    return `${s.slice(0, 4)}-${s.slice(4, 6)}-${s.slice(6, 8)}`;
  }

  function movingAverage(values, days) {
    let running = 0;
    return values.map((value, index) => {
      running += value;
      if (index >= days) running -= values[index - days];
      return index < days - 1 ? null : +(running / days).toFixed(4);
    });
  }

  function backtest(rows, short, long) {
    const closes = rows.map((row) => Number(row.close));
    const dates = rows.map((row) => fmtDate(row.trade_date));
    const maShort = movingAverage(closes, short);
    const maLong = movingAverage(closes, long);
    const signal = closes.map((_, i) => maLong[i] === null ? 0 : +(maShort[i] > maLong[i]));
    const position = signal.map((_, i) => i === 0 ? 0 : signal[i - 1]);
    const trades = signal.map((value, i) => i === 0 ? value : value - signal[i - 1]);
    const marketReturn = closes.map((value, i) => i === 0 ? 0 : value / closes[i - 1] - 1);
    const strategyReturn = position.map((value, i) => {
      const prior = i === 0 ? 0 : position[i - 1];
      return value * marketReturn[i] - fee * Math.abs(value - prior);
    });
    let strategyNav = 1;
    let buyHoldNav = 1;
    let peak = 1;
    const nav = [];
    const benchmark = [];
    const drawdown = [];
    strategyReturn.forEach((value, i) => {
      strategyNav *= 1 + value;
      buyHoldNav *= 1 + marketReturn[i];
      peak = Math.max(peak, strategyNav);
      nav.push(strategyNav);
      benchmark.push(buyHoldNav);
      drawdown.push(strategyNav / peak - 1);
    });
    const mean = strategyReturn.reduce((sum, value) => sum + value, 0) / strategyReturn.length;
    const variance = strategyReturn.reduce((sum, value) => sum + (value - mean) ** 2, 0) / (strategyReturn.length - 1);
    return {
      dates, closes, maShort, maLong, trades, nav, benchmark, drawdown,
      cumulative: nav.at(-1) - 1,
      maxDrawdown: Math.min(...drawdown),
      sharpe: variance > 0 ? Math.sqrt(252) * mean / Math.sqrt(variance) : 0,
      tradeCount: trades.filter((value) => value !== 0).length,
      buyHold: benchmark.at(-1) - 1
    };
  }

  function pct(value) { return `${(Number(value) * 100).toFixed(2)}%`; }
  function signedPct(value) { return `${Number(value) >= 0 ? "+" : ""}${pct(value)}`; }

  function renderControls() {
    document.getElementById("task3CompanyControls").innerHTML = companies.map((item, index) => `
      <button class="seg ${index === activeCompany ? "active" : ""}" data-company="${index}">${item.name}</button>
    `).join("");
    document.getElementById("task3PeriodControls").innerHTML = periods.map((item, index) => `
      <button class="seg ${index === activePeriod ? "active" : ""}" data-period="${index}">MA${item[0]}/${item[1]}</button>
    `).join("");
    document.querySelectorAll("[data-company]").forEach((button) => button.addEventListener("click", () => {
      activeCompany = Number(button.dataset.company); renderAll();
    }));
    document.querySelectorAll("[data-period]").forEach((button) => button.addEventListener("click", () => {
      activePeriod = Number(button.dataset.period); renderAll();
    }));
  }

  function renderMetrics(result, company, period) {
    const metrics = [
      ["累计回报", signedPct(result.cumulative), result.cumulative],
      ["最大回撤", pct(result.maxDrawdown), result.maxDrawdown],
      ["年化夏普", result.sharpe.toFixed(2), result.sharpe],
      ["交易次数", String(result.tradeCount), null]
    ];
    document.getElementById("task3MetricGrid").innerHTML = metrics.map(([label, value, raw]) => `
      <article class="metric-card">
        <div class="metric-top"><h3>${label}</h3><span class="badge">MA${period[0]}/${period[1]}</span></div>
        <div class="strategy-value ${raw === null ? "" : raw >= 0 ? "positive" : "negative"}">${value}</div>
        <div class="report-meta">${company.name} · 次日生效 · 单边成本 0.10%</div>
      </article>
    `).join("");
  }

  function renderSignalChart(result, company, period) {
    const buys = result.trades.flatMap((trade, i) => trade === 1 ? [[result.dates[i], result.closes[i]]] : []);
    const sells = result.trades.flatMap((trade, i) => trade === -1 ? [[result.dates[i], result.closes[i]]] : []);
    document.getElementById("signalTitle").textContent = `图1 ${company.name} MA${period[0]}/${period[1]} 均线与交易信号`;
    document.getElementById("signalCaption").textContent = `绿色三角为金叉买入信号，红色三角为死叉卖出信号；本组合共出现 ${result.tradeCount} 次买卖信号。`;
    signalChart.setOption({
      animation: false,
      tooltip: { trigger: "axis" },
      legend: { top: 0 },
      grid: { left: 50, right: 28, top: 54, bottom: 54 },
      xAxis: { type: "category", data: result.dates, boundaryGap: false },
      yAxis: { type: "value", name: "价格", scale: true },
      dataZoom: [{ type: "inside", start: 0, end: 100 }, { type: "slider", bottom: 8, height: 18 }],
      series: [
        { name: "收盘价", type: "line", data: result.closes, showSymbol: false, lineStyle: { width: 1.5, color: "#334155" } },
        { name: `MA${period[0]}`, type: "line", data: result.maShort, showSymbol: false, lineStyle: { width: 1.7, color: "#b7791f" } },
        { name: `MA${period[1]}`, type: "line", data: result.maLong, showSymbol: false, lineStyle: { width: 1.7, color: "#2f5597" } },
        { name: "买入", type: "scatter", data: buys, symbol: "triangle", symbolSize: 12, itemStyle: { color: "#2f7d5c" }, z: 5 },
        { name: "卖出", type: "scatter", data: sells, symbol: "triangle", symbolRotate: 180, symbolSize: 12, itemStyle: { color: "#b23a48" }, z: 5 }
      ]
    }, true);
  }

  function renderNavChart(result, company, period) {
    document.getElementById("navTitle").textContent = `图2 ${company.name} MA${period[0]}/${period[1]} 策略净值与回撤`;
    document.getElementById("navCaption").textContent = `策略累计回报 ${signedPct(result.cumulative)}，最大回撤 ${pct(result.maxDrawdown)}；同期买入持有 ${signedPct(result.buyHold)}。`;
    navChart.setOption({
      animation: false,
      tooltip: { trigger: "axis" }, legend: { top: 0 },
      grid: [{ left: 54, right: 28, top: 52, height: "52%" }, { left: 54, right: 28, top: "73%", height: "17%" }],
      xAxis: [{ type: "category", data: result.dates, boundaryGap: false, axisLabel: { show: false } }, { type: "category", data: result.dates, boundaryGap: false, gridIndex: 1 }],
      yAxis: [{ type: "value", name: "累计净值", scale: true }, { type: "value", name: "回撤", gridIndex: 1, axisLabel: { formatter: (v) => `${(v * 100).toFixed(0)}%` } }],
      dataZoom: [{ type: "inside", xAxisIndex: [0, 1], start: 0, end: 100 }],
      series: [
        { name: "策略净值", type: "line", data: result.nav, showSymbol: false, lineStyle: { width: 2.2, color: "#2f5597" } },
        { name: "买入持有", type: "line", data: result.benchmark, showSymbol: false, lineStyle: { width: 1.4, type: "dashed", color: "#647284" } },
        { name: "回撤", type: "line", xAxisIndex: 1, yAxisIndex: 1, data: result.drawdown, showSymbol: false, areaStyle: { color: "rgba(178,58,72,.42)" }, lineStyle: { color: "#b23a48" } }
      ]
    }, true);
  }

  function renderComparison() {
    const names = companies.map((item) => item.name);
    const labels = periods.map((item) => `${item[0]}/${item[1]}`);
    const values = [];
    companies.forEach((company, y) => periods.forEach((period, x) => {
      const row = comparisonRows.find((item) => item["公司"] === company.name && item["周期"] === `${period[0]}/${period[1]}`);
      values.push([x, y, +(Number(row["累计回报"]) * 100).toFixed(2)]);
    }));
    comparisonChart.setOption({
      tooltip: { formatter: (p) => `${names[p.value[1]]} MA${labels[p.value[0]]}<br>累计回报：${p.value[2]}%` },
      grid: { left: 90, right: 70, top: 28, bottom: 52 },
      xAxis: { type: "category", data: labels, name: "短/长均线周期" },
      yAxis: { type: "category", data: names },
      visualMap: { min: -43, max: 36, calculable: true, orient: "vertical", right: 4, top: "middle", inRange: { color: ["#b23a48", "#f4c36c", "#eaf4e8", "#2f7d5c"] } },
      series: [{ type: "heatmap", data: values, label: { show: true, formatter: (p) => `${p.value[2]}%` } }]
    }, true);

    document.getElementById("comparisonTable").innerHTML = `
      <thead><tr><th>公司</th><th>周期</th><th>累计回报</th><th>最大回撤</th><th>夏普比率</th><th>交易次数</th></tr></thead>
      <tbody>${comparisonRows.map((row) => `<tr><td>${row["公司"]}</td><td>${row["周期"]}</td><td class="${Number(row["累计回报"]) >= 0 ? "positive" : "negative"}">${signedPct(row["累计回报"])}</td><td>${pct(row["最大回撤"])}</td><td>${Number(row["夏普比率"]).toFixed(2)}</td><td>${row["交易次数"]}</td></tr>`).join("")}</tbody>
    `;
  }

  function renderAll() {
    renderControls();
    const company = companies[activeCompany];
    const period = periods[activePeriod];
    const result = backtest(priceSets[activeCompany], period[0], period[1]);
    renderMetrics(result, company, period);
    renderSignalChart(result, company, period);
    renderNavChart(result, company, period);
    setTimeout(() => charts.forEach((chart) => chart.resize()), 80);
  }

  async function init() {
    try {
      const priceResponses = await Promise.all(companies.map((item) => fetch(`assets/${item.code}_daily.csv`).then((response) => response.text())));
      priceSets = priceResponses.map(parseCsv);
      const comparisonText = await fetch("TASK3/results/all_stocks_period_comparison.csv").then((response) => response.text());
      comparisonRows = parseCsv(comparisonText);
      renderComparison();
      renderAll();
    } catch (error) {
      document.getElementById("task3MetricGrid").innerHTML = `<article class="metric-card"><h3>数据加载失败</h3><p>请通过网站服务器访问页面后重试。</p></article>`;
    }
  }

  window.addEventListener("resize", () => charts.forEach((chart) => chart.resize()));
  init();
})();
