import subprocess
import os

class Terminal:
    def __init__(self):
        pass
    
    def execute(self, command):
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                cwd=os.getcwd()
            )
            output = result.stdout
            error = result.stderr
            return_code = result.returncode
            
            if return_code == 0:
                return f"Command executed successfully:\n{output}"
            else:
                return f"Command failed with return code {return_code}:\n{error}"
        except Exception as e:
            return f"Error executing command: {str(e)}"