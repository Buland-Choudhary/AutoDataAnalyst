export const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.DEV
    ? "http://127.0.0.1:8000"
    : "https://autodataanalyst.onrender.com");

export const TELEMETRY_CONFIG = {
  enabled: import.meta.env.VITE_TELEMETRY_ENABLED !== 'false',
  notifyBackendUrl:
    import.meta.env.VITE_NOTIFY_BACKEND_URL || 'https://portfolio-rkfu.onrender.com/notify',
  maxNotifyAttempts: Number(import.meta.env.VITE_NOTIFY_MAX_ATTEMPTS || 3),
  notifyRetryDelayMs: Number(import.meta.env.VITE_NOTIFY_RETRY_DELAY_MS || 3000),
};

export const API_ENDPOINTS = {
  datasets: "/api/datasets",
  runAgent: "/api/run_agent",
};

export const SAMPLE_GOALS = [
  "Clean missing values and plot a correlation heatmap.",
  "Group by a categorical column and plot mean values.",
  "Show class distribution with a bar chart.",
];

export const UI_TEXT = {
  appTitle: "Autonomous Data Analyst",
  stepSelectDataset: "1. Select Dataset",
  stepGoal: "2. Analytical Goal",
  goalPlaceholder: "E.g., Drop missing values and plot a correlation heatmap...",
  runAgent: "Run Agent",
  runningAgent: "Agent is thinking...",
  emptyState: "Awaiting instructions. Formulate a goal and hit run.",
  loadingState: "Writing Python code, executing, and analyzing...",
  successStatus: "Execution Successful",
  failedStatus: "Execution Failed",
  generatedPlots: "Generated Plots",
  terminalOutput: "Terminal Output",
  noOutput: "No output returned.",
  executedCode: "Executed Python Code",
  feedbackTitle: "Did this output solve your problem?",
  feedbackSubtitle: "If the plot looks wrong or the logic is flawed, tell the agent what to fix.",
  feedbackPlaceholder: "e.g., Change the bar colors to red and add a grid...",
  sendFeedback: "Send Feedback",
  errorPrefix: "Error:\n",
};
