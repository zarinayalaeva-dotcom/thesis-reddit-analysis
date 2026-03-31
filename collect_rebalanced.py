"""
Reddit Data Collection — REBALANCED QUERIES
=============================================
More food, beauty, martial arts, media, philosophy.
Less hanfu/qipao dominance.

pip install requests pandas openpyxl
python collect_rebalanced.py
"""

import requests
import pandas as pd
import re
import time
from datetime import datetime

PULLPUSH_URL = "https://api.pullpush.io/reddit/search/submission/"

def search_pullpush(query, limit=50, after=None, before=None):
    params = {"q": query, "size": limit, "sort": "desc", "sort_type": "score"}
    if after: params["after"] = after
    if before: params["before"] = before
    try:
        response = requests.get(PULLPUSH_URL, params=params, timeout=30)
        if response.status_code == 200:
            return response.json().get("data", [])
        else:
            print(f"    Warning: {response.status_code} for '{query}'")
            return []
    except Exception as e:
        print(f"    Error: {e}")
        return []

def collect_posts(search_queries, target_total=350):
    all_posts = []
    seen_ids = set()

    time_periods = [
        (None, None),
        (1577836800, 1609459200),   # 2020
        (1609459200, 1640995200),   # 2021
        (1640995200, 1672531200),   # 2022
        (1672531200, 1704067200),   # 2023
        (1704067200, 1735689600),   # 2024
    ]

    print(f"\nTarget: {target_total} posts")
    print(f"Queries: {len(search_queries)}")
    print("=" * 60)

    for i, query in enumerate(search_queries):
        if len(all_posts) >= target_total:
            break
        for after_ts, before_ts in time_periods:
            if len(all_posts) >= target_total:
                break
            posts = search_pullpush(query, limit=20, after=after_ts, before=before_ts)
            new_count = 0
            for post in posts:
                post_id = post.get("id", "")
                if not post_id or post_id in seen_ids:
                    continue
                if len(all_posts) >= target_total:
                    break
                title = post.get("title", "") or ""
                selftext = post.get("selftext", "") or ""
                if len(title.strip()) < 5:
                    continue
                if selftext in ["[removed]", "[deleted]"]:
                    selftext = ""
                content = f"{title} {selftext}".strip()
                if len(content) < 20:
                    continue
                seen_ids.add(post_id)
                created = post.get("created_utc", 0)
                if isinstance(created, (int, float)) and created > 0:
                    date_str = datetime.utcfromtimestamp(created).strftime("%Y-%m-%d %H:%M:%S")
                    year = datetime.utcfromtimestamp(created).year
                else:
                    date_str = str(created)
                    year = 0
                subreddit = post.get("subreddit", "unknown")
                permalink = post.get("permalink", f"/r/{subreddit}/comments/{post_id}/")
                all_posts.append({
                    "post_id": post_id,
                    "subreddit": subreddit,
                    "title": title,
                    "selftext": selftext[:2000],
                    "content_combined": content[:2500],
                    "score": post.get("score", 0),
                    "num_comments": post.get("num_comments", 0),
                    "created_utc": date_str,
                    "year": year,
                    "url": f"https://reddit.com{permalink}",
                    "search_query": query,
                    "author": post.get("author", "[deleted]"),
                    "content_length": len(content),
                })
                new_count += 1
            time.sleep(1.0)
        print(f"  [{i+1}/{len(search_queries)}] '{query}'  |  Total: {len(all_posts)}/{target_total}")

    print("=" * 60)
    print(f"Done: {len(all_posts)} posts")
    return all_posts


def analyze_posts(df):
    results = []
    chinese_elements = {
        "hanfu": ["hanfu", "han fu"],
        "qipao": ["qipao", "cheongsam", "qi pao"],
        "tanghulu": ["tanghulu", "tang hulu", "candied fruit skewer", "candied haw"],
        "tea_ceremony": ["tea ceremony", "gongfu tea", "chinese tea", "gaiwan"],
        "calligraphy": ["calligraphy", "chinese characters", "hanzi"],
        "kung_fu": ["kung fu", "wushu", "martial art"],
        "confucianism": ["confucius", "confucianism", "confucian"],
        "dragon": ["chinese dragon", "long dragon", "dragon dance", "dragon boat"],
        "mooncake": ["mooncake", "moon cake", "mid-autumn"],
        "pagoda": ["pagoda", "chinese temple", "chinese architecture"],
        "chinese_makeup": ["flower knows", "douyin makeup", "chinese makeup", "chinese beauty", "chinese skincare", "chinese cosmetic"],
        "donghua": ["donghua", "chinese anime", "chinese animation"],
        "dynasty": ["ming dynasty", "qing dynasty", "tang dynasty", "han dynasty", "song dynasty"],
        "instruments": ["guzheng", "erhu", "pipa", "chinese instrument"],
        "mahjong": ["mahjong", "mah jong"],
        "lantern": ["chinese lantern", "red lantern"],
        "zodiac": ["chinese zodiac", "lunar new year", "chinese new year"],
        "tai_chi": ["tai chi", "taichi", "t'ai chi"],
        "boba": ["boba", "bubble tea"],
        "dimsum": ["dim sum", "dimsum", "dumpling", "xiaolongbao", "baozi", "jiaozi"],
        "tcm": ["traditional chinese medicine", "acupuncture", "chinese medicine"],
        "porcelain": ["chinese porcelain", "chinoiserie", "blue and white pottery"],
        "silk": ["chinese silk", "silk road"],
    }
    element_categories = {
        "clothing": ["hanfu", "qipao"],
        "food": ["tanghulu", "mooncake", "boba", "dimsum"],
        "philosophy": ["confucianism"],
        "martial_arts": ["kung_fu", "tai_chi"],
        "arts": ["calligraphy", "instruments", "porcelain"],
        "aesthetics": ["dragon", "pagoda", "lantern", "zodiac", "silk"],
        "media": ["donghua"],
        "beauty": ["chinese_makeup"],
        "history": ["dynasty", "mahjong"],
        "practices": ["tea_ceremony", "tcm"],
    }
    japanese_keywords = [
        "japanese", "japan", "kimono", "anime", "manga", "samurai",
        "geisha", "sakura", "tokyo", "nihon", "nippon", "katana",
        "sushi", "wasabi", "shinto", "zen", "origami", "ramen",
        "kawaii", "otaku", "futon", "karate", "judo", "ninja"
    ]
    korean_keywords = [
        "korean", "korea", "hanbok", "kpop", "k-pop", "k-drama",
        "kdrama", "hallyu", "seoul", "hangul", "bibimbap",
        "kimchi", "soju", "oppa", "aegyo", "manhwa", "webtoon"
    ]
    chinese_keywords = [
        "chinese", "china", "mandarin", "beijing", "shanghai",
        "cantonese", "taiwanese", "hong kong", "prc", "mainland",
        "wuhan", "guangzhou", "sichuan", "yunnan"
    ]

    for _, row in df.iterrows():
        text = str(row["content_combined"]).lower()
        found_elements = []
        for element, keywords in chinese_elements.items():
            if any(kw in text for kw in keywords):
                found_elements.append(element)
        found_categories = set()
        for el in found_elements:
            for cat, members in element_categories.items():
                if el in members:
                    found_categories.add(cat)
        jp_count = sum(1 for kw in japanese_keywords if re.search(r'\b' + re.escape(kw) + r'\b', text))
        kr_count = sum(1 for kw in korean_keywords if re.search(r'\b' + re.escape(kw) + r'\b', text))
        cn_count = sum(1 for kw in chinese_keywords if re.search(r'\b' + re.escape(kw) + r'\b', text))
        cultures = {"chinese": cn_count, "japanese": jp_count, "korean": kr_count}
        max_culture = max(cultures, key=cultures.get)
        dominant = max_culture if cultures[max_culture] > 0 else "neutral"
        misattribution = "none"
        misattribution_confidence = "none"
        if found_elements:
            if dominant == "japanese" and cn_count == 0:
                misattribution = "chinese_as_japanese"
                misattribution_confidence = "high"
            elif dominant == "korean" and cn_count == 0:
                misattribution = "chinese_as_korean"
                misattribution_confidence = "high"
            elif dominant == "japanese" and jp_count > cn_count * 2:
                misattribution = "chinese_as_japanese"
                misattribution_confidence = "medium"
            elif dominant == "korean" and kr_count > cn_count * 2:
                misattribution = "chinese_as_korean"
                misattribution_confidence = "medium"
            elif (jp_count > 0 or kr_count > 0) and cn_count == 0:
                misattribution = "chinese_as_east_asian_generic"
                misattribution_confidence = "low"
        discusses_misattribution = bool(re.search(
            r'mistaken|confused|mix.?up|misattribut|mislabel|wrong|not (japanese|korean)|actually chinese|'
            r'people think|assume.*(japanese|korean)|credit.*(japan|korea)|stolen|appropriat|origin',
            text
        ))
        results.append({
            "post_id": row["post_id"], "subreddit": row["subreddit"], "title": row["title"],
            "content_preview": str(row["content_combined"])[:300] + "...",
            "score": row["score"], "num_comments": row["num_comments"],
            "created_utc": row["created_utc"], "year": row.get("year", 0),
            "url": row["url"], "search_query": row["search_query"],
            "content_length": row.get("content_length", len(str(row["content_combined"]))),
            "found_elements": ", ".join(found_elements) if found_elements else "none",
            "element_count": len(found_elements),
            "element_categories": ", ".join(sorted(found_categories)) if found_categories else "none",
            "chinese_indicators": cn_count, "japanese_indicators": jp_count, "korean_indicators": kr_count,
            "dominant_framing": dominant,
            "misattribution_type": misattribution, "misattribution_confidence": misattribution_confidence,
            "discusses_misattribution": discusses_misattribution,
        })
    return pd.DataFrame(results)


def generate_statistics(results_df):
    total = len(results_df)
    has_elements = results_df[results_df["element_count"] > 0]
    misattr_all = results_df[results_df["misattribution_type"] != "none"]
    misattr_high = results_df[results_df["misattribution_confidence"] == "high"]
    misattr_med = results_df[results_df["misattribution_confidence"] == "medium"]
    stats = {}
    stats["Total posts analyzed"] = total
    stats["Posts with Chinese cultural elements"] = len(has_elements)
    stats["Posts with any misattribution detected"] = len(misattr_all)
    stats["High confidence misattribution"] = len(misattr_high)
    stats["Medium confidence misattribution"] = len(misattr_med)
    stats["Misattribution rate (of element posts)"] = (
        f"{len(misattr_all) / len(has_elements) * 100:.1f}%" if len(has_elements) > 0 else "N/A")
    stats["Posts discussing misattribution explicitly"] = int(results_df["discusses_misattribution"].sum())
    stats["Misattributed as Japanese"] = len(results_df[results_df["misattribution_type"] == "chinese_as_japanese"])
    stats["Misattributed as Korean"] = len(results_df[results_df["misattribution_type"] == "chinese_as_korean"])
    stats["Misattributed as generic East Asian"] = len(results_df[results_df["misattribution_type"] == "chinese_as_east_asian_generic"])
    if len(misattr_all) > 0:
        all_el = []
        for s in misattr_all["found_elements"]:
            if s != "none": all_el.extend(s.split(", "))
        if all_el:
            for el, c in pd.Series(all_el).value_counts().head(10).items():
                stats[f"Element in misattribution: {el}"] = c
    if len(misattr_all) > 0:
        all_cats = []
        for s in misattr_all["element_categories"]:
            if s != "none": all_cats.extend(s.split(", "))
        if all_cats:
            for cat, c in pd.Series(all_cats).value_counts().items():
                stats[f"Category in misattribution: {cat}"] = c
    framing = results_df["dominant_framing"].value_counts()
    for f, c in framing.items():
        stats[f"Dominant framing: {f}"] = c
    if len(misattr_all) > 0:
        for sub, c in misattr_all["subreddit"].value_counts().head(10).items():
            stats[f"Subreddit r/{sub}"] = f"{c} cases"
    if "year" in results_df.columns:
        for yr, c in results_df[results_df["year"] > 0]["year"].value_counts().sort_index().items():
            stats[f"Posts from {int(yr)}"] = c
    return stats


def save_results(raw_df, results_df, stats):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"misattribution_rebalanced_{timestamp}.xlsx"
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        results_df.to_excel(writer, sheet_name="Full_Results", index=False)
        misattr_df = results_df[results_df["misattribution_type"] != "none"]
        if not misattr_df.empty:
            misattr_df.to_excel(writer, sheet_name="Misattribution_Cases", index=False)
        discusses_df = results_df[results_df["discusses_misattribution"] == True]
        if not discusses_df.empty:
            discusses_df.to_excel(writer, sheet_name="Discusses_Misattribution", index=False)
        raw_df.to_excel(writer, sheet_name="Raw_Data", index=False)
        pd.DataFrame([{"Metric": k, "Value": str(v)} for k, v in stats.items()]).to_excel(writer, sheet_name="Statistics", index=False)
        element_rows = []
        for _, row in results_df.iterrows():
            if row["found_elements"] != "none":
                for el in row["found_elements"].split(", "):
                    element_rows.append({
                        "element": el, "subreddit": row["subreddit"], "year": row.get("year", 0),
                        "dominant_framing": row["dominant_framing"],
                        "misattribution_type": row["misattribution_type"],
                        "misattribution_confidence": row["misattribution_confidence"],
                        "post_id": row["post_id"],
                    })
        if element_rows:
            pd.DataFrame(element_rows).to_excel(writer, sheet_name="Element_Breakdown", index=False)
        sub_summary = results_df.groupby("subreddit").agg(
            total_posts=("post_id", "count"), avg_score=("score", "mean"),
            posts_with_elements=("element_count", lambda x: (x > 0).sum()),
            misattribution_count=("misattribution_type", lambda x: (x != "none").sum()),
        ).sort_values("total_posts", ascending=False)
        sub_summary.to_excel(writer, sheet_name="Subreddit_Summary")
        if "year" in results_df.columns:
            yearly = results_df[results_df["year"] > 0].groupby("year").agg(
                total_posts=("post_id", "count"),
                misattribution_count=("misattribution_type", lambda x: (x != "none").sum()),
                avg_score=("score", "mean"),
            )
            yearly.to_excel(writer, sheet_name="Temporal_Distribution")
        if element_rows:
            el_df = pd.DataFrame(element_rows)
            el_misattr = el_df[el_df["misattribution_type"] != "none"]
            if not el_misattr.empty:
                pd.crosstab(el_misattr["element"], el_misattr["misattribution_type"]).to_excel(writer, sheet_name="Element_x_Direction")
    print(f"\nSaved to: {filename}")
    return filename


# ============================================================
# REBALANCED QUERIES - spread across all cultural categories
# ============================================================

search_queries = [
    # FOOD (heavy)
    "tanghulu Korean",
    "tanghulu not Korean",
    "tanghulu origin",
    "Chinese food mistaken Korean",
    "Chinese food mistaken Japanese",
    "dim sum Japanese",
    "dumplings Korean Japanese",
    "boba tea origin Taiwan",
    "mooncake Japanese Korean",
    "hotpot Korean",
    "xiaolongbao Japanese",
    "Chinese street food",
    "mapo tofu Korean",

    # BEAUTY / COSMETICS
    "Flower Knows Korean",
    "Flower Knows Japanese",
    "Chinese makeup Korean",
    "Chinese skincare Korean",
    "douyin makeup Korean",
    "Chinese beauty brand mistaken",
    "Chinese cosmetics Japanese",

    # MEDIA / ENTERTAINMENT
    "donghua anime",
    "Chinese anime Japanese",
    "genshin impact Chinese Japanese",
    "Chinese drama mistaken Korean drama",
    "Chinese game Japanese",
    "mihoyo Chinese",
    "wuxia anime",

    # MARTIAL ARTS
    "kung fu karate difference",
    "kung fu Japanese",
    "tai chi Japanese",
    "wushu karate",
    "Chinese martial arts Japanese",
    "martial arts origin China",

    # PHILOSOPHY / TRADITIONS
    "Confucius Korean",
    "Confucianism Korea Japan origin",
    "feng shui Japanese",
    "Chinese zodiac Japanese",
    "Chinese New Year Korean",
    "lunar new year Chinese Korean",
    "yin yang Japanese Chinese",

    # ARTS / AESTHETICS
    "Chinese calligraphy Japanese",
    "Chinese porcelain Japanese",
    "chinoiserie",
    "Chinese dragon Japanese dragon",
    "pagoda Chinese Japanese",
    "Chinese architecture Japanese temple",
    "Chinese painting Japanese",

    # TEA / PRACTICES
    "Chinese tea ceremony Japanese",
    "tea ceremony origin China",
    "acupuncture Japanese Chinese",
    "traditional Chinese medicine Korean",

    # GENERAL MISATTRIBUTION
    "Chinese culture mistaken Japanese",
    "Chinese culture mistaken Korean",
    "people confuse Chinese Japanese Korean",
    "Chinese cultural erasure",
    "Asian culture all the same",
    "Chinese vs Japanese vs Korean",
    "Chinese culture stolen Korean",
    "Chinese origin Korean claim",

    # CLOTHING (reduced - only 4 queries instead of 7)
    "hanfu kimono difference",
    "qipao Japanese",
    "hanfu mistaken",
    "cheongsam origin",
]

target_total = 350  # slightly more to account for filtering

print("=" * 60)
print("  REBALANCED CULTURAL MISATTRIBUTION ANALYSIS")
print("  More food, beauty, martial arts, philosophy, media")
print("=" * 60)

posts = collect_posts(search_queries=search_queries, target_total=target_total)

if not posts:
    print("\nERROR: No posts collected.")
else:
    raw_df = pd.DataFrame(posts)
    print(f"\nCollected {len(raw_df)} posts from {raw_df['subreddit'].nunique()} subreddits")
    results_df = analyze_posts(raw_df)
    stats = generate_statistics(results_df)
    output_file = save_results(raw_df, results_df, stats)
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print("=" * 60)
    print(f"\n  Done! Results in: {output_file}")
    print(f"  Send this file back to Claude!")
