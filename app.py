from datetime import datetime, timedelta
import feedparser
from flask import Flask, jsonify
from pytz import utc

app = Flask(__name__)

# 訂閱的大谷翔平新聞 RSS 來源
RSS_FEEDS = [
    "https://www3.nhk.or.jp/rss/news/cat0.xml",
    "https://news.yahoo.co.jp/rss/topics/sports.xml",
    "https://full-count.jp/feed/",
    "https://rss.rssad.jp/rss/sports_baseball.xml",
    "https://feeds.bbci.co.uk/sport/baseball/rss.xml",
    "https://news.yahoo.com/rss/mlb",
]

@app.route("/smart_news", methods=["GET"])
def smart_news():
    now = datetime.utcnow().replace(tzinfo=utc)
    news_items = []
    fallback_mode = False

    def fetch_within(hours):
        cutoff = now - timedelta(hours=hours)
        items = []
        for feed_url in RSS_FEEDS:
            parsed = feedparser.parse(feed_url)
            for entry in parsed.entries:
                try:
                    published = getattr(entry, "published_parsed", None)
                    if published:
                        published_dt = datetime(*published[:6], tzinfo=utc)
                        if published_dt >= cutoff:
                            items.append({
                                "title": entry.title,
                                "summary": entry.get("summary", ""),
                                "published": published_dt.strftime("%Y-%m-%d"),
                                "source": parsed.feed.get("title", "Unknown Source"),
                                "link": entry.link,
                            })
                except Exception:
                    continue
        return items

    # 先抓 18 小時內
    news_items = fetch_within(18)

    # 若不足 3 則，抓取 36 小時內補足
    if len(news_items) < 3:
        news_items = fetch_within(36)
        fallback_mode = True

    # 限制最多顯示 10 則
    news_items = sorted(news_items, key=lambda x: x["published"], reverse=True)[:10]

    response = {"news": news_items, "fallback": fallback_mode}
    return jsonify(response)

if __name__ == "__main__":
    app.run(debug=True)
