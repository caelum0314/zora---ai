"""安全的 pip 操作工具 —— 支持 install、uninstall、list、outdated、search 等包管理操作，通过子进程调用 pip 模块。"""
import sys
import subprocess
import os


def run_pip(args: list, timeout: int = 120) -> dict:
    """使用当前 Python 解释器调用 pip 模块执行命令，返回结构化结果字典。"""
    cmd = [sys.executable, "-m", "pip"] + args
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {"success": r.returncode == 0, "output": r.stdout, "error": r.stderr,
                "returncode": r.returncode}
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "", "error": "Timeout", "returncode": -1}
    except Exception as e:
        return {"success": False, "output": "", "error": str(e), "returncode": -1}


if __name__ == "__main__":
    # 命令行入口，根据操作码分发
    if len(sys.argv) < 2:
        print("Usage: python skill/pip_ops.py <operation> [args]")
        print()
        print("Operations:")
        print("  list                     — list installed packages (top-level)")
        print("  install <pkg> [pkg ...]  — install package(s)")
        print("  uninstall <pkg>          — uninstall a package")
        print("  outdated                 — show outdated packages")
        print("  search <query>           — search PyPI")
        print("  show <pkg>               — show package details")
        print("  freeze                   — pip freeze (all packages)")
        print()
        print("Examples:")
        print("  python skill/pip_ops.py list")
        print("  python skill/pip_ops.py install requests rich")
        print("  python skill/pip_ops.py outdated")
        sys.exit(1)

    op = sys.argv[1]
    rest = sys.argv[2:]

    if op == "list":
        # 仅列出用户安装的顶层包，非依赖
        result = run_pip(["list", "--format=columns"])
        if result["success"]:
            lines = result["output"].split("\n")
            if len(lines) > 50:
                print("\n".join(lines[:50]))
                print(f"\n... ({len(lines) - 2} total packages)")
            else:
                print(result["output"])
        else:
            print(f"Error: {result['error']}")

    elif op == "install":
        if not rest:
            print("Error: specify at least one package name")
            sys.exit(1)
        print(f"Installing: {' '.join(rest)}")
        result = run_pip(["install"] + rest, timeout=180)
        print(result["output"] or result["error"])

    elif op == "uninstall":
        if not rest:
            print("Error: specify a package name")
            sys.exit(1)
        result = run_pip(["uninstall", "-y"] + rest, timeout=60)
        print(result["output"] or result["error"])

    elif op == "outdated":
        result = run_pip(["list", "--outdated", "--format=columns"], timeout=60)
        if result["success"]:
            output = result["output"]
            if not output.strip():
                print("All packages are up to date.")
            else:
                print(output)
        else:
            print(f"Error: {result['error']}")

    elif op == "search":
        if not rest:
            print("Error: specify a search query")
            sys.exit(1)
        query = " ".join(rest)
        print(f"Searching PyPI for: {query}")
        # pip search 在新版本中已被移除，改用 pip index search
        result = run_pip(["index", "search", query] if sys.version_info >= (3, 8) else ["search", query], timeout=30)
        print(result["output"] or result["error"] or "Search completed (try: pip index search <query>)")

    elif op == "show":
        if not rest:
            print("Error: specify a package name")
            sys.exit(1)
        result = run_pip(["show"] + rest, timeout=30)
        if result["success"]:
            print(result["output"])
        else:
            print(f"Package '{rest[0]}' not found or not installed.")

    elif op == "freeze":
        result = run_pip(["freeze"], timeout=30)
        if result["success"]:
            lines = result["output"].split("\n")
            if len(lines) > 100:
                print("\n".join(lines[:100]))
                print(f"\n... ({len(lines) - 1} total packages)")
            else:
                print(result["output"])

    else:
        print(f"Unknown operation: {op}")
        print("Available: list, install, uninstall, outdated, search, show, freeze")
