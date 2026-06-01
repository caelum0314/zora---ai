# 文件写入工具 —— 支持创建新文件或在已有文件末尾追加内容，自动创建不存在的父目录
"""文件写入工具 —— 支持创建新文件或在已有文件末尾追加内容，自动创建不存在的父目录。"""
# 导入 sys 模块，用于获取命令行参数
import sys
# 导入 os 模块，用于文件路径操作和目录创建
import os


# 当脚本直接运行时执行以下代码
if __name__ == "__main__":
    # 同时支持位置参数和 --path/--content/--append 标记两种传参方式
    # 获取命令行参数列表（去掉脚本名）
    args = sys.argv[1:]
    # 初始化文件路径变量
    filepath = None
    # 初始化文件内容变量
    content = None
    # 初始化追加模式标志
    append = False
    # 初始化临时文件路径变量
    from_temp = None
    # 初始化参数索引
    i = 0
    # 遍历所有命令行参数
    while i < len(args):
        # 解析 --path 标记及其后的路径值
        if args[i] == "--path" and i + 1 < len(args):
            # 获取 --path 后面的参数作为文件路径
            filepath = args[i + 1]
            # 跳过已处理的标记和值
            i += 2
        # 解析 --content 标记及其后的内容值
        elif args[i] == "--content" and i + 1 < len(args):
            # 获取 --content 后面的参数作为文件内容
            content = args[i + 1]
            # 跳过已处理的标记和值
            i += 2
        # 解析 --append 标记
        elif args[i] == "--append":
            # 启用追加模式
            append = True
            # 跳过已处理的标记
            i += 1
        # 解析 --from-temp 标记及其后的临时文件路径
        elif args[i] == "--from-temp" and i + 1 < len(args):
            # 获取 --from-temp 后面的参数作为临时文件路径
            from_temp = args[i + 1]
            # 跳过已处理的标记和值
            i += 2
        # 解析 --help 标记
        elif args[i] == "--help":
            # 跳过 --help，后续会因缺少参数而打印帮助
            i += 1
        # 处理位置参数（无标记的参数）
        else:
            # 如果文件路径尚未设置，则将当前参数作为文件路径
            if filepath is None:
                filepath = args[i]
            # 如果内容尚未设置，则将当前参数作为内容
            elif content is None:
                content = args[i]
            # 移动到下一个参数
            i += 1

    # 验证必填参数：文件路径和内容至少需要提供其一
    if filepath is None or (content is None and from_temp is None):
        # 打印使用说明
        print("Usage: python skill/write_file.py --path <file_path> --content <content> [--append]")
        print("   or: python skill/write_file.py <file_path> <content> [--append]")
        print("   or: python skill/write_file.py --path <file_path> --from-temp <temp_file>")
        print("Examples:")
        print('  python skill/write_file.py --path hello.py --content "print(\'hello\')"')
        print("  python skill/write_file.py --path MEMORY.md --content 'Remember: use snake_case' --append")
        # 以错误码 1 退出
        sys.exit(1)

    # 展开路径中的 ~ 和 ~user 为用户主目录
    filepath = os.path.expanduser(filepath)
    # 检查是否指定了临时文件来源
    if from_temp:
        # 验证临时文件是否存在
        if not os.path.exists(from_temp):
            # 临时文件不存在时打印错误并退出
            print(f"Error: temp file not found: {from_temp}")
            sys.exit(1)
        # 打开临时文件并以 UTF-8 编码读取内容
        with open(from_temp, "r", encoding="utf-8") as f:
            content = f.read()
    # 自动创建目标路径中不存在的父目录
    # 获取目标文件的父目录路径
    dirpath = os.path.dirname(filepath)
    # 如果父目录不为空且不存在
    if dirpath and not os.path.exists(dirpath):
        # 递归创建所有不存在的父目录
        os.makedirs(dirpath, exist_ok=True)
    # 根据追加模式选择文件打开模式：a 为追加，w 为覆盖写入
    mode = "a" if append else "w"
    # 以指定模式打开文件，UTF-8 编码
    with open(filepath, mode, encoding="utf-8") as f:
        # 追加模式下先写入一个换行符
        if append:
            f.write("\n")
        # 写入内容
        f.write(content)
    # 获取写入后文件的大小
    size = os.path.getsize(filepath)
    # 根据模式选择操作描述文案
    action = "Appended to" if append else "Wrote"
    # 打印操作结果：操作类型、文件路径和文件大小
    print(f"{action} {filepath} ({size} bytes)")
