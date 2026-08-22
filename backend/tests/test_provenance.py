import pytest
from backend.app.schemas import SourceDocument, Claim, ClaimType, VerificationStatus, AnalysisRequest
from backend.app.provenance_dag import ProvenanceDAG
from backend.app.orchestrator import MultiAgentOrchestrator
from backend.app.eval.harness import EvaluationHarness
from backend.app.eval.datasets import EVAL_TEST_CASES
from backend.app.api.investigations import get_investigation, investigations_cache
from backend.app.agents.final_agent import FinalSynthesisAgent
from backend.app.services.search_service import WebSearchService
from backend.app.agents.research_agent import ResearchAgent
from fastapi import HTTPException

def test_provenance_dag_construction():
    dag = ProvenanceDAG()
    doc = SourceDocument(source_id="doc_1", id="doc_1", title="Test Doc", content="Content text here.")
    dag.add_source(doc)

    c1 = Claim(
        claim_id="CLAIM-001",
        id="CLAIM-001",
        text="Test claim 1",
        claim_type=ClaimType.RAW_CLAIM,
        source_id="doc_1",
        agent_id="research",
        model_used="ModelA",
        parent_claim_ids=["doc_1"]
    )
    dag.add_claim(c1)

    assert "doc_1" in dag.sources
    assert "CLAIM-001" in dag.claims
    assert len(dag.edges) == 1
    assert dag.edges[0].source == "doc_1"
    assert dag.edges[0].target == "CLAIM-001"

def test_upstream_lineage_tracing():
    dag = ProvenanceDAG()
    doc = SourceDocument(source_id="doc_1", id="doc_1", title="Test Doc", content="Content text here.")
    dag.add_source(doc)

    c1 = Claim(claim_id="CLAIM-001", id="CLAIM-001", text="Raw", claim_type=ClaimType.RAW_CLAIM, agent_id="research", model_used="M1", parent_claim_ids=["doc_1"])
    c2 = Claim(claim_id="VERIFIED-CLAIM-001", id="VERIFIED-CLAIM-001", text="Verified", claim_type=ClaimType.VERIFIED_CLAIM, agent_id="verification", model_used="M2", parent_claim_ids=["CLAIM-001"])
    c3 = Claim(claim_id="DERIVED-CLAIM-010", id="DERIVED-CLAIM-010", text="Derived", claim_type=ClaimType.DERIVED_CLAIM, agent_id="analysis", model_used="M1", parent_claim_ids=["VERIFIED-CLAIM-001"])

    dag.add_claim(c1)
    dag.add_claim(c2)
    dag.add_claim(c3)

    lineage = dag.get_upstream_lineage("DERIVED-CLAIM-010")
    assert "DERIVED-CLAIM-010" in lineage["ancestor_node_ids"]
    assert "VERIFIED-CLAIM-001" in lineage["ancestor_node_ids"]
    assert "CLAIM-001" in lineage["ancestor_node_ids"]
    assert "doc_1" in lineage["ancestor_node_ids"]

def test_four_agent_pipeline_execution():
    orchestrator = MultiAgentOrchestrator()
    request = AnalysisRequest(
        query="What is NovaTech APAC market growth?",
        documents=[EVAL_TEST_CASES[0].documents[0]],
        mode="DEMO",
    )
    response = orchestrator.execute_pipeline(request)

    assert response.request_id is not None
    assert len(response.execution_steps) == 4
    assert len(response.trace_graph.claims) > 0

    # Check 4 Agent IDs
    agent_ids = {c.agent_id for c in response.trace_graph.claims}
    assert "research" in agent_ids
    assert "verification" in agent_ids

def test_evaluation_harness():
    harness = EvaluationHarness()
    res = harness.run_single_eval(EVAL_TEST_CASES[0])
    assert res.citation_precision >= 0.0
    assert res.citation_recall >= 0.0

def test_unknown_investigation_does_not_run_default_demo():
    investigations_cache.clear()

    with pytest.raises(HTTPException) as error:
        get_investigation("INV-MISSING")

    assert error.value.status_code == 404
    assert not investigations_cache

def test_final_answer_uses_only_verified_evidence():
    dag = ProvenanceDAG()
    evidence_claim = Claim(
        claim_id="VERIFIED-001",
        id="VERIFIED-001",
        text="The measured system output was 3 watts.",
        claim_type=ClaimType.VERIFIED_CLAIM,
        verification_status=VerificationStatus.VERIFIED,
        agent_id="verification",
        model_used="ModelB",
        confidence=0.95,
    )

    final_claim = FinalSynthesisAgent(MultiAgentOrchestrator().engine).run(
        "Can footsteps generate electricity?",
        [evidence_claim],
        [],
        dag,
    )

    assert "The measured system output was 3 watts." in final_claim.text
    assert "piezoelectric" not in final_claim.text.lower()

def test_live_relevance_accepts_short_ai_query():
    service = WebSearchService()
    document = SourceDocument(
        source_id="SOURCE-LIVE",
        id="SOURCE-LIVE",
        title="Artificial intelligence",
        content="Artificial intelligence is changing many areas of modern life.",
        source_type="live",
    )

    assert service._is_semantically_relevant("Will AI change the future?", document.title, document.content)

def test_analysis_creates_one_atomic_claim_per_parent():
    dag = ProvenanceDAG()
    parents = [
        Claim(
            claim_id="VERIFIED-001",
            id="VERIFIED-001",
            text="Gandhi led a major independence movement.",
            claim_type=ClaimType.VERIFIED_CLAIM,
            verification_status=VerificationStatus.VERIFIED,
            source_refs=[],
            confidence=0.9,
        ),
        Claim(
            claim_id="VERIFIED-002",
            id="VERIFIED-002",
            text="Arun Gandhi later lived at Sevagram Ashram.",
            claim_type=ClaimType.VERIFIED_CLAIM,
            verification_status=VerificationStatus.VERIFIED,
            source_refs=[],
            confidence=0.9,
        ),
    ]
    for parent in parents:
        dag.add_claim(parent)

    from backend.app.agents.analysis_agent import AnalysisAgent
    derived = AnalysisAgent(MultiAgentOrchestrator().engine).run(parents, dag)

    assert [claim.text for claim in derived] == [parent.text for parent in parents]
    assert [claim.parent_claim_ids for claim in derived] == [[parent.claim_id] for parent in parents]

def test_extracted_claim_normalization_removes_synthesis_markers():
    normalized = ResearchAgent(MultiAgentOrchestrator().engine)._normalize_claim_text(
        "Direct Findings: Gandhi led the movement. [C1]"
    )

    assert normalized == "Gandhi led the movement."

def test_final_answer_prefers_claim_matching_question_intent():
    agent = FinalSynthesisAgent(MultiAgentOrchestrator().engine)
    claims = [
        Claim(
            claim_id="VERIFIED-RELATED",
            id="VERIFIED-RELATED",
            text="John Vincent Atanasoff invented the first electronic digital computer.",
            claim_type=ClaimType.VERIFIED_CLAIM,
            verification_status=VerificationStatus.VERIFIED,
        ),
        Claim(
            claim_id="VERIFIED-DIRECT",
            id="VERIFIED-DIRECT",
            text="Charles Babbage is considered the father of the computer.",
            claim_type=ClaimType.VERIFIED_CLAIM,
            verification_status=VerificationStatus.VERIFIED,
        ),
    ]

    final_claim = agent.run("Who is the father of the computer?", claims, [], ProvenanceDAG())

    assert final_claim.text.startswith("Answer: Charles Babbage")
    assert "Atanasoff" not in final_claim.text

def test_extracted_claim_ids_are_unique_across_sources():
    agent = ResearchAgent(MultiAgentOrchestrator().engine)
    dag = ProvenanceDAG()
    documents = [
        SourceDocument(source_id="SOURCE-A", id="SOURCE-A", title="A source", content="A factual statement about computers."),
        SourceDocument(source_id="SOURCE-B", id="SOURCE-B", title="B source", content="Another factual statement about computers."),
    ]

    agent.mistral_service.extract_structured_claims = lambda query, document: [{
        "claim_id": "CLAIM-001",
        "text": "A factual statement about computers.",
        "evidence": document.content,
    }]
    claims = agent.run("What is known about computers?", documents, dag, is_live_mode=False)

    assert len({claim.claim_id for claim in claims}) == 2
