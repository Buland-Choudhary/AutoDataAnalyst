# AutoDataAnalyst: Self-Correcting Data Analyst Agent

## Live Website [Link](https://auto-data-analyst.vercel.app/)

## Overview

AutoDataAnalyst is a full-stack, autonomous AI agent that translates natural language queries into executable Python data analysis pipelines. Built with a robust Read-Eval-Print Loop (REPL) architecture, the system dynamically profiles datasets, writes pandas and matplotlib code, executes it in an isolated sandbox, and self-corrects runtime errors without human intervention.

## Key Architecture & Features

### 1. The Autonomous REPL Engine

- **Dynamic Schema Injection:** Before code generation, the system runs `df.info()` and `df.describe()` to ground the LLM in the actual dataset schema, preventing hallucinated column names and identifying non-standard missing values (e.g., `?`).
- **Self-Correction Loop:** If the generated code crashes, the execution engine captures the standard error (`stderr`), prunes the traceback to save context window tokens, and feeds the specific error back to the LLM to rewrite the script (up to 3 maximum retries).
- **Human-in-the-Loop Logic Validation:** Once code executes successfully, the UI pauses to allow the user to review the generated plots and data. If the logic is flawed (e.g., "Make the bars red instead of blue"), the user provides feedback, and the agent iterates.

### 2. Advanced Security Sandboxing

- **AST Static Analysis Gate:** Replaces manual security checks. Before any AI-generated code is executed, Python's `ast` module parses the script to block malicious system-level imports (`os`, `sys`, `subprocess`) and dangerous functions (`exec`, `eval`).
- **Subprocess Isolation & Timeout:** Code is executed in a completely separate system process with a strict 10-second hard timeout to prevent infinite loops from hanging the server.
- **Non-Root Docker Container:** The FastAPI backend is containerized. If the AI manages to break out of the Python subprocess, it remains trapped in an unprivileged Linux user account with no admin rights.

### 3. Full-Stack Decoupling & Artifact Tracking

- **Artifact Isolation:** Every execution generates a timestamped directory (e.g., `/runs/instance_X/attempt_Y`). The exact prompt, AI script, execution logs (`stdout.txt`/`stderr.txt`), and generated `.png` plots are saved securely within this run folder.
- **Cost & Token Metrics:** The backend precisely calculates OpenAI API token usage and cost (USD) per turn and per instance, surfacing this data to the frontend dashboard.
- **React/Vite Dashboard:** A modern UI that replaces the CLI, allowing users to select datasets, input goals, and view generated images, code, and terminal outputs asynchronously.

## Tech Stack

- **Backend:** Python 3.12, FastAPI, Uvicorn, Pandas, Matplotlib, AST
- **Frontend:** React, Vite, Tailwind CSS, Axios, Lucide React
- **AI & Orchestration:** OpenAI API (`gpt-4o-mini`), Prompt Engineering
- **Deployment & Infrastructure:** Docker, Render (Backend), Vercel (Frontend)

## Configuration-First Editing

If you are experimenting often, edit these files first (instead of changing core logic):

- **Backend config:** `backend_config.py`
  - LLM model, temperature, retry count
  - Prompt templates (system/task/retry/feedback)
  - Token pricing constants and common API messages
  - Security scanner blocklists and execution timeout
- **Frontend config:** `frontend/src/config.js`
  - API base URL fallback and API endpoint paths
  - UI text labels/placeholders/status strings
  - Sample goal strings for reuse

Core runtime files (`api.py`, `execution_engine.py`, `frontend/src/App.jsx`) now consume these config values.

---

## Project Structure

```text
AutoDataAnalyst/
├── api.py                  # FastAPI backend and LLM orchestrator
├── execution_engine.py     # AST scanner, markdown parser, and subprocess runner
├── Dockerfile              # Non-root containerization for secure deployment
├── requirements.txt        # Python backend dependencies
├── .env                    # Environment variables (OPENAI_API_KEY)
├── datasets/               # Directory for target CSV files
│   └── breast-cancer-wisconsin.csv
├── runs/                   # Auto-generated directory for instance isolation and plots
└── frontend/               # React Vite application
   ├── src/
   │   └── App.jsx         # Main dashboard UI
   ├── package.json
   └── tailwind.config.js
```

## Getting Started (Local Development)

### Prerequisites

- Python 3.12+
- Node.js (v18+)
- OpenAI API Key

### Local/Deployed URL Switching (Dynamic)

The project now supports environment-aware URL behavior:

- **Frontend (`frontend/src/App.jsx`)**
  - In local dev (`npm run dev`), it automatically calls: `http://127.0.0.1:8000`
  - In production build/deploy, it defaults to: `https://autodataanalyst.onrender.com`
  - You can override with `frontend/.env.local`:
    ```
    VITE_API_BASE_URL=http://127.0.0.1:8000
    ```

- **Backend CORS (`api.py`)**
  - Reads `FRONTEND_ORIGINS` from `.env` (comma-separated)
  - Default includes both local and deployed frontend origins

### 1. Backend Setup

Clone the repository and set up the isolated Python environment:

```
# Initialize and activate virtual environment
python3 -m venv env
source env/bin/activate


# Install dependencies
pip install -r requirements.txt


# Set up environment variables
cp .env.example .env
# Then edit .env and set OPENAI_API_KEY


# Start the FastAPI server
uvicorn api:app --reload
```

_The backend will be available at `http://127.0.0.1:8000`._

### 2. Frontend Setup

Open a new terminal window and start the React development server:

```
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

_The frontend will be available at `http://localhost:5173`._

## Docker Deployment

To run the backend inside the secure, non-root Docker sandbox:

```
# Build the image
docker build -t autodata-backend .


# Run the container (injecting the .env file)
docker run -d -p 8000:8000 --env-file .env --name autodata-api autodata-backend
```

### Usage

1. Open the React dashboard in your browser.
2. Select a target dataset from the dropdown.
3. Enter an analytical goal (e.g., _"Clean the dataset by replacing '?' with NaN, drop missing values, and plot a correlation heatmap of all features."_).
4. Click Run Agent and watch the system generate code, execute it securely, and render the final analytical artifacts.
