"""使用系统默认编辑器打开文件进行编辑。"""
# 导入 sys 模块，用于获取命令行参数和退出程序
import sys
# 导入 os 模块，用于检测操作系统类型和文件操作
import os

# 判断是否作为主程序运行（而非被导入为模块）
if __name__ == "__main__":
    # 检查是否提供了文件路径参数
    if len(sys.argv) < 2:
        # 没有提供参数时，打印使用说明
        print("Usage: edit <file_path>")
        # 以非零状态码退出，表示执行失败
        sys.exit(1)
    
    # 获取命令行中传入的文件路径（第一个参数）
    file_path = sys.argv[1]
    # 如果文件不存在，先创建一个空文件
    if not os.path.exists(file_path):
        # 以写入模式打开（即创建）一个空文件
        with open(file_path, 'w') as f:
            # 什么都不写入，仅创建空文件
            pass
    
    # 使用系统默认编辑器打开文件
    if os.name == 'nt':  # Windows 系统
        # 在 Windows 上使用 start 命令打开文件
        os.system(f"start {file_path}")
    elif os.name == 'posix':  # Linux/macOS 系统
        # 在 Linux/macOS 上使用 xdg-open 命令打开文件
        os.system(f"xdg-open {file_path}")
    # 打印提示信息，告知用户正在打开文件
    print(f"Opening {file_path} for editing...")