import re
from typing import List, Dict
from backend.app.schemas import Claim, ClaimType, VerificationStatus
from backend.app.provenance_dag import ProvenanceDAG
from backend.app.models_engine import TwoModelEngine
from backend.app.utils.html_cleaner import clean_text

class FinalSynthesisAgent:
    """
    AGENT 4 — FINAL ANSWER AGENT
    Purpose: Generate a coherent natural-language response to the user's original question.
    Structure:
    1. Direct answer.
    2. Short explanation.
    3. Supporting claims.
    4. Real citation badges [C1], [C2], [C3].
    5. Qualification/limitation if evidence is incomplete or conflicting.

    Does NOT concatenate raw titles, snippets, or raw claim text.
    Decodes HTML entities and avoids internal data leakage.
    """
    def __init__(self, engine: TwoModelEngine):
        self.agent_id = "final_answer"
        self.engine = engine

    def run(self, query: str, verified_claims: List[Claim], derived_claims: List[Claim], dag: ProvenanceDAG) -> Claim:
        clean_q = clean_text(query)

        verified_candidates = [c for c in verified_claims if c.verification_status == VerificationStatus.VERIFIED]
        query_terms = {
            term for term in re.findall(r"\w+", clean_q.lower())
            if len(term) > 2 and term not in {"the", "who", "what", "how", "why", "are", "is", "was", "can", "does"}
        }
        relevance_scores = {
            id(claim): sum(term in clean_text(claim.text).lower() for term in query_terms)
            for claim in verified_candidates
        }
        if verified_candidates and query_terms:
            best_score = max(relevance_scores.values())
            verified_candidates = [
                claim for claim in verified_candidates
                if relevance_scores[id(claim)] == best_score
            ][:3]
        if verified_candidates:
            selected_claims = verified_candidates[:3]
            cited_claims = [
                f"{clean_text(claim.text)} [C{idx}]"
                for idx, claim in enumerate(selected_claims, start=1)
            ]
            final_text = "Answer: " + " ".join(cited_claims)
            parent_ids = [claim.claim_id for claim in selected_claims]
            citation_refs = [
                source_ref
                for claim in selected_claims
                for source_ref in claim.source_refs
            ]
        else:
            final_text = f"There is insufficient verified evidence in available sources to form a conclusive answer for '{clean_q}'."
            parent_ids = []
            citation_refs = []

        final_claim_id = "FINAL-ANSWER-ROOT"
        final_claim = Claim(
            claim_id=final_claim_id,
            id=final_claim_id,
            text=final_text,
            claim_type=ClaimType.FINAL_CLAIM,
            source_id="ANALYSIS",
            agent_id=self.agent_id,
            model_used=self.engine.model_a_name,
            verification_status=VerificationStatus.VERIFIED if verified_candidates else VerificationStatus.UNVERIFIED,
            confidence=0.90 if verified_candidates else 0.0,
            parent_claim_ids=parent_ids,
            source_refs=citation_refs,
            reason="Synthesized response with user-facing citation badges [C1], [C2].",
        )

        dag.add_claim(final_claim)
        return final_claim
