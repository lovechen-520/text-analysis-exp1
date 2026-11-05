"""可视化工具：中文字体、词云、词频柱状图、好评率柱状图、周趋势、雷达图。"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from wordcloud import WordCloud

from config import FIG, FONT_PATH

C_GOOD = "#e4572e"
C_BAD = "#17a398"
C_MAIN = "#2e6f95"
C_ALT = "#8c6bb1"
GRID = "#d9d9d9"


def set_cn_font():
    matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
    matplotlib.rcParams["axes.unicode_minus"] = False
    matplotlib.rcParams["figure.dpi"] = 120
    matplotlib.rcParams["savefig.dpi"] = 200


def _save(fig, filename):
    FIG.mkdir(parents=True, exist_ok=True)
    out = FIG / filename
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


# ------------------------------------------------------------------ 词云 / 词频
def plot_wordcloud(counter, title: str, filename: str, max_words: int = 150,
                   cmap: str = "viridis") -> Path:
    wc = WordCloud(font_path=FONT_PATH, width=1600, height=1000,
                   background_color="white", max_words=max_words,
                   collocations=False, random_state=42, colormap=cmap,
                   prefer_horizontal=0.92)
    wc.generate_from_frequencies(Counter(counter))
    fig, ax = plt.subplots(figsize=(12, 7.5))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title(title, fontsize=20, pad=14)
    fig.tight_layout()
    return _save(fig, filename)


def plot_top_words(counter, title: str, filename: str, topn: int = 20,
                   color: str = C_MAIN) -> Path:
    items = Counter(counter).most_common(topn)[::-1]
    words = [w for w, _ in items]
    vals = [v for _, v in items]
    fig, ax = plt.subplots(figsize=(8, max(6, topn * 0.32)))
    ax.barh(words, vals, color=color)
    for y, v in enumerate(vals):
        ax.text(v, y, f" {v:,}", va="center", fontsize=8)
    ax.set_title(title, fontsize=14)
    ax.set_xlabel("词频")
    ax.grid(axis="x", color=GRID, alpha=0.6)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return _save(fig, filename)


# ------------------------------------------------------------------ 标签分布
def plot_label_distribution(dist, filename: str) -> Path:
    """dist 可以是 count 为值的 Series（index=中文标签），或含 count 列的 DataFrame。"""
    counts = dist if isinstance(dist, pd.Series) else dist["count"]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    colors = {
        "1（好评）": C_GOOD, "0（差评）": C_BAD, "-1（中性）": "#f2b134",
        "NaN（缺失填充）": "#bdbdbd", "删除（异常）": "#7f7f7f",
    }
    labels = [str(x) for x in counts.index]
    cols = [colors.get(x, C_MAIN) for x in labels]
    bars = ax.bar(labels, counts.values, color=cols)
    for b, v in zip(bars, counts.values):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:,}", ha="center", va="bottom", fontsize=8)
    ax.set_title("评分标签分布（4,107,199 条）", fontsize=13)
    ax.set_ylabel("条数")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    return _save(fig, filename)


# ------------------------------------------------------------------ 好评率 Top10
def plot_top_ratio(top: pd.DataFrame, filename: str, title: str,
                   label_col: str = "display", ratio_col: str = "ratio",
                   n_col: str = "lab", baseline: float = 0.8862) -> Path:
    top = top.iloc[::-1]
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(top[label_col], top[ratio_col], color=C_MAIN)
    for bar, v, n in zip(bars, top[ratio_col], top[n_col]):
        ax.text(v + 0.006, bar.get_y() + bar.get_height() / 2,
                f"{v:.3f}  (n={int(n)})", va="center", fontsize=9)
    ax.axvline(baseline, ls="--", color=C_GOOD, lw=1.2,
               label=f"全站极化好评率 {baseline:.2%}")
    ax.set_xlim(0, 1.06)
    ax.set_xlabel("好评率 = good / (good + bad)")
    ax.set_title(title, fontsize=14)
    ax.legend(loc="lower right")
    ax.grid(axis="x", color=GRID, alpha=0.6)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return _save(fig, filename)


# ------------------------------------------------------------------ 周趋势
def plot_weekly_lines(wk_roll: pd.DataFrame, name_map: dict, filename: str,
                      title: str, line_col: str = "ratio_roll",
                      ylabel: str = "4 周滚动好评率") -> Path:
    fig, ax = plt.subplots(figsize=(12, 6.5))
    for rid, g in wk_roll.groupby("restId"):
        g = g.sort_values("week")
        x = g["week"].dt.to_timestamp()
        name = name_map.get(rid)
        if not isinstance(name, str) or not name:
            name = f"restId={rid}"
        ax.plot(x, g[line_col], lw=1.7, label=name, alpha=0.9)
    ax.set_ylim(0, 1.03)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("时间（自然周）")
    ax.set_title(title, fontsize=14)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=7.5)
    ax.grid(color=GRID, alpha=0.6)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return _save(fig, filename)


# ------------------------------------------------------------------ 雷达图
def _radar_axes(fig, rect, cats, color):
    ax = fig.add_subplot(rect, polar=True)
    angles = np.linspace(0, 2 * np.pi, len(cats), endpoint=False).tolist()
    angles += angles[:1]
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(cats, fontsize=10)
    ax.set_ylim(0, 5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(["1", "2", "3", "4", "5"], fontsize=7)
    return ax, angles


def plot_radar_multi(values: pd.DataFrame, filename: str, title: str,
                     cats=("环境评分", "口味评分", "服务评分"),
                     labels=None, colors=None, fill_alpha: float = 0.06) -> Path:
    """values: 行=商户，列=3 项评分；叠加绘制多条曲线。"""
    labels = labels if labels is not None else list(values.index)
    fig, ax = plt.subplots(figsize=(9, 8), subplot_kw={"polar": True})
    angles = np.linspace(0, 2 * np.pi, len(cats), endpoint=False).tolist()
    angles += angles[:1]
    ax.set_xticks(angles[:-1]); ax.set_xticklabels(cats, fontsize=11)
    ax.set_ylim(0, 5)
    cmap = plt.get_cmap("tab10")
    for i, (idx, row) in enumerate(values.iterrows()):
        vals = row.tolist(); vals += vals[:1]
        color = colors[i] if colors else cmap(i % 10)
        ax.plot(angles, vals, lw=1.6, color=color, label=labels[i])
        ax.fill(angles, vals, color=color, alpha=fill_alpha)
    ax.legend(bbox_to_anchor=(1.15, 1), fontsize=8)
    ax.set_title(title, fontsize=14, pad=22)
    fig.tight_layout()
    return _save(fig, filename)


def plot_radar_grid(values: pd.DataFrame, filename: str, title: str,
                    cats=("环境评分", "口味评分", "服务评分"), labels=None,
                    ncols: int = 5) -> Path:
    """values: 行=商户，列=3 项评分；每店一个极坐标子图。"""
    labels = labels if labels is not None else list(values.index)
    n = len(values)
    nrows = int(np.ceil(n / ncols))
    fig = plt.figure(figsize=(3.2 * ncols, 3.2 * nrows))
    angles = np.linspace(0, 2 * np.pi, len(cats), endpoint=False).tolist()
    angles += angles[:1]
    for i, (idx, row) in enumerate(values.iterrows()):
        ax = fig.add_subplot(nrows, ncols, i + 1, polar=True)
        vals = row.tolist(); vals += vals[:1]
        color = plt.get_cmap("tab10")(i % 10)
        ax.plot(angles, vals, lw=1.8, color=color)
        ax.fill(angles, vals, color=color, alpha=0.18)
        ax.set_xticks(angles[:-1]); ax.set_xticklabels(cats, fontsize=8)
        ax.set_ylim(0, 5); ax.set_yticks([1, 2, 3, 4, 5])
        ax.set_yticklabels([], fontsize=0)
        ax.set_title(labels[i], fontsize=8.5, pad=6)
    fig.suptitle(title, fontsize=15, y=1.02)
    fig.tight_layout()
    return _save(fig, filename)


def plot_top_bottom_ratio(top: pd.DataFrame, bottom: pd.DataFrame, filename: str,
                          title: str, baseline: float = 0.8862) -> Path:
    """10.1 双面板：左=好评率最高 Top10（柱高 Wilson 下界，标注实际好评率），右=最低 Top10（柱高好评率）。

    说明：好评率 = good/(good+bad) 在头部大量为 1.000 并列，直接按比例画柱会全部等高；
    左图改用 Wilson 95% 下界作为柱高（样本越多越高），右图比例差异明显可正常画。
    """
    fig, axes = plt.subplots(1, 2, figsize=(15, 6.5))
    ax = axes[0]
    t = top.iloc[::-1]
    bars = ax.barh(t["display"], t["wilson"], color=C_MAIN)
    for bar, ratio, n in zip(bars, t["ratio"], t["lab"]):
        ax.text(bar.get_width() + 0.002, bar.get_y() + bar.get_height() / 2,
                f"好评率 {ratio:.3f} (n={int(n)})", va="center", fontsize=8.5)
    ax.set_xlim(0.9, 1.02)
    ax.set_xlabel("Wilson 95% 下界（柱高）")
    ax.set_title("好评率最高 Top10", fontsize=12)
    ax.grid(axis="x", color=GRID, alpha=0.6)
    ax.spines[["top", "right"]].set_visible(False)

    ax = axes[1]
    b = bottom.iloc[::-1]
    bars = ax.barh(b["display"], b["ratio"], color=C_BAD)
    for bar, ratio, n in zip(bars, b["ratio"], b["lab"]):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2,
                f"{ratio:.3f} (n={int(n)})", va="center", fontsize=8.5)
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("好评率 = good / (good + bad)")
    ax.set_title("好评率最低 Top10", fontsize=12)
    ax.grid(axis="x", color=GRID, alpha=0.6)
    ax.spines[["top", "right"]].set_visible(False)

    fig.suptitle(title, fontsize=14)
    fig.tight_layout()
    return _save(fig, filename)


# ------------------------------------------------------------------ 模型对比
def plot_model_compare(table: pd.DataFrame, filename: str, title: str) -> Path:
    """table: 列 model, features, accuracy, macro_f1。"""
    tbl = table.copy()
    tbl["label"] = tbl["model"] + "\n(" + tbl["features"] + ")"
    x = np.arange(len(tbl))
    w = 0.36
    fig, ax = plt.subplots(figsize=(max(8, 2.2 * len(tbl)), 5))
    b1 = ax.bar(x - w / 2, tbl["accuracy"], w, label="accuracy", color=C_MAIN)
    b2 = ax.bar(x + w / 2, tbl["macro_f1"], w, label="macro-F1", color=C_ALT)
    for bars in (b1, b2):
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f"{b.get_height():.3f}",
                    ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(tbl["label"], fontsize=8.5)
    ax.set_ylim(0.5, 1.0); ax.set_ylabel("指标")
    ax.set_title(title, fontsize=13)
    ax.legend(loc="lower right")
    ax.grid(axis="y", color=GRID, alpha=0.6)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return _save(fig, filename)
