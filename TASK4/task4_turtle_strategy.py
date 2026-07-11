#!/usr/bin/env python3
"""TASK4: 海龟交易法则回测、可视化与 PDF 作业报告生成。"""

from pathlib import Path
import json
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Frame, Image, KeepTogether, PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
TASK_DIR = ROOT / "TASK4"
FIG_DIR = TASK_DIR / "figures"
RESULT_DIR = TASK_DIR / "results"
ASSET_DIR = ROOT / "assets"
PDF_PATH = TASK_DIR / "辛家辉TASK4.pdf"
FONT_PATH = Path("/Users/jiahuixin/Library/Fonts/SimSun.ttf")
COMPANIES = {"600276_SH": "恒瑞医药", "688235_SH": "百济神州", "688180_SH": "君实生物", "600196_SH": "复星医药"}
CHANNELS = [(10, 5), (20, 10), (40, 20), (55, 20)]
ATR_PERIOD = 20
STOP_ATR = 2.0
COMMISSION = 0.0003
SLIPPAGE_IMPACT = 0.0001
TOTAL_COST = COMMISSION + SLIPPAGE_IMPACT


def load_price(code: str) -> pd.DataFrame:
    data = pd.read_csv(ASSET_DIR / f"{code}_daily.csv", encoding="utf-8-sig")
    data["trade_date"] = pd.to_datetime(data["trade_date"].astype(str), format="%Y%m%d")
    return data.sort_values("trade_date").reset_index(drop=True)


def add_turtle_indicators(raw: pd.DataFrame, entry: int, exit_: int, atr_period: int = ATR_PERIOD) -> pd.DataFrame:
    df = raw.copy()
    previous_close = df["close"].shift(1)
    tr = pd.concat([(df["high"] - df["low"]), (df["high"] - previous_close).abs(), (df["low"] - previous_close).abs()], axis=1).max(axis=1)
    df["tr"] = tr
    df["atr"] = tr.ewm(alpha=1 / atr_period, adjust=False, min_periods=atr_period).mean()
    # shift(1) 保证第 t 日看到的通道只包含第 t-1 日及更早数据。
    df["entry_high"] = df["high"].rolling(entry).max().shift(1)
    df["exit_low"] = df["low"].rolling(exit_).min().shift(1)
    return df


def backtest(raw: pd.DataFrame, entry: int = 20, exit_: int = 10, atr_period: int = ATR_PERIOD, stop_atr: float = STOP_ATR):
    df = add_turtle_indicators(raw, entry, exit_, atr_period)
    n = len(df)
    position = np.zeros(n)
    trade = np.zeros(n)
    stop_line = np.full(n, np.nan)
    reason = [""] * n
    active_stop = np.nan

    for t in range(1, n):
        previous_position = position[t - 1]
        previous = df.iloc[t - 1]
        target = previous_position
        action = ""
        if previous_position == 0:
            if pd.notna(previous.entry_high) and pd.notna(previous.atr) and previous.close > previous.entry_high:
                target = 1
                active_stop = float(df.iloc[t].open - stop_atr * previous.atr)
                action = "通道突破买入"
        else:
            channel_exit = pd.notna(previous.exit_low) and previous.close < previous.exit_low
            stop_exit = pd.notna(active_stop) and previous.close <= active_stop
            if stop_exit or channel_exit:
                target = 0
                action = "ATR止损卖出" if stop_exit else "退出通道卖出"
                active_stop = np.nan
        position[t] = target
        trade[t] = target - previous_position
        reason[t] = action
        if target == 1:
            stop_line[t] = active_stop

    df["position"] = position
    df["trade"] = trade
    df["trade_reason"] = reason
    df["stop_line"] = stop_line
    previous_position = df["position"].shift(1).fillna(0)
    overnight = (df["open"] / df["close"].shift(1) - 1).fillna(0)
    intraday = df["close"] / df["open"] - 1
    gross = (1 + previous_position * overnight) * (1 + df["position"] * intraday) - 1
    turnover = df["trade"].abs()
    df["market_return"] = df["close"].pct_change().fillna(0)
    df["strategy_return"] = gross - TOTAL_COST * turnover
    df["strategy_nav"] = (1 + df["strategy_return"]).cumprod()
    df["buy_hold_nav"] = (1 + df["market_return"]).cumprod()
    df["drawdown"] = df["strategy_nav"] / df["strategy_nav"].cummax() - 1
    ret = df["strategy_return"]
    std = ret.std(ddof=1)
    metrics = {
        "累计回报": df["strategy_nav"].iloc[-1] - 1,
        "最大回撤": df["drawdown"].min(),
        "夏普比率": math.sqrt(252) * ret.mean() / std if std else np.nan,
        "交易次数": int((df["trade"] != 0).sum()),
        "买入持有": df["buy_hold_nav"].iloc[-1] - 1,
    }
    return df, metrics


def setup_plot_font():
    matplotlib.font_manager.fontManager.addfont(str(FONT_PATH))
    plt.rcParams.update({"font.family": "SimSun", "axes.unicode_minus": False, "figure.dpi": 150, "savefig.dpi": 220})


def plot_channels(df: pd.DataFrame, out: Path):
    fig, ax = plt.subplots(figsize=(9.2, 4.8))
    ax.plot(df.trade_date, df.close, color="#263238", lw=1.2, label="收盘价")
    ax.plot(df.trade_date, df.entry_high, color="#2f5597", lw=1.15, label="20日入场上轨")
    ax.plot(df.trade_date, df.exit_low, color="#b7791f", lw=1.15, label="10日退出下轨")
    ax.plot(df.trade_date, df.stop_line, color="#b23a48", lw=1, ls="--", label="2ATR止损线")
    buys, sells = df[df.trade == 1], df[df.trade == -1]
    ax.scatter(buys.trade_date, buys.open, marker="^", s=58, color="#2f7d5c", label="开盘买入", zorder=5)
    ax.scatter(sells.trade_date, sells.open, marker="v", s=58, color="#b23a48", label="开盘卖出", zorder=5)
    ax.set_title("恒瑞医药：海龟通道、ATR止损与交易信号")
    ax.set_ylabel("价格（元）"); ax.grid(alpha=.2); ax.legend(ncol=3, fontsize=8, loc="upper center")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2)); ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate(rotation=20); fig.tight_layout(); fig.savefig(out, bbox_inches="tight"); plt.close(fig)


def plot_atr(df: pd.DataFrame, out: Path):
    fig, ax = plt.subplots(figsize=(9.2, 3.6))
    ax.plot(df.trade_date, df.atr, color="#006d77", lw=1.5)
    ax.fill_between(df.trade_date, df.atr, 0, color="#006d77", alpha=.18)
    ax.set_title("恒瑞医药：20日平均真实波幅（ATR）"); ax.set_ylabel("ATR（元）"); ax.grid(alpha=.2)
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2)); ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate(rotation=20); fig.tight_layout(); fig.savefig(out, bbox_inches="tight"); plt.close(fig)


def plot_nav(df: pd.DataFrame, out: Path):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.2, 5.5), sharex=True, gridspec_kw={"height_ratios": [2.1, 1]})
    ax1.plot(df.trade_date, df.strategy_nav, color="#2f5597", lw=1.6, label="海龟20/10策略")
    ax1.plot(df.trade_date, df.buy_hold_nav, color="#647284", lw=1.1, ls="--", label="买入持有")
    ax1.set_ylabel("累计净值"); ax1.legend(); ax1.grid(alpha=.2)
    ax2.fill_between(df.trade_date, df.drawdown * 100, 0, color="#b23a48", alpha=.55)
    ax2.set_ylabel("回撤（%）"); ax2.grid(alpha=.2)
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=2)); ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate(rotation=20); fig.tight_layout(); fig.savefig(out, bbox_inches="tight"); plt.close(fig)


def plot_heatmap(results: pd.DataFrame, out: Path):
    pivot = results.pivot(index="公司", columns="通道", values="累计回报") * 100
    pivot = pivot.reindex(index=list(COMPANIES.values()), columns=[f"{a}/{b}" for a, b in CHANNELS])
    fig, ax = plt.subplots(figsize=(8.8, 3.8)); im = ax.imshow(pivot.values, cmap="RdYlGn", aspect="auto")
    ax.set_xticks(range(len(pivot.columns)), pivot.columns); ax.set_yticks(range(len(pivot.index)), pivot.index)
    ax.set_xlabel("入场/退出通道周期"); ax.set_title("不同股票与海龟通道参数的累计回报（%）")
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            ax.text(j, i, f"{pivot.iloc[i,j]:.1f}%", ha="center", va="center", fontsize=9)
    fig.colorbar(im, ax=ax, shrink=.8, label="累计回报（%）"); fig.tight_layout(); fig.savefig(out, bbox_inches="tight"); plt.close(fig)


def pct(x): return f"{x:.2%}"
def num(x): return "--" if pd.isna(x) else f"{x:.2f}"


def build_report(primary: pd.DataFrame, metrics: dict, comparisons: pd.DataFrame):
    pdfmetrics.registerFont(TTFont("SimSun", str(FONT_PATH)))
    styles = getSampleStyleSheet()
    body = ParagraphStyle("BodyCN", parent=styles["BodyText"], fontName="SimSun", fontSize=10.5, leading=15.75, alignment=TA_JUSTIFY, spaceBefore=0, spaceAfter=0, firstLineIndent=21)
    h1 = ParagraphStyle("H1CN", parent=body, fontSize=14, leading=21, spaceBefore=9, spaceAfter=4, firstLineIndent=0, textColor=colors.HexColor("#17365D"))
    h2 = ParagraphStyle("H2CN", parent=body, fontSize=11.5, leading=17, spaceBefore=5, spaceAfter=2, firstLineIndent=0, textColor=colors.HexColor("#244A73"))
    title = ParagraphStyle("TitleCN", parent=body, fontSize=18, leading=27, alignment=TA_CENTER, firstLineIndent=0)
    center = ParagraphStyle("CenterCN", parent=body, alignment=TA_CENTER, firstLineIndent=0)
    caption = ParagraphStyle("CaptionCN", parent=body, alignment=TA_CENTER, firstLineIndent=0, spaceAfter=3)
    small = ParagraphStyle("SmallCN", parent=body, fontSize=8.7, leading=12.5, firstLineIndent=0)
    doc = BaseDocTemplate(str(PDF_PATH), pagesize=A4, leftMargin=24*mm, rightMargin=24*mm, topMargin=19*mm, bottomMargin=18*mm, title="辛家辉TASK4", author="辛家辉")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    def footer(canvas, _doc):
        canvas.saveState(); canvas.setFont("SimSun", 9); canvas.drawCentredString(A4[0]/2, 10*mm, f"- {canvas.getPageNumber()} -"); canvas.restoreState()
    doc.addPageTemplates(PageTemplate(id="main", frames=frame, onPage=footer))
    info = Table([["课程任务", "TASK4 复刻传奇：海龟交易法则实战演练"], ["姓名", "辛家辉"], ["完成日期", "2026年7月11日"], ["提交文件", "辛家辉TASK4.pdf"]], colWidths=[35*mm, 105*mm])
    info.setStyle(TableStyle([("FONTNAME",(0,0),(-1,-1),"SimSun"),("FONTSIZE",(0,0),(-1,-1),10.5),("LEADING",(0,0),(-1,-1),15.75),("BACKGROUND",(0,0),(0,-1),colors.HexColor("#EAF2F8")),("GRID",(0,0),(-1,-1),.5,colors.HexColor("#8FA4B5")),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("ALIGN",(0,0),(0,-1),"CENTER"),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
    story = [Spacer(1,8*mm), Paragraph("TASK4 复刻传奇：海龟交易法则实战演练", title), Paragraph("量化交易课程个人作业报告", center), Spacer(1,7*mm), info,
             Paragraph("一、作业任务", h1), Paragraph("本次作业学习海龟交易法则，解释高低点通道、ATR 和止损条件，使用 Python 完成信号生成、可视化与回测，并通过更换股票和通道周期比较策略效果。", body),
             Paragraph("二、海龟策略的核心思想与优势", h1),
             Paragraph("海龟交易法则是一套规则明确的趋势跟随方法。策略不预测价格顶部或底部，而是在价格突破过去一段时间高点后跟随趋势，在价格跌破退出通道或触发波动率止损时离场。其核心是让盈利趋势继续运行，同时用预先规定的退出规则限制单笔损失。", body),
             Paragraph("关键优势包括：规则透明，减少主观情绪干扰；高低点通道能够适应不同价格水平；ATR 将止损距离与市场波动联系起来；参数较少，容易编程、复现和跨股票比较。其不足是震荡行情中容易出现假突破，连续小额亏损也会受到交易成本影响。", body),
             Paragraph("三、关键概念", h1), Paragraph("1. 高低点通道", h2),
             Paragraph("入场上轨是此前 N 个交易日最高价的最大值，退出下轨是此前 M 个交易日最低价的最小值。主案例使用 20 日入场上轨和 10 日退出下轨。计算时通道整体滞后一天，保证第 t 日只能看到第 t-1 日及更早的信息。", body),
             Paragraph("2. 平均真实波幅（ATR）", h2),
             Paragraph("真实波幅 TR 取当日最高价减最低价、最高价与前收盘价差的绝对值、最低价与前收盘价差的绝对值三者最大值。ATR 是 TR 的平滑平均，本作业采用 20 日 Wilder 平滑，用于衡量近期波动。", body),
             Paragraph("3. 止损条件", h2),
             Paragraph("买入后将初始止损价设为成交开盘价减 2 倍入场前一日 ATR。如果前一日收盘价跌破该止损线，或跌破退出通道，则在下一交易日开盘卖出。", body),
             Paragraph("四、Python 实现与回测口径", h1),
             Paragraph("程序读取 TASK1 的日线 CSV，计算滞后通道和 ATR，再逐日维护仓位与止损线。第 t 日的交易决定只使用第 t-1 日及更早数据，按第 t 日开盘价执行。单边手续费为万分之三，滑点与价格冲击为万分之一。", body),
             Table([[Paragraph("df['entry_high'] = df['high'].rolling(20).max().shift(1)<br/>df['exit_low'] = df['low'].rolling(10).min().shift(1)<br/># t日开盘前只检查t-1日收盘、通道和ATR<br/>if previous.close &gt; previous.entry_high: target = 1<br/>active_stop = open_t - 2 * previous.atr<br/>if previous.close &lt; previous.exit_low or previous.close &lt;= active_stop: target = 0<br/>strategy_return = gross_return - (0.0003 + 0.0001) * turnover", small)]], colWidths=[doc.width], style=TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#F3F6F8")),("BOX",(0,0),(-1,-1),.5,colors.HexColor("#AAB7C4")),("LEFTPADDING",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)])),
             Paragraph("五、主案例结果：恒瑞医药 20/10 通道", h1),
             KeepTogether([Image(str(FIG_DIR/"figure1_turtle_channels.png"), width=doc.width, height=doc.width*.52), Paragraph("图1 恒瑞医药海龟通道、止损线与交易信号", caption)]),
             Paragraph("图1中蓝线为滞后 20 日入场上轨，橙线为滞后 10 日退出下轨，红色虚线为持仓后的 2ATR 止损线。绿色和红色三角分别标记下一交易日开盘执行的买入和卖出。", body),
             PageBreak(), KeepTogether([Image(str(FIG_DIR/"figure2_atr.png"), width=doc.width, height=doc.width*.38), Paragraph("图2 恒瑞医药20日ATR", caption)]),
             Paragraph("ATR 随价格波动放大或收缩。波动较大时，2ATR 止损距离更宽，减少普通噪声导致的过早退出；波动较小时，止损距离相应收窄。", body),
             KeepTogether([Image(str(FIG_DIR/"figure3_nav_drawdown.png"), width=doc.width, height=doc.width*.59), Paragraph("图3 海龟策略净值与回撤", caption)])]
    metric_rows = [["指标", "策略结果", "说明"], ["累计回报", pct(metrics["累计回报"]), "扣除手续费与滑点后的期末收益"], ["最大回撤", pct(metrics["最大回撤"]), "净值历史最大峰谷跌幅"], ["年化夏普比率", num(metrics["夏普比率"]), "无风险日收益近似为0"], ["交易次数", str(metrics["交易次数"]), "买入和卖出合计"], ["同期买入持有", pct(metrics["买入持有"]), "不择时基准"]]
    mt = Table(metric_rows, colWidths=[34*mm,34*mm,doc.width-68*mm], repeatRows=1)
    mt.setStyle(TableStyle([("FONTNAME",(0,0),(-1,-1),"SimSun"),("FONTSIZE",(0,0),(-1,-1),9.3),("LEADING",(0,0),(-1,-1),13.5),("BACKGROUND",(0,0),(-1,0),colors.HexColor("#D9EAF7")),("GRID",(0,0),(-1,-1),.4,colors.HexColor("#8FA4B5")),("ALIGN",(0,0),(1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    story += [Paragraph("表1 恒瑞医药海龟20/10策略绩效", caption), mt, Paragraph(f"主案例累计回报为 {pct(metrics['累计回报'])}，最大回撤为 {pct(metrics['最大回撤'])}，年化夏普比率为 {num(metrics['夏普比率'])}，共发生 {metrics['交易次数']} 次买卖。结果仅反映当前约一年样本。", body), Paragraph("六、不同股票与通道参数比较", h1)]
    show = comparisons.copy(); show["累计回报"] = show["累计回报"].map(pct); show["最大回撤"] = show["最大回撤"].map(pct); show["夏普比率"] = show["夏普比率"].map(num)
    rows = [["公司","通道","累计回报","最大回撤","夏普","交易次数"]] + show[["公司","通道","累计回报","最大回撤","夏普比率","交易次数"]].values.tolist()
    ct = Table(rows, colWidths=[27*mm,20*mm,27*mm,27*mm,22*mm,24*mm], repeatRows=1)
    ct.setStyle(TableStyle([("FONTNAME",(0,0),(-1,-1),"SimSun"),("FONTSIZE",(0,0),(-1,-1),8.0),("LEADING",(0,0),(-1,-1),10.5),("BACKGROUND",(0,0),(-1,0),colors.HexColor("#D9EAF7")),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F6F8FA")]),("GRID",(0,0),(-1,-1),.35,colors.HexColor("#9EADB8")),("ALIGN",(1,0),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2)]))
    story += [Paragraph("表2 四只股票与四组通道参数比较", caption), ct, Spacer(1,2*mm), KeepTogether([Image(str(FIG_DIR/"figure4_parameter_heatmap.png"), width=doc.width, height=doc.width*.38), Paragraph("图4 不同股票与通道参数的累计回报", caption)]),
              Paragraph("不同股票和通道周期的表现差异较大。短通道更敏感，交易次数通常更多，也更容易在震荡中出现假突破；长通道过滤噪声，但一年样本可能不足以形成多次完整趋势。参数比较用于观察敏感性，不应直接把样本内最高收益当作未来最优参数。", body),
              Paragraph("七、适用场景与作业心得", h1), Paragraph("海龟策略更适合具有持续方向、突破后能够延续的趋势行情。在窄幅震荡、频繁反转的市场中，策略容易反复进出并产生亏损。ATR 止损能够根据波动调整风险距离，但不能消除跳空、涨跌停或流动性不足造成的执行风险。", body),
              Paragraph("通过本次作业，我理解了海龟法则并不是单纯的“突破就买入”，而是一套由入场、退出、波动率和风险控制共同组成的规则。严格使用滞后信息和开盘执行，可以避免把当日收盘信息错误用于当日交易。后续可使用更长历史数据，加入按 ATR 控制仓位和分批加仓，再进行样本外检验。", body),
              Paragraph("八、作业总结", h1), Paragraph("本次作业完成通道、ATR、2ATR 止损、严格时序回测和参数比较；Python 源码、图表与 CSV 均保存在 TASK4 目录。", body)]
    doc.build(story)


def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True); RESULT_DIR.mkdir(parents=True, exist_ok=True); setup_plot_font()
    rows = []; primary = primary_metrics = None
    for code, company in COMPANIES.items():
        raw = load_price(code)
        for entry, exit_ in CHANNELS:
            bt, metrics = backtest(raw, entry, exit_)
            rows.append({"公司": company, "代码": code.replace("_", "."), "通道": f"{entry}/{exit_}", **metrics})
            if code == "600276_SH" and (entry, exit_) == (20, 10):
                primary, primary_metrics = bt, metrics
                bt.to_csv(RESULT_DIR / "600276_SH_turtle_20_10_backtest.csv", index=False, encoding="utf-8-sig")
    comparisons = pd.DataFrame(rows)
    comparisons.to_csv(RESULT_DIR / "all_stocks_channel_comparison.csv", index=False, encoding="utf-8-sig")
    plot_channels(primary, FIG_DIR / "figure1_turtle_channels.png"); plot_atr(primary, FIG_DIR / "figure2_atr.png")
    plot_nav(primary, FIG_DIR / "figure3_nav_drawdown.png"); plot_heatmap(comparisons, FIG_DIR / "figure4_parameter_heatmap.png")
    build_report(primary, primary_metrics, comparisons)
    print(comparisons.to_string(index=False)); print(f"\nGenerated: {PDF_PATH}")


if __name__ == "__main__":
    main()
