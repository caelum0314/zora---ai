"""Execute a command and diagnose failures — error → context → AI analysis loop."""
import sys
import subprocess
import os


def run_command(cmd: str, timeout: int = 60) -> dict:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          timeout=timeout, cwd=cwd)
        return {
            "success": r.returncode == 0,
            "stdout": r.stdout,
            "stderr": r.stderr,
            "returncode": r.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": f"Command timed out after {timeout}s", "returncode": -1}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}


if __name__ == "__main__":
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

    timeout = 60
    cmd_value = None
    cwd = os.getcwd()
    cmd_parts = []
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--timeout" and i + 1 < len(sys.argv):
            timeout = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--cmd" and i + 1 < len(sys.argv):
            cmd_value = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--cwd" and i + 1 < len(sys.argv):
            cwd = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--command" and i + 1 < len(sys.argv):
            cmd_value = sys.argv[i + 1]
            i += 2
        else:
            cmd_parts.append(sys.argv[i])
            i += 1

    if cmd_value:
        cmd = cmd_value
    else:
        cmd = " ".join(cmd_parts)

    print(f"Running: {cmd}\n")
    result = run_command(cmd, timeout)

    if result["success"]:
        print("Command succeeded.")
        if result["stdout"]:
            output = result["stdout"]
            lines = output.split("\n")
            if len(lines) > 60:
                print("\n".join(lines[:30]))
                print(f"\n... ({len(lines) - 60} more lines)")
                print("\n".join(lines[-30:]))
            else:
                print(output)
    else:
        print(f"Command FAILED (exit code {result['returncode']})\n")

        if result["stderr"]:
            print(f"[stderr]\n{result['stderr']}\n")

        if result["stdout"]:
            lines = result["stdout"].split("\n")
            if len(lines) > 40:
                print(f"[stdout — last 40 lines]")
                print("\n".join(lines[-40:]))
            else:
                print(f"[stdout]\n{result['stdout']}")

        # Extra context for the AI
        print(f"\n[Diagnosis context for AI analysis]")
        print(f"  Working directory: {os.getcwd()}")
        print(f"  Exit code: {result['returncode']}")
        print(f"  Command: {cmd}")

        # Check if it's a Python traceback
        if "Traceback (most recent call last)" in result["stderr"]:
            trace_lines = result["stderr"].strip().split("\n")
            last = trace_lines[-1] if trace_lines else ""
            print(f"  Error type: Python traceback detected")
            print(f"  Final error: {last}")
            # Find the file:line reference
            for tl in trace_lines:
                if 'File "' in tl:
                    print(f"  Source: {tl.strip()}")
                if tl.strip() and not tl.startswith("File") and not tl.startswith("  "):
                    print(f"  Error: {tl.strip()}")
                    break
