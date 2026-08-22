from typing import List, Dict, Set, Optional, Tuple, Any
from backend.app.schemas import (
    Claim, SourceDocument, GraphEdge, TraceGraph,
    ClaimType, VerificationStatus
)

class ProvenanceDAG:
    """
    Manages the Directed Acyclic Graph (DAG) of citation provenance across 4 logical agent steps:
    1. Research Agent (Sources + Raw Claims)
    2. Verification Agent (Model B Verification Status: VERIFIED, PARTIALLY_SUPPORTED, UNSUPPORTED, CONFLICTING)
    3. Analysis Agent (Derived Claims with parent_claim_ids dependency array)
    4. Final Answer Agent (Final Answer with embedded citation DAG badges)
    """
    def __init__(self):
        self.sources: Dict[str, SourceDocument] = {}
        self.claims: Dict[str, Claim] = {}
        self.edges: List[GraphEdge] = []
        self.adjacency_upstream: Dict[str, Set[str]] = {}
        self.adjacency_downstream: Dict[str, Set[str]] = {}

    def add_source(self, source: SourceDocument):
        sid = source.source_id or source.id
        self.sources[sid] = source
        if sid not in self.adjacency_upstream:
            self.adjacency_upstream[sid] = set()
        if sid not in self.adjacency_downstream:
            self.adjacency_downstream[sid] = set()

    def add_claim(self, claim: Claim):
        cid = claim.claim_id or claim.id
        self.claims[cid] = claim
        if cid not in self.adjacency_upstream:
            self.adjacency_upstream[cid] = set()
        if cid not in self.adjacency_downstream:
            self.adjacency_downstream[cid] = set()

        for parent_id in claim.parent_claim_ids:
            self.add_edge(parent_id, cid, edge_type="SUPPORTS" if claim.verification_status == VerificationStatus.VERIFIED else "DERIVED_FROM")

    def add_edge(self, source_id: str, target_id: str, edge_type: str = "DERIVED_FROM"):
        edge = GraphEdge(source=source_id, target=target_id, edge_type=edge_type)
        self.edges.append(edge)
        
        if source_id not in self.adjacency_downstream:
            self.adjacency_downstream[source_id] = set()
        self.adjacency_downstream[source_id].add(target_id)

        if target_id not in self.adjacency_upstream:
            self.adjacency_upstream[target_id] = set()
        self.adjacency_upstream[target_id].add(source_id)

    def get_upstream_lineage(self, claim_id: str) -> Dict[str, Any]:
        visited_nodes: Set[str] = set()
        visited_edges: List[GraphEdge] = []
        queue = [claim_id]

        while queue:
            curr = queue.pop(0)
            if curr in visited_nodes:
                continue
            visited_nodes.add(curr)

            parents = self.adjacency_upstream.get(curr, set())
            for p in parents:
                for e in self.edges:
                    if e.source == p and e.target == curr:
                        visited_edges.append(e)
                queue.append(p)

        return {
            "root_claim_id": claim_id,
            "ancestor_node_ids": list(visited_nodes),
            "lineage_edges": [e.model_dump() for e in visited_edges]
        }

    def compute_integrity_metrics(self) -> Dict[str, Any]:
        total = len(self.claims)
        if total == 0:
            return {"integrity_score": 1.0, "verified": 0, "unsupported": 0, "conflicting": 0}

        verified = sum(1 for c in self.claims.values() if c.verification_status in (VerificationStatus.VERIFIED, VerificationStatus.PARTIALLY_SUPPORTED))
        unsupported = sum(1 for c in self.claims.values() if c.verification_status in (VerificationStatus.UNSUPPORTED, VerificationStatus.UNVERIFIED))
        conflicting = sum(1 for c in self.claims.values() if c.verification_status == VerificationStatus.CONFLICTING)

        score = (verified * 1.0 + unsupported * 0.3 + conflicting * 0.0) / total
        return {
            "integrity_score": round(score, 3),
            "verified": verified,
            "unsupported": unsupported,
            "conflicting": conflicting,
            "total": total
        }

    def to_trace_graph(self, final_answer: str = "") -> TraceGraph:
        metrics = self.compute_integrity_metrics()
        return TraceGraph(
            sources=list(self.sources.values()),
            claims=list(self.claims.values()),
            edges=self.edges,
            integrity_score=metrics["integrity_score"],
            verified_count=metrics["verified"],
            unsupported_count=metrics["unsupported"],
            conflicting_count=metrics["conflicting"],
            final_answer=final_answer
        )
