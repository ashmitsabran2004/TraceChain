import React, { useMemo } from 'react';
import { ReactFlow, Background, Controls, MiniMap, Handle, Position } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { FileText, CheckCircle2, AlertTriangle, XCircle, Sparkles, Layers, ArrowRight, ShieldCheck, ShieldAlert } from 'lucide-react';

// Custom Node Components
const SourceNode = ({ data }) => (
  <div className="bg-slate-900 border-2 border-cyan-800 rounded-lg p-2.5 w-52 shadow-lg hover:border-cyan-400">
    <Handle type="source" position={Position.Right} className="w-2.5 h-2.5 bg-cyan-400" />
    <div className="flex items-center gap-1.5 mb-1">
      <FileText className="w-3.5 h-3.5 text-cyan-400" />
      <span className="text-[11px] font-bold text-slate-100 truncate">{data.title}</span>
    </div>
    <span className="text-[9px] font-mono text-slate-400 bg-slate-950 px-1.5 py-0.5 rounded">{data.id}</span>
    <p className="text-[10px] text-slate-400 italic line-clamp-2 mt-1">"{data.content}"</p>
  </div>
);

const ClaimNode = ({ data }) => {
  const isContradicted = data.status === 'CONFLICTING' || data.status === 'CONTRADICTED';
  const isUnsupported = data.status === 'UNSUPPORTED' || data.status === 'BROKEN';
  const isVerified = data.status === 'VERIFIED';

  const borderClass = isContradicted ? 'border-rose-600 bg-rose-950/40 ring-1 ring-rose-500/50' :
                      isUnsupported ? 'border-amber-500 bg-amber-950/40 ring-1 ring-amber-400/50' :
                      isVerified ? 'border-emerald-600 bg-slate-900' : 'border-slate-700 bg-slate-900';

  return (
    <div className={`border-2 rounded-lg p-2.5 w-56 shadow-lg transition-all ${borderClass}`}>
      <Handle type="target" position={Position.Left} className="w-2.5 h-2.5 bg-purple-400" />
      <div className="flex items-center justify-between gap-1 mb-1">
        <span className="text-[10px] font-mono font-bold text-slate-200 bg-slate-950 px-1.5 py-0.5 rounded">{data.id}</span>
        <span className="text-[9px] font-mono text-slate-400">{data.agent}</span>
      </div>
      <p className="text-[10px] text-slate-200 font-medium line-clamp-3 mb-1.5">{data.text}</p>
      <div className="flex items-center justify-between text-[9px]">
        {isContradicted && <span className="text-rose-400 font-bold flex items-center gap-0.5"><XCircle className="w-3 h-3" /> CONFLICTING</span>}
        {isUnsupported && <span className="text-amber-400 font-bold flex items-center gap-0.5"><AlertTriangle className="w-3 h-3" /> UNSUPPORTED</span>}
        {isVerified && <span className="text-emerald-400 font-bold flex items-center gap-0.5"><CheckCircle2 className="w-3 h-3" /> VERIFIED</span>}
        {!isContradicted && !isUnsupported && !isVerified && <span className="text-slate-400">UNVERIFIED</span>}
      </div>
      <Handle type="source" position={Position.Right} className="w-2.5 h-2.5 bg-cyan-400" />
    </div>
  );
};

const nodeTypes = {
  sourceNode: SourceNode,
  claimNode: ClaimNode
};

export default function ProvenanceGraph({ traceGraph, selectedNodeId, onSelectNode, ancestorIds }) {
  if (!traceGraph || (!traceGraph.sources.length && !traceGraph.claims.length)) {
    return (
      <div className="flex flex-col items-center justify-center h-80 bg-slate-900/60 rounded-xl border border-slate-800 p-8 text-center">
        <Layers className="w-12 h-12 text-slate-600 mb-3 animate-pulse" />
        <p className="text-slate-400 font-medium">No Provenance Graph Generated Yet</p>
        <p className="text-xs text-slate-500 max-w-md mt-1">
          Run an investigation to generate a dynamic React Flow citation DAG.
        </p>
      </div>
    );
  }

  // Convert backend TraceGraph into React Flow nodes & edges
  const { nodes, edges } = useMemo(() => {
    const rfNodes = [];
    const rfEdges = [];

    // Columns x positions
    const colX = { source: 40, raw: 300, verified: 560, derived: 820, final: 1080 };

    // Column counters for y placement
    const colY = { source: 40, raw: 40, verified: 40, derived: 40, final: 40 };

    // Add Source Nodes
    (traceGraph.sources || []).forEach(doc => {
      const sid = doc.source_id || doc.id;
      rfNodes.push({
        id: sid,
        type: 'sourceNode',
        position: { x: colX.source, y: colY.source },
        data: {
          id: sid,
          title: doc.title,
          content: doc.content,
          publisher: doc.publisher
        }
      });
      colY.source += 130;
    });

    // Add Claim Nodes
    (traceGraph.claims || []).forEach(claim => {
      const cid = claim.claim_id || claim.id;
      let colKey = 'raw';
      if (claim.claim_type === 'VERIFIED_CLAIM') colKey = 'verified';
      else if (claim.claim_type === 'DERIVED_CLAIM') colKey = 'derived';
      else if (claim.claim_type === 'FINAL_CLAIM') colKey = 'final';

      rfNodes.push({
        id: cid,
        type: 'claimNode',
        position: { x: colX[colKey], y: colY[colKey] },
        data: {
          id: cid,
          text: claim.text,
          agent: claim.agent_id,
          status: claim.verification_status
        }
      });
      colY[colKey] += 130;
    });

    // Add Edges
    (traceGraph.edges || []).forEach((e, idx) => {
      const isConflict = e.edge_type === 'CONTRADICTS';
      rfEdges.push({
        id: `e-${e.source}-${e.target}-${idx}`,
        source: e.source,
        target: e.target,
        type: 'smoothstep',
        animated: true,
        style: {
          stroke: isConflict ? '#f43f5e' : '#06b6d4',
          strokeWidth: isConflict ? 3 : 2,
          strokeDasharray: isConflict ? '5,5' : '0'
        }
      });
    });

    return { nodes: rfNodes, edges: rfEdges };
  }, [traceGraph]);

  const getChainBadge = (status) => {
    if (status === 'VERIFIED') return <span className="px-3 py-1 rounded-lg bg-emerald-950 text-emerald-300 border border-emerald-800 flex items-center gap-1.5 text-xs font-bold"><ShieldCheck className="w-4 h-4 text-emerald-400" /> ✅ VERIFIED PROVENANCE</span>;
    if (status === 'BROKEN') return <span className="px-3 py-1 rounded-lg bg-amber-950 text-amber-300 border border-amber-800 flex items-center gap-1.5 text-xs font-bold animate-pulse"><ShieldAlert className="w-4 h-4 text-amber-400" /> 🔴 BROKEN PROVENANCE DETECTED</span>;
    if (status === 'CONFLICTING') return <span className="px-3 py-1 rounded-lg bg-rose-950 text-rose-300 border border-rose-800 flex items-center gap-1.5 text-xs font-bold"><XCircle className="w-4 h-4 text-rose-400" /> 🟠 CONFLICTING EVIDENCE</span>;
    return <span className="px-3 py-1 rounded-lg bg-cyan-950 text-cyan-300 border border-cyan-800 flex items-center gap-1.5 text-xs font-bold"><CheckCircle2 className="w-4 h-4 text-cyan-400" /> 🟡 PARTIAL PROVENANCE</span>;
  };

  return (
    <div className="flex flex-col gap-4">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-slate-900/80 p-4 rounded-xl border border-slate-800">
        <div className="flex items-center gap-3">
          <Layers className="w-5 h-5 text-cyan-400" />
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-slate-200">React Flow Citation Provenance DAG</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">DYNAMIC BACKEND GRAPH</span>
            </div>
            <p className="text-xs text-slate-300 mt-0.5">{traceGraph.chain_diagnostic || "Graph rendered dynamically."}</p>
          </div>
        </div>
        <div>
          {getChainBadge(traceGraph.chain_status)}
        </div>
      </div>

      {/* React Flow Graph Canvas */}
      <div className="h-[460px] bg-slate-950 rounded-xl border border-slate-800/80 overflow-hidden relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodeClick={(_, node) => {
            const isSource = traceGraph.sources.some(s => (s.source_id || s.id) === node.id);
            onSelectNode(node.id, isSource ? 'source' : 'claim');
          }}
          fitView
        >
          <Background color="#1e293b" gap={16} size={1} />
          <Controls className="bg-slate-900 border-slate-800 text-white fill-current" />
          <MiniMap nodeColor={() => '#06b6d4'} className="bg-slate-900 border-slate-800" />
        </ReactFlow>
      </div>
    </div>
  );
}
