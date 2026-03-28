import os
import glob
from datetime import datetime
import traceback
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
from backend_config import (
    APP_TITLE,
    DEFAULT_FRONTEND_ORIGINS,
    DATASETS_DIR,
    RUNS_DIR,
    LLM_DEFAULT_MODEL,
    LLM_TEMPERATURE,
    MAX_RETRIES,
    TRACEBACK_TAIL_LINES,
    PROMPT_PRICE_PER_MILLION,
    COMPLETION_PRICE_PER_MILLION,
    SYSTEM_PROMPT,
    TASK_PROMPT_TEMPLATE,
    LOGIC_FEEDBACK_PROMPT_TEMPLATE,
    RETRY_PROMPT_TEMPLATE,
    DATASET_NOT_FOUND_MESSAGE,
    SECURITY_GATE_ERROR_TEMPLATE,
    SUCCESS_MESSAGE,
    FAILED_MESSAGE,
    PROMPT_FILE_NAME,
)

load_dotenv()
client = OpenAI()

app = FastAPI(title=APP_TITLE)


def log_event(level, message, **fields):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    details = " | ".join(f"{key}={value}" for key, value in fields.items())
    print(f"[{timestamp}] [{level}] {message}" + (f" | {details}" if details else ""))

# Configure CORS origins from environment with safe local + deployed defaults
frontend_origins_env = os.getenv("FRONTEND_ORIGINS", DEFAULT_FRONTEND_ORIGINS)
frontend_origins = [origin.strip() for origin in frontend_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the 'runs' directory so the frontend can fetch generated .png plots
os.makedirs(RUNS_DIR, exist_ok=True)
app.mount(f"/{RUNS_DIR}", StaticFiles(directory=RUNS_DIR), name=RUNS_DIR)

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
        log_event(
            "ERROR",
            "Failed to profile dataset",
            csv_path=csv_path,
            error=str(e),
            traceback=traceback.format_exc(),
        )
        return f"Error reading dataset profile: {str(e)}"

def call_llm(system_prompt, user_prompt, model=LLM_DEFAULT_MODEL):
    try:
        log_event("INFO", "Calling OpenAI Chat Completions", model=model)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=LLM_TEMPERATURE
        )
        prompt_tokens = response.usage.prompt_tokens
        comp_tokens = response.usage.completion_tokens
        cost = (prompt_tokens * PROMPT_PRICE_PER_MILLION / 1_000_000) + (
            comp_tokens * COMPLETION_PRICE_PER_MILLION / 1_000_000
        )
        log_event(
            "INFO",
            "OpenAI response received",
            prompt_tokens=prompt_tokens,
            completion_tokens=comp_tokens,
            total_tokens=response.usage.total_tokens,
            turn_cost=f"{cost:.6f}",
        )
        return response.choices[0].message.content, response.usage.total_tokens, cost
    except Exception as e:
        log_event(
            "ERROR",
            "LLM call failed",
            model=model,
            error=str(e),
            traceback=traceback.format_exc(),
        )
        raise Exception(f"LLM Call Failed: {str(e)}")

def prune_traceback(error_string):
    lines = error_string.strip().split('\n')
    return '\n'.join(lines[-TRACEBACK_TAIL_LINES:]) if len(lines) > TRACEBACK_TAIL_LINES else error_string

# --- API Endpoints ---

@app.get("/api/datasets")
async def list_datasets():
    """Returns a list of available CSV files in the datasets folder."""
    datasets = glob.glob(f"{DATASETS_DIR}/*.csv")
    log_event("INFO", "Datasets listed", count=len(datasets))
    return {"datasets": [os.path.basename(d) for d in datasets]}

@app.post("/api/run_agent")
async def run_agent(request: AgentRequest):
    """Executes the agent loop until successful execution or max retries."""
    log_event(
        "INFO",
        "Agent run requested",
        dataset=request.dataset_filename,
        has_feedback=bool(request.user_feedback),
        resumed_instance=bool(request.instance_dir),
    )

    csv_path = os.path.abspath(os.path.join(DATASETS_DIR, request.dataset_filename))
    if not os.path.exists(csv_path):
        log_event("ERROR", "Dataset not found", csv_path=csv_path)
        raise HTTPException(status_code=404, detail=DATASET_NOT_FOUND_MESSAGE)

    # Setup or resume instance directory
    if request.instance_dir and os.path.exists(request.instance_dir):
        instance_dir = request.instance_dir
        log_event("INFO", "Resuming existing instance", instance_dir=instance_dir)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        instance_dir = os.path.join(RUNS_DIR, f"instance_{timestamp}")
        os.makedirs(instance_dir, exist_ok=True)
        log_event("INFO", "Created new run instance", instance_dir=instance_dir)

    profile = get_data_profile(csv_path)
    
    # Handle logic correction vs new task
    if request.user_feedback and request.previous_code:
        current_prompt = LOGIC_FEEDBACK_PROMPT_TEMPLATE.format(
            user_feedback=request.user_feedback,
            previous_code=request.previous_code,
        )
        log_event("INFO", "Building logic-correction prompt")
    else:
        current_prompt = TASK_PROMPT_TEMPLATE.format(
            user_goal=request.user_goal,
            csv_path=csv_path,
            profile=profile,
        )
        log_event("INFO", "Building fresh task prompt")

    total_tokens = 0
    total_cost = 0.0

    for attempt in range(1, MAX_RETRIES + 1):
        attempt_dir = os.path.join(instance_dir, f"attempt_{attempt}")
        os.makedirs(attempt_dir, exist_ok=True)
        log_event("INFO", "Starting attempt", attempt=attempt, max_retries=MAX_RETRIES, attempt_dir=attempt_dir)

        with open(os.path.join(attempt_dir, PROMPT_FILE_NAME), "w") as f:
            f.write(current_prompt)
        
        # 1. Generate Code
        llm_response, tokens, cost = call_llm(SYSTEM_PROMPT, current_prompt)
        total_tokens += tokens
        total_cost += cost
        clean_code = extract_code(llm_response)
        log_event("INFO", "Generated code from LLM", attempt=attempt, code_chars=len(clean_code))
        
        # 2. Execute Code
        log_event("INFO", "Executing generated code", attempt=attempt)
        success, output = execute_script(clean_code, workspace_dir=attempt_dir)
        
        # Find any generated images to return to frontend
        generated_images = glob.glob(os.path.join(attempt_dir, "*.png"))
        image_urls = [img.replace("\\", "/") for img in generated_images] # Format for web
        
        if success:
            log_event(
                "INFO",
                "Attempt succeeded",
                attempt=attempt,
                cumulative_tokens=total_tokens,
                cumulative_cost=f"{total_cost:.6f}",
            )
            return {
                "status": "success",
                "message": SUCCESS_MESSAGE,
                "output": output,
                "code": clean_code,
                "images": image_urls,
                "instance_dir": instance_dir,
                "metrics": {"tokens": total_tokens, "cost": total_cost}
            }
        else:
            log_event("WARN", "Attempt failed", attempt=attempt)
            if "Security Violation" in output:
                log_event("ERROR", "Execution blocked by security gate", attempt=attempt)
                raise HTTPException(
                    status_code=400,
                    detail=SECURITY_GATE_ERROR_TEMPLATE.format(output=output),
                )
            
            # Update prompt for next internal loop iteration
            current_prompt = RETRY_PROMPT_TEMPLATE.format(
                failed_code=clean_code,
                error_traceback=prune_traceback(output),
            )

    log_event(
        "ERROR",
        "Max retries reached",
        max_retries=MAX_RETRIES,
        cumulative_tokens=total_tokens,
        cumulative_cost=f"{total_cost:.6f}",
    )
    return {
        "status": "failed",
        "message": FAILED_MESSAGE,
        "output": output,
        "code": clean_code,
        "instance_dir": instance_dir,
        "metrics": {"tokens": total_tokens, "cost": total_cost}
    }