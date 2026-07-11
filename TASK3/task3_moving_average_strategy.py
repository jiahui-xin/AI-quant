#!/usr/bin/env python3
"""TASK3: 双均线策略回测、可视化与 PDF 报告生成。"""

from pathlib import Path
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether,
                                PageTemplate, PageBreak, Paragraph, Spacer,
                                Table, TableStyle)

ROOT = Path(__file__).resolve().parents[1]
TASK_DIR = ROOT / "TASK3"
DATA_DIR = ROOT / "assets"
FIG_DIR = TASK_DIR / "figures"
RESULT_DIR = TASK_DIR / "results"
PDF_PATH = TASK_DIR / "辛家辉TASK3.pdf"
FONT_PATH = Path("/Users/jiahuixin/Library/Fonts/SimSun.ttf")
COMPANIES = {
    "600276_SH": "恒瑞医药",
    "688235_SH": "百济神州",
    "688180_SH": "君实生物",
    "600196_SH": "复星医药",
}
PERIODS = [(3, 10), (5, 15), (10, 30), (20, 60)]
TRADING_DAYS = 252
FEE = 0.001


def load_price(code: str) -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / f"{code}_daily.csv", encoding="utf-8-sig")
    df["trade_date"] = pd.to_datetime(df["trade_date"].astype(str), format="%Y%m%d")
    return df.sort_values("trade_date").reset_index(drop=True)


def backtest(raw: pd.DataFrame, short: int, long: int, fee: float = FEE):
    df = raw.copy()
    df["ma_short"] = df["close"].rolling(short).mean()
    df["ma_long"] = df["close"].rolling(long).mean()
    df["signal"] = (df["ma_short"] > df["ma_long"]).astype(int)
    df.loc[df["ma_long"].isna(), "signal"] = 0
    df["trade"] = df["signal"].diff().fillna(df["signal"])
    df["position"] = df["signal"].shift(1).fillna(0)  # 次日生效，避免前视偏差
    df["market_return"] = df["close"].pct_change().fillna(0)
    turnover = df["position"].diff().abs().fillna(df["position"].abs())
    df["strategy_return"] = df["position"] * df["market_return"] - fee * turnover
    df["strategy_nav"] = (1 + df["strategy_return"]).cumprod()
    df["buy_hold_nav"] = (1 + df["market_return"]).cumprod()
    df["drawdown"] = df["strategy_nav"] / df["strategy_nav"].cummax() - 1
    ret = df["strategy_return"]
    cumulative = df["strategy_nav"].iloc[-1] - 1
    sharpe = math.sqrt(TRADING_DAYS) * ret.mean() / ret.std(ddof=1) if ret.std(ddof=1) else np.nan
    mdd = df["drawdown"].min()
    metrics = {
        "累计回报": cumulative,
        "最大回撤": mdd,
        "夏普比率": sharpe,
        "交易次数": int((df["trade"] != 0).sum()),
        "买入持有": df["buy_hold_nav"].iloc[-1] - 1,
    }
    return df, metrics


def setup_plot_font():
    matplotlib.font_manager.fontManager.addfont(str(FONT_PATH))
    plt.rcParams.update({
        "font.family": "SimSun", "axes.unicode_minus": False,
        "figure.dpi": 150, "savefig.dpi": 220,
    })


def plot_signals(df: pd.DataFrame, company: str, out: Path):
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    ax.plot(df.trade_date, df.close, color="#263238", lw=1.25, label="收盘价")
    ax.plot(df.trade_date, df.ma_short, color="#ef6c00", lw=1.2, label="MA5")
    ax.plot(df.trade_date, df.ma_long, color="#1565c0", lw=1.2, label="MA15")
    buys, sells = df[df.trade == 1], df[df.trade == -1]
    ax.scatter(buys.trade_date, buys.close, marker="^", s=54, color="#2e7d32", label="买入（金叉）", zorder=4)
    ax.scatter(sells.trade_date, sells.close, marker="v", s=54, color="#c62828", label="卖出（死叉）", zorder=4)
    ax.set_title(f"{company}：收盘价、双均线与交易信号")
    ax.set_ylabel("价格（元）")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.grid(alpha=.2)
    ax.legend(ncol=5, fontsize=8, loc="upper center")
    fig.autofmt_xdate(rotation=20)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def plot_nav(df: pd.DataFrame, company: str, out: Path):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.2, 5.6), sharex=True, gridspec_kw={"height_ratios": [2.1, 1]})
    ax1.plot(df.trade_date, df.strategy_nav, color="#1565c0", lw=1.5, label="MA5/15 策略净值")
    ax1.plot(df.trade_date, df.buy_hold_nav, color="#757575", lw=1.1, ls="--", label="买入并持有")
    ax1.axhline(1, color="#bdbdbd", lw=.8)
    ax1.set_ylabel("累计净值")
    ax1.set_title(f"{company}：策略净值与回撤")
    ax1.grid(alpha=.2); ax1.legend()
    ax2.fill_between(df.trade_date, df.drawdown * 100, 0, color="#c62828", alpha=.55)
    ax2.set_ylabel("回撤（%）"); ax2.set_xlabel("交易日期"); ax2.grid(alpha=.2)
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate(rotation=20)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def plot_heatmap(results: pd.DataFrame, out: Path):
    pivot = results.pivot(index="公司", columns="周期", values="累计回报") * 100
    pivot = pivot.reindex(list(COMPANIES.values()))
    fig, ax = plt.subplots(figsize=(8.8, 3.8))
    im = ax.imshow(pivot.values, cmap="RdYlGn", aspect="auto")
    ax.set_xticks(range(len(pivot.columns)), pivot.columns)
    ax.set_yticks(range(len(pivot.index)), pivot.index)
    ax.set_xlabel("短/长均线周期"); ax.set_title("不同股票与均线周期的策略累计回报（%）")
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            ax.text(j, i, f"{pivot.iloc[i, j]:.1f}%", ha="center", va="center", fontsize=9)
    fig.colorbar(im, ax=ax, shrink=.8, label="累计回报（%）")
    fig.tight_layout(); fig.savefig(out, bbox_inches="tight"); plt.close(fig)


def pct(x): return f"{x:.2%}"
def num(x): return f"{x:.2f}"


def build_report(primary: pd.DataFrame, primary_metrics: dict, comparisons: pd.DataFrame):
    pdfmetrics.registerFont(TTFont("SimSun", str(FONT_PATH)))
    styles = getSampleStyleSheet()
    body = ParagraphStyle("BodyCN", parent=styles["BodyText"], fontName="SimSun", fontSize=10.5,
                          leading=15.75, alignment=TA_JUSTIFY, spaceBefore=0, spaceAfter=0,
                          firstLineIndent=21)
    h1 = ParagraphStyle("H1CN", parent=body, fontSize=14, leading=21, spaceBefore=10, spaceAfter=5,
                        firstLineIndent=0, textColor=colors.HexColor("#17365D"))
    h2 = ParagraphStyle("H2CN", parent=body, fontSize=11.5, leading=17, spaceBefore=6, spaceAfter=3,
                        firstLineIndent=0, textColor=colors.HexColor("#244A73"))
    title = ParagraphStyle("TitleCN", parent=body, fontSize=18, leading=27, alignment=TA_CENTER,
                           firstLineIndent=0, spaceAfter=10)
    center = ParagraphStyle("CenterCN", parent=body, alignment=TA_CENTER, firstLineIndent=0)
    caption = ParagraphStyle("CaptionCN", parent=body, fontSize=10.5, leading=15.75,
                             alignment=TA_CENTER, firstLineIndent=0, spaceBefore=2, spaceAfter=3)
    small = ParagraphStyle("SmallCN", parent=body, fontSize=9, leading=13.5, firstLineIndent=0)

    class NumberedDoc(BaseDocTemplate):
        pass
    doc = NumberedDoc(str(PDF_PATH), pagesize=A4, leftMargin=24*mm, rightMargin=24*mm,
                      topMargin=19*mm, bottomMargin=18*mm, title="辛家辉TASK3", author="辛家辉")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    def footer(canvas, _doc):
        canvas.saveState(); canvas.setFont("SimSun", 9)
        canvas.drawCentredString(A4[0]/2, 10*mm, f"- {canvas.getPageNumber()} -"); canvas.restoreState()
    doc.addPageTemplates(PageTemplate(id="main", frames=frame, onPage=footer))

    story = [Spacer(1, 12*mm), Paragraph("TASK3 策略首秀：用均线交叉反映市场趋势变化", title),
             Spacer(1, 4*mm), Paragraph("姓名：辛家辉", center), Paragraph("日期：2026年7月11日", center),
             Spacer(1, 10*mm), Paragraph("摘要", h1),
             Paragraph("本文基于 TASK1 已保存的四只创新药股票日线数据，实现经典双均线择时策略。以恒瑞医药（600276.SH）的 5 日/15 日简单移动平均线为主案例，按照“当日收盘确认信号、下一交易日持仓生效”的规则进行回测，并计入单边 0.10% 交易成本。策略评价采用累计回报、最大回撤和年化夏普比率，同时比较四只股票及四组均线周期。结果表明，双均线策略能够把价格波动转换为清晰、可复现的趋势信号，但收益对标的、参数和样本区间较敏感，不宜把单次样本中的最优参数直接视为未来最优参数。", body),
             Paragraph("关键词：双均线；金叉；死叉；回测；最大回撤；夏普比率", body),
             Paragraph("一、策略原理与基本概念", h1),
             Paragraph("双均线策略同时计算短期均线和长期均线。短期均线对新价格反应较快，长期均线更平滑，用于刻画中期趋势。当短期均线由下向上穿越长期均线时形成“金叉”，通常解释为近期价格动能转强，策略由空仓转为持有；当短期均线由上向下穿越长期均线时形成“死叉”，通常解释为趋势转弱，策略卖出并回到空仓。本作业只做多、不做空。", body),
             Paragraph("简单移动平均线可写为 MA(n)<sub>t</sub> = (P<sub>t</sub> + … + P<sub>t-n+1</sub>)/n，其中 P<sub>t</sub> 为第 t 个交易日收盘价。均线本质上是滞后指标：平滑能够过滤部分短期噪声，但也会使入场和离场晚于价格拐点。", body),
             Paragraph("二、策略评价指标", h1),
             Paragraph("累计回报（Cumulative Return）表示整个回测期内资金的总增值比例，即期末净值减 1。它直观反映最终盈亏，但不能单独说明实现该回报时承担了多大风险。", body),
             Paragraph("最大回撤（Maximum Drawdown, MDD）是净值从历史峰值到随后谷值的最大跌幅。本文按 MDD = min(V<sub>t</sub>/max<sub>s≤t</sub>V<sub>s</sub> - 1) 计算；数值越负，表示历史最坏亏损越大。", body),
             Paragraph("夏普比率（Sharpe Ratio）衡量单位波动对应的超额收益。由于样本为日频且回测期较短，本文将无风险日收益近似设为 0，按 √252 × 日策略收益均值 / 日策略收益标准差进行年化。夏普比率越高通常越好，但它对样本长度、收益分布和无风险利率设定敏感。", body),
             Paragraph("三、数据与 Python 实现", h1),
             Paragraph(f"数据读取自 assets 目录中的日线 CSV，覆盖 {primary.trade_date.min():%Y-%m-%d} 至 {primary.trade_date.max():%Y-%m-%d}，共 {len(primary)} 个交易日。主案例设置短均线为 5 日、长均线为 15 日。计算步骤为：读取并按日期升序排序；滚动计算 MA5 与 MA15；比较两条均线生成持有信号；由信号变化识别买卖点；将信号滞后一天形成实际持仓；扣除换仓成本；最后由日收益序列计算净值和风险指标。", body),
             Paragraph("关键实现如下（完整代码与结果 CSV 随报告保存在 TASK3 目录）：", body),
             Table([[Paragraph("df['ma_short'] = df['close'].rolling(5).mean()<br/>df['ma_long'] = df['close'].rolling(15).mean()<br/>df['signal'] = (df['ma_short'] &gt; df['ma_long']).astype(int)<br/>df['position'] = df['signal'].shift(1).fillna(0)<br/>turnover = df['position'].diff().abs().fillna(0)<br/>df['strategy_return'] = df['position'] * df['close'].pct_change().fillna(0) - 0.001 * turnover<br/>df['strategy_nav'] = (1 + df['strategy_return']).cumprod()", small)]], colWidths=[doc.width], style=TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#F3F6F8")),("BOX",(0,0),(-1,-1),.5,colors.HexColor("#AAB7C4")),("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)])),
             Paragraph("四、主案例回测结果：恒瑞医药 MA5/15", h1),
             KeepTogether([Image(str(FIG_DIR/"figure1_signals.png"), width=doc.width, height=doc.width*0.50), Paragraph("图1 恒瑞医药收盘价、长短均线与买卖信号", caption)]),
             Paragraph("图1中，绿色向上三角表示短均线上穿长均线后的买入信号，红色向下三角表示短均线下穿长均线后的卖出信号。信号主要出现在趋势方向发生持续变化的位置；当价格横盘震荡时，两条均线距离较近，容易反复交叉并产生交易成本。图中买卖标记用于展示信号确认日，实际持仓收益从下一交易日开始计算。", body),
             PageBreak(),
             KeepTogether([Image(str(FIG_DIR/"figure2_nav_drawdown.png"), width=doc.width, height=doc.width*0.61), Paragraph("图2 恒瑞医药 MA5/15 策略净值与回撤", caption)]),
             Paragraph("图2上半部分对比策略净值与买入持有净值，下半部分显示策略从历史净值高点的回撤。净值曲线用来观察收益累积路径，回撤曲线则揭示仅看期末收益容易忽略的中途亏损压力。", body)]

    metric_data = [["指标", "MA5/15 策略", "解释"],
                   ["累计回报", pct(primary_metrics["累计回报"]), "扣除交易成本后的期末收益"],
                   ["最大回撤", pct(primary_metrics["最大回撤"]), "样本期内最严重的峰谷损失"],
                   ["年化夏普比率", num(primary_metrics["夏普比率"]), "无风险日收益近似为 0"],
                   ["交易次数", str(primary_metrics["交易次数"]), "买入与卖出信号合计"],
                   ["同期买入持有", pct(primary_metrics["买入持有"]), "不择时的基准收益"]]
    t = Table(metric_data, colWidths=[34*mm, 34*mm, doc.width-68*mm], repeatRows=1)
    t.setStyle(TableStyle([("FONTNAME",(0,0),(-1,-1),"SimSun"),("FONTSIZE",(0,0),(-1,-1),9.5),("LEADING",(0,0),(-1,-1),14),("BACKGROUND",(0,0),(-1,0),colors.HexColor("#D9EAF7")),("GRID",(0,0),(-1,-1),.4,colors.HexColor("#8FA4B5")),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("ALIGN",(0,0),(1,-1),"CENTER"),("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    story += [Spacer(1, 2*mm), Paragraph("表1 恒瑞医药 MA5/15 策略绩效", caption), t,
              Paragraph(f"表1显示，策略累计回报为 {pct(primary_metrics['累计回报'])}，最大回撤为 {pct(primary_metrics['最大回撤'])}，年化夏普比率为 {num(primary_metrics['夏普比率'])}。同期买入持有收益为 {pct(primary_metrics['买入持有'])}。这些结果只描述当前样本，不构成未来收益保证；尤其是约一年的观察期较短，夏普比率和最优周期都可能随样本延长而明显变化。", body),
              Paragraph("五、跨股票与跨周期比较", h1)]

    show = comparisons.copy()
    show["累计回报"] = show["累计回报"].map(pct); show["最大回撤"] = show["最大回撤"].map(pct)
    show["夏普比率"] = show["夏普比率"].map(num)
    rows = [["公司", "周期", "累计回报", "最大回撤", "夏普", "交易次数"]] + show[["公司","周期","累计回报","最大回撤","夏普比率","交易次数"]].values.tolist()
    comp_table = Table(rows, colWidths=[26*mm,19*mm,28*mm,28*mm,22*mm,24*mm], repeatRows=1)
    comp_table.setStyle(TableStyle([("FONTNAME",(0,0),(-1,-1),"SimSun"),("FONTSIZE",(0,0),(-1,-1),8.5),("LEADING",(0,0),(-1,-1),12),("BACKGROUND",(0,0),(-1,0),colors.HexColor("#D9EAF7")),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F6F8FA")]),("GRID",(0,0),(-1,-1),.35,colors.HexColor("#9EADB8")),("ALIGN",(1,0),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3)]))
    best = comparisons.loc[comparisons.groupby("公司")["累计回报"].idxmax(), ["公司","周期","累计回报"]]
    best_text = "；".join(f"{r.公司}在本样本中最高为 {r.周期}（{pct(r.累计回报)}）" for r in best.itertuples())
    story += [Paragraph("表2 不同股票与均线周期的回测比较", caption), comp_table,
              Spacer(1, 4*mm), KeepTogether([Image(str(FIG_DIR/"figure3_period_heatmap.png"), width=doc.width, height=doc.width*0.43), Paragraph("图3 不同股票与均线周期的累计回报比较", caption)]),
              Paragraph(f"图3与表2说明参数表现并不稳定：{best_text}。同一周期在不同股票上的结果可能相反，同一股票的结果也会随周期改变。较短周期反应快，但更易受噪声影响并增加换手；较长周期能过滤部分震荡，却可能错过快速反转。这里的比较用于观察敏感性，而不是在同一样本中挑选“冠军参数”后宣称其具有样本外优势。", body),
              Paragraph("六、适用场景、局限与应用心得", h1),
              Paragraph("双均线策略更适合方向持续、趋势较清晰的市场。当上涨或下跌能够延续若干交易日时，均线交叉有机会让策略参与主要趋势，并在趋势转弱后退出。它也适合用作基础择时模块：规则透明、参数少、容易复现，便于进一步加入止损、仓位控制、成交量过滤或多资产配置。", body),
              Paragraph("该策略不适合频繁来回波动的窄幅震荡市场。此时短长均线会反复交叉，形成“假突破”和连续小额亏损。均线还存在天然滞后，极端行情中可能在下跌开始一段时间后才卖出。回测结果还受到复权方式、成交价格、停牌与涨跌停可交易性、手续费和滑点等假设影响；本作业使用收盘价并只模拟基础成本，尚未完整复刻真实订单执行。", body),
              Paragraph("本次实践的核心体会是：交易信号的可视化只是第一步，策略评价必须同时观察收益、风险和交易频率；参数比较也不能只看最高累计回报。更稳健的后续方法应将数据划分为训练期和测试期，采用滚动样本外检验，并在更多股票和更长区间上考察参数稳定性。", body),
              Paragraph("七、结论", h1),
              Paragraph("本文完成了从已存股价数据加载、均线计算、金叉与死叉识别、图形展示，到模拟交易、绩效计算和参数敏感性分析的完整流程。双均线策略能够简洁地反映趋势变化，但并不存在对所有股票和市场阶段都占优的固定周期。实际应用中，应把它视为可解释的趋势跟随基线，并通过样本外验证、交易成本建模和风险控制提高可信度。", body),
              Paragraph("参考资料", h1),
              Paragraph("[1] Brock, W., Lakonishok, J., &amp; LeBaron, B. (1992). Simple Technical Trading Rules and the Stochastic Properties of Stock Returns. Journal of Finance, 47(5), 1731-1764.<br/>[2] Sharpe, W. F. (1994). The Sharpe Ratio. Journal of Portfolio Management, 21(1), 49-58.<br/>[3] pandas documentation: rolling window calculations and percentage change methods.", small)]
    doc.build(story)


def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True); RESULT_DIR.mkdir(parents=True, exist_ok=True)
    setup_plot_font()
    all_rows = []
    primary_df = primary_metrics = None
    for code, company in COMPANIES.items():
        raw = load_price(code)
        for short, long in PERIODS:
            bt, metrics = backtest(raw, short, long)
            all_rows.append({"公司": company, "代码": code.replace("_", "."), "周期": f"{short}/{long}", **metrics})
            if code == "600276_SH" and (short, long) == (5, 15):
                primary_df, primary_metrics = bt, metrics
                bt.to_csv(RESULT_DIR / "600276_SH_MA5_15_backtest.csv", index=False, encoding="utf-8-sig")
    comparisons = pd.DataFrame(all_rows)
    comparisons.to_csv(RESULT_DIR / "all_stocks_period_comparison.csv", index=False, encoding="utf-8-sig")
    plot_signals(primary_df, "恒瑞医药", FIG_DIR / "figure1_signals.png")
    plot_nav(primary_df, "恒瑞医药", FIG_DIR / "figure2_nav_drawdown.png")
    plot_heatmap(comparisons, FIG_DIR / "figure3_period_heatmap.png")
    build_report(primary_df, primary_metrics, comparisons)
    print(comparisons.to_string(index=False))
    print(f"\nGenerated: {PDF_PATH}")


if __name__ == "__main__":
    main()
