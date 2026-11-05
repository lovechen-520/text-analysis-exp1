"""商户聚合、Wilson 下界、周聚合。

生产数据流：preprocessed_ratings.csv -> aggregate_restaurants() -> rest_agg.csv
后续 10.1/10.2/10.3/11.3-11.5 全部复用该宽表。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import RATINGS, RESTAURANTS

RATING_COLS = ["restId", "rating", "rating_env", "rating_flavor", "rating_service", "timestamp"]


def wilson_lower(good, n, z: float = 1.96) -> np.ndarray:
    """Wilson 95% 置信区间下界，用于好评率排序（样本越多越稳）。"""
    good = np.asarray(good, dtype="float64")
    n = np.asarray(n, dtype="float64")
    safe_n = np.where(n > 0, n, 1.0)
    p = np.divide(good, safe_n, out=np.zeros_like(safe_n))
    denom = 1.0 + z * z / safe_n
    centre = p + z * z / (2.0 * safe_n)
    var = p * (1.0 - p) / safe_n + z * z / (4.0 * safe_n * safe_n)
    margin = z * np.sqrt(np.clip(var, 0.0, None))
    out = (centre - margin) / denom
    out = np.where(n > 0, out, 0.0)
    return out


def aggregate_restaurants(ratings_path=RATINGS, rest_names_path=RESTAURANTS,
                          chunksize: int = 500_000) -> pd.DataFrame:
    """分块读主数据，构建商户聚合宽表（241,360 行）。"""
    names = pd.read_csv(rest_names_path)
    maxr = int(names["restId"].max())
    size = maxr + 1

    n = np.zeros(size, np.int64)
    good = np.zeros(size, np.int64)
    bad = np.zeros(size, np.int64)
    imp = np.zeros(size, np.int64)
    env_sum = np.zeros(size); env_cnt = np.zeros(size, np.int64)
    fla_sum = np.zeros(size); fla_cnt = np.zeros(size, np.int64)
    ser_sum = np.zeros(size); ser_cnt = np.zeros(size, np.int64)
    BIG = np.iinfo(np.int64).max
    ts_min = np.full(size, BIG, np.int64)
    ts_max = np.zeros(size, np.int64)

    reader = pd.read_csv(ratings_path, usecols=RATING_COLS, chunksize=chunksize)
    for chunk in reader:
        rid = chunk["restId"].to_numpy(np.int64)
        v = chunk["rating"].to_numpy(np.float64)
        np.add.at(n, rid, 1)

        g = v >= 4
        b = v <= 2
        np.add.at(good, rid[g], 1)
        np.add.at(bad, rid[b], 1)
        imp_mask = np.isclose(v, 3.6)
        np.add.at(imp, rid[imp_mask], 1)

        # 子评分：原始为整数 1-5；环境/服务存在均值填充伪值 2.7，可精确剔除
        env = chunk["rating_env"].to_numpy(np.float64)
        m = ~np.isnan(env) & ~np.isclose(env, 2.7)
        np.add.at(env_sum, rid[m], env[m]); np.add.at(env_cnt, rid[m], 1)

        fla = chunk["rating_flavor"].to_numpy(np.float64)
        m = ~np.isnan(fla)
        np.add.at(fla_sum, rid[m], fla[m]); np.add.at(fla_cnt, rid[m], 1)

        ser = chunk["rating_service"].to_numpy(np.float64)
        m = ~np.isnan(ser) & ~np.isclose(ser, 2.7)
        np.add.at(ser_sum, rid[m], ser[m]); np.add.at(ser_cnt, rid[m], 1)

        ts = chunk["timestamp"].to_numpy(np.int64)
        np.minimum.at(ts_min, rid, ts)
        np.maximum.at(ts_max, rid, ts)

    df = pd.DataFrame({
        "restId": np.arange(size),
        "n": n, "good": good, "bad": bad, "n_imputed": imp,
        "env_sum": env_sum, "env_cnt": env_cnt,
        "flavor_sum": fla_sum, "flavor_cnt": fla_cnt,
        "service_sum": ser_sum, "service_cnt": ser_cnt,
        "ts_min": ts_min, "ts_max": ts_max,
    })
    df = df[df["n"] > 0].copy()

    df["lab"] = df["good"] + df["bad"]
    df["n_neutral"] = df["n"] - df["lab"] - df["n_imputed"]
    df["ratio"] = df["good"] / df["lab"].replace(0, np.nan)                     # 极化口径
    df["ratio_valid"] = df["good"] / (df["lab"] + df["n_neutral"]).replace(0, np.nan)  # 全有效口径
    df["wilson"] = wilson_lower(df["good"], df["lab"])

    for stem in ("env", "flavor", "service"):
        df[f"{stem}_mean"] = df[f"{stem}_sum"] / df[f"{stem}_cnt"].replace(0, np.nan)

    name_map = names.set_index("restId")["name"]
    df["name"] = df["restId"].map(name_map)
    df["first_review"] = pd.to_datetime(df["ts_min"], unit="ms")
    df["last_review"] = pd.to_datetime(df["ts_max"], unit="ms")
    df["span_weeks"] = ((df["ts_max"] - df["ts_min"]) / 86_400_000 / 7).round(2)
    return df.reset_index(drop=True)


def top_by_wilson(agg: pd.DataFrame, min_lab: int = 30, k: int = 10,
                  prefer_named: bool = True) -> pd.DataFrame:
    """按 Wilson 下界取 TopK；prefer_named 时优先只保留有名称的商户（图表可读性）。"""
    cand = agg[agg["lab"] >= min_lab].copy()
    if prefer_named:
        named = cand[cand["name"].fillna("").astype(str).str.len() > 0]
        if len(named) >= k:
            cand = named
    return cand.sort_values(["wilson", "lab"], ascending=False).head(k).copy()


def bottom_by_ratio(agg: pd.DataFrame, min_lab: int = 30, k: int = 10,
                    prefer_named: bool = True) -> pd.DataFrame:
    """好评率最低 TopK（同样要求极化样本充足；优先有名称商户）。"""
    cand = agg[agg["lab"] >= min_lab].copy()
    if prefer_named:
        named = cand[cand["name"].fillna("").astype(str).str.len() > 0]
        if len(named) >= k:
            cand = named
    return cand.sort_values(["ratio", "lab"], ascending=[True, False]).head(k).copy()


def weekly_counts(polar_df: pd.DataFrame, rest_ids) -> pd.DataFrame:
    """按 (restId, week) 统计好评数与样本数（只用于极化样本）。"""
    sub = polar_df.loc[polar_df["restId"].isin(list(rest_ids)), ["restId", "week", "label"]].copy()
    sub["good"] = (sub["label"] == 1).astype("int8")
    out = (sub.groupby(["restId", "week"], observed=True)
              .agg(good=("good", "sum"), n=("label", "size"))
              .reset_index())
    return out


def rolling_ratio(weekly: pd.DataFrame, window: int = 4,
                  min_labels: int = 3, roll_min: int = 6) -> pd.DataFrame:
    """周样本 < min_labels 置空，再做 window 周滚动；滚动样本 < roll_min 不出值。"""
    out = weekly.copy()
    out["g_used"] = out["good"].where(out["n"] >= min_labels)
    out["n_used"] = out["n"].where(out["n"] >= min_labels)
    out = out.sort_values(["restId", "week"])
    out["g_roll"] = out.groupby("restId")["g_used"].transform(
        lambda s: s.rolling(window, min_periods=2).sum())
    out["n_roll"] = out.groupby("restId")["n_used"].transform(
        lambda s: s.rolling(window, min_periods=2).sum())
    out["ratio_roll"] = np.where(out["n_roll"] >= roll_min,
                                 out["g_roll"] / out["n_roll"], np.nan)
    return out


def restaurant_slice(rest_ids, ratings_path=RATINGS,
                     usecols=("restId", "rating", "timestamp", "comment"),
                     chunksize: int = 500_000) -> pd.DataFrame:
    """扫描主数据，返回指定商户的全部行（10.2 / 11.2-11.5 用）。"""
    id_set = set(int(x) for x in rest_ids)
    parts = []
    for chunk in pd.read_csv(ratings_path, usecols=list(usecols), chunksize=chunksize):
        sub = chunk[chunk["restId"].isin(id_set)]
        if len(sub):
            parts.append(sub)
    if not parts:
        return pd.DataFrame(columns=list(usecols))
    return pd.concat(parts, ignore_index=True)


def search_restaurants(keyword: str, agg: pd.DataFrame, ratings_path=RATINGS,
                       chunksize: int = 500_000, topk: int = 20) -> pd.DataFrame:
    """任务 11.1：关键词查询商户（名称命中 + 评论命中），按极化样本量降序。"""
    name_hit = set(agg.loc[agg["name"].fillna("").astype(str).str.contains(
        keyword, na=False, regex=False), "restId"].tolist())
    comment_hit: set[int] = set()
    for chunk in pd.read_csv(ratings_path, usecols=["restId", "comment"], chunksize=chunksize):
        m = chunk["comment"].astype(str).str.contains(keyword, na=False, regex=False)
        comment_hit.update(int(x) for x in chunk.loc[m, "restId"].unique())
    ids = name_hit | comment_hit
    out = agg[agg["restId"].isin(ids)].copy()
    out["命中方式"] = [
        "名称+评论" if (r in name_hit and r in comment_hit) else
        ("名称" if r in name_hit else "评论")
        for r in out["restId"]
    ]
    out = out.sort_values(["lab", "n"], ascending=False).head(topk).copy()
    displays = []
    for r, nm in zip(out["restId"], out["name"]):
        displays.append(f"{r} | {nm}" if isinstance(nm, str) and nm else f"{r} | restId={r}（无名称）")
    out["display"] = displays
    return out


def restaurant_weekly(polar_df: pd.DataFrame, rest_id: int,
                      window: int = 4, min_labels: int = 3,
                      roll_min: int = 6) -> pd.DataFrame:
    """单个商户的周好评率与滚动值（11.5 用）。"""
    weekly = weekly_counts(polar_df, [rest_id])
    return rolling_ratio(weekly, window=window, min_labels=min_labels, roll_min=roll_min)

