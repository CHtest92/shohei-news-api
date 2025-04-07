from flask import Flask, request, jsonify
import feedparser
from datetime import datetime, timezone
from deep_translator import GoogleTranslator
import re

app = Flask(__name__)

# RSS 來源
RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/%E5%A4%A7%E8%B0%B7%E7%BF%94%E5%B9%B3%E6%96%B0%E8%81%9E?type=rss"

# HTML 清除工具（移除 <img> 與 <script>，保留文字）
def clean_html(text):
    text = re.sub(r'<img[^>]*>', '', text)  # 移除圖片
    text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.DOTALL)
    text = text.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
    text = re.sub(r'</?(p|div)[^>]*>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)  # 移除其餘 HTML 標籤
    return text.strip()

# 翻譯工具
def translate(text):
    try:
        return GoogleTranslator(source='auto', target='zh-tw').translate(text)
    except:
        return text

# 取得精確發布時間（包含時區）
def get_published_time(entry):
    try:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    except:
        return datetime.now(timezone.utc)

# 取得網站標示發布「日期」
def get_display_date(entry):
    try:
        return entry.published.split(',')[-1].strip().split(' ')[0]
    except:
        return ""

# 自動喚醒頁面
@app.route("/")
def wakeup():
    return "Shohei News API is awake."

# 最新新聞
@app.route("/smart_news")
def smart_news():
    feed = feedparser.parse(RSS_URL)
    now = datetime.now(timezone.utc)
    result = []

    for entry in feed.entries:
        published_dt = get_published_time(entry)
        if (now - published_dt).total_seconds() <= 43200:  # 12 小時
            raw_summary = entry.get("summary", "")
            clean_summary = clean_html(raw_summary)
            result.append({
                "title": entry.title,
                "translated_title": translate(entry.title),
                "summary": clean_summary,
                "translated_summary": translate(clean_summary),
                "link": entry.link,
                "published": get_display_date(entry),  # 網站顯示日期
                "source": entry.get("source", {}).get("title", "Unknown")
            })
        if len(result) >= 10:
            break

    return jsonify(result)

# 根據網址取得單篇新聞內容
@app.route("/get_news_by_link")
def get_news_by_link():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    feed = feedparser.parse(RSS_URL)
    for entry in feed.entries:
        if entry.link == url:
            raw_summary = entry.get("summary", "")
            clean_summary = clean_html(raw_summary)
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

# 搜尋新聞
@app.route("/search_news")
def search_news():
    keyword = request.args.get("keyword", "")
    if not keyword:
        return jsonify({"error": "Missing keyword"}), 400

    feed = feedparser.parse(RSS_URL)
    now = datetime.now(timezone.utc)
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
                "published": get_display_date(entry),
                "source": entry.get("source", {}).get("title", "Unknown")
            })
        if len(results) >= 10:
            break

    return jsonify(results)

# 全域錯誤處理
@app.errorhandler(500)
def handle_500(e):
    return jsonify({"error": "伺服器可能尚未喚醒，請稍候 30 秒再試一次"}), 500

if __name__ == '__main__':
    app.run(debug=True)
