"""生成《综合实验1 文本分析》实验报告 docx。

依赖：python-docx、pandas（用 DSH 自带 Python 运行）
用法：
    C:\\Users\\13727\\.dsh\\dsh-runtimes\\dsh-primary-runtime\\dependencies\\python\\python.exe build_report.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "output" / "tables"
FIG = ROOT / "output" / "figures"
OUT = ROOT / "综合实验1_实验报告.docx"

C_BLUE = RGBColor(0x1F, 0x4E, 0x79)
C_GRAY = RGBColor(0x59, 0x59, 0x59)


# ------------------------------------------------------------------ 基础排版
def setup(doc: Document):
    sec = doc.sections[0]
    sec.page_width = Cm(21.0)
    sec.page_height = Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.4)
    sec.top_margin = sec.bottom_margin = Cm(2.4)

    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(10.5)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    normal.paragraph_format.line_spacing = 1.4
    normal.paragraph_format.space_after = Pt(3)

    for name, size in (("Heading 1", 16), ("Heading 2", 13), ("Heading 3", 11.5)):
        st = doc.styles[name]
        st.font.name = "Times New Roman"
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = C_BLUE
        st.element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")


def h(doc, text, level=1):
    return doc.add_heading(text, level=level)


def p(doc, text, bold=False, size=10.5, align=None, indent=True, color=None):
    par = doc.add_paragraph()
    par.paragraph_format.first_line_indent = Cm(0.74) if indent else None
    par.alignment = align or WD_ALIGN_PARAGRAPH.JUSTIFY
    run = par.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    if color:
        run.font.color.rgb = color
    return par


def bullet(doc, text, size=10.5):
    par = doc.add_paragraph(style="List Bullet")
    run = par.add_run(text)
    run.font.size = Pt(size)
    return par


def caption(doc, text):
    par = doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = par.add_run(text)
    run.font.size = Pt(9)
    run.font.color.rgb = C_GRAY


def image(doc, filename, cap, width=6.1):
    path = FIG / filename
    if not path.exists():
        p(doc, f"[缺少图片: {filename}]", color=C_GRAY)
        return
    doc.add_picture(str(path), width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption(doc, cap)


def table(doc, df: pd.DataFrame, cap: str, font_size=8.5, widths=None):
    caption(doc, cap)
    t = doc.add_table(rows=len(df) + 1, cols=len(df.columns))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, col in enumerate(df.columns):
        cell = t.rows[0].cells[j]
        cell.text = str(col)
        for par in cell.paragraphs:
            for run in par.runs:
                run.bold = True
                run.font.size = Pt(font_size)
    for i, (_, row) in enumerate(df.iterrows(), start=1):
        for j, val in enumerate(row):
            cell = t.rows[i].cells[j]
            cell.text = "" if pd.isna(val) else str(val)
            for par in cell.paragraphs:
                for run in par.runs:
                    run.font.size = Pt(font_size)
    doc.add_paragraph()


def code_block(doc, text):
    par = doc.add_paragraph()
    par.paragraph_format.left_indent = Cm(0.5)
    run = par.add_run(text)
    run.font.name = "Consolas"
    run.font.size = Pt(8.5)
    run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)


# ------------------------------------------------------------------ 正文
def build():
    doc = Document()
    setup(doc)

    # ---------------- 封面
    for _ in range(4):
        doc.add_paragraph()
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run("综合实验 1  《文本分析》")
    r.font.size = Pt(26)
    r.bold = True
    r.font.color.rgb = C_BLUE
    t2 = doc.add_paragraph()
    t2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t2.add_run("实验报告")
    r.font.size = Pt(20)
    r.font.color.rgb = C_BLUE

    for _ in range(3):
        doc.add_paragraph()
    info = [
        ("数据集", "大众点评商户点评数据集（yf_dianping，4,107,199 条评论）"),
        ("小组成员", "成员A（数据与模型）　成员B（文本可视化）　成员C（统计可视化 / 交互 / 报告）"),
        ("学号", "____________________"),
        ("课程", "数据科学综合实验"),
        ("日期", "2026 年 11 月"),
    ]
    for k, v in info:
        par = doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = par.add_run(f"{k}：{v}")
        run.font.size = Pt(11)

    doc.add_page_break()

    # ---------------- 摘要
    h(doc, "摘要", 1)
    p(doc, "本实验基于大众点评商户点评数据集（4,107,199 条评论文本），完成了从数据装载、"
           "缺失值与标签处理、中文清洗与分词、TF-IDF/Count 特征构造、二分类模型训练与评估，"
           "到词云词频、商户维度统计可视化和关键词交互查询的全流程文本分析。")
    p(doc, "实验首先发现并处理了预处理文件中的两处关键数据问题：评分字段的缺失被均值 3.6 填充"
           "（占 27.45%），以及 2009 年 12 月以前几乎不存在有效评分。随后构造好评（4–5 星）/差评（1–2 星）"
           "二分类标签，使用 jieba 对全量 594 M 字符的评论完成多进程分词（16 进程 / 238 s），"
           "在 60 万抽样上比较了 TF-IDF 与 Count 特征下 3 种模型；TF-IDF + LinearSVC 达到 "
           "accuracy 94.03%、macro-F1 0.868（全量 194 万极化样本模型见正文 6.5 节）。"
           "最后完成了 all/好评/差评三套词云与高频词、Top10/Bottom10 好评率、周好评率趋势、"
           "环境/口味/服务雷达图，以及关键词检索 + 单店分析交互流程。")
    p(doc, "关键词：文本分析；中文分词；TF-IDF；情感分类；词云；数据可视化")

    # ---------------- 1 实验目的
    h(doc, "1 实验目的", 1)
    for s in [
        "掌握中文文本数据的装载、缺失值处理与标签构造方法；",
        "掌握中文文本清洗、分词、停用词过滤与特征向量化（Count / TF-IDF）流程；",
        "训练并评估二分类模型，能够对新评论给出好评/差评判断；",
        "掌握词云、词频、柱状图、折线图、雷达图等文本可视化方法；",
        "完成“关键词查询商户 → 单店多维度分析”的交互式分析闭环。",
    ]:
        bullet(doc, s)

    # ---------------- 2 数据集
    h(doc, "2 数据集与字段", 1)
    p(doc, "实验使用大众点评商户点评数据集（yf_dianping），共 4 个文件。主数据为任务 1、2 已完成预处理后导出的 "
           "preprocessed_ratings.csv，后续任务直接基于该文件；本实验不重复执行清洗，但对其数据质量进行了系统复核。")
    df = pd.DataFrame({
        "文件": ["preprocessed_ratings.csv", "restaurants.csv", "links.csv"],
        "规模": ["4,107,199 行 × 8 列，1.9 GB", "243,247 行 × 2 列", "243,247 行 × 2 列"],
        "字段": ["userId, restId, rating, rating_env, rating_flavor, rating_service, timestamp, comment",
                 "restId, name", "restId, dianpingId"],
    })
    table(doc, df, "表 1  实验数据文件")
    p(doc, "timestamp 为毫秒级时间戳；rating 为总体评分（0–5），rating_env / rating_flavor / rating_service "
           "分别为环境、口味、服务评分；comment 为用户评论文本（≥10 字）。时间跨度为 2003-04-07 至 2012-02-08，"
           "共 241,360 家商户至少有一条评论。")

    # ---------------- 3 预处理
    h(doc, "3 数据预处理（任务 1、2）", 1)
    h(doc, "3.1 装载与缺失值处理", 2)
    p(doc, "任务 1、2 已在前置 notebook 中完成：读取原始 ratings.csv（4,422,473 行），删除空评论行、"
           "对评分字段的缺失用全局均值填充、删除长度小于 10 字的短评，最终导出 4,107,199 行。"
           "本实验复核后确认：导出文件中各列均无缺失，评论长度 10–2,001 字符（均值 144.7）。")
    h(doc, "3.2 关键数据质量问题", 2)
    p(doc, "复核发现预处理文件存在两处必须处理的问题：", indent=True)
    bullet(doc, "评分均值填充伪值：缺失 rating 被填充为 3.6（真实评分只取整数 0–5），共 1,127,570 行（27.45%）。"
                "本实验以 rating == 3.6 精确还原缺失掩码，所有监督学习与好评率统计均剔除该批数据。")
    bullet(doc, "评分时间覆盖不全：2009 年 12 月以前几乎没有有效星级（见表 2），因此情感分类与时间趋势"
                "只能覆盖 2009-07 ～ 2012-02。")
    bullet(doc, "类别极不均衡、商户样本长尾：极化样本好评率 88.62%（1,721,499 : 220,962）；"
                "每店评论数中位数仅 3 条，极化样本≥30 的商户只有 20,563 家。")
    bullet(doc, "商户名称缺失 14%（33,731/241,360），且数据实际包含超市、博物馆、酒吧等非餐饮商户，报告统一按“商户”理解。")

    yearly = pd.DataFrame({
        "年份": ["2003", "2004", "2005", "2006", "2007", "2008", "2009", "2010", "2011", "2012*"],
        "评论数": [246, 2587, 32315, 73409, 132715, 460809, 655441, 892223, 1688659, 168795],
        "3.6 伪值": [246, 2587, 32315, 73409, 132715, 460809, 424867, 264, 293, 65],
    })
    yearly["有效评分"] = yearly["评论数"] - yearly["3.6 伪值"]
    yearly["有效评分占比"] = (yearly["有效评分"] / yearly["评论数"] * 100).round(1).astype(str) + "%"
    table(doc, yearly, "表 2  评论数与有效评分（按年；*2012 仅 1–2 月）")
    p(doc, "表 2 表明：2003–2008 年评论的 rating 全部缺失，2009 年仍有 65% 缺失，2010 年起才完整。"
           "这一发现直接决定了后续标签构造与时间可视化的工作范围。")

    # ---------------- 4 标签
    h(doc, "4 标签构造（任务 3）", 1)
    p(doc, "按“好评（1）/差评（0）”构造标签，采用两种口径：")
    bullet(doc, "口径 A（主实验）：4–5 星 → 1，1–2 星 → 0；3 星（中性）与 3.6 伪值剔除；")
    bullet(doc, "口径 B（对照实验）：4–5 星 → 1，1–3 星 → 0；3.6 伪值剔除。")
    p(doc, "0 分记录仅 15 条且评论文本内容为正，判为异常值删除。最终有效评分 2,979,629 条："
           "好评 1,721,499（57.8%）、差评 220,962（7.4%）、三星 1,037,168（34.8%）；极化样本好评率 88.62%。")
    dist = pd.read_csv(TAB / "label_dist.csv")
    dist["占比"] = dist["share"].astype(str) + "%"
    table(doc, dist[["rating", "count", "占比", "label"]].rename(
        columns={"rating": "评分", "count": "条数", "label": "标签"}),
        "表 3  评分分布与标签映射")
    image(doc, "fig01_label_distribution.png", "图 1  评分标签分布")

    # ---------------- 5 分词
    h(doc, "5 文本清洗、分词与停用词（任务 4）", 1)
    p(doc, "清洗规则：去除 URL、换行/制表符，仅保留中文、英文与数字（标点、表情、特殊符号替换为空格），"
           "并压缩连续空格。分词采用 jieba 精确模式，加载餐饮/点评领域自定义词典（约 120 词）与自建停用词表（约 500 词），"
           "过滤停用词与空白词。")
    p(doc, "全量 4,107,199 条评论（约 5.94 亿字符）使用 16 进程分词，耗时 238 秒，词表规模 111 万；"
           "分词结果缓存为 cache/tokens_labeled.tsv.gz（2,979,614 行带标签样本，334.6 MB），供特征与词云复用。")
    p(doc, "分词与清洗示例：")
    sample = pd.DataFrame({
        "原始评论": ["这家的火锅很好吃，服务态度也不错，就是有点贵！！！",
                 "服务员态度极差，上菜慢得要死，再也不会来了……",
                 "http://www.dianping.com 团购的套餐，性价比很高，停车也方便。"],
        "分词结果（去停用词）": ["这家 火锅 很 好吃 服务态度 不错 有点 贵",
                        "服务员 态度 极差 上菜 慢 要死 再也 不会 来",
                        "团购 套餐 性价比 很 高 停车 方便"],
    })
    table(doc, sample, "表 4  清洗与分词示例")

    # ---------------- 6 模型
    h(doc, "6 特征工程与分类模型（任务 5–8）", 1)
    h(doc, "6.1 特征构造与数据划分", 2)
    p(doc, "构造两套特征进行对比：TF-IDF（word 1–2 gram，min_df=5，max_features=50,000，sublinear_tf=True）"
           "与 CountVectorizer（max_features=30,000）。以 600,000 条极化样本分层抽样（好评率 88.63%），"
           "按 8:2 分层划分训练集（480,000）与测试集（120,000），随机种子 42。")
    tbl_a = pd.read_csv(TAB / "model_compare_A_60w.csv")
    show = tbl_a[["features", "model", "accuracy", "macro_f1", "f1_bad", "precision_bad", "recall_bad", "train_sec"]]
    table(doc, show, "表 5  口径 A 模型对比（60 万抽样）")
    image(doc, "fig07_model_compare.png", "图 2  口径 A 各模型 accuracy 与 macro-F1 对比")

    h(doc, "6.2 结果分析", 2)
    p(doc, "从表 5 可见：多项式朴素贝叶斯（MultinomialNB）accuracy 最高（0.9450），但差评类召回率仅 0.5732，"
           "属于“偏向多数类”的虚高；逻辑回归（class_weight=balanced）与 LinearSVC 的 accuracy 分别为 0.9389 / 0.9403，"
           "macro-F1 达 0.868，差评召回率提升到 0.88–0.90。综合考虑两类均衡性，以 LinearSVC 作为主模型。")
    p(doc, "另需说明：全猜“好评”的基线 accuracy 即为 88.63%，因此仅报告 accuracy 会掩盖差评识别能力的差异，"
           "本实验同时报告 macro-F1、差评类精确率/召回率与混淆矩阵。")
    image(doc, "fig08_confusion_demo.png", "图 3  混淆矩阵（口径 A，LinearSVC，20 万演示样本）")
    p(doc, "对 20 万演示样本（16 万训练 / 4 万测试）的评估结果为：accuracy 0.9430，macro-F1 0.8700，"
           "差评类 precision 0.7069 / recall 0.8519，好评类 precision 0.9805 / recall 0.9547。")

    h(doc, "6.3 用户输入推理演示", 2)
    p(doc, "推理函数复用同一套清洗/分词流程，对新评论直接输出好评/差评。测试结果：")
    for s in [
        "“菜的味道非常好，服务也很周到，下次还会再来！” → 好评",
        "“难吃死了，服务态度极差，环境也很脏，再也不来了。” → 差评",
        "“环境一般，但是菜的味道还不错，价格略贵，可以接受。” → 好评（模型抓住了“味道不错”这一主要极性）",
    ]:
        bullet(doc, s)

    h(doc, "6.4 口径 B 对照实验", 2)
    tbl_b = pd.read_csv(TAB / "model_compare_B_60w.csv")
    table(doc, tbl_b[["features", "model", "accuracy", "macro_f1", "f1_bad", "precision_bad", "recall_bad"]],
          "表 6  口径 B（三星并入差评）模型对比（60 万抽样）")
    p(doc, "口径 B 类别更平衡（好 57.8% vs 差 42.2%），但三星文本语义中性、噪声大，最佳 accuracy 仅 0.7522、"
           "macro-F1 0.7474，显著低于口径 A。该对照说明：把中性三星强行并入差评会引入大量标签噪声，"
           "口径 A（剔除三星）更合理。")

    full_csv = TAB / "model_compare_A_full.csv"
    if full_csv.exists():
        h(doc, "6.5 全量 194 万极化样本模型", 3)
        tbl_full = pd.read_csv(full_csv)
        table(doc, tbl_full[["features", "model", "accuracy", "macro_f1", "f1_bad", "precision_bad", "recall_bad"]],
              "表 7  口径 A 全量模型对比（训练 1,553,956 / 测试 388,490）")
        split = json.loads((TAB / "model_split_A_full.json").read_text(encoding="utf-8"))
        p(doc, f"全量训练数据 {split['n_train']:,} 条、测试 {split['n_test']:,} 条（好评率 {split['pos_rate']:.2%}），"
               f"最佳模型为 {split['best_features']} + {split['best_model']}，"
               f"accuracy = {split['best_accuracy']:.4f}、macro-F1 = {split['best_macro_f1']:.4f}。"
               "该模型保存于 output/models/model_A_full.joblib，可直接用于推理。")

    # ---------------- 7 词云
    h(doc, "7 词频与词云可视化（任务 9）", 1)
    p(doc, "对全部评论、好评（4–5 星）、差评（1–2 星）分别统计词频并绘制词云（微软雅黑字体，"
           "仅保留长度≥2 的词，过滤停用词）。")
    image(doc, "fig09_all_wordcloud.png", "图 4  全部评论词云（4,107,199 条）")
    image(doc, "fig09_good_wordcloud.png", "图 5  好评词云（4–5 星，1,721,499 条）")
    image(doc, "fig09_bad_wordcloud.png", "图 6  差评词云（1–2 星，220,947 条）")
    p(doc, "all 词云以“不错、味道、喜欢、环境、好吃、价格、服务员”等通用评价维度为主；"
           "好评词云中“好吃、推荐、味道、服务、环境、划算”更突出；差评词云中“难吃、态度、服务员、贵、慢、失望”显著。"
           "通过好评/差评 log-odds 对比可见，最偏向差评的词为“难吃、差、失望、慢、脏”等，最偏向好评的词为"
           "“好吃、推荐、赞、不错、划算”等。")
    for nm, cap in [("fig09_top20_all.png", "图 7  全部评论 Top20 高频词"),
                    ("fig09_top20_good.png", "图 8  好评 Top20 高频词"),
                    ("fig09_top20_bad.png", "图 9  差评 Top20 高频词")]:
        image(doc, nm, cap, width=5.2)

    # ---------------- 8 商户可视化
    h(doc, "8 商户维度可视化（任务 10）", 1)
    h(doc, "8.1 好评率 Top10 / Bottom10", 2)
    p(doc, "以极化样本计算好评率 = good/(good+bad)。由于每店样本量极不均衡（中位 3 条），"
           "仅保留极化样本≥30 的 20,563 家商户，并按 Wilson 95% 置信下界排序，以避免小样本与 1.0 并列导致的排名失真。"
           "由于头部商户好评率普遍为 100%，图中左面板用 Wilson 下界作为柱高（样本越多越高），右面板给出最低的 10 家作对照。")
    image(doc, "fig10_1_top10_ratio.png", "图 10  好评率最高 Top10 与最低 Bottom10（极化样本≥30）")
    top10 = pd.read_csv(TAB / "top10_ratio.csv")
    top10["name"] = top10["name"].fillna("（无名称）")
    table(doc, top10[["restId", "name", "n", "good", "bad", "lab", "ratio", "wilson"]].round(4),
          "表 8  好评率最高 Top10（Wilson 下界排序）")

    h(doc, "8.2 好评率随时间变化（周粒度）", 2)
    p(doc, "10.1 的 Top10 好评率均为 100%，其周好评率恒为 1，无法体现时间变化；因此本节改用“评论量 Top10”"
           "（样本充足、含少量差评）展示时间趋势。按自然周聚合好评率，周样本<3 置空，再做 4 周滚动，"
           "以降低小样本波动。")
    image(doc, "fig10_2_weekly_ratio_top10.png", "图 11  评论量 Top10 商户周滚动好评率（4 周滚动）")

    h(doc, "8.3 环境 / 口味 / 服务雷达图", 2)
    p(doc, "对 10.1 的 Top10 商户分别计算环境、口味、服务评分均值（已剔除 2.7 填充伪值），绘制雷达图。"
           "Top10 三项评分整体在 3.5–4.5 区间，口味评分普遍高于环境与服务，与实际好评率 100% 的分布一致。")
    image(doc, "fig10_3_radar_grid.png", "图 12  Top10 商户环境/口味/服务雷达图", width=6.3)
    image(doc, "fig10_3_radar_overlay.png", "图 13  Top10 三项评分叠加图", width=5.4)

    # ---------------- 9 交互
    h(doc, "9 关键字查询与单店分析（任务 11）", 1)
    p(doc, "实现 search_restaurants(keyword)：同时检索商户名称与评论文本，合并候选并按极化样本量排序；"
           "用户输入序号选择商户后，依次输出该店的评论/好评/差评词云、好评率、雷达图与周趋势。"
           "以关键词“湘”为例：名称命中 2,796 家商户（其中评论数≥50 的 278 家），选择 "
           "“57℃湘(无限度广场店)”（207 条评论、160 条极化样本、20 个活跃周）进行演示。")
    kw = pd.DataFrame({
        "关键词": ["湘", "粤", "人大", "北大", "西直门"],
        "名称命中商户数": [2796, 711, 43, 244, 118],
        "其中评论数≥50": [278, 92, 8, 33, 61],
        "推荐示例店": ["57℃湘(无限度广场店)", "粤1525", "集天小吃(人大店)", "何贤记(北大店)", "姑姑宴(西直门凯德MALL店)"],
    })
    table(doc, kw, "表 9  关键词检索可行性（restaurants.csv 名称字段）")
    image(doc, "fig11_2_rest_wordcloud_all.png", "图 14  57℃湘(无限度广场店) 全部评论词云", width=5.4)
    image(doc, "fig11_2_rest_wordcloud_good.png", "图 15  该店好评词云", width=5.2)
    image(doc, "fig11_2_rest_wordcloud_bad.png", "图 16  该店差评词云", width=5.2)
    image(doc, "fig11_3_rest_ratio.png", "图 17  该店好评率与全站基线对比", width=4.6)
    image(doc, "fig11_4_rest_radar.png", "图 18  该店环境/口味/服务雷达图（与全站均值对比）", width=5.2)
    image(doc, "fig11_5_rest_weekly_ratio.png", "图 19  该店周滚动好评率", width=6.0)

    # ---------------- 10 讨论与结论
    h(doc, "10 结论与不足", 1)
    p(doc, "本实验完整实现了题目要求的 11 项任务：数据装载与缺失处理、标签编码、清洗分词、特征构造、"
           "训练测试划分、3 类模型对比、accuracy 与混淆矩阵评估、用户输入推理、三套词云与高频词、"
           "商户好评率 Top10、周趋势、雷达图、关键词查询与单店四图分析。主要结论如下：")
    for s in [
        "数据质量是本实验的关键：27.45% 的评分是均值填充伪值、2009 年以前基本无有效评分，若不识别会直接导致标签与图表错误；",
        "中文文本情感分类在该数据上可达到 accuracy 约 94%、macro-F1 约 0.87（口径 A），差评识别是主要难点（类别不均衡 7.8:1）；",
        "把中性三星并入差评（口径 B）会使准确率降至约 0.75，说明标签口径对结论影响显著，需在报告中显式说明；",
        "商户级分析必须控制样本量：每店评论中位仅 3 条，Top10 排序需要最小样本阈值与 Wilson 平滑；",
        "词云与雷达图能直观呈现“口味 > 环境 ≈ 服务”的评价结构，与 88.62% 的极化好评率一致。",
    ]:
        bullet(doc, s)
    p(doc, "不足与改进方向：")
    for s in [
        "数据截止 2012 年 2 月，且 2009 年前无评分，时间趋势结论只适用于 2009–2012；",
        "未使用词向量/预训练模型（如 Word2Vec、BERT），后续可对比深度模型效果；",
        "评价文本与星级存在少量不一致（如高星差评），可引入人工校验或弱监督降噪；",
        "商户名称缺失 14%，图表对无名称商户使用 restId 回退显示。",
    ]:
        bullet(doc, s)

    # ---------------- 附录
    h(doc, "附录 A  源代码结构与运行说明", 1)
    p(doc, "代码位于 D:\\DSH-Workspaces\\数据科学\\综合实验1\\：src/ 为可复用模块与数据生产脚本，"
           "notebooks/ 为 5 个按任务拆分的 notebook（均已执行并保存输出），output/ 存放图表、表格与模型，cache/ 为分词缓存。")
    code_block(doc,
"""综合实验1/
├─ src/  config.py / data_utils.py / text_utils.py / agg_utils.py
│        model_utils.py / viz_utils.py
│        build_rest_agg.py / build_tokens.py / train_models.py / make_notebooks.py
├─ notebooks/
│  01_data_label.ipynb        任务 1–3
│  02_tokenize_model.ipynb    任务 4–8
│  03_wordcloud.ipynb         任务 9（+11.2 词云方法）
│  04_restaurant_viz.ipynb    任务 10
│  05_query.ipynb             任务 11
├─ output/figures|tables|models
└─ cache/  tokens_labeled.tsv.gz / cnt_*.pkl""")
    p(doc, "环境：Python 3.13.7（C:\\mlenv），pandas 3.0.5、scikit-learn 1.9.1、jieba 0.42.1、"
           "wordcloud 1.9.6、matplotlib 3.11.1；随机种子 42。复现顺序：build_rest_agg.py → build_tokens.py → "
           "train_models.py → 依次执行 5 个 notebook。")

    h(doc, "附录 B  任务—产物对照表", 1)
    mapping = pd.DataFrame({
        "任务": ["1 装载", "2 缺失值", "3 标签", "4 清洗分词", "5 特征", "6 划分", "7 模型",
                 "8 评估+推理", "9 词云/词频", "10.1 Top10", "10.2 周趋势", "10.3 雷达图",
                 "11.1 查询", "11.2-11.5 单店"],
        "代码位置": ["01", "01", "01", "02", "02", "02", "02", "02", "03", "04", "04", "04", "05", "05"],
        "结果产物": ["表 2/图 1", "3.2 节", "表 3/图 1", "表 4/缓存", "6.1 节", "6.1 节", "表 5/图 2",
                 "图 3/6.3 节", "图 4–9", "图 10/表 8", "图 11", "图 12–13", "表 9", "图 14–19"],
    })
    table(doc, mapping, "表 10  实验任务与代码、产物对照")

    doc.save(OUT)
    print("saved:", OUT)


if __name__ == "__main__":
    build()
