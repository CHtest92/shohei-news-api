from flask import Flask, jsonify
import feedparser
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)

FEED_URLS = [
    "https://your-inoreader-filtered-feed-1.xml",
    "https://your-inoreader-filtered-feed-2.xml"
]

def parse_entries():
    all_items = []
    for url in FEED_URLS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            published = entry.get("published", "") or entry.get("pubDate", "")
            item = {
                "title": entry.title,
                "summary": entry.summary if "summary" in entry else entry.get("description", ""),
                "published": published,
                "link": entry.link,
                "source": entry.get("source", {}).get("title") or feed.feed.get("title") or "未知來源"
            }
            # 嘗試解析時間
            try:
                item["published_parsed"] = datetime(*entry.published_parsed[:6], tzinfo=pytz.utc)
            except:
                item["published_parsed"] = datetime.now(pytz.utc)
            all_items.append(item)
    return all_items

@app.route("/smart_news")
def smart_news():
    now = datetime.now(pytz.utc)
    all_items = parse_entries()

    recent_items = []
    for item in all_items:
        time_diff = now - item["published_parsed"]
        if time_diff <= timedelta(hours=18):
            recent_items.append(item)

    result = recent_items[:10]
    fallback = False

    if not result:
        result = all_items[:5]
        fallback = True

    return jsonify({
        "news": result,
        "fallback": fallback
    })

@app.route("/")
def index():
    return "Shohei News API running."

if __name__ == "__main__":
    app.run()
