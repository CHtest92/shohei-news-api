from flask import Flask, request, jsonify
import feedparser
from googletrans import Translator

app = Flask(__name__)

RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/大谷翔平新聞/view?type=rss"

# 翻譯工具
translator = Translator()

@app.route("/latest_news")
def latest_news():
    feed = feedparser.parse(RSS_URL)
    entries = feed.entries

    # 先篩選出 12 小時內的
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    recent_entries = []
    for entry in entries:
        if "published_parsed" in entry:
            published = datetime(*entry.published_parsed[:6])
            if now - published <= timedelta(hours=12):
                recent_entries.append(entry)

    # 若不足 10 則，補滿
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
    translated = translator.translate(entry.title + "\n\n" + entry.description, dest='zh-tw')

    return jsonify({
        "title": translated.text.split("\n\n")[0],
        "content": translated.text.split("\n\n")[1] if "\n\n" in translated.text else translated.text
    })


@app.route("/")
def index():
    return "Shohei News API is running!"

if __name__ == "__main__":
    app.run(debug=True)
