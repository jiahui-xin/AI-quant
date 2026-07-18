# TASK6 实现说明：机器学习选股模型——季度 Top 30 策略

> 配套文件：`TASK6/task6_ml_stock_selection.py` · `TASK6/辛家辉TASK6.pdf` · `TASK6/figures/` · `TASK6/results/` · `TASK6/models/`
> 数据集：`material/model_data.csv`（39,616 条 × 19 个财务因子，标签 Next_Ret 为下一季度收益）
> 完成日期：2026年7月18日

---

## 一、作业目标

用 A 股截面财务因子数据训练多种机器学习模型，预测股票下一季度收益，**每季度按预测得分挑选 Top 30 股票**构建投资组合，对比四模型（线性回归、逻辑回归、决策树、随机森林）的等权（EW）和预测收益加权（PW）组合与市场基准的收益、风险、夏普比率、最大回撤、信息比率等指标，评估机器学习选股策略的有效性。

## 二、整体实现流程

```
   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
   │ 1. 数据加载   │ → │ 2. 四模型训练 │ → │ 3. Top 30 选股│ → │ 4. 组合构建   │
   │  CSV + 19因子 │   │ LR/LR/DT/RF │   │  按预测分排序 │   │ EW / PW 两种 │
   └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
                                                                        │
                                                                        ▼
   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
   │ 8. 输出 PDF 报告│ ← │ 7. 生成图表  │ ← │ 6. 回测评估  │ ← │ 5. 聚合季度  │
   │  + 网站集成    │   │ 4 张 PNG     │   │ 7 项指标     │   │ 收益序列     │
   └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
```

## 三、详细步骤说明

### 3.1 数据加载与时间划分

```python
df = pd.read_csv("material/model_data.csv", encoding="utf-8-sig")
df = df.dropna(subset=FEATURE_COLS + ["Next_Ret"])

TRAIN_DATES = ["2020/3/31", "2020/6/30", "2020/9/30", "2020/12/31",
               "2021/3/31", "2021/6/30"]  # 6 个季度
TEST_DATES  = ["2021/9/30", "2021/12/31", "2022/3/31", "2022/6/30"]  # 4 个季度

train = df[df["Date"].isin(TRAIN_DATES)]
test  = df[df["Date"].isin(TEST_DATES)]
```

- 总样本 39,616 条；训练 22,855 条（6 季度），测试 16,761 条（4 季度）
- 19 个财务因子 + Date + Code + Next_Ret
- **关键陷阱**：字符串比较 `"2021/12/31" >= "2021/7/1"` 会因为 `'1' < '7'` 而失败，必须用 `isin()` 列表匹配

### 3.2 数据预处理

```python
# Winsorize 缩尾（消除极端值）
for c in FEATURE_COLS:
    lo, hi = train[c].quantile(0.01), train[c].quantile(0.99)
    train[c] = train[c].clip(lo, hi)
    test[c]  = test[c].clip(lo, hi)

# StandardScaler 标准化
scaler = StandardScaler().fit(train[FEATURE_COLS])
X_train = scaler.transform(train[FEATURE_COLS])
X_test  = scaler.transform(test[FEATURE_COLS])
```

- Next_Ret 最大值 6.4，最小值 -0.8，右偏分布，需要缩尾
- 标准化使各因子量纲统一

### 3.3 四模型训练

```python
models = {
    "LinearRegression":  LinearRegression().fit(X_train, y_train),
    "LogisticRegression": LogisticRegression(C=0.01, max_iter=500).fit(X_train, y_train > 0),
    "DecisionTree":      DecisionTreeRegressor(max_depth=8, min_samples_leaf=50).fit(X_train, y_train),
    "RandomForest":      RandomizedSearchCV(...).fit(X_train, y_train).best_estimator_,
}
```

- **逻辑回归**：把 Next_Ret 转为二分类标签（>0 为涨），输出正类概率作为排序分数
- **决策树**：max_depth=8 控制复杂度
- **随机森林**：n_estimators 范围 [50, 80, 100]，max_depth [6, 8, 10]，RandomizedSearchCV 4 轮搜索

### 3.4 Top 30 选股与组合构建

每季度在测试集上：
1. 按模型预测得分排序
2. 取前 30 名
3. 计算 EW（等权，权重 1/30）和 PW（按预测收益加权，权重 ∝ 预测收益）组合的实际收益
4. 输出每只股票的 Predicted、Actual_Return、Weight_EW、Weight_PW 到 `portfolios/*.csv`

### 3.5 回测评估指标

- **累计收益**：4 季度收益连乘 - 1
- **年化收益**：季度均值 × 4
- **年化波动率**：季度标准差 × √4
- **夏普比率**：年化收益 / 年化波动率
- **最大回撤**：累计净值最大峰谷跌幅
- **信息比率**：超额收益均值 / 标准差 × √4
- **超额胜率**：超越市场基准的季度占比

### 3.6 实测结果

| 模型 | 权重 | 累计收益 | 夏普 | 最大回撤 | 信息比率 | 超额胜率 |
|---|---|---|---|---|---|---|
| Market | -- | -6.35% | -0.31 | -15.91% | 0 | 0% |
| LinearRegression | EW | 13.62% | 0.80 | -5.42% | 1.13 | 75% |
| LogisticRegression | **EW** | **20.14%** | **1.19** | -3.22% | 1.33 | 75% |
| DecisionTree | EW | -1.21% | -0.01 | -10.03% | 0.36 | 50% |
| RandomForest | EW | 11.86% | 0.88 | -5.55% | 2.21 | 75% |

**最佳模型**：LogisticRegression-EW（夏普 1.19，累计收益 20.14%）
- 所有 ML 组合（除决策树）均跑赢市场基准
- 多数模型 4 季度中 3 季度超越基准（胜率 75%）
- EW 与 PW 效果接近，EW 略优

## 四、目录结构

```text
TASK6/
├── task6_ml_stock_selection.py    # 完整 Python 脚本
├── 辛家辉TASK6.pdf                # 最终 PDF 报告
├── figures/
│   ├── figure1_cumulative_returns.png   # 图1 各组合累计收益对比
│   ├── figure2_ew_vs_pw.png            # 图2 EW vs PW 对比
│   ├── figure3_feature_importance.png   # 图3 决策树/随机森林特征重要性
│   └── figure4_linear_coefficients.png  # 图4 线性回归系数
├── models/
│   ├── LinearRegression.pkl
│   ├── LogisticRegression.pkl
│   ├── DecisionTree.pkl
│   └── RandomForest.pkl
└── results/
    ├── model_metrics.csv        # 四模型 MSE/MAE
    ├── performance_metrics.csv  # 9 组合绩效
    ├── quarterly_returns.csv    # 季度收益透视表
    ├── feature_importance.csv   # DT + RF 特征重要性
    ├── linear_coefficients.csv  # 线性回归系数
    └── portfolios/              # 16 个组合明细（4 模型 × 2 权重 × 4 季度，但 EW/PW 合并为同一 CSV）
```

## 五、运行环境

- Python 3.13.12（managed venv）
- 依赖：numpy、pandas、matplotlib、scikit-learn
- 中文字体：`/Users/jiahuixin/Library/Fonts/SimSun.ttf`

## 六、复现方式

```bash
# 在项目根目录下
python3 TASK6/task6_ml_stock_selection.py
```

脚本会重新加载数据、训练模型、写出 4 张 PNG、4 个模型 .pkl、5+ 个结果 CSV 与最终的 `TASK6/辛家辉TASK6.pdf`。
