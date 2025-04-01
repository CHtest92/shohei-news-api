from flask import Flask, request, jsonify
import feedparser
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

app = Flask(__name__)

# RSS 來源（大谷翔平新聞）
RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/%E5%A4%A7%E8%B0%B7%E7%BF%94%E5%B9%B3%E6%96%B0%E8%81%9E?type=rss"

# 翻譯標題與摘要
def translate(text):
    try:
        return GoogleTranslator(source='auto', target='zh-tw').translate(text)
    except:
        return text  # 若失敗就原樣返回

# 時間格式處理
def get_published_time(entry):
    try:
        return datetime(*entry.published_parsed[:6])
    except:
        return datetime.utcnow()

# 取得最新 12 小時內最多 10 則新聞
@app.route("/smart_news")
def smart_news():
    feed = feedparser.parse(RSS_URL)
    now = datetime.utcnow()
    result = []

    for entry in feed.entries:
        published = get_published_time(entry)
        if (now - published).total_seconds() <= 43200:  # 12 小時內
            result.append(entry)
        if len(result) >= 10:
            break

    news_list = []
    for entry in result:
        title = entry.title
        summary = entry.get("summary", "")
        news_list.append({
            "title": title,
            "translated_title": translate(title),
            "translated_summary": translate(summary),
            "link": entry.link,
            "published": entry.published,
            "source": entry.get("source", {}).get("title", "Unknown")
        })

    return jsonify(news_list)

# 指定網址新聞內容（只取摘要）
@app.route("/get_news_by_link")
def get_news_by_link():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    feed = feedparser.parse(RSS_URL)
    for entry in feed.entries:
        if entry.link == url:
            return jsonify({
                "title": entry.title,
                "translated_title": translate(entry.title),
                "content": entry.get("summary", ""),
                "published": entry.published,
                "link": entry.link,
                "source": entry.get("source", {}).get("title", "Unknown")
            })
    return jsonify({"error": "Article not found"}), 404

# 搜尋新聞
@app.route("/search_news")
def search_news():
    keyword = request.args.get("keyword", "").lower()
    if not keyword:
        return jsonify({"error": "Missing keyword"}), 400

    feed = feedparser.parse(RSS_URL)
    results = []
    for entry in feed.entries:
        if keyword in entry.title.lower() or keyword in entry.get("summary", "").lower():
            results.append({
                "title": entry.title,
                "translated_title": translate(entry.title),
                "translated_summary": translate(entry.get("summary", "")),
                "link": entry.link,
                "published": entry.published,
                "source": entry.get("source", {}).get("title", "Unknown")
            })
        if len(results) >= 10:
            break
    return jsonify(results)

# 啟動 Flask
if __name__ == '__main__':
    app.run(debug=True)
