from typing import List
from backend.app.schemas import Claim, ClaimType, VerificationStatus
from backend.app.provenance_dag import ProvenanceDAG
from backend.app.models_engine import TwoModelEngine

class AnalysisAgent:
    """
    AGENT 3 — ANALYSIS AGENT
    Purpose: Reason ONLY over available claims, preferably verified claims.
    Creates derived claims.
    CRITICAL: DERIVED CLAIM stores parent_claim_ids array [CLAIM-001, CLAIM-004, CLAIM-007].
    """
    def __init__(self, engine: TwoModelEngine):
        self.agent_id = "analysis"
        self.engine = engine

    def run(self, verified_claims: List[Claim], dag: ProvenanceDAG) -> List[Claim]:
        derived_claims: List[Claim] = []
        valid_verified = [c for c in verified_claims if c.verification_status in (VerificationStatus.VERIFIED, VerificationStatus.PARTIALLY_SUPPORTED)]

        if not valid_verified:
            return derived_claims

        for index, parent in enumerate(valid_verified, start=1):
            derived_id = f"DERIVED-CLAIM-{index:03d}"
            parent_id = parent.claim_id
            parent_text = parent.text
            parent_evidence = parent.evidence_text
            parent_sources = list(parent.source_refs)
            derived_claim = Claim(
                claim_id=derived_id,
                id=derived_id,
                text=parent_text,
                claim_type=ClaimType.DERIVED_CLAIM,
                agent_id=self.agent_id,
                model_used=self.engine.model_a_name,
                verification_status=parent.verification_status,
                confidence=parent.confidence,
                source_refs=parent_sources,
                parent_claim_ids=[parent_id],
                reason="Derived from one verified evidence claim.",
                evidence_text=parent_evidence,
                evidence_reasoning=parent.evidence_reasoning
            )

            if parent_id in dag.claims:
                dag.claims[parent_id].child_claim_ids.append(derived_id)

            dag.add_claim(derived_claim)
            derived_claims.append(derived_claim)

        return derived_claims
