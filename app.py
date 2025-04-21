from flask import Flask, jsonify, request
import feedparser
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

app = Flask(__name__)

# RSS 訂閱來源（大谷翔平相關）
RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/%E5%A4%A7%E8%B0%B7%E7%BF%94%E5%B9%B3%E6%96%B0%E8%81%9E?type=rss"

# 翻譯工具（僅摘要與標題用）
def translate(text):
    try:
        return GoogleTranslator(source='auto', target='zh-tw').translate(text)
    except:
        return text

# 擷取 RSS 的發佈時間（保留原始網站標示日期）
def get_entry_date(entry):
    try:
        return datetime(*entry.published_parsed[:6])
    except:
        return datetime.utcnow()

# 擷取 RSS 項目中網站標示日期（只取年月日）
def get_entry_date_str(entry):
    try:
        dt = datetime(*entry.published_parsed[:6])
        return dt.strftime("%Y-%m-%d")
    except:
        return datetime.utcnow().strftime("%Y-%m-%d")

# 清理 HTML 摘要，保留文字、換行
from bs4 import BeautifulSoup

def clean_summary(summary):
    soup = BeautifulSoup(summary, "html.parser")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    return soup.get_text().strip()

@app.route("/smart_news")
def smart_news():
    feed = feedparser.parse(RSS_URL)
    now = datetime.utcnow()
    result = []

    # 先抓近 18 小時內的新聞
    for entry in feed.entries:
        published_time = get_entry_date(entry)
        if (now - published_time).total_seconds() <= 64800:  # 18 小時
            summary = clean_summary(entry.get("summary", ""))
            result.append({
                "title": translate(entry.title),
                "summary": translate(summary),
                "published": get_entry_date_str(entry),
                "source": entry.get("source", {}).get("title", "Unknown"),
                "link": entry.link
            })
        if len(result) >= 10:
            break

    # 如果不足 3 則，擴展到 36 小時內補滿到 5 則
    if len(result) < 3:
        for entry in feed.entries:
            if entry.link in [r["link"] for r in result]:
                continue
            published_time = get_entry_date(entry)
            if (now - published_time).total_seconds() <= 129600:  # 36 小時
                summary = clean_summary(entry.get("summary", ""))
                result.append({
                    "title": translate(entry.title),
                    "summary": translate(summary),
                    "published": get_entry_date_str(entry),
                    "source": entry.get("source", {}).get("title", "Unknown"),
                    "link": entry.link
                })
            if len(result) >= 5:
                break

    return jsonify(result)

# 主程式
if __name__ == '__main__':
    app.run(debug=True)
