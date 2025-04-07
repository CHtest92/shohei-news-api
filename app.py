from flask import Flask, request, jsonify
import feedparser
from datetime import datetime, timedelta, timezone
from deep_translator import GoogleTranslator
from bs4 import BeautifulSoup

app = Flask(__name__)

# RSS 來源
RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/%E5%A4%A7%E8%B0%B7%E7%BF%94%E5%B9%B3%E6%96%B0%E8%81%9E?type=rss"

# HTML 清理
def clean_html(raw_html):
    soup = BeautifulSoup(raw_html, "html.parser")
    for img in soup(["img"]):
        img.decompose()
    text = soup.get_text(separator="\n")
    return text.strip()

# 翻譯工具
def translate(text):
    try:
        return GoogleTranslator(source='auto', target='zh-tw').translate(text)
    except:
        return text

# 擷取網站標示日期
def get_display_date(entry):
    try:
        return entry.published.split(" ")[1] + "-" + entry.published.split(" ")[2]
    except:
        return ""

# 發布時間格式處理（UTC 內部比對用）
def get_published_time(entry):
    try:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    except:
        return datetime.now(timezone.utc)

# 最新新聞（近 12 小時，最多 10 則）
@app.route("/smart_news")
def smart_news():
    feed = feedparser.parse(RSS_URL)
    now = datetime.now(timezone.utc)
    result = []

    for entry in feed.entries:
        published_dt = get_published_time(entry)
        if (now - published_dt).total_seconds() <= 43200:  # 12 小時內
            summary_raw = entry.get("summary", "")
            summary_clean = clean_html(summary_raw)
            result.append({
                "title": entry.title,
                "translated_title": translate(entry.title),
                "summary": summary_clean,
                "translated_summary": translate(summary_clean),
                "link": entry.link,
                "published": entry.published.split(",")[1].strip().split(" +")[0],  # 顯示網站原始日期時間
                "source": entry.get("source", {}).get("title", "Unknown")
            })
        if len(result) >= 10:
            break

    return jsonify(result)

# 根據連結取得單則新聞
@app.route("/get_news_by_link")
def get_news_by_link():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    feed = feedparser.parse(RSS_URL)
    for entry in feed.entries:
        if entry.link == url:
            summary_raw = entry.get("summary", "")
            summary_clean = clean_html(summary_raw)
            return jsonify({
                "title": entry.title,
                "translated_title": translate(entry.title),
                "summary": summary_clean,
                "content": summary_clean,
                "published": entry.published.split(",")[1].strip().split(" +")[0],
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
    now = datetime.now(timezone.utc)

    for entry in feed.entries:
        title = entry.title
        summary_raw = entry.get("summary", "")
        summary_clean = clean_html(summary_raw)

        if keyword.lower() in title.lower() or keyword.lower() in summary_clean.lower():
            results.append({
                "title": title,
                "translated_title": translate(title),
                "summary": summary_clean,
                "translated_summary": translate(summary_clean),
                "link": entry.link,
                "published": entry.published.split(",")[1].strip().split(" +")[0],
                "source": entry.get("source", {}).get("title", "Unknown")
            })
        if len(results) >= 10:
            break

    return jsonify(results)

# 自動預熱 ping
@app.route("/ping")
def ping():
    return "pong"

# 主程式
if __name__ == '__main__':
    app.run(debug=True)
