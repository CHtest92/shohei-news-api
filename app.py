from datetime import datetime, timedelta
from flask import Flask, jsonify
import feedparser
import html
import re

app = Flask(__name__)

RSS_FEEDS = [
    "https://full-count.jp/feed/",
    "https://news.yahoo.co.jp/rss/media/full-c.xml"
]

KEYWORDS = ["大谷翔平", "shohei ohtani"]
MAX_ARTICLES = 10
TIME_WINDOW_HOURS = 18  # 時間拉長至近 18 小時內

def clean_html(text):
    text = re.sub(r'<img[^>]*>', '', text)  # 移除圖片
    text = re.sub(r'<br\s*/?>', '\n', text)  # <br> 換行
    text = re.sub(r'</p>|</div>', '\n', text)  # <p> <div> 段落結尾換行
    text = re.sub(r'<[^>]+>', '', text)  # 移除其他 HTML 標籤
    return html.unescape(text).strip()

def contains_keywords(entry):
    content = (entry.get("title", "") + " " + entry.get("summary", "")).lower()
    return any(keyword in content for keyword in [k.lower() for k in KEYWORDS])

@app.route("/smart_news", methods=["GET"])
def smart_news():
    now = datetime.utcnow()
    articles = []

    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            published = entry.get("published_parsed")
            if not published:
                continue
            published_dt = datetime(*published[:6])
            if (now - published_dt).total_seconds() > TIME_WINDOW_HOURS * 3600:
                continue
            if not contains_keywords(entry):
                continue
            title = clean_html(entry.get("title", ""))
            summary = clean_html(entry.get("summary", ""))
            published_str = published_dt.strftime("%Y-%m-%d")
            source = re.sub(r'\s*-\s*.*$', '', entry.get("source", {}).get("title", entry.get("title", "")))
            link = entry.get("link", "")
            articles.append({
                "title": title,
                "summary": summary,
                "published": published_str,
                "source": source,
                "link": link
            })

    articles = sorted(articles, key=lambda x: x["published"], reverse=True)
    return jsonify(articles[:MAX_ARTICLES])

if __name__ == "__main__":
    app.run(debug=True)
