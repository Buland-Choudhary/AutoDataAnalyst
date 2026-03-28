import re
import subprocess
import os
import ast
from datetime import datetime
import traceback
from backend_config import DANGEROUS_IMPORTS, DANGEROUS_CALLS, EXECUTION_TIMEOUT_SECONDS


def log_event(level, message, **fields):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    details = " | ".join(f"{key}={value}" for key, value in fields.items())
    print(f"[{timestamp}] [{level}] {message}" + (f" | {details}" if details else ""))

def extract_code(text):
    """
    Strips markdown backticks from LLM output to isolate the raw Python code.
    """
    backticks = "`" * 3
    pattern = backticks + r"(?:python)?(.*?)" + backticks
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    
    if match:
        return match.group(1).strip()
    return text.strip()

def security_scanner(code_string):
    """
    Step 2.1: AST Static Analysis Gate.
    Scans the generated code for dangerous imports and function calls before execution.
    """
    try:
        tree = ast.parse(code_string)
    except SyntaxError as e:
        return False, f"Syntax Error during security scan: {e}"

    for node in ast.walk(tree):
        # Block dangerous module imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split('.')[0] in DANGEROUS_IMPORTS:
                    return False, f"Security Violation: Import of '{alias.name}' is strictly blocked."
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split('.')[0] in DANGEROUS_IMPORTS:
                return False, f"Security Violation: Import from '{node.module}' is strictly blocked."

        # Block dangerous function calls
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in DANGEROUS_CALLS:
                    return False, f"Security Violation: Use of '{node.func.id}()' is strictly blocked."

    return True, "Code is safe."

def execute_script(code_string, workspace_dir, timeout_seconds=EXECUTION_TIMEOUT_SECONDS):
    """
    Saves code to the attempt folder, runs it securely via subprocess, 
    and saves the outputs/errors to log files.
    """
    os.makedirs(workspace_dir, exist_ok=True)
    
    script_path = os.path.join(workspace_dir, "agent_script.py")
    stdout_log_path = os.path.join(workspace_dir, "stdout.txt")
    stderr_log_path = os.path.join(workspace_dir, "stderr.txt")
    
    log_event(
        "INFO",
        "Preparing script execution",
        workspace_dir=workspace_dir,
        code_chars=len(code_string),
        timeout_seconds=timeout_seconds,
    )
    
    # ---------------------------------------------------------
    # AUTOMATED SECURITY GATE (Replaced Manual y/n)
    # ---------------------------------------------------------
    log_event("INFO", "Security gate scan started")
    is_safe, scan_msg = security_scanner(code_string)
    
    if not is_safe:
        log_event("ERROR", "Security gate blocked script", reason=scan_msg)
        with open(stderr_log_path, "w") as f:
            f.write(scan_msg)
        return False, scan_msg
        
    log_event("INFO", "Security gate approved script")
    # ---------------------------------------------------------

    with open(script_path, "w") as f:
        f.write(code_string)
        
    log_event("INFO", "Executing script in subprocess", script_path=script_path)
    
    try:
        abs_script_path = os.path.abspath(script_path)
        result = subprocess.run(
            ["python3", abs_script_path], 
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=workspace_dir 
        )
        
        if result.stdout:
            with open(stdout_log_path, "w") as f:
                f.write(result.stdout)
        
        if result.returncode != 0:
            log_event(
                "ERROR",
                "Script exited with non-zero status",
                returncode=result.returncode,
            )
            with open(stderr_log_path, "w") as f:
                f.write(result.stderr)
            return False, result.stderr

        log_event("INFO", "Script execution completed successfully")
        return True, result.stdout
        
    except subprocess.TimeoutExpired:
        error_msg = f"Timeout Error: Script exceeded the {timeout_seconds}-second limit."
        log_event("ERROR", "Script execution timed out", timeout_seconds=timeout_seconds)
        with open(stderr_log_path, "w") as f:
            f.write(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"System Error: {str(e)}"
        log_event(
            "ERROR",
            "Unexpected system error during script execution",
            error=str(e),
            traceback=traceback.format_exc(),
        )
        with open(stderr_log_path, "w") as f:
            f.write(error_msg)
        return False, error_msg