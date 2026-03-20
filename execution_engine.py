import re
import subprocess
import os
import ast

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
    dangerous_imports = {'os', 'sys', 'subprocess', 'shutil', 'socket', 'requests', 'urllib', 'pathlib'}
    dangerous_calls = {'exec', 'eval', '__import__'}

    try:
        tree = ast.parse(code_string)
    except SyntaxError as e:
        return False, f"Syntax Error during security scan: {e}"

    for node in ast.walk(tree):
        # Block dangerous module imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split('.')[0] in dangerous_imports:
                    return False, f"Security Violation: Import of '{alias.name}' is strictly blocked."
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split('.')[0] in dangerous_imports:
                return False, f"Security Violation: Import from '{node.module}' is strictly blocked."

        # Block dangerous function calls
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in dangerous_calls:
                    return False, f"Security Violation: Use of '{node.func.id}()' is strictly blocked."

    return True, "Code is safe."

def execute_script(code_string, workspace_dir, timeout_seconds=10):
    """
    Saves code to the attempt folder, runs it securely via subprocess, 
    and saves the outputs/errors to log files.
    """
    os.makedirs(workspace_dir, exist_ok=True)
    
    script_path = os.path.join(workspace_dir, "agent_script.py")
    stdout_log_path = os.path.join(workspace_dir, "stdout.txt")
    stderr_log_path = os.path.join(workspace_dir, "stderr.txt")
    
    print("--- Generated Code ---")
    print(code_string)
    print("----------------------")
    
    # ---------------------------------------------------------
    # AUTOMATED SECURITY GATE (Replaced Manual y/n)
    # ---------------------------------------------------------
    print("\n[SECURITY GATE] Scanning code via AST...")
    is_safe, scan_msg = security_scanner(code_string)
    
    if not is_safe:
        print(f"🛑 [BLOCKED] {scan_msg}")
        with open(stderr_log_path, "w") as f:
            f.write(scan_msg)
        return False, scan_msg
        
    print("✅ [APPROVED] Code passed static analysis.")
    # ---------------------------------------------------------

    with open(script_path, "w") as f:
        f.write(code_string)
        
    print(f"\n[SYSTEM] Executing script inside {workspace_dir}...")
    
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
            with open(stderr_log_path, "w") as f:
                f.write(result.stderr)
            return False, result.stderr
            
        return True, result.stdout
        
    except subprocess.TimeoutExpired:
        error_msg = f"Timeout Error: Script exceeded the {timeout_seconds}-second limit."
        with open(stderr_log_path, "w") as f:
            f.write(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"System Error: {str(e)}"
        with open(stderr_log_path, "w") as f:
            f.write(error_msg)
        return False, error_msg