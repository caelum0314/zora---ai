"""扫描源码文件并报告其结构 — 函数、类、导入、TODO 标记。"""
import sys
import os
import re


def scan_python(filepath: str) -> str:
    """扫描 Python 文件，提取函数、类、导入和 TODO 标记。"""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    funcs = []
    classes = []
    imports = []
    todos = []
    decorators = []

    # 预编译正则表达式以提高性能
    func_re = re.compile(r"^\s*(?:async\s+)?def\s+(\w+)")
    class_re = re.compile(r"^\s*class\s+(\w+)")
    import_re = re.compile(r"^\s*(?:import\s+|from\s+\S+\s+import\s+)")
    todo_re = re.compile(r"TODO|FIXME|HACK|XXX", re.IGNORECASE)
    decorator_re = re.compile(r"^\s*@(\w+)")

    for lineno, line in enumerate(lines, 1):
        m = func_re.match(line)
        if m:
            funcs.append((lineno, m.group(1)))
            continue
        m = class_re.match(line)
        if m:
            classes.append((lineno, m.group(1)))
            continue
        m = import_re.match(line)
        if m:
            imports.append((lineno, line.rstrip()))
            continue
        m = todo_re.search(line)
        if m:
            todos.append((lineno, line.rstrip()))

    out = [f"File: {filepath}  ({len(lines)} lines, Python)\n"]
    out.append(f"Classes ({len(classes)}):")
    for ln, name in classes:
        out.append(f"  \033[35mclass\033[0m {name}  (line {ln})")

    out.append(f"\nFunctions ({len(funcs)}):")
    for ln, name in funcs:
        out.append(f"  \033[34mdef\033[0m {name}()  (line {ln})")

    out.append(f"\nImports ({len(imports)}):")
    for ln, line in imports:
        out.append(f"  {line}")

    if todos:
        out.append(f"\nTODOs ({len(todos)}):")
        for ln, line in todos:
            out.append(f"  line {ln}: {line.strip()}")

    return "\n".join(out)


def scan_generic(filepath: str) -> str:
    """非 Python 文件的通用扫描回退方案。"""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    ext = os.path.splitext(filepath)[1]
    todos = []
    todo_re = re.compile(r"TODO|FIXME|HACK|XXX", re.IGNORECASE)

    for lineno, line in enumerate(lines, 1):
        if todo_re.search(line):
            todos.append((lineno, line.rstrip()))

    out = [f"File: {filepath}  ({len(lines)} lines, {ext or 'no ext'})"]
    if todos:
        out.append(f"\nTODOs ({len(todos)}):")
        for ln, line in todos:
            out.append(f"  line {ln}: {line.strip()}")
    else:
        out.append("\n(no structural analysis available for this file type)")

    return "\n".join(out)


# 根据文件扩展名分派到对应的扫描函数
LANGS = {
    ".py": scan_python,
    ".js": scan_generic,
    ".ts": scan_generic,
    ".tsx": scan_generic,
    ".jsx": scan_generic,
    ".go": scan_generic,
    ".rs": scan_generic,
    ".java": scan_generic,
    ".c": scan_generic,
    ".cpp": scan_generic,
    ".h": scan_generic,
    ".html": scan_generic,
    ".css": scan_generic,
    ".json": scan_generic,
    ".md": scan_generic,
    ".yaml": scan_generic,
    ".yml": scan_generic,
    ".toml": scan_generic,
    ".sh": scan_generic,
}


if __name__ == "__main__":
    # 支持 --path 标志和位置参数两种传参方式
    args = sys.argv[1:]
    filepath = None
    i = 0
    while i < len(args):
        if args[i] == "--path" and i + 1 < len(args):
            filepath = args[i + 1]
            i += 2
        elif args[i] == "--help":
            i += 1
        else:
            filepath = args[i]
            i += 1

    if filepath is None:
        print("Usage: python skill/code_scan.py --path <file_path>")
        print("   or: python skill/code_scan.py <file_path>")
        print("Analyze a source file and report classes, functions, imports, TODOs.")
        sys.exit(1)

    filepath = os.path.expanduser(filepath)
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    ext = os.path.splitext(filepath)[1].lower()
    scanner = LANGS.get(ext, scan_generic)
    print(scanner(filepath))
