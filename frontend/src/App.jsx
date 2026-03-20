import { useState, useEffect } from 'react';
import axios from 'axios';
import { Bot, Play, CheckCircle, XCircle, Loader2 } from 'lucide-react';

const API_BASE = "https://your-render-url-here.onrender.com"; 

export default function App() {
  const [datasets, setDatasets] = useState([]);
  const [selectedDataset, setSelectedDataset] = useState("");
  const [goal, setGoal] = useState("");
  
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [feedback, setFeedback] = useState("");

  // Fetch datasets on load
  useEffect(() => {
    axios.get(`${API_BASE}/api/datasets`).then((res) => {
      setDatasets(res.data.datasets);
      if (res.data.datasets.length > 0) setSelectedDataset(res.data.datasets[0]);
    }).catch(err => console.error("Error fetching datasets:", err));
  }, []);

  const runAgent = async (isRetry = false) => {
    if (!selectedDataset || (!goal && !isRetry)) return;
    setLoading(true);
    setResult(null); // Clear previous results while loading

    const payload = {
      dataset_filename: selectedDataset,
      user_goal: goal,
      // If retrying, pass the feedback and the previous context
      user_feedback: isRetry ? feedback : null,
      previous_code: isRetry ? result?.code : null,
      instance_dir: isRetry ? result?.instance_dir : null
    };

    try {
      const res = await axios.post(`${API_BASE}/api/run_agent`, payload);
      setResult(res.data);
      setFeedback(""); // Clear feedback input on success
    } catch (err) {
      // Safely parse FastAPI's detail array if it exists
      const errorDetail = err.response?.data?.detail;
      const errorMessage = typeof errorDetail === 'object' 
        ? JSON.stringify(errorDetail, null, 2) 
        : errorDetail || err.message;
      alert("Error:\n" + errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-6">
        
        {/* Header */}
        <header className="flex items-center space-x-3 pb-6 border-b border-gray-200">
          <Bot className="w-8 h-8 text-blue-600" />
          <h1 className="text-3xl font-bold tracking-tight">Autonomous Data Analyst</h1>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* LEFT PANEL: Controls */}
          <div className="lg:col-span-1 space-y-6 bg-white p-6 rounded-xl shadow-sm border border-gray-100 h-fit">
            
            <div>
              <label className="block text-sm font-semibold mb-2">1. Select Dataset</label>
              <select 
                className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                value={selectedDataset}
                onChange={(e) => setSelectedDataset(e.target.value)}
              >
                {datasets.map(ds => <option key={ds} value={ds}>{ds}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold mb-2">2. Analytical Goal</label>
              <textarea 
                className="w-full p-3 border border-gray-300 rounded-lg h-32 focus:ring-2 focus:ring-blue-500 outline-none resize-none"
                placeholder="E.g., Drop missing values and plot a correlation heatmap..."
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
              />
            </div>

            <button 
              onClick={() => runAgent(false)}
              disabled={loading || !goal}
              className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-medium rounded-lg flex items-center justify-center transition-colors"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <Play className="w-5 h-5 mr-2" />}
              {loading ? "Agent is thinking..." : "Run Agent"}
            </button>
          </div>

          {/* RIGHT PANEL: Outputs */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Empty State */}
            {!loading && !result && (
              <div className="h-full flex flex-col items-center justify-center text-gray-400 bg-white rounded-xl shadow-sm border border-gray-100 py-20">
                <Bot className="w-16 h-16 mb-4 opacity-20" />
                <p>Awaiting instructions. Formulate a goal and hit run.</p>
              </div>
            )}

            {/* Loading State */}
            {loading && (
              <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100 flex flex-col items-center justify-center animate-pulse py-20">
                <Loader2 className="w-12 h-12 text-blue-500 animate-spin mb-4" />
                <p className="text-gray-500 font-medium">Writing Python code, executing, and analyzing...</p>
              </div>
            )}

            {/* Result State */}
            {result && !loading && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                
                {/* Status Bar */}
                <div className={`px-6 py-4 flex items-center justify-between text-white ${result.status === 'success' ? 'bg-green-600' : 'bg-red-600'}`}>
                  <div className="flex items-center space-x-2 font-semibold">
                    {result.status === 'success' ? <CheckCircle className="w-5 h-5"/> : <XCircle className="w-5 h-5"/>}
                    <span>{result.status === 'success' ? 'Execution Successful' : 'Execution Failed'}</span>
                  </div>
                  <div className="text-sm opacity-90">
                    Cost: ${result.metrics.cost.toFixed(4)} | Tokens: {result.metrics.tokens}
                  </div>
                </div>

                <div className="p-6 space-y-6">
                  
                  {/* Generated Images */}
                  {result.images && result.images.length > 0 && (
                    <div>
                      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">Generated Plots</h3>
                      <div className="grid gap-4">
                        {result.images.map((img, idx) => (
                          <img key={idx} src={`${API_BASE}/${img}`} alt="Generated plot" className="w-full h-auto rounded border border-gray-200" />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Terminal Output */}
                  <div>
                    <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">Terminal Output</h3>
                    <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm font-mono whitespace-pre-wrap">
                      {result.output || "No output returned."}
                    </pre>
                  </div>

                  {/* AI Generated Code */}
                  <div>
                    <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">Executed Python Code</h3>
                    <pre className="bg-gray-50 border border-gray-200 text-gray-800 p-4 rounded-lg overflow-x-auto text-sm font-mono">
                      {result.code}
                    </pre>
                  </div>

                  {/* Logic Feedback Loop (Only show if successful) */}
                  {result.status === 'success' && (
                    <div className="mt-8 pt-6 border-t border-gray-200">
                      <h3 className="font-semibold text-lg mb-2">Did this output solve your problem?</h3>
                      <p className="text-sm text-gray-500 mb-4">If the plot looks wrong or the logic is flawed, tell the agent what to fix.</p>
                      <div className="flex space-x-3">
                        <input 
                          type="text"
                          className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                          placeholder="e.g., Change the bar colors to red and add a grid..."
                          value={feedback}
                          onChange={(e) => setFeedback(e.target.value)}
                        />
                        <button 
                          onClick={() => runAgent(true)}
                          disabled={!feedback}
                          className="px-6 bg-gray-800 hover:bg-gray-900 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors"
                        >
                          Send Feedback
                        </button>
                      </div>
                    </div>
                  )}

                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}