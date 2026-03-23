import sys
import os

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: edit <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            pass
    
    # 使用系统默认编辑器打开文件
    if os.name == 'nt':  # Windows
        os.system(f"start {file_path}")
    elif os.name == 'posix':  # Linux/macOS
        os.system(f"xdg-open {file_path}")
    print(f"Opening {file_path} for editing...")