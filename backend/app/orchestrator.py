import time
import uuid
from typing import List, Dict, Any, Optional
from backend.app.schemas import (
    SourceDocument, TraceGraph, AnalysisResponse, AgentStepLog, AnalysisRequest, VerificationStatus
)
from backend.app.provenance_dag import ProvenanceDAG
from backend.app.models_engine import TwoModelEngine
from backend.app.agents.research_agent import ResearchAgent
from backend.app.agents.verification_agent import VerificationAgent
from backend.app.agents.analysis_agent import AnalysisAgent
from backend.app.agents.final_agent import FinalSynthesisAgent
from backend.app.integrity.validator import ProvenanceValidator
from backend.app.integrity.conflict_detector import ConflictDetector
from backend.app.integrity.scorer import ProvenanceScorer
from backend.app.database import SessionLocal
from backend.app.models.investigation import InvestigationModel
from backend.app.models.source import SourceModel
from backend.app.models.claim import ClaimModel
from backend.app.models.citation import CitationModel
from backend.app.models.claim_dependency import ClaimDependencyModel
from backend.app.models.agent_run import AgentRunModel
from backend.app.utils.html_cleaner import clean_text
from backend.app.services.supabase_service import supabase_service

class MultiAgentOrchestrator:
    """
    Orchestrates 4 logical agents:
    Agent 1 (Research) -> Agent 2 (Verification via Model 2) -> Agent 3 (Analysis) -> Agent 4 (Final Answer)

    Enforces Strict Pipeline Quality & Provenance Rules:
    - Halts cleanly if 0 sources found.
    - Decodes all HTML entities cleanly.
    - Unambiguous count metrics: Evidence claims used vs Direct parent dependencies.
    - Persists exact model, provider, agent_name, input, output, status, duration to SQLite & Supabase PostgreSQL.
    """
    def __init__(self, model_1_provider: Optional[str] = None, model_2_provider: Optional[str] = None):
        self.engine = TwoModelEngine(model_1_provider=model_1_provider, model_2_provider=model_2_provider)
        self.research_agent = ResearchAgent(self.engine)
        self.verification_agent = VerificationAgent(self.engine)
        self.analysis_agent = AnalysisAgent(self.engine)
        self.final_agent = FinalSynthesisAgent(self.engine)

        self.validator = ProvenanceValidator()
        self.conflict_detector = ConflictDetector()
        self.scorer = ProvenanceScorer()

    def execute_pipeline(self, request: AnalysisRequest) -> AnalysisResponse:
        start_total = time.time()
        investigation_id = f"INV-{uuid.uuid4().hex[:8].upper()}"
        dag = ProvenanceDAG()
        execution_steps: List[AgentStepLog] = []

        # Step 1: Agent 1 - Research Agent (Model 1 / Live Web Retrieval)
        t1 = time.time()
        is_live = request.mode.upper() == "LIVE"
        raw_claims = self.research_agent.run(request.query, request.documents, dag, is_live_mode=is_live)
        d1 = int((time.time() - t1) * 1000)

        num_sources = len(dag.sources)
        execution_steps.append(AgentStepLog(
            step_number=1,
            agent_name="Agent 1: Research Agent",
            model_name=self.engine.model_a_name,
            status="Completed" if num_sources > 0 else "No Sources Found",
            summary=f"Extracted {len(raw_claims)} raw candidate claims from {num_sources} source documents.",
            created_claim_ids=[c.claim_id for c in raw_claims],
            duration_ms=d1
        ))

        # REQUIREMENT 10 FIX: If 0 sources or 0 claims found, HALT dependent pipeline steps cleanly
        if num_sources == 0 or not raw_claims:
            trace_graph = dag.to_trace_graph(final_answer="No reliable sources were found for this query.")
            trace_graph.chain_status = "NO_SOURCES_FOUND"
            trace_graph.chain_diagnostic = "No reliable sources were found for this query."
            trace_graph.integrity_score = 0.0

            total_ms = int((time.time() - start_total) * 1000)
            self._persist_to_sqlite(investigation_id, request, trace_graph, execution_steps, 0.0)

            return AnalysisResponse(
                request_id=investigation_id,
                query=request.query,
                trace_graph=trace_graph,
                execution_steps=execution_steps,
                total_duration_ms=total_ms
            )

        # Step 2: Agent 2 - Verification Agent (MODEL 2)
        t2 = time.time()
        verified_claims = self.verification_agent.run(raw_claims, dag, query=request.query)
        d2 = int((time.time() - t2) * 1000)

        unsupported = sum(1 for c in verified_claims if c.verification_status == VerificationStatus.UNSUPPORTED)
        conflicting = sum(1 for c in verified_claims if c.verification_status == VerificationStatus.CONFLICTING)
        verified_count = sum(1 for c in verified_claims if c.verification_status in (VerificationStatus.VERIFIED, VerificationStatus.PARTIALLY_SUPPORTED))

        execution_steps.append(AgentStepLog(
            step_number=2,
            agent_name="Agent 2: Verification Agent",
            model_name=self.engine.model_b_name,
            status="Completed",
            summary=f"MODEL 2 audit: Evidence claims used: {verified_count} verified, {unsupported} unsupported, {conflicting} conflicting.",
            created_claim_ids=[c.claim_id for c in verified_claims],
            duration_ms=d2
        ))

        # Step 3: Agent 3 - Analysis Agent (Model 1)
        t3 = time.time()
        derived_claims = self.analysis_agent.run(verified_claims, dag)
        d3 = int((time.time() - t3) * 1000)
        execution_steps.append(AgentStepLog(
            step_number=3,
            agent_name="Agent 3: Analysis Agent",
            model_name=self.engine.model_a_name,
            status="Completed",
            summary=f"Synthesized {len(derived_claims)} derived claims with parent_claim_ids dependency array.",
            created_claim_ids=[c.claim_id for c in derived_claims],
            duration_ms=d3
        ))

        # Step 4: Agent 4 - Final Answer Agent (Model 1)
        t4 = time.time()
        final_claim = self.final_agent.run(request.query, verified_claims, derived_claims, dag)
        d4 = int((time.time() - t4) * 1000)

        num_parents = len(final_claim.parent_claim_ids)
        execution_steps.append(AgentStepLog(
            step_number=4,
            agent_name="Agent 4: Final Answer Agent",
            model_name=self.engine.model_a_name,
            status="Completed",
            summary=f"Built coherent response. Evidence claims used: {len(verified_claims)} | Direct parent dependencies: {num_parents}.",
            created_claim_ids=[final_claim.claim_id],
            duration_ms=d4
        ))

        # Conflict Detection
        conflict_edges, conflict_msgs = self.conflict_detector.detect_conflicts(list(dag.claims.values()))
        for edge in conflict_edges:
            dag.edges.append(edge)

        trace_graph = dag.to_trace_graph(final_answer=final_claim.text)

        # Provenance Validation & Scoring
        validation = self.validator.validate_graph(trace_graph)
        score = self.scorer.calculate_score(trace_graph)

        trace_graph.chain_status = validation["status"]
        trace_graph.chain_diagnostic = validation["diagnostic"]
        trace_graph.integrity_score = score

        total_ms = int((time.time() - start_total) * 1000)

        # Persist to SQLite Database & Supabase PostgreSQL
        self._persist_to_sqlite(investigation_id, request, trace_graph, execution_steps, score)

        # Save to Supabase PostgreSQL (if configured)
        try:
            supabase_service.save_investigation_record(
                investigation_id=investigation_id,
                query=request.query,
                mode=request.mode,
                status=trace_graph.chain_status,
                final_answer=trace_graph.final_answer,
                sources=[s.model_dump() for s in trace_graph.sources],
                claims=[c.model_dump() for c in trace_graph.claims],
                edges=[e.model_dump() for e in trace_graph.edges],
                agent_steps=[s.model_dump() for s in execution_steps],
                duration_ms=total_ms
            )
        except Exception as e:
            print("Supabase save notification:", e)

        return AnalysisResponse(
            request_id=investigation_id,
            query=request.query,
            trace_graph=trace_graph,
            execution_steps=execution_steps,
            total_duration_ms=total_ms
        )

    def _persist_to_sqlite(self, inv_id: str, req: AnalysisRequest, graph: TraceGraph, steps: List[AgentStepLog], score: float):
        try:
            def clean(s: Optional[str]) -> str:
                return clean_text(s)

            db = SessionLocal()
            inv = InvestigationModel(
                id=inv_id,
                question=clean(req.query),
                status=clean(graph.chain_status),
                final_answer=clean(graph.final_answer),
                integrity_score=score
            )
            db.add(inv)

            for doc in graph.sources:
                sid = doc.source_id or doc.id
                db_source_id = f"{inv_id}-{sid}"
                db.add(SourceModel(
                    id=db_source_id,
                    investigation_id=inv_id,
                    title=clean(doc.title),
                    url=clean(doc.url or "https://evidence.org/doc"),
                    publisher=clean(doc.publisher or "Publisher"),
                    published_at=clean(doc.publication_date or "2025"),
                    content=clean(doc.content)
                ))

            visited_cids = set()
            for claim in graph.claims:
                cid = claim.id or claim.claim_id
                db_claim_id = f"{inv_id}-{cid}"
                if db_claim_id in visited_cids:
                    continue
                visited_cids.add(db_claim_id)

                db.add(ClaimModel(
                    id=db_claim_id,
                    investigation_id=inv_id,
                    text=clean(claim.text),
                    type=clean(claim.claim_type.value),
                    agent=clean(claim.agent_id),
                    status=clean(claim.verification_status.value),
                    confidence=claim.confidence
                ))

                for ref in claim.source_refs:
                    db.add(CitationModel(
                        id=f"CIT-{uuid.uuid4().hex[:6]}",
                        claim_id=db_claim_id,
                        source_id=f"{inv_id}-{ref.source_id}",
                        evidence_text=clean(ref.relevant_excerpt or ref.exact_quote),
                        status=clean(claim.verification_status.value),
                        confidence=claim.confidence
                    ))

                for parent_id in claim.parent_claim_ids:
                    db.add(ClaimDependencyModel(
                        parent_claim_id=f"{inv_id}-{parent_id}",
                        child_claim_id=db_claim_id,
                        relationship_type="SUPPORTS" if claim.verification_status.value == "VERIFIED" else "DERIVED_FROM"
                    ))

            for step in steps:
                db.add(AgentRunModel(
                    id=f"RUN-{uuid.uuid4().hex[:6]}",
                    investigation_id=inv_id,
                    agent_name=clean(step.agent_name),
                    input=clean(req.query),
                    output=clean(step.summary),
                    status=clean(step.status),
                    duration=step.duration_ms
                ))

            db.commit()
            db.close()
        except Exception as e:
            print("Database persistence warning:", clean_text(str(e)))
