from flask import Flask, request, jsonify
import feedparser
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
from pytz import timezone, utc
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

# 時間轉為台灣時間
def get_published_time(entry):
    try:
        utc_dt = datetime(*entry.published_parsed[:6], tzinfo=utc)
        tw_dt = utc_dt.astimezone(timezone("Asia/Taipei"))
        return tw_dt
    except:
        return datetime.now(timezone("Asia/Taipei"))

# 清理 HTML 摘要
def clean_html(raw_html):
    soup = BeautifulSoup(raw_html, "html.parser")
    for img in soup.find_all("img"):
        img.decompose()
    for br in soup.find_all("br"):
        br.replace_with("\n")
    text = soup.get_text(separator="\n")
    return text.strip()

# 最新新聞（近 12 小時，最多 10 則）
@app.route("/smart_news")
def smart_news():
    feed = feedparser.parse(RSS_URL)
    now = datetime.utcnow()
    result = []

    for entry in feed.entries:
        published = get_published_time(entry)
        if (now - published.astimezone(utc)).total_seconds() <= 43200:  # 12 小時
            summary = entry.get("summary", "")
            cleaned = clean_html(summary)
            result.append({
                "title": entry.title,
                "translated_title": translate(entry.title),
                "summary": cleaned,
                "translated_summary": translate(cleaned),
                "link": entry.link,
                "published": published.strftime("%Y-%m-%d %H:%M:%S"),
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
            content = clean_html(entry.get("summary", ""))
            return jsonify({
                "title": entry.title,
                "translated_title": translate(entry.title),
                "summary": content,
                "content": content,
                "published": get_published_time(entry).strftime("%Y-%m-%d %H:%M:%S"),
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
        summary = clean_html(entry.get("summary", ""))
        if keyword.lower() in title.lower() or keyword.lower() in summary.lower():
            results.append({
                "title": title,
                "translated_title": translate(title),
                "summary": summary,
                "translated_summary": translate(summary),
                "link": entry.link,
                "published": get_published_time(entry).strftime("%Y-%m-%d %H:%M:%S"),
                "source": entry.get("source", {}).get("title", "Unknown")
            })
        if len(results) >= 10:
            break
    return jsonify(results)

# 錯誤提示（Render 醒著 or timeout）
@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Render backend may be sleeping. Please try again in 30 seconds."}), 500

# 主程式
if __name__ == '__main__':
    app.run(debug=True)
