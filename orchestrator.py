import pandas as pd
import io
import os
from dotenv import load_dotenv
from openai import OpenAI
from execution_engine import extract_code, execute_script

# Load environment variables (API Key) from .env file
load_dotenv()

# Initialize OpenAI Client
# (It automatically looks for os.environ.get("OPENAI_API_KEY"))
client = OpenAI()

# ==========================================
# PHASE 3.1: Data Profiling
# ==========================================
def get_data_profile(csv_path):
    """
    Reads the CSV and generates a statistical profile (schema, missing values, distribution).
    This prevents the LLM from hallucinating column names or misinterpreting data types.
    """
    try:
        df = pd.read_csv(csv_path)
        
        # Capture df.info() which usually prints directly to the console
        buffer = io.StringIO()
        df.info(buf=buffer)
        info_str = buffer.getvalue()
        
        # Capture df.describe() for numerical distribution
        describe_str = df.describe().to_string()
        
        profile = (
            f"--- DATASET INFO ---\n{info_str}\n"
            f"--- DATASET DESCRIPTION ---\n{describe_str}\n"
        )
        return profile
    except Exception as e:
        return f"Error reading dataset profile: {str(e)}"

# ==========================================
# PHASE 3.2 & 3.3: Prompt Engineering
# ==========================================

# The System Prompt strictly defines the persona, boundaries, and formatting rules.
SYSTEM_PROMPT = """You are an expert, autonomous Python Data Analyst.
Your goal is to write clean, efficient, and robust Python code to solve the user's data analysis request.

CRITICAL CONSTRAINTS:
1. You may ONLY use standard Python libraries, `pandas`, and `matplotlib`. Do not import any other third-party libraries.
2. If the user asks for a plot, save it as a '.png' file in the current directory. Do not use plt.show().
3. You must include `assert` statements to validate your logic (e.g., ensure the dataframe is not empty after filtering).
4. Output ONLY executable Python code. No conversational text. No explanations. No markdown formatting or backticks.
"""

def generate_task_prompt(user_goal, csv_path, data_profile):
    """
    Dynamically injects the user's goal and the dataset's schema into the prompt.
    """
    return f"""
USER GOAL: {user_goal}

DATASET PATH: '{csv_path}'
Note: Read the dataset using the path provided above.

DATASET PROFILE:
Below is the output of df.info() and df.describe() for this dataset. 
Pay close attention to column names, data types (Dtype), and non-null counts. 
If a column contains non-standard missing values (like '?'), you MUST write code to handle them (e.g., replace with NaN and drop/impute) before running numerical analysis.

{data_profile}

Write the Python code to achieve the USER GOAL.
"""

# ==========================================
# PHASE 4: The LLM Connection
# ==========================================
def call_llm(system_prompt, user_prompt, model="gpt-4o-mini"):
    """
    Step 4.2: Sends the prompts to the OpenAI API and returns the generated code.
    """
    print(f"\n[SYSTEM] Calling {model}...")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0 # Keep it deterministic for coding tasks
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error calling LLM: {str(e)}"

# ==========================================
# PHASE 5: The Autonomous REPL Loop
# ==========================================
def prune_traceback(error_string):
    """
    Step 5.2: Extracts the last few lines of a traceback to save tokens 
    and focus the LLM on the actual exception.
    """
    lines = error_string.strip().split('\n')
    # Return the last 4 lines which usually contain the specific Exception
    return '\n'.join(lines[-4:]) if len(lines) > 4 else error_string

def generate_correction_prompt(failed_code, error_traceback):
    """
    Step 5.3: Formats the failed code and the pruned error for the LLM to self-correct.
    """
    return f"""
Your previous code failed with an error.

FAILED CODE:
{failed_code}

ERROR MESSAGE:
{error_traceback}

Please fix the code and try again. 
Remember: Output ONLY executable Python code. No markdown formatting.
"""

def autonomous_agent(csv_path, user_goal, max_retries=3):
    """
    Steps 5.1, 5.4, & 5.5: The main loop that manages retries, error feeding, and logic validation.
    """
    print(f"\n🚀 Starting Autonomous Agent for goal: '{user_goal}'")
    print(f"[SYSTEM] Profiling Data...")
    profile = get_data_profile(csv_path)
    
    # Initialize the first prompt
    current_prompt = generate_task_prompt(user_goal, csv_path, profile)
    
    for attempt in range(1, max_retries + 1):
        print(f"\n{'='*40}")
        print(f"--- Attempt {attempt}/{max_retries} ---")
        
        # 1. Generate Code
        llm_response = call_llm(SYSTEM_PROMPT, current_prompt)
        clean_code = extract_code(llm_response)
        
        # 2. Execute Code
        success, output = execute_script(clean_code)
        
        if success:
            print("\n✅ Execution Succeeded!")
            print("Output:\n", output)
            
            # Step 5.5: Manual Logic Validation
            solved = input("\n[LOGIC CHECK] Did this output actually solve your problem? (y/n): ").strip().lower()
            if solved == 'y':
                print("🎉 Agent completed the task successfully!")
                return True
            else:
                feedback = input("Why did it fail or what should it do differently? ")
                print("[SYSTEM] Feeding user feedback back to the LLM...")
                # Repurpose the loop to correct logic errors instead of syntax errors
                current_prompt = (
                    f"The previous code ran without errors, but the user said it did not solve the problem.\n"
                    f"USER FEEDBACK: {feedback}\n\n"
                    f"PREVIOUS CODE:\n{clean_code}\n\n"
                    f"Please rewrite the code to incorporate this feedback."
                )
        else:
            print("\n❌ Execution Failed!")
            
            if "Execution aborted by user" in output:
                print("🛑 Agent stopped by manual security gate.")
                return False
                
            # Step 5.4: Prune traceback and prepare correction prompt
            pruned_error = prune_traceback(output)
            print(f"[SYSTEM] Generating correction prompt based on error...")
            current_prompt = generate_correction_prompt(clean_code, pruned_error)
            
    print("\n🚨 Maximum retries reached. Agent failed to complete the task.")
    return False

# --- Test Block ---
if __name__ == "__main__":
    print("Testing Phase 5: Autonomous REPL Loop...\n")
    
    test_csv = "breast-cancer-wisconsin.csv"
    # A slightly harder goal that might require a retry or logic check
    dummy_goal = "Group the data by 'Class' and plot a bar chart showing the average of 'F1' for each class. Save it as 'f1_avg_by_class.png'."
    
    autonomous_agent(test_csv, dummy_goal)