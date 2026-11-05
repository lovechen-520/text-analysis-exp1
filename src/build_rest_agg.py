"""脚本：构建商户聚合宽表 -> output/tables/rest_agg.csv"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agg_utils import aggregate_restaurants
from config import TAB, ensure_dirs


def main():
    ensure_dirs()
    t0 = time.time()
    print("building restaurant aggregate table ...", flush=True)
    agg = aggregate_restaurants()
    out = TAB / "rest_agg.csv"
    agg.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"saved: {out}")
    print(f"shape: {agg.shape}  elapsed: {time.time() - t0:.1f}s")
    print(agg[["n", "good", "bad", "lab", "ratio"]].describe().round(3).to_string())
    print("restaurants with lab>=30:", int((agg["lab"] >= 30).sum()))
    print("restaurants with lab>=50:", int((agg["lab"] >= 50).sum()))


if __name__ == "__main__":
    main()
