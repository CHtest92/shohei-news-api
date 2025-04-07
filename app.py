from flask import Flask, request, jsonify
import feedparser
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
from email.utils import parsedate_to_datetime
import re

app = Flask(__name__)

# RSS 來源（大谷翔平新聞）
RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/%E5%A4%A7%E8%B0%B7%E7%BF%94%E5%B9%B3%E6%96%B0%E8%81%9E?type=rss"

# 翻譯工具（標題與摘要）
def translate(text):
    try:
        return GoogleTranslator(source='auto', target='zh-tw').translate(text)
    except:
        return text

# 清理 HTML summary（保留換行）
def clean_summary(summary):
    summary = re.sub(r'<img[^>]*>', '', summary)  # 移除圖片
    summary = re.sub(r'<br\s*/?>', '\n', summary)  # br 換成換行
    summary = re.sub(r'</p>|</div>', '\n', summary)  # p/div 結尾換行
    summary = re.sub(r'<[^>]+>', '', summary)  # 移除其他 HTML
    return summary.strip()

# 回傳日期為 RSS 標示日（網站呈現日期）
def get_display_date(entry):
    try:
        pub_date = parsedate_to_datetime(entry.published)
        return pub_date.strftime("%Y-%m-%d")  # yyyy-mm-dd 格式
    except:
        return "Unknown"

# 最新新聞（近 12 小時內最多 10 則）
@app.route("/smart_news")
def smart_news():
    feed = feedparser.parse(RSS_URL)
    now = datetime.utcnow()
    result = []

    for entry in feed.entries:
        published_dt = parsedate_to_datetime(entry.published)
        if (now - published_dt).total_seconds() <= 43200:  # 12 小時
            summary_raw = entry.get("summary", "")
            summary = clean_summary(summary_raw)
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

# 取得指定新聞連結的內容
@app.route("/get_news_by_link")
def get_news_by_link():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    feed = feedparser.parse(RSS_URL)
    for entry in feed.entries:
        if entry.link == url:
            summary_raw = entry.get("summary", "")
            summary = clean_summary(summary_raw)
            return jsonify({
                "title": entry.title,
                "translated_title": translate(entry.title),
                "summary": summary,
                "content": summary,
                "published": get_display_date(entry),
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
    now = datetime.utcnow()
    results = []
    for entry in feed.entries:
        title = entry.title
        summary_raw = entry.get("summary", "")
        summary = clean_summary(summary_raw)
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

# 錯誤處理
@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "伺服器暫時無法回應，請稍後再試"}), 500

# 本地測試用
if __name__ == '__main__':
    app.run(debug=True)
