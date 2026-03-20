import re
import subprocess
import os

def extract_code(text):
    """
    Step 2.1: Strips markdown backticks from LLM output 
    to isolate the raw Python code.
    """
    # Using string concatenation to avoid breaking the markdown parser
    backticks = "`" * 3
    pattern = backticks + r"(?:python)?(.*?)" + backticks
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    
    # If regex finds markdown blocks, return the inner code. Otherwise, return raw text.
    if match:
        return match.group(1).strip()
    return text.strip()

def execute_script(code_string, workspace_dir="workspace", timeout_seconds=10):
    """
    Steps 2.2 - 2.5: Saves code to a file, runs it securely via subprocess, 
    and catches standard output or tracebacks.
    """
    # Ensure workspace exists
    os.makedirs(workspace_dir, exist_ok=True)
    
    script_path = os.path.join(workspace_dir, "temp_script.py")
    
    # Write the extracted code to the temporary file
    with open(script_path, "w") as f:
        f.write(code_string)
        
    print(f"\n[SYSTEM] Code saved to {script_path}")
    print("--- Generated Code ---")
    print(code_string)
    print("----------------------")
    
    # Step 2.4: Manual Security Gate
    approval = input("\n[SECURITY GATE] Do you want to execute this code? (y/n): ").strip().lower()
    if approval != 'y':
        return False, "Execution aborted by user at the Security Gate."
        
    print("\n[SYSTEM] Executing script...")
    
    # Steps 2.2, 2.3 & 2.5: Subprocess execution with Hard Timeout
    try:
        # Using python3 specifically for your Ubuntu environment
        result = subprocess.run(
            ["python3", script_path], 
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        
        # Check if the process threw a Python traceback
        if result.returncode != 0:
            return False, result.stderr
            
        # Return successful standard output
        return True, result.stdout
        
    except subprocess.TimeoutExpired:
        return False, f"Timeout Error: Script exceeded the {timeout_seconds}-second limit."
    except Exception as e:
        return False, f"System Error: {str(e)}"

# --- Test Block ---
if __name__ == "__main__":
    # A dummy response mimicking what the LLM will eventually return
    # Constructed dynamically to prevent parser issues
    dummy_llm_response = (
        "Here is the code to test your environment:\n"
        + "`" * 3 + "python\n"
        + "import pandas as pd\n"
        + "print('Pandas imported successfully.')\n"
        + "print('Execution Engine is working perfectly.')\n"
        + "`" * 3
    )
    
    print("Testing Phase 2 Engine...")
    clean_code = extract_code(dummy_llm_response)
    success, output = execute_script(clean_code)
    
    if success:
        print("\n✅ Execution Succeeded. Output:\n", output)
    else:
        print("\n❌ Execution Failed. Error:\n", output)