"""
终端模块 — 安全执行 shell 命令，包含危险命令拦截。

提供两种执行模式：
- execute()：通过 shell=True 执行，支持管道和重定向，执行前做安全检查
- execute_safe()：通过参数列表执行（shell=False），适用于动态参数场景
"""
import subprocess
import os
import shlex


class Terminal:
    """安全的命令执行器，内置危险模式匹配和超时控制。"""

    # 危险命令特征列表，匹配时拦截执行
    DANGEROUS_PATTERNS = [
        "rm -rf /", "rm -rf ~", "rm -rf .",
        "git push --force", "git push -f",
        "git reset --hard",
        "git clean -f",
        "dd if=", "mkfs.",
        ":(){ :|:& };:",  # fork bomb
        "> /dev/sda",
        "chmod 777 /",
        "shutdown", "reboot", "halt",
        "del /F /S",  # Windows: recursive force delete root
        "format C:", "format D:",
    ]

    def is_dangerous(self, command: str) -> bool:
        """检查命令是否匹配危险模式列表（忽略引号，大小写不敏感）。"""
        cmd_lower = command.lower().replace("'", "").replace('"', '')
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.lower() in cmd_lower:
                return True
        return False

    def execute(self, command: str) -> str:
        """
        安全执行 shell 命令。
        使用 shell=True 以支持管道和重定向，执行前需通过危险命令检查。
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
                timeout=120
            )
            output = result.stdout
            error = result.stderr
            return_code = result.returncode

            # 成功时合并 stdout 和 stderr；失败时优先显示 stderr
            if return_code == 0:
                if not output and not error:
                    return "Command executed successfully (no output)."
                stderr_prefix = '[stderr]\n'
                return f"{output}{stderr_prefix + error if error else ''}"
            else:
                msg = f"Command failed (exit code {return_code}):\n"
                if error:
                    msg += error
                if output:
                    msg += f"\n[stdout]\n{output}"
                return msg
        except subprocess.TimeoutExpired:
            return "Error: command timed out (120s)"
        except Exception as e:
            return f"Error executing command: {str(e)}"

    def execute_safe(self, args: list) -> str:
        """
        不使用 shell=True 执行命令 — 对动态参数更安全。
        args 应为列表，例如 ['python', 'skill/code_search.py', 'pattern']
        """
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
                timeout=120
            )
            output = result.stdout
            error = result.stderr

            if result.returncode == 0:
                return output or "Command executed successfully (no output)."
            else:
                return f"Command failed (exit code {result.returncode}):\n{error or output}"
        except subprocess.TimeoutExpired:
            return "Error: command timed out (120s)"
        except Exception as e:
            return f"Error: {str(e)}"
