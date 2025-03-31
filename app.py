from flask import Flask, request, jsonify
import feedparser
from deep_translator import GoogleTranslator
from datetime import datetime, timedelta

app = Flask(__name__)

RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/大谷翔平新聞/view?type=rss"

@app.route("/latest_news")
def latest_news():
    feed = feedparser.parse(RSS_URL)
    entries = feed.entries

    # 過濾近 12 小時內的新聞
    now = datetime.utcnow()
    recent_entries = []
    for entry in entries:
        if "published_parsed" in entry:
            published = datetime(*entry.published_parsed[:6])
            if now - published <= timedelta(hours=12):
                recent_entries.append(entry)

    # 補滿至 10 則
    if len(recent_entries) < 10:
        recent_entries = entries[:10]

    news_list = []
    for idx, entry in enumerate(recent_entries):
        news_list.append({
            "id": idx + 1,
            "title": entry.title,
            "published": entry.published,
            "link": entry.link,
            "source": entry.get("source", {}).get("title", "來源不明")
        })

    return jsonify(news_list)

@app.route("/get_news")
def get_news():
    news_id = int(request.args.get("id", 1)) - 1
    feed = feedparser.parse(RSS_URL)
    entries = feed.entries

    if news_id < 0 or news_id >= len(entries):
        return jsonify({"error": "新聞編號超出範圍"}), 400

    entry = entries[news_id]

    translated_title = GoogleTranslator(source='auto', target='zh-tw').translate(entry.title)
    translated_content = GoogleTranslator(source='auto', target='zh-tw').translate(entry.description)

    return jsonify({
        "title": translated_title,
        "content": translated_content
    })

@app.route("/")
def index():
    return "Shohei News API is running!"

if __name__ == "__main__":
    app.run(debug=True)
