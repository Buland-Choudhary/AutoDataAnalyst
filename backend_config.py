APP_TITLE = "Autonomous Data Analyst API"

DEFAULT_FRONTEND_ORIGINS = (
    "http://localhost:5173,"
    "http://127.0.0.1:5173,"
    "https://auto-data-analyst.vercel.app"
)

DATASETS_DIR = "datasets"
RUNS_DIR = "runs"

LLM_DEFAULT_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE = 0.0
MAX_RETRIES = 3
TRACEBACK_TAIL_LINES = 4

PROMPT_PRICE_PER_MILLION = 0.150
COMPLETION_PRICE_PER_MILLION = 0.600

SYSTEM_PROMPT = """You are an expert, autonomous Python Data Analyst.
Your goal is to write clean, efficient, and robust Python code to solve the user's data analysis request.

CRITICAL CONSTRAINTS:
1. You may ONLY use standard Python libraries, `pandas`, and `matplotlib`. Do not import any other third-party libraries.
2. If the user asks for a plot, save it as a '.png' file in the CURRENT directory. Do not use plt.show() or specify a folder path.
3. You must include `assert` statements to validate your logic.
4. Output ONLY executable Python code. No conversational text. No markdown formatting.
5. To display text, numbers, or dataframes to the user, you MUST use the print() function. Do not evaluate variables at the end of the script like in Jupyter Notebooks.
"""

TASK_PROMPT_TEMPLATE = (
    "USER GOAL: {user_goal}\n\n"
    "DATASET ABSOLUTE PATH: '{csv_path}'\n"
    "(You must use this exact absolute path to load the data).\n\n"
    "DATASET PROFILE:\n{profile}\n"
    "Write the Python code to achieve the USER GOAL."
)

LOGIC_FEEDBACK_PROMPT_TEMPLATE = (
    "The previous code ran without errors, but the user provided this logic feedback: {user_feedback}\n\n"
    "PREVIOUS CODE:\n{previous_code}\n\n"
    "Rewrite the code to fix the logic."
)

RETRY_PROMPT_TEMPLATE = (
    "Your previous code failed with an error.\n"
    "FAILED CODE:\n{failed_code}\n"
    "ERROR MESSAGE:\n{error_traceback}\n"
    "Please fix the code and try again. Output ONLY executable Python code."
)

DATASET_NOT_FOUND_MESSAGE = "Dataset not found"
SECURITY_GATE_ERROR_TEMPLATE = "Code blocked by security gate: {output}"

SUCCESS_MESSAGE = "Execution succeeded."
FAILED_MESSAGE = "Max retries reached. Agent failed to write executable code."

PROMPT_FILE_NAME = "prompt.txt"

EXECUTION_TIMEOUT_SECONDS = 10
DANGEROUS_IMPORTS = {
    "os",
    "sys",
    "subprocess",
    "shutil",
    "socket",
    "requests",
    "urllib",
    "pathlib",
}
DANGEROUS_CALLS = {"exec", "eval", "__import__"}
