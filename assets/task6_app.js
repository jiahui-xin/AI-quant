(function () {
  "use strict";
  const cumulativeChart = echarts.init(document.getElementById("cumulativeChart"));
  const ewpwChart = echarts.init(document.getElementById("ewpwChart"));
  const charts = [cumulativeChart, ewpwChart];

  // 实测结果（由 task6_ml_stock_selection.py 生成，random_state=42）
  const TEST_DATES = ["2021/9/30", "2021/12/31", "2022/3/31", "2022/6/30"];
  const results = {
    Market:                    [-0.0546, 0.0211, 0.0320, -0.0635],
    LinearRegression_EW:        [0.0408, -0.0459, 0.1163, 0.0193],
    LinearRegression_PW:        [0.0408, -0.0459, 0.1163, 0.0193],
    LogisticRegression_EW:      [0.0439, -0.0476, 0.1875, 0.0120],
    LogisticRegression_PW:      [0.0439, -0.0476, 0.1875, 0.0120],
    DecisionTree_EW:           [-0.0010,  0.0034,  0.0411, -0.0541],
    DecisionTree_PW:           [-0.0010,  0.0034,  0.0411, -0.0541],
    RandomForest_EW:           [0.0530, -0.0531, 0.0972,  0.0193],
    RandomForest_PW:           [0.0683, -0.0531, 0.1085,  0.0038],
  };
  const metrics = [
    { model: "Market",            weight: "--",     ret: -0.0635, ann: -0.0514, vol: 0.1669, sharpe: -0.3079, dd: -0.1591, ir: 0,      win: 0.00 },
    { model: "LinearRegression",  weight: "EW",     ret:  0.1362, ann:  0.1451, vol: 0.1818, sharpe:  0.7982, dd: -0.0542, ir: 1.1270, win: 0.75 },
    { model: "LinearRegression",  weight: "PW",     ret:  0.1357, ann:  0.1448, vol: 0.1831, sharpe:  0.7910, dd: -0.0524, ir: 1.1283, win: 0.75 },
    { model: "LogisticRegression",weight: "EW",     ret:  0.2014, ann:  0.2007, vol: 0.1687, sharpe:  1.1901, dd: -0.0322, ir: 1.3310, win: 0.75 },
    { model: "LogisticRegression",weight: "PW",     ret:  0.1989, ann:  0.1987, vol: 0.1698, sharpe:  1.1704, dd: -0.0321, ir: 1.3198, win: 0.75 },
    { model: "DecisionTree",      weight: "EW",     ret: -0.0121, ann: -0.0008, vol: 0.1511, sharpe: -0.0052, dd: -0.1003, ir: 0.3619, win: 0.50 },
    { model: "DecisionTree",      weight: "PW",     ret: -0.0119, ann: -0.0006, vol: 0.1503, sharpe: -0.0043, dd: -0.1010, ir: 0.3574, win: 0.50 },
    { model: "RandomForest",      weight: "EW",     ret:  0.1186, ann:  0.1233, vol: 0.1407, sharpe:  0.8762, dd: -0.0555, ir: 2.2106, win: 0.75 },
    { model: "RandomForest",      weight: "PW",     ret:  0.1293, ann:  0.1330, vol: 0.1401, sharpe:  0.9497, dd: -0.0495, ir: 2.5869, win: 0.75 },
  ];

  const fmt4 = v => (+v).toFixed(4);
  const fmtPct = v => `${(+(v) * 100).toFixed(2)}%`;

  function metricsCards() {
    const best = metrics.filter(m => m.weight === "EW").sort((a, b) => b.sharpe - a.sharpe)[0];
    const items = [
      ["最佳模型（EW）", best.model, "按夏普比率排序"],
      ["最佳累计收益", fmtPct(best.ret), best.model + "-" + best.weight],
      ["最佳夏普比率", fmt4(best.sharpe), "vs 市场基准 -0.31"],
      ["超额胜率", fmtPct(best.win), "4 季度中超越基准的比例"],
      ["组合规模", "Top 30", "每季度按预测分排序"],
      ["测试期间", "2021Q3–2022Q2", "4 个季度"],
    ];
    document.getElementById("task6MetricGrid").innerHTML = items.map(([k, v, note]) => `
      <article class="metric-card">
        <div class="metric-top"><h3>${k}</h3><span class="badge">${v}</span></div>
        <div class="report-meta">${note}</div>
      </article>`).join("");
  }

  function cumulativeReturns() {
    const series = Object.entries(results).map(([name, rets]) => {
      const nav = [];
      let acc = 1;
      rets.forEach(r => { acc *= (1 + r); nav.push(acc); });
      let color = "#888";
      let ls = "--";
      if (name === "Market") { color = "#888"; ls = "--"; }
      else {
        const [m, w] = name.split("_");
        const palette = { LinearRegression: "#378ADD", LogisticRegression: "#534AB7", DecisionTree: "#0F6E56", RandomForest: "#993C1D" };
        color = palette[m] || "#444";
        ls = w === "EW" ? "-" : ":";
      }
      return { name, type: "line", data: nav, showSymbol: true, symbolSize: 6, lineStyle: { color, width: 1.8, type: ls }, itemStyle: { color } };
    });
    cumulativeChart.setOption({
      animation: false,
      tooltip: { trigger: "axis" },
      legend: { top: 0, type: "scroll", textStyle: { fontSize: 9 } },
      grid: { left: 50, right: 24, top: 50, bottom: 40 },
      xAxis: { type: "category", data: TEST_DATES.map(d => d.replace("/", "\n")) },
      yAxis: { type: "value", name: "累计净值" },
      series,
    }, true);
  }

  function ewpwCompare() {
    const models = ["LinearRegression", "LogisticRegression", "DecisionTree", "RandomForest"];
    const ew = metrics.filter(m => m.weight === "EW" && models.includes(m.model));
    const pw = metrics.filter(m => m.weight === "PW" && models.includes(m.model));
    const market = metrics.find(m => m.model === "Market");
    ewpwChart.setOption({
      animation: false,
      tooltip: { trigger: "axis" },
      legend: { top: 0 },
      grid: [
        { left: 50, right: "55%", top: 40, height: "70%" },
        { left: "50%", right: 24, top: 40, height: "70%" },
      ],
      xAxis: [
        { type: "category", data: models, gridIndex: 0, axisLabel: { fontSize: 9 } },
        { type: "category", data: models, gridIndex: 1, axisLabel: { fontSize: 9 } },
      ],
      yAxis: [
        { type: "value", name: "累计收益", gridIndex: 0, axisLabel: { formatter: v => `${(v * 100).toFixed(0)}%` } },
        { type: "value", name: "夏普比率", gridIndex: 1 },
      ],
      series: [
        { name: "EW 等权", type: "bar", data: ew.map(m => m.ret), xAxisIndex: 0, yAxisIndex: 0, itemStyle: { color: "#378ADD" }, label: { show: true, position: "top", formatter: p => `${(p.value * 100).toFixed(1)}%`, fontSize: 9 } },
        { name: "PW 预测加权", type: "bar", data: pw.map(m => m.ret), xAxisIndex: 0, yAxisIndex: 0, itemStyle: { color: "#534AB7" }, label: { show: true, position: "top", formatter: p => `${(p.value * 100).toFixed(1)}%`, fontSize: 9 } },
        { name: "EW 等权", type: "bar", data: ew.map(m => m.sharpe), xAxisIndex: 1, yAxisIndex: 1, itemStyle: { color: "#0F6E56" }, label: { show: true, position: "top", formatter: p => (+p.value).toFixed(2), fontSize: 9 } },
        { name: "PW 预测加权", type: "bar", data: pw.map(m => m.sharpe), xAxisIndex: 1, yAxisIndex: 1, itemStyle: { color: "#993C1D" }, label: { show: true, position: "top", formatter: p => (+p.value).toFixed(2), fontSize: 9 } },
        { name: "市场基准", type: "line", data: models.map(() => market.ret), xAxisIndex: 0, yAxisIndex: 0, markLine: { silent: true, lineStyle: { color: "#888", type: "dashed" }, data: [{ yAxis: market.ret, label: { formatter: `市场 ${(market.ret * 100).toFixed(1)}%` } }] } },
        { name: "市场基准", type: "line", data: models.map(() => market.sharpe), xAxisIndex: 1, yAxisIndex: 1, markLine: { silent: true, lineStyle: { color: "#888", type: "dashed" }, data: [{ yAxis: market.sharpe, label: { formatter: `市场 ${market.sharpe.toFixed(2)}` } }] } },
      ],
    }, true);
  }

  function performanceTable() {
    document.getElementById("performanceTable").innerHTML = `
      <thead><tr>
        <th>模型</th><th>权重</th><th>累计收益</th><th>年化收益</th>
        <th>波动率</th><th>夏普</th><th>最大回撤</th><th>信息比率</th><th>超额胜率</th>
      </tr></thead>
      <tbody>${metrics.map(m => `<tr${m.model === "Market" ? ' class="market-row"' : ""}>
        <td>${m.model}</td><td>${m.weight}</td>
        <td class="${m.ret >= 0 ? "positive" : "negative"}">${fmtPct(m.ret)}</td>
        <td class="${m.ann >= 0 ? "positive" : "negative"}">${fmtPct(m.ann)}</td>
        <td>${fmtPct(m.vol)}</td>
        <td>${fmt4(m.sharpe)}</td>
        <td class="negative">${fmtPct(m.dd)}</td>
        <td>${fmt4(m.ir)}</td>
        <td>${fmtPct(m.win)}</td>
      </tr>`).join("")}</tbody>`;
  }

  function render() {
    metricsCards();
    cumulativeReturns();
    ewpwCompare();
    performanceTable();
    setTimeout(() => charts.forEach(x => x.resize()), 60);
  }

  window.addEventListener("resize", () => charts.forEach(x => x.resize()));
  render();
})();
