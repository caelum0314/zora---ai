"""显示 git diff 摘要 — 变更文件、增删行数、关键上下文。"""
# 导入 sys 模块，用于命令行参数和退出
import sys
# 导入 subprocess 模块，用于执行 git 命令
import subprocess
# 导入 os 模块，用于文件路径和扩展名操作
import os
# 导入 re 模块（本文件中未直接使用，仅作为便利导入）
import re


# 定义 run 函数：执行 git 命令并返回输出，出错时返回错误信息
def run(cmd: str) -> str:
    """执行 git 命令并返回输出，出错时返回错误信息。"""
    try:
        # 使用 subprocess.run 执行命令，捕获输出，超时时间 30 秒
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        # 返回标准输出，若为空则返回标准错误，都为空则返回空字符串
        return r.stdout or r.stderr or ""
    # 捕获所有异常
    except Exception as e:
        # 返回格式化的错误信息
        return f"Error: {e}"


# 定义 diff_summary 函数：展示所有变更的简洁摘要，包括文件统计和每文件增删行数
def diff_summary() -> str:
    """展示所有变更的简洁摘要，包括文件统计和每文件增删行数。"""
    # 输出行的列表
    out = []

    # 获取未暂存和已暂存变更的统计信息
    # 获取未暂存的变更统计
    stat = run("git diff --stat")
    # 获取已暂存的变更统计
    stat_staged = run("git diff --staged --stat")

    # 如果有未暂存变更，加入输出
    if stat.strip():
        out.append("Unstaged changes:")
        out.append(stat)
        out.append("")
    # 如果有已暂存变更，加入输出
    if stat_staged.strip():
        out.append("Staged changes:")
        out.append(stat_staged)
        out.append("")

    # 如果既无未暂存也无已暂存变更，返回干净状态提示
    if not stat.strip() and not stat_staged.strip():
        return "No changes (working tree clean)."

    # 按文件列出增删行数明细
    # 获取每个文件的增删行数统计
    numstat = run("git diff --numstat")
    # 如果有统计信息，格式化输出
    if numstat.strip():
        out.append("Per-file breakdown (+additions -deletions):")
        # 逐行解析统计信息
        for line in numstat.strip().split("\n"):
            if line.strip():
                # 以制表符分割为字段
                parts = line.split("\t")
                # 确保有三个字段：新增行数、删除行数、文件名
                if len(parts) == 3:
                    adds, dels, fname = parts
                    # 输出格式化的增删统计
                    out.append(f"  +{adds} -{dels}  {fname}")

    out.append("")
    out.append("Changed files:")
    # 获取未暂存变更的文件名列表
    names = run("git diff --name-only")
    # 获取已暂存变更的文件名列表
    names_staged = run("git diff --staged --name-only")
    # 用集合去重合并所有变更文件名
    all_names = set()
    # 将未暂存变更文件名加入集合
    for n in names.strip().split("\n"):
        if n.strip():
            all_names.add(n.strip())
    # 将已暂存变更文件名加入集合
    for n in names_staged.strip().split("\n"):
        if n.strip():
            all_names.add(n.strip())
    # 按字母顺序遍历所有变更文件
    for n in sorted(all_names):
        # 获取文件扩展名
        ext = os.path.splitext(n)[1]
        # 根据扩展名选择对应的图标（纯文本图标）
        icon = {"py": " ", "js": " ", "ts": " ", "html": " ", "css": " ", "json": " ", "md": " ",
                "yml": " ", "yaml": " ", "toml": " ", "sh": " "}.get(ext, " ")
        # 输出带图标的文件名
        out.append(f"  {icon} {n}")

    # 用换行符连接所有输出行并返回
    return "\n".join(out)


# 定义 diff_detail 函数：展示实际的 diff 内容，可选按文件过滤
def diff_detail(filepath: str = None) -> str:
    """展示实际的 diff 内容，可选按文件过滤。"""
    # 构建未暂存变更的 git diff 命令
    cmd = "git diff"
    # 如果指定了文件路径，添加文件过滤参数
    if filepath:
        cmd += f' -- "{filepath}"'
    # 同时包含已暂存的变更
    # 构建已暂存变更的 git diff 命令
    cmd_staged = "git diff --staged"
    # 如果指定了文件路径，添加文件过滤参数
    if filepath:
        cmd_staged += f' -- "{filepath}"'

    # 执行未暂存变更的 diff 命令
    output = run(cmd)
    # 执行已暂存变更的 diff 命令
    output_staged = run(cmd_staged)

    # 构建输出部分列表
    parts = []
    # 如果有已暂存变更，加入输出
    if output_staged.strip():
        parts.append("=== Staged Changes ===")
        parts.append(output_staged)
    # 如果有未暂存变更，加入输出
    if output.strip():
        parts.append("=== Unstaged Changes ===")
        parts.append(output)

    # 如果没有任何变更内容，返回提示
    if not parts:
        return "No diff content."

    # 将各部分用换行符连接
    full = "\n".join(parts)
    # 将内容按行分割
    lines = full.split("\n")
    # 超过 300 行时截断，避免输出过大
    if len(lines) > 300:
        return "\n".join(lines[:300]) + f"\n\n... (truncated, {len(lines)} total lines)"
    # 行数未超过限制，返回完整内容
    return full


# 当脚本直接运行时执行以下代码
if __name__ == "__main__":
    # 根据子命令分发到不同操作：summary / detail / files
    # 检查是否提供了子命令参数
    if len(sys.argv) < 2:
        print("Usage: python skill/diff_review.py <operation> [args]")
        print()
        print("Operations:")
        print("  summary          — overview of all changes (files, stats)")
        print("  detail [file]    — full diff, optionally filtered to one file")
        print("  files            — list changed files only")
        sys.exit(1)

    # 获取子命令（第一个位置参数）
    op = sys.argv[1]

    # 如果子命令为 summary，调用 diff_summary 并打印结果
    if op == "summary":
        print(diff_summary())
    # 如果子命令为 detail，可选传入文件路径参数
    elif op == "detail":
        # 如果有第二个参数则作为文件路径，否则为 None
        fp = sys.argv[2] if len(sys.argv) > 2 else None
        # 调用 diff_detail 并打印结果
        print(diff_detail(fp))
    # 如果子命令为 files，列出所有变更文件
    elif op == "files":
        # 获取未暂存变更的文件名列表
        unstaged = run("git diff --name-only").strip()
        # 获取已暂存变更的文件名列表
        staged = run("git diff --staged --name-only").strip()
        # 如果有未暂存变更，打印文件名
        if unstaged:
            print("Unstaged:")
            # 逐行输出文件名
            for f in unstaged.split("\n"):
                print(f"  {f}")
        # 如果有已暂存变更，打印文件名
        if staged:
            print("Staged:")
            # 逐行输出文件名
            for f in staged.split("\n"):
                print(f"  {f}")
        # 如果两者都没有变更，打印提示
        if not unstaged and not staged:
            print("No changed files.")
    # 未知子命令，打印错误提示
    else:
        print(f"Unknown operation: {op}")
        print("Available: summary, detail, files")
