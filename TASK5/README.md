# TASK5 实现说明：分类型机器学习算法与场景应用

> 配套文件：`TASK5/task5_classification_models.py` · `TASK5/辛家辉TASK5.pdf` · `TASK5/figures/` · `TASK5/results/`
> 数据集：`material/model_data_stock.csv`（20,772 条 × 17 个财务指标，标签 Y 为布尔型 0/1）
> 完成日期：2026年7月18日

---

## 一、作业目标

围绕 AI 交易引擎中的**监督学习分类任务**，使用课程提供的 A 股股票财务指标收益数据
（`model_data_stock.csv`）构建两个分类型机器学习模型（决策树与随机森林），对股票后续
收益的涨跌方向（二分类标签 0/1）进行预测，并通过**混淆矩阵、AUC 与 ROC 曲线**评估模型
表现。本作业分为理论梳理与编程实现两部分：

- **理论部分**：解释逻辑回归、决策树、随机森林三个分类算法的原理与适用边界；解释
  混淆矩阵（TP/FP/TN/FN）、AUC 取值范围、ROC 曲线横纵轴含义与解读方法。
- **编程部分**：在 Python 中完成数据加载、训练/测试划分、模型训练、模型评估、
  ROC 曲线绘制，并最终生成符合宋体、五号字、1.5 倍行距、0 段间距、两端对齐格式
  要求的 PDF 报告。

---

## 二、整体实现流程

```
   ┌────────────────┐   ┌────────────────┐   ┌────────────────┐   ┌────────────────┐
   │ 1. 加载分类数据 │ → │ 2. 划分训练/测试│ → │ 3. 构建并训练  │ → │ 4. 评估混淆矩阵 │
   │    (CSV → X,y) │   │   80/20 + 随机  │   │  决策树/随机森林│   │   与 AUC 值    │
   └────────────────┘   └────────────────┘   └────────────────┘   └────────────────┘
                                                                      │
                                                                      ▼
                                                            ┌────────────────┐
                                                            │ 5. 绘制 ROC 曲线│
                                                            │  并附文字解读  │
                                                            └────────────────┘
                                                                      │
                                                                      ▼
                                                            ┌────────────────┐
                                                            │ 6. 输出 PDF 报告│
                                                            │  ＋结果 CSV    │
                                                            └────────────────┘
```

完整流程由 `task5_classification_models.py` 一键执行：从读取 CSV → 划分数据集 →
训练两个分类模型 → 计算混淆矩阵和 AUC → 绘制 ROC 曲线 → 生成 4 张 PNG → 写出
`results/model_comparison.csv` 与 `results/feature_importance.csv` → 渲染
`辛家辉TASK5.pdf`。

---

## 三、详细步骤说明

### 3.1 加载分类数据集

```python
df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
feature_cols = [c for c in df.columns if c not in ("Date", "Code", "Y")]
X = df[feature_cols].astype(float)
y = df["Y"].astype(int)        # 布尔 → 0/1
```

- 数据共 20,772 条记录、20 列；剔除 `Date`、`Code`、`Y` 后保留 17 个财务特征
  作为自变量，包括市净率 PB、市盈率 PE、市销率 PS、企业倍数、MV（市值）、各类
  同比增长率等。
- `Y` 原为布尔型（True/False），`astype(int)` 后 `True=1`（涨）、`False=0`（跌）。
- 整体正负样本 8,389 : 12,383，正类占比 40.4%，略偏负类但未严重失衡。
- 缺失值检查结果：无 NaN 样本。

### 3.2 划分训练集与测试集

```python
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
```

- 比例：训练集 80% / 测试集 20%（约 16,617 : 4,155）。
- `random_state = 42` 固定随机种子，保证实验可复现。
- `stratify = y` 保证训练集和测试集的正负比例与原始数据一致。
- 由于本数据的每条记录对应某只股票在一个截面日的财务快照，样本之间没有强时间
  顺序约束，因此采用**随机划分**而不是时间序列划分。如果换成按日线面板的时序
  数据，则需改用按时间切分以避免未来信息泄露。

### 3.3 构建并训练分类模型

```python
dt = DecisionTreeClassifier(
    max_depth=8, min_samples_split=50, min_samples_leaf=20, random_state=42
).fit(X_train, y_train)

rf = RandomForestClassifier(
    n_estimators=100, max_depth=10, min_samples_split=50, min_samples_leaf=20,
    max_features="sqrt", n_jobs=-1, random_state=42
).fit(X_train, y_train)
```

- **决策树**：基尼不纯度、最大深度 8、最小分裂样本 50、最小叶节点样本 20。
- **随机森林**：100 棵树、最大深度 10、`max_features="sqrt"` 在每个节点随机抽取
  √17 ≈ 4 个特征进行分裂，并行训练（`n_jobs=-1`）。
- 两个模型都设置 `random_state=42`，保证可复现。

### 3.4 模型评估

```python
y_proba = model.predict_proba(X_test)[:, 1]    # 正类概率
y_pred  = model.predict(X_test)                 # 0/1 预测标签
cm = confusion_matrix(y_test, y_pred)           # 2×2 混淆矩阵
auc_value = roc_auc_score(y_test, y_proba)      # AUC
```

评估维度包括：

- **混淆矩阵**：得到 TP / FP / FN / TN 四个计数；
- **准确率 Accuracy** = (TP+TN) / 总样本；
- **精确率 Precision** = TP / (TP+FP)；
- **召回率 Recall** = TP / (TP+FN)；
- **F1 分数** = 2·P·R / (P+R)；
- **AUC**（ROC 曲线下面积）：取值 0~1，越接近 1 排序能力越强。

最终评估结果（测试集 4,155 条）：

| 指标        | 决策树 | 随机森林 |
| ----------- | ------ | -------- |
| 准确率      | 0.5983 | 0.6224   |
| 精确率      | 0.5042 | 0.5639   |
| 召回率      | 0.3224 | 0.2867   |
| F1 分数     | 0.3933 | 0.3801   |
| AUC         | 0.5848 | 0.6278   |
| TP / FP / FN / TN | 541 / 532 / 1137 / 1945 | 481 / 372 / 1197 / 2105 |

随机森林在准确率、精确率、AUC 三项上优于决策树，但召回率低于决策树，说明随机森林
倾向更保守的预测（更少报“涨”但更准）。两个模型整体 AUC 都在 0.6 上下，离实盘可用
还有距离，主要受限于横截面数据的信噪比本身。

### 3.5 绘制 ROC 曲线

```python
fpr, tpr, _ = roc_curve(y_test, y_proba)
auc_value   = auc(fpr, tpr)
```

- 横轴：假阳性率 FPR = FP/(FP+TN)；
- 纵轴：真正例率 TPR = TP/(TP+FN)；
- 对角线：随机猜测基准（AUC = 0.5）；
- 曲线越靠近左上角，模型排序能力越强。

**ROC 曲线解读**（图1）：

两条 ROC 曲线均明显偏离对角线，说明决策树和随机森林在测试集上都具有超过随机猜测
的排序能力。随机森林（红线）整体上包住决策树（蓝线），AUC 也更高（0.6278 vs 0.5848），
验证了集成学习的提升效果。但两条曲线都距离理想的左上角 (0, 1) 较远，说明在 17 个
截面财务特征上做横截面涨跌分类的信号相对有限。

特征重要性（图2）显示：市值 MV（0.118）> 基本每股收益同比增长率（0.093）> 营业
总收入同比增长率（0.087）> 市净率 PB（0.075）> 净利润同比增长率（0.070）。说明
**股票规模 + 基本面改善**是横截面涨跌方向的主要驱动因素，估值类指标（PB、PS、
企业倍数等）提供增量信息。

---

## 四、目录结构

```text
TASK5/
├── task5_classification_models.py     # 完整 Python 脚本
├── 辛家辉TASK5.pdf                    # 最终 PDF 报告
├── figures/
│   ├── figure1_roc_curves.png         # 图1 决策树与随机森林 ROC 曲线对比
│   ├── figure2_feature_importance.png # 图2 随机森林 Top-15 特征重要性
│   ├── figure3_dt_confusion_matrix.png# 图3 决策树测试集混淆矩阵
│   └── figure4_rf_confusion_matrix.png# 图4 随机森林测试集混淆矩阵
└── results/
    ├── model_comparison.csv           # 两个模型在测试集上的指标汇总
    └── feature_importance.csv         # 随机森林的特征重要性排序
```

## 五、运行环境与依赖

- Python：3.13.12（managed）
- 主要依赖：`pandas`、`numpy`、`matplotlib`、`scikit-learn`、`reportlab`
- 中文字体：`/Users/jiahuixin/Library/Fonts/SimSun.ttf`（由 `reportlab.pdfbase.ttfonts.TTFont`
  注册为 `SimSun`）

## 六、复现方式

```bash
# 在项目根目录 /Users/jiahuixin/Downloads/AI-quant 下
python3 TASK5/task5_classification_models.py
```

脚本会重新加载数据、训练模型、写出 4 张 PNG、2 个结果 CSV 与最终的
`TASK5/辛家辉TASK5.pdf`，所有输出均带有 `random_state=42` 的可复现控制。
