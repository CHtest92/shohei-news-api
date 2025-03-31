from flask import Flask, request, jsonify
import feedparser
from datetime import datetime, timedelta
from googletrans import Translator

app = Flask(__name__)
translator = Translator()

# RSS 來源
RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/大谷翔平新聞?type=rss"

# 翻譯標題
def translate_title(title):
    try:
        translated = translator.translate(title, dest="zh-tw")
        return translated.text
    except Exception:
        return title  # 若失敗就顯示原始

# 健康檢查
@app.route("/")
def home():
    return "Shohei News API is running"

# 最新新聞（不看時間）
@app.route("/latest_news")
def latest_news():
    feed = feedparser.parse(RSS_URL)
    news_list = []
    for entry in feed.entries[:10]:
        news_list.append({
            "title": entry.title,
            "translated_title": translate_title(entry.title),
            "link": entry.link,
            "published": datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d %H:%M:%S"),
            "source": entry.get("source", {}).get("title", "來源不明")
        })
    return jsonify(news_list)

# 近 12 小時新聞（最多 10 則）
@app.route("/recent_news")
def recent_news():
    feed = feedparser.parse(RSS_URL)
    cutoff_time = datetime.utcnow() - timedelta(hours=12)
    news_list = []
    for entry in feed.entries:
        published_time = datetime(*entry.published_parsed[:6])
        if published_time >= cutoff_time:
            news_list.append({
                "title": entry.title,
                "translated_title": translate_title(entry.title),
                "link": entry.link,
                "published": published_time.strftime("%Y-%m-%d %H:%M:%S"),
                "source": entry.get("source", {}).get("title", "來源不明")
            })
        if len(news_list) >= 10:
            break
    return jsonify(news_list)

# 智慧新聞（先抓近 12 小時，不足補舊的）
@app.route("/smart_news")
def smart_news():
    feed = feedparser.parse(RSS_URL)
    cutoff_time = datetime.utcnow() - timedelta(hours=12)
    smart_list = []

    for entry in feed.entries:
        published_time = datetime(*entry.published_parsed[:6])
        if published_time >= cutoff_time:
            smart_list.append({
                "title": entry.title,
                "translated_title": translate_title(entry.title),
                "link": entry.link,
                "published": published_time.strftime("%Y-%m-%d %H:%M:%S"),
                "source": entry.get("source", {}).get("title", "來源不明")
            })
        if len(smart_list) >= 10:
            return jsonify(smart_list)

    # 補滿 10 則
    for entry in feed.entries:
        item = {
            "title": entry.title,
            "translated_title": translate_title(entry.title),
            "link": entry.link,
            "published": datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d %H:%M:%S"),
            "source": entry.get("source", {}).get("title", "來源不明")
        }
        if item not in smart_list:
            smart_list.append(item)
        if len(smart_list) >= 10:
            break
    return jsonify(smart_list)

# 關鍵字搜尋
@app.route("/search_news")
def search_news():
    keyword = request.args.get("keyword", "").lower()
    if not keyword:
        return jsonify({"error": "請提供 keyword 參數"})
    feed = feedparser.parse(RSS_URL)
    matched = []
    for entry in feed.entries:
        if keyword in entry.title.lower() or keyword in entry.description.lower():
            matched.append({
                "title": entry.title,
                "translated_title": translate_title(entry.title),
                "link": entry.link,
                "published": datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d %H:%M:%S"),
                "source": entry.get("source", {}).get("title", "來源不明")
            })
        if len(matched) >= 10:
            break
    return jsonify(matched)

# 用連結取新聞全文（精準對應）
@app.route("/get_news_by_link")
def get_news_by_link():
    url = request.args.get("url", "")
    if not url:
        return jsonify({"error": "請提供新聞網址 URL"})
    feed = feedparser.parse(RSS_URL)
    for entry in feed.entries:
        if entry.link == url:
            return jsonify({
                "title": entry.title,
                "translated_title": translate_title(entry.title),
                "content": entry.description,
                "link": entry.link,
                "published": datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d %H:%M:%S"),
                "source": entry.get("source", {}).get("title", "來源不明")
            })
    return jsonify({"error": "找不到對應新聞"})

# 最新新聞清單（含翻譯標題 + 連結）
@app.route("/list_news_with_link")
def list_news_with_link():
    feed = feedparser.parse(RSS_URL)
    news_list = []
    for entry in feed.entries[:10]:
        news_list.append({
            "title": entry.title,
            "translated_title": translate_title(entry.title),
            "link": entry.link,
            "published": datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d %H:%M:%S"),
            "source": entry.get("source", {}).get("title", "來源不明")
        })
    return jsonify(news_list)

if __name__ == "__main__":
    app.run(debug=True)
