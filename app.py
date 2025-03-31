from flask import Flask, request, jsonify
import feedparser

app = Flask(__name__)

RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/大谷翔平新聞?type=rss"

@app.route("/latest_news")
def latest_news():
    feed = feedparser.parse(RSS_URL)
    news_list = []
    for idx, entry in enumerate(feed.entries[:6]):
        news_list.append({
            "id": idx + 1,
            "title": entry.title
        })
    return jsonify(news_list)

@app.route("/get_news")
def get_news():
    news_id = int(request.args.get("id", 1)) - 1
    feed = feedparser.parse(RSS_URL)
    if news_id >= len(feed.entries):
        return jsonify({"error": "新聞編號超出範圍"})
    entry = feed.entries[news_id]
    return jsonify({
        "title": entry.title,
        "content": entry.description
    })

if __name__ == "__main__":
    app.run(debug=True)
