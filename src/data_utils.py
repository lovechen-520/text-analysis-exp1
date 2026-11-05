"""数据读取、缺失掩码恢复、标签编码、时间列。

关键背景（任务 2 的遗留问题）：
    preprocessed_ratings.csv 中缺失的 rating 被全局均值 3.6 填充，
    而真实评分只取整数 0/1/2/3/4/5，因此 rating == 3.6 可精确识别为伪值。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import RATINGS, RESTAURANTS


def encode_label(rating: pd.Series, scheme: str = "A") -> np.ndarray:
    """5 级评分 -> 二分类（浮点数组，便于容纳 NaN / -1）。

    scheme="A": 4-5 -> 1, 1-2 -> 0, 3 -> -1（中性）, 3.6 -> NaN（缺失填充）
    scheme="B": 4-5 -> 1, 1-3 -> 0, 3.6 -> NaN
    """
    r = rating.astype("float64")
    if scheme.upper() == "A":
        conds = [r.between(4, 5), r.between(1, 2), r.eq(3)]
        choices = [1, 0, -1]
    elif scheme.upper() == "B":
        conds = [r.between(4, 5), r.between(1, 3)]
        choices = [1, 0]
    else:
        raise ValueError("scheme must be 'A' or 'B'")
    return np.select(conds, choices, default=np.nan).astype("float32")


def load_ratings(usecols=None, nrows=None, drop_zero=True) -> pd.DataFrame:
    """读取主数据，补充 is_imputed_rating 与 label 两列。"""
    df = pd.read_csv(RATINGS, usecols=usecols, nrows=nrows)
    if "rating" in df.columns:
        r = df["rating"].astype("float64")
        df["is_imputed_rating"] = np.isclose(r.to_numpy(), 3.6)
        if drop_zero:
            df = df[r.to_numpy() != 0.0].copy()
        df["label"] = encode_label(df["rating"], "A")
    return df


def add_time_cols(df: pd.DataFrame, ts_col: str = "timestamp") -> pd.DataFrame:
    ts = pd.to_datetime(df[ts_col], unit="ms")
    out = df.copy()
    out["dt"] = ts
    out["week"] = ts.dt.to_period("W")
    out["month"] = ts.dt.to_period("M")
    out["year"] = ts.dt.year
    return out


def polar_mask(df: pd.DataFrame) -> pd.Series:
    """极化样本：真实评分中的 1-2 星或 4-5 星（label 为 0/1）。"""
    return df["label"].isin([0, 1])


def label_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """输出评分分布表（含伪值），供报告使用。"""
    r = df["rating"].round(1)
    total = len(df)
    out = pd.DataFrame({"count": r.value_counts().sort_index()})
    out["share"] = (out["count"] / total * 100).round(2)
    out["label"] = out.index.map(
        lambda v: "1（好评）" if v in (4.0, 5.0) else
                  ("0（差评）" if v in (1.0, 2.0) else
                   ("-1（中性）" if v == 3.0 else
                    ("删除（异常）" if v == 0.0 else "NaN（缺失填充）")))
    )
    return out.reset_index().rename(columns={"index": "rating"})
