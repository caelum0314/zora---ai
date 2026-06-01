"""多文件查找替换工具 —— 支持 dry-run 模式预览变更，确认后才实际写入的重构辅助脚本。"""
# 导入 sys 模块，用于命令行参数解析和退出
import sys
# 导入 os 模块，用于文件路径和目录遍历
import os
# 导入 re 模块，用于正则表达式匹配和替换
import re
# 导入 fnmatch 模块，用于 Unix 风格的文件名通配符匹配
import fnmatch


# 定义 find_replace 函数：在目录下递归查找并替换文本内容
def find_replace(root: str, pattern: str, replacement: str, glob: str = None,
                 dry_run: bool = True, max_files: int = 100) -> list:
    """在指定目录下递归查找并替换文本内容。"""
    # 跳过常见的非源码目录，避免误操作
    ignore = [".git", "__pycache__", "node_modules", ".venv", "venv",
              ".idea", ".vscode", "dist", "build", ".cache", "__pycache__"]
    # 初始化结果列表，存储 (文件路径, 匹配次数) 元组
    results = []

    # 使用 os.walk 递归遍历目录树
    for dirpath, dirnames, filenames in os.walk(root):
        # 原地过滤 dirnames，排除需要忽略的目录，避免进入它们
        dirnames[:] = [d for d in dirnames if d not in ignore]
        # 遍历当前目录下的所有文件
        for fname in filenames:
            # 如果指定了 glob 模式且文件名不匹配，则跳过
            if glob and not fnmatch.fnmatch(fname, glob):
                continue
            # 拼接完整文件路径
            fpath = os.path.join(dirpath, fname)
            # 再次检查路径中是否包含忽略目录（双重保险）
            if any(pat in fpath for pat in ignore):
                continue
            try:
                # 以只读模式打开文件，忽略编码错误
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    # 读取文件全部内容
                    content = f.read()
                # 使用正则表达式替换，返回新内容和替换次数
                new_content, count = re.subn(pattern, replacement, content)
                # 如果找到匹配项，记录结果
                if count > 0:
                    # 将文件路径和匹配次数加入结果列表
                    results.append((fpath, count))
                    # 仅在非 dry-run 模式下才实际写入文件
                    if not dry_run:
                        # 以写入模式打开文件，覆盖原内容
                        with open(fpath, "w", encoding="utf-8") as f:
                            # 写入替换后的内容
                            f.write(new_content)
                    # 达到最大文件数上限时停止遍历
                    if len(results) >= max_files:
                        break
            # 捕获文件读取/写入权限异常，跳过该文件
            except (OSError, PermissionError):
                continue

    # 返回所有匹配结果
    return results


# 判断是否作为主程序运行
if __name__ == "__main__":
    # 解析命令行参数
    if len(sys.argv) < 3:
        # 参数不足时打印使用说明
        print("Usage: python skill/find_replace.py <pattern> <replacement> [options]")
        # 空行，美化输出
        print()
        # 打印可选参数说明
        print("Options:")
        # --glob 选项：按文件模式过滤
        print("  --glob <*.py>     Only match files matching glob pattern")
        # --path 选项：指定搜索目录
        print("  --path <dir>      Search in specific directory (default: .)")
        # --execute 选项：实际执行替换
        print("  --execute         Actually make changes (default: dry-run)")
        # --max 选项：最大处理文件数
        print("  --max <n>         Max files to change (default: 100)")
        # 空行
        print()
        # 打印使用示例
        print("Examples:")
        # 示例：按 glob 模式替换
        print('  python skill/find_replace.py "old_func" "new_func" --glob "*.py"')
        # 示例：实际执行替换
        print('  python skill/find_replace.py "import os" "import os\\nimport sys" --execute')
        # 以非零状态码退出
        sys.exit(1)

    # 第一个参数：正则匹配模式
    pattern = sys.argv[1]
    # 第二个参数：替换字符串
    replacement = sys.argv[2]
    # glob 过滤模式，默认为 None（不过滤）
    glob_filter = None
    # 搜索路径，默认为当前目录
    search_path = "."
    # dry-run 模式默认开启（只预览不写入）
    dry_run = True
    # 最大处理文件数，默认 100
    max_files = 100

    # 从第 3 个参数开始解析可选选项
    i = 3
    # 遍历剩余的命令行参数
    while i < len(sys.argv):
        # 处理 --glob 选项：文件通配符过滤
        if sys.argv[i] == "--glob" and i + 1 < len(sys.argv):
            # 获取 glob 模式字符串
            glob_filter = sys.argv[i + 1]
            # 跳过已处理的选项和值
            i += 2
        # 处理 --path 选项：指定搜索目录
        elif sys.argv[i] == "--path" and i + 1 < len(sys.argv):
            # 获取搜索路径
            search_path = sys.argv[i + 1]
            # 跳过已处理的选项和值
            i += 2
        # 处理 --execute 选项：实际执行替换
        elif sys.argv[i] == "--execute":
            # 关闭 dry-run 模式
            dry_run = False
            # 移动到下一个参数
            i += 1
        # 处理 --max 选项：最大文件数
        elif sys.argv[i] == "--max" and i + 1 < len(sys.argv):
            # 将字符串转换为整数
            max_files = int(sys.argv[i + 1])
            # 跳过已处理的选项和值
            i += 2
        # 未知选项，跳过
        else:
            i += 1

    # 根据模式设置显示标题
    mode = "DRY RUN" if dry_run else "EXECUTING"
    # 在 stderr 输出当前模式和替换信息
    print(f"[{mode}] Replace '{pattern}' → '{replacement}'", file=sys.stderr)

    # 调用 find_replace 函数执行查找替换
    results = find_replace(search_path, pattern, replacement, glob_filter, dry_run, max_files)

    # 如果没有匹配结果
    if not results:
        # 打印"未找到匹配项"
        print("No matches found.")
    else:
        # 汇总所有文件中的匹配次数
        total = sum(c for _, c in results)
        # 打印匹配统计信息
        print(f"Found {total} occurrence(s) in {len(results)} file(s):\n")
        # 遍历每个匹配结果
        for fpath, count in results:
            # 将绝对路径转为相对路径，使输出更简洁
            rel = os.path.relpath(fpath)
            # 打印匹配次数（黄色高亮）和文件路径
            print(f"  \033[33m{count}\033[0m  {rel}")
        # 如果当前是 dry-run 模式，提示如何实际执行
        if dry_run:
            print(f"\n  Re-run with --execute to apply changes.")
        # 实际执行模式，确认变更已应用
        else:
            print(f"\n  Changes applied to {len(results)} file(s).")
