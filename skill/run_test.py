"""Run tests and report failures with context — pytest / unittest support."""
import sys
import subprocess
import os
import re
import json


def find_test_framework():
    """Detect which test framework is available."""
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
    cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short", "--color=no"]
    if args:
        cmd.extend(args)
    else:
        cmd.append(".")

    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=os.getcwd())
    return {"success": r.returncode == 0, "output": r.stdout, "stderr": r.stderr,
            "returncode": r.returncode}


def run_unittest(args: list) -> dict:
    cmd = [sys.executable, "-m", "unittest", "discover", "-v"]
    if args:
        target = args[0].replace("/", ".").replace("\\", ".").replace(".py", "")
        cmd = [sys.executable, "-m", "unittest", target, "-v"]

    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=os.getcwd())
    return {"success": r.returncode == 0, "output": r.stdout, "stderr": r.stderr,
            "returncode": r.returncode}


def extract_failures(output: str):
    """Extract failure/traceback lines for concise output."""
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

    # Always print full output
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
