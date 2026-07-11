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

    info_table = Table([["课程任务", "TASK3 策略首秀"], ["姓名", "辛家辉"],
                        ["完成日期", "2026年7月11日"], ["提交文件", "辛家辉TASK3.pdf"]],
                       colWidths=[35*mm, 90*mm])
    info_table.setStyle(TableStyle([("FONTNAME",(0,0),(-1,-1),"SimSun"),("FONTSIZE",(0,0),(-1,-1),10.5),
                                    ("LEADING",(0,0),(-1,-1),15.75),("BACKGROUND",(0,0),(0,-1),colors.HexColor("#EAF2F8")),
                                    ("GRID",(0,0),(-1,-1),.5,colors.HexColor("#8FA4B5")),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
                                    ("ALIGN",(0,0),(0,-1),"CENTER"),("LEFTPADDING",(0,0),(-1,-1),8),
                                    ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
    task_table = Table([
        ["1", "解释双均线策略中的金叉、死叉等概念"],
        ["2", "解释累计回报、最大回撤和夏普比率等评价指标"],
        ["3", "使用 Python 完成数据加载、均线计算、信号生成、可视化与回测"],
        ["4", "更换股票和均线周期，比较结果并总结适用场景与心得"],
    ], colWidths=[12*mm, doc.width-12*mm])
    task_table.setStyle(TableStyle([("FONTNAME",(0,0),(-1,-1),"SimSun"),("FONTSIZE",(0,0),(-1,-1),10.5),
                                    ("LEADING",(0,0),(-1,-1),15.75),("GRID",(0,0),(-1,-1),.35,colors.HexColor("#B2BEC7")),
                                    ("ALIGN",(0,0),(0,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
                                    ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)]))

    story = [Spacer(1, 8*mm), Paragraph("TASK3 策略首秀：用均线交叉反映市场趋势变化", title),
             Paragraph("量化交易课程个人作业报告", center), Spacer(1, 8*mm), info_table,
             Spacer(1, 7*mm), Paragraph("一、作业任务", h1), task_table,
             Paragraph("本次作业使用 TASK1 已保存的四只创新药股票日线数据。恒瑞医药（600276.SH）作为主要展示对象，短期均线和长期均线设置为 5 日与 15 日；另外使用其他股票和周期组合进行比较。回测采用“当日收盘确认信号、下一交易日持仓生效”的方式，并计入单边 0.10% 交易成本。", body),
             Paragraph("二、双均线策略与评价指标", h1),
             Paragraph("1. 双均线策略", h2),
             Paragraph("双均线策略同时计算短期均线和长期均线。短期均线对新价格反应较快，长期均线更平滑，用于刻画中期趋势。当短期均线由下向上穿越长期均线时形成“金叉”，通常解释为近期价格动能转强，策略由空仓转为持有；当短期均线由上向下穿越长期均线时形成“死叉”，通常解释为趋势转弱，策略卖出并回到空仓。本作业只做多、不做空。", body),
             Paragraph("简单移动平均线可写为 MA(n)<sub>t</sub> = (P<sub>t</sub> + … + P<sub>t-n+1</sub>)/n，其中 P<sub>t</sub> 为第 t 个交易日收盘价。均线本质上是滞后指标：平滑能够过滤部分短期噪声，但也会使入场和离场晚于价格拐点。", body),
             Paragraph("2. 策略评价指标", h2),
             Paragraph("累计回报（Cumulative Return）表示整个回测期内资金的总增值比例，即期末净值减 1。它直观反映最终盈亏，但不能单独说明实现该回报时承担了多大风险。", body),
             Paragraph("最大回撤（Maximum Drawdown, MDD）是净值从历史峰值到随后谷值的最大跌幅。本次作业按 MDD = min(V<sub>t</sub>/max<sub>s≤t</sub>V<sub>s</sub> - 1) 计算；数值越负，表示历史最坏亏损越大。", body),
             Paragraph("夏普比率（Sharpe Ratio）衡量单位波动对应的超额收益。由于样本为日频且回测期较短，本次作业将无风险日收益近似设为 0，按 √252 × 日策略收益均值 / 日策略收益标准差进行年化。夏普比率越高通常越好，但它对样本长度、收益分布和无风险利率设定敏感。", body),
             KeepTogether([Paragraph("三、Python 实现过程", h1),
                           Paragraph("1. 加载并整理数据", h2),
                           Paragraph(f"程序从 assets 目录读取日线 CSV，将交易日期转换为日期格式并按升序排列。数据区间为 {primary.trade_date.min():%Y-%m-%d} 至 {primary.trade_date.max():%Y-%m-%d}，共 {len(primary)} 个交易日。", body)]),
             Paragraph("2. 计算均线和交易信号", h2),
             Paragraph("主案例滚动计算 MA5 与 MA15。MA5 高于 MA15 时持有股票，MA5 低于 MA15 时空仓；信号由 0 变为 1 时标记买入，由 1 变为 0 时标记卖出。", body),
             Paragraph("3. 模拟交易并计算指标", h2),
             Paragraph("为避免使用未来信息，程序将当日信号滞后一个交易日形成实际持仓。策略日收益等于持仓乘以股票日收益，再减去换仓成本；由日收益累计得到策略净值，并据此计算累计回报、最大回撤和夏普比率。", body),
             Paragraph("关键实现如下（完整代码与结果 CSV 随报告保存在 TASK3 目录）：", body),
             Table([[Paragraph("df['ma_short'] = df['close'].rolling(5).mean()<br/>df['ma_long'] = df['close'].rolling(15).mean()<br/>df['signal'] = (df['ma_short'] &gt; df['ma_long']).astype(int)<br/>df['position'] = df['signal'].shift(1).fillna(0)<br/>turnover = df['position'].diff().abs().fillna(0)<br/>df['strategy_return'] = df['position'] * df['close'].pct_change().fillna(0) - 0.001 * turnover<br/>df['strategy_nav'] = (1 + df['strategy_return']).cumprod()", small)]], colWidths=[doc.width], style=TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#F3F6F8")),("BOX",(0,0),(-1,-1),.5,colors.HexColor("#AAB7C4")),("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)])),
             Paragraph("四、运行结果与图形解读", h1),
             Paragraph("1. 均线与交易信号", h2),
             KeepTogether([Image(str(FIG_DIR/"figure1_signals.png"), width=doc.width, height=doc.width*0.50), Paragraph("图1 恒瑞医药收盘价、长短均线与买卖信号", caption)]),
             Paragraph("图1中，绿色向上三角表示短均线上穿长均线后的买入信号，红色向下三角表示短均线下穿长均线后的卖出信号。信号主要出现在趋势方向发生持续变化的位置；当价格横盘震荡时，两条均线距离较近，容易反复交叉并产生交易成本。图中买卖标记用于展示信号确认日，实际持仓收益从下一交易日开始计算。", body),
             PageBreak(),
             Paragraph("2. 策略净值与回撤", h2),
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
              Paragraph(f"从表1可以读出：策略累计回报为 {pct(primary_metrics['累计回报'])}，最大回撤为 {pct(primary_metrics['最大回撤'])}，年化夏普比率为 {num(primary_metrics['夏普比率'])}，同期买入持有收益为 {pct(primary_metrics['买入持有'])}。MA5/15 在这一样本中的收益为正，但优势不明显，而且回撤较大。因此，不能只根据期末盈利就判断策略效果很好，还必须结合回撤和夏普比率。", body),
              Paragraph("五、更换股票和均线周期", h1)]

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
              Paragraph(f"比较结果为：{best_text}。我发现，同一组均线参数用于不同股票时，收益可能相差很大；同一只股票更换周期后，结果也会明显改变。较短周期对价格变化反应快，但交易更频繁，也更容易受到短期噪声影响；较长周期比较平滑，但可能错过较快的趋势反转。", body),
              Paragraph("六、适用场景和应用心得", h1),
              KeepTogether([Paragraph("1. 适用场景", h2),
                           Paragraph("双均线策略更适合方向持续、趋势较清晰的行情。如果上涨或下跌能够保持一段时间，均线交叉有机会跟随主要趋势。策略规则直观、参数较少，也适合作为初学量化交易时的基础策略。", body)]),
              KeepTogether([Paragraph("2. 使用时需要注意的问题", h2),
                           Paragraph("当市场处于窄幅震荡状态时，长短均线可能反复交叉，产生多次无效买卖和交易成本。均线本身具有滞后性，遇到快速下跌时可能不能及时卖出。此外，本次回测只使用收盘价和基础手续费，没有完整模拟滑点、停牌以及涨跌停无法成交等真实交易情况。", body)]),
              KeepTogether([Paragraph("3. 作业心得", h2),
                           Paragraph("通过这次作业，我把前两个任务中准备的数据和指标真正用于交易策略。可视化能够帮助检查信号位置是否合理，但评价策略时不能只看累计回报，还需要同时观察最大回撤、夏普比率和交易次数。参数比较也说明，不能因为某一组参数在当前样本中收益最高，就直接认为它以后仍然最好。后续可以增加更长时间的数据，并将样本划分为训练区间和测试区间进行验证。", body)]),
              Paragraph("七、作业总结", h1),
              Paragraph("本次作业已经完成股价数据加载、长短均线计算、金叉与死叉识别、买卖信号绘制、模拟交易和绩效指标计算，并对四只股票及四组均线周期进行了比较。双均线策略能够用简单规则反映趋势变化，但实际效果取决于股票特征、均线周期和市场状态，使用时需要结合交易成本与风险控制。", body),
              Paragraph("提交内容说明", h1),
              Paragraph("TASK3 文件夹中包括：辛家辉TASK3.pdf、task3_moving_average_strategy.py、三张结果图，以及主案例回测明细和多股票多周期比较结果 CSV。", body)]
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
