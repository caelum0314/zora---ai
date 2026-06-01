"""多文件查找替换工具 —— 支持 dry-run 模式预览变更，确认后才实际写入的重构辅助脚本。"""
import sys
import os
import re
import fnmatch


def find_replace(root: str, pattern: str, replacement: str, glob: str = None,
                 dry_run: bool = True, max_files: int = 100) -> list:
    """在指定目录下递归查找并替换文本内容。"""
    # 跳过常见的非源码目录，避免误操作
    ignore = [".git", "__pycache__", "node_modules", ".venv", "venv",
              ".idea", ".vscode", "dist", "build", ".cache", "__pycache__"]
    results = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ignore]
        for fname in filenames:
            if glob and not fnmatch.fnmatch(fname, glob):
                continue
            fpath = os.path.join(dirpath, fname)
            if any(pat in fpath for pat in ignore):
                continue
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                new_content, count = re.subn(pattern, replacement, content)
                if count > 0:
                    results.append((fpath, count))
                    # 仅在非 dry-run 模式下才实际写入文件
                    if not dry_run:
                        with open(fpath, "w", encoding="utf-8") as f:
                            f.write(new_content)
                    if len(results) >= max_files:
                        break
            except (OSError, PermissionError):
                continue

    return results


if __name__ == "__main__":
    # 解析命令行参数
    if len(sys.argv) < 3:
        print("Usage: python skill/find_replace.py <pattern> <replacement> [options]")
        print()
        print("Options:")
        print("  --glob <*.py>     Only match files matching glob pattern")
        print("  --path <dir>      Search in specific directory (default: .)")
        print("  --execute         Actually make changes (default: dry-run)")
        print("  --max <n>         Max files to change (default: 100)")
        print()
        print("Examples:")
        print('  python skill/find_replace.py "old_func" "new_func" --glob "*.py"')
        print('  python skill/find_replace.py "import os" "import os\\nimport sys" --execute')
        sys.exit(1)

    pattern = sys.argv[1]
    replacement = sys.argv[2]
    glob_filter = None
    search_path = "."
    dry_run = True
    max_files = 100

    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == "--glob" and i + 1 < len(sys.argv):
            glob_filter = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--path" and i + 1 < len(sys.argv):
            search_path = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--execute":
            dry_run = False
            i += 1
        elif sys.argv[i] == "--max" and i + 1 < len(sys.argv):
            max_files = int(sys.argv[i + 1])
            i += 2
        else:
            i += 1

    mode = "DRY RUN" if dry_run else "EXECUTING"
    print(f"[{mode}] Replace '{pattern}' → '{replacement}'", file=sys.stderr)

    results = find_replace(search_path, pattern, replacement, glob_filter, dry_run, max_files)

    if not results:
        print("No matches found.")
    else:
        total = sum(c for _, c in results)
        print(f"Found {total} occurrence(s) in {len(results)} file(s):\n")
        for fpath, count in results:
            rel = os.path.relpath(fpath)
            print(f"  \033[33m{count}\033[0m  {rel}")
        if dry_run:
            print(f"\n  Re-run with --execute to apply changes.")
        else:
            print(f"\n  Changes applied to {len(results)} file(s).")
