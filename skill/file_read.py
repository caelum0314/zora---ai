"""读取文件内容并附带行号显示 — 用于代码审查和上下文查看。"""
# 导入 sys 模块，用于命令行参数解析和程序退出
import sys
# 导入 os 模块，用于文件路径和目录操作
import os


# 定义 read_file 函数：读取文件内容，支持分页和行号显示
def read_file(filepath: str, start: int = 1, count: int = None) -> str:
    """读取文件内容，支持分页和行号显示。目录路径则列出目录内容。"""
    # 检查文件或目录是否存在
    if not os.path.exists(filepath):
        # 不存在时返回错误信息
        return f"Error: File not found: {filepath}"

    # 如果是目录，列出其内容
    if os.path.isdir(filepath):
        # 获取目录下所有文件和子目录名称
        items = os.listdir(filepath)
        # 构建输出行的列表，第一行为目录路径
        lines = [f"Directory: {filepath}", ""]
        # 按字母顺序遍历目录内容
        for item in sorted(items):
            # 拼接完整路径，用于判断是否为目录
            full = os.path.join(filepath, item)
            # 如果是目录，追加 "/" 作为标记
            tag = "/" if os.path.isdir(full) else ""
            # 将条目添加到输出列表
            lines.append(f"  {item}{tag}")
        # 返回拼接后的目录列表字符串
        return "\n".join(lines)

    # 大文件拒绝直接读取，防止内存溢出
    if os.path.getsize(filepath) > 1_000_000:
        # 文件超过 1MB 时返回错误提示
        return f"Error: File too large ({os.path.getsize(filepath)} bytes). Use --start and --lines."

    # 以 UTF-8 编码打开文件，遇到无效字符时替换而非报错
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        # 读取文件所有行到列表
        all_lines = f.readlines()

    # 设置结束行号，默认为文件总行数
    end = len(all_lines)
    # 如果指定了读取行数 count，调整结束行号
    if count is not None:
        # 取 "起始行+行数-1" 和总行数中的较小值
        end = min(start + count - 1, end)

    # 根据最大行号计算行号列宽度（用于右对齐格式化）
    width = len(str(end))
    # 构建输出列表，首行为文件名和总行数
    out = [f"File: {filepath}  ({len(all_lines)} lines)\n"]
    # 遍历需要显示的行范围
    for i in range(start - 1, end):
        # 格式化输出：黄色行号 + 右对齐 + 重置颜色 + 内容
        out.append(f"\033[33m{i + 1:>{width}}\033[0m  {all_lines[i].rstrip()}")

    # 如果还有未显示的行，追加省略提示
    if end < len(all_lines):
        out.append(f"\n... ({len(all_lines) - end} more lines)")

    # 返回拼接后的完整输出字符串
    return "\n".join(out)


# 判断是否作为主程序运行
if __name__ == "__main__":
    # 解析命令行参数：支持 --path、--start、--lines 和位置参数
    if len(sys.argv) < 2:
        # 参数不足时打印使用说明
        print("Usage: python skill/file_read.py <file_path> [--start <line>] [--lines <n>]")
        # 打印示例
        print("Examples:")
        # 示例：读取整个文件
        print("  python skill/file_read.py main.py")
        # 示例：从第 50 行开始读取 30 行
        print("  python skill/file_read.py main.py --start 50 --lines 30")
        # 以非零状态码退出
        sys.exit(1)

    # 支持 --path 标志和位置参数两种传参方式
    # 获取除脚本名外的所有参数
    args = sys.argv[1:]
    # 初始化文件路径变量
    filepath = None
    # 起始行号默认为 1
    start = 1
    # 读取行数默认为 None（读取全部）
    count = None
    # 参数索引计数器
    i = 0
    # 遍历解析所有命令行参数
    while i < len(args):
        # 处理 --path 选项：指定文件路径
        if args[i] == "--path" and i + 1 < len(args):
            # 获取 --path 后的值作为文件路径
            filepath = args[i + 1]
            # 跳过已处理的选项和值
            i += 2
        # 处理 --start 选项：指定起始行号
        elif args[i] == "--start" and i + 1 < len(args):
            # 将字符串转换为整数，作为起始行号
            start = int(args[i + 1])
            # 跳过已处理的选项和值
            i += 2
        # 处理 --lines 选项：指定读取行数
        elif args[i] == "--lines" and i + 1 < len(args):
            # 将字符串转换为整数，作为读取行数
            count = int(args[i + 1])
            # 跳过已处理的选项和值
            i += 2
        # 处理 --help 选项：直接跳过
        elif args[i] == "--help":
            # 跳过 --help 参数本身
            i += 1
        # 位置参数：直接作为文件路径
        else:
            # 将当前参数作为文件路径
            filepath = args[i]
            # 移动到下一个参数
            i += 1

    # 如果解析完仍未得到文件路径，报错退出
    if filepath is None:
        # 打印两种使用方式
        print("Usage: python skill/file_read.py --path <file_path> [--start <line>] [--lines <n>]")
        # 第二种使用方式
        print("   or: python skill/file_read.py <file_path> [--start <line>] [--lines <n>]")
        # 以非零状态码退出
        sys.exit(1)

    # 展开用户主目录符号（如 ~ 展开为 /home/user）
    filepath = os.path.expanduser(filepath)
    # 调用 read_file 函数并打印结果
    print(read_file(filepath, start, count))
