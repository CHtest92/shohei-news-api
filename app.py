@app.route("/latest_news")
def latest_news():
    feed = feedparser.parse(RSS_URL)
    twelve_hours_ago = datetime.utcnow() - timedelta(hours=12)
    news_list = []

    def safe_parse_time(entry):
        try:
            if "published_parsed" in entry and entry.published_parsed:
                return datetime.fromtimestamp(time.mktime(entry.published_parsed))
        except:
            return None
        return None

    def safe_value(entry, key, default=""):
        try:
            return entry.get(key, default)
        except:
            return default

    for entry in feed.entries:
        published_dt = safe_parse_time(entry)
        if published_dt and published_dt > twelve_hours_ago:
            news_list.append({
                "id": len(news_list) + 1,
                "title": entry.title,
                "published": published_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "source": entry.get("source", {}).get("title", "未知來源"),
                "link": entry.get("link", "")
            })
        if len(news_list) >= 10:
            break

    # 補舊聞
    if len(news_list) < 10:
        for entry in feed.entries:
            if len(news_list) >= 10:
                break
            if not any(news["title"] == entry.title for news in news_list):
                published_dt = safe_parse_time(entry)
                news_list.append({
                    "id": len(news_list) + 1,
                    "title": entry.title,
                    "published": published_dt.strftime("%Y-%m-%d %H:%M:%S") if published_dt else "未知時間",
                    "source": entry.get("source", {}).get("title", "未知來源"),
                    "link": entry.get("link", "")
                })

    return jsonify(news_list)
