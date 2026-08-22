from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from backend.app.schemas import (
    AnalysisRequest, AnalysisResponse, EvalMetricResult, SourceDocument
)
from backend.app.orchestrator import MultiAgentOrchestrator
from backend.app.eval.harness import EvaluationHarness
from backend.app.eval.datasets import EVAL_TEST_CASES
from backend.app.database import SessionLocal
from backend.app.models.claim_dependency import ClaimDependencyModel
from backend.app.api.investigations import router as investigations_router
from backend.app.api.claims import router as claims_router
from backend.app.api.graph import router as graph_router
from backend.app.api.investigations import investigations_cache

app = FastAPI(
    title="TraceChain API — Citation Integrity Chains for Multi-Agent AI",
    description="Backend API powering multi-agent provenance tracking, dual-model verification, wrong-claim detection, and evaluation harness.",
    version="1.0.0"
)

# Enable CORS for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://trace-chain-eight.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(investigations_router)
app.include_router(claims_router)
app.include_router(graph_router)

orchestrator = MultiAgentOrchestrator()
eval_harness = EvaluationHarness(orchestrator)

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "system": "TraceChain Multi-Agent Citation Integrity Engine",
        "mock_mode": orchestrator.engine.mock_mode,
        "model_a": orchestrator.engine.model_a_name,
        "model_b": orchestrator.engine.model_b_name,
    }

@app.get("/api/presets")
def get_demo_presets():
    """
    Returns pre-packaged hackathon demo presets.
    Flagship #1: Should NovaTech expand into India? (WOW Demo Centerpiece)
    """
    presets = [
        {
            "id": "preset_wow_novatech",
            "name": "⭐ CENTERPIECE WOW DEMO: Should NovaTech expand into India?",
            "description": "Demonstrates Broken Provenance (CLAIM-017 Unsupported Market Leader Claim -> CLAIM-021 Derived Claim -> Final Answer) & Conflicting Evidence (12% vs 7% Growth Rate).",
            "query": "Should NovaTech expand into India?",
            "documents": EVAL_TEST_CASES[0].documents
        },
        {
            "id": "preset_med_contradiction",
            "name": "🏥 Clinical Trial Contradiction Audit",
            "description": "Exposes subtle factual and numerical contradictions between primary clinical trial data and secondary summaries.",
            "query": "What were the safety and efficacy outcomes of Clinical Trial TX-409?",
            "documents": EVAL_TEST_CASES[1].documents
        }
    ]
    return presets

@app.post("/api/analyze", response_model=AnalysisResponse)
def run_analysis(request: AnalysisRequest):
    """
    Run full 4-stage multi-agent citation provenance pipeline.
    """
    try:
        response = orchestrator.execute_pipeline(request)
        investigations_cache[response.request_id] = response
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/lineage")
def get_claim_lineage(request_id: str, claim_id: str):
    """
    Retrieve upstream ancestor nodes and edges for a specific claim to highlight lineage.
    """
    try:
        db = SessionLocal()
        child_claim_id = f"{request_id}-{claim_id}"
        dependencies = db.query(ClaimDependencyModel).filter(
            ClaimDependencyModel.child_claim_id == child_claim_id
        ).all()
        investigation_prefix = f"{request_id}-"
        ancestor_claim_ids = [
            d.parent_claim_id[len(investigation_prefix):]
            if d.parent_claim_id.startswith(investigation_prefix)
            else d.parent_claim_id
            for d in dependencies
        ]
        db.close()

        return {
            "target_claim_id": claim_id,
            "ancestor_claim_ids": ancestor_claim_ids or [claim_id],
            "ancestor_source_ids": []
        }
    except Exception as e:
        return {"target_claim_id": claim_id, "ancestor_claim_ids": [claim_id], "ancestor_source_ids": []}

@app.post("/api/evaluate", response_model=List[EvalMetricResult])
def run_evaluation():
    """
    Execute evaluation harness benchmarks (20 test cases) and return metrics.
    """
    return eval_harness.run_all_evals()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
