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

# 解析摘要內容，清除 img 和多餘 HTML，但保留換行與段落
def clean_summary(html):
    soup = BeautifulSoup(html, 'html.parser')
    for img in soup.find_all('img'):
        img.decompose()
    text = soup.get_text(separator="\n")
    return text.strip()

# 時間格式處理（直接用 RSS 提供的日期為主，不轉換）
def get_published_date(entry):
    try:
        pub_date = entry.published_parsed
        return datetime(*pub_date[:6]) if pub_date else None
    except:
        return None

def get_website_date_str(entry):
    try:
        pub_date = entry.published_parsed
        return datetime(*pub_date[:3]).date().isoformat()
    except:
        return "Unknown"

# 取得近 12 小時內新聞（最多 10 則）
@app.route("/smart_news")
def smart_news():
    feed = feedparser.parse(RSS_URL)
    now = datetime.utcnow()
    result = []

    for entry in feed.entries:
        published_dt = get_published_date(entry)
        if published_dt is None:
            continue

        # 關鍵修正：轉為 offset-naive datetime 再比較
        if (now - published_dt.replace(tzinfo=None)).total_seconds() <= 43200:
            summary_html = entry.get("summary", "")
            cleaned_summary = clean_summary(summary_html)

            result.append({
                "title": entry.title,
                "translated_title": translate(entry.title),
                "summary": cleaned_summary,
                "translated_summary": translate(cleaned_summary),
                "link": entry.link,
                "published": get_website_date_str(entry),  # 顯示網站標示日期
                "source": entry.get("source", {}).get("title", "Unknown")
            })

        if len(result) >= 10:
            break

    return jsonify(result)

# 根據新聞連結取得該則摘要（for GPT 貼文使用）
@app.route("/get_news_by_link")
def get_news_by_link():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    feed = feedparser.parse(RSS_URL)
    for entry in feed.entries:
        if entry.link == url:
            summary_html = entry.get("summary", "")
            cleaned_summary = clean_summary(summary_html)

            return jsonify({
                "title": entry.title,
                "translated_title": translate(entry.title),
                "summary": cleaned_summary,
                "content": cleaned_summary,
                "published": get_website_date_str(entry),
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
        summary_html = entry.get("summary", "")
        cleaned_summary = clean_summary(summary_html)

        if keyword.lower() in title.lower() or keyword.lower() in cleaned_summary.lower():
            results.append({
                "title": title,
                "translated_title": translate(title),
                "summary": cleaned_summary,
                "translated_summary": translate(cleaned_summary),
                "link": entry.link,
                "published": get_website_date_str(entry),
                "source": entry.get("source", {}).get("title", "Unknown")
            })

        if len(results) >= 10:
            break

    return jsonify(results)

# 後端錯誤處理
@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Server internal error. Backend may be sleeping or misconfigured."}), 500

# 執行主程式
if __name__ == '__main__':
    app.run(debug=True)
