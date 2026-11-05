# 综合实验 1《文本分析》—— 工程目录与使用说明

本目录是综合实验 1 的代码与产物目录。原始数据仍保留在 `D:\DSH-Workspaces\数据科学\`，不复制、不修改。

## 0. 仓库说明（GitHub）

- 本仓库只包含**源码、notebook 与结果图表**；原始数据（约 1.8 GB）与分词缓存（约 359 MB）体积过大，未纳入仓库。
- 数据来源：大众点评商户点评数据集 `yf_dianping`（ChineseNlpCorpus），下载与字段说明见
  <https://github.com/SophonPlus/ChineseNlpCorpus/blob/master/datasets/yf_dianping/intro.ipynb>。
- 复现时请把 `preprocessed_ratings.csv`、`restaurants.csv`、`links.csv` 放到本地数据目录，并按需修改 `src/config.py` 的 `DATA_DIR`。
- 实验报告与 PPT 作为课程材料单独提交，不在本仓库内；随机种子为 42，运行顺序见第 4 节。

## 1. 环境

- 解释器：`C:\mlenv\Scripts\python.exe`（Python 3.13.7）
- 关键库：pandas 3.0.5 / numpy 2.5.3 / scikit-learn 1.9.1 / scipy 1.18.1 /
  matplotlib 3.11.1 / seaborn 0.13.2 / jieba 0.42.1 / wordcloud 1.9.6 / joblib 1.6.0 / JupyterLab 4.6.3
- Jupyter 内核：**Python (mlenv)**
- 中文字体：`C:\Windows\Fonts\msyh.ttc`

## 2. 目录结构

```
综合实验1/
├─ src/                 复用代码 + 数据生产脚本
│  ├─ config.py         路径、随机种子、字体、口径常量
│  ├─ data_utils.py     读取、3.6 伪值掩码恢复、标签编码
│  ├─ text_utils.py     清洗、jieba 分词、停用词（多进程 worker 初始化）
│  ├─ agg_utils.py      商户聚合、Wilson 下界、周聚合与滚动
│  ├─ model_utils.py    TF-IDF/Count 特征、模型训练评估、推理
│  ├─ viz_utils.py      中文字体、词云、柱状图、周趋势、雷达图
│  ├─ build_rest_agg.py 生成 output/tables/rest_agg.csv（241,360 行）
│  ├─ build_tokens.py   全量分词 → cache/（词频 + 带标签分词缓存）
│  └─ train_models.py   训练/评估（口径 A 主实验、B 对照），保存模型
├─ notebooks/           5 个 notebook（01 数据标签 … 05 交互查询）
├─ output/
│  ├─ figures/          全部图表 PNG
│  ├─ tables/           聚合宽表、模型对比表、混淆矩阵
│  └─ models/           vectorizer / model（joblib）
├─ cache/               分词缓存、词频 Counter（可删除后重建）
├─ stopwords.txt        自建中文停用词表（约 500 词）
├─ userdict.txt         jieba 餐饮/点评领域词典
└─ 综合实验1_文本分析_方案.md   方案文档（在上级目录）
```

## 3. 数据口径（与方案一致）

| 口径 | 定义 |
|---|---|
| 缺失评分 | 任务 2 用全局均值 3.6 填充，`rating == 3.6` 视为无标签 |
| 标签 A（主） | 4–5 星 → 1，1–2 星 → 0；3 星与 3.6 剔除 |
| 标签 B（对照） | 4–5 星 → 1，1–3 星 → 0；3.6 剔除 |
| 极化好评率（主） | good / (good + bad)，全站 88.62% |
| 全有效好评率（对照） | good / (good + bad + 三星) |
| Top10 | 极化样本 ≥30，Wilson 95% 下界降序，并列时样本多者优先 |
| 周趋势 | 自然周聚合，周样本 <3 置空，4 周滚动（滚动样本 ≥6 出值） |
| 有效时间区间 | 2009-07 起（完整 2009-12 起）至 2012-02 |

## 4. 运行顺序

```bat
cd /d D:\DSH-Workspaces\数据科学\综合实验1\src
C:\mlenv\Scripts\python.exe build_rest_agg.py
C:\mlenv\Scripts\python.exe build_tokens.py --workers 16
C:\mlenv\Scripts\python.exe train_models.py --scheme A --sample 600000
C:\mlenv\Scripts\python.exe train_models.py --scheme B --sample 600000
```

冒烟测试：

```bat
C:\mlenv\Scripts\python.exe build_tokens.py --workers 4 --limit 3000 --out-suffix _test
```

## 6. 当前完成状态（2026-11-05）

| 项 | 状态 / 产物 |
|---|---|
| 环境 | 已装 `jieba 0.42.1`、`wordcloud 1.9.6`；冒烟测试通过（分词 / 词云 / 中文渲染 / sklearn） |
| 分词缓存 | 4,107,199 行全量分词，16 进程 238 s；`cache/tokens_labeled.tsv.gz`（334.6 MB，2,979,614 行带标签） |
| 商户宽表 | `output/tables/rest_agg.csv`（241,360 行 × 25 列） |
| 模型 A（主，60 万） | TF-IDF + LinearSVC：accuracy 0.9403 / macro-F1 0.8680 |
| 模型 B（对照，60 万） | TF-IDF + LogisticRegression：accuracy 0.7522 / macro-F1 0.7474 |
| 模型 A 全量（194 万） | 训练 1,553,956 / 测试 388,490：LogisticRegression accuracy 0.9395 / macro-F1 0.8699 |
| Notebook | `notebooks/01–05` 全部已执行并保存输出（无报错） |
| 图表 | `output/figures/` 共 19 张（词云 6、模型 2、商户 5、单店 6） |
| 报告 | `综合实验1_实验报告.docx`（**按课程《实验报告模板.doc》重排**：封面标题 + 学院/专业/班级行 + 9 行实验报告表；实验目标/要求/原理/步骤/总结均已填写；18 页，19 张图、11 张嵌套表） |
| 报告 PDF | `综合实验1_实验报告.pdf`（Word 导出，便于直接查看/提交） |
| 旧版报告 | `综合实验1_实验报告_旧版.docx`（模板重排前的自由排版版本，自动备份） |
| 模板 | `template/实验报告模板.docx`（由 .doc 转换，用于保持一致格式） |
| PPT | `综合实验1_汇报PPT.pptx`（16 页，首页含组员占位） |
| 待补充 | PPT 首页与报告封面的**组员姓名 / 学号**（当前为“成员A/B/C”“____”占位） |
| 说明 | `output/` 中带 `_smoke`、`_2w` 后缀的文件为冒烟测试产物，可安全删除 |

