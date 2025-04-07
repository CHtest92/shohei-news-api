from flask import Flask, request, jsonify
import feedparser
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
from bs4 import BeautifulSoup
from email.utils import parsedate_to_datetime

app = Flask(__name__)

# RSS 來源
RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/%E5%A4%A7%E8%B0%B7%E7%BF%94%E5%B9%B3%E6%96%B0%E8%81%9E?type=rss"

# 翻譯工具（標題與摘要）
def translate(text):
    try:
        return GoogleTranslator(source='auto', target='zh-tw').translate(text)
    except:
        return text

# 清除 HTML <img> 並保留文字段落與換行
def clean_summary(summary):
    try:
        soup = BeautifulSoup(summary, "html.parser")
        [img.decompose() for img in soup.find_all("img")]
        text = soup.get_text("\n", strip=True)
        return text
    except:
        return summary

# 發布時間格式轉換（保留網站顯示日期）
def get_published_date(entry):
    try:
        dt = parsedate_to_datetime(entry.published)
        return dt.strftime('%Y-%m-%d')
    except:
        return "未知日期"

# 最新新聞（近 12 小時，最多 10 則）
@app.route("/smart_news")
def smart_news():
    feed = feedparser.parse(RSS_URL)
    now = datetime.utcnow()
    result = []

    for entry in feed.entries:
        dt = parsedate_to_datetime(entry.published)
        if (now - dt).total_seconds() <= 43200:  # 12 小時
            raw_summary = entry.get("summary", "")
            cleaned = clean_summary(raw_summary)
            result.append({
                "title": entry.title,
                "translated_title": translate(entry.title),
                "summary": cleaned,
                "translated_summary": translate(cleaned),
                "link": entry.link,
                "published": get_published_date(entry),
                "source": entry.get("source", {}).get("title", "Unknown")
            })
        if len(result) >= 10:
            break

    return jsonify(result)

# 指定新聞（由 URL 抓取摘要）
@app.route("/get_news_by_link")
def get_news_by_link():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    feed = feedparser.parse(RSS_URL)
    for entry in feed.entries:
        if entry.link == url:
            raw_summary = entry.get("summary", "")
            cleaned = clean_summary(raw_summary)
            return jsonify({
                "title": entry.title,
                "translated_title": translate(entry.title),
                "summary": cleaned,
                "content": cleaned,
                "published": get_published_date(entry),
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
        raw_summary = entry.get("summary", "")
        cleaned = clean_summary(raw_summary)
        if keyword.lower() in title.lower() or keyword.lower() in cleaned.lower():
            results.append({
                "title": title,
                "translated_title": translate(title),
                "summary": cleaned,
                "translated_summary": translate(cleaned),
                "link": entry.link,
                "published": get_published_date(entry),
                "source": entry.get("source", {}).get("title", "Unknown")
            })
        if len(results) >= 10:
            break
    return jsonify(results)

# Render 錯誤備援
@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Render 伺服器可能尚未喚醒，請稍候 30 秒後重試。"}), 500

# 主程式
if __name__ == '__main__':
    app.run(debug=True)
