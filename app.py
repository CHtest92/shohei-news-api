from flask import Flask, request, jsonify
import feedparser
from datetime import datetime, timedelta
from googletrans import Translator

app = Flask(__name__)
translator = Translator()

# RSS 資料來源
RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/大谷翔平新聞?type=rss"

# 翻譯標題（googletrans）
def translate_title(title):
    try:
        translated = translator.translate(title, dest="zh-tw")
        return translated.text
    except Exception as e:
        return f"(翻譯失敗: {str(e)})"

# 健康檢查
@app.route("/")
def home():
    return "Shohei News API is running"

# 最新新聞（不管時間）最多 10 則
@app.route("/latest_news")
def latest_news():
    feed = feedparser.parse(RSS_URL)
    news_list = []
    for idx, entry in enumerate(feed.entries[:10]):
        translated_title = translate_title(entry.title)
        news_list.append({
            "id": idx + 1,
            "title": entry.title,
            "translated_title": translated_title,
            "link": entry.link,
            "published": datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d %H:%M:%S"),
            "source": entry.get("source", {}).get("title", "來源不明")
        })
    return jsonify(news_list)

# 指定編號的新聞內容
@app.route("/get_news")
def get_news():
    try:
        news_id = int(request.args.get("id", 1)) - 1
        feed = feedparser.parse(RSS_URL)
        if news_id >= len(feed.entries) or news_id < 0:
            return jsonify({"error": "新聞編號超出範圍"})
        entry = feed.entries[news_id]
        translated_title = translate_title(entry.title)
        return jsonify({
            "title": entry.title,
            "translated_title": translated_title,
            "content": entry.description,
            "link": entry.link,
            "published": datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d %H:%M:%S"),
            "source": entry.get("source", {}).get("title", "來源不明")
        })
    except Exception as e:
        return jsonify({"error": str(e)})

# 最近 12 小時內的新聞（最多 10 則）
@app.route("/recent_news")
def recent_news():
    feed = feedparser.parse(RSS_URL)
    cutoff_time = datetime.utcnow() - timedelta(hours=12)
    recent_list = []
    for entry in feed.entries:
        published_time = datetime(*entry.published_parsed[:6])
        if published_time >= cutoff_time:
            translated_title = translate_title(entry.title)
            recent_list.append({
                "title": entry.title,
                "translated_title": translated_title,
                "link": entry.link,
                "published": published_time.strftime("%Y-%m-%d %H:%M:%S"),
                "source": entry.get("source", {}).get("title", "來源不明")
            })
        if len(recent_list) >= 10:
            break
    return jsonify(recent_list)

# 搜尋含關鍵字的新聞（最多 10 則）
@app.route("/search_news")
def search_news():
    keyword = request.args.get("keyword", "").lower()
    if not keyword:
        return jsonify({"error": "請提供 keyword 參數"})
    
    feed = feedparser.parse(RSS_URL)
    matched_list = []
    for entry in feed.entries:
        title = entry.title.lower()
        content = entry.description.lower()
        if keyword in title or keyword in content:
            translated_title = translate_title(entry.title)
            matched_list.append({
                "title": entry.title,
                "translated_title": translated_title,
                "link": entry.link,
                "published": datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d %H:%M:%S"),
                "source": entry.get("source", {}).get("title", "來源不明")
            })
        if len(matched_list) >= 10:
            break
    return jsonify(matched_list)

# smart_news：優先取近 12 小時內新聞，不足補舊到 10 則
@app.route("/smart_news")
def smart_news():
    feed = feedparser.parse(RSS_URL)
    cutoff_time = datetime.utcnow() - timedelta(hours=12)
    smart_list = []

    for entry in feed.entries:
        published_time = datetime(*entry.published_parsed[:6])
        translated_title = translate_title(entry.title)
        news_item = {
            "title": entry.title,
            "translated_title": translated_title,
            "link": entry.link,
            "published": published_time.strftime("%Y-%m-%d %H:%M:%S"),
            "source": entry.get("source", {}).get("title", "來源不明")
        }
        if published_time >= cutoff_time:
            smart_list.append(news_item)

    if len(smart_list) < 10:
        for entry in feed.entries:
            published_time = datetime(*entry.published_parsed[:6])
            translated_title = translate_title(entry.title)
            news_item = {
                "title": entry.title,
                "translated_title": translated_title,
                "link": entry.link,
                "published": published_time.strftime("%Y-%m-%d %H:%M:%S"),
                "source": entry.get("source", {}).get("title", "來源不明")
            }
            if news_item not in smart_list:
                smart_list.append(news_item)
            if len(smart_list) >= 10:
                break

    return jsonify(smart_list)

if __name__ == "__main__":
    app.run(debug=True)
