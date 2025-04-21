from flask import Flask, jsonify, request
from datetime import datetime, timedelta
import feedparser
from deep_translator import GoogleTranslator
from bs4 import BeautifulSoup
import pytz

app = Flask(__name__)

RSS_FEEDS = [
    "https://news.yahoo.co.jp/rss/topics/sports.xml",
    "https://full-count.jp/feed/",
    "https://news.yahoo.co.jp/rss/media/full_count/all.xml"
]

KEYWORDS = ["大谷翔平", "ohtani", "Ohtani", "shohei ohtani"]
MAX_NEWS = 10
TIME_WINDOW_HOURS = 12
TARGET_LANG = "zh-TW"

def clean_html(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    for img in soup.find_all("img"):
        img.decompose()
    return soup.get_text(separator="\n").strip()

@app.route("/smart_news", methods=["GET"])
def smart_news():
    now = datetime.utcnow().replace(tzinfo=pytz.utc)
    news_items = []

    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            published_parsed = entry.get("published_parsed")
            if not published_parsed:
                continue
            published_dt = datetime(*published_parsed[:6], tzinfo=pytz.utc)
            if (now - published_dt).total_seconds() > TIME_WINDOW_HOURS * 3600:
                continue

            title = entry.get("title", "")
            summary = clean_html(entry.get("summary", ""))
            content_combined = f"{title}\n{summary}"

            if not any(keyword.lower() in content_combined.lower() for keyword in KEYWORDS):
                continue

            translated_title = GoogleTranslator(source="auto", target=TARGET_LANG).translate(title)
            translated_summary = GoogleTranslator(source="auto", target=TARGET_LANG).translate(summary)

            news_items.append({
                "translated_title": translated_title,
                "translated_summary": translated_summary,
                "link": entry.get("link", ""),
                "published": published_dt.strftime("%Y-%m-%d"),
                "source": entry.get("source", {}).get("title", "Unknown")
            })

    news_items = sorted(news_items, key=lambda x: x["published"], reverse=True)[:MAX_NEWS]
    return jsonify(news_items)

if __name__ == "__main__":
    app.run(debug=True)
