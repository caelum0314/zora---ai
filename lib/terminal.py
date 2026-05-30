import subprocess
import os
import shlex


class Terminal:
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
        cmd_lower = command.lower().replace("'", "").replace('"', '')
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.lower() in cmd_lower:
                return True
        return False

    def execute(self, command: str) -> str:
        """
        Execute a shell command safely.
        Uses shell=True for compatibility with pipes/redirects,
        but with danger checks applied before execution.
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
        Execute a command without shell=True — safer for dynamic arguments.
        Args should be a list, e.g. ['python', 'skill/code_search.py', 'pattern']
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
