"""网页搜索工具 —— 通过 DuckDuckGo 免费 API 执行关键词搜索，返回摘要及相关主题。"""
# 导入 sys 模块，用于获取命令行参数和退出程序
import sys
# 导入 requests 库，用于发送 HTTP 请求
import requests

# 当脚本直接运行时执行以下代码
if __name__ == "__main__":
    # 检查是否提供了搜索关键词
    if len(sys.argv) < 2:
        # 未提供参数时打印使用说明
        print("Usage: web <search_query>")
        # 以错误码 1 退出
        sys.exit(1)
    
    # 将命令行参数用空格拼接成搜索查询字符串
    query = " ".join(sys.argv[1:])
    # 打印正在搜索的提示
    print(f"Searching for: {query}")
    
    # 使用 DuckDuckGo API 进行搜索，禁止 HTML 和重定向
    # DuckDuckGo API 的请求地址
    url = "https://api.duckduckgo.com/"
    # 构建请求参数字典
    params = {
        # 搜索关键词
        "q": query,
        # 返回 JSON 格式数据
        "format": "json",
        # 禁止在结果中包含 HTML
        "no_html": "1",
        # 禁止自动重定向
        "no_redirect": "1"
    }
    
    # 发送 GET 请求到 DuckDuckGo API，传入查询参数
    response = requests.get(url, params=params)
    # 将响应解析为 JSON 字典
    data = response.json()
    
    # 打印搜索结果标题
    print("\nSearch Results:")
    # 打印分隔线
    print("================")
    
    # 检查是否有摘要信息
    if data.get("Abstract"):
        # 打印搜索摘要文本
        print(f"Abstract: {data['Abstract']}")
        # 打印摘要来源 URL
        print(f"Abstract URL: {data['AbstractURL']}")
    
    # 检查是否有相关主题结果
    if data.get("RelatedTopics"):
        # 打印相关主题标题
        print("\nRelated Topics:")
        # 遍历前 5 个相关主题
        for topic in data['RelatedTopics'][:5]:
            # 检查该主题是否包含文本描述
            if 'Text' in topic:
                # 打印主题文本
                print(f"- {topic['Text']}")
                # 检查该主题是否包含 URL
                if 'FirstURL' in topic:
                    # 打印主题对应的 URL
                    print(f"  URL: {topic['FirstURL']}")
    
    # 打印搜索完成提示
    print("\nSearch completed.")