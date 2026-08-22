from typing import List, Dict, Set, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field
from backend.app.schemas import VerificationStatus, Claim, TraceGraph

class ChainIntegrityStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIAL = "PARTIAL"
    BROKEN = "BROKEN"
    CONFLICTING = "CONFLICTING"

class ProvenanceChainReport(BaseModel):
    root_claim_id: str
    status: ChainIntegrityStatus
    provenance_depth: int = 0
    total_ancestor_claims: int = 0
    verified_claim_ids: List[str] = Field(default_factory=list)
    unsupported_claim_ids: List[str] = Field(default_factory=list)
    conflicting_claim_ids: List[str] = Field(default_factory=list)
    original_source_ids: List[str] = Field(default_factory=list)
    diagnostic_message: str = ""

class CitationIntegrityEngine:
    """
    DETERMINISTIC CITATION INTEGRITY ENGINE (NON-AI BACKEND LOGIC)
    
    Does NOT ask an LLM if a citation chain is valid.
    Directly inspects the graph structure:
    1. Finds parent claims.
    2. Recursively traverses all upstream dependencies.
    3. Identifies root sources.
    4. Checks verification status of every node in the chain.
    5. Flags BROKEN provenance if any upstream claim is UNSUPPORTED.
    6. Flags CONFLICTING provenance if any upstream claim is CONFLICTING.
    7. Computes provenance depth.
    8. Assigns final chain status: VERIFIED, PARTIAL, BROKEN, or CONFLICTING.
    """
    def __init__(self, trace_graph: TraceGraph):
        self.trace_graph = trace_graph
        self.claims_map: Dict[str, Claim] = {c.claim_id or c.id: c for c in trace_graph.claims}
        self.sources_map: Dict[str, Any] = {s.source_id or s.id: s for s in trace_graph.sources}

    def evaluate_chain(self, root_claim_id: str) -> ProvenanceChainReport:
        if root_claim_id not in self.claims_map:
            return ProvenanceChainReport(
                root_claim_id=root_claim_id,
                status=ChainIntegrityStatus.BROKEN,
                diagnostic_message=f"Root claim '{root_claim_id}' not found in claim registry."
            )

        visited_nodes: Set[str] = set()
        visited_claim_ids: List[str] = []
        verified_claim_ids: List[str] = []
        unsupported_claim_ids: List[str] = []
        conflicting_claim_ids: List[str] = []
        original_source_ids: List[str] = []

        # Queue for BFS/DFS traversal: tuple of (node_id, depth)
        queue = [(root_claim_id, 0)]
        max_depth = 0

        while queue:
            curr_id, depth = queue.pop(0)
            if curr_id in visited_nodes:
                continue
            visited_nodes.add(curr_id)
            max_depth = max(max_depth, depth)

            if curr_id in self.claims_map:
                claim = self.claims_map[curr_id]
                visited_claim_ids.append(curr_id)

                status = claim.verification_status
                if status == VerificationStatus.CONFLICTING:
                    conflicting_claim_ids.append(curr_id)
                elif status == VerificationStatus.UNSUPPORTED:
                    unsupported_claim_ids.append(curr_id)
                elif status in (VerificationStatus.VERIFIED, VerificationStatus.PARTIALLY_SUPPORTED):
                    verified_claim_ids.append(curr_id)

                # Add parent claims and source IDs to queue
                for pid in claim.parent_claim_ids:
                    queue.append((pid, depth + 1))
                if claim.source_id:
                    queue.append((claim.source_id, depth + 1))

            elif curr_id in self.sources_map:
                original_source_ids.append(curr_id)

        # Deterministic status classification logic
        if conflicting_claim_ids:
            final_status = ChainIntegrityStatus.CONFLICTING
            diag = f"⚠ CONFLICTING PROVENANCE: Upstream claim {conflicting_claim_ids[0]} contradicts source text."
        elif unsupported_claim_ids:
            final_status = ChainIntegrityStatus.BROKEN
            diag = f"⚠ BROKEN PROVENANCE: Upstream claim {unsupported_claim_ids[0]} has unsupported evidence."
        elif len(verified_claim_ids) == len(visited_claim_ids):
            final_status = ChainIntegrityStatus.VERIFIED
            diag = f"✅ VERIFIED PROVENANCE: 100% of upstream claims ({len(verified_claim_ids)}) strictly verified."
        else:
            final_status = ChainIntegrityStatus.PARTIAL
            diag = f"🟡 PARTIAL PROVENANCE: {len(verified_claim_ids)} of {len(visited_claim_ids)} claims verified."

        return ProvenanceChainReport(
            root_claim_id=root_claim_id,
            status=final_status,
            provenance_depth=max_depth,
            total_ancestor_claims=len(visited_claim_ids),
            verified_claim_ids=verified_claim_ids,
            unsupported_claim_ids=unsupported_claim_ids,
            conflicting_claim_ids=conflicting_claim_ids,
            original_source_ids=original_source_ids,
            diagnostic_message=diag
        )
