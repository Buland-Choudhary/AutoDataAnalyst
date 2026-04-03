import { useState, useEffect } from 'react';
import axios from 'axios';
import { Bot, Play, CheckCircle, XCircle, Loader2, ChevronDown, ChevronRight } from 'lucide-react';
import { API_BASE, API_ENDPOINTS, SAMPLE_GOALS, UI_TEXT } from './config';

export default function App() {
  const [datasets, setDatasets] = useState([]);
  const [selectedDataset, setSelectedDataset] = useState("");
  const [goal, setGoal] = useState("");
  
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [feedback, setFeedback] = useState("");
  const [imagesExpanded, setImagesExpanded] = useState(false);
  const [terminalExpanded, setTerminalExpanded] = useState(false);
  const [codeExpanded, setCodeExpanded] = useState(true);

  // Fetch datasets on load
  useEffect(() => {
    axios.get(`${API_BASE}${API_ENDPOINTS.datasets}`).then((res) => {
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
      const res = await axios.post(`${API_BASE}${API_ENDPOINTS.runAgent}`, payload);
      setResult(res.data);
      setFeedback(""); // Clear feedback input on success
      setImagesExpanded(false);
      setTerminalExpanded(false);
      setCodeExpanded(true);
    } catch (err) {
      // Safely parse FastAPI's detail array if it exists
      const errorDetail = err.response?.data?.detail;
      const errorMessage = typeof errorDetail === 'object' 
        ? JSON.stringify(errorDetail, null, 2) 
        : errorDetail || err.message;
      alert(UI_TEXT.errorPrefix + errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900 p-4 sm:p-6 lg:p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        
        {/* Header */}
        <header className="flex items-center space-x-3 pb-6 border-b border-slate-200">
          <Bot className="w-8 h-8 text-teal-600" />
          <h1 className="text-3xl font-bold tracking-tight">{UI_TEXT.appTitle}</h1>
        </header>

        {/* TOP ROW: Controls */}
        <section className="bg-white p-5 sm:p-6 rounded-2xl shadow-sm border border-slate-200">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            <div className="lg:col-span-4">
              <label className="block text-sm font-semibold mb-2 text-slate-700">{UI_TEXT.stepSelectDataset}</label>
              <select
                className="w-full p-3 border border-slate-300 rounded-xl bg-slate-50 focus:ring-2 focus:ring-teal-500 focus:border-teal-500 outline-none"
                value={selectedDataset}
                onChange={(e) => setSelectedDataset(e.target.value)}
              >
                {datasets.map((ds) => (
                  <option key={ds} value={ds}>{ds}</option>
                ))}
              </select>
            </div>

            <div className="lg:col-span-8 space-y-3">
              <label className="block text-sm font-semibold text-slate-700">{UI_TEXT.stepGoal}</label>
              <textarea
                className="w-full p-3.5 border border-slate-300 rounded-xl bg-slate-50 min-h-32 focus:ring-2 focus:ring-teal-500 focus:border-teal-500 outline-none resize-y"
                placeholder={UI_TEXT.goalPlaceholder}
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
              />

              <div className="flex flex-wrap gap-2">
                {SAMPLE_GOALS.slice(0, 3).map((sampleGoal) => (
                  <button
                    key={sampleGoal}
                    type="button"
                    className="px-3 py-1.5 text-xs sm:text-sm rounded-full border border-teal-200 bg-teal-50 text-teal-800 hover:bg-teal-100 transition-colors"
                    onClick={() => setGoal(sampleGoal)}
                  >
                    {sampleGoal}
                  </button>
                ))}
              </div>

              <div className="flex justify-end pt-1">
                <button
                  onClick={() => runAgent(false)}
                  disabled={loading || !goal}
                  className="w-full sm:w-auto py-3 px-6 bg-teal-600 hover:bg-teal-700 disabled:bg-teal-300 text-white font-medium rounded-xl flex items-center justify-center transition-colors"
                >
                  {loading ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <Play className="w-5 h-5 mr-2" />}
                  {loading ? UI_TEXT.runningAgent : UI_TEXT.runAgent}
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* OUTPUTS */}
        <div className="space-y-6">
            
            {/* Empty State */}
            {!loading && !result && (
              <div className="h-full flex flex-col items-center justify-center text-slate-500 bg-white rounded-2xl shadow-sm border border-slate-200 py-20">
                <Bot className="w-16 h-16 mb-4 opacity-25" />
                <p>{UI_TEXT.emptyState}</p>
              </div>
            )}

            {/* Loading State */}
            {loading && (
              <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 flex flex-col items-center justify-center animate-pulse py-20">
                <Loader2 className="w-12 h-12 text-teal-500 animate-spin mb-4" />
                <p className="text-slate-500 font-medium">{UI_TEXT.loadingState}</p>
              </div>
            )}

            {/* Result State */}
            {result && !loading && (
              <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                
                {/* Status Bar */}
                <div className={`px-6 py-4 flex items-center justify-between text-white ${result.status === 'success' ? 'bg-emerald-600' : 'bg-rose-600'}`}>
                  <div className="flex items-center space-x-2 font-semibold">
                    {result.status === 'success' ? <CheckCircle className="w-5 h-5"/> : <XCircle className="w-5 h-5"/>}
                    <span>{result.status === 'success' ? UI_TEXT.successStatus : UI_TEXT.failedStatus}</span>
                  </div>
                  <div className="text-sm opacity-90">
                    Cost: ${result.metrics.cost.toFixed(4)} | Tokens: {result.metrics.tokens}
                  </div>
                </div>

                <div className="p-6 space-y-6">
                  
                  {/* Generated Images */}
                  {result.images && result.images.length > 0 && (
                    <section className="rounded-xl border border-slate-200 overflow-hidden">
                      <button
                        type="button"
                        className="w-full px-4 py-3 bg-slate-50 hover:bg-slate-100 transition-colors flex items-center justify-between text-left"
                        onClick={() => setImagesExpanded((prev) => !prev)}
                      >
                        <span className="text-xs font-semibold text-slate-600 uppercase tracking-[0.15em]">
                          {UI_TEXT.generatedPlots} ({result.images.length})
                        </span>
                        {imagesExpanded ? <ChevronDown className="w-4 h-4 text-slate-600" /> : <ChevronRight className="w-4 h-4 text-slate-600" />}
                      </button>
                      {imagesExpanded && (
                        <div className="p-4 grid gap-4 bg-white">
                          {result.images.map((img, idx) => (
                            <img key={idx} src={`${API_BASE}/${img}`} alt="Generated plot" className="w-full h-auto rounded-xl border border-slate-200" />
                          ))}
                        </div>
                      )}
                    </section>
                  )}

                  {/* Terminal Output */}
                  <section className="rounded-xl border border-slate-200 overflow-hidden">
                    <button
                      type="button"
                      className="w-full px-4 py-3 bg-slate-50 hover:bg-slate-100 transition-colors flex items-center justify-between text-left"
                      onClick={() => setTerminalExpanded((prev) => !prev)}
                    >
                      <span className="text-xs font-semibold text-slate-600 uppercase tracking-[0.15em]">{UI_TEXT.terminalOutput}</span>
                      {terminalExpanded ? <ChevronDown className="w-4 h-4 text-slate-600" /> : <ChevronRight className="w-4 h-4 text-slate-600" />}
                    </button>
                    {terminalExpanded && (
                      <div className="p-4 bg-slate-900">
                        <pre className="bg-slate-950 text-slate-100 p-4 rounded-xl overflow-auto text-sm leading-6 font-mono whitespace-pre-wrap border border-slate-800 text-left">
                          {result.output || UI_TEXT.noOutput}
                        </pre>
                      </div>
                    )}
                  </section>

                  {/* AI Generated Code */}
                  <section className="rounded-xl border border-slate-200 overflow-hidden">
                    <button
                      type="button"
                      className="w-full px-4 py-3 bg-slate-50 hover:bg-slate-100 transition-colors flex items-center justify-between text-left"
                      onClick={() => setCodeExpanded((prev) => !prev)}
                    >
                      <span className="text-xs font-semibold text-slate-600 uppercase tracking-[0.15em]">{UI_TEXT.executedCode}</span>
                      {codeExpanded ? <ChevronDown className="w-4 h-4 text-slate-600" /> : <ChevronRight className="w-4 h-4 text-slate-600" />}
                    </button>
                    {codeExpanded && (
                      <div className="p-4 bg-slate-900">
                        <pre className="bg-slate-900 text-slate-100 border border-slate-700 p-4 rounded-xl overflow-auto text-sm leading-6 font-mono whitespace-pre text-left">
                          {result.code}
                        </pre>
                      </div>
                    )}
                  </section>

                  {/* Logic Feedback Loop (Only show if successful) */}
                  {result.status === 'success' && (
                    <div className="mt-8 pt-6 border-t border-slate-200">
                      <h3 className="font-semibold text-lg mb-2">{UI_TEXT.feedbackTitle}</h3>
                      <p className="text-sm text-slate-500 mb-4">{UI_TEXT.feedbackSubtitle}</p>
                      <div className="flex flex-col sm:flex-row gap-3">
                        <input 
                          type="text"
                          className="flex-1 p-3 border border-slate-300 rounded-xl bg-slate-50 focus:ring-2 focus:ring-teal-500 focus:border-teal-500 outline-none"
                          placeholder={UI_TEXT.feedbackPlaceholder}
                          value={feedback}
                          onChange={(e) => setFeedback(e.target.value)}
                        />
                        <button 
                          onClick={() => runAgent(true)}
                          disabled={!feedback}
                          className="px-6 py-3 bg-slate-800 hover:bg-slate-900 disabled:bg-slate-400 text-white font-medium rounded-xl transition-colors"
                        >
                          {UI_TEXT.sendFeedback}
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
  );
}