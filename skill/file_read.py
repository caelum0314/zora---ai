"""读取文件内容并附带行号显示 — 用于代码审查和上下文查看。"""
import sys
import os


def read_file(filepath: str, start: int = 1, count: int = None) -> str:
    """读取文件内容，支持分页和行号显示。目录路径则列出目录内容。"""
    if not os.path.exists(filepath):
        return f"Error: File not found: {filepath}"

    # 如果是目录，列出其内容
    if os.path.isdir(filepath):
        items = os.listdir(filepath)
        lines = [f"Directory: {filepath}", ""]
        for item in sorted(items):
            full = os.path.join(filepath, item)
            tag = "/" if os.path.isdir(full) else ""
            lines.append(f"  {item}{tag}")
        return "\n".join(lines)

    # 大文件拒绝直接读取，防止内存溢出
    if os.path.getsize(filepath) > 1_000_000:
        return f"Error: File too large ({os.path.getsize(filepath)} bytes). Use --start and --lines."

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        all_lines = f.readlines()

    end = len(all_lines)
    if count is not None:
        end = min(start + count - 1, end)

    # 根据最大行号计算行号列宽度
    width = len(str(end))
    out = [f"File: {filepath}  ({len(all_lines)} lines)\n"]
    for i in range(start - 1, end):
        out.append(f"\033[33m{i + 1:>{width}}\033[0m  {all_lines[i].rstrip()}")

    if end < len(all_lines):
        out.append(f"\n... ({len(all_lines) - end} more lines)")

    return "\n".join(out)


if __name__ == "__main__":
    # 解析命令行参数：支持 --path、--start、--lines 和位置参数
    if len(sys.argv) < 2:
        print("Usage: python skill/file_read.py <file_path> [--start <line>] [--lines <n>]")
        print("Examples:")
        print("  python skill/file_read.py main.py")
        print("  python skill/file_read.py main.py --start 50 --lines 30")
        sys.exit(1)

    # 支持 --path 标志和位置参数两种传参方式
    args = sys.argv[1:]
    filepath = None
    start = 1
    count = None
    i = 0
    while i < len(args):
        if args[i] == "--path" and i + 1 < len(args):
            filepath = args[i + 1]
            i += 2
        elif args[i] == "--start" and i + 1 < len(args):
            start = int(args[i + 1])
            i += 2
        elif args[i] == "--lines" and i + 1 < len(args):
            count = int(args[i + 1])
            i += 2
        elif args[i] == "--help":
            i += 1
        else:
            filepath = args[i]
            i += 1

    if filepath is None:
        print("Usage: python skill/file_read.py --path <file_path> [--start <line>] [--lines <n>]")
        print("   or: python skill/file_read.py <file_path> [--start <line>] [--lines <n>]")
        sys.exit(1)

    filepath = os.path.expanduser(filepath)
    print(read_file(filepath, start, count))
