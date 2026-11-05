"""按《数据科学导论实验报告》模板（实验报告模板.doc）生成综合实验1报告。

做法：打开模板 docx，保留封面标题、学院/专业/班级行与整张表格的格式（列宽、合并单元格、
行高、边框），把各栏目内容填入对应单元格，并插入表格、代码、结果截图。

输出：
    D:\\DSH-Workspaces\\数据科学\\综合实验1\\综合实验1_实验报告.docx
    （旧版自动备份为 综合实验1_实验报告_旧版.docx）
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "output" / "tables"
FIG = ROOT / "output" / "figures"
TPL = ROOT / "template" / "实验报告模板.docx"
OUT = ROOT / "综合实验1_实验报告.docx"
BAK = ROOT / "综合实验1_实验报告_旧版.docx"

REPO_URL = "https://github.com/lovechen-520/text-analysis-exp1"

BODY = 10.5
SMALL = 9
CODE = 8.5
BLUE = RGBColor(0x1F, 0x4E, 0x79)
GRAY = RGBColor(0x59, 0x59, 0x59)


# ------------------------------------------------------------------ 文本工具
def style_run(run, size=BODY, bold=False, font="宋体", color=None):
    run.font.size = Pt(size)
    run.bold = bold
    run.font.name = "Times New Roman"
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), font)
    if color:
        run.font.color.rgb = color


def clear_cell(cell):
    for p in list(cell._tc.findall(qn("w:p"))):
        cell._tc.remove(p)
    cell.add_paragraph()


def par(cell, text="", size=BODY, bold=False, font="宋体", align=None,
        indent=False, color=None, space_before=0, space_after=0):
    existing = cell.paragraphs
    if len(existing) == 1 and not existing[0].text.strip() and not existing[0].runs:
        p = existing[0]          # 复用单元格里唯一的空段落，避免出现前导空行
    else:
        p = cell.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing = 1.5
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    if indent:
        pf.first_line_indent = Pt(size * 2)
    if align is not None:
        p.alignment = align
        # 居中段落不保留首行缩进
        pf.first_line_indent = None
    if text:
        run = p.add_run(text)
        style_run(run, size=size, bold=bold, font=font, color=color)
    return p


def h2(cell, text):
    return par(cell, text, size=12, bold=True, font="黑体", color=BLUE,
               space_before=8, space_after=2)


def code_block(cell, text):
    for line in text.split("\n"):
        p = cell.add_paragraph()
        pf = p.paragraph_format
        pf.line_spacing = 1.15
        pf.first_line_indent = None
        pf.space_before = Pt(0)
        pf.space_after = Pt(0)
        pf.left_indent = Cm(0.4)
        run = p.add_run(line if line else " ")
        style_run(run, size=CODE, font="Consolas")


def set_table_borders(table, sz=4):
    """模板文档没有 Table Grid 样式，手动加单线边框。"""
    tblPr = table._tbl.tblPr
    old = tblPr.find(qn("w:tblBorders"))
    if old is not None:
        tblPr.remove(old)
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(sz))
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "000000")
        borders.append(el)
    tblPr.append(borders)


def add_table(cell, df: pd.DataFrame, caption: str = "", font=8.0):
    if caption:
        par(cell, caption, size=SMALL, align=WD_ALIGN_PARAGRAPH.CENTER, color=GRAY)
    t = cell.add_table(rows=len(df) + 1, cols=len(df.columns))
    set_table_borders(t)
    t.autofit = True
    for j, col in enumerate(df.columns):
        c = t.rows[0].cells[j]
        c.text = ""
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(str(col))
        style_run(r, size=font, bold=True)
    for i, (_, row) in enumerate(df.iterrows(), start=1):
        for j, val in enumerate(row):
            c = t.rows[i].cells[j]
            c.text = ""
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if j else WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run("" if pd.isna(val) else str(val))
            style_run(r, size=font)
    return t


def table_model_results(tbl: pd.DataFrame) -> pd.DataFrame:
    """把模型对比表转成中文表头、4 位小数、特征名规范化。"""
    out = tbl[["features", "model", "accuracy", "macro_f1",
               "f1_bad", "precision_bad", "recall_bad"]].copy()
    out["features"] = out["features"].map({"tfidf": "TF-IDF", "count": "Count"})
    out = out.rename(columns={"features": "特征", "model": "模型", "accuracy": "accuracy",
                              "macro_f1": "macro-F1", "f1_bad": "差评 F1",
                              "precision_bad": "差评 P", "recall_bad": "差评 R"})
    return fmt4(out)


def fmt4(df: pd.DataFrame) -> pd.DataFrame:
    """浮点列统一显示为 4 位小数（避免 0.945 / 0.9450 混排）。"""
    out = df.copy()
    for c in out.columns:
        if pd.api.types.is_float_dtype(out[c]):
            out[c] = out[c].map(lambda v: f"{v:.4f}")
    return out


def add_pic(cell, filename, caption="", width=13.4):
    path = FIG / filename
    if not path.exists():
        par(cell, f"[缺少图片 {filename}]", size=SMALL, color=GRAY)
        return
    p = cell.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(str(path), width=Cm(width))
    if caption:
        cp = cell.add_paragraph()
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = cp.add_run(caption)
        style_run(r, size=SMALL, color=GRAY)


def add_hyperlink(paragraph, url, text=None):
    """在段落末尾追加一个可点击的外链。"""
    r_id = paragraph.part.relate_to(url, RT.HYPERLINK, is_external=True)
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)
    run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "0563C1")
    rPr.append(color)
    u = OxmlElement("w:u")
    u.set(qn("w:val"), "single")
    rPr.append(u)
    run.append(rPr)
    t = OxmlElement("w:t")
    t.text = text or url
    t.set(qn("xml:space"), "preserve")
    run.append(t)
    hyperlink.append(run)
    paragraph._p.append(hyperlink)
    return hyperlink


# ------------------------------------------------------------------ 各栏目内容
def fill_goals(cell):
    clear_cell(cell)
    goals = [
        "掌握中文文本数据的装载、缺失值复核与标签构造方法；",
        "掌握中文评论的清洗、jieba 分词、停用词过滤与 Count / TF-IDF 特征构造；",
        "训练并评估二分类模型，对测试集计算 accuracy 等指标，并支持用户输入新评论得到好评/差评；",
        "完成全部评论、好评、差评的高频词统计与词云可视化；",
        "完成商户好评率 Top10、好评率随时间变化、环境/口味/服务雷达图；",
        "实现关键字查询商户，并对选中商户输出词云、好评率、雷达图与时间趋势。",
    ]
    for g in goals:
        par(cell, "• " + g, indent=False)


def fill_requirements(cell):
    clear_cell(cell)
    reqs = [
        "装载数据集，查看数据集前几行内容；",
        "查看数据是否存在缺失值并处理（很短的文本也可以删除）；",
        "将 5 级评论编码为好评（1）与差评（0）；",
        "对评论字段删除标点符号/特殊符号、删除停用词并进行分词；",
        "使用 CountVectorizer / TfidfVectorizer 构造特征；",
        "划分训练集与测试集；",
        "训练二值分类模型（可选用不同算法），实现评论好评/差评分类；",
        "在测试集上计算 accuracy，并支持用户输入新评论得到分类结果；",
        "绘制全部评论、好评、差评的高频词/词云；",
        "10.1 不同餐馆好评/差评比率排序 Top10 柱状图；10.2 Top10 随时间变化的线图（可按周聚集）；"
        "10.3 Top10 环境、口味、服务评分雷达图；",
        "11.1 关键字查询餐馆名称或评论，得到餐馆列表供选择；11.2 单店评论/好评/差评词云；"
        "11.3 单店好评/差评比率；11.4 单店环境/口味/服务雷达图；11.5 单店好评率随时间变化线图。",
        "另外提交：PPT、实验报告（步骤中含源代码与结果截图）、实验源代码（.ipynb 或 .py）。",
    ]
    for i, r in enumerate(reqs, start=1):
        par(cell, f"（{i}）{r}", indent=False, space_after=2)


def fill_principle(cell):
    clear_cell(cell)
    h2(cell, "1. 中文分词与停用词")
    par(cell, "中文文本没有天然空格，需先分词。实验使用 jieba 精确模式，对评论文本做清洗（去 URL、标点、表情）后切分，"
              "并过滤停用词（自建约 500 词表，含哈工大/百度等词表整理结果）与无意义符号，得到词序列。", indent=True)
    h2(cell, "2. 文本表示：Count 与 TF-IDF")
    par(cell, "CountVectorizer 统计词频；TF-IDF 对词频加权：tf-idf(t,d)=tf(t,d)×log((1+N)/(1+df(t))+1)，"
              "以降低“的、了”等高频词的权重。实验使用词级 1–2 gram（min_df=5、max_features=50,000、sublinear_tf）。", indent=True)
    h2(cell, "3. 分类模型")
    par(cell, "MultinomialNB 假设特征条件独立，训练快；LogisticRegression 用 Sigmoid 将线性打分映射为概率，"
              "可设置 class_weight=balanced 应对类别不均衡；LinearSVC 用最大间隔思想做线性分类。三者均适合高维稀疏文本特征。", indent=True)
    h2(cell, "4. 评价指标")
    par(cell, "accuracy = 正确数/总数；精确率 P、召回率 R、F1 = 2PR/(P+R)；macro-F1 对两类 F1 取均值，"
              "能反映少数类（差评）的识别能力；混淆矩阵给出 TP/FP/FN/TN。", indent=True)
    h2(cell, "5. 好评率与 Wilson 下界")
    par(cell, "好评率 = 好评数 /(好评数+差评数)。由于单店样本少且大量为 100%，按 Wilson 95% 置信区间下界排序：", indent=True)
    code_block(cell, "p_hat = good/n;  LB = (p_hat + z^2/(2n) - z*sqrt(p_hat(1-p_hat)/n + z^2/(4n^2))) / (1+z^2/n),  z=1.96")
    h2(cell, "6. 词云、周趋势与雷达图")
    par(cell, "词云按词频映射字号；周趋势把评论按自然周聚合好评率，周样本<3 置空后再做 4 周滚动；"
              "雷达图把环境、口味、服务三项均值映射到 0–5 的三轴极坐标。", indent=True)


def fill_steps(cell):
    clear_cell(cell)

    # ---------------- 一、数据装载与复核
    h2(cell, "一、数据装载与复核（任务 1、2）")
    par(cell, "任务 1、2 已在前置 notebook 中完成：读取原始 ratings.csv（4,422,473 行），删除空评论行、"
              "对评分缺失做均值填充、删除长度<10 字的短评，最终导出 preprocessed_ratings.csv。"
              "本实验直接使用该文件，并对其数据质量进行复核。", indent=True)
    data_tbl = pd.DataFrame({
        "文件": ["preprocessed_ratings.csv", "restaurants.csv", "links.csv"],
        "规模": ["4,107,199 行 × 8 列，1.9 GB", "243,247 行 × 2 列", "243,247 行 × 2 列"],
        "用途": ["主数据（任务 3–11）", "商户名称", "点评 ID 映射（未使用）"],
    })
    add_table(cell, data_tbl, "表 1  实验数据文件")
    par(cell, "装载与查看前几行（过程见 notebook 01_data_label.ipynb）：", indent=True)
    code_block(cell, """import pandas as pd
df = pd.read_csv("preprocessed_ratings.csv")
print(df.shape)          # (4107199, 8)
df.head()""")
    par(cell, "前几行为 userId、restId、rating、rating_env、rating_flavor、rating_service、timestamp（毫秒）"
              "与 comment；例如第 1 行为 userId=0、restId=0、rating=3.6、comment=“经常去的，不过我自己的卡很久不用……”"
              "——该行原始评分缺失，被填充为 3.6。", indent=True)
    par(cell, "复核发现两个必须处理的问题：（1）缺失的 rating 被全局均值填充为 3.6，共 1,127,570 行（27.45%），"
              "而真实评分只取整数 0–5，因此可用 rating==3.6 精确识别伪值并剔除；"
              "（2）2009 年 7 月以前基本没有有效星级（2009-07～2009-11 仅 15%～53% 有星级，2009-12 起才基本完整），"
              "因此情感分类与时间趋势主要覆盖 2009-07～2012-02。", indent=True)
    miss = pd.DataFrame({
        "字段": ["userId", "restId", "rating", "rating_env", "rating_flavor", "rating_service", "timestamp", "comment"],
        "缺失数（导出文件复核）": [0, 0, 0, 0, 0, 0, 0, 0],
    })
    add_table(cell, miss, "表 2  缺失值复核")
    yearly = pd.DataFrame({
        "年份": ["2003", "2004", "2005", "2006", "2007", "2008", "2009", "2010", "2011", "2012*"],
        "评论数": [246, 2587, 32315, 73409, 132715, 460809, 655441, 892223, 1688659, 168795],
        "3.6 伪值": [246, 2587, 32315, 73409, 132715, 460809, 424867, 264, 293, 65],
    })
    yearly["有效评分"] = yearly["评论数"] - yearly["3.6 伪值"]
    yearly["有效评分占比"] = (yearly["有效评分"] / yearly["评论数"] * 100).round(1).astype(str) + "%"
    add_table(cell, yearly, "表 3  评论数与有效评分（按年；*2012 仅 1–2 月）")
    par(cell, "其他发现：每店评论数中位数仅 3 条（极化样本≥30 的商户 20,563 家）；商户名称缺失 13.97%；"
              "数据实际包含超市、博物馆、酒吧等非餐饮商户，报告按“商户”理解。", indent=True)

    # ---------------- 二、标签构造
    h2(cell, "二、标签构造（任务 3）")
    par(cell, "口径 A（主实验）：4–5 星→1，1–2 星→0，3 星（中性）与 3.6（伪值）剔除；"
              "口径 B（对照）：4–5 星→1，1–3 星→0，3.6 剔除。0 分记录仅 15 条且内容为正，作为异常值删除。", indent=True)
    lab = pd.DataFrame({
        "评分": ["5 星", "4 星", "3 星", "2 星", "1 星", "0 分", "3.6（伪值）"],
        "条数": [370067, 1351432, 1037168, 139981, 80966, 15, 1127570],
        "占比": ["9.01%", "32.90%", "25.25%", "3.41%", "1.97%", "0.0004%", "27.45%"],
        "标签": ["1 好评", "1 好评", "-1 中性", "0 差评", "0 差评", "删除", "NaN 无标签"],
    })
    add_table(cell, lab, "表 4  评分分布与标签映射")
    code_block(cell, """import numpy as np
df["is_imputed_rating"] = np.isclose(df["rating"], 3.6)
df = df[df["rating"] != 0.0]                       # 删除 15 条 0 分异常
df["label"] = np.select(
    [df["rating"].between(4, 5), df["rating"].between(1, 2), df["rating"].eq(3)],
    [1, 0, -1], default=np.nan)                    # 1 好评 / 0 差评 / -1 中性""")
    par(cell, "最终有效评分 2,979,629 条（含 15 条 0 分异常，删除后 2,979,614 条）："
              "好评 1,721,499、差评 220,947、三星 1,037,168；极化样本好评率 88.62%。"
              "由于好评:差评≈7.8:1，仅报告 accuracy 会被“全猜好评”的 88.63% 基线掩盖，需同时报告 macro-F1 与混淆矩阵。", indent=True)
    add_pic(cell, "fig01_label_distribution.png", "图 1  评分标签分布", width=12.0)

    # ---------------- 三、清洗分词
    h2(cell, "三、文本清洗与分词（任务 4）")
    par(cell, "清洗规则：去除 URL 与换行/制表符，仅保留中文、英文、数字（标点、表情、特殊符号替换为空格），压缩空格；"
              "分词使用 jieba 精确模式，加载餐饮/点评领域自定义词典（约 120 词）和停用词表。核心代码如下：", indent=True)
    code_block(cell, """import re, jieba
URL = re.compile(r"(https?://\\S+|www\\.\\S+)")
KEEP = re.compile(r"[^\\u4e00-\\u9fa5A-Za-z0-9]+")
STOP = set(open("stopwords.txt", encoding="utf-8").read().split())
def clean_text(s):
    s = URL.sub(" ", str(s)).replace("\\n", " ").replace("\\r", " ")
    return re.sub(r"\\s+", " ", KEEP.sub(" ", s)).strip()
def tokenize(s):
    return [w for w in jieba.lcut(clean_text(s)) if w.strip() and w not in STOP]""")
    sample = pd.DataFrame({
        "原始评论": ["这家的火锅很好吃，服务态度也不错，就是有点贵！！！",
                 "服务员态度极差，上菜慢得要死，再也不会来了……",
                 "http://www.dianping.com 团购的套餐，性价比很高，停车也方便。"],
        "分词结果（去停用词）": ["这家 火锅 很 好吃 服务态度 不错 有点 贵",
                        "服务员 态度 极差 上菜 慢 要死 再也 不会 来",
                        "团购 套餐 性价比 很 高 停车 方便"],
    })
    add_table(cell, sample, "表 5  清洗与分词示例")
    par(cell, "全量 4,107,199 条评论（约 5.94 亿字符）采用 16 进程分词，耗时 238 秒，词表规模 111 万；"
              "分词结果缓存为 2,979,614 行带标签样本（334.6 MB），供特征与词云复用。", indent=True)

    # ---------------- 四、特征与划分
    h2(cell, "四、特征构造与数据划分（任务 5、6）")
    par(cell, "构造两套特征：TF-IDF（word 1–2 gram，min_df=5，max_features=50,000，sublinear_tf=True）"
              "与 CountVectorizer（max_features=30,000）。以 60 万条极化样本分层抽样（好评率 88.63%），"
              "按 8:2 分层划分训练集 48 万、测试集 12 万，随机种子 42。核心代码如下：", indent=True)
    code_block(cell, """from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
tfidf = TfidfVectorizer(tokenizer=str.split, lowercase=False, token_pattern=None,
                        max_features=50000, min_df=5, ngram_range=(1, 2), sublinear_tf=True)
Xtr, Xte, ytr, yte = train_test_split(text, y, test_size=0.2, stratify=y, random_state=42)
Xtr = tfidf.fit_transform(Xtr); Xte = tfidf.transform(Xte)""")

    # ---------------- 五、模型与评估
    h2(cell, "五、模型训练与评估（任务 7、8）")
    code_block(cell, """from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, f1_score
models = {"MultinomialNB": MultinomialNB(),
          "LogisticRegression": LogisticRegression(class_weight="balanced", max_iter=1000),
          "LinearSVC": LinearSVC(class_weight="balanced")}
for name, clf in models.items():
    clf.fit(Xtr, ytr)
    pred = clf.predict(Xte)
    print(name, accuracy_score(yte, pred), f1_score(yte, pred, average="macro"))""")
    tbl_a = pd.read_csv(TAB / "model_compare_A_60w.csv")
    show = table_model_results(tbl_a)
    add_table(cell, show, "表 6  口径 A 模型对比（60 万抽样）")
    par(cell, "朴素贝叶斯 accuracy 最高（0.9450）但差评召回仅 0.5732，属于偏向多数类；逻辑回归与 LinearSVC 的 macro-F1 达 0.868，"
              "差评召回提升到 0.88–0.90，综合两类均衡性选择 LinearSVC 作为主模型。", indent=True)
    add_pic(cell, "fig07_model_compare.png", "图 2  口径 A 各模型 accuracy 与 macro-F1 对比", width=13.4)
    add_pic(cell, "fig08_confusion_demo.png", "图 3  混淆矩阵（口径 A，LinearSVC，20 万演示样本）", width=10.5)
    par(cell, "20 万演示样本评估结果：accuracy 0.9430、macro-F1 0.8700；差评 precision 0.7069 / recall 0.8519，"
              "好评 precision 0.9805 / recall 0.9547。用户输入推理示例：", indent=True)
    for s in [
        "“菜的味道非常好，服务也很周到，下次还会再来！” → 好评",
        "“难吃死了，服务态度极差，环境也很脏，再也不来了。” → 差评",
        "“环境一般，但是菜的味道还不错，价格略贵，可以接受。” → 好评（模型抓住“味道不错”的主要极性）",
    ]:
        par(cell, "• " + s, indent=False)
    tbl_b = pd.read_csv(TAB / "model_compare_B_60w.csv")
    add_table(cell, table_model_results(tbl_b), "表 7  口径 B（三星并入差评）模型对比（60 万抽样）")
    par(cell, "口径 B 类别更平衡（好评 57.8% / 差评 42.2%，其“全猜好评”基线为 57.8%），但三星文本语义中性、噪声大，"
              "最佳 accuracy 0.7522、macro-F1 0.7474，明显低于口径 A（0.9403 / 0.8680），"
              "说明把中性三星并入差评会引入标签噪声，口径 A 更合理。", indent=True)
    full_csv = TAB / "model_compare_A_full.csv"
    if full_csv.exists():
        full = pd.read_csv(full_csv)
        add_table(cell, table_model_results(full),
                  "表 8  口径 A 全量 194 万极化样本模型对比（训练 1,553,956 / 测试 388,490）")
        par(cell, "全量训练后逻辑回归 accuracy 0.9395、macro-F1 0.8699，模型保存为 output/models/model_A_full.joblib"
                  "（本地生成，未纳入 GitHub 仓库），可直接推理。", indent=True)

    # ---------------- 六、词云
    h2(cell, "六、词频与词云（任务 9）")
    par(cell, "对全部评论、好评、差评分别统计词频（仅保留长度≥2 的词并过滤停用词），用微软雅黑字体绘制词云。", indent=True)
    add_pic(cell, "fig09_all_wordcloud.png", "图 4  全部评论词云（4,107,199 条）", width=13.0)
    add_pic(cell, "fig09_good_wordcloud.png", "图 5  好评词云（4–5 星，1,721,499 条）", width=12.6)
    add_pic(cell, "fig09_bad_wordcloud.png", "图 6  差评词云（1–2 星，220,947 条）", width=12.6)
    par(cell, "全部评论词云以“不错、味道、喜欢、环境、好吃、价格、服务员”为主；好评偏“好吃、推荐、味道、服务、划算”；"
              "差评偏“难吃、态度、服务员、贵、慢、失望”。Top20 高频词如下：", indent=True)
    add_pic(cell, "fig09_top20_all.png", "图 7  全部评论 Top20 高频词", width=10.0)
    add_pic(cell, "fig09_top20_good.png", "图 8  好评 Top20 高频词", width=10.0)
    add_pic(cell, "fig09_top20_bad.png", "图 9  差评 Top20 高频词", width=10.0)

    # ---------------- 七、商户可视化
    h2(cell, "七、商户维度可视化（任务 10）")
    par(cell, "10.1 计算好评率 = good/(good+bad)，仅保留极化样本≥30 的 20,563 家商户，按 Wilson 95% 下界排序，"
              "避免小样本与 100% 并列导致的排名失真。由于头部商户好评率普遍为 100%，左图用 Wilson 下界作柱高，右图给出最低 10 家作对照。", indent=True)
    add_pic(cell, "fig10_1_top10_ratio.png", "图 10  好评率最高 Top10 与最低 Bottom10", width=13.6)
    top10 = pd.read_csv(TAB / "top10_ratio.csv")
    top10["name"] = top10["name"].fillna("（无名称）")
    show10 = top10[["name", "n", "good", "bad", "lab", "ratio", "wilson"]].rename(columns={
        "name": "商户", "n": "评论数", "good": "好评", "bad": "差评",
        "lab": "极化样本", "ratio": "好评率", "wilson": "Wilson 下界"})
    add_table(cell, fmt4(show10), "表 9  好评率最高 Top10（Wilson 下界排序）")
    par(cell, "10.2 由于 10.1 的 Top10 好评率均为 100%，周好评率恒为 1，无法体现变化；改用“评论量 Top10”"
              "（样本充足、含少量差评）展示时间趋势：按自然周聚合好评率，周样本<3 置空后做 4 周滚动。", indent=True)
    add_pic(cell, "fig10_2_weekly_ratio_top10.png", "图 11  评论量 Top10 商户周滚动好评率", width=13.6)
    par(cell, "10.3 对 10.1 的 Top10 计算环境、口味、服务评分均值（剔除 2.7 填充伪值）绘制雷达图。", indent=True)
    add_pic(cell, "fig10_3_radar_grid.png", "图 12  Top10 商户环境/口味/服务雷达图", width=13.6)
    add_pic(cell, "fig10_3_radar_overlay.png", "图 13  Top10 三项评分叠加图", width=11.0)

    # ---------------- 八、交互
    h2(cell, "八、关键字查询与单店分析（任务 11）")
    par(cell, "实现 search_restaurants(keyword)：同时检索商户名称与评论文本，合并候选并按极化样本量排序；"
              "用户选择商户后输出 11.2–11.5 四类结果。以关键词“湘”为例，选择“57℃湘(无限度广场店)”演示。", indent=True)
    kw = pd.DataFrame({
        "关键词": ["湘", "粤", "人大", "北大", "西直门"],
        "名称命中商户数": [2796, 711, 43, 244, 118],
        "其中评论数≥50": [278, 92, 8, 33, 61],
    })
    add_table(cell, kw, "表 10  关键词检索命中情况")
    add_pic(cell, "fig11_2_rest_wordcloud_all.png", "图 14  该店全部评论词云", width=10.5)
    add_pic(cell, "fig11_2_rest_wordcloud_good.png", "图 15  该店好评词云", width=10.0)
    add_pic(cell, "fig11_2_rest_wordcloud_bad.png", "图 16  该店差评词云", width=10.0)
    add_pic(cell, "fig11_3_rest_ratio.png", "图 17  该店好评率与全站基线", width=9.0)
    add_pic(cell, "fig11_4_rest_radar.png", "图 18  该店环境/口味/服务雷达图", width=10.0)
    add_pic(cell, "fig11_5_rest_weekly_ratio.png", "图 19  该店周滚动好评率", width=12.5)

    # ---------------- 九、代码与复现
    h2(cell, "九、源代码结构与复现说明")
    par(cell, "源代码已托管至 GitHub 仓库：", indent=True)
    add_hyperlink(cell.paragraphs[-1], REPO_URL, REPO_URL)
    run = cell.paragraphs[-1].add_run("（分支 main）。按任务拆分为 5 个 notebook（均已执行并保存输出），"
                                      "复现代码封装在 src/ 模块中。目录如下：")
    style_run(run, size=BODY)
    code_block(cell, """text-analysis-exp1/              # GitHub 仓库根目录
├─ src/                          # 可复用模块与数据生产脚本
│  ├─ config.py / data_utils.py / text_utils.py / agg_utils.py
│  ├─ model_utils.py / viz_utils.py
│  └─ build_rest_agg.py / build_tokens.py / train_models.py / make_notebooks.py
├─ notebooks/
│  ├─ 01_data_label.ipynb        任务 1–3
│  ├─ 02_tokenize_model.ipynb    任务 4–8
│  ├─ 03_wordcloud.ipynb         任务 9
│  ├─ 04_restaurant_viz.ipynb    任务 10
│  └─ 05_query.ipynb             任务 11
├─ output/figures/               19 张结果图
├─ output/tables/                模型对比等小表（rest_agg.csv 未入库）
├─ stopwords.txt / userdict.txt
└─ README.md                     数据来源与复现说明""")
    mapping = pd.DataFrame({
        "任务": ["1 装载", "2 缺失值", "3 标签", "4 清洗分词", "5 特征", "6 划分", "7 模型",
                 "8 评估+推理", "9 词云/词频", "10.1 Top10", "10.2 周趋势", "10.3 雷达图",
                 "11.1 查询", "11.2–11.5 单店"],
        "代码位置（GitHub 仓库内路径）": [
            "notebooks/01_data_label.ipynb", "notebooks/01_data_label.ipynb", "notebooks/01_data_label.ipynb",
            "notebooks/02_tokenize_model.ipynb", "notebooks/02_tokenize_model.ipynb", "notebooks/02_tokenize_model.ipynb",
            "notebooks/02_tokenize_model.ipynb", "notebooks/02_tokenize_model.ipynb",
            "notebooks/03_wordcloud.ipynb", "notebooks/04_restaurant_viz.ipynb",
            "notebooks/04_restaurant_viz.ipynb", "notebooks/04_restaurant_viz.ipynb",
            "notebooks/05_query.ipynb", "notebooks/05_query.ipynb"],
        "结果": ["表 1–3", "表 2", "表 4/图 1", "表 5", "四节代码", "四节", "表 6/图 2",
                 "图 3", "图 4–9", "图 10/表 9", "图 11", "图 12–13", "表 10", "图 14–19"],
    })
    add_table(cell, mapping, "表 11  任务与代码、结果对照（路径相对 GitHub 仓库根目录）")
    par(cell, "环境：Python 3.13.7（本地 C:\\mlenv），pandas 3.0.5、scikit-learn 1.9.1、jieba 0.42.1、"
              "wordcloud 1.9.6、matplotlib 3.11.1，随机种子 42。", indent=True)


def fill_summary(cell):
    clear_cell(cell)
    par(cell, "1. 完成情况：按实验要求完成 11 项任务，包括数据装载与缺失值处理、标签编码、清洗分词、"
              "Count/TF-IDF 特征、训练测试划分、3 种分类模型对比、accuracy 与混淆矩阵评估、用户输入推理、"
              "三套词云与高频词、商户好评率 Top10、周趋势、雷达图以及关键词查询与单店四图分析。", indent=True)
    par(cell, "2. 主要结论：", indent=True, space_before=4)
    for s in [
        "数据质量决定结论：27.45% 的评分是均值填充伪值、2009 年 7 月前基本无有效评分，不识别会直接导致标签与图表错误；",
        "口径 A 下 TF-IDF + LinearSVC 达到 accuracy 94.03%、macro-F1 0.868（全量 194 万模型 accuracy 0.9395、macro-F1 0.8699）；",
        "把中性三星并入差评（口径 B）后最佳 accuracy 仅 0.7522（其全猜好评基线为 57.8%）、macro-F1 0.7474，"
        "明显低于口径 A，说明标签口径对结论影响显著，必须显式说明；",
        "商户分析必须控制样本量：每店评论中位仅 3 条，Top10 需最小样本阈值与 Wilson 平滑；",
        "可视化结果与数据一致：好评率 88.62%，词云呈现“口味 > 环境 ≈ 服务”的评价结构。",
    ]:
        par(cell, "• " + s, indent=False)
    par(cell, "3. 不足与改进：数据止于 2012 年 2 月且 2009 年 7 月前无评分，时间结论适用范围有限；"
              "未使用词向量或预训练模型（如 BERT）做对比；评论与星级存在少量不一致，可引入人工校验或弱监督降噪；"
              "商户名称缺失 14%，图表以 restId 回退显示。", indent=True, space_before=4)
    par(cell, "4. 心得体会：通过本实验完整走通了中文文本分析链路，体会到数据质量核查（尤其是缺失值填充带来的伪值）"
              "比模型调参更影响最终结论；同时认识到可视化必须建立在正确的统计口径与样本量控制之上。", indent=True)


# ------------------------------------------------------------------ 主流程
def main():
    if OUT.exists():
        shutil.copy2(OUT, BAK)
        print("backup old report ->", BAK)

    doc = Document(TPL)

    # 封面行补充班级占位
    para = doc.paragraphs[2]
    r = para.add_run("__________")
    style_run(r, size=BODY)

    t = doc.tables[0]
    # 基本信息
    for (row, col, text) in [
        (0, 2, "__________"), (0, 4, "__________"), (0, 6, "__________"),
        (1, 2, "2026 年 11 月 5 日"), (1, 4, "__________"), (1, 6, ""),
    ]:
        c = t.cell(row, col)
        clear_cell(c)
        if text:
            par(c, text, indent=False, align=WD_ALIGN_PARAGRAPH.CENTER)

    c = t.cell(2, 2)
    clear_cell(c)
    par(c, "综合实验 1  文本分析", indent=False)

    fill_goals(t.cell(3, 1))
    fill_requirements(t.cell(4, 1))
    fill_principle(t.cell(5, 1))
    fill_steps(t.cell(6, 1))
    fill_summary(t.cell(7, 1))

    doc.save(OUT)
    print("saved:", OUT)


if __name__ == "__main__":
    main()
