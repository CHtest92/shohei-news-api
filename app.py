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

# 擷取網站標示發布日期（YYYY-MM-DD）
def get_display_date(entry):
    try:
        raw = entry.published_parsed
        date = datetime(*raw[:3])
        return date.strftime("%Y-%m-%d")
    except:
        return "Unknown"

# 清除 HTML 的摘要內容
def clean_summary(summary):
    try:
        soup = BeautifulSoup(summary, "html.parser")
        for tag in soup.find_all("img"):
            tag.decompose()
        for br in soup.find_all("br"):
            br.replace_with("\n")
        return soup.get_text("\n").strip()
    except:
        return summary

# 最新新聞（近 12 小時，最多 10 則）
@app.route("/smart_news")
def smart_news():
    feed = feedparser.parse(RSS_URL)
    now = datetime.utcnow()
    result = []

    for entry in feed.entries:
        published = datetime(*entry.published_parsed[:6])
        if (now - published).total_seconds() <= 43200:
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

# 單篇新聞內容（透過 URL）
@app.route("/get_news_by_link")
def get_news_by_link():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    feed = feedparser.parse(RSS_URL)
    for entry in feed.entries:
        if entry.link == url:
            summary = clean_summary(entry.get("summary", ""))
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

# 關鍵字搜尋（標題與摘要）
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

# 錯誤提示範例（Render 休眠或 timeout）
@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Render backend may be sleeping. Please try again in 30 seconds."}), 500

# 主程式
if __name__ == '__main__':
    app.run(debug=True)
