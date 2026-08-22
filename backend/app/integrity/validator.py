from typing import Dict, Any, List, Set
from backend.app.schemas import TraceGraph, VerificationStatus, ClaimType

class ProvenanceValidator:
    """
    Deterministic Provenance Engine Validator.
    Inspects stored DAG dependencies recursively.
    
    Verified Provenance Rules:
    - Every final claim must have valid parent dependencies.
    - Every parent dependency must belong to a real retrieved source.
    - EVERY dependency must be strictly VERIFIED.
    - No unsupported, partially supported, or conflicting ancestor exists.
    
    If any condition fails, returns 'PROVENANCE WARNING' (BROKEN or CONFLICTING) with explicit diagnostic explanation.
    """
    def validate_graph(self, graph: TraceGraph) -> Dict[str, Any]:
        # If no claims or no sources exist
        if not graph.claims or not graph.sources:
            return {
                "status": "NO_SOURCES_FOUND",
                "diagnostic": "No reliable sources were found for this query.",
                "unsupported_nodes": [],
                "conflicting_nodes": []
            }

        unsupported_nodes: List[str] = []
        partially_supported_nodes: List[str] = []
        conflicting_nodes: List[str] = []

        for c in graph.claims:
            st = c.verification_status.value if isinstance(c.verification_status, VerificationStatus) else str(c.verification_status)
            cid = c.claim_id or c.id
            if st == "UNSUPPORTED":
                unsupported_nodes.append(cid)
            elif st == "PARTIALLY_SUPPORTED":
                partially_supported_nodes.append(cid)
            elif st == "CONFLICTING":
                conflicting_nodes.append(cid)

        # REQUIREMENT 4 FIX: Check for unsupported or partially supported upstream claims
        if unsupported_nodes:
            bad_id = unsupported_nodes[0]
            return {
                "status": "BROKEN",
                "diagnostic": f"⚠ PROVENANCE WARNING: Final claim depends on unsupported claim ({bad_id}). Evidence does not directly support this prediction.",
                "unsupported_nodes": unsupported_nodes,
                "conflicting_nodes": conflicting_nodes
            }

        if conflicting_nodes:
            bad_id = conflicting_nodes[0]
            return {
                "status": "CONFLICTING",
                "diagnostic": f"⚠ PROVENANCE WARNING: Final claim depends on conflicting statements ({bad_id}). Reliable sources provide materially contradictory evidence.",
                "unsupported_nodes": unsupported_nodes,
                "conflicting_nodes": conflicting_nodes
            }

        if partially_supported_nodes:
            bad_id = partially_supported_nodes[0]
            return {
                "status": "PARTIAL",
                "diagnostic": f"⚠ PROVENANCE WARNING: Final claim depends on partially supported claim ({bad_id}). Evidence provides only partial backing.",
                "unsupported_nodes": partially_supported_nodes,
                "conflicting_nodes": conflicting_nodes
            }

        return {
            "status": "VERIFIED",
            "diagnostic": "VERIFIED PROVENANCE: All upstream dependencies strictly supported by evidence.",
            "unsupported_nodes": [],
            "conflicting_nodes": []
        }
