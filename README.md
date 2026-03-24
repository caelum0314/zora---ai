# Zora

将大语言模型与系统命令执行能力结合，让活泼的 zora 成为你终端里的贴心助手，帮你对话、执行命令、管理文件，还能连接飞书和Telegram等手机软件。

## ✨ 功能特点

- **智能对话**：基于 OpenAI API 兼容的模型，支持自定义模型和接口地址。
- **命令执行**：AI 可以通过在消息末尾添加 command: 标签调用系统 Shell，并返回执行结果。
- **上下文管理**：自动保存最近的对话历史，支持手动压缩（summary）或清空（clear）上下文，以控制 token 消耗。
- **工作目录保持**：AI 执行的命令会在当前工作目录下运行，支持 cd 命令（仅限绝对路径）。
- **记忆机制**：AI 拥有专属的 MEMORY.md 文件，可写入重要信息，实现长期记忆。
- **技能扩展**：通过配置文件可自定义可调用的外部命令列表（技能），AI 能通过 --help 查看用法。
- **美观输出**：使用 rich 库渲染彩色终端输出、Markdown 格式和错误回溯。
- **飞书集成**：支持通过命令发送消息到飞书。
- **Telegram集成**：支持通过命令发送消息到Telegram。

## 📦 安装

### 环境要求

- Python 3.8+
- 一个兼容 OpenAI API 的模型接口（如 OpenAI、Azure OpenAI、本地部署的 vLLM 等）
- 飞书开发者账号（可选，用于飞书集成）
- Telegram Bot Token（可选，用于Telegram集成）

### 安装步骤

1. 克隆仓库或下载源码：
   ```bash
   git clone https://github.com/caelum0314/zora---ai.git
   cd zora---ai
   ```
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 配置API密钥：
   编辑 `config.json` 文件，填写你的 API 密钥和其他配置信息：
   ```json
   {
     "openai": {
       "api_key": "your_openai_api_key",
       "model": "gpt-3.5-turbo",
       "base_url": "https://api.openai.com/v1"
     },
     "telegram": {
       "bot_token": "your_telegram_bot_token",
       "chat_id": "your_chat_id"
     },
     "feishu": {
       "app_id": "your_feishu_app_id",
       "app_secret": "your_feishu_app_secret",
       "chat_id": "your_feishu_chat_id"
     }
   }
   ```

## 🚀 使用方法

在项目目录下运行主程序：

```bash
python main.py
```

启动后将显示 ASCII 艺术标题和最近的历史上下文，然后进入交互模式。

### 内置命令

在输入框（>>）中可直接输入以下命令：

| 命令            | 作用                       |
| ------------- | ------------------------ |
| summary       | 压缩当前上下文，保留重要信息（调用 AI 总结） |
| clear         | 清空所有上下文历史                |
| command <命令>  | 手动执行Shell命令              |
| feishu <消息>   | 发送消息到飞书                  |
| telegram <消息> | 发送消息到Telegram            |
| exit          | 退出程序                     |

### 示例

1. **智能对话**：
   ```
   >> 你好，pomi
   你好！我是你的AI助手pomi，有什么可以帮你的吗？
   ```
2. **执行命令**：
   ```
   >> command ls -la
   Command executed successfully:
   total 40
   drwxr-xr-x  7 user  staff   224 Mar 23 19:47 .
   drwxr-xr-x  5 user  staff   160 Mar 23 19:45 ..
   -rw-r--r--  1 user  staff   200 Mar 23 19:47 config.json
   -rw-r--r--  1 user  staff   150 Mar 23 19:47 requirements.txt
   drwxr-xr-x  3 user  staff    96 Mar 23 19:47 lib
   drwxr-xr-x  3 user  staff    96 Mar 23 19:47 skill
   drwxr-xr-x  3 user  staff    96 Mar 23 19:47 home
   drwxr-xr-x  2 user  staff    64 Mar 23 19:47 database
   drwxr-xr-x  3 user  staff    96 Mar 23 19:47 integration
   ```
3. **发送消息到飞书**：
   ```
   >> feishu 测试消息
   Message sent successfully
   ```
4. **发送消息到Telegram**：
   ```
   >> telegram 测试消息
   Message sent successfully
   ```

## 📁 项目结构

```
.
├── config.json          # 配置文件
├── requirements.txt     # 依赖库
├── main.py              # 主程序
├── lib/                 # 核心库
│   ├── database.py      # 上下文和记忆管理
│   ├── terminal.py      # 命令执行
│   └── core.py          # 核心功能
├── skill/               # 技能扩展
│   ├── edit.py          # 文件编辑
│   └── web.py           # web搜索
├── home/                # 记忆和日志
│   ├── MEMORY.md        # 长期记忆
│   └── diary/           # 日志目录
├── database/            # 上下文存储
│   └── context.json     # 上下文历史
└── integration/         # 集成模块
    ├── feishu.py        # 飞书集成
    └── telegram.py      # Telegram集成
```

## 🛠️ 依赖库

- openai —— 调用大语言模型 API
- rich —— 终端美化、Markdown 渲染、错误回溯
- python-dotenv —— 环境变量管理
- requests —— HTTP 请求
- python-telegram-bot —— Telegram 机器人
- feishu-sdk-python —— 飞书 SDK
- pyreadline3 —— 增强输入行编辑功能

## ⚠️ 已知问题

- 命令执行使用了 subprocess 并加载了 Shell 配置文件，请确保配置文件中没有交互式提示或长期阻塞的命令。
- 飞书和Telegram集成需要正确配置 API 密钥和相关参数，否则可能无法正常工作。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request。请确保代码风格清晰，并更新相应文档。

## 📄 许可证

本项目采用 GPL-3.0 许可证。详见 LICENSE 文件。

Zora —— 让 AI 住在你的终端里，成为你的贴心小助手！🎉
