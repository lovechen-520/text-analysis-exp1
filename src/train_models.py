"""脚本：训练 / 评估二分类模型（口径 A 主实验、口径 B 对照实验），保存结果与模型。

用法示例：
    python train_models.py --scheme A --sample 600000      # 快速迭代版
    python train_models.py --scheme A --sample 0           # 全量极化样本（194 万）
    python train_models.py --scheme B --sample 600000      # 三星并入差评
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import CACHE, MODEL, SEED, TAB, ensure_dirs  # noqa: E402
import model_utils as mu  # noqa: E402


def build_results(scheme: str, df: pd.DataFrame, args):
    """按口径筛选/重编码 -> 抽样 -> 划分 -> 特征 -> 多模型训练评估。"""
    df = mu.apply_scheme(df, scheme)
    if args.sample:
        df = mu.stratified_sample(df, args.sample)
    X_tr, X_te, y_tr, y_te = mu.split_data(df, args.test_size)
    print(f"[{scheme}] sample={len(df):,} train={len(X_tr):,} test={len(X_te):,} "
          f"pos_rate={y_tr.mean():.4f}", flush=True)

    frames = []
    keep = {}          # (features, model) -> (vectorizer, estimator)
    matrix = {}        # features -> (Xtr, Xte)

    if args.features in ("tfidf", "both"):
        t0 = time.time()
        tfidf = mu.make_tfidf(args.max_features, args.min_df, tuple(args.ngram))
        Xtr = tfidf.fit_transform(X_tr)
        Xte = tfidf.transform(X_te)
        matrix["tfidf"] = (Xtr, Xte)
        print(f"[{scheme}] tfidf {Xtr.shape} done in {time.time() - t0:.1f}s", flush=True)
        res = mu.train_and_evaluate(Xtr, y_tr, Xte, y_te, features="tfidf")
        for _, row in res.iterrows():
            keep[("tfidf", row["model"])] = (tfidf, row["estimator"])
        frames.append(res.drop(columns=["estimator", "pred"]))
        del Xtr

    if args.features in ("count", "both"):
        t0 = time.time()
        count = mu.make_count(args.count_features, args.min_df)
        Ctr = count.fit_transform(X_tr)
        Cte = count.transform(X_te)
        matrix["count"] = (Ctr, Cte)
        print(f"[{scheme}] count {Ctr.shape} done in {time.time() - t0:.1f}s", flush=True)
        models = {
            "MultinomialNB": MultinomialNB(alpha=1.0),
            "LogisticRegression": LogisticRegression(
                C=1.0, class_weight="balanced", max_iter=1000,
                solver="liblinear", random_state=SEED),
        }
        res = mu.train_and_evaluate(Ctr, y_tr, Cte, y_te, models=models, features="count")
        for _, row in res.iterrows():
            keep[("count", row["model"])] = (count, row["estimator"])
        frames.append(res.drop(columns=["estimator", "pred"]))
        del Ctr

    table = pd.concat(frames, ignore_index=True)
    table["scheme"] = scheme

    best_row = table.sort_values(["macro_f1", "accuracy"], ascending=False).iloc[0]
    best_key = (best_row["features"], best_row["model"])
    vec, clf = keep[best_key]
    Xte_best = matrix[best_row["features"]][1]
    pred = clf.predict(Xte_best)

    info = {
        "scheme": scheme,
        "n_sample": int(len(df)),
        "n_train": int(len(X_tr)),
        "n_test": int(len(X_te)),
        "pos_rate": round(float(y_tr.mean()), 4),
        "best_features": best_row["features"],
        "best_model": best_row["model"],
        "best_accuracy": float(best_row["accuracy"]),
        "best_macro_f1": float(best_row["macro_f1"]),
        "test_size": args.test_size,
        "sample": args.sample,
        "max_features": args.max_features,
        "min_df": args.min_df,
        "ngram": list(args.ngram),
    }
    return table, info, (vec, clf, pred, y_te)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scheme", choices=["A", "B"], default="A")
    ap.add_argument("--sample", type=int, default=600_000, help="0 表示全量")
    ap.add_argument("--test-size", type=float, default=0.2)
    ap.add_argument("--features", choices=["tfidf", "count", "both"], default="both")
    ap.add_argument("--max-features", type=int, default=50_000)
    ap.add_argument("--count-features", type=int, default=30_000)
    ap.add_argument("--min-df", type=int, default=5)
    ap.add_argument("--ngram", type=int, nargs=2, default=(1, 2))
    ap.add_argument("--stamp", type=str, default="", help="产物后缀，默认按 sample 推断")
    args = ap.parse_args()

    ensure_dirs()
    t0 = time.time()
    print("loading token cache ...", flush=True)
    df_all = mu.load_tokens()
    print(f"loaded rows={len(df_all):,} in {time.time() - t0:.1f}s", flush=True)

    table, info, (vec, clf, pred, y_te) = build_results(args.scheme, df_all, args)

    stamp = args.stamp or ("full" if args.sample == 0 else f"{args.sample // 10_000}w")
    table.to_csv(TAB / f"model_compare_{args.scheme}_{stamp}.csv",
                 index=False, encoding="utf-8-sig")
    with open(TAB / f"model_split_{args.scheme}_{stamp}.json", "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)

    with open(TAB / f"model_report_{args.scheme}_{stamp}.txt", "w", encoding="utf-8") as f:
        f.write(mu.evaluation_text(y_te, pred, f"scheme={args.scheme} best={info['best_model']}"))
    cm = pd.crosstab(pd.Series(y_te, name="true"), pd.Series(pred, name="pred"))
    cm.to_csv(TAB / f"confusion_matrix_{args.scheme}_{stamp}.csv", encoding="utf-8-sig")

    mu.save_model(vec, f"vectorizer_{args.scheme}_{stamp}.joblib")
    mu.save_model(clf, f"model_{args.scheme}_{stamp}.joblib")

    print(table.to_string(index=False))
    print(json.dumps(info, ensure_ascii=False, indent=2))
    print(f"elapsed {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
