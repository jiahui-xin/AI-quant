(function () {
  const data = window.PHARMA_DATA;
  const companies = data.companies;
  const colors = ["#006d77", "#b23a48", "#b7791f", "#2f5597"];
  const analysis = {
    "600276.SH": {
      buy: ["创新药收入占比提升，传统仿制药估值逻辑正在向研发平台逻辑切换。", "国内商业化网络成熟，利于新适应症和新产品快速放量。"],
      risk: ["创新药研发存在临床失败风险，集采和医保谈判仍可能压缩利润率。", "国际化进展需要持续验证，海外审批和商业化节奏可能波动。"]
    },
    "688235.SH": {
      buy: ["全球多中心临床和海外商业化能力突出，是中国创新药国际化代表。", "核心产品组合具备全球收入弹性，研发管线覆盖肿瘤多个方向。"],
      risk: ["持续研发投入较高，盈利释放节奏依赖核心产品商业化和费用控制。", "海外市场竞争强，产品差异化和适应症拓展需要持续验证。"]
    },
    "688180.SH": {
      buy: ["PD-1 出海注册打开样板意义，免疫肿瘤资产具备长期跟踪价值。", "公司在感染和自免方向扩展，有机会形成差异化研发组合。"],
      risk: ["单品依赖度仍需降低，后续管线兑现速度决定估值弹性。", "生物科技公司波动较大，融资环境和研发里程碑会影响市场预期。"]
    },
    "600196.SH": {
      buy: ["业务覆盖药品、疫苗、器械与全球化平台，抗单一产品周期能力较强。", "产业整合经验丰富，可通过外延和合作承接创新药机会。"],
      risk: ["业务结构较复杂，投资者需要拆分观察各板块盈利质量。", "高投入业务和外部合作项目可能带来费用波动与减值压力。"]
    }
  };

  function fmtDate(value) {
    return `${value.slice(0, 4)}-${value.slice(4, 6)}-${value.slice(6, 8)}`;
  }

  function cls(value) {
    return value >= 0 ? "positive" : "negative";
  }

  function signed(value) {
    return `${value > 0 ? "+" : ""}${Number(value).toFixed(2)}%`;
  }

  function movingAverage(series, days) {
    return series.map((_, index) => {
      if (index < days - 1) return null;
      const slice = series.slice(index - days + 1, index + 1);
      const avg = slice.reduce((sum, row) => sum + row.close, 0) / days;
      return +avg.toFixed(2);
    });
  }

  function calcRsi(series, days = 14) {
    if (series.length <= days) return 50;
    let gains = 0;
    let losses = 0;
    const recent = series.slice(-days - 1);
    for (let i = 1; i < recent.length; i += 1) {
      const diff = recent[i].close - recent[i - 1].close;
      if (diff >= 0) gains += diff;
      else losses -= diff;
    }
    if (losses === 0) return 100;
    const rs = gains / losses;
    return +(100 - 100 / (1 + rs)).toFixed(1);
  }

  function getCompany(code) {
    return companies.find((item) => item.code === code) || companies[0];
  }

  function renderMetrics() {
    const grid = document.getElementById("metricGrid");
    grid.innerHTML = companies.map((c, i) => `
      <article class="metric-card">
        <div class="metric-top">
          <div>
            <h3>${c.name}</h3>
            <div class="report-meta">${c.code}<br>${c.role}</div>
          </div>
          <span class="badge" style="background:${colors[i]}">${c.records}日</span>
        </div>
        <div class="metric-list">
          <div class="metric-line"><span>区间收益</span><strong class="${cls(c.returnPct)}">${signed(c.returnPct)}</strong></div>
          <div class="metric-line"><span>期末收盘</span><strong>${c.endClose.toFixed(2)}</strong></div>
          <div class="metric-line"><span>最大回撤</span><strong class="negative">${c.maxDrawdownPct.toFixed(2)}%</strong></div>
          <div class="metric-line"><span>日波动率</span><strong>${c.dailyVolPct.toFixed(2)}%</strong></div>
        </div>
      </article>
    `).join("");
  }

  function renderReports() {
    const grid = document.getElementById("reportGrid");
    grid.innerHTML = companies.map((c) => `
      <article class="report-card">
        <h3>${c.name} 近一年交易数据观察</h3>
        <div class="report-meta">
          生成时间：${data.generatedAt}<br>
          数据区间：${fmtDate(c.startDate)} 至 ${fmtDate(c.endDate)}<br>
          数据来源：${data.source}
        </div>
        <p>${c.theme} 样本期内收盘价区间为 ${c.lowClose.toFixed(2)} 至 ${c.highClose.toFixed(2)}，区间收益为 ${signed(c.returnPct)}，平均每日成交额约 ${c.avgTurnoverYi.toFixed(2)} 亿元。</p>
        <a class="csv-link" href="${c.csv}" download>下载 CSV 数据</a>
        <div class="tags">
          ${c.focus.split("、").map((tag) => `<span class="tag">${tag}</span>`).join("")}
        </div>
      </article>
    `).join("");
  }

  const klineChart = echarts.init(document.getElementById("klineChart"));
  const compareChart = echarts.init(document.getElementById("compareChart"));
  const detailChart = echarts.init(document.getElementById("detailChart"));

  function renderQuote(c) {
    const last = c.series[c.series.length - 1];
    const ma20 = movingAverage(c.series, 20).at(-1);
    const ma60 = movingAverage(c.series, 60).at(-1);
    const rsi = calcRsi(c.series);
    document.getElementById("quoteName").textContent = c.name;
    document.getElementById("quoteCode").textContent = c.code;
    document.getElementById("quotePrice").textContent = last.close.toFixed(2);
    const quoteReturn = document.getElementById("quoteReturn");
    quoteReturn.textContent = signed(c.returnPct);
    quoteReturn.className = cls(c.returnPct);
    document.getElementById("quoteTheme").textContent = c.theme;
    document.getElementById("quoteStats").innerHTML = `
      <div><span>样本交易日</span><strong>${c.records}</strong></div>
      <div><span>最新成交额</span><strong>${(last.amount / 100000).toFixed(2)}亿</strong></div>
      <div><span>MA20</span><strong>${ma20 ? ma20.toFixed(2) : "--"}</strong></div>
      <div><span>MA60</span><strong>${ma60 ? ma60.toFixed(2) : "--"}</strong></div>
    `;
    document.getElementById("techGrid").innerHTML = `
      <div><span>RSI(14)</span><strong>${rsi}</strong><em>${rsi > 70 ? "偏热" : rsi < 30 ? "偏冷" : "中性"}</em></div>
      <div><span>区间高点</span><strong>${c.highClose.toFixed(2)}</strong><em>收盘价</em></div>
      <div><span>区间低点</span><strong>${c.lowClose.toFixed(2)}</strong><em>收盘价</em></div>
      <div><span>最大回撤</span><strong class="negative">${c.maxDrawdownPct.toFixed(2)}%</strong><em>风险观察</em></div>
    `;
    const item = analysis[c.code];
    document.getElementById("analysisList").innerHTML = `
      <h4>看多逻辑</h4>
      ${item.buy.map((text) => `<p>${text}</p>`).join("")}
      <h4>风险提示</h4>
      ${item.risk.map((text) => `<p>${text}</p>`).join("")}
    `;
  }

  function renderKline(c) {
    const dates = c.series.map((row) => fmtDate(row.date));
    const values = c.series.map((row) => [row.open, row.close, row.low, row.high]);
    const ma5 = movingAverage(c.series, 5);
    const ma20 = movingAverage(c.series, 20);
    const ma60 = movingAverage(c.series, 60);
    document.getElementById("klineTitle").textContent = `图1 ${c.name} K线与均线`;
    document.getElementById("klineCaption").textContent = `${c.name}最近一年区间收益 ${signed(c.returnPct)}，日波动率 ${c.dailyVolPct.toFixed(2)}%。K线、均线和成交额应结合创新药研发里程碑共同判断。`;

    klineChart.setOption({
      animation: false,
      color: ["#006d77", "#b23a48", "#b7791f"],
      tooltip: { trigger: "axis", axisPointer: { type: "cross" } },
      legend: { top: 0, data: ["K线", "MA5", "MA20", "MA60"] },
      grid: [
        { left: 50, right: 24, top: 52, height: "58%" },
        { left: 50, right: 24, top: "76%", height: "14%" }
      ],
      xAxis: [
        { type: "category", data: dates, boundaryGap: true, axisLine: { lineStyle: { color: "#9aa7b4" } } },
        { type: "category", data: dates, gridIndex: 1, boundaryGap: true, axisLabel: { show: false } }
      ],
      yAxis: [
        { scale: true, splitLine: { lineStyle: { color: "#e7edf3" } } },
        { scale: true, gridIndex: 1, splitNumber: 2, axisLabel: { formatter: "{value}" } }
      ],
      dataZoom: [
        { type: "inside", xAxisIndex: [0, 1], start: 42, end: 100 },
        { show: true, xAxisIndex: [0, 1], type: "slider", bottom: 8, start: 42, end: 100, height: 18 }
      ],
      series: [
        { name: "K线", type: "candlestick", data: values, itemStyle: { color: "#c44e52", color0: "#2f9b72", borderColor: "#c44e52", borderColor0: "#2f9b72" } },
        { name: "MA5", type: "line", data: ma5, smooth: true, showSymbol: false, lineStyle: { width: 1.5 } },
        { name: "MA20", type: "line", data: ma20, smooth: true, showSymbol: false, lineStyle: { width: 1.5 } },
        { name: "MA60", type: "line", data: ma60, smooth: true, showSymbol: false, lineStyle: { width: 1.5 } },
        { name: "成交额", type: "bar", xAxisIndex: 1, yAxisIndex: 1, data: c.series.map((row) => +(row.amount / 100000).toFixed(2)), itemStyle: { color: "rgba(47,85,151,.38)" } }
      ]
    });
  }

  function renderCompare() {
    const dates = companies[0].series.map((row) => fmtDate(row.date));
    const series = companies.map((c, i) => {
      const base = c.series[0].close;
      return {
        name: c.name,
        type: "line",
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 2.4 },
        itemStyle: { color: colors[i] },
        data: c.series.map((row) => +(row.close / base * 100).toFixed(2))
      };
    });
    compareChart.setOption({
      color: colors,
      tooltip: { trigger: "axis" },
      legend: { top: 0 },
      grid: { left: 44, right: 24, top: 56, bottom: 44 },
      xAxis: { type: "category", data: dates, boundaryGap: false },
      yAxis: { type: "value", name: "期初=100", scale: true },
      series
    });
  }

  function renderDetail(c) {
    document.getElementById("detailTitle").textContent = `图3 ${c.name}每日收盘价与成交额`;
    document.getElementById("detailCaption").textContent = `${c.name}样本期区间收益为 ${signed(c.returnPct)}，最大回撤为 ${c.maxDrawdownPct.toFixed(2)}%，成交额变化可辅助观察资金关注度。`;

    detailChart.setOption({
      color: ["#006d77", "#b7791f"],
      tooltip: { trigger: "axis" },
      legend: { top: 0, data: ["收盘价", "成交额"] },
      grid: { left: 48, right: 58, top: 56, bottom: 48 },
      xAxis: { type: "category", data: c.series.map((row) => fmtDate(row.date)), boundaryGap: false },
      yAxis: [
        { type: "value", name: "收盘价", scale: true },
        { type: "value", name: "亿元", scale: true }
      ],
      series: [
        { name: "收盘价", type: "line", smooth: true, showSymbol: false, lineStyle: { width: 2.3 }, data: c.series.map((row) => row.close) },
        { name: "成交额", type: "bar", yAxisIndex: 1, barWidth: "55%", opacity: .36, data: c.series.map((row) => +(row.amount / 100000).toFixed(2)) }
      ]
    });
  }

  function setCompany(code) {
    const c = getCompany(code);
    document.querySelectorAll(".seg").forEach((item) => {
      item.classList.toggle("active", item.dataset.code === code);
    });
    renderQuote(c);
    renderKline(c);
    renderDetail(c);
  }

  function bindControls() {
    document.querySelectorAll(".seg").forEach((button) => {
      button.addEventListener("click", () => setCompany(button.dataset.code));
    });
  }

  renderMetrics();
  renderReports();
  renderCompare();
  bindControls();
  setCompany("600276.SH");

  function resizeCharts() {
    klineChart.resize();
    compareChart.resize();
    detailChart.resize();
  }

  window.addEventListener("resize", resizeCharts);
  if ("ResizeObserver" in window) {
    const observer = new ResizeObserver(resizeCharts);
    document.querySelectorAll(".chart").forEach((node) => observer.observe(node));
  }
  setTimeout(resizeCharts, 80);
  setTimeout(resizeCharts, 400);
})();
