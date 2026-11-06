"""综合实验1《文本分析》课程汇报 PPT —— Build Mode（pptx-designer 1.0.0b11）

主题：sci-paper（白底 + 深海军蓝 + 琥珀强调），14 页，16:9。
运行：C:\\mlenv\\Scripts\\python.exe build.py
产物：exp1-text-analysis-v1.pptx（同目录）
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn as pqn
from pptx.util import Inches, Pt
from pptx_designer import Presentation
from pptx_designer.tools.cards import highlight_cards, kpi_card
from pptx_designer.tools.layout import add_slide, page_header, page_number, rect
from pptx_designer.tools.text import text

ROOT = Path(__file__).resolve().parents[2]          # 综合实验1/
FIG = ROOT / "output" / "figures"
TASK = Path(__file__).resolve().parent
OUT = TASK / "exp1-text-analysis-v1.pptx"

W, H = 13.333, 7.5
M = 0.65                      # 页边距
CW = W - 2 * M                # 内容宽 12.03
TOTAL = 14

# 主题色（来自 resolved-theme-v1.json 的 semantic_roles / colors）
C = {
    "primary": "#1E3A5F",
    "accent": "#E8A838",
    "bg": "#FFFFFF",
    "surface": "#F0F4F8",
    "ink": "#1A1A1A",
    "muted": "#6B7B8D",
    "border": "#DEE5EF",
    "danger": "#DC2626",
    "white": "#FFFFFF",
}
FONT = "Microsoft YaHei"
CF = {"font_heading": FONT, "font_body": FONT}


def rgb(hex_str: str) -> RGBColor:
    return RGBColor.from_string(hex_str.lstrip("#"))


# ---------------------------------------------------------------- 基础组件
def header(slide, title: str, subtitle: str = ""):
    page_header(slide, title, subtitle, C=CF)


def footer(slide, n: int):
    page_number(slide, n, TOTAL, C=CF)
    text(slide, M, 7.06, 6.5, 0.28, "综合实验 1 · 文本分析", font_size=8,
         color="text_muted", font_name=FONT, C=CF)
    rect(slide, M, 7.02, CW, 0.008, C["border"])


def t(slide, x, y, w, h, s, size=12, bold=False, color="text_body",
      align="left", anchor="top"):
    text(slide, x, y, w, h, s, font_size=size, bold=bold, color=color,
         align=align, font_name=FONT, C=CF, anchor=anchor)


def takeaway(slide, y, s, color=C["primary"]):
    rect(slide, M, y + 0.05, 0.06, 0.30, C["accent"])
    t(slide, M + 0.16, y, CW - 0.2, 0.40, s, size=14, bold=True, color="text_dark")


def card(slide, x, y, w, h, fill=C["surface"], line=C["border"]):
    rect(slide, x, y, w, h, fill, line=line)


def add_figure(slide, name: str, x, y, max_w, max_h, caption: str = "",
               align="left"):
    path = FIG / name
    iw, ih = Image.open(path).size
    r = min(max_w / iw, max_h / ih)
    fw, fh = iw * r, ih * r
    left = x if align == "left" else x + (max_w - fw) / 2
    pic = slide.shapes.add_picture(str(path), Inches(left), Inches(y), width=Inches(fw))
    pic.line.color.rgb = rgb(C["border"])
    pic.line.width = Pt(0.75)
    if caption:
        t(slide, x, y + fh + 0.06, max_w, 0.26, caption, size=9, color="text_muted",
          align="left" if align == "left" else "center")
    return fh


def simple_table(slide, rows, x, y, w, h, col_w=None, font_size=11,
                 header_fill=C["primary"], first_col_bold=False):
    shape = slide.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y),
                                   Inches(w), Inches(h))
    tbl = shape.table
    if col_w:
        for i, cw in enumerate(col_w):
            tbl.columns[i].width = Inches(cw)
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            cell = tbl.cell(r, c)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_left = Inches(0.06)
            cell.margin_right = Inches(0.06)
            cell.margin_top = Inches(0.02)
            cell.margin_bottom = Inches(0.02)
            cell.fill.solid()
            if r == 0:
                cell.fill.fore_color.rgb = rgb(header_fill)
            else:
                cell.fill.fore_color.rgb = rgb(C["bg"] if r % 2 else "#F7FAFC")
            cell.text = ""
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER if c else PP_ALIGN.LEFT
            run = p.add_run()
            run.text = str(val)
            run.font.size = Pt(font_size)
            run.font.name = FONT
            run.font.bold = (r == 0) or (first_col_bold and c == 0)
            run.font.color.rgb = rgb(C["white"] if r == 0 else C["ink"])
    return shape


def fix_cjk(shape):
    """把每段 run 的 eastAsia 字体也设为微软雅黑，避免中文回退成宋体。"""
    if shape.shape_type == 6:  # group
        for s in shape.shapes:
            fix_cjk(s)
        return
    if shape.has_text_frame:
        for p in shape.text_frame.paragraphs:
            for r in p.runs:
                rPr = r._r.get_or_add_rPr()
                ea = rPr.find(pqn("a:ea"))
                if ea is None:
                    ea = rPr.makeelement(pqn("a:ea"), {})
                    rPr.append(ea)
                ea.set("typeface", FONT)
    if shape.has_table:
        for row in shape.table.rows:
            for cell in row.cells:
                for p in cell.text_frame.paragraphs:
                    for r in p.runs:
                        rPr = r._r.get_or_add_rPr()
                        ea = rPr.find(pqn("a:ea"))
                        if ea is None:
                            ea = rPr.makeelement(pqn("a:ea"), {})
                            rPr.append(ea)
                        ea.set("typeface", FONT)


# ---------------------------------------------------------------- 幻灯片
def slide_cover(prs):
    s = add_slide(prs)
    # 左侧竖向强调条
    rect(s, 0.90, 1.85, 0.10, 2.05, C["primary"])
    t(s, 1.15, 1.35, 10.5, 0.4, "数据科学导论 · 综合实验 1", size=12, color="text_muted")
    t(s, 1.15, 1.80, 11.2, 1.05, "文本分析", size=52, bold=True, color="text_dark")
    t(s, 1.15, 2.95, 11.2, 0.55, "大众点评商户评论的情感分类与可视化", size=20,
      color="text_muted")
    rect(s, 1.15, 3.62, 2.30, 0.055, C["accent"])
    t(s, 1.15, 4.05, 11.0, 1.55,
      "组员：成员A（数据与模型）｜成员B（文本可视化）｜成员C（统计可视化 / 交互 / 报告）\n"
      "学号：__________　　班级：__________　　指导教师：__________\n"
      "日期：2026 年 11 月　｜　代码仓库：github.com/lovechen-520/text-analysis-exp1",
      size=12.5, color="text_body")
    t(s, 7.55, 6.25, 5.1, 0.35, "11 项任务 · 19 张结果图 · 5 个 notebook", size=12,
      color="text_muted", align="right")
    t(s, M, 6.95, 6.0, 0.3, "综合实验 1 · 文本分析", size=8, color="text_muted")


def slide_data(prs):
    s = add_slide(prs)
    header(s, "实验背景与数据", "大众点评 yf_dianping：4,107,199 条评论，241,360 家商户")
    kpis = [
        ("4,107,199", "评论条数"),
        ("241,360", "有评论商户"),
        ("1.9 GB", "主数据 · 8 列"),
        ("2003–2012", "时间跨度"),
    ]
    cw = (CW - 0.3 * 3) / 4
    for i, (num, label) in enumerate(kpis):
        kpi_card(s, M + i * (cw + 0.3), 1.50, cw, 1.55, num, label, C=CF)
    simple_table(s, [
        ["文件", "规模", "用途"],
        ["preprocessed_ratings.csv", "4,107,199 行 × 8 列，1.9 GB", "主数据（任务 3–11）"],
        ["restaurants.csv", "243,247 行 × 2 列", "商户名称检索"],
        ["links.csv", "243,247 行 × 2 列", "点评 ID 映射（未使用）"],
    ], M, 3.40, CW, 1.75, col_w=[3.3, 4.3, 4.43])
    takeaway(s, 5.55, "主数据已完成任务 1、2 的清洗与导出，本实验直接使用并复核质量")
    t(s, M, 6.15, CW, 0.6,
      "字段：userId、restId、rating、rating_env / rating_flavor / rating_service、timestamp（毫秒）、comment",
      size=12, color="text_muted")


def slide_quality(prs):
    s = add_slide(prs)
    header(s, "数据质量：三个必须先处理的问题", "不识别这三点，标签、图表与结论都会失真")
    cards = [
        ("3.6 是伪值", "1,127,570 行（27.45%）的 rating 由全局均值填充；真实评分只取整数 0–5，可用 rating==3.6 掩码剔除", C["accent"]),
        ("2009 年前无评分", "2009-07 前基本无有效星级；情感分类与时间趋势只能覆盖 2009-07～2012-02", C["primary"]),
        ("店均样本极少", "每店评论数中位仅 3 条；极化样本 ≥30 的商户只有 20,563 家，Top10 需设阈值", C["muted"]),
    ]
    highlight_cards(s, M, 1.55, cards, total_width=CW, C=CF)
    # 影响说明条
    card(s, M, 4.05, CW, 1.55, fill="#FBF7EC", line="#EAD9B0")
    t(s, M + 0.25, 4.20, CW - 0.5, 0.35, "三个直接后果", size=13, bold=True, color="text_dark")
    t(s, M + 0.25, 4.60, CW - 0.5, 0.85,
      "① 监督学习必须剔除 3.6 伪值行；② 时间序列只能从 2009 年下半年开始；"
      "③ 商户排名必须用最小样本阈值 + Wilson 下界，否则会被 1–2 条评论的店刷榜。",
      size=12, color="text_body")
    takeaway(s, 6.05, "数据质量决定了后续所有口径，而不是模型调参")


def slide_labels(prs):
    s = add_slide(prs)
    header(s, "标签构造：5 级评分 → 好评 / 差评", "口径 A（主实验）与口径 B（对照）")
    rows = [
        ["评分", "条数", "标签"],
        ["5 星", "370,067", "1 好评"],
        ["4 星", "1,351,432", "1 好评"],
        ["3 星", "1,037,168", "中性（剔除）"],
        ["2 星", "139,981", "0 差评"],
        ["1 星", "80,966", "0 差评"],
        ["0 分", "15", "异常删除"],
        ["3.6 伪值", "1,127,570", "无标签"],
    ]
    simple_table(s, rows, M, 1.55, 5.55, 3.55, col_w=[1.35, 1.75, 2.45], font_size=11)
    t(s, M, 5.25, 5.55, 1.05,
      "口径 A：4–5 星→1，1–2 星→0，三星与 3.6 剔除\n"
      "口径 B（对照）：4–5 星→1，1–3 星→0",
      size=12, color="text_body")
    add_figure(s, "fig01_label_distribution.png", 6.55, 1.60, 6.1, 3.55,
               caption="图 1  评分标签分布")
    takeaway(s, 6.15, "有效评分 2,979,614 条：好评 1,721,499 / 差评 220,947，极化好评率 88.62%")


def slide_nlp(prs):
    s = add_slide(prs)
    header(s, "文本清洗与分词", "先规则清洗，再 jieba 分词，最后去停用词")
    steps = [
        ("01  清洗", "去 URL、换行、标点与表情；仅保留中文、英文、数字"),
        ("02  分词", "jieba 精确模式 + 餐饮/点评领域词典（约 120 词）"),
        ("03  去停用词", "自建停用词表（约 500 词），过滤无意义词"),
    ]
    cw = (CW - 0.3 * 2) / 3
    for i, (title, desc) in enumerate(steps):
        card(s, M + i * (cw + 0.3), 1.50, cw, 1.45)
        t(s, M + i * (cw + 0.3) + 0.18, 1.62, cw - 0.36, 0.35, title, size=14,
          bold=True, color="text_dark")
        t(s, M + i * (cw + 0.3) + 0.18, 2.02, cw - 0.36, 0.80, desc, size=11.5,
          color="text_body")
    simple_table(s, [
        ["原始评论", "分词结果（去停用词）"],
        ["这家的火锅很好吃，服务态度也不错，就是有点贵！！！", "这家 火锅 很 好吃 服务态度 不错 有点 贵"],
        ["服务员态度极差，上菜慢得要死，再也不会来了……", "服务员 态度 极差 上菜 慢 要死 再也 不会 来"],
        ["团购的套餐，性价比很高，停车也方便。", "团购 套餐 性价比 很 高 停车 方便"],
    ], M, 3.35, CW, 1.75, col_w=[6.0, 6.03], font_size=10.5)
    t(s, M, 5.35, CW, 0.55,
      "全量 4,107,199 条 · 约 5.94 亿字符 · 16 进程 238 秒 · 词表 111 万 · 缓存 334.6 MB（2,979,614 行带标签样本）",
      size=12, color="text_muted")
    takeaway(s, 6.10, "分词结果缓存一次，供特征工程与词云复用")


def slide_features(prs):
    s = add_slide(prs)
    header(s, "特征构造与数据划分", "TF-IDF 主特征，Count 作为对照")
    simple_table(s, [
        ["特征", "参数", "用途"],
        ["TF-IDF", "word 1–2 gram，min_df=5，max_features=50,000，sublinear_tf", "主模型特征"],
        ["CountVectorizer", "max_features=30,000", "对照特征"],
    ], M, 1.55, CW, 1.45, col_w=[2.2, 7.2, 2.63], font_size=11)
    t(s, M, 3.15, CW, 0.40, "60 万极化样本分层抽样（好评率 88.63%），按 8:2 划分：", size=12,
      color="text_body")
    # 划分比例条
    bar_y, bar_h = 3.70, 0.62
    rect(s, M, bar_y, CW * 0.8, bar_h, C["primary"])
    rect(s, M + CW * 0.8, bar_y, CW * 0.2, bar_h, C["accent"])
    t(s, M + 0.2, bar_y + 0.13, 5.0, 0.35, "训练集 480,000（80%）", size=12, bold=True,
      color="text_body")
    t(s, M + CW * 0.8 + 0.1, bar_y + 0.13, 2.3, 0.35, "测试集 120,000", size=12,
      bold=True, color="text_body")
    # 补充指标卡，填充下半区
    chips = [("训练样本", "480,000"), ("测试样本", "120,000"), ("TF-IDF 特征", "50,000")]
    cw2 = (CW - 0.3 * 2) / 3
    for i, (lab, val) in enumerate(chips):
        x = M + i * (cw2 + 0.3)
        card(s, x, 4.60, cw2, 1.05)
        t(s, x + 0.2, 4.70, cw2 - 0.4, 0.3, lab, size=11, color="text_muted")
        t(s, x + 0.2, 4.98, cw2 - 0.4, 0.45, val, size=20, bold=True, color="text_dark")
    takeaway(s, 6.10, "特征矩阵：480,000 × 50,000（TF-IDF），训练与对比一次完成")


def slide_models(prs):
    s = add_slide(prs)
    header(s, "模型对比：准确率与差评识别的权衡", "口径 A，60 万抽样，TF-IDF / Count × 3 种算法")
    add_figure(s, "fig07_model_compare.png", M, 1.50, 8.05, 4.90,
               caption="图 2  各模型 accuracy 与 macro-F1 对比")
    x2 = 8.95
    card(s, x2, 1.55, 3.75, 1.55, fill="#FBF7EC", line="#EAD9B0")
    t(s, x2 + 0.2, 1.66, 3.3, 0.7, "0.9403", size=30, bold=True, color="text_dark")
    t(s, x2 + 0.2, 2.35, 3.3, 0.3, "LinearSVC · accuracy", size=10.5, color="text_muted")
    t(s, x2 + 0.2, 2.70, 3.3, 0.3, "macro-F1 0.868　差评 recall 0.88", size=10.5,
      color="text_muted")
    t(s, x2, 3.30, 3.75, 1.9,
      "朴素贝叶斯 accuracy 最高（0.9450），但差评召回仅 0.5732，偏向多数类。\n"
      "LinearSVC / 逻辑回归 macro-F1 均达 0.868，差评召回提升到 0.88–0.90。",
      size=12, color="text_body")
    takeaway(s, 6.10, "综合两类均衡性，选 LinearSVC 作为主模型")


def slide_eval(prs):
    s = add_slide(prs)
    header(s, "测试集评估与用户输入推理", "20 万演示样本：accuracy 0.9430 · macro-F1 0.8700 · 差评 recall 0.8519")
    add_figure(s, "fig08_confusion_demo.png", M, 1.50, 5.30, 4.55,
               caption="图 3  混淆矩阵（LinearSVC，20 万演示样本）")
    x2 = 6.30
    t(s, x2, 1.55, 6.2, 0.35, "用户输入推理示例（同一套清洗 / 分词 / 模型）", size=13,
      bold=True, color="text_dark")
    cases = [
        ("菜的味道非常好，服务也很周到，下次还会再来！", "好评", C["primary"]),
        ("难吃死了，服务态度极差，环境也很脏，再也不来了。", "差评", C["danger"]),
        ("环境一般，但菜的味道还不错，价格略贵，可以接受。", "好评", C["primary"]),
    ]
    y = 2.05
    for sentence, label, col in cases:
        card(s, x2, y, 6.2, 1.10)
        t(s, x2 + 0.2, y + 0.13, 4.6, 0.85, "“" + sentence + "”", size=12, color="text_body")
        t(s, x2 + 4.95, y + 0.35, 1.05, 0.4, label, size=13, bold=True, color="text_dark")
        rect(s, x2 + 6.05, y + 0.36, 0.08, 0.34, col)
        y += 1.25
    takeaway(s, 6.10, "模型能抓住“味道不错”等主要极性，可直接用于新评论")


def slide_caliber(prs):
    s = add_slide(prs)
    header(s, "口径对照与最终模型", "口径 B（三星并入差评）说明标签口径的影响")
    t(s, M, 1.50, 5.9, 0.35, "口径 B：三星并入差评（60 万抽样）", size=13, bold=True,
      color="text_dark")
    simple_table(s, [
        ["模型", "accuracy", "macro-F1"],
        ["MultinomialNB", "0.7398", "0.7210"],
        ["LogisticRegression", "0.7522", "0.7474"],
        ["LinearSVC", "0.7419", "0.7369"],
    ], M, 1.92, 5.9, 1.75, col_w=[2.9, 1.5, 1.5], font_size=11)
    t(s, M, 3.85, 5.9, 0.6,
      "口径 B 类别更平衡，但三星文本语义中性、噪声大；其“全猜好评”基线为 57.8%，"
      "最佳 accuracy 0.7522 明显低于口径 A。",
      size=11.5, color="text_body")
    x2 = 6.85
    t(s, x2, 1.50, 5.8, 0.35, "口径 A：全量 194 万极化样本（最终模型）", size=13,
      bold=True, color="text_dark")
    simple_table(s, [
        ["模型", "accuracy", "macro-F1"],
        ["MultinomialNB", "0.9475", "0.8468"],
        ["LogisticRegression", "0.9395", "0.8699"],
        ["LinearSVC", "0.9375", "0.8657"],
    ], x2, 1.92, 5.8, 1.75, col_w=[2.9, 1.45, 1.45], font_size=11)
    t(s, x2, 3.85, 5.8, 0.6,
      "训练 1,553,956 / 测试 388,490；逻辑回归 macro-F1 最高（0.8699），"
      "保存为最终推理模型。",
      size=12, color="text_body")
    # 口径 A / B 准确率对比条
    t(s, M, 4.65, CW, 0.35, "同一测试口径下的 accuracy 对比（口径 B 的全猜好评基线为 57.8%）",
      size=12, bold=True, color="text_dark")
    rows = [("口径 A（主）", 0.9395, C["primary"]),
            ("口径 B（三星并入差评）", 0.7522, C["accent"])]
    for i, (lab, val, col) in enumerate(rows):
        y = 5.05 + i * 0.48
        t(s, M + 3.55, y, 3.4, 0.32, lab, size=11.5, color="text_body")
        rect(s, M + 3.55, y + 0.03, 6.6 * val, 0.34, col)
        t(s, M + 3.55 + 6.6 * val + 0.12, y, 1.2, 0.32, f"{val:.4f}", size=13,
          bold=True, color="text_dark")
    takeaway(s, 6.10, "三星并入差评引入标签噪声，口径 A 更合理；全量模型结果与 60 万一致")


def slide_wordcloud(prs):
    s = add_slide(prs)
    header(s, "词云：好评与差评的语言差异", "全部评论 / 好评（4–5 星）/ 差评（1–2 星）")
    add_figure(s, "fig09_all_wordcloud.png", M, 1.50, 3.95, 3.10,
               caption="图 4  全部评论词云（4,107,199 条）")
    add_figure(s, "fig09_good_wordcloud.png", 4.80, 1.50, 3.95, 3.10,
               caption="图 5  好评词云（1,721,499 条）")
    add_figure(s, "fig09_bad_wordcloud.png", 8.95, 1.50, 3.75, 3.10,
               caption="图 6  差评词云（220,947 条）")
    # 好评 / 差评 Top10 高频词对照
    t(s, M, 4.85, 5.9, 0.32, "好评高频词 Top10", size=12, bold=True, color="text_dark")
    t(s, M, 5.20, 5.9, 0.70,
      "好吃 · 推荐 · 味道 · 服务 · 环境 · 喜欢 · 不错 · 价格 · 实惠 · 朋友",
      size=12, color="text_body")
    t(s, 6.95, 4.85, 5.7, 0.32, "差评高频词 Top10", size=12, bold=True, color="text_dark")
    t(s, 6.95, 5.20, 5.7, 0.70,
      "难吃 · 态度 · 服务员 · 贵 · 慢 · 失望 · 环境 · 差 · 服务 · 价格",
      size=12, color="text_body")
    takeaway(s, 6.05, "好评偏“好吃 / 推荐 / 味道 / 服务”，差评偏“难吃 / 态度 / 服务员 / 贵 / 慢”")


def slide_top10(prs):
    s = add_slide(prs)
    header(s, "商户好评率 Top10 / Bottom10", "极化样本≥30，Wilson 95% 下界排序，避免小样本刷榜")
    add_figure(s, "fig10_1_top10_ratio.png", M, 1.50, 8.35, 4.75,
               caption="图 10  好评率最高 Top10 与最低 Bottom10")
    x2 = 9.20
    rows = [
        ["商户（Top10 节选）", "n", "好评率"],
        ["海底捞(邯郸路店)", "203", "1.000"],
        ["比萨马上诺(上海商城店)", "174", "1.000"],
        ["王品台塑牛排(徐家汇店)", "171", "1.000"],
        ["檬舒舒(久光百货店)", "204", "0.994"],
    ]
    simple_table(s, rows, x2, 1.95, 3.45, 1.75, col_w=[2.25, 0.45, 0.75], font_size=9.5)
    t(s, x2, 3.85, 3.5, 1.7,
      "好评率 = 好评 /(好评 + 差评)；\n"
      "头部 10 家均为 100%（Wilson 下界区分样本量）；\n"
      "Bottom10 为 0%–12%，差异真实存在。",
      size=11, color="text_body")
    takeaway(s, 6.10, "样本量控制 + 置信下界，才能让“好评率排名”有意义")


def slide_trend(prs):
    s = add_slide(prs)
    header(s, "时间趋势与评分结构", "周滚动好评率 + 环境 / 口味 / 服务雷达图")
    add_figure(s, "fig10_2_weekly_ratio_top10.png", M, 1.50, 7.55, 4.55,
               caption="图 11  评论量 Top10 商户周滚动好评率（4 周滚动，周样本<3 置空）")
    add_figure(s, "fig10_3_radar_overlay.png", 8.45, 1.50, 4.20, 4.55,
               caption="图 13  Top10 三项评分叠加图")
    takeaway(s, 6.10, "周好评率在 0.85–1.0 波动；三项评分中口味最高、环境≈服务")


def slide_query(prs):
    s = add_slide(prs)
    header(s, "关键词查询与单店分析", "示例：关键词“湘” → 57℃湘(无限度广场店)")
    add_figure(s, "fig11_5_rest_weekly_ratio.png", M, 1.50, 7.30, 4.55,
               caption="图 19  该店周滚动好评率（20 个活跃周）")
    x2 = 8.30
    steps = ["输入关键词（名称或评论）", "候选列表按样本量排序", "选择商户 → 四张图",
             "词云 / 好评率 / 雷达图 / 周趋势"]
    y = 1.60
    for i, st in enumerate(steps):
        rect(s, x2, y, 0.30, 0.30, C["accent"])
        t(s, x2 + 0.02, y + 0.02, 0.28, 0.26, str(i + 1), size=11, bold=True,
          color="text_dark", align="center")
        t(s, x2 + 0.42, y, 4.0, 0.32, st, size=12, color="text_body")
        y += 0.48
    t(s, x2, 3.95, 4.3, 1.15,
      "演示店：207 条评论 / 160 条极化样本 / 20 个活跃周；\n"
      "好评率 0.944，环境 4.1 / 口味 4.4 / 服务 4.0。",
      size=11, color="text_body")
    card(s, x2, 5.25, 4.20, 1.00, fill="#FBF7EC", line="#EAD9B0")
    t(s, x2 + 0.18, 5.34, 2.4, 0.55, "0.944", size=22, bold=True, color="text_dark")
    t(s, x2 + 0.18, 5.82, 3.9, 0.3, "该店好评率（全站 88.62%）", size=10, color="text_muted")
    takeaway(s, 6.55, "search_restaurants() + 单店四图，可复用到任意商户")


def slide_close(prs):
    s = add_slide(prs)
    header(s, "结论与分工", "完成 11 项任务；数据质量与口径决定结论")
    items = [
        ("完成度", "11 项任务全部实现：清洗分词、TF-IDF、3 模型对比、词云、商户可视化、单店查询"),
        ("主结果", "口径 A：LinearSVC accuracy 0.9403 / macro-F1 0.868；全量 194 万 0.9395 / 0.8699"),
        ("关键判断", "3.6 伪值必须掩码剔除；2009-07 前无评分；Top10 需样本阈值 + Wilson 平滑"),
        ("可视化", "好评 88.62%；词云呈“口味 > 环境 ≈ 服务”；单店四图可交互复用"),
    ]
    y = 1.50
    for title, desc in items:
        rect(s, M, y + 0.06, 0.06, 0.42, C["accent"])
        t(s, M + 0.18, y, 1.35, 0.40, title, size=12.5, bold=True, color="text_dark")
        t(s, M + 1.60, y, CW - 1.7, 0.55, desc, size=12, color="text_body")
        y += 0.72
    t(s, M, 4.55, 5.8, 0.35, "不足与改进", size=12.5, bold=True, color="text_dark")
    t(s, M, 4.92, 6.2, 1.15,
      "数据止于 2012 年且 2009-07 前无评分；未使用预训练模型对比；"
      "评论与星级存在少量不一致；商户名称缺失 14%。",
      size=11, color="text_muted")
    t(s, 7.25, 4.55, 5.4, 0.35, "分工与致谢", size=12.5, bold=True, color="text_dark")
    t(s, 7.25, 4.92, 5.4, 1.15,
      "成员A：数据与模型\n成员B：文本可视化\n成员C：统计可视化 + 交互 + 报告 / PPT",
      size=11, color="text_body")
    t(s, M, 6.45, CW, 0.45, "谢谢！欢迎提问", size=20, bold=True, color="text_dark")


# ---------------------------------------------------------------- 主流程
def main():
    theme = json.loads((TASK / "resolved-theme-v1.json").read_text(encoding="utf-8"))
    prs = Presentation(theme=theme, strict_theme=True)
    builders = [slide_cover, slide_data, slide_quality, slide_labels, slide_nlp,
                slide_features, slide_models, slide_eval, slide_caliber,
                slide_wordcloud, slide_top10, slide_trend, slide_query, slide_close]
    for i, fn in enumerate(builders):
        fn(prs)
        if i > 0:
            footer(prs.slides[i], i + 1)
    # 页脚页码：封面不编号，内容页 2–14
    for shape in list(prs.slides)[1:]:
        pass
    for s in list(prs.slides):
        for shape in list(s.shapes):
            fix_cjk(shape)
    prs.save(str(OUT))
    print("saved:", OUT)


if __name__ == "__main__":
    main()
