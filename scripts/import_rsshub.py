#!/usr/bin/env python3
"""
RSSHub Feed Importer for Money Radar
Fetches RSSHub routes and adds them to feeds.fun.

Usage:
    python3 import_rsshub.py --rsshub http://localhost:1200
    python3 import_rsshub.py --rsshub http://localhost:1200 --categories finance,tech
    python3 import_rsshub.py --rsshub http://localhost:1200 --dry-run
"""

import argparse
import json
import sys
from urllib.request import urlopen, Request
from urllib.error import URLError


# Predefined feed collections by category
FEED_COLLECTIONS = {
    "finance": {
        "name": "财经金融",
        "feeds": [
            {"name": "华尔街见闻", "path": "/wallstreetcn/news/global"},
            {"name": "财联社", "path": "/cls/telegraph"},
            {"name": "第一财经", "path": "/yicai/brief"},
            {"name": "金十数据", "path": "/jin10"},
            {"name": "雪球热帖", "path": "/xueqiu/hot"},
            {"name": "雪球组合", "path": "/xueqiu/merger"},
            {"name": "格隆汇", "path": "/gelonghui/live"},
        ],
    },
    "tech": {
        "name": "科技",
        "feeds": [
            {"name": "36氪", "path": "/36kr/newsflashes"},
            {"name": "虎嗅", "path": "/huxiu/article"},
            {"name": "少数派", "path": "/sspai/matrix"},
            {"name": "Hacker News", "path": "/hackernews/best"},
            {"name": "TechCrunch", "path": "/techcrunch/news"},
            {"name": "The Verge", "path": "/theverge"},
        ],
    },
    "policy": {
        "name": "政策时政",
        "feeds": [
            {"name": "新华社", "path": "/xinhuanet/news"},
            {"name": "中国政府网", "path": "/gov/zhengce"},
            {"name": "人民日报", "path": "/rmrb"},
        ],
    },
    "market": {
        "name": "市场行情",
        "feeds": [
            {"name": "A股公告", "path": "/eastmoney/report/strategy"},
            {"name": "港股资讯", "path": "/zhihu/pins/hot"},
        ],
    },
    "crypto": {
        "name": "加密货币",
        "feeds": [
            {"name": "CoinDesk", "path": "/coindesk"},
            {"name": "PANews", "path": "/panewslab"},
        ],
    },
    "general": {
        "name": "综合资讯",
        "feeds": [
            {"name": "知乎热榜", "path": "/zhihu/hotlist"},
            {"name": "微博热搜", "path": "/weibo/search/hot"},
            {"name": "V2EX 热门", "path": "/v2ex/topics/hot"},
            {"name": "掘金", "path": "/juejin/trending/all"},
        ],
    },
}


def fetch_json(url: str) -> dict:
    """Fetch JSON from URL."""
    try:
        req = Request(url, headers={"User-Agent": "MoneyRadar/1.0"})
        with urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except (URLError, json.JSONDecodeError) as e:
        print(f"  WARNING: Failed to fetch {url}: {e}")
        return {}


def check_rsshub_health(rsshub_url: str) -> bool:
    """Check if RSSHub is accessible."""
    print(f"Checking RSSHub at {rsshub_url}...")
    data = fetch_json(f"{rsshub_url}/api/routes")
    if data and "data" in data:
        routes = data["data"]
        print(f"  RSSHub is healthy. {len(routes)} route categories available.")
        return True
    print("  ERROR: RSSHub is not accessible.")
    return False


def generate_feed_urls(rsshub_url: str, categories: list[str]) -> list[dict]:
    """Generate feed URLs for selected categories."""
    feeds = []
    for cat in categories:
        if cat not in FEED_COLLECTIONS:
            print(f"  WARNING: Unknown category '{cat}', skipping.")
            continue
        collection = FEED_COLLECTIONS[cat]
        print(f"  [{cat}] {collection['name']}: {len(collection['feeds'])} feeds")
        for feed in collection["feeds"]:
            url = f"{rsshub_url}{feed['path']}"
            feeds.append({
                "name": feed["name"],
                "url": url,
                "category": cat,
            })
    return feeds


def add_feed_to_feedsfun(feedsfun_url: str, feed_url: str, feed_name: str) -> bool:
    """Add a feed to feeds.fun via API."""
    # feeds.fun uses /api/v1/feeds/add endpoint
    data = json.dumps({"url": feed_url}).encode("utf-8")
    req = Request(
        f"{feedsfun_url}/api/v1/feeds/add",
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "MoneyRadar/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            return True
    except (URLError, json.JSONDecodeError) as e:
        print(f"  WARNING: Failed to add {feed_name}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Import RSSHub feeds into feeds.fun")
    parser.add_argument(
        "--rsshub",
        default="http://localhost:1200",
        help="RSSHub URL (default: http://localhost:1200)",
    )
    parser.add_argument(
        "--feedsfun",
        default="http://localhost:8000",
        help="feeds.fun URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--categories",
        default="finance,tech,policy,market,general",
        help="Comma-separated categories to import (default: finance,tech,policy,market,general)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only show what would be imported, don't actually add",
    )
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="List available categories",
    )

    args = parser.parse_args()

    if args.list_categories:
        print("Available categories:")
        for key, val in FEED_COLLECTIONS.items():
            print(f"  {key}: {val['name']} ({len(val['feeds'])} feeds)")
        return

    categories = [c.strip() for c in args.categories.split(",")]

    print("=== Money Radar — RSSHub Feed Importer ===")
    print()

    # Check RSSHub
    if not check_rsshub_health(args.rsshub):
        print("Make sure RSSHub is running: docker compose up -d rsshub")
        sys.exit(1)

    print()
    print("Feeds to import:")
    feeds = generate_feed_urls(args.rsshub, categories)
    print(f"\nTotal: {len(feeds)} feeds")
    print()

    if args.dry_run:
        print("DRY RUN — no feeds will be added.")
        print()
        for feed in feeds:
            print(f"  [{feed['category']}] {feed['name']}")
            print(f"    {feed['url']}")
        return

    # Import feeds
    print("Importing feeds...")
    success = 0
    failed = 0
    for feed in feeds:
        print(f"  Adding {feed['name']}...", end=" ")
        if add_feed_to_feedsfun(args.feedsfun, feed["url"], feed["name"]):
            print("OK")
            success += 1
        else:
            print("FAILED")
            failed += 1

    print()
    print(f"Done: {success} added, {failed} failed out of {len(feeds)} total.")


if __name__ == "__main__":
    main()
