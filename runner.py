# runner.py
import subprocess
import os

def run_command(command: str, working_dir: str) -> dict:
    """
    Runs a shell command in a specified directory and captures the output.
    """
    if not os.path.isdir(working_dir):
        return {"success": False, "output": "Error: Directory does not exist."}

    try:
        # Using shell=True for simplicity in a hackathon context.
        # Be aware of security implications in production.
        process = subprocess.run(
            command,
            cwd=working_dir,
            capture_output=True,
            text=True,
            shell=True,
            timeout=300  # 5-minute timeout to prevent long-running builds
        )

        if process.returncode == 0:
            return {"success": True, "output": process.stdout}
        else:
            return {"success": False, "output": process.stderr}

    except subprocess.TimeoutExpired:
        return {"success": False, "output": "Error: Command timed out."}
    except Exception as e:
        return {"success": False, "output": f"An unexpected error occurred: {str(e)}"}
    
def detect_project_type(path: str) -> str:
    """Detects the project type based on key files."""
    if os.path.exists(os.path.join(path, "package.json")):
        return "nodejs"
    if os.path.exists(os.path.join(path, "requirements.txt")):
        return "python"
    return "unknown"

def check_for_test_files(path: str) -> bool:
    """Scans for common test file or directory patterns."""
    for root, dirs, files in os.walk(path):
        # Check for test directories
        if "tests" in dirs or "test" in dirs or "__tests__" in dirs:
            return True
        # Check for test files
        for file in files:
            if "test" in file or "spec" in file:
                return True
    return False