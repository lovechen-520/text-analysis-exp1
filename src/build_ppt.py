"""生成《综合实验1 文本分析》汇报 PPT（16:9）。

依赖：python-pptx、pandas（用 DSH 自带 Python 运行）
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "output" / "figures"
TAB = ROOT / "output" / "tables"
OUT = ROOT / "综合实验1_汇报PPT.pptx"

C_BLUE = RGBColor(0x1F, 0x4E, 0x79)
C_RED = RGBColor(0xE4, 0x57, 0x2E)
C_DARK = RGBColor(0x2B, 0x2B, 0x2B)
C_GRAY = RGBColor(0x66, 0x66, 0x66)
C_LIGHT = RGBColor(0xF2, 0xF5, 0xF9)

W, H = Inches(13.333), Inches(7.5)


def blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def bg(slide, color=C_LIGHT):
    from pptx.enum.shapes import MSO_SHAPE
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, H)
    shp.fill.solid()
    shp.fill.fore_color.rgb = color
    shp.line.fill.background()
    return shp


def textbox(slide, x, y, w, h, text, size=18, bold=False, color=C_DARK,
            align=PP_ALIGN.LEFT, font="微软雅黑"):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    lines = text.split("\n")
    for i, line in enumerate(lines):
        par = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        par.alignment = align
        run = par.add_run()
        run.text = line
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = color
        run.font.name = font
    return tb


def title_bar(slide, title, sub=""):
    bar = slide.shapes.add_shape(1, 0, 0, W, Inches(1.05))
    bar.fill.solid()
    bar.fill.fore_color.rgb = C_BLUE
    bar.line.fill.background()
    textbox(slide, Inches(0.45), Inches(0.18), Inches(12), Inches(0.7),
            title, size=26, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF))
    if sub:
        textbox(slide, Inches(0.45), Inches(1.12), Inches(12), Inches(0.4),
                sub, size=13, color=C_GRAY)


def bullets(slide, items, x=Inches(0.7), y=Inches(1.7), w=Inches(6.0), h=Inches(5.2), size=17):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        par = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        par.space_after = Pt(10)
        run = par.add_run()
        run.text = "• " + item
        run.font.size = Pt(size)
        run.font.color.rgb = C_DARK
        run.font.name = "微软雅黑"
    return tb


def picture(slide, filename, x, y, w=None, h=None):
    path = FIG / filename
    if not path.exists():
        textbox(slide, x, y, Inches(6), Inches(0.5), f"[缺少 {filename}]", color=C_GRAY)
        return
    if w:
        slide.shapes.add_picture(str(path), x, y, width=w)
    else:
        slide.shapes.add_picture(str(path), x, y, height=h)


def table(slide, df, x, y, w, h, font=11):
    rows, cols = df.shape
    shape = slide.shapes.add_table(rows + 1, cols, x, y, w, h)
    tbl = shape.table
    for j, col in enumerate(df.columns):
        cell = tbl.cell(0, j)
        cell.text = str(col)
        for par in cell.text_frame.paragraphs:
            for run in par.runs:
                run.font.size = Pt(font)
                run.font.bold = True
    for i, (_, row) in enumerate(df.iterrows(), start=1):
        for j, val in enumerate(row):
            cell = tbl.cell(i, j)
            cell.text = "" if pd.isna(val) else str(val)
            for par in cell.text_frame.paragraphs:
                for run in par.runs:
                    run.font.size = Pt(font)
    return shape


def page_no(slide, n):
    textbox(slide, W - Inches(1.0), H - Inches(0.55), Inches(0.6), Inches(0.35),
            str(n), size=12, color=C_GRAY, align=PP_ALIGN.RIGHT)


def build():
    prs = Presentation()
    prs.slide_width = W
    prs.slide_height = H
    n = 0

    # 1 封面
    n += 1
    s = blank(prs); bg(s, C_BLUE)
    textbox(s, Inches(1.0), Inches(2.0), Inches(11.3), Inches(1.2),
            "综合实验 1  《文本分析》", size=44, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF))
    textbox(s, Inches(1.0), Inches(3.3), Inches(11.3), Inches(0.8),
            "大众点评商户评论的情感分类与可视化", size=24, color=RGBColor(0xDD, 0xE8, 0xF2))
    textbox(s, Inches(1.0), Inches(4.6), Inches(11.3), Inches(1.6),
            "小组成员：成员A（数据与模型）｜成员B（文本可视化）｜成员C（统计可视化 / 交互 / 报告）\n"
            "学号：____________　　日期：2026 年 11 月",
            size=16, color=RGBColor(0xFF, 0xFF, 0xFF))

    # 2 目标与数据
    n += 1
    s = blank(prs); title_bar(s, "实验目标与数据集")
    bullets(s, [
        "完成中文文本分析全流程：装载 → 缺失值 → 标签 → 清洗分词 → 特征 → 模型 → 评估",
        "文本可视化：all / 好评 / 差评 词云与高频词",
        "商户维度：好评率 Top10、周趋势、环境/口味/服务雷达图",
        "交互查询：关键词检索商户 → 单店四图分析",
    ], w=Inches(6.9))
    df = pd.DataFrame({
        "项目": ["评论数", "商户数", "字段", "时间跨度", "极化好评率"],
        "数值": ["4,107,199", "241,360", "8 列", "2003-04 ~ 2012-02", "88.62%"],
    })
    table(s, df, Inches(7.7), Inches(1.9), Inches(5.2), Inches(2.6), font=13)
    textbox(s, Inches(7.7), Inches(4.9), Inches(5.2), Inches(1.6),
            "数据：大众点评 yf_dianping\n主文件：preprocessed_ratings.csv（任务 1、2 产物）",
            size=12, color=C_GRAY)

    # 3 数据质量
    n += 1
    s = blank(prs); title_bar(s, "数据质量三大发现（决定后续口径）")
    bullets(s, [
        "评分缺失被均值填充为 3.6：1,127,570 行（27.45%），非真实评分 → 必须剔除",
        "2009-12 以前几乎没有有效星级 → 情感分类 / 时间趋势只能覆盖 2009-07 ~ 2012-02",
        "样本长尾：每店评论中位 3 条；极化样本≥30 的商户仅 20,563 家 → Top10 需阈值 + Wilson 平滑",
        "商户名称缺失 14%；数据实为“商户点评”，含超市/博物馆/酒吧等",
    ], w=Inches(12.2), size=18)

    # 4 标签与分布
    n += 1
    s = blank(prs); title_bar(s, "数据预处理与标签构造（任务 1–3）")
    bullets(s, [
        "口径 A（主）：4–5 星→1，1–2 星→0；3 星、3.6 伪值剔除",
        "口径 B（对照）：4–5 星→1，1–3 星→0",
        "有效评分 2,979,629 条；好评 1,721,499 / 差评 220,962",
        "全猜好评基线 accuracy = 88.63%，需看 macro-F1 与混淆矩阵",
    ], w=Inches(5.6), size=15)
    picture(s, "fig01_label_distribution.png", Inches(6.3), Inches(1.5), w=Inches(6.6))

    # 5 清洗分词
    n += 1
    s = blank(prs); title_bar(s, "文本清洗与分词（任务 4）")
    bullets(s, [
        "清洗：去 URL / 换行 / 标点 / 表情，仅保留中英文数字",
        "jieba 精确模式 + 餐饮领域词典（120 词）+ 公开停用词表（四表合并 2,437 词）",
        "全量 594 M 字符，16 进程分词 215 s，词表 111 万",
        "缓存 2,979,614 行带标签分词，特征与词云复用",
    ], w=Inches(6.4), size=15)
    sample = pd.DataFrame({
        "原始": ["这家火锅很好吃，服务也不错", "服务员态度极差，上菜很慢"],
        "分词": ["这家 火锅 很 好吃 服务 不错", "服务员 态度 极差 上菜 很 慢"],
    })
    table(s, sample, Inches(7.2), Inches(2.0), Inches(5.6), Inches(1.2), font=12)

    # 6 特征与划分
    n += 1
    s = blank(prs); title_bar(s, "特征工程与数据划分（任务 5–6）")
    bullets(s, [
        "TF-IDF：word 1–2 gram，min_df=5，max_features=50,000，sublinear_tf",
        "CountVectorizer：max_features=30,000",
        "60 万分层抽样（好评率 88.63%），8:2 分层划分：48 万训练 / 12 万测试",
        "随机种子 42，模型对比全程固定同一划分",
    ], w=Inches(12.0), size=18)

    # 7 模型对比
    n += 1
    s = blank(prs); title_bar(s, "模型对比（任务 7）", "60 万抽样；TF-IDF / Count × 3 模型")
    picture(s, "fig07_model_compare.png", Inches(0.6), Inches(1.45), w=Inches(8.6))
    tbl = pd.read_csv(TAB / "model_compare_A_60w.csv")
    show = tbl[["model", "features", "accuracy", "macro_f1", "recall_bad"]].round(4)
    table(s, show, Inches(9.4), Inches(1.7), Inches(3.6), Inches(2.2), font=9)

    # 8 混淆矩阵 + 推理
    n += 1
    s = blank(prs); title_bar(s, "评估与推理演示（任务 8）")
    picture(s, "fig08_confusion_demo.png", Inches(0.6), Inches(1.5), w=Inches(5.6))
    bullets(s, [
        "演示 20 万：accuracy 0.9371，macro-F1 0.8573",
        "差评：precision 0.6835 / recall 0.8323",
        "好评：precision 0.9779 / recall 0.9505",
        "推理示例 → “味道非常好…” = 好评；“难吃死了…” = 差评",
    ], x=Inches(6.6), y=Inches(1.6), w=Inches(6.1), size=15)

    # 9 口径 A/B
    n += 1
    s = blank(prs); title_bar(s, "标签口径对照：A（主）vs B（三星并入差评）")
    ta = pd.read_csv(TAB / "model_compare_A_60w.csv")
    tb = pd.read_csv(TAB / "model_compare_B_60w.csv")
    df = pd.DataFrame({
        "口径": ["A 主（剔除三星）", "B 对照（三星并入差评）"],
        "最佳模型": ["LogisticRegression (tfidf)", "LogisticRegression (tfidf)"],
        "accuracy": [ta["accuracy"].max(), tb["accuracy"].max()],
        "macro-F1": [ta["macro_f1"].max(), tb["macro_f1"].max()],
        "差评 recall": [0.8905, 0.7144],
    }).round(4)
    table(s, df, Inches(1.2), Inches(2.0), Inches(11.0), Inches(1.6), font=15)
    textbox(s, Inches(1.2), Inches(4.3), Inches(11.0), Inches(1.6),
            "结论：三星文本语义中性、噪声大，强行并入差评使 accuracy 由 0.933 降至 0.742；\n"
            "因此主实验采用口径 A，并在报告中显式说明该选择。",
            size=16, color=C_DARK)

    # 10 词云 all
    n += 1
    s = blank(prs); title_bar(s, "词云与高频词（任务 9）", "全部评论 4,107,199 条")
    picture(s, "fig09_all_wordcloud.png", Inches(0.5), Inches(1.4), w=Inches(8.0))
    bullets(s, ["不错 / 味道 / 喜欢 / 环境 / 好吃 / 价格 / 服务员", "反映点评文本的通用评价维度"],
            x=Inches(8.7), y=Inches(2.2), w=Inches(4.3), size=15)

    # 11 好/差词云
    n += 1
    s = blank(prs); title_bar(s, "好评 vs 差评词云", "好评 1,721,499 条 / 差评 220,947 条")
    picture(s, "fig09_good_wordcloud.png", Inches(0.4), Inches(1.5), w=Inches(6.2))
    picture(s, "fig09_bad_wordcloud.png", Inches(6.8), Inches(1.5), w=Inches(6.2))
    textbox(s, Inches(0.6), Inches(6.3), Inches(12), Inches(0.6),
            "好评偏“好吃 / 推荐 / 味道 / 服务 / 环境 / 划算”；差评偏“难吃 / 态度 / 服务员 / 贵 / 慢 / 失望”",
            size=14, color=C_DARK)

    # 12 Top10
    n += 1
    s = blank(prs); title_bar(s, "商户好评率 Top10 / Bottom10（任务 10.1）",
                              "极化样本≥30；Wilson 95% 下界排序")
    picture(s, "fig10_1_top10_ratio.png", Inches(0.4), Inches(1.5), w=Inches(12.5))
    textbox(s, Inches(0.5), Inches(6.4), Inches(12.3), Inches(0.6),
            "头部 10 家好评率均为 100%，用 Wilson 下界区分样本量；右图为最低 10 家（0%–12%）",
            size=13, color=C_GRAY)

    # 13 周趋势
    n += 1
    s = blank(prs); title_bar(s, "周好评率趋势（任务 10.2）", "评论量 Top10；4 周滚动，周样本<3 置空")
    picture(s, "fig10_2_weekly_ratio_top10.png", Inches(0.5), Inches(1.5), w=Inches(9.6))
    bullets(s, ["Top10 集中于 2011-08 ~ 2012-02", "周有效样本中位 4–10 条", "曲线在 0.85–1.0 区间波动"],
            x=Inches(10.3), y=Inches(1.9), w=Inches(2.6), size=13)

    # 14 雷达图
    n += 1
    s = blank(prs); title_bar(s, "环境 / 口味 / 服务雷达图（任务 10.3）", "Top10 商户三项评分均值")
    picture(s, "fig10_3_radar_grid.png", Inches(0.5), Inches(1.4), w=Inches(9.4))
    bullets(s, ["口味评分最高", "环境 ≈ 服务", "整体 3.5–4.5 分", "与 88.62% 好评率一致"],
            x=Inches(10.2), y=Inches(2.0), w=Inches(2.8), size=14)

    # 15 单店查询
    n += 1
    s = blank(prs); title_bar(s, "关键词查询与单店分析（任务 11）", "示例：关键词“湘” → 57℃湘(无限度广场店)")
    picture(s, "fig11_3_rest_ratio.png", Inches(0.4), Inches(1.5), w=Inches(4.2))
    picture(s, "fig11_4_rest_radar.png", Inches(4.8), Inches(1.5), w=Inches(4.2))
    picture(s, "fig11_5_rest_weekly_ratio.png", Inches(0.4), Inches(4.4), w=Inches(8.6))
    textbox(s, Inches(9.2), Inches(1.6), Inches(3.8), Inches(4.5),
            "关键词同时检索名称与评论\n\n"
            "以“湘”为例：命中 2,796 家（≥50 条评论 278 家）\n\n"
            "选择店：207 条评论 / 160 极化 / 20 个活跃周\n\n"
            "输出：词云、好评率、雷达图、周趋势",
            size=13, color=C_DARK)

    # 16 结论
    n += 1
    s = blank(prs); title_bar(s, "结论与分工")
    bullets(s, [
        "完成 11 项任务：清洗分词、TF-IDF 特征、3 模型对比、accuracy 0.933 / macro-F1 0.857",
        "数据质量决定结论：3.6 伪值、2009 前无评分、样本长尾必须显式处理",
        "可视化覆盖词云、Top10、周趋势、雷达图、单店交互",
        "不足：数据止于 2012、未用预训练模型、名称缺失 14%",
        "分工：A 数据与模型｜B 文本可视化｜C 统计可视化 + 交互 + 报告 / PPT",
    ], w=Inches(12.2), size=17)
    textbox(s, Inches(0.7), Inches(5.9), Inches(12), Inches(0.6),
            "谢谢！欢迎提问", size=22, bold=True, color=C_BLUE)

    prs.save(OUT)
    print("saved:", OUT)


if __name__ == "__main__":
    build()
