import re
from typing import List
from backend.app.schemas import Claim, SourceRef, ClaimType, VerificationStatus, SourceDocument
from backend.app.provenance_dag import ProvenanceDAG
from backend.app.models_engine import TwoModelEngine
from backend.app.services.search_service import WebSearchService
from backend.app.services.mistral_service import MistralService
from backend.app.utils.html_cleaner import clean_text

class ResearchAgent:
    """AGENT 1 — RESEARCH AGENT
    Purpose: Retrieve real web evidence for the user query and extract structured factual claims.
    Outputs: Sources + claims.
    Uses WebSearchService for live retrieval and MistralService for structured claim extraction.
    Rejects sentence fragments and incomplete text.
    Halts cleanly with 0 claims if 0 valid sources exist.
    """

    def __init__(self, engine: TwoModelEngine):
        self.agent_id = "research"
        self.engine = engine
        self.search_service = WebSearchService()
        self.mistral_service = MistralService()

    def run(self, query: str, documents: List[SourceDocument], dag: ProvenanceDAG, is_live_mode: bool = True) -> List[Claim]:
        """Retrieve sources → filter for relevance → extract claims.
        Returns a list of raw Claim objects added to the DAG.
        """
        extracted_claims: List[Claim] = []
        # Live retrieval if requested
        if is_live_mode:
            retrieved_docs = self.search_service.search_web(query)
            documents = retrieved_docs or []

        # Semantic relevance filtering
        relevant_docs = [doc for doc in documents if self._is_relevant_source(query, doc)]
        if not relevant_docs:
            return []

        for doc in relevant_docs:
            sid = doc.source_id or doc.id
            doc.source_id = sid
            doc.id = sid
            dag.add_source(doc)
            # Extract raw claims from document via Mistral model
            raw_data = self.mistral_service.extract_structured_claims(query, doc)
            # Demo specific injection (unchanged behaviour)
            if not is_live_mode and sid == "SOURCE-002":
                raw_data.append({
                    "claim_id": "CLAIM-017",
                    "text": "NovaTech is the market leader in India with 90% market share.",
                    "source_id": sid,
                    "evidence": "Unbacked assertion: NovaTech is the market share.",
                    "confidence": 0.30
                })
            for idx, raw in enumerate(raw_data):
                text = self._normalize_claim_text(raw.get("text", ""))
                if not self._is_complete_claim_sentence(text):
                    continue
                source_ref = SourceRef(
                    source_id=sid,
                    title=clean_text(doc.title),
                    url=doc.url or "https://evidence.org/doc",
                    publisher=clean_text(doc.publisher or "Market Research"),
                    publication_date=doc.publication_date or getattr(doc, "published_at", "2025-08-01"),
                    relevant_excerpt=clean_text(raw.get("evidence", doc.content[:180])),
                    exact_quote=clean_text(raw.get("evidence", text)),
                    location=f"Paragraph {idx + 1}"
                )
                raw_claim_id = str(raw.get("claim_id", f"CLAIM-{idx+1:02d}"))
                claim_id = raw_claim_id
                if not claim_id.upper().startswith(f"CLAIM-{sid.upper()}-"):
                    claim_id = f"CLAIM-{sid.upper()}-{claim_id.removeprefix('CLAIM-')}"
                if claim_id in dag.claims:
                    claim_id = f"{claim_id}-{idx + 1:02d}"
                claim = Claim(
                    claim_id=claim_id,
                    id=claim_id,
                    text=text,
                    claim_type=ClaimType.RAW_CLAIM,
                    source_id=sid,
                    agent_id=self.agent_id,
                    model_used=self.engine.model_a_name,
                    verification_status=VerificationStatus.UNVERIFIED,
                    confidence=float(raw.get("confidence", 0.90)),
                    source_refs=[source_ref],
                    parent_claim_ids=[sid],
                    reason="Extracted from source document.",
                    evidence_text=clean_text(raw.get("evidence", text)),
                    evidence_reasoning="Extracted directly from source document excerpt by Research Agent."
                )
                dag.add_claim(claim)
                extracted_claims.append(claim)
        return extracted_claims

    def _normalize_claim_text(self, text: str) -> str:
        normalized = clean_text(text).strip()
        normalized = re.sub(r"\[(?:C|CLAIM)[-_]?\w+\]", "", normalized, flags=re.IGNORECASE)
        normalized = re.sub(
            r"^(?:based on (?:verified )?source evidence[^:]*:|direct findings:|practical application:|according to the sources?:|the evidence suggests:|based on the provided information:)",
            "",
            normalized,
            flags=re.IGNORECASE,
        )
        return re.sub(r"\s+", " ", normalized).strip()

    def _is_relevant_source(self, query: str, doc: SourceDocument) -> bool:
        """Heuristic relevance: require at least two non‑stopword token overlaps between query and doc title/content."""
        stopwords = {"the", "is", "and", "or", "to", "a", "of", "in", "for", "on", "with", "by", "as", "at", "from"}
        query_tokens = {t for t in re.findall(r"\w+", query.lower()) if t not in stopwords and len(t) > 2}
        if not query_tokens:
            return True
        text = f"{doc.title} {doc.content}".lower()
        doc_tokens = {t for t in re.findall(r"\w+", text) if t not in stopwords and len(t) > 3}
        required_overlap = 1 if doc.source_type == "live" or len(query_tokens) <= 2 else 2
        return len(query_tokens.intersection(doc_tokens)) >= required_overlap

    def _is_complete_claim_sentence(self, text: str) -> bool:
        """Reject sentence fragments, headings, and incomplete phrases."""
        words = text.split()
        if len(words) < 5:
            return False
        last_word = words[-1].lower().strip(".,;:!?")
        incomplete = {"are", "is", "the", "of", "to", "and", "in", "with", "for", "on", "at", "by", "from", "or", "as"}
        if last_word in incomplete:
            return False

        return True
