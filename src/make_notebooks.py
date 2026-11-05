"""生成 notebook（用 nbformat 构建，便于版本管理与重复生成）。

用法：
    python make_notebooks.py 02 03 04 05     # 生成指定编号
    python make_notebooks.py all
生成后配合：
    jupyter nbconvert --to notebook --execute --inplace notebooks/<名称>.ipynb
"""
from __future__ import annotations

import sys
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
NB_DIR = ROOT / "notebooks"


def new_nb(*, title: str):
    nb = nbf.v4.new_notebook()
    nb["metadata"] = {
        "kernelspec": {"display_name": "Python (mlenv)", "language": "python", "name": "mlenv"},
        "language_info": {"name": "python", "version": "3.13.7"},
    }
    return nb


def add(nb, kind: str, src: str):
    if kind == "md":
        nb["cells"].append(nbf.v4.new_markdown_cell(src))
    else:
        nb["cells"].append(nbf.v4.new_code_cell(src))


def build_02() -> Path:
    nb = new_nb(title="任务4-8")
    md = lambda s: add(nb, "md", s)
    code = lambda s: add(nb, "code", s)

    md("""# 综合实验 1 文本分析 · 任务 4–8：清洗分词、特征、模型与评估

- 分词缓存：`cache/tokens_labeled.tsv.gz`（2,979,614 行，由 `src/build_tokens.py` 全量生成，耗时 238 s / 16 进程）
- 本 notebook 演示完整链路：用 20 万抽样快速训练；
- **主对比结果（60 万抽样）与全量模型**由 `src/train_models.py` 产出，见 `output/tables/model_compare_A_60w.csv` 与 `output/models/`。""")

    code("""import sys, time
import numpy as np
import pandas as pd
from IPython.display import Image, display

SRC = "D:/DSH-Workspaces/数据科学/综合实验1/src"
sys.path.insert(0, SRC)

from config import CACHE, TAB, FIG, MODEL
import data_utils, text_utils, model_utils as mu, viz_utils
from text_utils import clean_text, tokenize

text_utils.ensure_init(str(CACHE.parent / "stopwords.txt"), str(CACHE.parent / "userdict.txt"))
viz_utils.set_cn_font()
pd.set_option("display.width", 160)
print("环境就绪")""")

    md("""## 任务 4：评论清洗、去停用词与分词

清洗规则：去 URL → 去换行/制表符 → 仅保留中文/英文/数字 → 压缩空格。
分词：jieba 精确模式 + 停用词表 + 餐饮领域自定义词典。""")

    code("""samples = [
    "这家的火锅很好吃，服务态度也不错，就是有点贵！！！O(∩_∩)O",
    "环境一般般，但是菜的味道真的不错，推荐大家来试试~",
    "服务员态度极差，上菜慢得要死，再也不会来了……",
    "http://www.dianping.com 团购的套餐，性价比很高，停车也方便。",
    "第三次来了，还是一如既往的好吃，老板娘人很好，下次还来。",
]
rows = []
for s in samples:
    rows.append({"原始评论": s,
                 "清洗后": clean_text(s),
                 "分词结果": " / ".join(tokenize(s))})
pd.DataFrame(rows)""")

    code("""import json
man = json.load(open(CACHE / "token_manifest.json", encoding="utf-8"))
print("全量分词概况:", {k: man[k] for k in ["rows", "workers", "elapsed_sec", "vocab_all"]})
print("缓存文件:", (CACHE / "tokens_labeled.tsv.gz").exists())""")

    md("## 任务 5：Count / TF-IDF 特征构造 + 任务 6：训练/测试划分")

    code("""t0 = time.time()
df = mu.load_tokens()
print("带标签分词缓存:", df.shape, "| 读取耗时 %.1fs" % (time.time() - t0))
print("标签分布:", df["label"].value_counts().to_dict())""")

    code("""SAMPLE_N = 200_000          # 演示抽样；主实验为 60 万，最终版为全量 194 万
df_a = mu.apply_scheme(df, "A")
df_s = mu.stratified_sample(df_a, SAMPLE_N)
X_tr, X_te, y_tr, y_te = mu.split_data(df_s)
print("口径A 演示样本:", len(df_s), "| train:", len(X_tr),
      "| test:", len(X_te), "| 好评率: %.4f" % y_tr.mean())""")

    code("""# TF-IDF（词级 1-2 gram）
t0 = time.time()
tfidf = mu.make_tfidf(max_features=50_000, min_df=5, ngram_range=(1, 2))
Xtr = tfidf.fit_transform(X_tr)
Xte = tfidf.transform(X_te)
print("TF-IDF 矩阵:", Xtr.shape, "| 特征数:", len(tfidf.vocabulary_), "| 耗时 %.1fs" % (time.time() - t0))

# CountVectorizer（对照特征）
t0 = time.time()
count = mu.make_count(max_features=30_000, min_df=5)
Ctr = count.fit_transform(X_tr)
Cte = count.transform(X_te)
print("Count 矩阵:", Ctr.shape, "| 耗时 %.1fs" % (time.time() - t0))""")

    code("""# TF-IDF / Count 前 10 个高频特征词（按词频）
cv = count.vocabulary_
freq = np.asarray(Ctr.sum(axis=0)).ravel()
top_idx = np.argsort(freq)[-10:][::-1]
inv = {v: k for k, v in cv.items()}
pd.DataFrame({"特征词": [inv[i] for i in top_idx], "词频": [int(freq[i]) for i in top_idx]})""")

    md("## 任务 7：训练二值分类模型（3 种算法对比）")

    code("""t0 = time.time()
res = mu.train_and_evaluate(Xtr, y_tr, Xte, y_te, features="tfidf")
demo = res.drop(columns=["estimator", "pred"])
print("演示训练+评估耗时 %.1fs" % (time.time() - t0))
demo""")

    code("""# 主实验对比表（60 万抽样，由 src/train_models.py 产出）
main_tbl = pd.read_csv(TAB / "model_compare_A_60w.csv")
main_tbl""")

    code("""fig = viz_utils.plot_model_compare(main_tbl, "fig07_model_compare.png",
                                   "口径A 模型对比（60 万抽样，TF-IDF / Count）")
display(Image(filename=str(fig)))""")

    md("## 任务 8：测试集 accuracy、混淆矩阵与用户输入推理")

    code("""best = res.sort_values(["macro_f1", "accuracy"], ascending=False).iloc[0]
print("演示最佳模型:", best["model"],
      "| accuracy=%.4f | macro-F1=%.4f" % (best["accuracy"], best["macro_f1"]))
print(mu.evaluation_text(y_te, best["pred"], title="演示 20 万：" + best["model"]))""")

    code("""import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay
fig, ax = plt.subplots(figsize=(5, 4))
ConfusionMatrixDisplay.from_predictions(
    y_te, best["pred"], display_labels=["差评(0)", "好评(1)"],
    cmap="Blues", ax=ax, colorbar=False)
ax.set_title("混淆矩阵（演示 20 万）")
fig.tight_layout()
out = FIG / "fig08_confusion_demo.png"
fig.savefig(out, dpi=200)
plt.close(fig)
display(Image(filename=str(out)))""")

    code("""# 用主实验（60 万）保存的模型做推理演示
vec = mu.load_model(MODEL / "vectorizer_A_60w.joblib")
clf = mu.load_model(MODEL / "model_A_60w.joblib")
cases = [
    "菜的味道非常好，服务也很周到，下次还会再来！",
    "难吃死了，服务态度极差，环境也很脏，再也不来了。",
    "环境一般，但是菜的味道还不错，价格略贵，可以接受。",
]
for c in cases:
    print(f"[{mu.predict_sentiment(c, vec, clf)}] {c}")""")

    md("""## 小结

- 全量 2,979,614 条带标签评论完成多进程分词（238 s）；构造 TF-IDF（5 万特征）与 Count（3 万特征）两套特征；
- 口径 A 主实验准确率约 0.9+；差评类 recall 受 7.8:1 不平衡影响，报告同时给出 macro-F1 与逐类指标；
- `predict_sentiment(text, vectorizer, clf)` 可对新评论直接输出好评/差评。""")

    out = NB_DIR / "02_tokenize_model.ipynb"
    nbf.write(nb, str(out))
    return out


def build_03() -> Path:
    nb = new_nb(title="任务9")
    md = lambda s: add(nb, "md", s)
    code = lambda s: add(nb, "code", s)

    md("""# 综合实验 1 文本分析 · 任务 9：全部 / 好评 / 差评词频与词云

- 词频来自 `src/build_tokens.py` 全量分词时顺带统计的 3 个 Counter（无需二次扫描）；
- 词云字体：`C:/Windows/Fonts/msyh.ttc`（微软雅黑）；
- all = 4,107,199 条；好评 = 4–5 星（1,721,499 条）；差评 = 1–2 星（220,947 条）。""")

    code("""import sys, pickle
import numpy as np
import pandas as pd
from IPython.display import Image, display

SRC = "D:/DSH-Workspaces/数据科学/综合实验1/src"
sys.path.insert(0, SRC)
from config import CACHE, TAB
import viz_utils

viz_utils.set_cn_font()
pd.set_option("display.width", 160)

def load_counter(name):
    with open(CACHE / name, "rb") as f:
        return pickle.load(f)

cnt_all = load_counter("cnt_all.pkl")
cnt_good = load_counter("cnt_good.pkl")
cnt_bad = load_counter("cnt_bad.pkl")
print("词表规模: all=%d | 好评=%d | 差评=%d" % (len(cnt_all), len(cnt_good), len(cnt_bad)))
print("词条总量: all=%d | 好评=%d | 差评=%d" % (
    sum(cnt_all.values()), sum(cnt_good.values()), sum(cnt_bad.values())))""")

    code("""def top_table(counter, topn=20, name="词频"):
    t = pd.DataFrame(counter.most_common(topn), columns=["词", name])
    t.index = np.arange(1, len(t) + 1)
    return t

print("=== all Top20 ===")
display(top_table(cnt_all, 20, "all频次"))
print("=== 好评 Top20 ===")
display(top_table(cnt_good, 20, "好评频次"))
print("=== 差评 Top20 ===")
display(top_table(cnt_bad, 20, "差评频次"))""")

    code("""fig = viz_utils.plot_wordcloud(cnt_all, "全部评论词云（4,107,199 条）",
                               "fig09_all_wordcloud.png", max_words=160, cmap="viridis")
display(Image(filename=str(fig)))""")

    code("""fig = viz_utils.plot_wordcloud(cnt_good, "好评词云（4–5 星，1,721,499 条）",
                               "fig09_good_wordcloud.png", max_words=160, cmap="spring")
display(Image(filename=str(fig)))""")

    code("""fig = viz_utils.plot_wordcloud(cnt_bad, "差评词云（1–2 星，220,947 条）",
                               "fig09_bad_wordcloud.png", max_words=160, cmap="autumn")
display(Image(filename=str(fig)))""")

    code("""figs = []
figs.append(viz_utils.plot_top_words(cnt_all, "全部评论 Top20 高频词", "fig09_top20_all.png", color="#2e6f95"))
figs.append(viz_utils.plot_top_words(cnt_good, "好评 Top20 高频词", "fig09_top20_good.png", color="#e4572e"))
figs.append(viz_utils.plot_top_words(cnt_bad, "差评 Top20 高频词", "fig09_top20_bad.png", color="#17a398"))
for f in figs:
    display(Image(filename=str(f)))""")

    code("""# 好评 vs 差评 区分词（对数比 log-odds，取两边频次都 >= 1000 的词）
tot_g = sum(cnt_good.values()); tot_b = sum(cnt_bad.values())
words = [w for w in set(cnt_good) | set(cnt_bad)
         if cnt_good.get(w, 0) >= 1000 and cnt_bad.get(w, 0) >= 1000]
rows = []
for w in words:
    pg = cnt_good.get(w, 0) / tot_g
    pb = cnt_bad.get(w, 0) / tot_b
    rows.append((w, cnt_good.get(w, 0), cnt_bad.get(w, 0),
                 float(np.log((pg + 1e-12) / (pb + 1e-12)))))
cmp = pd.DataFrame(rows, columns=["词", "好评频次", "差评频次", "log_odds"]).sort_values("log_odds")
print("偏向差评的词 Top15:"); display(cmp.head(15))
print("偏向好评的词 Top15:"); display(cmp.tail(15).iloc[::-1])""")

    md("""## 小结

- all 词云以「不错 / 味道 / 喜欢 / 环境 / 好吃 / 价格 / 服务员」为主，反映点评文本的通用维度；
- 好评词云偏「好吃 / 推荐 / 味道 / 服务 / 环境 / 划算」，差评词云偏「难吃 / 态度 / 服务员 / 贵 / 慢 / 失望」；
- 好评/差评 log-odds 对比表可直接用于报告"情感差异"分析。""")

    out = NB_DIR / "03_wordcloud.ipynb"
    nbf.write(nb, str(out))
    return out


def build_04() -> Path:
    nb = new_nb(title="任务10")
    md = lambda s: add(nb, "md", s)
    code = lambda s: add(nb, "code", s)

    md("""# 综合实验 1 文本分析 · 任务 10：商户维度可视化

- 10.1 好评率 Top10（极化样本 ≥30，Wilson 95% 下界排序，避免小样本/并列刷榜）；
- 10.2 Top10 周好评率折线（自然周聚合，周样本 <3 置空，4 周滚动）；
- 10.3 Top10 环境 / 口味 / 服务雷达图（子评分均值，已剔除 2.7 伪值）。""")

    code("""import sys
import numpy as np
import pandas as pd
from IPython.display import Image, display

SRC = "D:/DSH-Workspaces/数据科学/综合实验1/src"
sys.path.insert(0, SRC)
from config import TAB
import data_utils, viz_utils
from agg_utils import (top_by_wilson, bottom_by_ratio, weekly_counts,
                       rolling_ratio, restaurant_slice)

viz_utils.set_cn_font()
pd.set_option("display.width", 200)

agg = pd.read_csv(TAB / "rest_agg.csv")
print("商户聚合宽表:", agg.shape)""")

    code("""top = top_by_wilson(agg, min_lab=30, k=10)
bottom = bottom_by_ratio(agg, min_lab=30, k=10)
name_map = dict(zip(top["restId"], top["name"]))

def disp(r, nm):
    return f"{r} {nm}" if isinstance(nm, str) and nm else f"{r}（无名称）"

top["display"] = [disp(r, nm) for r, nm in zip(top["restId"], top["name"])]
bottom["display"] = [disp(r, nm) for r, nm in zip(bottom["restId"], bottom["name"])]
print("=== 好评率最高 Top10（Wilson 下界排序）===")
display(top[["display", "n", "good", "bad", "lab", "ratio", "wilson",
             "env_mean", "flavor_mean", "service_mean"]].round(4))
print("=== 好评率最低 Top10（对照）===")
display(bottom[["display", "n", "good", "bad", "lab", "ratio", "wilson"]].round(4))""")

    code("""fig = viz_utils.plot_top_bottom_ratio(top, bottom, "fig10_1_top10_ratio.png",
                                     "不同商户好评率 Top10 / Bottom10（极化样本≥30）")
display(Image(filename=str(fig)))

top[["restId", "name", "n", "good", "bad", "lab", "ratio", "wilson"]].to_csv(
    TAB / "top10_ratio.csv", index=False, encoding="utf-8-sig")
bottom[["restId", "name", "n", "good", "bad", "lab", "ratio", "wilson"]].to_csv(
    TAB / "bottom10_ratio.csv", index=False, encoding="utf-8-sig")""")

    code("""# 10.2 周趋势：10.1 的 Top10 好评率均为 100%（周好评率恒为 1，曲线重合），无法体现变化；
# 因此改用「评论量 Top10」展示时间趋势（该口径已在报告中说明）。
top_n = agg.sort_values("n", ascending=False).head(10).copy()
top_n["display"] = [disp(r, nm) for r, nm in zip(top_n["restId"], top_n["name"])]
name_map_n = dict(zip(top_n["restId"], top_n["name"]))
display(top_n[["display", "n", "good", "bad", "lab", "ratio"]])

ids = top_n["restId"].tolist()
sub = restaurant_slice(ids, usecols=("restId", "rating", "timestamp"))
print("评论量 Top10 评论行数:", len(sub))
sub["label"] = data_utils.encode_label(sub["rating"], "A")
sub = sub[sub["label"].isin([0, 1])].copy()
sub["week"] = pd.to_datetime(sub["timestamp"], unit="ms").dt.to_period("W")
print("极化样本:", len(sub))

wk = weekly_counts(sub, ids)
wk_roll = rolling_ratio(wk, window=4, min_labels=3, roll_min=6)
print("周记录数:", len(wk), "| 有效滚动点:", int(wk_roll["ratio_roll"].notna().sum()))""")

    code("""fig = viz_utils.plot_weekly_lines(wk_roll, name_map_n, "fig10_2_weekly_ratio_top10.png",
                                 "评论量 Top10 商户周滚动好评率（4 周滚动，周样本<3 置空）")
display(Image(filename=str(fig)))""")

    code("""# 10.3 雷达图
radar = top.set_index("restId")[["env_mean", "flavor_mean", "service_mean"]].copy()
labels = [disp(r, name_map.get(r)) for r in radar.index]
print(radar.round(3))""")

    code("""fig = viz_utils.plot_radar_grid(radar, "fig10_3_radar_grid.png",
                                "Top10 商户环境 / 口味 / 服务评分（0–5）", labels=labels, ncols=5)
display(Image(filename=str(fig)))

fig2 = viz_utils.plot_radar_multi(radar, "fig10_3_radar_overlay.png",
                                  "Top10 三项评分叠加图", labels=labels)
display(Image(filename=str(fig2)))""")

    md("""## 小结

- 好评率 Top10 由 Wilson 下界排序选出，样本量均在 130 条以上，避免「1 条好评 = 100%」的失真；
- 周趋势图显示 Top10 集中在 2011-08 ～ 2012-02（数据快照末端），周有效样本中位 4–10 条；
- 雷达图显示 Top10 三项评分整体偏高（口味 > 环境 ≈ 服务），与 88.62% 的全站好评率一致。""")

    out = NB_DIR / "04_restaurant_viz.ipynb"
    nbf.write(nb, str(out))
    return out


def build_05() -> Path:
    nb = new_nb(title="任务11")
    md = lambda s: add(nb, "md", s)
    code = lambda s: add(nb, "code", s)

    md("""# 综合实验 1 文本分析 · 任务 11：关键字查询与单店分析

演示流程：**输入关键词 → 候选商户列表 → 选择商户 → 词云 / 好评率 / 雷达图 / 周趋势**。
本 notebook 用 `keyword="湘"`、选择 `57℃湘(无限度广场店)` 作为演示；函数 `run_query()` 支持交互输入。""")

    code("""import sys
from collections import Counter
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import Image, display

SRC = "D:/DSH-Workspaces/数据科学/综合实验1/src"
sys.path.insert(0, SRC)
from config import TAB, FIG
import data_utils, text_utils, viz_utils
from agg_utils import (search_restaurants, restaurant_slice,
                       restaurant_weekly, weekly_counts, rolling_ratio)
from text_utils import tokenize

text_utils.ensure_init(str(TAB.parents[1] / "stopwords.txt"),
                       str(TAB.parents[1] / "userdict.txt"))
viz_utils.set_cn_font()
pd.set_option("display.width", 200)

agg = pd.read_csv(TAB / "rest_agg.csv")
print("商户宽表:", agg.shape)""")

    code("""keyword = "湘"
cands = search_restaurants(keyword, agg, topk=20)
print(f"关键词「{keyword}」命中 {len(cands)} 个候选（按极化样本量排序，Top20）：")
cands[["display", "n", "lab", "ratio", "命中方式"]].round(4)""")

    code("""DEMO_ID = 177416          # 57℃湘(无限度广场店)：评论多、周均有效样本约 9 条
row = agg[agg["restId"] == DEMO_ID].iloc[0]
DEMO_NAME = row["name"] if isinstance(row["name"], str) else f"restId={DEMO_ID}"
print("演示商户:", DEMO_ID, DEMO_NAME)
print("评论数 %d | 好评 %d | 差评 %d | 极化好评率 %.3f | 环境/口味/服务 %.2f/%.2f/%.2f" % (
    row["n"], row["good"], row["bad"], row["ratio"],
    row["env_mean"], row["flavor_mean"], row["service_mean"]))""")

    md("## 11.2 该商户的评论 / 好评 / 差评词云")
    code("""sub = restaurant_slice([DEMO_ID], usecols=("restId", "rating", "timestamp", "comment"))
sub["label"] = data_utils.encode_label(sub["rating"], "A")
print("该店评论行数:", len(sub), "| 好评:", int((sub["label"] == 1).sum()),
      "| 差评:", int((sub["label"] == 0).sum()))

counters = {"all": Counter(), "good": Counter(), "bad": Counter()}
for _, r in sub.iterrows():
    toks = tokenize(r["comment"])
    counters["all"].update(t for t in toks if len(t) >= 2)
    if r["label"] == 1:
        counters["good"].update(t for t in toks if len(t) >= 2)
    elif r["label"] == 0:
        counters["bad"].update(t for t in toks if len(t) >= 2)
print("all 词表:", len(counters["all"]), "| good:", len(counters["good"]), "| bad:", len(counters["bad"]))""")

    code("""fig = viz_utils.plot_wordcloud(counters["all"], f"{DEMO_NAME} · 全部评论词云",
                               "fig11_2_rest_wordcloud_all.png", max_words=100, cmap="viridis")
display(Image(filename=str(fig)))
fig = viz_utils.plot_wordcloud(counters["good"], f"{DEMO_NAME} · 好评词云",
                               "fig11_2_rest_wordcloud_good.png", max_words=100, cmap="spring")
display(Image(filename=str(fig)))
fig = viz_utils.plot_wordcloud(counters["bad"], f"{DEMO_NAME} · 差评词云",
                               "fig11_2_rest_wordcloud_bad.png", max_words=100, cmap="autumn")
display(Image(filename=str(fig)))""")

    md("## 11.3 该商户好评率（按总体评分）")
    code("""fig, ax = plt.subplots(figsize=(5.5, 4.5))
ax.bar(["该店"], [row["ratio"]], color="#2e6f95", width=0.5)
ax.axhline(0.8862, ls="--", color="#e4572e", label="全站极化好评率 88.62%")
ax.text(0, row["ratio"] + 0.02, "%.3f" % row["ratio"], ha="center", fontsize=12)
ax.set_ylim(0, 1.05); ax.set_ylabel("好评率 = good / (good + bad)")
ax.set_title(f"{DEMO_NAME} 好评率（n={int(row['lab'])}）")
ax.legend(loc="lower right")
fig.tight_layout()
out = FIG / "fig11_3_rest_ratio.png"
fig.savefig(out, dpi=200); plt.close(fig)
display(Image(filename=str(out)))""")

    md("## 11.4 该商户环境 / 口味 / 服务雷达图")
    code("""cats = ["环境评分", "口味评分", "服务评分"]
vals = [row["env_mean"], row["flavor_mean"], row["service_mean"]]
site = [agg["env_mean"].mean(), agg["flavor_mean"].mean(), agg["service_mean"].mean()]

fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={"polar": True})
angles = np.linspace(0, 2 * np.pi, len(cats), endpoint=False).tolist()
angles += angles[:1]
ax.set_xticks(angles[:-1]); ax.set_xticklabels(cats)
ax.set_ylim(0, 5)
ax.plot(angles, vals + vals[:1], lw=2.2, color="#e4572e", label=DEMO_NAME)
ax.fill(angles, vals + vals[:1], color="#e4572e", alpha=0.2)
ax.plot(angles, site + site[:1], lw=2.0, ls="--", color="#2e6f95", label="全站均值")
ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1))
ax.set_title(f"{DEMO_NAME} vs 全站均值", pad=20)
fig.tight_layout()
out = FIG / "fig11_4_rest_radar.png"
fig.savefig(out, dpi=200); plt.close(fig)
display(Image(filename=str(out)))""")

    md("## 11.5 该商户随时间的周好评率")
    code("""polar = sub[sub["label"].isin([0, 1])].copy()
polar["week"] = pd.to_datetime(polar["timestamp"], unit="ms").dt.to_period("W")
wk = weekly_counts(polar, [DEMO_ID])
wk_roll = rolling_ratio(wk, window=4, min_labels=3, roll_min=6)
print("活跃周数:", len(wk), "| 周有效样本中位数:", float(np.median(wk["n"])))
display(wk_roll[["week", "good", "n", "ratio_roll"]].tail(12))

fig = viz_utils.plot_weekly_lines(
    wk_roll, {DEMO_ID: DEMO_NAME}, "fig11_5_rest_weekly_ratio.png",
    f"{DEMO_NAME} 周滚动好评率（4 周滚动，周样本<3 置空）")
display(Image(filename=str(fig)))""")

    md("""## 交互接口

`run_query()` 支持在终端 / Jupyter 中直接输入关键词并选择商户（notebook 中执行会阻塞等待输入，故此处只定义不调用）：

```python
def run_query():
    kw = input("请输入关键词（如 湘/粤/人大/北大/西直门）：")
    cands = search_restaurants(kw, agg, topk=20)
    print(cands[["display", "n", "lab", "ratio"]].to_string())
    idx = int(input("请选择候选序号（0 开始）："))
    rid = int(cands.iloc[idx]["restId"])
    ...  # 复用 11.2-11.5 的四段代码
```
""")

    md("""## 小结

- 关键词同时检索名称与评论，命中商户按极化样本量排序，可避免选中样本过少的店；
- 演示店 `57℃湘(无限度广场店)`：207 条评论、160 条极化样本、20 个活跃周，四张图均可用；
- 交互函数与四段分析代码可复用到任意商户。""")

    out = NB_DIR / "05_query.ipynb"
    nbf.write(nb, str(out))
    return out


BUILDERS = {"02": build_02, "03": build_03, "04": build_04, "05": build_05}


def main(argv):
    targets = argv[1:] or ["all"]
    if targets == ["all"]:
        targets = list(BUILDERS)
    for t in targets:
        p = BUILDERS[t]()
        print("written:", p)


if __name__ == "__main__":
    main(sys.argv)
