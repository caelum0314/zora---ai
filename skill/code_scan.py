"""扫描源码文件并报告其结构 — 函数、类、导入、TODO 标记。"""
# 导入 sys 模块，用于命令行参数和退出
import sys
# 导入 os 模块，用于文件路径操作
import os
# 导入 re 模块，用于正则表达式匹配
import re


# 定义 scan_python 函数：扫描 Python 文件，提取函数、类、导入和 TODO 标记
def scan_python(filepath: str) -> str:
    """扫描 Python 文件，提取函数、类、导入和 TODO 标记。"""
    # 以 UTF-8 编码打开文件，读取所有行
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        # 读取文件的所有行到列表中
        lines = f.readlines()

    # 存储函数名称和行号的列表
    funcs = []
    # 存储类名称和行号的列表
    classes = []
    # 存储导入语句和行号的列表
    imports = []
    # 存储 TODO/FIXME 等标记和行号的列表
    todos = []
    # 存储装饰器名称的列表（本文件中未使用但保留）
    decorators = []

    # 预编译正则表达式以提高性能
    # 匹配函数定义行（支持 async def 和普通 def）
    func_re = re.compile(r"^\s*(?:async\s+)?def\s+(\w+)")
    # 匹配类定义行
    class_re = re.compile(r"^\s*class\s+(\w+)")
    # 匹配 import 或 from...import 语句
    import_re = re.compile(r"^\s*(?:import\s+|from\s+\S+\s+import\s+)")
    # 匹配 TODO/FIXME/HACK/XXX 标记（不区分大小写）
    todo_re = re.compile(r"TODO|FIXME|HACK|XXX", re.IGNORECASE)
    # 匹配装饰器行（本文件中未使用但保留）
    decorator_re = re.compile(r"^\s*@(\w+)")

    # 遍历所有行，行号从 1 开始
    for lineno, line in enumerate(lines, 1):
        # 尝试匹配函数定义
        m = func_re.match(line)
        # 如果匹配成功，记录函数名和行号
        if m:
            funcs.append((lineno, m.group(1)))
            continue
        # 尝试匹配类定义
        m = class_re.match(line)
        # 如果匹配成功，记录类名和行号
        if m:
            classes.append((lineno, m.group(1)))
            continue
        # 尝试匹配导入语句
        m = import_re.match(line)
        # 如果匹配成功，记录完整导入语句和行号
        if m:
            imports.append((lineno, line.rstrip()))
            continue
        # 在整行中搜索 TODO 等标记
        m = todo_re.search(line)
        # 如果搜索到，记录行号和该行内容
        if m:
            todos.append((lineno, line.rstrip()))

    # 构建输出结果，第一部分为文件路径和行数信息
    out = [f"File: {filepath}  ({len(lines)} lines, Python)\n"]
    # 添加类信息标题
    out.append(f"Classes ({len(classes)}):")
    # 遍历所有类，用紫色输出类名和行号
    for ln, name in classes:
        out.append(f"  \033[35mclass\033[0m {name}  (line {ln})")

    # 添加函数信息标题
    out.append(f"\nFunctions ({len(funcs)}):")
    # 遍历所有函数，用蓝色输出函数名和行号
    for ln, name in funcs:
        out.append(f"  \033[34mdef\033[0m {name}()  (line {ln})")

    # 添加导入信息标题
    out.append(f"\nImports ({len(imports)}):")
    # 遍历所有导入语句并输出
    for ln, line in imports:
        out.append(f"  {line}")

    # 如果存在 TODO 标记，添加对应标题和内容
    if todos:
        out.append(f"\nTODOs ({len(todos)}):")
        # 遍历所有 TODO 行并输出
        for ln, line in todos:
            out.append(f"  line {ln}: {line.strip()}")

    # 将所有输出行用换行符连接后返回
    return "\n".join(out)


# 定义 scan_generic 函数：非 Python 文件的通用扫描回退方案
def scan_generic(filepath: str) -> str:
    """非 Python 文件的通用扫描回退方案。"""
    # 以 UTF-8 编码打开文件，读取所有行
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        # 读取文件的所有行到列表中
        lines = f.readlines()

    # 提取文件的扩展名（含点号）
    ext = os.path.splitext(filepath)[1]
    # 存储 TODO/FIXME 等标记和行号的列表
    todos = []
    # 预编译匹配 TODO/FIXME/HACK/XXX 的正则（不区分大小写）
    todo_re = re.compile(r"TODO|FIXME|HACK|XXX", re.IGNORECASE)

    # 遍历所有行，行号从 1 开始
    for lineno, line in enumerate(lines, 1):
        # 在当前行中搜索 TODO 等标记
        if todo_re.search(line):
            # 如果匹配，记录行号和该行内容
            todos.append((lineno, line.rstrip()))

    # 构建输出结果，第一部分为文件路径和行数信息
    out = [f"File: {filepath}  ({len(lines)} lines, {ext or 'no ext'})"]
    # 如果存在 TODO 标记，添加对应标题和内容
    if todos:
        out.append(f"\nTODOs ({len(todos)}):")
        # 遍历所有 TODO 行并输出
        for ln, line in todos:
            out.append(f"  line {ln}: {line.strip()}")
    # 如果没有 TODO，提示该文件类型不支持结构分析
    else:
        out.append("\n(no structural analysis available for this file type)")

    # 将所有输出行用换行符连接后返回
    return "\n".join(out)


# 根据文件扩展名分派到对应的扫描函数
# 语言到扫描函数的映射字典
LANGS = {
    # Python 文件使用 scan_python 函数
    ".py": scan_python,
    # JavaScript 文件使用 scan_generic 函数
    ".js": scan_generic,
    # TypeScript 文件使用 scan_generic 函数
    ".ts": scan_generic,
    # TSX 文件使用 scan_generic 函数
    ".tsx": scan_generic,
    # JSX 文件使用 scan_generic 函数
    ".jsx": scan_generic,
    # Go 文件使用 scan_generic 函数
    ".go": scan_generic,
    # Rust 文件使用 scan_generic 函数
    ".rs": scan_generic,
    # Java 文件使用 scan_generic 函数
    ".java": scan_generic,
    # C 文件使用 scan_generic 函数
    ".c": scan_generic,
    # C++ 文件使用 scan_generic 函数
    ".cpp": scan_generic,
    # 头文件使用 scan_generic 函数
    ".h": scan_generic,
    # HTML 文件使用 scan_generic 函数
    ".html": scan_generic,
    # CSS 文件使用 scan_generic 函数
    ".css": scan_generic,
    # JSON 文件使用 scan_generic 函数
    ".json": scan_generic,
    # Markdown 文件使用 scan_generic 函数
    ".md": scan_generic,
    # YAML 文件使用 scan_generic 函数
    ".yaml": scan_generic,
    # YML 文件使用 scan_generic 函数
    ".yml": scan_generic,
    # TOML 文件使用 scan_generic 函数
    ".toml": scan_generic,
    # Shell 脚本使用 scan_generic 函数
    ".sh": scan_generic,
}


# 当脚本直接运行时执行以下代码
if __name__ == "__main__":
    # 支持 --path 标志和位置参数两种传参方式
    # 获取命令行参数列表（跳过脚本名本身）
    args = sys.argv[1:]
    # 初始化文件路径变量
    filepath = None
    # 初始化参数索引
    i = 0
    # 遍历所有命令行参数
    while i < len(args):
        # 如果遇到 --path 参数且后面还有值，读取文件路径
        if args[i] == "--path" and i + 1 < len(args):
            filepath = args[i + 1]
            i += 2
        # 如果遇到 --help 参数，跳过（由后续判断 filepath 为 None 时处理）
        elif args[i] == "--help":
            i += 1
        # 否则将当前参数作为文件路径（位置参数方式）
        else:
            filepath = args[i]
            i += 1

    # 如果没有提供文件路径，打印使用说明并退出
    if filepath is None:
        print("Usage: python skill/code_scan.py --path <file_path>")
        print("   or: python skill/code_scan.py <file_path>")
        print("Analyze a source file and report classes, functions, imports, TODOs.")
        sys.exit(1)

    # 展开用户目录中的 ~ 符号为实际路径
    filepath = os.path.expanduser(filepath)
    # 检查文件是否存在，不存在则报错退出
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    # 获取文件扩展名并转为小写
    ext = os.path.splitext(filepath)[1].lower()
    # 根据扩展名从映射字典中获取扫描函数，未匹配则使用 scan_generic
    scanner = LANGS.get(ext, scan_generic)
    # 调用扫描函数并打印结果
    print(scanner(filepath))
