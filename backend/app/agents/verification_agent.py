from typing import List
from backend.app.schemas import Claim, ClaimType, VerificationStatus
from backend.app.provenance_dag import ProvenanceDAG
from backend.app.models_engine import TwoModelEngine
from backend.app.services.mistral_service import MistralService
from backend.app.config import CAUSAL_CUES

# List of cue words indicating a causal relationship (case-insensitive)
# CAUSAL_CUES imported from backend.app.config

class VerificationAgent:
    """
    AGENT 2 — VERIFICATION
    Purpose: Determine whether a source actually supports a claim using Mistral Model 2.
    Inputs: Claim + Source excerpt + Research Query.
    Outputs: VERIFIED | PARTIALLY_SUPPORTED | UNSUPPORTED | CONFLICTING.
    Returns: confidence, reason, evidence.
    Stores complete verification result in registry.
    """
    def __init__(self, engine: TwoModelEngine):
        self.agent_id = "verification"
        self.engine = engine
        self.mistral_service = MistralService()

    def run(self, raw_claims: List[Claim], dag: ProvenanceDAG, query: str = "") -> List[Claim]:
        verified_claims: List[Claim] = []

        for raw_claim in raw_claims:
            source_ref = raw_claim.source_refs[0] if raw_claim.source_refs else None
            sid = raw_claim.source_id or (source_ref.source_id if source_ref else None)
            source_doc = dag.sources.get(sid) if sid else None

            if not source_doc:
                raw_claim.verification_status = VerificationStatus.UNSUPPORTED
                raw_claim.confidence = 0.20
                raw_claim.reason = "Verification failed: Source document missing from DAG context."
                raw_claim.evidence_text = "No supporting source available."
                verified_claims.append(raw_claim)
                continue

            # Call the structured verification service
            verification_result = self.mistral_service.verify_structured_claim(
                claim_text=raw_claim.claim_text if hasattr(raw_claim, "claim_text") else raw_claim.text,
                source_doc=source_doc,
                evidence_quote=(
                    source_ref.exact_quote or source_ref.relevant_excerpt
                    if source_ref else source_doc.content[:500]
                ),
                query=query,
            )
            status = verification_result.get("status", "UNSUPPORTED")
            conf = verification_result.get("confidence", 0.0)
            reason = verification_result.get("reason", "")
            evidence = verification_result.get("evidence", "")
            query_rel = verification_result.get("query_relevance")
            evidence_sup = verification_result.get("evidence_support")
            # Determine if claim is causal
            is_causal = any(cue.lower() in (raw_claim.claim_text if hasattr(raw_claim, "claim_text") else raw_claim.text).lower() for cue in CAUSAL_CUES)
            # Apply backend thresholds
            if status == "VERIFIED":
                req_e = 0.6 if is_causal else 0.4
                if not (query_rel is not None and evidence_sup is not None and query_rel >= 0.5 and evidence_sup >= req_e):
                    status = "UNSUPPORTED"
            verified_claim_id = f"VERIFIED-{raw_claim.claim_id}"
            verified_claim = Claim(
                claim_id=verified_claim_id,
                id=verified_claim_id,
                claim_text=raw_claim.claim_text if hasattr(raw_claim, "claim_text") else raw_claim.text,
                claim_type=ClaimType.VERIFIED_CLAIM,
                source_id=sid,
                agent_id=self.agent_id,
                model_used=self.engine.model_b_name,
                verification_status=VerificationStatus[status],
                confidence=conf,
                reason=reason,
                evidence_text=evidence,
                query_relevance=query_rel,
                evidence_support=evidence_sup,
                source_refs=raw_claim.source_refs,
                parent_claim_ids=[raw_claim.claim_id],
            )
            # Update raw claim
            raw_claim.verification_status = VerificationStatus[status]
            raw_claim.confidence = conf
            raw_claim.child_claim_ids.append(verified_claim_id)

            dag.add_claim(verified_claim)
            verified_claims.append(verified_claim)

        return verified_claims
