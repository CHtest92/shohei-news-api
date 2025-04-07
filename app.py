from flask import Flask, request, jsonify
import feedparser
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

app = Flask(__name__)

# 大谷小報專用 RSS 來源
RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/%E5%A4%A7%E8%B0%B7%E7%BF%94%E5%B9%B3%E6%96%B0%E8%81%9E?type=rss"

# 翻譯工具

def translate(text):
    try:
        return GoogleTranslator(source='auto', target='zh-tw').translate(text)
    except:
        return text

# 發布時間轉換

def get_published_time(entry):
    try:
        return datetime(*entry.published_parsed[:6])
    except:
        return datetime.utcnow()

# 最新新聞（近 12 小時最多 6 則，摘要裁切）
@app.route("/smart_news")
def smart_news():
    feed = feedparser.parse(RSS_URL)
    now = datetime.utcnow()
    result = []

    for entry in feed.entries:
        published = get_published_time(entry)
        if (now - published).total_seconds() <= 43200:
            title = entry.get("title", "")
            summary = entry.get("summary", "")[:300]
            translated_title = translate(title)
            translated_summary = translate(summary)
            link = entry.get("link", "")
            source = entry.get("source", {}).get("title", "Unknown")

            result.append({
                "title": title,
                "translated_title": translated_title,
                "summary": summary,
                "translated_summary": translated_summary,
                "link": link,
                "published": published.isoformat(),
                "source": source
            })
        if len(result) >= 6:
            break

    return jsonify(result)

# 取得單篇新聞
@app.route("/get_news_by_link")
def get_news_by_link():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    feed = feedparser.parse(RSS_URL)
    for entry in feed.entries:
        if entry.get("link") == url:
            title = entry.get("title", "")
            summary = entry.get("summary", "")[:300]
            translated_title = translate(title)
            published = get_published_time(entry).isoformat()
            source = entry.get("source", {}).get("title", "Unknown")

            return jsonify({
                "title": title,
                "translated_title": translated_title,
                "summary": summary,
                "content": summary,
                "published": published,
                "source": source,
                "link": url
            })

    return jsonify({"error": "Article not found", "link": url}), 404

# 關鍵字搜尋
@app.route("/search_news")
def search_news():
    keyword = request.args.get("keyword", "")
    if not keyword:
        return jsonify({"error": "Missing keyword"}), 400

    feed = feedparser.parse(RSS_URL)
    results = []
    for entry in feed.entries:
        title = entry.get("title", "")
        summary = entry.get("summary", "")[:300]
        if keyword.lower() in title.lower() or keyword.lower() in summary.lower():
            translated_title = translate(title)
            translated_summary = translate(summary)
            link = entry.get("link", "")
            published = get_published_time(entry).isoformat()
            source = entry.get("source", {}).get("title", "Unknown")

            results.append({
                "title": title,
                "translated_title": translated_title,
                "summary": summary,
                "translated_summary": translated_summary,
                "link": link,
                "published": published,
                "source": source
            })
        if len(results) >= 6:
            break
    return jsonify(results)

# Render 伺服器休眠錯誤處理
@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Unexpected backend error or malformed response. Please retry in 30 seconds."}), 500

if __name__ == '__main__':
    app.run(debug=True)
