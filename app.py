from flask import Flask, request, jsonify
import feedparser
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
from bs4 import BeautifulSoup

app = Flask(__name__)

# RSS 來源
RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/%E5%A4%A7%E8%B0%B7%E7%BF%94%E5%B9%B3%E6%96%B0%E8%81%9E?type=rss"

# 翻譯工具（標題與摘要）
def translate(text):
    try:
        return GoogleTranslator(source='auto', target='zh-tw').translate(text)
    except:
        return text

# 清除 HTML 並保留段落與換行
def clean_html(raw_html):
    soup = BeautifulSoup(raw_html, "html.parser")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    return soup.get_text("\n", strip=True)

# 發布日期（網站顯示為主）
def get_display_date(entry):
    try:
        pub_date = datetime(*entry.published_parsed[:6])
        return pub_date.strftime("%Y-%m-%d")
    except:
        return ""

# 最新新聞（近 12 小時，最多 10 則）
@app.route("/smart_news")
def smart_news():
    feed = feedparser.parse(RSS_URL)
    now = datetime.utcnow()
    result = []

    for entry in feed.entries:
        published_time = datetime(*entry.published_parsed[:6])
        if (now - published_time).total_seconds() <= 43200:
            summary_raw = entry.get("summary", "")
            summary_clean = clean_html(summary_raw)
            result.append({
                "translated_title": translate(entry.title),
                "translated_summary": translate(summary_clean),
                "link": entry.link,
                "published": get_display_date(entry),
                "source": entry.get("source", {}).get("title", "Unknown")
            })
        if len(result) >= 10:
            break

    return jsonify(result)

# 指定新聞全文
@app.route("/get_news_by_link")
def get_news_by_link():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    feed = feedparser.parse(RSS_URL)
    for entry in feed.entries:
        if entry.link == url:
            summary = clean_html(entry.get("summary", ""))
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
        summary = clean_html(entry.get("summary", ""))
        if keyword.lower() in title.lower() or keyword.lower() in summary.lower():
            results.append({
                "translated_title": translate(title),
                "translated_summary": translate(summary),
                "link": entry.link,
                "published": get_display_date(entry),
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
