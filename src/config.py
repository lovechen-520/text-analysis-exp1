"""全局路径与常量配置。

目录约定：
    综合实验1/
        src/       本模块与脚本
        notebooks/ 5 个 notebook
        output/    figures / tables / models
        cache/     分词缓存、词频
原始数据仍放在 D:\\DSH-Workspaces\\数据科学\\，不复制、不移动。
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # 综合实验1/
DATA_DIR = Path(r"D:\DSH-Workspaces\数据科学")

RATINGS = DATA_DIR / "preprocessed_ratings.csv"
RESTAURANTS = DATA_DIR / "restaurants.csv"
LINKS = DATA_DIR / "links.csv"

CACHE = ROOT / "cache"
OUTPUT = ROOT / "output"
FIG = OUTPUT / "figures"
TAB = OUTPUT / "tables"
MODEL = OUTPUT / "models"

STOPWORDS = ROOT / "stopwords.txt"
USERDICT = ROOT / "userdict.txt"

SEED = 42
FONT_PATH = r"C:\Windows\Fonts\msyh.ttc"            # 微软雅黑，matplotlib / wordcloud 共用

# 标签口径
#   A（主口径）: 4-5 -> 1, 1-2 -> 0, 3 与 3.6 剔除
#   B（对照）  : 4-5 -> 1, 1-3 -> 0, 3.6 剔除
LABEL_A = {"good": (4, 5), "bad": (1, 2), "neutral": (3,)}
LABEL_B = {"good": (4, 5), "bad": (1, 3)}

# 好评率口径
#   polar: good / (good + bad)      —— 主口径
#   valid: good / (好+差+三星)       —— 对照
RATIO_POLAR = "polar"
RATIO_VALID = "valid"


def ensure_dirs():
    for d in (CACHE, FIG, TAB, MODEL):
        d.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    ensure_dirs()
    for p in (RATINGS, RESTAURANTS, LINKS):
        print(p, "exists" if p.exists() else "MISSING")
