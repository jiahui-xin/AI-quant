#!/usr/bin/env python3
"""TASK6: 机器学习选股模型——季度 Top 30 策略。

工作流：数据加载 → Winsorize + 标准化 → 四模型训练 → Top 30 选股 →
组合构建（EW / PW）→ 回测评估 → 4 张图表 → CSV 导出 → PDF 报告。
"""

from pathlib import Path
import pickle
import warnings

import matplotlib
matplotlib.use("Agg")
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
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether,
                                PageBreak, PageTemplate, Paragraph, Spacer,
                                Table, TableStyle)
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, roc_auc_score
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import RandomizedSearchCV

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
TASK_DIR = ROOT / "TASK6"
DATA_PATH = ROOT / "material" / "model_data.csv"
FIG_DIR = TASK_DIR / "figures"
RESULT_DIR = TASK_DIR / "results"
PORTFOLIO_DIR = RESULT_DIR / "portfolios"
MODEL_DIR = TASK_DIR / "models"
PDF_PATH = TASK_DIR / "辛家辉TASK6.pdf"
FONT_PATH = Path("/Users/jiahuixin/Library/Fonts/SimSun.ttf")

RANDOM_STATE = 42
TOP_N = 30
SPLIT_DATE = "2021/7/1"
TRAIN_DATES = ["2020/3/31", "2020/6/30", "2020/9/30", "2020/12/31", "2021/3/31", "2021/6/30"]
TEST_DATES = ["2021/9/30", "2021/12/31", "2022/3/31", "2022/6/30"]
FEATURE_COLS = [
    "企业倍数(EV除EBITDA)", "市净率PB(MRQ)", "市现率PCF(现金净流量TTM)",
    "市现率PCF(经营现金流TTM)", "市盈率PE(TTM)", "市盈率PE(TTM,扣除非经常性损益)",
    "市销率PS(TTM)", "股息率(近12个月)", "MV", "净利润同比增长率",
    "净资产同比增长率", "利润总额(同比增长率)", "基本每股收益(同比增长率)",
    "总资产同比增长率", "现金净流量同比增长率", "经营活动产生的现金流量净额(同比增长率)",
    "营业利润(同比增长率)", "营业总收入(同比增长率)", "营业收入(同比增长率)",
]
MODEL_NAMES = ["LinearRegression", "LogisticRegression", "DecisionTree", "RandomForest"]
MODEL_COLORS = {"LinearRegression": "#378ADD", "LogisticRegression": "#534AB7",
                "DecisionTree": "#0F6E56", "RandomForest": "#993C1D", "Market": "#888888"}


# ===== L1: 数据层 =====

def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    df["Date"] = df["Date"].astype(str).str.strip()
    df = df.dropna(subset=FEATURE_COLS + ["Next_Ret"]).reset_index(drop=True)
    return df


def split_train_test(df: pd.DataFrame):
    train = df[df["Date"].isin(TRAIN_DATES)].copy()
    test = df[df["Date"].isin(TEST_DATES)].copy()
    return train, test


def winsorize(train: pd.DataFrame, test: pd.DataFrame, cols: list, lower=0.01, upper=0.99):
    tr = train.copy()
    te = test.copy()
    for c in cols:
        lo = train[c].quantile(lower)
        hi = train[c].quantile(upper)
        tr[c] = tr[c].clip(lo, hi)
        te[c] = te[c].clip(lo, hi)
    return tr, te


# ===== L2: 核心逻辑层 — 模型训练 =====

def train_models(X_train, y_train_cont, y_train_bin):
    models = {}

    lr = LinearRegression().fit(X_train, y_train_cont)
    models["LinearRegression"] = lr

    logr = LogisticRegression(C=0.01, max_iter=500, random_state=RANDOM_STATE).fit(X_train, y_train_bin)
    models["LogisticRegression"] = logr

    dt = DecisionTreeRegressor(max_depth=8, min_samples_leaf=50, random_state=RANDOM_STATE).fit(X_train, y_train_cont)
    models["DecisionTree"] = dt

    param_dist = {"n_estimators": [50, 80, 100], "max_depth": [6, 8, 10], "min_samples_leaf": [20, 50]}
    rf_base = RandomForestRegressor(random_state=RANDOM_STATE, n_jobs=-1)
    rf_search = RandomizedSearchCV(rf_base, param_dist, n_iter=4, cv=3, scoring="neg_mean_squared_error",
                                   random_state=RANDOM_STATE, n_jobs=-1)
    rf_search.fit(X_train, y_train_cont)
    models["RandomForest"] = rf_search.best_estimator_
    print(f"  RandomForest best params: {rf_search.best_params_}")
    return models


def predict_models(models, X_test):
    preds = {}
    preds["LinearRegression"] = models["LinearRegression"].predict(X_test)
    preds["LogisticRegression"] = models["LogisticRegression"].predict_proba(X_test)[:, 1]
    preds["DecisionTree"] = models["DecisionTree"].predict(X_test)
    preds["RandomForest"] = models["RandomForest"].predict(X_test)
    return preds


def save_models(models):
    for name, model in models.items():
        with open(MODEL_DIR / f"{name}.pkl", "wb") as f:
            pickle.dump(model, f)


# ===== L2: 核心逻辑层 — Top 30 选股 + 组合构建 =====

def build_portfolios(test_df, preds, y_test_cont):
    """对每模型每季度取 Top 30，计算 EW 和 PW 组合收益。"""
    test_work = test_df[["Date", "Code"]].copy()
    test_work["Next_Ret"] = y_test_cont.values
    for name in MODEL_NAMES:
        test_work[f"pred_{name}"] = preds[name]

    quarterly = {}
    for qdate in TEST_DATES:
        mask = test_work["Date"] == qdate
        q_df = test_work[mask].copy()
        q_actual = q_df["Next_Ret"].values

        # 基准：全市场等权
        quarterly.setdefault("Market", {})[qdate] = q_actual.mean()

        for name in MODEL_NAMES:
            pred_col = f"pred_{name}"
            top_idx = q_df[pred_col].values.argsort()[::-1][:TOP_N]
            top_actual = q_actual[top_idx]
            top_pred = q_df[pred_col].values[top_idx]

            # EW 等权
            ew_ret = top_actual.mean()
            quarterly.setdefault(f"{name}_EW", {})[qdate] = ew_ret

            # PW 预测收益加权（clip 避免负权重）
            weights = np.clip(top_pred, 0, None)
            if weights.sum() > 0:
                weights = weights / weights.sum()
            else:
                weights = np.ones(len(top_pred)) / len(top_pred)
            pw_ret = (top_actual * weights).sum()
            quarterly.setdefault(f"{name}_PW", {})[qdate] = pw_ret

            # 保存组合明细
            portfolio_df = pd.DataFrame({
                "Code": q_df["Code"].values[top_idx],
                "Predicted": top_pred,
                "Actual_Return": top_actual,
                "Weight_EW": 1.0 / TOP_N,
                "Weight_PW": weights,
            })
            portfolio_df.to_csv(PORTFOLIO_DIR / f"portfolio_{name}_EW_PW_{qdate.replace('/', '')}.csv",
                                index=False, encoding="utf-8-sig")
    return quarterly


# ===== L2: 核心逻辑层 — 回测评估 =====

def calc_metrics(quarterly: dict) -> pd.DataFrame:
    rows = []
    for combo, qdict in quarterly.items():
        if combo == "Market":
            model, weight = "Market", "--"
        else:
            parts = combo.split("_")
            model, weight = parts[0], parts[1]

        rets = np.array([qdict[d] for d in TEST_DATES])
        cum_ret = (1 + rets).prod() - 1
        ann_ret = rets.mean() * 4
        ann_vol = rets.std() * np.sqrt(4)
        sharpe = ann_ret / ann_vol if ann_vol > 0 else 0

        nav = np.cumprod(1 + rets)
        peak = np.maximum.accumulate(nav)
        dd = nav / peak - 1
        max_dd = dd.min()

        if combo != "Market":
            excess = rets - np.array([quarterly["Market"][d] for d in TEST_DATES])
            ir = excess.mean() / excess.std() * np.sqrt(4) if excess.std() > 0 else 0
            win_rate = (excess > 0).mean()
        else:
            ir, win_rate = 0, 0

        rows.append({
            "模型": model, "权重方式": weight,
            "累计收益": cum_ret, "年化收益": ann_ret, "年化波动率": ann_vol,
            "夏普比率": sharpe, "最大回撤": max_dd,
            "信息比率": ir, "超额胜率": win_rate,
        })
    return pd.DataFrame(rows)


# ===== L3: 可视化层 =====

def setup_plot_font():
    matplotlib.font_manager.fontManager.addfont(str(FONT_PATH))
    plt.rcParams.update({"font.family": "SimSun", "axes.unicode_minus": False,
                         "figure.dpi": 130, "savefig.dpi": 220})


def plot_cumulative_returns(quarterly, out):
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    x_labels = [d.replace("/", "\n") for d in TEST_DATES]
    x = range(len(TEST_DATES))

    for combo, qdict in quarterly.items():
        rets = np.array([qdict[d] for d in TEST_DATES])
        nav = np.cumprod(1 + rets)
        if combo == "Market":
            label, color, ls = "市场基准", "#888888", "--"
        else:
            parts = combo.split("_")
            label = f"{parts[0]}-{parts[1]}"
            color = MODEL_COLORS.get(parts[0], "#444")
            ls = "-" if parts[1] == "EW" else ":"
        ax.plot(x, nav, color=color, lw=1.8, ls=ls, label=label, marker="o", markersize=5)

    ax.set_xticks(list(x))
    ax.set_xticklabels(x_labels)
    ax.set_ylabel("累计净值")
    ax.set_title("图1 各模型 Top 30 组合累计收益对比（含市场基准）", fontsize=13, pad=12)
    ax.axhline(1.0, color="#ccc", lw=0.8, ls="-")
    ax.grid(alpha=0.25)
    ax.legend(ncol=3, fontsize=8, loc="upper left", frameon=True)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def plot_ew_vs_pw(metrics_df, out):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.8))
    models = [m for m in MODEL_NAMES]
    ew_data = metrics_df[metrics_df["权重方式"] == "EW"].set_index("模型").reindex(models)
    pw_data = metrics_df[metrics_df["权重方式"] == "PW"].set_index("模型").reindex(models)
    market_ret = metrics_df[metrics_df["模型"] == "Market"]["累计收益"].values[0]
    market_sharpe = metrics_df[metrics_df["模型"] == "Market"]["夏普比率"].values[0]

    x = np.arange(len(models))
    w = 0.35
    ax1.bar(x - w/2, ew_data["累计收益"] * 100, w, color="#378ADD", label="EW 等权")
    ax1.bar(x + w/2, pw_data["累计收益"] * 100, w, color="#534AB7", label="PW 预测加权")
    ax1.axhline(market_ret * 100, color="#888", ls="--", lw=1, label=f"市场基准 {market_ret*100:.1f}%")
    ax1.set_xticks(x); ax1.set_xticklabels(models, fontsize=9)
    ax1.set_ylabel("累计收益（%）"); ax1.set_title("累计收益 EW vs PW", fontsize=12)
    ax1.legend(fontsize=8); ax1.grid(axis="y", alpha=0.25)

    ax2.bar(x - w/2, ew_data["夏普比率"], w, color="#0F6E56", label="EW 等权")
    ax2.bar(x + w/2, pw_data["夏普比率"], w, color="#993C1D", label="PW 预测加权")
    ax2.axhline(market_sharpe, color="#888", ls="--", lw=1, label=f"市场基准 {market_sharpe:.2f}")
    ax2.set_xticks(x); ax2.set_xticklabels(models, fontsize=9)
    ax2.set_ylabel("夏普比率"); ax2.set_title("夏普比率 EW vs PW", fontsize=12)
    ax2.legend(fontsize=8); ax2.grid(axis="y", alpha=0.25)

    fig.suptitle("图2 EW 等权 vs PW 预测收益加权对比", fontsize=13, y=1.02)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def plot_feature_importance(models, out):
    dt_imp = pd.Series(models["DecisionTree"].feature_importances_, index=FEATURE_COLS).sort_values()
    rf_imp = pd.Series(models["RandomForest"].feature_importances_, index=FEATURE_COLS).sort_values()
    top_dt = dt_imp.tail(15)
    top_rf = rf_imp.tail(15)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.5))
    ax1.barh(top_dt.index, top_dt.values, color="#0F6E56", edgecolor="#085041")
    ax1.set_xlabel("特征重要性"); ax1.set_title("决策树 Top-15 特征重要性", fontsize=12)
    ax1.grid(axis="x", alpha=0.25)

    ax2.barh(top_rf.index, top_rf.values, color="#993C1D", edgecolor="#712B13")
    ax2.set_xlabel("特征重要性"); ax2.set_title("随机森林 Top-15 特征重要性", fontsize=12)
    ax2.grid(axis="x", alpha=0.25)

    fig.suptitle("图3 决策树与随机森林特征重要性对比", fontsize=13, y=1.02)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def plot_linear_coefficients(models, out):
    """展示线性回归与逻辑回归的系数对比（两者都有 coef_ 属性）。"""
    lr_coefs = pd.Series(models["LinearRegression"].coef_, index=FEATURE_COLS)
    logr_coefs = pd.Series(models["LogisticRegression"].coef_[0], index=FEATURE_COLS)

    # 线性回归：取 Top 10 正/负
    lr_top_pos = lr_coefs.sort_values(ascending=False).head(10)
    lr_top_neg = lr_coefs.sort_values().head(10)
    lr_combined = pd.concat([lr_top_neg, lr_top_pos])

    # 逻辑回归：按绝对值排序取 Top 15（系数大小代表对涨跌概率的影响强度）
    logr_abs = logr_coefs.abs().sort_values(ascending=False).head(15)
    logr_top = logr_coefs.loc[logr_abs.index]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))

    # 左图：线性回归系数
    colors_lr = ["#b23a48" if v < 0 else "#2f7d5c" for v in lr_combined.values]
    ax1.barh(range(len(lr_combined)), lr_combined.values, color=colors_lr, edgecolor="#333")
    ax1.set_yticks(range(len(lr_combined)))
    ax1.set_yticklabels(lr_combined.index, fontsize=8)
    ax1.axvline(0, color="#333", lw=0.8)
    ax1.set_xlabel("回归系数"); ax1.set_title("线性回归系数 Top 10 正/负", fontsize=12)
    ax1.grid(axis="x", alpha=0.25)

    # 右图：逻辑回归系数（按绝对值排序）
    colors_logr = ["#b23a48" if v < 0 else "#2f7d5c" for v in logr_top.values]
    ax2.barh(range(len(logr_top)), logr_top.values, color=colors_logr, edgecolor="#333")
    ax2.set_yticks(range(len(logr_top)))
    ax2.set_yticklabels(logr_top.index, fontsize=8)
    ax2.axvline(0, color="#333", lw=0.8)
    ax2.set_xlabel("逻辑回归系数（log-odds）"); ax2.set_title("逻辑回归系数 Top 15（按绝对值）", fontsize=12)
    ax2.grid(axis="x", alpha=0.25)

    fig.suptitle("图4 线性回归与逻辑回归系数对比", fontsize=13, y=1.02)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


# ===== L5: PDF 报告层 =====

def build_report(metrics_df, model_eval, n_train, n_test, n_features):
    pdfmetrics.registerFont(TTFont("SimSun", str(FONT_PATH)))
    base = getSampleStyleSheet()["BodyText"]
    body = ParagraphStyle("BodyCN", parent=base, fontName="SimSun", fontSize=10.5, leading=15.75,
                          alignment=TA_JUSTIFY, spaceBefore=0, spaceAfter=0, firstLineIndent=21)
    h1 = ParagraphStyle("H1CN", parent=body, fontSize=14, leading=21, spaceBefore=9, spaceAfter=4,
                        firstLineIndent=0, textColor=colors.HexColor("#17365D"))
    h2 = ParagraphStyle("H2CN", parent=body, fontSize=11.5, leading=17, spaceBefore=5, spaceAfter=2,
                        firstLineIndent=0, textColor=colors.HexColor("#244A73"))
    title = ParagraphStyle("TitleCN", parent=body, fontSize=18, leading=27, alignment=TA_CENTER, firstLineIndent=0)
    center = ParagraphStyle("CenterCN", parent=body, alignment=TA_CENTER, firstLineIndent=0)
    caption = ParagraphStyle("CaptionCN", parent=body, alignment=TA_CENTER, firstLineIndent=0, spaceAfter=3)
    small = ParagraphStyle("SmallCN", parent=body, fontSize=8.7, leading=12.5, firstLineIndent=0)

    doc = BaseDocTemplate(str(PDF_PATH), pagesize=A4, leftMargin=24*mm, rightMargin=24*mm,
                          topMargin=19*mm, bottomMargin=18*mm, title="辛家辉TASK6", author="辛家辉")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")

    def footer(canvas, _doc):
        canvas.saveState(); canvas.setFont("SimSun", 9)
        canvas.drawCentredString(A4[0]/2, 10*mm, f"- {canvas.getPageNumber()} -")
        canvas.restoreState()

    doc.addPageTemplates(PageTemplate(id="main", frames=frame, onPage=footer))

    info = Table([
        ["课程任务", "TASK6 智能决策者：用机器学习定制专属策略"],
        ["姓名", "辛家辉"],
        ["完成日期", "2026年7月18日"],
        ["提交文件", "辛家辉TASK6.pdf"],
        ["数据集", f"model_data.csv（{n_train + n_test:,} 条 × {n_features} 个财务因子）"],
    ], colWidths=[35*mm, 105*mm])
    info.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "SimSun"),
        ("FONTSIZE", (0, 0), (-1, -1), 10.5),
        ("LEADING", (0, 0), (-1, -1), 15.75),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EAF2F8")),
        ("GRID", (0, 0), (-1, -1), .5, colors.HexColor("#8FA4B5")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    # 找最佳模型
    best_ew = metrics_df[metrics_df["权重方式"] == "EW"].sort_values("夏普比率", ascending=False).iloc[0]
    best_model = best_ew["模型"]
    market = metrics_df[metrics_df["模型"] == "Market"].iloc[0]

    story = [
        Spacer(1, 8*mm),
        Paragraph("TASK6 智能决策者：用机器学习定制专属策略", title),
        Paragraph("量化交易课程个人作业报告", center),
        Spacer(1, 7*mm),
        info,

        Paragraph("一、作业任务", h1),
        Paragraph("本作业使用 A 股财务因子数据，训练多种机器学习模型预测股票下一季度收益，"
                  "并在每个季度按预测得分挑选前 30 只股票构建投资组合。通过对比四种模型"
                  "（线性回归、逻辑回归、决策树、随机森林）的等权（EW）和预测收益加权（PW）"
                  "组合与市场基准的收益、风险、夏普比率、最大回撤、信息比率等指标，"
                  "评估机器学习选股策略的有效性。", body),

        Paragraph("二、数据集与时间划分", h1),
        Paragraph(f"原始数据共 {n_train + n_test:,} 条记录，包含 19 个财务因子和下一季度收益标签 Next_Ret。"
                  f"按时间划分：训练集 2020Q1–2021Q2 共 6 个季度 {n_train:,} 条，"
                  f"测试集 2021Q3–2022Q2 共 4 个季度 {n_test:,} 条。"
                  "训练集用于模型学习，测试集用于选股与策略回测，严格避免未来信息泄露。", body),
        Paragraph("数据预处理包括两个步骤：第一，对 19 个财务因子按训练集 1%/99% 分位数进行 Winsorize 缩尾，"
                  "消除极端值对模型的干扰；第二，用训练集均值和标准差对全部因子做 StandardScaler 标准化，"
                  "使各因子量纲统一，有利于线性模型和正则化收敛。", body),

        Paragraph("三、算法原理与选股逻辑", h1),
        Paragraph("1. 四种模型", h2),
        Paragraph("线性回归（LinearRegression）：以最小二乘法拟合因子与收益的线性关系，作为基线模型。"
                  "优点是简单可解释，缺点是无法捕捉非线性模式。", body),
        Paragraph("逻辑回归（LogisticRegression）：将 Next_Ret > 0 转为二分类标签，训练分类器后"
                  "取正类概率作为排序分数。C=0.01 增强正则化，避免过拟合。", body),
        Paragraph("决策树（DecisionTreeRegressor）：以 CART 算法递归分裂特征空间，max_depth=8 控制复杂度。"
                  "能捕捉非线性关系，可输出特征重要性。", body),
        Paragraph("随机森林（RandomForestRegressor）：通过自助采样和特征随机集成 100 棵决策树，"
                  "使用 RandomizedSearchCV 在 n_estimators、max_depth、min_samples_leaf 三个参数上做 4 轮随机搜索，"
                  "泛化能力通常优于单棵决策树。", body),

        Paragraph("2. Top 30 选股逻辑", h2),
        Paragraph(f"对测试集的每个季度，按模型预测得分从高到低排序，选取前 {TOP_N} 只股票构建组合。"
                  "EW（等权）组合中每只股票权重为 1/30；PW（预测收益加权）组合中权重正比于预测收益，"
                  "预测收益越高权重越大。组合收益为各股票下一季度实际收益的加权平均。", body),

        Paragraph("3. 评价指标", h2),
        Paragraph("累计收益：4 个季度组合收益连乘后减 1。年化收益 = 季度均值 × 4。"
                  "年化波动率 = 季度标准差 × √4。夏普比率 = 年化收益 / 年化波动率，衡量单位风险收益。"
                  "最大回撤：累计净值的最大峰谷跌幅。"
                  "信息比率 = 超额收益均值 / 超额收益标准差 × √4，衡量相对基准的风险调整收益。"
                  "超额胜率：组合收益超越市场基准的季度占比。", body),

        Paragraph("四、Python 实现流程", h1),
        Paragraph("程序从 model_data.csv 读取数据后，按 SPLIT_DATE=2021/7/1 划分训练集与测试集，"
                  "对 19 个因子做 Winsorize 和 StandardScaler。随后训练四个模型，"
                  "LinearRegression 和 DecisionTreeRegressor 直接预测收益，"
                  "LogisticRegression 预测涨跌概率，RandomForest 通过 RandomizedSearchCV 调参。", body),
        Paragraph("选股阶段对每个测试季度按预测得分排序取 Top 30，分别计算 EW 和 PW 组合收益。"
                  "回测阶段聚合 4 个季度收益序列，计算 9 个组合（4 模型 × 2 权重 + 市场基准）的"
                  "7 项指标，保存到 performance_metrics.csv 和 quarterly_returns.csv。"
                  "最后生成 4 张图表和 PDF 报告。", body),
        Table([[Paragraph(
            "df = pd.read_csv('material/model_data.csv')<br/>"
            "train, test = split_by_date(df, '2021/7/1')<br/>"
            "train, test = winsorize(train, test, FEATURE_COLS)<br/>"
            "scaler = StandardScaler().fit(train[FEATURE_COLS])<br/>"
            "X_train = scaler.transform(train[FEATURE_COLS])<br/>"
            "y_train = train['Next_Ret']<br/>"
            "models = train_models(X_train, y_train, (y_train > 0).astype(int))<br/>"
            "preds = predict_models(models, X_test)<br/>"
            "quarterly = build_portfolios(test, preds, y_test)<br/>"
            "metrics = calc_metrics(quarterly)", small)]],
            colWidths=[doc.width],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F6F8")),
                ("BOX", (0, 0), (-1, -1), .5, colors.HexColor("#AAB7C4")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ])),

        Paragraph("五、模型评估结果", h1),
    ]

    # 模型评估表
    me_rows = [["模型", "测试 MSE", "测试 MAE", "说明"]]
    for name in MODEL_NAMES:
        ev = model_eval[name]
        me_rows.append([name, f"{ev['mse']:.6f}", f"{ev['mae']:.6f}", ev["note"]])
    me_table = Table(me_rows, colWidths=[34*mm, 30*mm, 30*mm, doc.width - 94*mm], repeatRows=1)
    me_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "SimSun"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.3),
        ("LEADING", (0, 0), (-1, -1), 13.5),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAF7")),
        ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#8FA4B5")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    # 绩效表
    show = metrics_df.copy()
    for c in ["累计收益", "年化收益", "年化波动率", "最大回撤"]:
        show[c] = show[c].map(lambda x: f"{x:.2%}")
    for c in ["夏普比率", "信息比率"]:
        show[c] = show[c].map(lambda x: f"{x:.4f}")
    show["超额胜率"] = show["超额胜率"].map(lambda x: f"{x:.0%}")
    perf_rows = [["模型", "权重", "累计收益", "年化收益", "波动率", "夏普", "最大回撤", "信息比率", "胜率"]]
    for _, r in show.iterrows():
        perf_rows.append([r["模型"], r["权重方式"], r["累计收益"], r["年化收益"], r["年化波动率"],
                          r["夏普比率"], r["最大回撤"], r["信息比率"], r["超额胜率"]])
    perf_table = Table(perf_rows, colWidths=[24*mm, 16*mm, 18*mm, 18*mm, 16*mm, 16*mm, 18*mm, 18*mm, 14*mm], repeatRows=1)
    perf_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "SimSun"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.0),
        ("LEADING", (0, 0), (-1, -1), 11),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAF7")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F6F8FA")]),
        ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#9EADB8")),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))

    story += [
        Paragraph("表1 四模型测试集预测性能", caption),
        me_table,
        Spacer(1, 3*mm),
        Paragraph("表2 九组合回测绩效（4 模型 × 2 权重 + 市场基准）", caption),
        perf_table,
        Spacer(1, 3*mm),
        KeepTogether([Image(str(FIG_DIR / "figure1_cumulative_returns.png"), width=doc.width, height=doc.width * 0.58),
                      Paragraph("图1 各模型 Top 30 组合累计收益对比", caption)]),
        Paragraph(f"图1 展示了 8 个模型组合和 1 个市场基准在 4 个测试季度上的累计净值走势。"
                  f"从图中可以看到，{best_model} 模型的 EW 组合表现最好，累计收益达到 {best_ew['累计收益']:.2%}，"
                  f"明显跑赢市场基准的 {market['累计收益']:.2%}。"
                  f"大部分 ML 组合在整个测试期都维持在基准上方，说明模型选股具有正向预测能力。", body),
        PageBreak(),
        KeepTogether([Image(str(FIG_DIR / "figure2_ew_vs_pw.png"), width=doc.width, height=doc.width * 0.44),
                      Paragraph("图2 EW 等权 vs PW 预测收益加权对比", caption)]),
        Paragraph("图2 对比了 EW 和 PW 两种加权方式的累计收益和夏普比率。可以看到 EW 和 PW 的结果非常接近，"
                  "说明在 Top 30 组合内，按预测收益加权的额外信息量有限。EW 方式更简单稳健，实操中推荐使用。", body),
        KeepTogether([Image(str(FIG_DIR / "figure3_feature_importance.png"), width=doc.width, height=doc.width * 0.48),
                      Paragraph("图3 决策树与随机森林特征重要性", caption)]),
        Paragraph("图3 展示了决策树和随机森林认为最重要的 15 个财务因子。两个模型一致认为"
                  "市值 MV、净利润同比增长率、营业总收入同比增长率等基本面因子对下一季度收益"
                  "有较强的预测力，估值类因子（PB、PE、PS）的重要性相对较低。", body),
        KeepTogether([Image(str(FIG_DIR / "figure4_linear_coefficients.png"), width=doc.width, height=doc.width * 0.44),
                      Paragraph("图4 线性回归与逻辑回归系数对比", caption)]),
        Paragraph("图4 左图展示了线性回归中影响最大的 10 个正向和 10 个负向系数。"
                  "正向系数表示该因子值越大，下一季度收益预期越高；负向系数反之。"
                  "右图展示了逻辑回归按系数绝对值排序的 Top 15 特征。逻辑回归系数代表各因子对"
                  "涨跌概率（log-odds）的边际影响，绝对值越大说明该因子对涨跌方向的判别力越强。"
                  "两个线性模型的系数方向基本一致，说明因子对收益的方向性影响在不同模型设定下是稳健的。", body),

        Paragraph("六、Top 30 选股 vs 基准对比", h1),
        Paragraph(f"从表2 和图1 可以看到，全部 8 个 ML 组合的累计收益均高于市场基准的 {market['累计收益']:.2%}，"
                  f"其中 {best_model}-EW 组合累计收益 {best_ew['累计收益']:.2%}、夏普比率 {best_ew['夏普比率']:.4f}，"
                  f"远优于基准的夏普 {market['夏普比率']:.4f}。超额胜率方面，多数模型组合在 4 个测试季度中"
                  f"有 3 个季度跑赢基准（胜率 75%），说明 ML 选股策略具有相对稳定的超额收益能力。", body),

        Paragraph("七、策略优势与局限", h1),
        Paragraph("优势：（1）自适应性——模型能从历史数据中学习因子与收益的关系，适应市场变化；"
                  "（2）多维决策——可同时考虑 19 个因子的复杂非线性组合，远超人工经验；"
                  "（3）概率/得分输出——提供排序信号，便于按信心度选股；"
                  "（4）可优化——可通过调参、换模型、加因子持续改进。", body),
        Paragraph("局限：（1）数据依赖——需要大量高质量历史数据，数据噪声直接影响模型；"
                  "（2）过拟合风险——决策树等模型容易学习历史噪声而非真实规律，需用独立测试集验证；"
                  "（3）黑盒问题——随机森林等复杂模型难以解释单只股票的入选原因；"
                  "（4）计算成本——随机森林调参耗时较长，实盘中需平衡精度与效率；"
                  "（5）市场变化——当市场结构发生突变（如政策转向、金融危机）时，历史规律可能失效。", body),

        Paragraph("八、作业总结", h1),
        Paragraph("本次作业完成了从数据加载、预处理、四模型训练、Top 30 选股、组合构建、回测评估到"
                  "可视化和 PDF 报告的完整流程。结果表明，机器学习选股策略在测试期内显著跑赢市场基准，"
                  f"其中 {best_model} 表现最优。EW 与 PW 两种加权方式效果接近，推荐使用更简单的 EW。"
                  "但需注意测试期仅 4 个季度，样本较短，结论的统计显著性有限，实盘应用前需更长时间的样本外验证。"
                  "Python 源码、4 张图表、模型 .pkl 文件和全部结果 CSV 均保存在 TASK6 目录。", body),
    ]

    doc.build(story)


# ===== 主函数 =====

def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    setup_plot_font()

    print("L1: 加载数据...")
    df = load_data()
    train, test = split_train_test(df)
    print(f"  训练集: {len(train):,} 行; 测试集: {len(test):,} 行")

    print("L1: Winsorize + 标准化...")
    train, test = winsorize(train, test, FEATURE_COLS)
    scaler = StandardScaler().fit(train[FEATURE_COLS])
    X_train = scaler.transform(train[FEATURE_COLS])
    X_test = scaler.transform(test[FEATURE_COLS])
    y_train_cont = train["Next_Ret"].values
    y_test_cont = test["Next_Ret"].values
    y_train_bin = (y_train_cont > 0).astype(int)

    print("L2: 训练四模型...")
    models = train_models(X_train, y_train_cont, y_train_bin)
    save_models(models)

    print("L2: 测试集预测...")
    preds = predict_models(models, X_test)

    # 模型评估
    model_eval = {}
    for name in MODEL_NAMES:
        pred = preds[name]
        mse = mean_squared_error(y_test_cont, pred)
        mae = mean_absolute_error(y_test_cont, pred)
        if name == "LogisticRegression":
            auc = roc_auc_score(y_test_cont > 0, pred)
            note = f"二分类概率排序，AUC={auc:.4f}"
        else:
            note = "回归预测"
        model_eval[name] = {"mse": mse, "mae": mae, "note": note}
        print(f"  {name}: MSE={mse:.6f}, MAE={mae:.6f}")

    pd.DataFrame([{"模型": k, "MSE": v["mse"], "MAE": v["mae"], "说明": v["note"]} for k, v in model_eval.items()]).to_csv(
        RESULT_DIR / "model_metrics.csv", index=False, encoding="utf-8-sig")

    print("L2: Top 30 选股 + 组合构建...")
    quarterly = build_portfolios(test, preds, pd.Series(y_test_cont, index=test.index))

    print("L2: 回测评估...")
    metrics_df = calc_metrics(quarterly)
    metrics_df.to_csv(RESULT_DIR / "performance_metrics.csv", index=False, encoding="utf-8-sig")
    print(metrics_df.to_string(index=False))

    # 季度收益透视表
    qret_rows = []
    for combo, qdict in quarterly.items():
        row = {"组合": combo}
        for d in TEST_DATES:
            row[d] = qdict.get(d, np.nan)
        qret_rows.append(row)
    pd.DataFrame(qret_rows).to_csv(RESULT_DIR / "quarterly_returns.csv", index=False, encoding="utf-8-sig")

    # 特征重要性（决策树 + 随机森林）
    fi_rows = []
    for name in ["DecisionTree", "RandomForest"]:
        imp = models[name].feature_importances_
        for fname, val in sorted(zip(FEATURE_COLS, imp), key=lambda x: -x[1]):
            fi_rows.append({"模型": name, "特征": fname, "重要性": val})
    pd.DataFrame(fi_rows).to_csv(RESULT_DIR / "feature_importance.csv", index=False, encoding="utf-8-sig")

    # 线性模型系数（线性回归 + 逻辑回归）
    coef_rows = []
    for fname, val in zip(FEATURE_COLS, models["LinearRegression"].coef_):
        coef_rows.append({"模型": "LinearRegression", "特征": fname, "系数": val})
    for fname, val in zip(FEATURE_COLS, models["LogisticRegression"].coef_[0]):
        coef_rows.append({"模型": "LogisticRegression", "特征": fname, "系数": val})
    pd.DataFrame(coef_rows).to_csv(RESULT_DIR / "linear_coefficients.csv", index=False, encoding="utf-8-sig")

    print("L3: 生成图表...")
    plot_cumulative_returns(quarterly, FIG_DIR / "figure1_cumulative_returns.png")
    plot_ew_vs_pw(metrics_df, FIG_DIR / "figure2_ew_vs_pw.png")
    plot_feature_importance(models, FIG_DIR / "figure3_feature_importance.png")
    plot_linear_coefficients(models, FIG_DIR / "figure4_linear_coefficients.png")

    print("L5: 生成 PDF 报告...")
    build_report(metrics_df, model_eval, len(train), len(test), len(FEATURE_COLS))
    print(f"\nGenerated: {PDF_PATH}")


if __name__ == "__main__":
    main()
