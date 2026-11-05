"""文本清洗、jieba 分词、停用词。

用法：
    单进程：ensure_init(STOPWORDS, USERDICT) 后调用 tokenize(text)
    多进程：Pool(initializer=init_worker, initargs=(STOPWORDS, USERDICT))
"""
from __future__ import annotations

import re

import jieba

URL_RE = re.compile(r"(https?://\S+|www\.\S+)")
KEEP_RE = re.compile(r"[^\u4e00-\u9fa5A-Za-z0-9]+")
SPACE_RE = re.compile(r"\s+")

STOPWORDS: set[str] = set()
_INITED = False


def load_stopwords(path) -> set[str]:
    words: set[str] = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            w = line.strip()
            if w and not w.startswith("#"):
                words.add(w)
    return words


def init_worker(stop_path, userdict_path) -> None:
    """进程池初始化：加载停用词与自定义词典。"""
    global STOPWORDS, _INITED
    if _INITED:
        return
    STOPWORDS = load_stopwords(stop_path)
    jieba.load_userdict(str(userdict_path))
    jieba.initialize()
    _INITED = True


def ensure_init(stop_path, userdict_path) -> None:
    init_worker(stop_path, userdict_path)


def clean_text(s) -> str:
    """去 URL、换行、标点/表情，仅保留中文/英文/数字。"""
    if not isinstance(s, str):
        s = str(s)
    s = URL_RE.sub(" ", s)
    s = s.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    s = KEEP_RE.sub(" ", s)
    return SPACE_RE.sub(" ", s).strip()


def tokenize(s) -> list[str]:
    """清洗 + 精确模式分词 + 去停用词。"""
    text = clean_text(s)
    if not text:
        return []
    return [w for w in jieba.lcut(text) if w.strip() and w not in STOPWORDS]


def tokenize_keep_single(s) -> list[str]:
    """保留单字的分词版本（分类模型可选，词云不用）。"""
    return tokenize(s)
