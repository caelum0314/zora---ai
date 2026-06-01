"""网页搜索工具 —— 通过 DuckDuckGo 免费 API 执行关键词搜索，返回摘要及相关主题。"""
import sys
import requests

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: web <search_query>")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    print(f"Searching for: {query}")
    
    # 使用 DuckDuckGo API 进行搜索，禁止 HTML 和重定向
    url = "https://api.duckduckgo.com/"
    params = {
        "q": query,
        "format": "json",
        "no_html": "1",
        "no_redirect": "1"
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    print("\nSearch Results:")
    print("================")
    
    if data.get("Abstract"):
        print(f"Abstract: {data['Abstract']}")
        print(f"Abstract URL: {data['AbstractURL']}")
    
    if data.get("RelatedTopics"):
        print("\nRelated Topics:")
        for topic in data['RelatedTopics'][:5]:  # 只显示前5个结果
            if 'Text' in topic:
                print(f"- {topic['Text']}")
                if 'FirstURL' in topic:
                    print(f"  URL: {topic['FirstURL']}")
    
    print("\nSearch completed.")