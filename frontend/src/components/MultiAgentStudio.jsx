import React, { useState } from 'react';
import { Play, Sparkles, FileText, Globe, Cpu, Clock, Layers, ShieldAlert, CheckCircle2 } from 'lucide-react';

export default function MultiAgentStudio({ presets, onRunAnalysis, isRunning, executionSteps, currentResult }) {
  const [mode, setMode] = useState('LIVE'); // 'LIVE' or 'DEMO'
  const [query, setQuery] = useState('Can footsteps generate electricity?');
  const [documents, setDocuments] = useState([]);
  const [modelAName] = useState('Mistral-Small (Generator)');
  const [modelBName] = useState('Mistral-Large (Verifier)');

  const handleSelectPreset = (preset) => {
    setMode('DEMO');
    setQuery(preset.query);
    setDocuments(preset.documents);
  };

  const handleQuickQuery = (qText) => {
    setMode('LIVE');
    setQuery(qText);
    setDocuments([]);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onRunAnalysis({
      query,
      documents: mode === 'LIVE' ? [] : documents,
      mode,
      model_a_name: modelAName,
      model_b_name: modelBName
    });
  };

  return (
    <div className="flex flex-col gap-5">
      {/* Top Mode Selection Bar */}
      <div className="bg-slate-900/90 rounded-xl border border-slate-800 p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${mode === 'LIVE' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-amber-950 text-amber-400 border border-amber-800'}`}>
            {mode === 'LIVE' ? <Globe className="w-5 h-5" /> : <ShieldAlert className="w-5 h-5" />}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-slate-100">
                {mode === 'LIVE' ? 'LIVE INVESTIGATION MODE' : 'DEMO SCENARIO MODE'}
              </h2>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-semibold ${mode === 'LIVE' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'}`}>
                {mode === 'LIVE' ? 'Using retrieved web sources' : 'Using predefined evidence'}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              {mode === 'LIVE' 
                ? 'Retrieves real web content live for any user question via search + Mistral API.'
                : 'Pre-packaged NovaTech broken provenance centerpiece for hackathon demonstration.'}
            </p>
          </div>
        </div>

        {/* Mode Switcher */}
        <div className="flex items-center gap-2 bg-slate-950 p-1 rounded-lg border border-slate-800">
          <button
            type="button"
            onClick={() => { setMode('LIVE'); setDocuments([]); }}
            className={`px-3 py-1.5 rounded text-xs font-bold transition-all ${
              mode === 'LIVE' ? 'bg-emerald-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            🌐 Live Investigation
          </button>
          <button
            type="button"
            onClick={() => { if (presets && presets[0]) handleSelectPreset(presets[0]); }}
            className={`px-3 py-1.5 rounded text-xs font-bold transition-all ${
              mode === 'DEMO' ? 'bg-amber-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            ⚠️ Demo Scenario
          </button>
        </div>
      </div>

      {/* Quick Live Query Presets */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-xs font-semibold text-slate-400">Try Live Questions:</span>
        <button
          type="button"
          onClick={() => handleQuickQuery("Can footsteps generate electricity?")}
          className="text-xs px-3 py-1 rounded-full bg-slate-900 hover:bg-slate-800 text-cyan-300 border border-slate-800 transition-all"
        >
          ⚡ "Can footsteps generate electricity?"
        </button>
        <button
          type="button"
          onClick={() => handleQuickQuery("How does solar energy storage work?")}
          className="text-xs px-3 py-1 rounded-full bg-slate-900 hover:bg-slate-800 text-cyan-300 border border-slate-800 transition-all"
        >
          ☀️ "How does solar energy storage work?"
        </button>
      </div>

      {/* Main Form */}
      <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Input & Model Info */}
        <div className="bg-slate-900/90 rounded-xl border border-slate-800 p-5 flex flex-col gap-4">
          <div>
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-1.5">
              Research Question
            </label>
            <textarea
              rows={3}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-100 focus:outline-none focus:border-cyan-500 font-medium"
              placeholder="Enter research query (e.g. Can footsteps generate electricity?)..."
              required
            />
          </div>

          <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 flex flex-col gap-2.5">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-purple-400" /> Mistral AI Provider Models
            </span>
            <div className="text-xs flex flex-col gap-2">
              <div className="p-2 rounded bg-slate-900 border border-slate-800 flex items-center justify-between">
                <span className="text-slate-400 text-[10px]">MODEL 1 (Generator)</span>
                <span className="font-semibold text-cyan-400 text-[11px]">{modelAName}</span>
              </div>
              <div className="p-2 rounded bg-slate-900 border border-slate-800 flex items-center justify-between">
                <span className="text-slate-400 text-[10px]">MODEL 2 (Verifier)</span>
                <span className="font-semibold text-purple-400 text-[11px]">{modelBName}</span>
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={isRunning}
            className={`w-full py-3 rounded-lg text-white text-xs font-bold shadow-lg flex items-center justify-center gap-2 transition-all disabled:opacity-50 ${
              mode === 'LIVE'
                ? 'bg-gradient-to-r from-emerald-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 shadow-emerald-600/20'
                : 'bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 shadow-amber-600/20'
            }`}
          >
            {isRunning ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                Executing Pipeline...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" /> {mode === 'LIVE' ? 'Start Live Investigation' : 'Run Demo Scenario'}
              </>
            )}
          </button>
        </div>

        {/* Live Execution Timeline */}
        <div className="lg:col-span-2 bg-slate-900/90 rounded-xl border border-slate-800 p-5 flex flex-col gap-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
              <Layers className="w-4 h-4 text-cyan-400" /> Real-Time Agent Execution Pipeline
            </span>
            {currentResult && (
              <span className="text-xs text-slate-400 font-mono flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-cyan-400" /> Duration: {currentResult.total_duration_ms}ms
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {executionSteps && executionSteps.length > 0 ? (
              executionSteps.map(step => (
                <div key={step.step_number} className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex flex-col gap-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-cyan-400">Step {step.step_number}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                      ✓ Done
                    </span>
                  </div>
                  <h4 className="text-xs font-semibold text-slate-200">{step.agent_name}</h4>
                  <p className="text-[11px] text-slate-400 leading-normal">{step.summary}</p>
                </div>
              ))
            ) : (
              [
                "○ Retrieving sources...",
                "○ Extracting claims...",
                "○ Verifying citations...",
                "○ Generating answer..."
              ].map((label, idx) => (
                <div key={idx} className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs text-slate-500 font-mono">
                  {label}
                </div>
              ))
            )}
          </div>
        </div>
      </form>
    </div>
  );
}
