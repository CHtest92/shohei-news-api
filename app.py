from flask import Flask, request, jsonify
import feedparser
from datetime import datetime, timedelta, timezone
from deep_translator import GoogleTranslator
from bs4 import BeautifulSoup

app = Flask(__name__)

RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/%E5%A4%A7%E8%B0%B7%E7%BF%94%E5%B9%B3%E6%96%B0%E8%81%9E?type=rss"

def translate(text):
    try:
        return GoogleTranslator(source='auto', target='zh-tw').translate(text)
    except:
        return text

def clean_html(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["img", "script", "style"]):
        tag.decompose()
    text = soup.get_text(separator="\n").strip()
    return text

def get_published_date(entry):
    try:
        # 直接讀取 RFC822 格式時間為 UTC 並轉換為 aware datetime
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    except:
        return datetime.utcnow().replace(tzinfo=timezone.utc)

@app.route("/smart_news")
def smart_news():
    feed = feedparser.parse(RSS_URL)
    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    result = []

    for entry in feed.entries:
        published_dt = get_published_date(entry)
        if (now - published_dt).total_seconds() <= 43200:  # 12 小時
            summary_raw = entry.get("summary", "")
            summary_clean = clean_html(summary_raw)
            result.append({
                "title": entry.title,
                "translated_title": translate(entry.title),
                "summary": summary_clean,
                "translated_summary": translate(summary_clean),
                "link": entry.link,
                "published": published_dt.date().isoformat(),  # 只保留日期，對應網站顯示
                "source": entry.get("source", {}).get("title", "Unknown")
            })
        if len(result) >= 10:
            break

    return jsonify(result)

# 其他 endpoint 可照舊保留...

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "後端伺服器暫時無法連線，請稍後再試"}), 500

if __name__ == '__main__':
    app.run(debug=True)
