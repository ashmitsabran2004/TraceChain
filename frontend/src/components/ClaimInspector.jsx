import React from 'react';
import { ShieldCheck, AlertTriangle, XCircle, Info, Cpu, UserCheck, Quote, Network, AlertOctagon } from 'lucide-react';

export default function ClaimInspector({ selectedNode, nodeType, onTraceLineage }) {
  if (!selectedNode) {
    return (
      <div className="bg-slate-900/80 rounded-xl border border-slate-800 p-6 flex flex-col items-center justify-center text-center h-full min-h-[300px]">
        <Info className="w-10 h-10 text-slate-600 mb-2" />
        <p className="text-sm font-semibold text-slate-300">Select Any Node in React Flow DAG</p>
        <p className="text-xs text-slate-500 max-w-xs mt-1">
          Click on any node to inspect its exact claim text, ID, agent, status, confidence, evidence, and parent dependencies.
        </p>
      </div>
    );
  }

  if (nodeType === 'source') {
    const doc = selectedNode;
    return (
      <div className="bg-slate-900/90 rounded-xl border border-slate-800 p-5 flex flex-col gap-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <span className="p-2 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/50">📄</span>
            <div>
              <h3 className="text-sm font-bold text-slate-100">{doc.title}</h3>
              <p className="text-xs text-slate-500 font-mono">Source ID: {doc.source_id || doc.id}</p>
            </div>
          </div>
          <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">{doc.publisher || "Publisher"}</span>
          {doc.source_type === "demo" && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-800/80 text-amber-200 font-bold uppercase tracking-wider border border-amber-600/50 ml-1">DEMO</span>
          )}
        </div>

        <div>
          <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Relevant Excerpt</label>
          <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 font-mono text-xs text-slate-300 leading-relaxed max-h-60 overflow-y-auto whitespace-pre-wrap">
            {doc.relevant_excerpt || doc.content}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="p-2.5 rounded bg-slate-800/60 border border-slate-700/50">
            <span className="text-slate-400 block text-[10px]">URL</span>
            <a href={doc.url || "#"} target="_blank" rel="noreferrer" className="font-semibold text-cyan-400 truncate block text-[11px]">
              {doc.url || "https://evidence.org/doc"}
            </a>
          </div>
          <div className="p-2.5 rounded bg-slate-800/60 border border-slate-700/50">
            <span className="text-slate-400 block text-[10px]">PUBLICATION DATE</span>
            <span className="font-semibold text-slate-200">{doc.published_at || doc.publication_date || doc.date || "2025"}</span>
          </div>
        </div>
      </div>
    );
  }

  // Claim Node
  const claim = selectedNode;
  const cid = claim.claim_id || claim.id;
  const isFinalClaim = claim.claim_type === 'FINAL_CLAIM';
  const isContradicted = claim.verification_status === 'CONFLICTING' || claim.verification_status === 'CONTRADICTED';
  const isUnsupported = claim.verification_status === 'UNSUPPORTED' || claim.verification_status === 'BROKEN';
  const isVerified = claim.verification_status === 'VERIFIED';

  return (
    <div className="bg-slate-900/90 rounded-xl border border-slate-800 p-5 flex flex-col gap-4">
      {/* Top Banner */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono px-2 py-1 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/60">{cid}</span>
          <span className="text-xs font-semibold text-slate-300">{claim.claim_type}</span>
          {claim.source_type === "demo" && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-800/80 text-amber-200 font-bold uppercase tracking-wider border border-amber-600/50">DEMO</span>
          )}
        </div>
        <button
          onClick={() => onTraceLineage(cid)}
          className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium shadow-sm transition-all"
        >
          <Network className="w-3.5 h-3.5" /> Trace Lineage
        </button>
      </div>

      {/* SECTION 9: THE "WOW" DEMO CENTERPIECE ALERT */}
      {isUnsupported && (
        <div className="p-4 rounded-xl bg-amber-950/80 border-2 border-amber-500 text-amber-100 flex flex-col gap-2 shadow-lg shadow-amber-950/60 animate-pulse">
          <div className="flex items-center gap-2 text-amber-300 font-bold text-xs uppercase tracking-wider">
            <AlertOctagon className="w-5 h-5 text-amber-400" />
            <span>🔴 BROKEN PROVENANCE DETECTED (CENTERPIECE DEMO)</span>
          </div>
          <p className="text-xs font-semibold text-amber-200 leading-relaxed">
            This claim (or an upstream dependency) is <strong className="text-amber-300 underline">UNSUPPORTED</strong> by source evidence.
          </p>
          <div className="text-[11px] bg-slate-950/80 p-2 rounded border border-amber-800/60 text-amber-300 font-mono">
            {claim.reason || "This final claim depends on an unsupported claim (CLAIM-017)."}
          </div>
        </div>
      )}

      {/* SECTION 10: CONFLICT DETECTION ALERT */}
      {isContradicted && (
        <div className="p-4 rounded-xl bg-rose-950/80 border-2 border-rose-600 text-rose-100 flex flex-col gap-2 shadow-lg shadow-rose-950/60">
          <div className="flex items-center gap-2 text-rose-300 font-bold text-xs uppercase tracking-wider">
            <XCircle className="w-5 h-5 text-rose-400" />
            <span>🟠 CONFLICTING EVIDENCE DETECTED</span>
          </div>
          <p className="text-xs text-rose-200 leading-relaxed">
            {claim.reason || "Source A and Source B state contradictory facts. System preserves uncertainty."}
          </p>
        </div>
      )}

      {isVerified && (
        <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-800/60 text-emerald-300 flex items-center gap-2 text-xs">
          <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{claim.reason || claim.evidence_reasoning || "Verified against evidence source."}</span>
        </div>
      )}

      {/* Claim Text */}
      <div>
        <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
          {isFinalClaim ? 'Final Answer' : 'Claim Statement'}
        </label>
        <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 text-xs font-medium text-slate-100 leading-relaxed">
          {claim.text}
        </div>
      </div>

      {!isFinalClaim && claim.source_refs && claim.source_refs.length > 0 && (
        <div>
          <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Citation</label>
          <div className="flex flex-wrap gap-1.5">
            {claim.source_refs.map((sourceRef, index) => (
              <span key={`${sourceRef.source_id}-${index}`} className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                [C{index + 1}] {sourceRef.source_id}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Parent Claims Dependency Array */}
      {claim.parent_claim_ids && claim.parent_claim_ids.length > 0 && (
        <div>
          <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Parent Claim Dependencies ({claim.parent_claim_ids.length})
          </label>
          <div className="flex flex-wrap gap-1.5">
            {claim.parent_claim_ids.map(pid => (
              <span key={pid} className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-950 text-cyan-400 border border-slate-800">
                {pid}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Evidence Text */}
      {claim.evidence_text && (
        <div>
          <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1">
            <Quote className="w-3 h-3 text-cyan-400" /> Evidence Text
          </label>
          <div className="p-3 rounded-lg bg-slate-950/90 border border-cyan-900/40 text-xs text-slate-300 italic border-l-2 border-cyan-500 pl-2">
            {claim.evidence_text === claim.text && claim.verification_status === 'UNVERIFIED'
              ? 'No sufficient supporting evidence was found.'
              : `"${claim.evidence_text}"`}
          </div>
        </div>
      )}

      {/* Metadata Grid */}
      <div className="grid grid-cols-3 gap-2 text-xs">
        <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
          <span className="text-[10px] text-slate-500 flex items-center gap-1"><UserCheck className="w-3 h-3 text-slate-400" /> AGENT</span>
          <span className="font-semibold text-slate-200 text-[11px] truncate block">{claim.agent_id}</span>
        </div>
        <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
          <span className="text-[10px] text-slate-500 flex items-center gap-1"><Cpu className="w-3 h-3 text-purple-400" /> MODEL</span>
          <span className="font-semibold text-purple-300 text-[11px] truncate block">{claim.model_used ? claim.model_used.split(' ')[0] : 'Model'}</span>
        </div>
        <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
          <span className="text-[10px] text-slate-500 block">CONFIDENCE</span>
          <span className="font-bold text-slate-100 text-[11px]">{(claim.confidence * 100).toFixed(0)}%</span>
        </div>
      </div>
    </div>
  );
}
