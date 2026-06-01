"""安全的 Git 操作工具 —— 提供 status、diff、log、branch 等只读操作，不执行任何破坏性命令。"""
import subprocess
import sys


def run(cmd: str) -> str:
    """执行 shell 命令并安全返回输出，带 30 秒超时保护。"""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return r.stdout or r.stderr or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: command timed out"
    except Exception as e:
        return f"Error: {e}"


def git_status() -> str:
    return run("git status --short")


def git_diff(staged: bool = False) -> str:
    """显示未暂存或已暂存的变更，超过 200 行自动截断。"""
    cmd = "git diff"
    if staged:
        cmd += " --staged"
    output = run(cmd)
    lines = output.split("\n")
    if len(lines) > 200:
        return "\n".join(lines[:200]) + f"\n\n... (truncated, {len(lines)} total lines)"
    return output


def git_log(n: int = 10) -> str:
    return run(f'git log --oneline -{n}')


def git_branch() -> str:
    return run("git branch --list")


def git_show_head() -> str:
    return run("git show --stat HEAD")


if __name__ == "__main__":
    # 命令行入口，根据第一个参数分发到对应操作
    if len(sys.argv) < 2:
        print("Usage: python skill/git_ops.py <operation> [args]")
        print("Operations:")
        print("  status           — show working tree status")
        print("  diff             — show unstaged changes")
        print("  diff --staged    — show staged changes")
        print("  log [n]          — show last n commits (default 10)")
        print("  branch           — list branches")
        print("  head             — show HEAD commit details")
        sys.exit(1)

    op = sys.argv[1]

    if op == "status":
        print(git_status())
    elif op == "diff":
        staged = "--staged" in sys.argv
        print(git_diff(staged=staged))
    elif op == "log":
        n = 10
        if len(sys.argv) > 2:
            try:
                n = int(sys.argv[2])
            except ValueError:
                pass
        print(git_log(n))
    elif op == "branch":
        print(git_branch())
    elif op == "head":
        print(git_show_head())
    else:
        print(f"Unknown operation: {op}")
        print("Available: status, diff, log, branch, head")
