from flask import Flask, request, jsonify
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

app = Flask(__name__)

RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/%E5%A4%A7%E8%B0%B7%E7%BF%94%E5%B9%B3%E6%96%B0%E8%81%9E/type/rss"

@app.route("/latest_news")
def latest_news():
    feed = feedparser.parse(RSS_URL)
    news_list = []

    # 抓取近 12 小時的新聞，補足為 10 則
    cutoff_time = datetime.utcnow() - timedelta(hours=12)
    count = 0
    for idx, entry in enumerate(feed.entries):
        published = entry.get("published", "")
        try:
            published_time = datetime.strptime(published, "%a, %d %b %Y %H:%M:%S %z")
        except:
            published_time = datetime.utcnow()

        news_list.append({
            "id": idx + 1,
            "title": entry.title,
            "published": published_time.strftime("%Y-%m-%d %H:%M:%S"),
            "source": entry.get("source", {}).get("title", "Unknown"),
            "link": entry.link
        })

        count += 1
        if count >= 10:
            break

    return jsonify(news_list)

@app.route("/get_news")
def get_news():
    try:
        news_id = int(request.args.get("id", 1)) - 1
        feed = feedparser.parse(RSS_URL)
        if news_id >= len(feed.entries):
            return jsonify({"error": "指定的新聞編號不存在。"}), 404

        entry = feed.entries[news_id]
        # 嘗試取出純文字內容
        raw_html = entry.get("description", "")
        soup = BeautifulSoup(raw_html, "html.parser")
        content = soup.get_text().strip()

        if not content:
            return jsonify({"error": "新聞來源未提供完整內容，請稍後再試。"}), 502

        return jsonify({
            "title": entry.title,
            "content": content
        })
    except Exception as e:
        return jsonify({"error": f"發生錯誤：{str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
