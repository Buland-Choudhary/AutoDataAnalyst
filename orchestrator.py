import pandas as pd
import io
import os
import glob
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from execution_engine import extract_code, execute_script

load_dotenv()
client = OpenAI()

# ==========================================
# PHASE 3: Data Profiling & Prompts
# ==========================================
def get_data_profile(csv_path):
    try:
        df = pd.read_csv(csv_path)
        buffer = io.StringIO()
        df.info(buf=buffer)
        info_str = buffer.getvalue()
        describe_str = df.describe().to_string()
        return f"--- DATASET INFO ---\n{info_str}\n--- DATASET DESCRIPTION ---\n{describe_str}\n"
    except Exception as e:
        return f"Error reading dataset profile: {str(e)}"

SYSTEM_PROMPT = """You are an expert, autonomous Python Data Analyst.
Your goal is to write clean, efficient, and robust Python code to solve the user's data analysis request.

CRITICAL CONSTRAINTS:
1. You may ONLY use standard Python libraries, `pandas`, and `matplotlib`. Do not import any other third-party libraries.
2. If the user asks for a plot, save it as a '.png' file in the CURRENT directory. Do not use plt.show() or specify a folder path.
3. You must include `assert` statements to validate your logic.
4. Output ONLY executable Python code. No conversational text. No markdown formatting.
"""

def generate_task_prompt(user_goal, absolute_csv_path, data_profile):
    return f"""USER GOAL: {user_goal}\n\nDATASET ABSOLUTE PATH: '{absolute_csv_path}'\n(You must use this exact absolute path to load the data).\n\nDATASET PROFILE:\n{data_profile}\nWrite the Python code to achieve the USER GOAL."""

# ==========================================
# PHASE 4 & 5: LLM & Agent Loop with Cost Tracking
# ==========================================
def call_llm(system_prompt, user_prompt, model="gpt-4o-mini"):
    print(f"\n[SYSTEM] Calling {model}...")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0
        )
        
        # Calculate tokens and cost (Approximate pricing for gpt-4o-mini)
        # Input: $0.150 / 1M tokens | Output: $0.600 / 1M tokens
        prompt_tokens = response.usage.prompt_tokens
        comp_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens
        cost = (prompt_tokens * 0.150 / 1_000_000) + (comp_tokens * 0.600 / 1_000_000)
        
        return response.choices[0].message.content, total_tokens, cost
    except Exception as e:
        return f"Error calling LLM: {str(e)}", 0, 0.0

def prune_traceback(error_string):
    lines = error_string.strip().split('\n')
    return '\n'.join(lines[-4:]) if len(lines) > 4 else error_string

def generate_correction_prompt(failed_code, error_traceback):
    return f"Your previous code failed with an error.\nFAILED CODE:\n{failed_code}\nERROR MESSAGE:\n{error_traceback}\nPlease fix the code and try again. Output ONLY executable Python code."

def autonomous_agent(csv_path, user_goal, instance_dir, max_retries=3):
    print(f"\n🚀 Starting Agent Loop...")
    
    total_instance_tokens = 0
    total_instance_cost = 0.0
    
    # We MUST pass the absolute path so the script can find it no matter what folder it runs in
    abs_csv_path = os.path.abspath(csv_path)
    profile = get_data_profile(abs_csv_path)
    current_prompt = generate_task_prompt(user_goal, abs_csv_path, profile)
    
    for attempt in range(1, max_retries + 1):
        print(f"\n{'='*40}\n--- Attempt {attempt}/{max_retries} ---")
        
        # 1. Setup isolated folder for this specific attempt
        attempt_dir = os.path.join(instance_dir, f"attempt_{attempt}")
        os.makedirs(attempt_dir, exist_ok=True)
        
        # Log the prompt used for this attempt
        with open(os.path.join(attempt_dir, "prompt.txt"), "w") as f:
            f.write(current_prompt)
            
        # 2. Call LLM & Track Costs
        llm_response, tokens, cost = call_llm(SYSTEM_PROMPT, current_prompt)
        total_instance_tokens += tokens
        total_instance_cost += cost
        print(f"[METRICS] Turn Tokens: {tokens} | Turn Cost: ${cost:.6f}")
        
        clean_code = extract_code(llm_response)
        
        # 3. Execute script isolated inside the attempt_dir
        success, output = execute_script(clean_code, workspace_dir=attempt_dir)
        
        if success:
            print("\n✅ Execution Succeeded! Output:\n", output)
            solved = input("\n[LOGIC CHECK] Did this output solve the problem? (y/n): ").strip().lower()
            if solved == 'y':
                print(f"\n🎉 Success! Artifacts saved in: {attempt_dir}")
                print(f"💰 Total Instance Tokens: {total_instance_tokens} | Total Cost: ${total_instance_cost:.6f}")
                return True
            else:
                feedback = input("Why did it fail? What should it do differently? ")
                current_prompt = f"The code ran perfectly, but the user provided this logic feedback: {feedback}\nPREVIOUS CODE:\n{clean_code}\nRewrite the code to incorporate this feedback."
        else:
            print("\n❌ Execution Failed!")
            if "Execution aborted by user" in output: 
                print(f"💰 Total Instance Tokens: {total_instance_tokens} | Total Cost: ${total_instance_cost:.6f}")
                return False
            
            # Prune error and update prompt for the next loop
            current_prompt = generate_correction_prompt(clean_code, prune_traceback(output))
            
    print("\n🚨 Max retries reached.")
    print(f"💰 Total Instance Tokens: {total_instance_tokens} | Total Cost: ${total_instance_cost:.6f}")
    return False

# ==========================================
# PHASE 1: Interactive CLI & Instance Isolation
# ==========================================
def setup_instance_environment():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    instance_dir = os.path.join("runs", f"instance_{timestamp}")
    os.makedirs(instance_dir, exist_ok=True)
    return instance_dir

def interactive_menu():
    print("\n" + "*"*50)
    print("🧠 AUTONOMOUS DATA ANALYST CLI 🧠")
    print("*"*50)

    datasets = glob.glob("datasets/*.csv")
    if not datasets:
        print("❌ No CSV files found in /datasets folder. Please add some datasets.")
        return

    print("\nAvailable Datasets:")
    for i, path in enumerate(datasets):
        print(f"[{i+1}] {os.path.basename(path)}")
    
    ds_idx = int(input("\nSelect a dataset number: ")) - 1
    selected_csv = datasets[ds_idx]

    print(f"\nSelected: {selected_csv}")
    predefined_prompts = [
        "Clean the dataset by handling any non-standard missing values, then plot a correlation heatmap of all numerical features.",
        "Group the data by the most logical categorical column, calculate the mean of all other columns, and plot a bar chart of the result.",
        "Write a custom query..."
    ]
    
    print("\nAnalytical Goals:")
    for i, p in enumerate(predefined_prompts):
        print(f"[{i+1}] {p}")
        
    p_idx = int(input("\nSelect a goal number: ")) - 1
    
    if p_idx == 2:
        selected_goal = input("\nType your custom analytical goal: ")
    else:
        selected_goal = predefined_prompts[p_idx]

    instance_dir = setup_instance_environment()
    print(f"\n[SYSTEM] Run instance initialized at: {instance_dir}")
    autonomous_agent(selected_csv, selected_goal, instance_dir)

if __name__ == "__main__":
    interactive_menu()