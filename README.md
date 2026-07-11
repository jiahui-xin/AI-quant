# AI-quant 课程任务站点

本仓库使用一个首页管理全部课程任务，每个任务保留独立网页和独立提交目录，共享数据与前端资源统一存放。

## 目录约定

```text
AI-quant/
├── index.html                 # 课程任务总入口
├── task1.html                 # TASK1 展示页面
├── task2.html                 # TASK2 展示页面
├── task3.html                 # TASK3 展示页面
├── TASK1/                     # TASK1 提交物
│   └── 辛家辉TASK1.pdf
├── TASK2/                     # TASK2 提交物与结果
│   ├── 辛家辉TASK2.pdf
│   └── results/
├── TASK3/                     # TASK3 报告、源码、图表与结果
│   ├── 辛家辉TASK3.pdf
│   ├── task3_moving_average_strategy.py
│   ├── figures/
│   └── results/
└── assets/                    # 各任务共享的样式、脚本和原始行情数据
    ├── tasks.js               # 首页任务清单
    ├── portal.js              # 首页任务卡片生成逻辑
    ├── styles.css
    └── ...
```

## 新增后续任务

新增 TASK4、TASK5 时沿用以下步骤：

1. 新建 `TASK4/`，保存 PDF、源码、图表和结果文件。
2. 新建 `task4.html`，沿用现有任务页的导航、页头和页脚。
3. 如需独立交互逻辑，在 `assets/` 下新增 `task4_app.js`。
4. 在 `assets/tasks.js` 中增加一条任务配置，首页会自动生成新任务卡片。
5. 在已有任务页顶部导航中加入 TASK4 入口。

共享行情数据继续放在 `assets/`，任务特有的结果放在对应 `TASKN/` 目录，避免重复文件和目录含义混乱。
