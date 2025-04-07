{
  "openapi": "3.1.0",
  "info": {
    "title": "Shohei News API",
    "version": "1.0.0"
  },
  "servers": [{ "url": "https://shohei-news-api.onrender.com" }],
  "paths": {
    "/smart_news": {
      "get": {
        "summary": "取得近 12 小時內新聞（最多 10 則）",
        "operationId": "smartNews",
        "responses": {
          "200": {
            "description": "新聞清單",
            "content": {
              "application/json": {
                "schema": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "title": { "type": "string" },
                      "translated_title": { "type": "string" },
                      "summary": { "type": "string" },
                      "translated_summary": { "type": "string" },
                      "link": { "type": "string" },
                      "published": { "type": "string" },
                      "source": { "type": "string" }
                    },
                    "required": [
                      "title", "translated_title", "translated_summary", "link", "published"
                    ]
                  }
                }
              }
            }
          }
        }
      }
    },
    "/get_news_by_link": {
      "get": {
        "summary": "根據新聞網址取得摘要內容，供 GPT 翻譯與改寫使用",
        "operationId": "getNewsByLink",
        "parameters": [
          {
            "name": "url",
            "in": "query",
            "required": true,
            "schema": { "type": "string" }
          }
        ],
        "responses": {
          "200": {
            "description": "新聞單則內容",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "title": { "type": "string" },
                    "translated_title": { "type": "string" },
                    "summary": { "type": "string" },
                    "content": { "type": "string" },
                    "published": { "type": "string" },
                    "source": { "type": "string" },
                    "link": { "type": "string" }
                  }
                }
              }
            }
          }
        }
      }
    },
    "/search_news": {
      "get": {
        "summary": "搜尋關鍵字新聞",
        "operationId": "searchNews",
        "parameters": [
          {
            "name": "keyword",
            "in": "query",
            "required": true,
            "schema": { "type": "string" }
          }
        ],
        "responses": {
          "200": {
            "description": "搜尋新聞列表",
            "content": {
              "application/json": {
                "schema": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "title": { "type": "string" },
                      "translated_title": { "type": "string" },
                      "summary": { "type": "string" },
                      "translated_summary": { "type": "string" },
                      "link": { "type": "string" },
                      "published": { "type": "string" },
                      "source": { "type": "string" }
                    },
                    "required": [
                      "title", "translated_title", "translated_summary", "link", "published"
                    ]
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
