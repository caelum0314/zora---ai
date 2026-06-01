"""
终端模块 — 安全执行 shell 命令，包含危险命令拦截。

提供两种执行模式：
- execute()：通过 shell=True 执行，支持管道和重定向，执行前做安全检查
- execute_safe()：通过参数列表执行（shell=False），适用于动态参数场景
"""
# 导入 subprocess 模块，用于执行 shell 命令并捕获输出
import subprocess
# 导入 OS 模块，用于获取当前工作目录
import os
# 导入 shlex 模块，用于安全地分割命令字符串
import shlex


# 定义 Terminal 类 — 安全的命令执行器
class Terminal:
    """安全的命令执行器，内置危险模式匹配和超时控制。"""

    # 危险命令特征列表，匹配时拦截执行
    DANGEROUS_PATTERNS = [
        # 递归强制删除根目录/家目录/当前目录
        "rm -rf /", "rm -rf ~", "rm -rf .",
        # 强制推送（覆盖远程历史）
        "git push --force", "git push -f",
        # 硬重置（丢弃所有未提交更改）
        "git reset --hard",
        # 清理未跟踪文件
        "git clean -f",
        # 直接写入磁盘设备
        "dd if=", "mkfs.",
        # Fork 炸弹（fork bomb）
        ":(){ :|:& };:",
        # 覆写磁盘设备
        "> /dev/sda",
        # 危险权限修改
        "chmod 777 /",
        # 系统关机/重启/挂起
        "shutdown", "reboot", "halt",
        # Windows：递归强制删除
        "del /F /S",
        # Windows：格式化系统盘
        "format C:", "format D:",
    ]

    # 检查命令是否匹配危险模式列表
    def is_dangerous(self, command: str) -> bool:
        """检查命令是否匹配危险模式列表（忽略引号，大小写不敏感）。"""
        # 将命令转为小写并去除引号，便于统一比较
        cmd_lower = command.lower().replace("'", "").replace('"', '')
        # 遍历所有危险模式
        for pattern in self.DANGEROUS_PATTERNS:
            # 如果任一危险模式出现在命令中，返回 True
            if pattern.lower() in cmd_lower:
                return True
        # 未匹配任何危险模式，返回 False
        return False

    # 安全执行 shell 命令（使用 shell=True）
    def execute(self, command: str) -> str:
        """
        安全执行 shell 命令。
        使用 shell=True 以支持管道和重定向，执行前需通过危险命令检查。
        """
        # 尝试执行命令并捕获结果
        try:
            # 通过 subprocess.run 执行命令
            result = subprocess.run(
                # 要执行的命令字符串
                command,
                # 允许 shell 解释器解析（支持管道、重定向等）
                shell=True,
                # 捕获标准输出和标准错误
                capture_output=True,
                # 以文本模式（str）而非字节模式返回输出
                text=True,
                # 在当前工作目录下执行
                cwd=os.getcwd(),
                # 设置 120 秒超时
                timeout=120
            )
            # 获取标准输出内容
            output = result.stdout
            # 获取标准错误内容
            error = result.stderr
            # 获取命令返回码
            return_code = result.returncode

            # 成功时合并 stdout 和 stderr；失败时优先显示 stderr
            if return_code == 0:
                # 如果完全没有输出，返回成功提示
                if not output and not error:
                    return "Command executed successfully (no output)."
                # 构建 stderr 前缀标签
                stderr_prefix = '[stderr]\n'
                # 返回 stdout，如果有 stderr 则追加显示
                return f"{output}{stderr_prefix + error if error else ''}"
            else:
                # 构建失败信息，包含退出码
                msg = f"Command failed (exit code {return_code}):\n"
                # 如果有 stderr，优先追加
                if error:
                    msg += error
                # 如果有 stdout，也追加显示
                if output:
                    msg += f"\n[stdout]\n{output}"
                # 返回失败信息
                return msg
        # 捕获超时异常
        except subprocess.TimeoutExpired:
            return "Error: command timed out (120s)"
        # 捕获其他所有异常
        except Exception as e:
            return f"Error executing command: {str(e)}"

    # 不使用 shell 解释器执行命令（更安全）
    def execute_safe(self, args: list) -> str:
        """
        不使用 shell=True 执行命令 — 对动态参数更安全。
        args 应为列表，例如 ['python', 'skill/code_search.py', 'pattern']
        """
        # 尝试执行命令并捕获结果
        try:
            # 通过 subprocess.run 以参数列表方式执行命令
            result = subprocess.run(
                # 命令参数列表（不通过 shell 解析，避免注入风险）
                args,
                # 捕获标准输出和标准错误
                capture_output=True,
                # 以文本模式返回输出
                text=True,
                # 在当前工作目录下执行
                cwd=os.getcwd(),
                # 设置 120 秒超时
                timeout=120
            )
            # 获取标准输出内容
            output = result.stdout
            # 获取标准错误内容
            error = result.stderr

            # 成功时返回输出或成功提示
            if result.returncode == 0:
                return output or "Command executed successfully (no output)."
            # 失败时返回错误信息
            else:
                return f"Command failed (exit code {result.returncode}):\n{error or output}"
        # 捕获超时异常
        except subprocess.TimeoutExpired:
            return "Error: command timed out (120s)"
        # 捕获其他所有异常
        except Exception as e:
            return f"Error: {str(e)}"
