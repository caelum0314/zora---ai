"""安全的 Git 操作工具 —— 提供 status、diff、log、branch 等只读操作，不执行任何破坏性命令。"""
# 导入 subprocess 模块，用于执行外部 shell 命令
import subprocess
# 导入 sys 模块，用于命令行参数解析和程序退出
import sys


# 定义 run 函数：安全执行 shell 命令并返回输出
def run(cmd: str) -> str:
    """执行 shell 命令并安全返回输出，带 30 秒超时保护。"""
    try:
        # 执行 shell 命令，捕获标准输出和标准错误，文本模式，30 秒超时
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        # 优先返回标准输出，若为空则返回标准错误，否则返回占位文本
        return r.stdout or r.stderr or "(no output)"
    # 捕获超时异常
    except subprocess.TimeoutExpired:
        # 返回超时错误信息
        return "Error: command timed out"
    # 捕获其他所有异常
    except Exception as e:
        # 返回异常信息
        return f"Error: {e}"


# 定义 git_status 函数：查看工作区状态
def git_status() -> str:
    # 执行 git status --short 命令，返回简短格式的状态
    return run("git status --short")


# 定义 git_diff 函数：查看差异
def git_diff(staged: bool = False) -> str:
    """显示未暂存或已暂存的变更，超过 200 行自动截断。"""
    # 基础命令：git diff
    cmd = "git diff"
    # 如果需要查看已暂存的变更，追加 --staged 参数
    if staged:
        cmd += " --staged"
    # 执行命令获取输出
    output = run(cmd)
    # 将输出按换行符拆分为行列表
    lines = output.split("\n")
    # 超过 200 行时截断输出
    if len(lines) > 200:
        # 返回前 200 行并附加截断提示
        return "\n".join(lines[:200]) + f"\n\n... (truncated, {len(lines)} total lines)"
    # 未超过 200 行，返回完整输出
    return output


# 定义 git_log 函数：查看最近 N 条提交记录
def git_log(n: int = 10) -> str:
    # 执行 git log --oneline 命令，显示简洁格式的提交历史
    return run(f'git log --oneline -{n}')


# 定义 git_branch 函数：列出所有分支
def git_branch() -> str:
    # 执行 git branch --list 命令，列出本地分支
    return run("git branch --list")


# 定义 git_show_head 函数：查看 HEAD 提交详情
def git_show_head() -> str:
    # 执行 git show --stat HEAD 命令，显示最近提交的文件变更统计
    return run("git show --stat HEAD")


# 判断是否作为主程序运行
if __name__ == "__main__":
    # 命令行入口，根据第一个参数分发到对应操作
    if len(sys.argv) < 2:
        # 参数不足时打印使用说明
        print("Usage: python skill/git_ops.py <operation> [args]")
        # 打印可用操作列表
        print("Operations:")
        # status 操作说明
        print("  status           — show working tree status")
        # diff 操作说明
        print("  diff             — show unstaged changes")
        # diff --staged 操作说明
        print("  diff --staged    — show staged changes")
        # log 操作说明
        print("  log [n]          — show last n commits (default 10)")
        # branch 操作说明
        print("  branch           — list branches")
        # head 操作说明
        print("  head             — show HEAD commit details")
        # 以非零状态码退出
        sys.exit(1)

    # 获取第一个参数作为操作类型
    op = sys.argv[1]

    # 根据操作类型分发到对应的处理函数
    if op == "status":
        # 调用 git_status 并打印结果
        print(git_status())
    elif op == "diff":
        # 检查参数中是否包含 --staged 标志
        staged = "--staged" in sys.argv
        # 调用 git_diff，传入 staged 参数
        print(git_diff(staged=staged))
    elif op == "log":
        # 默认显示最近 10 条提交
        n = 10
        # 如果提供了第二个参数，尝试将其作为显示条数
        if len(sys.argv) > 2:
            try:
                # 将第二个参数转换为整数
                n = int(sys.argv[2])
            # 转换失败时忽略，使用默认值
            except ValueError:
                pass
        # 调用 git_log 并打印结果
        print(git_log(n))
    elif op == "branch":
        # 调用 git_branch 并打印结果
        print(git_branch())
    elif op == "head":
        # 调用 git_show_head 并打印结果
        print(git_show_head())
    # 未知操作的处理
    else:
        # 提示未知操作
        print(f"Unknown operation: {op}")
        # 列出所有可用操作
        print("Available: status, diff, log, branch, head")
