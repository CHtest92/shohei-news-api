from flask import Flask, jsonify
import feedparser
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

app = Flask(__name__)

# 訂閱來源 RSS
RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/大谷翔平新聞?type=rss"

# 工具：移除 HTML 標籤，保留段落與換行
def clean_html(content):
    soup = BeautifulSoup(content, "html.parser")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for p in soup.find_all("p"):
        p.insert_after("\n")
    return soup.get_text(separator="\n").strip()

# 工具：取得時間（若解析錯誤就使用 UTC 現在時間）
def parse_datetime(entry):
    try:
        return datetime(*entry.published_parsed[:6])
    except:
        return datetime.utcnow()

# 主功能：取得新聞清單
@app.route("/smart_news")
def smart_news():
    feed = feedparser.parse(RSS_URL)
    now = datetime.utcnow()

    # 設定時間範圍
    primary_window = timedelta(hours=18)
    fallback_window = timedelta(hours=36)

    all_news = []
    for entry in feed.entries:
        pub_time = parse_datetime(entry)
        time_diff = now - pub_time
        if time_diff <= fallback_window:
            summary = clean_html(entry.get("summary", ""))
            all_news.append({
                "title": entry.get("title", "").strip(),
                "summary": summary[:1000],
                "published": pub_time.strftime("%Y-%m-%d"),
                "source": entry.get("source", {}).get("title", "來源不明"),
                "link": entry.get("link", "")
            })

    # 先過濾近 18 小時的新聞
    recent_news = [n for n in all_news if (now - parse_datetime({"published_parsed": datetime.strptime(n["published"], "%Y-%m-%d").timetuple()})) <= primary_window]

    # 若不足 3 則 ➜ fallback 模式補到最多 5 則
    result = recent_news if len(recent_news) >= 3 else all_news[:5]

    return jsonify(result[:10])

# 根目錄測試訊息
@app.route("/")
def index():
    return "Shohei News API is running."

if __name__ == "__main__":
    app.run(debug=True)
