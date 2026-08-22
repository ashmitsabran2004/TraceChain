from backend.app.schemas import TraceGraph, VerificationStatus

class ProvenanceScorer:
    """
    Computes numerical integrity score (0.0 to 1.0) based on verified vs broken/conflicting nodes.
    """
    def calculate_score(self, graph: TraceGraph) -> float:
        total = len(graph.claims)
        if total == 0:
            return 1.0

        verified = sum(1 for c in graph.claims if c.verification_status in (VerificationStatus.VERIFIED, VerificationStatus.PARTIALLY_SUPPORTED))
        unsupported = sum(1 for c in graph.claims if c.verification_status == VerificationStatus.UNSUPPORTED)
        conflicting = sum(1 for c in graph.claims if c.verification_status == VerificationStatus.CONFLICTING)

        score = (verified * 1.0 + unsupported * 0.2 + conflicting * 0.0) / total
        return round(score, 2)
