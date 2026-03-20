import re
import subprocess
import os

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

def execute_script(code_string, workspace_dir, timeout_seconds=10):
    """
    Saves code to the specific attempt's folder, runs it securely via subprocess 
    (from WITHIN that folder), and saves the outputs/errors to log files.
    """
    # Ensure workspace exists
    os.makedirs(workspace_dir, exist_ok=True)
    
    script_path = os.path.join(workspace_dir, "agent_script.py")
    stdout_log_path = os.path.join(workspace_dir, "stdout.txt")
    stderr_log_path = os.path.join(workspace_dir, "stderr.txt")
    
    # Write the extracted code to the temporary file
    with open(script_path, "w") as f:
        f.write(code_string)
        
    print(f"\n[SYSTEM] Code saved to {script_path}")
    print("--- Generated Code ---")
    print(code_string)
    print("----------------------")
    
    # Manual Security Gate
    approval = input("\n[SECURITY GATE] Do you want to execute this code? (y/n): ").strip().lower()
    if approval != 'y':
        return False, "Execution aborted by user at the Security Gate."
        
    print(f"\n[SYSTEM] Executing script inside {workspace_dir}...")
    
    try:
        # Run process. `cwd=workspace_dir` ensures plots save exactly in this folder.
        # We pass the absolute path to the script to be safe.
        abs_script_path = os.path.abspath(script_path)
        result = subprocess.run(
            ["python3", abs_script_path], 
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=workspace_dir 
        )
        
        # Log outputs
        if result.stdout:
            with open(stdout_log_path, "w") as f:
                f.write(result.stdout)
        
        # Check if the process threw a Python traceback
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