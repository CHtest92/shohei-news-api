from flask import Flask, request, jsonify
import feedparser
from datetime import datetime, timedelta
import time

app = Flask(__name__)

RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/大谷翔平新聞?type=rss"

@app.route("/")
def home():
    return "Shohei Ohtani News API is running."

@app.route("/latest_news")
def latest_news():
    feed = feedparser.parse(RSS_URL)
    twelve_hours_ago = datetime.utcnow() - timedelta(hours=12)
    news_list = []

    # 優先取近 12 小時內新聞
    for entry in feed.entries:
        if "published_parsed" in entry and entry.published_parsed:
            published_dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
            if published_dt > twelve_hours_ago:
                news_list.append({
                    "id": len(news_list) + 1,
                    "title": entry.title,
                    "published": published_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "source": entry.get("source", {}).get("title", "未知來源"),
                    "link": entry.link
                })
        if len(news_list) >= 10:
            break

    # 若不足 10 則 → 補舊聞
    if len(news_list) < 10:
        for entry in feed.entries:
            if len(news_list) >= 10:
                break
            if not any(news["title"] == entry.title for news in news_list):
                published_dt = datetime.fromtimestamp(time.mktime(entry.published_parsed)) if entry.published_parsed else None
                news_list.append({
                    "id": len(news_list) + 1,
                    "title": entry.title,
                    "published": published_dt.strftime("%Y-%m-%d %H:%M:%S") if published_dt else "不明",
                    "source": entry.get("source", {}).get("title", "未知來源"),
                    "link": entry.link
                })

    return jsonify(news_list)

@app.route("/get_news")
def get_news():
    try:
        news_id = int(request.args.get("id", 1)) - 1
        feed = feedparser.parse(RSS_URL)
        if news_id >= len(feed.entries) or news_id < 0:
            return jsonify({"error": "新聞編號超出範圍"})
        entry = feed.entries[news_id]
        return jsonify({
            "title": entry.title,
            "content": entry.description
        })
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)
