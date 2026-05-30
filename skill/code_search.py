"""Search codebase for patterns — like grep/ripgrep for your project."""
import sys
import os
import re
import fnmatch
from pathlib import Path


def should_skip(path: str, ignore_patterns: list) -> bool:
    for pat in ignore_patterns:
        if pat in path:
            return True
    return False


def search_files(root: str, pattern: str, glob: str = None, max_results: int = 30):
    ignore = [".git", "__pycache__", "node_modules", ".venv", "venv", ".idea", ".vscode", "dist", "build", ".cache"]
    results = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ignore]
        for fname in filenames:
            fpath = os.path.join(dirpath, fname)
            if should_skip(fpath, ignore):
                continue
            if glob and not fnmatch.fnmatch(fname, glob):
                continue
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for lineno, line in enumerate(f, 1):
                        if re.search(pattern, line):
                            results.append((fpath, lineno, line.rstrip()))
                            if len(results) >= max_results:
                                break
                if len(results) >= max_results:
                    break
            except (OSError, PermissionError):
                continue
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python skill/code_search.py <regex_pattern> [--glob <*.py>] [--path <dir>] [--max <n>]")
        print("Examples:")
        print("  python skill/code_search.py 'def execute' --glob '*.py'")
        print("  python skill/code_search.py 'TODO|FIXME'")
        print("  python skill/code_search.py 'import json' --max 10")
        sys.exit(1)

    pattern = sys.argv[1]
    glob_filter = None
    search_path = "."
    max_results = 30

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--glob" and i + 1 < len(sys.argv):
            glob_filter = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--path" and i + 1 < len(sys.argv):
            search_path = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--max" and i + 1 < len(sys.argv):
            max_results = int(sys.argv[i + 1])
            i += 2
        else:
            i += 1

    print(f"Searching for: '{pattern}'", file=sys.stderr)
    results = search_files(search_path, pattern, glob_filter, max_results)

    if not results:
        print("No matches found.")
    else:
        print(f"Found {len(results)} matches:\n")
        for fpath, lineno, line in results:
            rel = os.path.relpath(fpath)
            print(f"\033[36m{rel}:{lineno}\033[0m  {line}")
