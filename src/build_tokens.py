"""脚本：全量分词 + 词频统计 + 带标签样本分词缓存

产物（均在 cache/ 下）：
    cnt_all.pkl / cnt_good.pkl / cnt_bad.pkl    三个词频 Counter（仅统计长度 >=2 的词）
    tokens_labeled.tsv.gz                       restId \t label \t tokens
                                                label ∈ {1 好评, 0 差评, -1 三星中性}；
                                                3.6 伪值行不写入（无标签）
    token_manifest.json                         运行信息

用法：
    python build_tokens.py --workers 16          # 全量
    python build_tokens.py --workers 4 --limit 3000   # 冒烟测试
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import pickle
import sys
import time
from collections import Counter
from multiprocessing import Pool, cpu_count

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import CACHE, RATINGS, STOPWORDS, USERDICT, ensure_dirs  # noqa: E402
from data_utils import encode_label  # noqa: E402
from text_utils import init_worker, tokenize  # noqa: E402

TOK_FILE = "tokens_labeled.tsv.gz"


def update_counters(cnt_all, cnt_good, cnt_bad, toks_list, labels):
    """一次遍历累加 all / good / bad 三个词频表（只保留长度 >= 2 的词）。"""
    flat = [t for toks in toks_list for t in toks if len(t) >= 2]
    cnt_all.update(flat)
    idx_good = np.nonzero(labels == 1)[0]
    idx_bad = np.nonzero(labels == 0)[0]
    if len(idx_good):
        cnt_good.update(t for j in idx_good for t in toks_list[j] if len(t) >= 2)
    if len(idx_bad):
        cnt_bad.update(t for j in idx_bad for t in toks_list[j] if len(t) >= 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=min(16, cpu_count()))
    ap.add_argument("--chunksize", type=int, default=50_000)
    ap.add_argument("--limit", type=int, default=0, help=">0 时只处理前 N 行（冒烟测试）")
    ap.add_argument("--out-suffix", type=str, default="", help="冒烟测试时给产物加后缀，避免覆盖")
    args = ap.parse_args()

    ensure_dirs()
    suffix = args.out_suffix
    tok_path = CACHE / f"tokens_labeled{suffix}.tsv.gz"
    t0 = time.time()
    rows = 0
    cnt_all, cnt_good, cnt_bad = Counter(), Counter(), Counter()

    pool = Pool(args.workers, initializer=init_worker,
                initargs=(str(STOPWORDS), str(USERDICT)))
    try:
        with gzip.open(tok_path, "wt", encoding="utf-8", compresslevel=6) as fout:
            reader = pd.read_csv(RATINGS, usecols=["restId", "rating", "comment"],
                                 chunksize=args.chunksize)
            for i, chunk in enumerate(reader):
                if args.limit:
                    remain = args.limit - rows
                    if remain <= 0:
                        break
                    chunk = chunk.head(remain)
                comments = chunk["comment"].tolist()
                labels = encode_label(chunk["rating"], "A")
                toks_list = pool.map(tokenize, comments)

                update_counters(cnt_all, cnt_good, cnt_bad, toks_list, labels)

                rid = chunk["restId"].to_numpy(np.int64)
                for j in np.nonzero(np.isfinite(labels))[0]:
                    fout.write(f"{rid[j]}\t{int(labels[j])}\t{' '.join(toks_list[j])}\n")

                rows += len(chunk)
                print(f"chunk {i:02d}: rows={rows:,} elapsed={time.time() - t0:.0f}s",
                      flush=True)
    finally:
        pool.close()
        pool.join()

    with open(CACHE / f"cnt_all{suffix}.pkl", "wb") as f:
        pickle.dump(cnt_all, f, protocol=4)
    with open(CACHE / f"cnt_good{suffix}.pkl", "wb") as f:
        pickle.dump(cnt_good, f, protocol=4)
    with open(CACHE / f"cnt_bad{suffix}.pkl", "wb") as f:
        pickle.dump(cnt_bad, f, protocol=4)

    manifest = {
        "rows": rows,
        "workers": args.workers,
        "limit": args.limit,
        "elapsed_sec": round(time.time() - t0, 1),
        "vocab_all": len(cnt_all),
        "vocab_good": len(cnt_good),
        "vocab_bad": len(cnt_bad),
        "top20_all": cnt_all.most_common(20),
    }
    with open(CACHE / f"token_manifest{suffix}.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print("=== DONE ===")
    print(json.dumps({k: v for k, v in manifest.items() if k != "top20_all"},
                     ensure_ascii=False, indent=2))
    print("top20:", cnt_all.most_common(20))


if __name__ == "__main__":
    main()
