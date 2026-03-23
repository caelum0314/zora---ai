import sys
import requests

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: web <search_query>")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    print(f"Searching for: {query}")
    
    # 使用DuckDuckGo API进行搜索
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