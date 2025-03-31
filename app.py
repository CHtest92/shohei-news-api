from flask import Flask, request, jsonify
import feedparser

app = Flask(__name__)

# RSS 資料來源
RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/大谷翔平新聞?type=rss"

# 首頁：健康檢查
@app.route("/")
def home():
    return "Shohei News API is running"

# 取得最新六則新聞標題
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

# 取得指定編號的新聞內容
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
