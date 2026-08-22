import React, { useState, useEffect } from 'react';
import { Layers, ShieldCheck, Award, Sparkles, Cpu, AlertTriangle, Network, Info } from 'lucide-react';
import MultiAgentStudio from './components/MultiAgentStudio';
import ProvenanceGraph from './components/ProvenanceGraph';
import ClaimInspector from './components/ClaimInspector';
import EvaluationDashboard from './components/EvaluationDashboard';

export default function App() {
  const [activeTab, setActiveTab] = useState('studio'); // 'studio', 'inspector', 'eval'
  const [presets, setPresets] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [isRunningEval, setIsRunningEval] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [selectedNodeType, setSelectedNodeType] = useState(null);
  const [ancestorIds, setAncestorIds] = useState(new Set());
  const [evalResults, setEvalResults] = useState([]);

  // Fetch presets on load
  useEffect(() => {
    fetchPresets();
  }, []);

  const fetchPresets = async () => {
    try {
      const res = await fetch('/api/presets');
      if (res.ok) {
        const data = await res.json();
        setPresets(data);
      }
    } catch (e) {
      console.error("Failed to fetch presets:", e);
    }
  };

  const handleRunAnalysis = async (requestData) => {
    setIsRunning(true);
    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData)
      });
      if (res.ok) {
        const data = await res.json();
        setAnalysisResult(data);
        // Default select final root claim if present
        const finalClaim = data.trace_graph.claims.find(c => c.claim_type === 'FINAL_CLAIM');
        if (finalClaim) {
          handleSelectNode(finalClaim.id, 'claim', data);
        }
      }
    } catch (e) {
      console.error("Analysis failed:", e);
    } finally {
      setIsRunning(false);
    }
  };

  const handleSelectNode = async (nodeId, type, currentRes = analysisResult) => {
    setSelectedNodeId(nodeId);
    setSelectedNodeType(type);

    if (type === 'claim' && currentRes) {
      try {
        const res = await fetch(`/api/lineage?request_id=${currentRes.request_id}&claim_id=${nodeId}`);
        if (res.ok) {
          const data = await res.json();
          const combined = new Set([...data.ancestor_claim_ids, ...data.ancestor_source_ids]);
          setAncestorIds(combined);
        }
      } catch (e) {
        console.error("Failed to fetch lineage:", e);
      }
    } else {
      setAncestorIds(new Set([nodeId]));
    }
  };

  const handleRunEvaluation = async () => {
    setIsRunningEval(true);
    try {
      const res = await fetch('/api/evaluate', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setEvalResults(data);
      }
    } catch (e) {
      console.error("Evaluation run failed:", e);
    } finally {
      setIsRunningEval(false);
    }
  };

  // Resolve selected node object
  const selectedNodeObject = React.useMemo(() => {
    if (!analysisResult || !selectedNodeId) return null;
    if (selectedNodeType === 'source') {
      return analysisResult.trace_graph.sources.find(s => s.id === selectedNodeId);
    }
    return analysisResult.trace_graph.claims.find(c => c.id === selectedNodeId);
  }, [analysisResult, selectedNodeId, selectedNodeType]);

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      {/* Top Navigation Bar */}
      <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-600 shadow-md shadow-cyan-600/30">
              <Network className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-black tracking-tight text-white">TraceChain</h1>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/60 font-semibold">
                  PROVENANCE DAG ENGINE
                </span>
              </div>
              <p className="text-[11px] text-slate-400">Citation Integrity Chains for Multi-Agent AI</p>
            </div>
          </div>

          {/* Model Badges */}
          <div className="hidden md:flex items-center gap-3 text-xs">
            <div className="px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
              <span className="text-slate-400 text-[10px] font-mono">MODEL A:</span>
              <span className="font-semibold text-cyan-300">Mistral Small</span>
            </div>
            <div className="px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-purple-400"></span>
              <span className="text-slate-400 text-[10px] font-mono">MODEL B:</span>
              <span className="font-semibold text-purple-300">Mistral Large</span>
            </div>
          </div>

          {/* Tab Navigation */}
          <nav className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => setActiveTab('studio')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'studio' ? 'bg-cyan-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Layers className="w-3.5 h-3.5" /> Studio & Live DAG
            </button>
            <button
              onClick={() => setActiveTab('inspector')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'inspector' ? 'bg-cyan-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" /> Audit Inspector
            </button>
            <button
              onClick={() => setActiveTab('eval')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'eval' ? 'bg-cyan-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Award className="w-3.5 h-3.5" /> Evaluation Suite
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 flex flex-col gap-6">
        {activeTab === 'studio' && (
          <div className="flex flex-col gap-6">
            <MultiAgentStudio
              presets={presets}
              onRunAnalysis={handleRunAnalysis}
              isRunning={isRunning}
              executionSteps={analysisResult?.execution_steps}
              currentResult={analysisResult}
            />

            {/* Interactive Provenance Graph & Inspector Split */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <ProvenanceGraph
                  traceGraph={analysisResult?.trace_graph}
                  selectedNodeId={selectedNodeId}
                  onSelectNode={handleSelectNode}
                  ancestorIds={ancestorIds}
                />
              </div>
              <div>
                <ClaimInspector
                  selectedNode={selectedNodeObject}
                  nodeType={selectedNodeType}
                  onTraceLineage={(claimId) => handleSelectNode(claimId, 'claim')}
                />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'inspector' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <ProvenanceGraph
                traceGraph={analysisResult?.trace_graph}
                selectedNodeId={selectedNodeId}
                onSelectNode={handleSelectNode}
                ancestorIds={ancestorIds}
              />
            </div>
            <div>
              <ClaimInspector
                selectedNode={selectedNodeObject}
                nodeType={selectedNodeType}
                onTraceLineage={(claimId) => handleSelectNode(claimId, 'claim')}
              />
            </div>
          </div>
        )}

        {activeTab === 'eval' && (
          <EvaluationDashboard
            evalResults={evalResults}
            onRunEvaluation={handleRunEvaluation}
            isRunningEval={isRunningEval}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 py-3 text-center text-xs text-slate-600">
        TraceChain — Multi-Agent Citation Integrity & Provenance DAG Engine • Hackathon Track: Agents & Automation
      </footer>
    </div>
  );
}
