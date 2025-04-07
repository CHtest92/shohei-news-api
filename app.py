from flask import Flask, request, jsonify
import feedparser
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
from bs4 import BeautifulSoup
from pytz import timezone

app = Flask(__name__)

# RSS 來源
RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/%E5%A4%A7%E8%B0%B7%E7%BF%94%E5%B9%B3%E6%96%B0%E8%81%9E?type=rss"

# 翻譯工具（標題與摘要）
def translate(text):
    try:
        return GoogleTranslator(source='auto', target='zh-tw').translate(text)
    except:
        return text

# 時區轉換函式：UTC → Asia/Taipei
def format_published_time(entry):
    try:
        utc_dt = datetime(*entry.published_parsed[:6])
    except:
        utc_dt = datetime.utcnow()
    taiwan_time = utc_dt.replace(tzinfo=timezone('UTC')).astimezone(timezone('Asia/Taipei'))
    return taiwan_time.strftime('%Y-%m-%d %H:%M:%S')

# 精簡摘要文字內容（去除 HTML 並裁切）
def clean_summary(html):
    try:
        text = BeautifulSoup(html, 'html.parser').get_text()
        return text[:300]  # 最多保留 300 字
    except:
        return html

# 最新新聞（近 12 小時，最多 10 則）
@app.route("/smart_news")
def smart_news():
    try:
        feed = feedparser.parse(RSS_URL)
        now = datetime.utcnow()
        result = []

        for entry in feed.entries:
            published = datetime(*entry.published_parsed[:6])
            if (now - published).total_seconds() <= 43200:  # 12 小時
                summary = entry.get("summary", "")
                clean = clean_summary(summary)
                result.append({
                    "title": entry.title,
                    "translated_title": translate(entry.title),
                    "summary": clean,
                    "translated_summary": translate(clean),
                    "link": entry.link,
                    "published": format_published_time(entry),
                    "source": entry.get("source", {}).get("title", "Unknown")
                })
            if len(result) >= 10:
                break

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": "Smart news loading failed", "reason": str(e)}), 500

# 指定新聞網址取得原文摘要
@app.route("/get_news_by_link")
def get_news_by_link():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    try:
        feed = feedparser.parse(RSS_URL)
        for entry in feed.entries:
            if entry.link == url:
                summary = entry.get("summary", "")
                clean = clean_summary(summary)
                return jsonify({
                    "title": entry.title,
                    "translated_title": translate(entry.title),
                    "summary": clean,
                    "content": clean,
                    "published": format_published_time(entry),
                    "source": entry.get("source", {}).get("title", "Unknown"),
                    "link": entry.link
                })
        return jsonify({"error": "Article not found", "link": url}), 404

    except Exception as e:
        return jsonify({"error": "Error retrieving article", "reason": str(e)}), 500

# 關鍵字搜尋（標題與摘要）
@app.route("/search_news")
def search_news():
    keyword = request.args.get("keyword", "")
    if not keyword:
        return jsonify({"error": "Missing keyword"}), 400

    try:
        feed = feedparser.parse(RSS_URL)
        results = []
        for entry in feed.entries:
            title = entry.title
            summary = entry.get("summary", "")
            clean = clean_summary(summary)
            if keyword.lower() in title.lower() or keyword.lower() in clean.lower():
                results.append({
                    "title": title,
                    "translated_title": translate(title),
                    "summary": clean,
                    "translated_summary": translate(clean),
                    "link": entry.link,
                    "published": format_published_time(entry),
                    "source": entry.get("source", {}).get("title", "Unknown")
                })
            if len(results) >= 10:
                break
        return jsonify(results)

    except Exception as e:
        return jsonify({"error": "Search failed", "reason": str(e)}), 500

# 主程式
if __name__ == '__main__':
    app.run(debug=True)
