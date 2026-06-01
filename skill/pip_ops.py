"""安全的 pip 操作工具 —— 支持 install、uninstall、list、outdated、search 等包管理操作，通过子进程调用 pip 模块。"""
# 导入 sys 模块，用于获取解释器路径和命令行参数
import sys
# 导入 subprocess 模块，用于在子进程中执行命令
import subprocess
# 导入 os 模块，用于操作系统相关功能
import os


# 定义 run_pip 函数，接收参数列表和超时时间，返回结构化结果字典
def run_pip(args: list, timeout: int = 120) -> dict:
    """使用当前 Python 解释器调用 pip 模块执行命令，返回结构化结果字典。"""
    # 构建命令：使用当前 Python 解释器以模块方式运行 pip，并拼接额外参数
    cmd = [sys.executable, "-m", "pip"] + args
    # 尝试执行子进程命令
    try:
        # 运行命令，捕获标准输出和标准错误，以文本模式返回，设置超时
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        # 返回结构化字典，包含成功标志、输出、错误和返回码
        return {"success": r.returncode == 0, "output": r.stdout, "error": r.stderr,
                "returncode": r.returncode}
    # 捕获超时异常
    except subprocess.TimeoutExpired:
        # 超时时返回失败结果，错误信息为 "Timeout"
        return {"success": False, "output": "", "error": "Timeout", "returncode": -1}
    # 捕获其他所有异常
    except Exception as e:
        # 返回失败结果，错误信息为异常的字符串表示
        return {"success": False, "output": "", "error": str(e), "returncode": -1}


# 当脚本直接运行（而非作为模块导入）时执行以下代码
if __name__ == "__main__":
    # 命令行入口，根据操作码分发
    # 检查命令行参数数量是否不足
    if len(sys.argv) < 2:
        # 打印使用说明标题
        print("Usage: python skill/pip_ops.py <operation> [args]")
        # 打印空行
        print()
        # 打印可用操作列表标题
        print("Operations:")
        # 打印 list 操作说明
        print("  list                     — list installed packages (top-level)")
        # 打印 install 操作说明
        print("  install <pkg> [pkg ...]  — install package(s)")
        # 打印 uninstall 操作说明
        print("  uninstall <pkg>          — uninstall a package")
        # 打印 outdated 操作说明
        print("  outdated                 — show outdated packages")
        # 打印 search 操作说明
        print("  search <query>           — search PyPI")
        # 打印 show 操作说明
        print("  show <pkg>               — show package details")
        # 打印 freeze 操作说明
        print("  freeze                   — pip freeze (all packages)")
        # 打印空行
        print()
        # 打印示例标题
        print("Examples:")
        # 打印 list 示例
        print("  python skill/pip_ops.py list")
        # 打印 install 示例
        print("  python skill/pip_ops.py install requests rich")
        # 打印 outdated 示例
        print("  python skill/pip_ops.py outdated")
        # 以错误码 1 退出程序
        sys.exit(1)

    # 获取第一个命令行参数作为操作码
    op = sys.argv[1]
    # 获取剩余的命令行参数
    rest = sys.argv[2:]

    # 处理 list 操作：列出已安装的包
    if op == "list":
        # 仅列出用户安装的顶层包，非依赖
        # 调用 run_pip 执行 list 命令，以列格式输出
        result = run_pip(["list", "--format=columns"])
        # 判断命令是否执行成功
        if result["success"]:
            # 将输出按换行符分割成行列表
            lines = result["output"].split("\n")
            # 如果包数量超过 50 个则截断显示
            if len(lines) > 50:
                # 只显示前 50 行
                print("\n".join(lines[:50]))
                # 打印省略提示，显示总包数（减 2 是因为列表有表头和空行）
                print(f"\n... ({len(lines) - 2} total packages)")
            else:
                # 包数量不多，直接打印全部输出
                print(result["output"])
        else:
            # 命令执行失败，打印错误信息
            print(f"Error: {result['error']}")

    # 处理 install 操作：安装包
    elif op == "install":
        # 检查是否指定了包名
        if not rest:
            # 未指定包名时提示错误并退出
            print("Error: specify at least one package name")
            sys.exit(1)
        # 打印正在安装的包名
        print(f"Installing: {' '.join(rest)}")
        # 执行 pip install 命令，超时时间设为 180 秒
        result = run_pip(["install"] + rest, timeout=180)
        # 打印输出或错误信息
        print(result["output"] or result["error"])

    # 处理 uninstall 操作：卸载包
    elif op == "uninstall":
        # 检查是否指定了包名
        if not rest:
            # 未指定包名时提示错误并退出
            print("Error: specify a package name")
            sys.exit(1)
        # 执行 pip uninstall，-y 表示自动确认卸载，超时 60 秒
        result = run_pip(["uninstall", "-y"] + rest, timeout=60)
        # 打印输出或错误信息
        print(result["output"] or result["error"])

    # 处理 outdated 操作：查看可升级的包
    elif op == "outdated":
        # 执行 pip list --outdated 命令
        result = run_pip(["list", "--outdated", "--format=columns"], timeout=60)
        # 判断命令是否执行成功
        if result["success"]:
            # 获取输出内容
            output = result["output"]
            # 检查输出是否为空
            if not output.strip():
                # 输出为空说明所有包都是最新版本
                print("All packages are up to date.")
            else:
                # 打印可升级的包列表
                print(output)
        else:
            # 命令执行失败，打印错误信息
            print(f"Error: {result['error']}")

    # 处理 search 操作：在 PyPI 中搜索包
    elif op == "search":
        # 检查是否指定了搜索关键词
        if not rest:
            # 未指定搜索词时提示错误并退出
            print("Error: specify a search query")
            sys.exit(1)
        # 将剩余参数用空格拼接成搜索查询字符串
        query = " ".join(rest)
        # 打印正在搜索的提示
        print(f"Searching PyPI for: {query}")
        # pip search 在新版本中已被移除，改用 pip index search
        # 根据 Python 版本选择不同的搜索命令
        result = run_pip(["index", "search", query] if sys.version_info >= (3, 8) else ["search", query], timeout=30)
        # 打印搜索结果或错误提示
        print(result["output"] or result["error"] or "Search completed (try: pip index search <query>)")

    # 处理 show 操作：显示包的详细信息
    elif op == "show":
        # 检查是否指定了包名
        if not rest:
            # 未指定包名时提示错误并退出
            print("Error: specify a package name")
            sys.exit(1)
        # 执行 pip show 命令，超时 30 秒
        result = run_pip(["show"] + rest, timeout=30)
        # 判断命令是否执行成功
        if result["success"]:
            # 打印包的详细信息
            print(result["output"])
        else:
            # 包未安装或未找到，打印提示
            print(f"Package '{rest[0]}' not found or not installed.")

    # 处理 freeze 操作：导出所有已安装包的精确版本
    elif op == "freeze":
        # 执行 pip freeze 命令
        result = run_pip(["freeze"], timeout=30)
        # 判断命令是否执行成功
        if result["success"]:
            # 将输出按换行符分割
            lines = result["output"].split("\n")
            # 如果包数量超过 100 行则截断显示
            if len(lines) > 100:
                # 只显示前 100 行
                print("\n".join(lines[:100]))
                # 打印省略提示
                print(f"\n... ({len(lines) - 1} total packages)")
            else:
                # 包数量不多，直接打印全部输出
                print(result["output"])

    # 处理未知操作码
    else:
        # 打印未知操作提示
        print(f"Unknown operation: {op}")
        # 打印可用操作列表
        print("Available: list, install, uninstall, outdated, search, show, freeze")
