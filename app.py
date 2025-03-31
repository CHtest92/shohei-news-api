from flask import Flask, request, jsonify
import feedparser
import hashlib
from datetime import datetime, timedelta

app = Flask(__name__)

# Inoreader RSS 來源
RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/%E5%A4%A7%E8%B0%B7%E7%BF%94%E5%B9%B3%E6%96%B0%E8%81%9E?type=rss"

# 假翻譯：實務可串 GPT API
def translate_title(title):
    return title.replace("　", " ").replace("“", "\"").replace("”", "\"")

# 路由：取得最新 10 則新聞（含翻譯標題）
@app.route("/list_news_with_link")
def list_news_with_link():
    feed = feedparser.parse(RSS_URL)
    news_list = []
    for entry in feed.entries[:10]:
        news_list.append({
            "title": entry.title,
            "translated_title": translate_title(entry.title),
            "link": entry.link,
            "published": entry.published,
            "source": entry.get("source", {}).get("title", "Unknown")
        })
    return jsonify(news_list)

# 路由：依照 URL 抓取新聞全文
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
                "translated_title": translate_title(entry.title),
                "content": entry.description,
                "published": entry.published,
                "source": entry.get("source", {}).get("title", "Unknown"),
                "link": entry.link
            })
    return jsonify({"error": "Article not found"}), 404

# 路由：搜尋新聞（最多 10 筆）
@app.route("/search_news")
def search_news():
    keyword = request.args.get("keyword", "")
    if not keyword:
        return jsonify({"error": "Missing keyword"}), 400

    feed = feedparser.parse(RSS_URL)
    results = []
    for entry in feed.entries:
        if keyword.lower() in entry.title.lower() or keyword.lower() in entry.description.lower():
            results.append({
                "title": entry.title,
                "translated_title": translate_title(entry.title),
                "link": entry.link,
                "published": entry.published,
                "source": entry.get("source", {}).get("title", "Unknown")
            })
        if len(results) >= 10:
            break
    return jsonify(results)

# 路由：近 12 小時內新聞（補滿最多 10 則）
@app.route("/smart_news")
def smart_news():
    feed = feedparser.parse(RSS_URL)
    news_list = []
    now = datetime.utcnow()
    for entry in feed.entries:
        try:
            published = datetime(*entry.published_parsed[:6])
            if now - published <= timedelta(hours=12):
                news_list.append({
                    "title": entry.title,
                    "translated_title": translate_title(entry.title),
                    "link": entry.link,
                    "published": entry.published,
                    "source": entry.get("source", {}).get("title", "Unknown")
                })
        except Exception:
            continue
    for entry in feed.entries:
        if len(news_list) >= 10:
            break
        if not any(item['link'] == entry.link for item in news_list):
            news_list.append({
                "title": entry.title,
                "translated_title": translate_title(entry.title),
                "link": entry.link,
                "published": entry.published,
                "source": entry.get("source", {}).get("title", "Unknown")
            })
    return jsonify(news_list)

# 路由：近 12 小時內新聞（最多 10 則，不補滿）
@app.route("/recent_news")
def recent_news():
    feed = feedparser.parse(RSS_URL)
    recent_list = []
    now = datetime.utcnow()
    for entry in feed.entries:
        try:
            published = datetime(*entry.published_parsed[:6])
            if now - published <= timedelta(hours=12):
                recent_list.append({
                    "title": entry.title,
                    "translated_title": translate_title(entry.title),
                    "link": entry.link,
                    "published": entry.published,
                    "source": entry.get("source", {}).get("title", "Unknown")
                })
        except Exception:
            continue
        if len(recent_list) >= 10:
            break
    return jsonify(recent_list)

# 主程式啟動（開發用）
if __name__ == '__main__':
    app.run(debug=True)
