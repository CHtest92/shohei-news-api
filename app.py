from flask import Flask, request, jsonify
import feedparser
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

app = Flask(__name__)

# Inoreader RSS 來源
RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/%E5%A4%A7%E8%B0%B7%E7%BF%94%E5%B9%B3%E6%96%B0%E8%81%9E?type=rss"

# 假翻譯標題
def translate_title(title):
    return title.replace("　", " ").replace("“", "\"").replace("”", "\"")

# 翻譯摘要與內容
def translate(text):
    try:
        return GoogleTranslator(source='auto', target='zh-tw').translate(text)
    except:
        return text

# 取得發布時間
def get_published_time(entry):
    try:
        return datetime(*entry.published_parsed[:6])
    except:
        return datetime.utcnow()

# 最新 10 則新聞清單（含翻譯標題、摘要翻譯、時間、連結）
@app.route("/list_news_with_link")
def list_news_with_link():
    feed = feedparser.parse(RSS_URL)
    news_list = []
    for entry in feed.entries[:10]:
        content = entry.get("summary", "")
        news_list.append({
            "title": entry.title,
            "translated_title": translate_title(entry.title),
            "summary": content,
            "translated_summary": translate(content),
            "link": entry.link,
            "published": entry.published,
            "source": entry.get("source", {}).get("title", "Unknown")
        })
    return jsonify(news_list)

# 指定時間內最多 10 則（範例：近 12 小時）
@app.route("/recent_news")
def recent_news():
    feed = feedparser.parse(RSS_URL)
    news_list = []
    now = datetime.utcnow()
    for entry in feed.entries:
        published = get_published_time(entry)
        if now - published <= timedelta(hours=12):
            news_list.append({
                "title": entry.title,
                "translated_title": translate_title(entry.title),
                "summary": entry.get("summary", ""),
                "translated_summary": translate(entry.get("summary", "")),
                "link": entry.link,
                "published": entry.published,
                "source": entry.get("source", {}).get("title", "Unknown")
            })
        if len(news_list) >= 10:
            break
    return jsonify(news_list)

# 關鍵字搜尋（標題 + 摘要）
@app.route("/search_news")
def search_news():
    keyword = request.args.get("keyword", "")
    if not keyword:
        return jsonify({"error": "Missing keyword"}), 400

    feed = feedparser.parse(RSS_URL)
    results = []
    for entry in feed.entries:
        if keyword.lower() in entry.title.lower() or keyword.lower() in entry.get("summary", "").lower():
            results.append({
                "title": entry.title,
                "translated_title": translate_title(entry.title),
                "summary": entry.get("summary", ""),
                "translated_summary": translate(entry.get("summary", "")),
                "link": entry.link,
                "published": entry.published,
                "source": entry.get("source", {}).get("title", "Unknown")
            })
        if len(results) >= 10:
            break
    return jsonify(results)

# 單篇新聞內容（只抓 RSS 摘要）
@app.route("/get_news_by_link")
def get_news_by_link():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    feed = feedparser.parse(RSS_URL)
    for entry in feed.entries:
        if entry.link == url:
            content = entry.get("summary", "")
            return jsonify({
                "title": entry.title,
                "translated_title": translate_title(entry.title),
                "content": content,
                "published": entry.published,
                "source": entry.get("source", {}).get("title", "Unknown"),
                "link": entry.link
            })
    return jsonify({"error": "Article not found"}), 404

# 啟動應用
if __name__ == '__main__':
    app.run(debug=True)
