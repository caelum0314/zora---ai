"""在代码库中搜索正则模式 — 类似 grep/ripgrep 的项目搜索工具。"""
# 导入 sys 模块，用于命令行参数和退出
import sys
# 导入 os 模块，用于文件系统和路径操作
import os
# 导入 re 模块，用于正则表达式匹配
import re
# 导入 fnmatch 模块，用于 Unix 风格的 glob 文件名匹配
import fnmatch
# 导入 Path 类（本文件中未直接使用，仅作为便利导入）
from pathlib import Path


# 定义 should_skip 函数：检查文件路径是否匹配任一忽略规则，匹配则跳过
def should_skip(path: str, ignore_patterns: list) -> bool:
    """检查文件路径是否匹配任一忽略规则，匹配则跳过。"""
    # 遍历所有忽略模式
    for pat in ignore_patterns:
        # 如果路径中包含忽略模式字符串，返回 True 表示应跳过
        if pat in path:
            return True
    # 没有匹配到任何忽略模式，返回 False
    return False


# 定义 search_files 函数：递归遍历目录树，搜索匹配正则模式的行
def search_files(root: str, pattern: str, glob: str = None, max_results: int = 30):
    """递归遍历目录树，搜索匹配正则模式的行。"""
    # 需要忽略的目录和文件名关键字列表
    ignore = [".git", "__pycache__", "node_modules", ".venv", "venv", ".idea", ".vscode", "dist", "build", ".cache"]
    # 存储搜索结果的列表，每项为 (文件路径, 行号, 行内容)
    results = []

    # 递归遍历根目录下的所有子目录和文件
    for dirpath, dirnames, filenames in os.walk(root):
        # 原地过滤掉需要忽略的目录，避免重复遍历
        dirnames[:] = [d for d in dirnames if d not in ignore]
        # 遍历当前目录下的所有文件
        for fname in filenames:
            # 拼接完整的文件路径
            fpath = os.path.join(dirpath, fname)
            # 如果文件路径匹配忽略规则，跳过该文件
            if should_skip(fpath, ignore):
                continue
            # 如果指定了 glob 过滤且文件名不匹配，跳过该文件
            if glob and not fnmatch.fnmatch(fname, glob):
                continue
            try:
                # 以 UTF-8 编码打开文件，忽略编解码错误
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    # 逐行读取文件，行号从 1 开始
                    for lineno, line in enumerate(f, 1):
                        # 在当前行中搜索正则模式
                        if re.search(pattern, line):
                            # 匹配成功，记录文件路径、行号和行内容
                            results.append((fpath, lineno, line.rstrip()))
                            # 如果结果数已达到上限，跳出内层循环
                            if len(results) >= max_results:
                                break
                # 如果结果数已达到上限，跳出外层循环
                if len(results) >= max_results:
                    break
            # 捕获文件读取权限等异常，跳过该文件继续执行
            except (OSError, PermissionError):
                continue
    # 返回所有匹配结果
    return results


# 当脚本直接运行时执行以下代码
if __name__ == "__main__":
    # 解析命令行参数：模式、glob 过滤、搜索路径、最大结果数
    # 检查是否提供了必要的正则模式参数
    if len(sys.argv) < 2:
        print("Usage: python skill/code_search.py <regex_pattern> [--glob <*.py>] [--path <dir>] [--max <n>]")
        print("Examples:")
        print("  python skill/code_search.py 'def execute' --glob '*.py'")
        print("  python skill/code_search.py 'TODO|FIXME'")
        print("  python skill/code_search.py 'import json' --max 10")
        sys.exit(1)

    # 第一个位置参数为正则搜索模式
    pattern = sys.argv[1]
    # 初始化 glob 文件名过滤条件
    glob_filter = None
    # 默认搜索当前目录
    search_path = "."
    # 默认最多返回 30 条结果
    max_results = 30

    # 从索引 2 开始解析可选参数
    i = 2
    # 遍历剩余的命令行参数
    while i < len(sys.argv):
        # 如果遇到 --glob 参数且后面还有值，读取 glob 模式
        if sys.argv[i] == "--glob" and i + 1 < len(sys.argv):
            glob_filter = sys.argv[i + 1]
            i += 2
        # 如果遇到 --path 参数且后面还有值，读取搜索路径
        elif sys.argv[i] == "--path" and i + 1 < len(sys.argv):
            search_path = sys.argv[i + 1]
            i += 2
        # 如果遇到 --max 参数且后面还有值，读取最大结果数
        elif sys.argv[i] == "--max" and i + 1 < len(sys.argv):
            max_results = int(sys.argv[i + 1])
            i += 2
        # 忽略无法识别的参数
        else:
            i += 1

    # 向标准错误输出当前搜索的模式，便于区分日志和结果
    print(f"Searching for: '{pattern}'", file=sys.stderr)
    # 调用 search_files 执行搜索
    results = search_files(search_path, pattern, glob_filter, max_results)

    # 如果没有找到匹配结果
    if not results:
        print("No matches found.")
    # 如果找到匹配结果，逐条输出
    else:
        print(f"Found {len(results)} matches:\n")
        # 遍历所有结果
        for fpath, lineno, line in results:
            # 输出相对路径和行号，便于定位
            # 将绝对路径转为相对路径
            rel = os.path.relpath(fpath)
            # 用青色输出文件路径和行号，后面跟匹配的行内容
            print(f"\033[36m{rel}:{lineno}\033[0m  {line}")
