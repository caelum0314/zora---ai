"""执行命令并诊断失败原因 — 错误 → 上下文 → AI 分析闭环。"""
# 导入 sys 模块，用于命令行参数和退出
import sys
# 导入 subprocess 模块，用于创建子进程执行命令
import subprocess
# 导入 os 模块，用于获取当前工作目录等路径操作
import os


# 定义 run_command 函数：在子进程中执行 shell 命令，捕获标准输出、标准错误和返回码
def run_command(cmd: str, timeout: int = 60) -> dict:
    """在子进程中执行 shell 命令，捕获标准输出、标准错误和返回码。"""
    try:
        # 使用 subprocess.run 在 shell 中执行命令，捕获输出和错误
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          timeout=timeout, cwd=cwd)
        # 返回包含执行结果、标准输出、标准错误和返回码的字典
        return {
            "success": r.returncode == 0,
            "stdout": r.stdout,
            "stderr": r.stderr,
            "returncode": r.returncode
        }
    # 捕获命令超时异常
    except subprocess.TimeoutExpired:
        # 返回超时信息和 -1 返回码
        return {"success": False, "stdout": "", "stderr": f"Command timed out after {timeout}s", "returncode": -1}
    # 捕获其他所有异常
    except Exception as e:
        # 返回异常信息和 -1 返回码
        return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}


# 当脚本直接运行时执行以下代码
if __name__ == "__main__":
    # 解析命令行参数：支持 --cmd、--cwd、--timeout、--command 和位置参数
    # 检查是否提供了必要的命令参数
    if len(sys.argv) < 2:
        print("Usage: python skill/diagnose.py <command> [--timeout <seconds>]")
        print()
        print("Runs a command. If it fails, captures the error + relevant info")
        print("so the AI can analyze and suggest fixes.")
        print()
        print("Examples:")
        print("  python skill/diagnose.py 'python main.py'")
        print("  python skill/diagnose.py 'pip install -r requirements.txt' --timeout 120")
        sys.exit(1)

    # 默认超时时间为 60 秒
    timeout = 60
    # 初始化命令字符串变量
    cmd_value = None
    # 默认工作目录为当前目录
    cwd = os.getcwd()
    # 用于收集位置参数拼接为命令
    cmd_parts = []
    # 从索引 1 开始解析命令行参数
    i = 1
    # 遍历所有命令行参数
    while i < len(sys.argv):
        # 如果遇到 --timeout 参数且后面还有值，读取超时时间
        if sys.argv[i] == "--timeout" and i + 1 < len(sys.argv):
            timeout = int(sys.argv[i + 1])
            i += 2
        # 如果遇到 --cmd 参数且后面还有值，读取命令
        elif sys.argv[i] == "--cmd" and i + 1 < len(sys.argv):
            cmd_value = sys.argv[i + 1]
            i += 2
        # 如果遇到 --cwd 参数且后面还有值，读取工作目录
        elif sys.argv[i] == "--cwd" and i + 1 < len(sys.argv):
            cwd = sys.argv[i + 1]
            i += 2
        # 如果遇到 --command 参数且后面还有值，读取命令（与 --cmd 等效）
        elif sys.argv[i] == "--command" and i + 1 < len(sys.argv):
            cmd_value = sys.argv[i + 1]
            i += 2
        # 将无法识别的参数作为命令的一部分收集
        else:
            cmd_parts.append(sys.argv[i])
            i += 1

    # 优先使用通过 --cmd 或 --command 指定的命令
    if cmd_value:
        cmd = cmd_value
    # 否则将位置参数拼接为命令字符串
    else:
        cmd = " ".join(cmd_parts)

    # 打印要执行的命令
    print(f"Running: {cmd}\n")
    # 调用 run_command 执行命令并获取结果
    result = run_command(cmd, timeout)

    # 如果命令执行成功
    if result["success"]:
        print("Command succeeded.")
        # 如果有标准输出，打印输出内容
        if result["stdout"]:
            output = result["stdout"]
            # 将输出按行分割
            lines = output.split("\n")
            # 输出过长时只显示头尾各 30 行，避免刷屏
            if len(lines) > 60:
                print("\n".join(lines[:30]))
                print(f"\n... ({len(lines) - 60} more lines)")
                print("\n".join(lines[-30:]))
            # 输出较短时直接全部打印
            else:
                print(output)
    # 如果命令执行失败
    else:
        print(f"Command FAILED (exit code {result['returncode']})\n")

        # 如果有标准错误输出，打印 stderr 内容
        if result["stderr"]:
            print(f"[stderr]\n{result['stderr']}\n")

        # 如果有标准输出，截取最后部分打印
        if result["stdout"]:
            # 将标准输出按行分割
            lines = result["stdout"].split("\n")
            # 超过 40 行时只显示最后 40 行
            if len(lines) > 40:
                print(f"[stdout — last 40 lines]")
                print("\n".join(lines[-40:]))
            # 行数较少时直接全部打印
            else:
                print(f"[stdout]\n{result['stdout']}")

        # 为 AI 分析提供诊断上下文
        print(f"\n[Diagnosis context for AI analysis]")
        print(f"  Working directory: {os.getcwd()}")
        print(f"  Exit code: {result['returncode']}")
        print(f"  Command: {cmd}")

        # 检测是否为 Python 异常回溯，提取关键错误信息
        if "Traceback (most recent call last)" in result["stderr"]:
            # 将 stderr 按行拆分
            trace_lines = result["stderr"].strip().split("\n")
            # 取最后一行作为最终错误信息
            last = trace_lines[-1] if trace_lines else ""
            print(f"  Error type: Python traceback detected")
            print(f"  Final error: {last}")
            # 定位 traceback 中的文件:行号引用
            for tl in trace_lines:
                # 提取含文件名的行
                if 'File "' in tl:
                    print(f"  Source: {tl.strip()}")
                # 提取错误类型和消息（非文件名行、非代码片段行）
                if tl.strip() and not tl.startswith("File") and not tl.startswith("  "):
                    print(f"  Error: {tl.strip()}")
                    break
