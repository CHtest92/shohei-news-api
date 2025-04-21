from flask import Flask, request, jsonify
import feedparser
from datetime import datetime, timedelta
import re
from bs4 import BeautifulSoup

app = Flask(__name__)

# RSS 來源
RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/大谷翔平新聞?type=rss"

# 移除 HTML 標籤，保留純文字
def clean_html(text):
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator="\n").strip()

# 判斷是否包含關鍵字（標題或內文）
def contains_keywords(title, summary):
    text = (title + " " + summary).lower()
    return "大谷翔平" in text or "shohei ohtani" in text

# 網站標示的日期（取自 published 的年月日部分）
def extract_pubdate(entry):
    try:
        return datetime(*entry.published_parsed[:6]).date().isoformat()
    except:
        return "日期未知"

@app.route("/smart_news")
def smart_news():
    feed = feedparser.parse(RSS_URL)
    now = datetime.utcnow()
    result = []

    for entry in feed.entries:
        try:
            published = datetime(*entry.published_parsed[:6])
        except:
            continue

        if (now - published).total_seconds() > 64800:  # 18 小時
            continue

        title = entry.title
        summary = clean_html(entry.get("summary", ""))
        if contains_keywords(title, summary):
            result.append({
                "translated_title": title,  # 預設已翻譯
                "translated_summary": summary,
                "published_date": extract_pubdate(entry),
                "source": entry.get("source", {}).get("title", "Unknown"),
                "link": entry.link
            })

        if len(result) >= 10:
            break

    # 若無符合新聞，也回傳 3～5 則以防畫面空白
    if not result:
        fallback = []
        for entry in feed.entries[:5]:
            fallback.append({
                "translated_title": entry.title,
                "translated_summary": clean_html(entry.get("summary", "")),
                "published_date": extract_pubdate(entry),
                "source": entry.get("source", {}).get("title", "Unknown"),
                "link": entry.link
            })
        return jsonify({
            "warning": "以下新聞可能僅部分與大谷翔平相關，請自行判斷",
            "articles": fallback
        })

    return jsonify(result)

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "後端伺服器可能尚在預熱中，請稍候再試"}), 500

if __name__ == '__main__':
    app.run(debug=True)

