from flask import Flask, request, jsonify
import feedparser
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

app = Flask(__name__)

# Inoreader RSS 來源
RSS_URL = "https://www.inoreader.com/stream/user/1003787482/tag/%E5%A4%A7%E8%B0%B7%E7%BF%94%E5%B9%B3%E6%96%B0%E8%81%9E?type=rss"

# 假翻譯（可接 GPT API）
def translate_title(title):
    return title.replace("　", " ").replace("“", "\"").replace("”", "\"")

# 網域專屬 selector 配對（可擴充）
DOMAIN_SELECTOR_MAP = {
    "full-count.jp": "artL-detail",
    "sponichi.co.jp": "article-body"
    # 可繼續擴充其他網站
}

# 根據網址決定主文選擇器
def get_domain_selector(url):
    hostname = urlparse(url).hostname or ""
    for domain, class_name in DOMAIN_SELECTOR_MAP.items():
        if domain in hostname:
            return {"name": "div", "class_": class_name}
    return None

# RSS 最新新聞清單（10 則）
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

# 根據連結取得原文全文（自動判斷網站主文位置）
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
        soup = BeautifulSoup(response.content, "html.parser")

        selector = get_domain_selector(url)
        if selector:
            article = soup.find(selector["name"], class_=selector["class_"])
        else:
            # fallback selectors
            candidates = [
                {"name": "div", "class_": "art_box"},
                {"name": "div", "class_": "article-body"},
                {"name": "div", "class_": "post-content"},
                {"name": "div", "class_": "entry-content"},
                {"name": "div", "class_": "l-article"},
                {"name": "article"}
            ]
            article = None
            for c in candidates:
                article = soup.find(c["name"], class_=c.get("class_"))
                if article:
                    break

        if not article:
            return jsonify({"error": "Article content not found"}), 404

        for tag in article.find_all(["img", "video", "iframe", "script", "style"]):
            tag.decompose()

        text = article.get_text(separator="\n", strip=True)
        return jsonify({"content": text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 啟動應用（本地開發）
if __name__ == '__main__':
    app.run(debug=True)
