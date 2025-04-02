from flask import Flask, request, jsonify
import feedparser
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

app = Flask(__name__)

# RSS 來源
RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/%E5%A4%A7%E8%B0%B7%E7%BF%94%E5%B9%B3%E6%96%B0%E8%81%9E?type=rss"

# 翻譯標題與摘要

def translate(text):
    try:
        return GoogleTranslator(source='auto', target='zh-tw').translate(text)
    except:
        return text

# 發布時間格式轉換

def get_published_time(entry):
    try:
        return datetime(*entry.published_parsed[:6])
    except:
        return datetime.utcnow()

# 近 12 小時最多 10 則
@app.route("/smart_news")
def smart_news():
    feed = feedparser.parse(RSS_URL)
    now = datetime.utcnow()
    result = []
    for entry in feed.entries:
        published = get_published_time(entry)
        if (now - published).total_seconds() <= 43200:
            result.append({
                "title": entry.title,
                "translated_title": translate(entry.title),
                "summary": entry.get("summary", ""),
                "translated_summary": translate(entry.get("summary", "")),
                "link": entry.link,
                "published": entry.published,
                "source": entry.get("source", {}).get("title", "Unknown")
            })
        if len(result) >= 10:
            break
    return jsonify(result)

# 所有最新 10 則
@app.route("/list_news_with_link")
def list_news_with_link():
    feed = feedparser.parse(RSS_URL)
    result = []
    for entry in feed.entries[:10]:
        result.append({
            "title": entry.title,
            "translated_title": translate(entry.title),
            "summary": entry.get("summary", ""),
            "translated_summary": translate(entry.get("summary", "")),
            "link": entry.link,
            "published": entry.published,
            "source": entry.get("source", {}).get("title", "Unknown")
        })
    return jsonify(result)

# 搜尋
@app.route("/search_news")
def search_news():
    keyword = request.args.get("keyword", "")
    if not keyword:
        return jsonify({"error": "Missing keyword"}), 400

    feed = feedparser.parse(RSS_URL)
    result = []
    for entry in feed.entries:
        if keyword.lower() in entry.title.lower() or keyword.lower() in entry.get("summary", "").lower():
            result.append({
                "title": entry.title,
                "translated_title": translate(entry.title),
                "summary": entry.get("summary", ""),
                "translated_summary": translate(entry.get("summary", "")),
                "link": entry.link,
                "published": entry.published,
                "source": entry.get("source", {}).get("title", "Unknown")
            })
        if len(result) >= 10:
            break
    return jsonify(result)

# 取得單一新聞內容
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
                "summary": entry.get("summary", ""),
                "content": entry.get("summary", ""),
                "published": entry.published,
                "source": entry.get("source", {}).get("title", "Unknown"),
                "link": entry.link
            })
    return jsonify({"error": "Article not found", "link": url}), 404

if __name__ == '__main__':
    app.run(debug=True)
