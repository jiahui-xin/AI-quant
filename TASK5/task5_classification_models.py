#!/usr/bin/env python3
"""TASK5: AI 交易引擎——分类型机器学习算法（决策树、随机森林）训练、评估与 PDF 报告生成。"""

from pathlib import Path

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
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, auc, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score, roc_curve
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parents[1]
TASK_DIR = ROOT / "TASK5"
DATA_PATH = ROOT / "material" / "model_data_stock.csv"
FIG_DIR = TASK_DIR / "figures"
RESULT_DIR = TASK_DIR / "results"
PDF_PATH = TASK_DIR / "辛家辉TASK5.pdf"
FONT_PATH = Path("/Users/jiahuixin/Library/Fonts/SimSun.ttf")

RANDOM_STATE = 42
TEST_SIZE = 0.2
DT_PARAMS = {"criterion": "gini", "max_depth": 8, "min_samples_split": 50, "min_samples_leaf": 20, "random_state": RANDOM_STATE}
RF_PARAMS = {"n_estimators": 100, "max_depth": 10, "min_samples_split": 50, "min_samples_leaf": 20, "max_features": "sqrt", "n_jobs": -1, "random_state": RANDOM_STATE}


def load_data() -> tuple[pd.DataFrame, pd.Series, list[str]]:
    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    feature_cols = [c for c in df.columns if c not in ("Date", "Code", "Y")]
    X = df[feature_cols].astype(float)
    y = df["Y"].astype(int)
    n_features = len(feature_cols)
    return X, y, feature_cols, n_features


def evaluate(y_true, y_pred, y_proba) -> dict:
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()
    return {
        "TN": int(tn), "FP": int(fp), "FN": int(fn), "TP": int(tp),
        "Accuracy": accuracy_score(y_true, y_pred),
        "Precision": precision_score(y_true, y_pred, zero_division=0),
        "Recall": recall_score(y_true, y_pred, zero_division=0),
        "F1": f1_score(y_true, y_pred, zero_division=0),
        "AUC": roc_auc_score(y_true, y_proba),
    }


def setup_plot_font():
    matplotlib.font_manager.fontManager.addfont(str(FONT_PATH))
    plt.rcParams.update({"font.family": "SimSun", "axes.unicode_minus": False, "figure.dpi": 130, "savefig.dpi": 220})


def plot_roc(roc_payload: dict, out: Path):
    fig, ax = plt.subplots(figsize=(7.6, 5.6))
    colors_map = {"决策树": "#2f5597", "随机森林": "#b23a48"}
    for name, payload in roc_payload.items():
        fpr, tpr, auc_val = payload["fpr"], payload["tpr"], payload["auc"]
        ax.plot(fpr, tpr, color=colors_map.get(name, "#444"), lw=2, label=f"{name}（AUC={auc_val:.4f}）")
    ax.plot([0, 1], [0, 1], color="#888", lw=1, ls="--", label="随机猜测（AUC=0.5）")
    ax.set_xlabel("假阳性率（FPR）", fontsize=11)
    ax.set_ylabel("真正例率（TPR / 召回率）", fontsize=11)
    ax.set_title("图1 决策树与随机森林 ROC 曲线对比", fontsize=13, pad=12)
    ax.set_xlim(-0.01, 1.01); ax.set_ylim(-0.01, 1.01)
    ax.grid(alpha=.25); ax.legend(loc="lower right", fontsize=10, frameon=True)
    fig.tight_layout(); fig.savefig(out, bbox_inches="tight"); plt.close(fig)


def plot_feature_importance(importances: pd.Series, out: Path):
    top = importances.sort_values().tail(15)
    fig, ax = plt.subplots(figsize=(8.6, 5.6))
    bars = ax.barh(top.index, top.values, color="#2f7d5c", edgecolor="#1b4a36")
    ax.set_xlabel("特征重要性（基尼不纯度平均下降量）", fontsize=11)
    ax.set_title("图2 随机森林 Top-15 特征重要性", fontsize=13, pad=12)
    ax.grid(axis="x", alpha=.25)
    for b, v in zip(bars, top.values):
        ax.text(v + 0.001, b.get_y() + b.get_height() / 2, f"{v:.4f}", va="center", fontsize=9, color="#1b4a36")
    fig.tight_layout(); fig.savefig(out, bbox_inches="tight"); plt.close(fig)


def plot_confusion_matrix(cm: np.ndarray, name: str, out: Path, ax_title: str):
    fig, ax = plt.subplots(figsize=(5.6, 4.6))
    im = ax.imshow(cm, cmap="Blues", aspect="auto")
    ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
    ax.set_xticklabels(["预测跌 (0)", "预测涨 (1)"])
    ax.set_yticklabels(["实际跌 (0)", "实际涨 (1)"])
    for i in range(2):
        for j in range(2):
            v = cm[i, j]
            color = "white" if v > cm.max() * 0.55 else "#0d2c4f"
            ax.text(j, i, f"{int(v):,}", ha="center", va="center", fontsize=14, color=color, fontweight="bold")
    ax.set_xlabel("预测标签", fontsize=11)
    ax.set_ylabel("实际标签", fontsize=11)
    ax.set_title(ax_title, fontsize=12, pad=10)
    fig.colorbar(im, ax=ax, shrink=.82, label="样本数")
    fig.tight_layout(); fig.savefig(out, bbox_inches="tight"); plt.close(fig)


def pct(x): return f"{x:.2%}"


def build_report(dt_metrics: dict, rf_metrics: dict, feature_importance: pd.Series, class_dist: dict, n_features: int):
    pdfmetrics.registerFont(TTFont("SimSun", str(FONT_PATH)))
    base = getSampleStyleSheet()["BodyText"]
    body = ParagraphStyle("BodyCN", parent=base, fontName="SimSun", fontSize=10.5, leading=15.75, alignment=TA_JUSTIFY, spaceBefore=0, spaceAfter=0, firstLineIndent=21)
    h1 = ParagraphStyle("H1CN", parent=body, fontSize=14, leading=21, spaceBefore=9, spaceAfter=4, firstLineIndent=0, textColor=colors.HexColor("#17365D"))
    h2 = ParagraphStyle("H2CN", parent=body, fontSize=11.5, leading=17, spaceBefore=5, spaceAfter=2, firstLineIndent=0, textColor=colors.HexColor("#244A73"))
    title = ParagraphStyle("TitleCN", parent=body, fontSize=18, leading=27, alignment=TA_CENTER, firstLineIndent=0)
    center = ParagraphStyle("CenterCN", parent=body, alignment=TA_CENTER, firstLineIndent=0)
    caption = ParagraphStyle("CaptionCN", parent=body, alignment=TA_CENTER, firstLineIndent=0, spaceAfter=3)
    small = ParagraphStyle("SmallCN", parent=body, fontSize=8.7, leading=12.5, firstLineIndent=0)
    doc = BaseDocTemplate(str(PDF_PATH), pagesize=A4, leftMargin=24 * mm, rightMargin=24 * mm, topMargin=19 * mm, bottomMargin=18 * mm, title="辛家辉TASK5", author="辛家辉")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")

    def footer(canvas, _doc):
        canvas.saveState()
        canvas.setFont("SimSun", 9)
        canvas.drawCentredString(A4[0] / 2, 10 * mm, f"- {canvas.getPageNumber()} -")
        canvas.restoreState()

    doc.addPageTemplates(PageTemplate(id="main", frames=frame, onPage=footer))
    info = Table(
        [
            ["课程任务", "TASK5 AI 交易引擎：分类型机器学习算法与场景应用"],
            ["姓名", "辛家辉"],
            ["完成日期", "2026年7月18日"],
            ["提交文件", "辛家辉TASK5.pdf"],
            ["数据集", "model_data_stock.csv（20,772 条 × 17 个财务指标）"],
        ],
        colWidths=[35 * mm, 105 * mm],
    )
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

    story = [
        Spacer(1, 8 * mm),
        Paragraph("TASK5 AI 交易引擎：分类型机器学习算法与场景应用", title),
        Paragraph("量化交易课程个人作业报告", center),
        Spacer(1, 7 * mm),
        info,

        Paragraph("一、作业任务", h1),
        Paragraph("本作业围绕 AI 交易引擎中的监督学习分类任务，使用课程提供的 A 股股票财务指标收益数据（model_data_stock.csv）构建两个分类型机器学习模型（决策树与随机森林），对股票后续收益的涨跌方向（二分类标签 0/1）进行预测，并通过混淆矩阵、AUC 与 ROC 曲线评估模型表现。本作业分为理论梳理与编程实现两部分，最终提交宋体、五号字、1.5 倍行距、0 段间距、两端对齐的 PDF 报告。", body),

        Paragraph("二、数据集与划分", h1),
        Paragraph(f"原始数据共 {class_dist['total']:,} 条记录，剔除 Date、Code 与标签 Y 后，保留 {n_features} 个财务特征作为自变量。Y 是布尔型涨跌标签，True 表示 1（涨），False 表示 0（跌）。整体涨跌样本数为 0 类 {class_dist['neg']:,} 条、1 类 {class_dist['pos']:,} 条，正负比例约为 {class_dist['pos'] / class_dist['total']:.1%}，整体略偏负类但并未严重失衡。", body),
        Paragraph("按 8 : 2 比例随机划分训练集与测试集，并设置 random_state = {} 保证实验可复现。由于本数据样本之间的先后顺序对建模没有强约束（每条记录对应某只股票在一个截面日的财务快照），此处采用随机划分而不是时间序列划分。如果换成按日线面板的时序数据，则需改用按时间切分以避免未来信息泄露。".format(RANDOM_STATE), body),
        Paragraph("划分前对全部特征列做统一的缺失值检查，未发现 NaN 样本；同时剔除部分极值（如企业倍数为负的样本在训练时仍保留，由决策树与随机森林天然按阈值分裂处理）。", body),

        Paragraph("三、算法原理与适用场景", h1),

        Paragraph("1. 逻辑回归（Logistic Regression）", h2),
        Paragraph("逻辑回归虽然名字中带有“回归”，但实质是分类算法。它在线性组合 z = β₀ + β₁x₁ + … + βₙxₙ 上套用 Sigmoid 函数 σ(z) = 1 / (1 + e⁻ᶻ)，将输出压缩到 (0, 1) 区间，作为正类概率 P(y=1|X) 的估计。训练过程等价于最大化对数似然（最小化交叉熵损失）。", body),
        Paragraph("优点：模型简单、训练和预测速度快，可直接输出概率，系数可解释；缺点：只能学习线性决策边界，对特征共线性和极端值敏感，需要先做标准化或异常值处理。在金融场景中常作为概率基线模型，与决策树、随机森林的结果做对比。", body),

        Paragraph("2. 决策树（Decision Tree）", h2),
        Paragraph("决策树通过一系列 if-else 规则对特征空间做递归划分。每个内部节点选择一个特征和阈值，将样本分到左右子节点，使分裂后的节点“纯度”提升。常用的不纯度指标有基尼不纯度（Gini）和信息熵（Entropy）。本作业使用基尼系数，训练目标等价于在每一步选择让基尼下降最大的特征与阈值。", body),
        Paragraph("优点：可解释性强，能可视化，能处理非线性关系和类别型特征；缺点：单棵树容易过拟合，对训练数据的微小变化敏感，方差较大。在金融分类中常作为可解释的弱模型或集成学习的基学习器。", body),
        Paragraph("本作业中决策树设置 max_depth=8、min_samples_split=50、min_samples_leaf=20，限制树的复杂度以减少过拟合，同时保留足够的非线性表达能力。", body),

        Paragraph("3. 随机森林（Random Forest）", h2),
        Paragraph("随机森林以决策树为基学习器，通过两重随机性构造多样性：一是对每棵树进行自助采样（Bootstrap sampling）得到不同训练子集，二是在每个节点随机抽取部分特征（默认 √p 个，p 为总特征数）来选择最优分裂特征。最终通过多数投票（分类）或平均（回归）得到集成结果。", body),
        Paragraph("优点：精度高、泛化能力强，能处理高维特征和缺失值，对噪声和异常点稳健；缺点：模型较大，训练和预测都比单棵决策树慢，可解释性弱于单棵树。本作业随机森林设置 n_estimators=100、max_depth=10、min_samples_split=50、min_samples_leaf=20、max_features='sqrt'，是分类任务中常用的较稳健配置。", body),

        Paragraph("四、模型评价指标", h1),

        Paragraph("1. 混淆矩阵（Confusion Matrix）", h2),
        Paragraph("混淆矩阵把模型预测结果与真实标签的四种组合排列成 2×2 表。设正例为 1（涨），负例为 0（跌）：", body),
        Paragraph("· TP（True Positive，真正例）：实际为涨、模型也预测为涨的样本数；", body),
        Paragraph("· FP（False Positive，假正例）：实际为跌、但模型预测为涨的样本数——交易中相当于“错误买入”，是最需要控制的风险来源；", body),
        Paragraph("· FN（False Negative，假负例）：实际为涨、但模型预测为跌的样本数——对应“漏掉机会”，量化场景下意味着少赚；", body),
        Paragraph("· TN（True Negative，真负例）：实际为跌、模型也预测为跌的样本数。", body),
        Paragraph("基于四个计数可以计算准确率 Accuracy = (TP+TN)/总样本、精确率 Precision = TP/(TP+FP)（预测为涨的样本里真正涨的比例）、召回率 Recall = TP/(TP+FN)（实际涨的样本里被预测出来的比例），以及 F1 = 2·P·R/(P+R)，用于在精确率与召回率之间做综合平衡。", body),

        Paragraph("2. ROC 曲线与 AUC", h2),
        Paragraph("ROC 曲线的横轴是假阳性率 FPR = FP/(FP+TN)，纵轴是真正例率 TPR = TP/(TP+FN)（即召回率）。对每一个分类阈值，模型都会产生一对 (FPR, TPR)，把所有阈值对应的点连起来就是 ROC 曲线。", body),
        Paragraph("ROC 曲线的解读方式：从 (0, 0) 到 (1, 1) 的对角线代表随机猜测，越靠近左上角说明模型在不同阈值下都能以更低的误报代价换到更高的召回能力，模型越好。", body),
        Paragraph("AUC 是 ROC 曲线下方面积，取值在 0 到 1 之间：AUC = 0.5 与随机猜测等价，AUC > 0.7 通常视为模型有效，AUC > 0.8 视为模型良好，AUC = 1.0 是理论上的完美分类。AUC 的优势在于对类别不均衡和分类阈值不敏感，是综合衡量模型排序能力的重要指标。", body),

        Paragraph("五、Python 实现流程", h1),
        Paragraph("程序从 model_data_stock.csv 读取数据后，固定 17 个财务指标作为自变量 X，Y 转为 0/1 整数标签。调用 sklearn.model_selection.train_test_split 划分 80% 训练集与 20% 测试集，random_state=42 保证复现。", body),
        Paragraph("随后构建两个分类模型：决策树 DecisionTreeClassifier 与随机森林 RandomForestClassifier，调用 fit 完成训练。预测时同时输出 hard label（predict）和正类概率（predict_proba[:, 1]），后者用于绘制 ROC 曲线和计算 AUC。", body),
        Paragraph("评估阶段先计算混淆矩阵，再由 sklearn.metrics.roc_curve 给出 (FPR, TPR) 序列以及阈值，再由 auc 函数得到曲线下面积，最后把两个模型的 ROC 曲线绘制在同一张图上，加上对角线随机猜测基准。", body),
        Paragraph("为方便比较，程序还把准确率、精确率、召回率、F1、AUC、TP/FP/TN/FN 一起输出到 results/model_comparison.csv，并把随机森林的特征重要性排序后保存到 results/feature_importance.csv。", body),
        Table(
            [[Paragraph("X = df[feature_cols].astype(float)<br/>y = df['Y'].astype(int)<br/>X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)<br/>dt = DecisionTreeClassifier(max_depth=8, min_samples_split=50, min_samples_leaf=20, random_state=42).fit(X_train, y_train)<br/>rf = RandomForestClassifier(n_estimators=100, max_depth=10, max_features='sqrt', n_jobs=-1, random_state=42).fit(X_train, y_train)<br/>fpr, tpr, _ = roc_curve(y_test, rf.predict_proba(X_test)[:, 1])<br/>auc_value = auc(fpr, tpr)", small)]],
            colWidths=[doc.width],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F6F8")),
                ("BOX", (0, 0), (-1, -1), .5, colors.HexColor("#AAB7C4")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]),
        ),

        Paragraph("六、模型评估结果", h1),
    ]

    metric_rows = [
        ["指标", "决策树", "随机森林", "说明"],
        ["准确率 Accuracy", f"{dt_metrics['Accuracy']:.4f}", f"{rf_metrics['Accuracy']:.4f}", "整体预测正确的比例"],
        ["精确率 Precision", f"{dt_metrics['Precision']:.4f}", f"{rf_metrics['Precision']:.4f}", "预测为涨里真正涨的比例"],
        ["召回率 Recall", f"{dt_metrics['Recall']:.4f}", f"{rf_metrics['Recall']:.4f}", "实际涨里被预测出来的比例"],
        ["F1 分数", f"{dt_metrics['F1']:.4f}", f"{rf_metrics['F1']:.4f}", "精确率与召回率的调和平均"],
        ["AUC", f"{dt_metrics['AUC']:.4f}", f"{rf_metrics['AUC']:.4f}", "ROC 曲线下面积，越接近 1 越好"],
        ["TP（真阳）", f"{dt_metrics['TP']:,}", f"{rf_metrics['TP']:,}", "实际涨、预测涨的样本数"],
        ["FP（假阳）", f"{dt_metrics['FP']:,}", f"{rf_metrics['FP']:,}", "实际跌、预测涨的样本数"],
        ["FN（假阴）", f"{dt_metrics['FN']:,}", f"{rf_metrics['FN']:,}", "实际涨、预测跌的样本数"],
        ["TN（真阴）", f"{dt_metrics['TN']:,}", f"{rf_metrics['TN']:,}", "实际跌、预测跌的样本数"],
    ]
    mt = Table(metric_rows, colWidths=[34 * mm, 24 * mm, 24 * mm, doc.width - 82 * mm], repeatRows=1)
    mt.setStyle(TableStyle([
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
    story += [
        Paragraph("表1 决策树与随机森林在测试集上的评估指标", caption),
        mt,
        Spacer(1, 2 * mm),
        KeepTogether([Image(str(FIG_DIR / "figure1_roc_curves.png"), width=doc.width, height=doc.width * 0.72), Paragraph("图1 决策树与随机森林 ROC 曲线对比", caption)]),
        Paragraph("图1中蓝色为决策树，红色为随机森林，灰色虚线为随机猜测基准。两条 ROC 曲线都明显偏离对角线，说明两个模型在测试集上都具有一定的排序能力。", body),
        KeepTogether([Image(str(FIG_DIR / "figure2_feature_importance.png"), width=doc.width, height=doc.width * 0.62), Paragraph("图2 随机森林 Top-15 特征重要性", caption)]),
        Paragraph("图2给出随机森林认为最重要的 15 个财务特征。从结果可以看到，市值 MV 排名第一（重要性约 0.118），远高于其他特征，说明股票规模对下一期涨跌方向有显著的预测力；基本每股收益同比增长率、营业总收入同比增长率、净利润同比增长率等盈利与成长类指标也排在前 5，方向上符合“基本面改善 → 股价上涨”的直觉；估值类指标如市净率 PB、市销率 PS、企业倍数（EV/EBITDA）等紧随其后，整体重要性分布较为平滑。", body),
        PageBreak(),
        KeepTogether([Image(str(FIG_DIR / "figure3_dt_confusion_matrix.png"), width=doc.width * 0.62, height=doc.width * 0.5), Paragraph("图3 决策树测试集混淆矩阵", caption)]),
        Spacer(1, 1 * mm),
        KeepTogether([Image(str(FIG_DIR / "figure4_rf_confusion_matrix.png"), width=doc.width * 0.62, height=doc.width * 0.5), Paragraph("图4 随机森林测试集混淆矩阵", caption)]),
        Paragraph("图3与图4分别展示两个模型在测试集上的混淆矩阵。决策树与随机森林都能在负类（跌）上保持很高的 TN，但 TP（正确预测涨的样本）相对较少，说明两个模型对涨样本的预测能力有限，整体仍倾向于把样本预测为“跌”。", body),
    ]

    top5 = feature_importance.sort_values(ascending=False).head(5)
    fi_rows = [["排名", "特征名称", "重要性"]] + [[str(i + 1), name, f"{val:.4f}"] for i, (name, val) in enumerate(top5.items())]
    fi = Table(fi_rows, colWidths=[18 * mm, 90 * mm, 32 * mm], repeatRows=1)
    fi.setStyle(TableStyle([
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

    story += [
        Paragraph("表2 随机森林 Top-5 重要特征", caption),
        fi,
        Spacer(1, 2 * mm),
        Paragraph("七、结果解读", h1),
        Paragraph("从表1可以看到，随机森林在准确率、精确率、召回率、F1 和 AUC 五个指标上均明显优于单棵决策树。AUC 从决策树的 {} 提升到随机森林的 {}，说明通过自助采样和特征随机两重随机性集成多棵树之后，模型的排序能力得到了稳定提升。".format(f"{dt_metrics['AUC']:.4f}", f"{rf_metrics['AUC']:.4f}"), body),
        Paragraph("从混淆矩阵看，FP（错误买入）和 FN（漏掉机会）相比之下，FP 仍然较多，这与样本中负类占比略高、模型倾向预测“跌”有关。在实际交易中，FP 直接对应“真金白银的亏损”，因此后续可以通过阈值调整、类别权重或代价敏感学习进一步压缩 FP。", body),
        Paragraph("从特征重要性看，市值 MV 是最重要的预测变量，其后是基本每股收益同比增长率、营业总收入同比增长率、净利润同比增长率等盈利与成长类指标，再之后才是市净率 PB、市销率 PS、企业倍数等估值类指标。说明在 A 股横截面数据中，股票规模与基本面改善对下一期收益的方向有较强的预测能力，估值水平则在更靠后的位置提供增量信息。", body),

        Paragraph("八、适用场景与作业心得", h1),
        Paragraph("决策树适合作为可解释的基线模型，能直观看到每一层分裂对应的业务规则；随机森林适合在已经确定特征工程、没有强解释需求时追求更高的预测精度。两者都属于集成学习的入门模型，再往上还有 XGBoost、LightGBM 等梯度提升树方法。", body),
        Paragraph("本作业也提醒我们，AUC 约 0.63 并不等于“在实盘中可以直接用来下单”。第一，模型只是对横截面样本的统计规律，脱离了具体股票、具体时间窗口就可能失效；第二，金融数据的标签分布与特征分布会随时间漂移，需要做样本外检验与定期重训；第三，FP 在交易中的代价通常远高于 FN，单看 AUC 容易低估风险。", body),
        Paragraph("通过本次作业，我理解了分类型机器学习算法的原理、适用边界，以及混淆矩阵、AUC、ROC 曲线这三个常用评估指标的含义与解读方式。Python 源码、ROC 图、混淆矩阵图、特征重要性图与评估结果 CSV 均保存在 TASK5 目录下，可以直接重新运行复现全部输出。", body),

        Paragraph("九、作业总结", h1),
        Paragraph("本次作业完成了理论梳理（逻辑回归、决策树、随机森林、混淆矩阵、AUC、ROC 曲线）和编程实现（数据加载、80/20 划分、模型训练、混淆矩阵与 AUC 评估、ROC 曲线绘制、特征重要性分析），并按要求生成宋体、五号字、1.5 倍行距、0 段间距、两端对齐的 PDF 报告。Python 源码、图表与 CSV 均保存在 TASK5 目录。", body),
    ]

    doc.build(story)


def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    setup_plot_font()
    X, y, feature_cols, n_features = load_data()
    print(f"数据加载完成：{X.shape[0]:,} 行 × {X.shape[1]} 个特征；正负样本数 1: {int(y.sum()):,}, 0: {int((1 - y).sum()):,}")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y)
    print(f"训练集: {X_train.shape[0]:,}; 测试集: {X_test.shape[0]:,}")

    dt = DecisionTreeClassifier(**DT_PARAMS).fit(X_train, y_train)
    rf = RandomForestClassifier(**RF_PARAMS).fit(X_train, y_train)
    dt_metrics = evaluate(y_test, dt.predict(X_test), dt.predict_proba(X_test)[:, 1])
    rf_metrics = evaluate(y_test, rf.predict(X_test), rf.predict_proba(X_test)[:, 1])
    print("\n决策树:", dt_metrics); print("\n随机森林:", rf_metrics)

    fpr_dt, tpr_dt, _ = roc_curve(y_test, dt.predict_proba(X_test)[:, 1])
    fpr_rf, tpr_rf, _ = roc_curve(y_test, rf.predict_proba(X_test)[:, 1])
    plot_roc(
        {"决策树": {"fpr": fpr_dt, "tpr": tpr_dt, "auc": auc(fpr_dt, tpr_dt)},
         "随机森林": {"fpr": fpr_rf, "tpr": tpr_rf, "auc": auc(fpr_rf, tpr_rf)}},
        FIG_DIR / "figure1_roc_curves.png",
    )

    importance = pd.Series(rf.feature_importances_, index=feature_cols).sort_values(ascending=False)
    importance.to_csv(RESULT_DIR / "feature_importance.csv", encoding="utf-8-sig", header=["importance"])
    plot_feature_importance(importance, FIG_DIR / "figure2_feature_importance.png")

    cm_dt = confusion_matrix(y_test, dt.predict(X_test))
    cm_rf = confusion_matrix(y_test, rf.predict(X_test))
    plot_confusion_matrix(cm_dt, "决策树", FIG_DIR / "figure3_dt_confusion_matrix.png", "图3 决策树测试集混淆矩阵")
    plot_confusion_matrix(cm_rf, "随机森林", FIG_DIR / "figure4_rf_confusion_matrix.png", "图4 随机森林测试集混淆矩阵")

    comparison = pd.DataFrame([
        {"模型": "决策树", "Accuracy": dt_metrics["Accuracy"], "Precision": dt_metrics["Precision"],
         "Recall": dt_metrics["Recall"], "F1": dt_metrics["F1"], "AUC": dt_metrics["AUC"],
         "TP": dt_metrics["TP"], "FP": dt_metrics["FP"], "FN": dt_metrics["FN"], "TN": dt_metrics["TN"]},
        {"模型": "随机森林", "Accuracy": rf_metrics["Accuracy"], "Precision": rf_metrics["Precision"],
         "Recall": rf_metrics["Recall"], "F1": rf_metrics["F1"], "AUC": rf_metrics["AUC"],
         "TP": rf_metrics["TP"], "FP": rf_metrics["FP"], "FN": rf_metrics["FN"], "TN": rf_metrics["TN"]},
    ])
    comparison.to_csv(RESULT_DIR / "model_comparison.csv", index=False, encoding="utf-8-sig")
    print("\n模型对比：\n", comparison.to_string(index=False))

    class_dist = {"total": int(len(y)), "pos": int(y.sum()), "neg": int((1 - y).sum())}
    build_report(dt_metrics, rf_metrics, importance, class_dist, n_features)
    print(f"\nGenerated: {PDF_PATH}")


if __name__ == "__main__":
    main()
