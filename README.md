# Zora — 终端 AI 编程助手

**Zora** 是一个住在终端里的 AI 编程伙伴。她将大语言模型与系统命令执行能力结合，能够理解你的意图并自动调用 12 个编程技能完成任务。

## 核心特性

**智能对话**
- 流式输出 + Markdown 渲染 + 自动重试（3次）
- 上下文自动压缩（超 30 条触发 summary）
- 对话历史持久化 + MEMORY.md 长期记忆
- `export` 命令导出对话为 Markdown

**编程技能（AI 自动调用）**

| 技能 | 用途 |
|------|------|
| `code_search` | 正则搜索代码，支持 `--glob '*.py'` 文件过滤 |
| `code_scan` | 扫描类/函数/导入/TODO/FIXME（Python 深度支持） |
| `file_read` | 带行号读文件，`--start` `--lines` 分段读取 |
| `write_file` | 写入/创建文件，`--append` 追加模式 |
| `find_replace` | 跨文件批量替换，默认 dry-run 预览 |
| `edit` | 打开系统默认编辑器 |
| `git_ops` | status / diff / log / branch（全只读） |
| `diff_review` | diff 摘要 + 文件级统计 |
| `run_test` | 运行 pytest/unittest，只展示失败用例 |
| `diagnose` | 执行命令 + 失败时捕获上下文供 AI 分析 |
| `pip_ops` | pip install / uninstall / list / outdated |
| `web` | DuckDuckGo 即时搜索 |

**远程交互**
- 飞书 + Telegram 收发消息
- 支持远程执行命令和 AI 对话

**安全保护**
- 危险命令拦截（rm -rf /、git push --force 等）
- `!!` 强制执行（跳过安全检查）

## 安装

```bash
git clone https://github.com/caelum0314/zora---ai.git
cd zora---ai
pip install -r requirements.txt
```

编辑 `config.json` 填入 API 密钥：

```json
{
  "openai": {
    "api_key": "sk-your-key",
    "model": "gpt-3.5-turbo",
    "base_url": "https://api.openai.com/v1"
  },
  "context_limit": 30,
  "system_prompt": "你是 Zora..."
}
```

- `context_limit`: 对话超过此条数自动触发压缩（默认 30）
- `system_prompt`: 自定义 AI 人格和行为规则

## 使用

```bash
python main.py
```

### 内置命令

| 命令 | 作用 |
|------|------|
| `summary` | AI 压缩上下文，释放 token |
| `clear` | 清空对话历史 |
| `export` | 导出当前对话为 Markdown 文件 |
| `command <cmd>` | 手动执行 Shell 命令 |
| `!! <cmd>` | 强制执行（跳过安全拦截） |
| `feishu <msg>` | 发送飞书消息 |
| `telegram <msg>` | 发送 Telegram 消息 |
| `exit` | 退出 |

### 技能清单（12 个）

AI 在需要时自动通过 `command:` 标签调用这些技能：

**代码理解**
| 技能 | 用途 |
|------|------|
| `code_search.py` | 正则搜索代码，支持 `--glob` `--max` |
| `code_scan.py` | 扫描类/函数/导入/TODO |
| `file_read.py` | 带行号读文件，`--start` `--lines` 分段 |

**代码修改**
| 技能 | 用途 |
|------|------|
| `write_file.py` | 写入/创建文件，`--append` 追加 |
| `find_replace.py` | 跨文件批量替换，默认 dry-run |
| `edit.py` | 打开系统编辑器 |

**验证 & 诊断**
| 技能 | 用途 |
|------|------|
| `run_test.py` | 运行 pytest/unittest，只展示失败用例 |
| `diagnose.py` | 执行命令 + 失败时捕获上下文供 AI 分析 |

**Git & 审查**
| 技能 | 用途 |
|------|------|
| `git_ops.py` | status / diff / log / branch |
| `diff_review.py` | diff 摘要 + 文件级统计 |

**工具**
| 技能 | 用途 |
|------|------|
| `pip_ops.py` | install / uninstall / list / outdated |
| `web.py` | DuckDuckGo 搜索 |

### 示例

**代码搜索 + 分析 + 修改：**
```
>> 帮我把所有 get_context 重命名为 load_context

[AI 自动执行]
  command python skill/code_search.py 'get_context' --glob '*.py'
  Found 3 matches in 2 files...

  command python skill/find_replace.py 'get_context' 'load_context' --glob '*.py'
  [DRY RUN] Found 3 occurrence(s) in 2 file(s):
    2  lib/database.py
    1  lib/core.py
  Re-run with --execute to apply changes.

>> 确认执行

  command python skill/find_replace.py 'get_context' 'load_context' --glob '*.py' --execute
  [EXECUTING] Changes applied to 2 file(s).

  command python skill/run_test.py
  [pytest] All tests passed!
```

**错误诊断 + 修复：**
```
>> 我运行报错了帮我看看

  command python skill/diagnose.py 'python main.py'
  Command FAILED (exit code 1)
  [stderr]
  ModuleNotFoundError: No module named 'requests'
  [Diagnosis context]
  Final error: ModuleNotFoundError: No module named 'requests'

>> command python skill/pip_ops.py install requests
  Installing: requests
  Successfully installed requests-2.32.0
```

**代码结构分析：**
```
>> 分析一下这个项目的代码结构

  command python skill/code_scan.py --glob '*.py'
  [Scanning] 15 files...

  lib/core.py:
    Classes: Core
    Imports: json, os, openai, rich
    Functions: get_chat_response, summarize_context, execute_command

  lib/database.py:
    Classes: Database
    Functions: add_message, get_context, clear_context
```

**Git 审查：**
```
>> 看一下我改了啥

  command python skill/diff_review.py summary
  Unstaged changes:
    main.py   | 15 +++++++++------
    config.json | 2 +-
  2 files changed, 10 insertions(+), 7 deletions(-)
```

**飞书/Telegram 远程控制：**
```
（在飞书群或 Telegram 发送）
  command: python skill/git_ops.py status
  ai: 解释一下这个项目的架构

（Zora 自动执行并回复结果）
```

## 架构

```
用户输入 → main.py
              │
              ├─ 内置命令? → summary / clear / export / exit
              ├─ command?   → terminal.py → subprocess
              ├─ feishu/tg? → integration/ 发送消息
              │
              └─ AI 对话 → core.py
                              │
                              ├─ discover_skills()  扫描 skill/ 目录
                              ├─ _auto_trim()       context > N 自动压缩
                              ├─ OpenAI API (stream=True, 3次重试)
                              │
                              ├─ 读 context ← database.py (context.json)
                              ├─ 读 memory  ← home/MEMORY.md
                              │
                              └─ 回复含 command: 标签?
                                  └─ terminal.py
                                      ├─ is_dangerous()  安全检查
                                      └─ execute()       执行并返回
```

| 模块 | 文件 | 核心职责 |
|------|------|----------|
| 入口 | `main.py` | 交互循环、命令路由、消息轮询、`!!` 强制执行 |
| AI 核心 | `lib/core.py` | 流式 API 调用、自动重试、上下文自动修剪、技能自动发现 |
| 持久化 | `lib/database.py` | 对话历史 CRUD、长期记忆、Markdown 导出 |
| 命令执行 | `lib/terminal.py` | 安全拦截 + subprocess 执行 + 超时保护 |
| 技能 | `skill/*.py` | 12 个独立脚本，AI 按需调用 |
| 飞书 | `integration/feishu.py` | 飞书消息收发 |
| Telegram | `integration/telegram.py` | Telegram Bot |

## 添加自定义技能

1. 在 `skill/` 目录创建 `.py` 文件
2. 实现 `--help` 输出（Zora 启动时自动扫描并注入 system prompt）
3. 通过 `sys.argv` 接收参数，`print()` 输出结果
4. 无需修改任何其他代码

```python
# skill/weather.py
import sys
if __name__ == "__main__":
    city = sys.argv[1] if len(sys.argv) > 1 else "Beijing"
    print(f"{city}: 22C")
```

## 依赖

```
openai              # OpenAI API 客户端
rich                # 终端美化 + Markdown 渲染
python-dotenv       # 环境变量
requests            # HTTP
python-telegram-bot # Telegram Bot
lark-oapi           # 飞书 SDK
pyreadline3         # 行编辑增强 (Windows)
```

## 安全

- `terminal.py` 内置危险命令黑名单（`rm -rf /`、`git push --force`、`shutdown` 等）
- 拦截时提示用户用 `command !! <cmd>` 强制执行
- `execute_safe()` 方法支持 `shell=False` 列表模式传参
- 所有 Git 操作只读（`git_ops.py` / `diff_review.py`）

## 许可证

GPL-3.0

---

**Zora — 让 AI 住在终端里，做你的编程搭档。**
