from enum import Enum
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class ClaimType(str, Enum):
    RAW_CLAIM = "RAW_CLAIM"
    VERIFIED_CLAIM = "VERIFIED_CLAIM"
    DERIVED_CLAIM = "DERIVED_CLAIM"
    FINAL_CLAIM = "FINAL_CLAIM"

class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    CONFLICTING = "CONFLICTING"
    UNVERIFIED = "UNVERIFIED"
    IRRELEVANT = "IRRELEVANT"

class SourceRef(BaseModel):
    source_id: str = Field(..., description="ID of the source document")
    title: str = Field(..., description="Title of the source document")
    url: Optional[str] = Field(default="https://evidence.org/doc", description="Source document URL")
    publisher: Optional[str] = Field(default="Market Analytics", description="Publisher organization")
    publication_date: Optional[str] = Field(default="2025-08-01", description="Publication date")
    relevant_excerpt: str = Field(..., description="Relevant source excerpt or snippet")
    exact_quote: str = Field(..., description="Exact textual match from source")
    location: Optional[str] = Field(None, description="Section, page, or line number")

    @classmethod
    def sync_ids(cls, data: Any) -> Any:
        if isinstance(data, dict):
            sid = data.get('source_id') or data.get('id') or 'doc_1'
            data['source_id'] = sid
            data['id'] = sid
        return data

class Claim(BaseModel):
    claim_id: str = Field(..., description="Unique claim identifier")
    id: Optional[str] = Field(None, description="Alias for claim_id")
    claim_text: str = Field(..., description="The claim being made")
    text: Optional[str] = Field(None, description="Alias for claim_text (legacy)")
    claim_type: ClaimType = Field(default=ClaimType.RAW_CLAIM)
    verification_status: VerificationStatus = Field(default=VerificationStatus.UNVERIFIED)
    evidence: List[SourceRef] = Field(default_factory=list)
    source_refs: List[SourceRef] = Field(default_factory=list, description="Source references supporting this claim")
    reasoning: Optional[str] = Field(None, description="Explanation for verification status")
    reason: Optional[str] = Field(None, description="Alias for reasoning (legacy)")
    evidence_text: Optional[str] = Field(None, description="Excerpt of evidence text")
    evidence_reasoning: Optional[str] = Field(None, description="Reasoning chain about evidence")
    source_id: Optional[str] = Field(None, description="Primary source document ID")
    agent_id: Optional[str] = Field(None, description="Agent that generated this claim")
    model_used: Optional[str] = Field(None, description="Model used to generate this claim")
    confidence: Optional[float] = Field(None, description="Confidence score (0.0-1.0)")
    parent_claim_ids: List[str] = Field(default_factory=list, description="Parent claim IDs in the provenance chain")
    child_claim_ids: List[str] = Field(default_factory=list, description="Child claim IDs derived from this claim")
    source_type: Optional[Literal["live", "demo"]] = Field(None, description="Provenance of originating source")
    query_relevance: Optional[float] = Field(None, description="Semantic relevance of claim to the original query (0.0-1.0)")
    evidence_support: Optional[float] = Field(None, description="Degree to which source evidence supports the claim (0.0-1.0)")

    def __init__(self, **data):
        # Support legacy 'text' -> 'claim_text' and 'id' -> 'claim_id' aliases
        if "text" in data and "claim_text" not in data:
            data["claim_text"] = data["text"]
        if "id" in data and data.get("id") and "claim_id" not in data:
            data["claim_id"] = data["id"]
        if "claim_id" in data and "id" not in data:
            data["id"] = data["claim_id"]
        if "claim_text" in data and "text" not in data:
            data["text"] = data["claim_text"]
        super().__init__(**data)

class SourceDocument(BaseModel):
    source_id: Optional[str] = Field(default="doc_1", description="Unique document ID, e.g. doc_1")
    id: str = Field(default="doc_1", description="Alias matching source_id")
    title: str = Field(..., description="Document title")
    url: Optional[str] = Field(default="https://evidence.org/doc")
    publisher: Optional[str] = Field(default="Market Analytics")
    publication_date: Optional[str] = Field(default="2025-08-01")
    relevant_excerpt: Optional[str] = Field(default="")
    content: str = Field(..., description="Full text content of document")
    author: Optional[str] = Field(default="Unknown")
    date: Optional[str] = Field(default="2026")
    doc_type: Optional[str] = Field(default="Research Paper")
    source_type: Optional[Literal["live", "demo"]] = Field(None, description="Provenance flag: live web retrieval or demo fixture")

    @classmethod
    def sync_ids(cls, data: Any) -> Any:
        if isinstance(data, dict):
            sid = data.get('source_id') or data.get('id') or 'doc_1'
            data['source_id'] = sid
            data['id'] = sid
        return data

class GraphEdge(BaseModel):
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    edge_type: str = Field(default="DERIVED_FROM", description="Relationship type")

class TraceGraph(BaseModel):
    sources: List[SourceDocument] = Field(default_factory=list)
    claims: List[Claim] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    integrity_score: float = Field(default=1.0, description="Overall citation integrity score (0.0 - 1.0)")
    verified_count: int = Field(default=0)
    unsupported_count: int = Field(default=0)
    conflicting_count: int = Field(default=0)
    chain_status: str = Field(default="VERIFIED", description="Final chain integrity status: VERIFIED, PARTIAL, BROKEN, CONFLICTING")
    chain_diagnostic: str = Field(default="", description="Diagnostic report from deterministic Citation Integrity Engine")
    final_answer: str = Field(default="")

class AgentStepLog(BaseModel):
    step_number: int
    agent_name: str
    model_name: str
    status: str
    summary: str
    created_claim_ids: List[str] = Field(default_factory=list)
    duration_ms: int = Field(default=0)

class AnalysisRequest(BaseModel):
    query: str = Field(..., description="User research question")
    documents: List[SourceDocument] = Field(default_factory=list)
    preset_id: Optional[str] = Field(None, description="Optional hackathon demo scenario ID")
    mode: str = Field(default="LIVE", description="Execution mode: LIVE or DEMO")
    model_a_name: Optional[str] = Field(default="Mistral-Small (Generator)")
    model_b_name: Optional[str] = Field(default="Mistral-Large (Verifier)")

class AnalysisResponse(BaseModel):
    request_id: str
    query: str
    trace_graph: TraceGraph
    execution_steps: List[AgentStepLog]
    total_duration_ms: int

class EvalTestCase(BaseModel):
    id: str
    name: str
    description: str
    query: str
    documents: List[SourceDocument]
    expected_verified_claims: int = 3
    expected_conflicting: int = 1
    expected_unsupported: int = 1

class EvalMetricResult(BaseModel):
    test_case_id: str
    test_case_name: str
    capability_tested: str = "Citation & Provenance Integrity"
    expected_result: str = "VERIFIED"
    actual_result: str = "VERIFIED"
    pass_reason: str = "PASSED — All evidence claims verified."
    total_claims: int = 14
    verified_count: int = 10
    partial_count: int = 1
    unsupported_count: int = 2
    conflicting_count: int = 1
    unresolved_count: int = 0
    citation_precision: float
    citation_recall: float
    contradiction_detection_rate: float
    provenance_integrity_score: float
    passed: bool
    details: str
