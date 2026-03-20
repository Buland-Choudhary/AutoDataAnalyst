import os
import glob
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from execution_engine import extract_code, execute_script
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
from typing import Optional

load_dotenv()
client = OpenAI()

app = FastAPI(title="Autonomous Data Analyst API")

# Add this CORS block to allow the frontend to talk to the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace "*" with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the 'runs' directory so the frontend can fetch generated .png plots
os.makedirs("runs", exist_ok=True)
app.mount("/runs", StaticFiles(directory="runs"), name="runs")

# --- Pydantic Models for API Requests ---
class AgentRequest(BaseModel):
    dataset_filename: str
    user_goal: str
    previous_code: Optional[str] = None
    user_feedback: Optional[str] = None
    instance_dir: Optional[str] = None

# --- Core Logic (Adapted from Orchestrator) ---
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
5. To display text, numbers, or dataframes to the user, you MUST use the print() function. Do not evaluate variables at the end of the script like in Jupyter Notebooks.
"""

def call_llm(system_prompt, user_prompt, model="gpt-4o-mini"):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0
        )
        prompt_tokens = response.usage.prompt_tokens
        comp_tokens = response.usage.completion_tokens
        cost = (prompt_tokens * 0.150 / 1_000_000) + (comp_tokens * 0.600 / 1_000_000)
        return response.choices[0].message.content, response.usage.total_tokens, cost
    except Exception as e:
        raise Exception(f"LLM Call Failed: {str(e)}")

def prune_traceback(error_string):
    lines = error_string.strip().split('\n')
    return '\n'.join(lines[-4:]) if len(lines) > 4 else error_string

# --- API Endpoints ---

@app.get("/api/datasets")
async def list_datasets():
    """Returns a list of available CSV files in the datasets folder."""
    datasets = glob.glob("datasets/*.csv")
    return {"datasets": [os.path.basename(d) for d in datasets]}

@app.post("/api/run_agent")
async def run_agent(request: AgentRequest):
    """Executes the agent loop until successful execution or max retries."""
    csv_path = os.path.abspath(os.path.join("datasets", request.dataset_filename))
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Setup or resume instance directory
    if request.instance_dir and os.path.exists(request.instance_dir):
        instance_dir = request.instance_dir
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        instance_dir = os.path.join("runs", f"instance_{timestamp}")
        os.makedirs(instance_dir, exist_ok=True)

    profile = get_data_profile(csv_path)
    
    # Handle logic correction vs new task
    if request.user_feedback and request.previous_code:
        current_prompt = f"The previous code ran without errors, but the user provided this logic feedback: {request.user_feedback}\n\nPREVIOUS CODE:\n{request.previous_code}\n\nRewrite the code to fix the logic."
    else:
        current_prompt = f"USER GOAL: {request.user_goal}\n\nDATASET ABSOLUTE PATH: '{csv_path}'\n(You must use this exact absolute path to load the data).\n\nDATASET PROFILE:\n{profile}\nWrite the Python code to achieve the USER GOAL."

    max_retries = 3
    total_tokens = 0
    total_cost = 0.0

    for attempt in range(1, max_retries + 1):
        attempt_dir = os.path.join(instance_dir, f"attempt_{attempt}")
        os.makedirs(attempt_dir, exist_ok=True)
        
        # 1. Generate Code
        llm_response, tokens, cost = call_llm(SYSTEM_PROMPT, current_prompt)
        total_tokens += tokens
        total_cost += cost
        clean_code = extract_code(llm_response)
        
        # 2. Execute Code
        success, output = execute_script(clean_code, workspace_dir=attempt_dir)
        
        # Find any generated images to return to frontend
        generated_images = glob.glob(os.path.join(attempt_dir, "*.png"))
        image_urls = [img.replace("\\", "/") for img in generated_images] # Format for web
        
        if success:
            return {
                "status": "success",
                "message": "Execution succeeded.",
                "output": output,
                "code": clean_code,
                "images": image_urls,
                "instance_dir": instance_dir,
                "metrics": {"tokens": total_tokens, "cost": total_cost}
            }
        else:
            if "Security Violation" in output:
                raise HTTPException(status_code=400, detail=f"Code blocked by security gate: {output}")
            
            # Update prompt for next internal loop iteration
            current_prompt = f"Your previous code failed with an error.\nFAILED CODE:\n{clean_code}\nERROR MESSAGE:\n{prune_traceback(output)}\nPlease fix the code and try again. Output ONLY executable Python code."

    return {
        "status": "failed",
        "message": "Max retries reached. Agent failed to write executable code.",
        "output": output,
        "code": clean_code,
        "instance_dir": instance_dir,
        "metrics": {"tokens": total_tokens, "cost": total_cost}
    }