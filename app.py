from flask import Flask, request, jsonify
import feedparser
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# Inoreader RSS 來源
RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/%E5%A4%A7%E8%B0%B7%E7%BF%94%E5%B9%B3%E6%96%B0%E8%81%9E?type=rss"

# 假翻譯（可接 GPT API）
def translate_title(title):
    return title.replace("　", " ").replace("“", "\"").replace("”", "\"")

# 最新 10 則新聞清單
@app.route("/list_news_with_link")
def list_news_with_link():
    feed = feedparser.parse(RSS_URL)
    news_list = []
    for entry in feed.entries[:10]:
        news_list.append({
            "title": entry.title,
            "translated_title": translate_title(entry.title),
            "link": entry.link,
            "published": entry.published,
            "source": entry.get("source", {}).get("title", "Unknown")
        })
    return jsonify(news_list)

# 根據網址取得新聞內容（RSS 內 content 或 description）
@app.route("/get_news_by_link")
def get_news_by_link():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    feed = feedparser.parse(RSS_URL)
    for entry in feed.entries:
        if entry.link == url:
            content = getattr(entry, "content", [{"value": entry.get("description", "")}])[0]["value"]
            return jsonify({
                "title": entry.title,
                "translated_title": translate_title(entry.title),
                "content": content,
                "published": entry.published,
                "source": entry.get("source", {}).get("title", "Unknown"),
                "link": entry.link
            })
    return jsonify({"error": "Article not found"}), 404

# 搜尋新聞（關鍵字）
@app.route("/search_news")
def search_news():
    keyword = request.args.get("keyword", "")
    if not keyword:
        return jsonify({"error": "Missing keyword"}), 400

    feed = feedparser.parse(RSS_URL)
    results = []
    for entry in feed.entries:
        if keyword.lower() in entry.title.lower() or keyword.lower() in entry.description.lower():
            results.append({
                "title": entry.title,
                "translated_title": translate_title(entry.title),
                "link": entry.link,
                "published": entry.published,
                "source": entry.get("source", {}).get("title", "Unknown")
            })
        if len(results) >= 10:
            break
    return jsonify(results)

# 近 12 小時新聞（補滿最多 10 則）
@app.route("/smart_news")
def smart_news():
    feed = feedparser.parse(RSS_URL)
    news_list = []
    now = datetime.utcnow()
    for entry in feed.entries:
        try:
            published = datetime(*entry.published_parsed[:6])
            if now - published <= timedelta(hours=12):
                news_list.append({
                    "title": entry.title,
                    "translated_title": translate_title(entry.title),
                    "link": entry.link,
                    "published": entry.published,
                    "source": entry.get("source", {}).get("title", "Unknown")
                })
        except Exception:
            continue
    for entry in feed.entries:
        if len(news_list) >= 10:
            break
        if not any(item["link"] == entry.link for item in news_list):
            news_list.append({
                "title": entry.title,
                "translated_title": translate_title(entry.title),
                "link": entry.link,
                "published": entry.published,
                "source": entry.get("source", {}).get("title", "Unknown")
            })
    return jsonify(news_list)

# 近 12 小時新聞（不補滿）
@app.route("/recent_news")
def recent_news():
    feed = feedparser.parse(RSS_URL)
    recent_list = []
    now = datetime.utcnow()
    for entry in feed.entries:
        try:
            published = datetime(*entry.published_parsed[:6])
            if now - published <= timedelta(hours=12):
                recent_list.append({
                    "title": entry.title,
                    "translated_title": translate_title(entry.title),
                    "link": entry.link,
                    "published": entry.published,
                    "source": entry.get("source", {}).get("title", "Unknown")
                })
        except Exception:
            continue
        if len(recent_list) >= 10:
            break
    return jsonify(recent_list)

# 爬取原始網站全文內容（加上 User-Agent 模擬）
@app.route("/get_full_article")
def get_full_article():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        article = soup.find("div", class_="article-body")
        if not article:
            return jsonify({"error": "Article content not found"}), 404

        for tag in article.find_all(["img", "video", "iframe"]):
            tag.decompose()

        text = article.get_text(separator="\n", strip=True)
        return jsonify({"content": text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 啟動應用（開發模式）
if __name__ == '__main__':
    app.run(debug=True)
