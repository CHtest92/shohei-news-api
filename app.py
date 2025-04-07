from flask import Flask, request, jsonify
import feedparser
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
import re

app = Flask(__name__)

# RSS 來源
RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/%E5%A4%A7%E8%B0%B7%E7%BF%94%E5%B9%B3%E6%96%B0%E8%81%9E?type=rss"

# HTML 清理
TAG_RE = re.compile(r'<[^>]+>')
IMG_RE = re.compile(r'<img[^>]*>')
BR_RE = re.compile(r'<br */?>')

# 翻譯工具

def translate(text):
    try:
        return GoogleTranslator(source='auto', target='zh-CN').translate(text)
    except:
        return text

# 根據 RSS 預設格式找出「網站頁面」所顯示的日期

def extract_web_date(entry):
    if 'published_parsed' in entry:
        dt = datetime(*entry.published_parsed[:6])
        return dt.strftime('%Y-%m-%d')
    return ""

# 新聞清單
@app.route("/smart_news")
def smart_news():
    feed = feedparser.parse(RSS_URL)
    now = datetime.utcnow()
    result = []

    for entry in feed.entries:
        if 'published_parsed' not in entry:
            continue

        published_dt = datetime(*entry.published_parsed[:6])
        if (now - published_dt).total_seconds() <= 43200:  # 12 小時
            summary = entry.get("summary", "")
            summary = BR_RE.sub('\n', summary)
            summary = IMG_RE.sub('', summary)
            summary = TAG_RE.sub('', summary)

            result.append({
                "title": entry.title,
                "translated_title": translate(entry.title),
                "summary": summary,
                "translated_summary": translate(summary[:500]),
                "link": entry.link,
                "published": extract_web_date(entry),
                "source": entry.get("source", {}).get("title", "Unknown")
            })

        if len(result) >= 10:
            break

    return jsonify(result)

# 單篇新聞內容
@app.route("/get_news_by_link")
def get_news_by_link():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    feed = feedparser.parse(RSS_URL)
    for entry in feed.entries:
        if entry.link == url:
            content = entry.get("summary", "")
            content = BR_RE.sub('\n', content)
            content = IMG_RE.sub('', content)
            content = TAG_RE.sub('', content)

            return jsonify({
                "title": entry.title,
                "translated_title": translate(entry.title),
                "summary": content,
                "content": content,
                "published": extract_web_date(entry),
                "source": entry.get("source", {}).get("title", "Unknown"),
                "link": entry.link
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
        title = entry.title
        summary = entry.get("summary", "")
        if keyword.lower() in title.lower() or keyword.lower() in summary.lower():
            summary = BR_RE.sub('\n', summary)
            summary = IMG_RE.sub('', summary)
            summary = TAG_RE.sub('', summary)

            results.append({
                "title": title,
                "translated_title": translate(title),
                "summary": summary,
                "translated_summary": translate(summary[:500]),
                "link": entry.link,
                "published": extract_web_date(entry),
                "source": entry.get("source", {}).get("title", "Unknown")
            })
        if len(results) >= 10:
            break

    return jsonify(results)

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Server error, please try again later."}), 500

if __name__ == '__main__':
    app.run(debug=True)
