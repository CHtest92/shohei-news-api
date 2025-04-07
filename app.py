from flask import Flask, request, jsonify
import feedparser
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
from email.utils import parsedate_to_datetime
import re

app = Flask(__name__)

# RSS 來源
RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/%E5%A4%A7%E8%B0%B7%E7%BF%94%E5%B9%B3%E6%96%B0%E8%81%9E?type=rss"

# 翻譯工具
def translate(text):
    try:
        return GoogleTranslator(source='auto', target='zh-tw').translate(text)
    except:
        return text

# 擷取網站顯示的日期（非時區換算）
def get_display_date(entry):
    try:
        dt = parsedate_to_datetime(entry.published)
        return dt.strftime("%Y-%m-%d")
    except:
        return "未知"

# 清除 HTML img 和多餘標籤
def clean_summary(summary):
    summary = re.sub(r'<img[^>]*>', '', summary)
    summary = re.sub(r'<br\s*/?>', '\n', summary)
    summary = re.sub(r'</p>|</div>', '\n', summary)
    summary = re.sub(r'<[^>]+>', '', summary)
    return summary.strip()

@app.route("/smart_news")
def smart_news():
    feed = feedparser.parse(RSS_URL)
    result = []
    now = datetime.utcnow()

    for entry in feed.entries:
        try:
            published_dt = parsedate_to_datetime(entry.published)
        except:
            continue

        if (now - published_dt).total_seconds() <= 43200:  # 12 小時內
            summary = clean_summary(entry.get("summary", ""))
            result.append({
                "title": entry.title,
                "translated_title": translate(entry.title),
                "summary": summary,
                "translated_summary": translate(summary),
                "link": entry.link,
                "published": get_display_date(entry),
                "source": entry.get("source", {}).get("title", "Unknown")
            })

        if len(result) >= 10:
            break

    return jsonify(result)

@app.route("/get_news_by_link")
def get_news_by_link():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    feed = feedparser.parse(RSS_URL)
    for entry in feed.entries:
        if entry.link == url:
            content = clean_summary(entry.get("summary", ""))
            return jsonify({
                "title": entry.title,
                "translated_title": translate(entry.title),
                "summary": content,
                "content": content,
                "published": get_display_date(entry),
                "source": entry.get("source", {}).get("title", "Unknown"),
                "link": entry.link
            })
    return jsonify({"error": "Article not found", "link": url}), 404

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
            results.append({
                "title": title,
                "translated_title": translate(title),
                "summary": summary,
                "translated_summary": translate(summary),
                "link": entry.link,
                "published": get_display_date(entry),
                "source": entry.get("source", {}).get("title", "Unknown")
            })
        if len(results) >= 10:
            break
    return jsonify(results)

# 自動喚醒錯誤提示
@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "伺服器可能正在喚醒中，請稍候再試"}), 500

if __name__ == '__main__':
    app.run(debug=True)
