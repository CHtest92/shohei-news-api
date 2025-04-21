from flask import Flask, jsonify, request
import feedparser
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

app = Flask(__name__)

# 訂閱來源 RSS
RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/大谷翔平新聞?type=rss"

# 工具：移除 HTML 標籤並保留換行文字
def clean_html(content):
    soup = BeautifulSoup(content, "html.parser")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for p in soup.find_all("p"):
        p.insert_after("\n")
    return soup.get_text(separator="\n").strip()

# 工具：轉換 RSS 時間格式
def parse_datetime(entry):
    try:
        return datetime(*entry.published_parsed[:6])
    except:
        return datetime.utcnow()

# API：/smart_news
@app.route("/smart_news")
def smart_news():
    feed = feedparser.parse(RSS_URL)
    now = datetime.utcnow()

    # 先抓 18 小時內新聞
    primary_window = timedelta(hours=18)
    fallback_window = timedelta(hours=36)

    news = []
    for entry in feed.entries:
        pub_time = parse_datetime(entry)
        time_diff = now - pub_time
        if time_diff <= fallback_window:
            summary = clean_html(entry.get("summary", ""))
            news.append({
                "title": entry.title.strip(),
                "summary": summary[:1000],  # 控制長度
                "published": pub_time.date().isoformat(),  # 顯示網站日期
                "source": entry.get("source", {}).get("title", "來源不明"),
                "link": entry.link
            })

    # 篩選近 18 小時新聞
    recent_news = [n for n in news if (now - datetime.fromisoformat(n["published"])) <= primary_window]

    # 若不足 3 則，使用 fallback 資料補滿到 3～5 則
    result = recent_news if len(recent_news) >= 3 else news[:5]

    return jsonify(result[:10])

# 測試 API 可用性
@app.route("/")
def index():
    return "Shohei News API is running."

if __name__ == "__main__":
    app.run(debug=True)
