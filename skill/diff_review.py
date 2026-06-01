"""显示 git diff 摘要 — 变更文件、增删行数、关键上下文。"""
import sys
import subprocess
import os
import re


def run(cmd: str) -> str:
    """执行 git 命令并返回输出，出错时返回错误信息。"""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return r.stdout or r.stderr or ""
    except Exception as e:
        return f"Error: {e}"


def diff_summary() -> str:
    """展示所有变更的简洁摘要，包括文件统计和每文件增删行数。"""
    out = []

    # 获取未暂存和已暂存变更的统计信息
    stat = run("git diff --stat")
    stat_staged = run("git diff --staged --stat")

    if stat.strip():
        out.append("Unstaged changes:")
        out.append(stat)
        out.append("")
    if stat_staged.strip():
        out.append("Staged changes:")
        out.append(stat_staged)
        out.append("")

    if not stat.strip() and not stat_staged.strip():
        return "No changes (working tree clean)."

    # 按文件列出增删行数明细
    numstat = run("git diff --numstat")
    if numstat.strip():
        out.append("Per-file breakdown (+additions -deletions):")
        for line in numstat.strip().split("\n"):
            if line.strip():
                parts = line.split("\t")
                if len(parts) == 3:
                    adds, dels, fname = parts
                    out.append(f"  +{adds} -{dels}  {fname}")

    out.append("")
    out.append("Changed files:")
    names = run("git diff --name-only")
    names_staged = run("git diff --staged --name-only")
    all_names = set()
    for n in names.strip().split("\n"):
        if n.strip():
            all_names.add(n.strip())
    for n in names_staged.strip().split("\n"):
        if n.strip():
            all_names.add(n.strip())
    for n in sorted(all_names):
        ext = os.path.splitext(n)[1]
        icon = {"py": " ", "js": " ", "ts": " ", "html": " ", "css": " ", "json": " ", "md": " ",
                "yml": " ", "yaml": " ", "toml": " ", "sh": " "}.get(ext, " ")
        out.append(f"  {icon} {n}")

    return "\n".join(out)


def diff_detail(filepath: str = None) -> str:
    """展示实际的 diff 内容，可选按文件过滤。"""
    cmd = "git diff"
    if filepath:
        cmd += f' -- "{filepath}"'
    # 同时包含已暂存的变更
    cmd_staged = "git diff --staged"
    if filepath:
        cmd_staged += f' -- "{filepath}"'

    output = run(cmd)
    output_staged = run(cmd_staged)

    parts = []
    if output_staged.strip():
        parts.append("=== Staged Changes ===")
        parts.append(output_staged)
    if output.strip():
        parts.append("=== Unstaged Changes ===")
        parts.append(output)

    if not parts:
        return "No diff content."

    full = "\n".join(parts)
    lines = full.split("\n")
    # 超过 300 行时截断，避免输出过大
    if len(lines) > 300:
        return "\n".join(lines[:300]) + f"\n\n... (truncated, {len(lines)} total lines)"
    return full


if __name__ == "__main__":
    # 根据子命令分发到不同操作：summary / detail / files
    if len(sys.argv) < 2:
        print("Usage: python skill/diff_review.py <operation> [args]")
        print()
        print("Operations:")
        print("  summary          — overview of all changes (files, stats)")
        print("  detail [file]    — full diff, optionally filtered to one file")
        print("  files            — list changed files only")
        sys.exit(1)

    op = sys.argv[1]

    if op == "summary":
        print(diff_summary())
    elif op == "detail":
        fp = sys.argv[2] if len(sys.argv) > 2 else None
        print(diff_detail(fp))
    elif op == "files":
        unstaged = run("git diff --name-only").strip()
        staged = run("git diff --staged --name-only").strip()
        if unstaged:
            print("Unstaged:")
            for f in unstaged.split("\n"):
                print(f"  {f}")
        if staged:
            print("Staged:")
            for f in staged.split("\n"):
                print(f"  {f}")
        if not unstaged and not staged:
            print("No changed files.")
    else:
        print(f"Unknown operation: {op}")
        print("Available: summary, detail, files")
