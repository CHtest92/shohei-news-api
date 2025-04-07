from flask import Flask, request, jsonify
import feedparser
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
from bs4 import BeautifulSoup

app = Flask(__name__)

# RSS 來源
RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/%E5%A4%A7%E8%B0%B7%E7%BF%94%E5%B9%B3%E6%96%B0%E8%81%9E?type=rss"

# 翻譯工具
translator = GoogleTranslator(source='auto', target='zh-tw')

def translate(text):
    try:
        return translator.translate(text)
    except:
        return text

def clean_html_summary(summary):
    soup = BeautifulSoup(summary, "html.parser")
    # 去除圖片
    for img in soup.find_all("img"):
        img.decompose()
    # 將 <br> 轉為換行
    for br in soup.find_all("br"):
        br.replace_with("\n")
    # 將 <p> 轉換為段落文字加換行
    for p in soup.find_all("p"):
        p.insert_after("\n")
    return soup.get_text(separator=' ').strip()

# 取得網站顯示的發布日期（YYYY-MM-DD）
def get_display_date(entry):
    try:
        published = entry.published_parsed
        dt = datetime(*published[:6])
        return dt.strftime("%Y-%m-%d")
    except:
        return ""

# 近12小時新聞（最多10則）
@app.route("/smart_news")
def smart_news():
    feed = feedparser.parse(RSS_URL)
    now = datetime.utcnow()
    results = []

    for entry in feed.entries:
        published_dt = datetime(*entry.published_parsed[:6])
        if (now - published_dt).total_seconds() <= 43200:
            raw_summary = entry.get("summary", "")
            clean_summary = clean_html_summary(raw_summary)
            results.append({
                "title": entry.title,
                "translated_title": translate(entry.title),
                "summary": clean_summary,
                "translated_summary": translate(clean_summary),
                "link": entry.link,
                "published": get_display_date(entry),
                "source": entry.get("source", {}).get("title", "Unknown")
            })
        if len(results) >= 10:
            break

    return jsonify(results)

@app.route("/get_news_by_link")
def get_news_by_link():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    feed = feedparser.parse(RSS_URL)
    for entry in feed.entries:
        if entry.link == url:
            raw_summary = entry.get("summary", "")
            clean_summary = clean_html_summary(raw_summary)
            return jsonify({
                "title": entry.title,
                "translated_title": translate(entry.title),
                "summary": clean_summary,
                "content": clean_summary,
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
    now = datetime.utcnow()
    results = []

    for entry in feed.entries:
        published_dt = datetime(*entry.published_parsed[:6])
        if (now - published_dt).total_seconds() > 43200:
            continue

        title = entry.title
        raw_summary = entry.get("summary", "")
        clean_summary = clean_html_summary(raw_summary)

        if keyword.lower() in title.lower() or keyword.lower() in raw_summary.lower():
            results.append({
                "title": title,
                "translated_title": translate(title),
                "summary": clean_summary,
                "translated_summary": translate(clean_summary),
                "link": entry.link,
                "published": get_display_date(entry),
                "source": entry.get("source", {}).get("title", "Unknown")
            })
        if len(results) >= 10:
            break

    return jsonify(results)

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "伺服器可能正在喚醒中，請稍候幾秒後再試。"}), 500

if __name__ == '__main__':
    app.run(debug=True)
