"""特征工程、模型训练/评估、模型保存、推理函数。"""
from __future__ import annotations

import csv
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, f1_score, precision_score,
                             recall_score)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC

from config import CACHE, MODEL, SEED, TAB
from text_utils import tokenize


# ---------------------------------------------------------------- 数据读取
def load_tokens(path=None, nrows=None) -> pd.DataFrame:
    """读取带标签的分词缓存：restId, label(1/0/-1), tokens。"""
    path = path or (CACHE / "tokens_labeled.tsv.gz")
    df = pd.read_csv(path, sep="\t", names=["restId", "label", "tokens"],
                     dtype={"restId": "int64", "label": "int8", "tokens": "string"},
                     quoting=csv.QUOTE_NONE, engine="c", nrows=nrows,
                     keep_default_na=False, na_values=[])
    df["tokens"] = df["tokens"].fillna("")
    return df


def apply_scheme(df: pd.DataFrame, scheme: str = "A") -> pd.DataFrame:
    """按口径生成二分类样本。

    A：只用 4-5 / 1-2（label 0/1），三星 -1 剔除
    B：4-5 -> 1，1-3 -> 0（三星并入差评）
    """
    scheme = scheme.upper()
    if scheme == "A":
        out = df[df["label"].isin([0, 1])].copy()
    elif scheme == "B":
        out = df.copy()
        out["label"] = (out["label"] == 1).astype("int8")
    else:
        raise ValueError("scheme must be 'A' or 'B'")
    return out.reset_index(drop=True)


def stratified_sample(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """按类别比例分层抽样 n 条（n<=0 或 n>=len 时原样返回）。"""
    if n <= 0 or n >= len(df):
        return df
    parts = []
    for lab, g in df.groupby("label", observed=True):
        k = max(1, int(round(n * len(g) / len(df))))
        parts.append(g.sample(n=min(k, len(g)), random_state=SEED))
    return pd.concat(parts, ignore_index=True)


def split_data(df: pd.DataFrame, test_size: float = 0.2):
    """分层划分训练/测试集。"""
    X = df["tokens"].astype(str)
    y = df["label"].astype("int8")
    return train_test_split(X, y, test_size=test_size, stratify=y, random_state=SEED)


# ---------------------------------------------------------------- 特征
def make_tfidf(max_features: int = 50_000, min_df: int = 5,
               ngram_range=(1, 2)) -> TfidfVectorizer:
    return TfidfVectorizer(tokenizer=str.split, lowercase=False, token_pattern=None,
                           max_features=max_features, min_df=min_df,
                           ngram_range=ngram_range, sublinear_tf=True)


def make_count(max_features: int = 30_000, min_df: int = 5) -> CountVectorizer:
    return CountVectorizer(tokenizer=str.split, lowercase=False, token_pattern=None,
                           max_features=max_features, min_df=min_df)


# ---------------------------------------------------------------- 模型
def default_models() -> dict:
    return {
        "MultinomialNB": MultinomialNB(alpha=1.0),
        "LogisticRegression": LogisticRegression(
            C=1.0, class_weight="balanced", max_iter=1000,
            solver="liblinear", random_state=SEED),
        "LinearSVC": LinearSVC(C=0.5, class_weight="balanced", random_state=SEED),
    }


def train_and_evaluate(X_tr, y_tr, X_te, y_te, models: dict | None = None,
                       features: str = "tfidf") -> pd.DataFrame:
    """训练多个模型并返回对比表（含训练好的 estimator 对象列）。"""
    models = models or default_models()
    rows = []
    for name, clf in models.items():
        t0 = time.time()
        clf.fit(X_tr, y_tr)
        fit_sec = time.time() - t0
        pred = clf.predict(X_te)
        rows.append({
            "features": features,
            "model": name,
            "accuracy": round(float(accuracy_score(y_te, pred)), 4),
            "macro_f1": round(float(f1_score(y_te, pred, average="macro")), 4),
            "f1_bad": round(float(f1_score(y_te, pred, pos_label=0)), 4),
            "precision_bad": round(float(precision_score(y_te, pred, pos_label=0)), 4),
            "recall_bad": round(float(recall_score(y_te, pred, pos_label=0)), 4),
            "train_sec": round(fit_sec, 2),
            "n_train": int(X_tr.shape[0]),
            "n_test": int(X_te.shape[0]),
            "estimator": clf,
            "pred": pred,
        })
    return pd.DataFrame(rows)


def evaluation_text(y_te, pred, title: str = "") -> str:
    cm = confusion_matrix(y_te, pred)
    rep = classification_report(y_te, pred, digits=4, target_names=["差评(0)", "好评(1)"])
    lines = [f"=== {title} ===", "confusion_matrix (rows=true, cols=pred):",
             str(cm), "", rep]
    return "\n".join(lines)


def save_model(obj, name: str, folder=None):
    folder = folder or MODEL
    path = folder / name
    joblib.dump(obj, path)
    return path


def load_model(path):
    return joblib.load(path)


# ---------------------------------------------------------------- 推理
def predict_sentiment(text: str, vectorizer, clf) -> str:
    """用户输入一条评论 -> 好评/差评（需先调用 text_utils.ensure_init）。"""
    toks = " ".join(tokenize(text))
    pred = clf.predict(vectorizer.transform([toks]))[0]
    return "好评" if int(pred) == 1 else "差评"


def predict_proba(text: str, vectorizer, clf):
    toks = " ".join(tokenize(text))
    if hasattr(clf, "predict_proba"):
        p = clf.predict_proba(vectorizer.transform([toks]))[0]
        return {"差评(0)": round(float(p[0]), 4), "好评(1)": round(float(p[1]), 4)}
    return None
