# 测试运行工具 —— 自动检测项目使用的测试框架（pytest/unittest），运行测试并提取失败用例的关键信息
"""测试运行工具 —— 自动检测项目使用的测试框架（pytest/unittest），运行测试并提取失败用例的关键信息。"""
# 导入 sys 模块，用于获取解释器路径和命令行参数
import sys
# 导入 subprocess 模块，用于在子进程中执行测试命令
import subprocess
# 导入 os 模块，用于检测文件是否存在
import os
# 导入 re 模块，用于正则匹配（预留）
import re
# 导入 json 模块，用于 JSON 序列化（预留）
import json


# 定义 find_test_framework 函数，自动检测项目使用的测试框架
def find_test_framework():
    # 检测当前项目可用的测试框架，优先返回 pytest
    """检测当前项目可用的测试框架，优先返回 pytest。"""
    # 遍历常见的 pytest 配置文件列表
    for f in ["pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini"]:
        # 如果配置文件存在，则判定为 pytest 项目
        if os.path.exists(f):
            return "pytest"
    # 尝试检查 pytest 是否已安装
    try:
        # 执行 pytest --version 命令来检测
        subprocess.run([sys.executable, "-m", "pytest", "--version"],
                       capture_output=True, timeout=5)
        # 执行成功则返回 pytest
        return "pytest"
    # 捕获任何异常（pytest 未安装或命令失败）
    except Exception:
        # 忽略异常，继续尝试下一个检测方式
        pass
    # 默认返回 unittest 作为兜底框架
    return "unittest"


# 定义 run_pytest 函数，使用 pytest 框架运行测试
def run_pytest(args: list) -> dict:
    # 以 pytest 框架运行测试，使用 --tb=short 精简输出
    """以 pytest 框架运行测试，使用 --tb=short 精简输出。"""
    # 构建 pytest 命令，添加详细输出、短回溯、无颜色标记
    cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short", "--color=no"]
    # 检查是否有额外参数传入
    if args:
        # 有参数时扩展命令参数列表
        cmd.extend(args)
    else:
        # 无参数时默认测试当前目录
        cmd.append(".")
    # 在子进程中执行 pytest 命令，捕获输出
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=os.getcwd())
    # 返回结构化结果字典
    return {"success": r.returncode == 0, "output": r.stdout, "stderr": r.stderr,
            "returncode": r.returncode}


# 定义 run_unittest 函数，使用 unittest 框架运行测试
def run_unittest(args: list) -> dict:
    # 以 unittest discover 模式运行测试，将路径转换为模块名
    """以 unittest discover 模式运行测试，将路径转换为模块名。"""
    # 构建 unittest discover 命令
    cmd = [sys.executable, "-m", "unittest", "discover", "-v"]
    # 检查是否指定了测试目标路径
    if args:
        # 将文件路径转换为模块名（替换路径分隔符，去掉 .py 后缀）
        target = args[0].replace("/", ".").replace("\\", ".").replace(".py", "")
        # 用目标模块名重新构建命令
        cmd = [sys.executable, "-m", "unittest", target, "-v"]
    # 在子进程中执行 unittest 命令，捕获输出
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=os.getcwd())
    # 返回结构化结果字典
    return {"success": r.returncode == 0, "output": r.stdout, "stderr": r.stderr,
            "returncode": r.returncode}


# 定义 extract_failures 函数，从测试输出中提取失败相关信息
def extract_failures(output: str):
    # 从测试输出中提取 FAIL/ERROR/assert 相关的失败行，用于简洁展示
    """从测试输出中提取 FAIL/ERROR/assert 相关的失败行，用于简洁展示。"""
    # 将输出按换行符分割成行列表
    lines = output.split("\n")
    # 初始化失败行列表
    failures = []
    # 标记是否处于失败输出区域
    in_failure = False
    # 逐行遍历测试输出
    for line in lines:
        # 检测包含 FAIL、ERROR 或 assert 关键字的行
        if "FAIL" in line or "ERROR" in line or "assert" in line.lower():
            # 进入失败区域标记
            in_failure = True
        # 如果当前处于失败区域
        if in_failure:
            # 将该行加入失败列表
            failures.append(line)
            # 遇到空行表示一个失败块结束
            if line.strip() == "":
                # 退出失败区域标记
                in_failure = False
    # 如果没有捕获到任何失败行，则显示最后 40 行（摘要区域）
    if not failures:
        failures = lines[-40:]
    # 返回提取的失败行列表
    return failures


# 当脚本直接运行时执行以下代码
if __name__ == "__main__":
    # 获取命令行参数
    args = sys.argv[1:]
    # 自动检测测试框架
    framework = find_test_framework()
    # 打印当前使用的测试框架
    print(f"\n[{framework}] Running tests...\n")
    # 根据检测结果选择对应的运行函数
    if framework == "pytest":
        # 使用 pytest 运行测试
        result = run_pytest(args)
    else:
        # 使用 unittest 运行测试
        result = run_unittest(args)
    # 获取测试标准输出
    output = result["output"]
    # 获取测试标准错误
    stderr = result["stderr"]
    # 将输出按换行符分割，用于统计行数
    lines = output.split("\n")
    # 记录总行数
    total = len(lines)
    # 总是打印完整输出，超过 80 行则截取最后 80 行
    # 如果输出超过 80 行
    if total > 80:
        # 打印行数提示信息
        print(f"({total} lines total, showing last 80)\n")
        # 只显示最后 80 行
        print("\n".join(lines[-80:]))
    else:
        # 行数不多，直接打印全部输出
        print(output)
    # 如果有标准错误输出则打印
    if stderr:
        # 打印标准错误内容
        print(f"\n[stderr]\n{stderr}")
    # 判断测试是否全部通过
    if result["success"]:
        # 打印全部通过提示
        print(f"\n  All tests passed!")
    else:
        # 提取失败用例的关键信息
        failures = extract_failures(output)
        # 如果有失败信息
        if failures:
            # 打印关键失败标题
            print(f"\n  Key failures:")
            # 遍历前 20 条失败信息并打印
            for fl in failures[:20]:
                print(f"    {fl}")
    # 以测试进程的实际返回码退出
    sys.exit(result["returncode"])
