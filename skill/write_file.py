"""文件写入工具 —— 支持创建新文件或在已有文件末尾追加内容，自动创建不存在的父目录。"""
import sys
import os


if __name__ == "__main__":
    # 同时支持位置参数和 --path/--content/--append 标记两种传参方式
    args = sys.argv[1:]
    filepath = None
    content = None
    append = False
    from_temp = None

    i = 0
    while i < len(args):
        if args[i] == "--path" and i + 1 < len(args):
            filepath = args[i + 1]
            i += 2
        elif args[i] == "--content" and i + 1 < len(args):
            content = args[i + 1]
            i += 2
        elif args[i] == "--append":
            append = True
            i += 1
        elif args[i] == "--from-temp" and i + 1 < len(args):
            from_temp = args[i + 1]
            i += 2
        elif args[i] == "--help":
            i += 1
        else:
            if filepath is None:
                filepath = args[i]
            elif content is None:
                content = args[i]
            i += 1

    if filepath is None or (content is None and from_temp is None):
        print("Usage: python skill/write_file.py --path <file_path> --content <content> [--append]")
        print("   or: python skill/write_file.py <file_path> <content> [--append]")
        print("   or: python skill/write_file.py --path <file_path> --from-temp <temp_file>")
        print("Examples:")
        print('  python skill/write_file.py --path hello.py --content "print(\'hello\')"')
        print("  python skill/write_file.py --path MEMORY.md --content 'Remember: use snake_case' --append")
        sys.exit(1)

    filepath = os.path.expanduser(filepath)

    if from_temp:
        if not os.path.exists(from_temp):
            print(f"Error: temp file not found: {from_temp}")
            sys.exit(1)
        with open(from_temp, "r", encoding="utf-8") as f:
            content = f.read()

    # 自动创建目标路径中不存在的父目录
    dirpath = os.path.dirname(filepath)
    if dirpath and not os.path.exists(dirpath):
        os.makedirs(dirpath, exist_ok=True)

    mode = "a" if append else "w"
    with open(filepath, mode, encoding="utf-8") as f:
        if append:
            f.write("\n")
        f.write(content)

    size = os.path.getsize(filepath)
    action = "Appended to" if append else "Wrote"
    print(f"{action} {filepath} ({size} bytes)")
