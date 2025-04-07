from flask import Flask, request, jsonify
import feedparser
from datetime import datetime, timedelta, timezone
import re
from deep_translator import GoogleTranslator

app = Flask(__name__)

RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/%E5%A4%A7%E8%B0%B7%E7%BF%94%E5%B9%B3%E6%96%B0%E8%81%9E?type=rss"

# 翻譯工具
def translate(text):
    try:
        return GoogleTranslator(source='auto', target='zh-tw').translate(text)
    except:
        return text

# 清除 HTML，保留段落與換行
def clean_summary(summary):
    summary = re.sub(r'<img[^>]*>', '', summary)  # 移除圖片
    summary = re.sub(r'<br\s*/?>', '\n', summary)  # 換行
    summary = re.sub(r'</p>', '\n', summary)
    summary = re.sub(r'<[^>]+>', '', summary)  # 其他標籤
    return summary.strip()

# 時間處理
def get_published_datetime(entry):
    try:
        return datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %z')
    except:
        return datetime.now(timezone.utc)

# 最新新聞（近 12 小時、最多 10 則）
@app.route("/smart_news")
def smart_news():
    feed = feedparser.parse(RSS_URL)
    now = datetime.now(timezone.utc)
    result = []

    for entry in feed.entries:
        published_dt = get_published_datetime(entry)
        published_date = published_dt.date().isoformat()  # 僅顯示網站標示日期

        if (now - published_dt).total_seconds() <= 43200:
            summary = clean_summary(entry.get("summary", ""))
            result.append({
                "title": entry.title,
                "translated_title": translate(entry.title),
                "summary": summary,
                "translated_summary": translate(summary),
                "link": entry.link,
                "published": published_date,
                "source": entry.get("source", {}).get("title", "Unknown")
            })

        if len(result) >= 10:
            break

    return jsonify(result)

# 根據連結取得單篇新聞
@app.route("/get_news_by_link")
def get_news_by_link():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    feed = feedparser.parse(RSS_URL)
    for entry in feed.entries:
        if entry.link == url:
            summary = clean_summary(entry.get("summary", ""))
            published_dt = get_published_datetime(entry)
            published_date = published_dt.date().isoformat()
            return jsonify({
                "title": entry.title,
                "translated_title": translate(entry.title),
                "summary": summary,
                "content": summary,
                "published": published_date,
                "source": entry.get("source", {}).get("title", "Unknown"),
                "link": entry.link
            })
    return jsonify({"error": "Article not found", "link": url}), 404

# 搜尋新聞
@app.route("/search_news")
def search_news():
    keyword = request.args.get("keyword", "")
    if not keyword:
        return jsonify({"error": "Missing keyword"}), 400

    feed = feedparser.parse(RSS_URL)
    results = []
    for entry in feed.entries:
        title = entry.title
        summary = clean_summary(entry.get("summary", ""))
        if keyword.lower() in title.lower() or keyword.lower() in summary.lower():
            published_dt = get_published_datetime(entry)
            published_date = published_dt.date().isoformat()
            results.append({
                "title": title,
                "translated_title": translate(title),
                "summary": summary,
                "translated_summary": translate(summary),
                "link": entry.link,
                "published": published_date,
                "source": entry.get("source", {}).get("title", "Unknown")
            })

        if len(results) >= 10:
            break

    return jsonify(results)

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Render backend may be sleeping. Please try again in 30 seconds."}), 500

if __name__ == '__main__':
    app.run(debug=True)
