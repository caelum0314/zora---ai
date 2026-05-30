import datetime
import os
import json

MEMORY_DIR = os.path.dirname(os.path.abspath(__file__))

def save_conversation(user_input, ai_response, tags=None):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"chat_{timestamp}.md"
    filepath = os.path.join(MEMORY_DIR, filename)

    tags_line = ""
    if tags:
        tags_line = "Tags: " + ", ".join(tags) + "\n\n"

    content = f"""# 对话记录 - {timestamp}

{tags_line}**用户**: {user_input}

**Zora**: {ai_response}

---
*保存时间: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"已保存: {filepath}")
    return filepath


if __name__ == "__main__":
    save_conversation("你好！", "你好！我是你的终端助手 Zora！")
