"""测试运行工具 —— 自动检测项目使用的测试框架（pytest/unittest），运行测试并提取失败用例的关键信息。"""
import sys
import subprocess
import os
import re
import json


def find_test_framework():
    """检测当前项目可用的测试框架，优先返回 pytest。"""
    # Check for pytest config files
    for f in ["pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini"]:
        if os.path.exists(f):
            return "pytest"
    # Check if pytest is installed
    try:
        subprocess.run([sys.executable, "-m", "pytest", "--version"],
                       capture_output=True, timeout=5)
        return "pytest"
    except Exception:
        pass
    return "unittest"


def run_pytest(args: list) -> dict:
    """以 pytest 框架运行测试，使用 --tb=short 精简输出。"""
    cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short", "--color=no"]
    if args:
        cmd.extend(args)
    else:
        cmd.append(".")

    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=os.getcwd())
    return {"success": r.returncode == 0, "output": r.stdout, "stderr": r.stderr,
            "returncode": r.returncode}


def run_unittest(args: list) -> dict:
    """以 unittest discover 模式运行测试，将路径转换为模块名。"""
    cmd = [sys.executable, "-m", "unittest", "discover", "-v"]
    if args:
        target = args[0].replace("/", ".").replace("\\", ".").replace(".py", "")
        cmd = [sys.executable, "-m", "unittest", target, "-v"]

    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=os.getcwd())
    return {"success": r.returncode == 0, "output": r.stdout, "stderr": r.stderr,
            "returncode": r.returncode}


def extract_failures(output: str):
    """从测试输出中提取 FAIL/ERROR/assert 相关的失败行，用于简洁展示。"""
    lines = output.split("\n")
    failures = []
    in_failure = False
    for line in lines:
        if "FAIL" in line or "ERROR" in line or "assert" in line.lower():
            in_failure = True
        if in_failure:
            failures.append(line)
            if line.strip() == "":
                in_failure = False
    # If nothing captured, show last 40 lines (summary area)
    if not failures:
        failures = lines[-40:]
    return failures


if __name__ == "__main__":
    args = sys.argv[1:]
    framework = find_test_framework()

    print(f"\n[{framework}] Running tests...\n")

    if framework == "pytest":
        result = run_pytest(args)
    else:
        result = run_unittest(args)

    output = result["output"]
    stderr = result["stderr"]

    # 总是打印完整输出，超过 80 行则截取最后 80 行
    lines = output.split("\n")
    total = len(lines)

    # Print last 80 lines (summary + failures)
    if total > 80:
        print(f"({total} lines total, showing last 80)\n")
        print("\n".join(lines[-80:]))
    else:
        print(output)

    if stderr:
        print(f"\n[stderr]\n{stderr}")

    if result["success"]:
        print(f"\n  All tests passed!")
    else:
        failures = extract_failures(output)
        if failures:
            print(f"\n  Key failures:")
            for fl in failures[:20]:
                print(f"    {fl}")

    sys.exit(result["returncode"])
