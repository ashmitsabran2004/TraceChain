import os
import logging
from typing import Optional, Dict, Any, List
from supabase import create_client, Client

logger = logging.getLogger("supabase_client")

class SupabaseService:
    """
    Server-side Supabase PostgreSQL service.
    Uses SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY / SUPABASE_ANON_KEY from environment.
    Provides persistence for investigations, sources, claims, claim_evidence, provenance_edges, agent_runs, evaluation_cases, and evaluation_runs.
    """
    def __init__(self):
        self.url: str = os.getenv("SUPABASE_URL", "")
        self.key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_ANON_KEY", ""))
        self.client: Optional[Client] = None
        
        if self.url and self.key and "your-supabase" not in self.url:
            try:
                self.client = create_client(self.url, self.key)
                logger.info("Supabase client successfully initialized.")
            except Exception as e:
                logger.warning(f"Supabase client initialization warning: {e}")

    def is_connected(self) -> bool:
        return self.client is not None

    def save_investigation_record(
        self,
        investigation_id: str,
        query: str,
        mode: str,
        status: str,
        final_answer: str,
        sources: List[Dict[str, Any]],
        claims: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        agent_steps: List[Dict[str, Any]],
        duration_ms: int
    ) -> bool:
        """
        Persists the complete provenance investigation record into Supabase PostgreSQL tables.
        """
        if not self.client:
            return False

        try:
            # 1. Table: investigations
            inv_payload = {
                "id": investigation_id,
                "query": query,
                "mode": mode,
                "status": status,
                "final_answer": final_answer,
                "created_at": "now()",
                "completed_at": "now()"
            }
            self.client.table("investigations").upsert(inv_payload).execute()

            # 2. Table: sources
            for doc in sources:
                src_payload = {
                    "id": doc.get("source_id") or doc.get("id"),
                    "investigation_id": investigation_id,
                    "title": doc.get("title", ""),
                    "url": doc.get("url", ""),
                    "source_type": doc.get("source_type") or doc.get("doc_type", "Web Article"),
                    "content": doc.get("content", ""),
                    "retrieved_at": "now()"
                }
                self.client.table("sources").upsert(src_payload).execute()

            # 3. Table: claims & claim_evidence
            visited_claims = set()
            for c in claims:
                cid = c.get("claim_id") or c.get("id")
                if cid in visited_claims:
                    continue
                visited_claims.add(cid)

                claim_payload = {
                    "id": cid,
                    "investigation_id": investigation_id,
                    "claim_id": cid,
                    "claim_text": c.get("text", "") or c.get("claim_text", ""),
                    "claim_type": c.get("claim_type", "RAW_CLAIM"),
                    "status": c.get("verification_status", "UNVERIFIED"),
                    "confidence": c.get("confidence", 0.90),
                    "query_relevance": c.get("query_relevance"),
                    "evidence_support": c.get("evidence_support"),
                    "created_at": "now()"
                }
                self.client.table("claims").upsert(claim_payload).execute()

                # Source Evidence
                for ref in c.get("source_refs", []):
                    ev_payload = {
                        "claim_id": cid,
                        "source_id": ref.get("source_id"),
                        "evidence_text": ref.get("relevant_excerpt") or ref.get("exact_quote", ""),
                        "created_at": "now()"
                    }
                    self.client.table("claim_evidence").upsert(ev_payload).execute()

            # 4. Table: provenance_edges
            for edge in edges:
                edge_payload = {
                    "investigation_id": investigation_id,
                    "parent_claim_id": edge.get("source"),
                    "child_claim_id": edge.get("target"),
                    "relationship_type": edge.get("edge_type", "DERIVED_FROM"),
                    "created_at": "now()"
                }
                self.client.table("provenance_edges").upsert(edge_payload).execute()

            # 5. Table: agent_runs
            for step in agent_steps:
                run_payload = {
                    "investigation_id": investigation_id,
                    "agent_name": step.get("agent_name", ""),
                    "provider": "mistral",
                    "model": step.get("model_name", ""),
                    "input": query,
                    "output": step.get("summary", ""),
                    "status": step.get("status", "Completed"),
                    "duration_ms": step.get("duration_ms", 0),
                    "created_at": "now()"
                }
                self.client.table("agent_runs").upsert(run_payload).execute()

            return True
        except Exception as e:
            logger.warning(f"Supabase persistence notice: {e}")
            return False

    def save_evaluation_run(self, run_data: Dict[str, Any]) -> bool:
        """
        Persists live Evaluation Suite benchmark execution run results into Supabase table evaluation_runs.
        """
        if not self.client:
            return False
        try:
            self.client.table("evaluation_runs").upsert({
                "evaluation_case_id": run_data.get("test_case_id"),
                "actual_status": run_data.get("actual_result"),
                "passed": run_data.get("passed"),
                "claims_evaluated": run_data.get("total_claims"),
                "verified_count": run_data.get("verified_count"),
                "partial_count": run_data.get("partial_count"),
                "unsupported_count": run_data.get("unsupported_count"),
                "conflicting_count": run_data.get("conflicting_count"),
                "unresolved_count": run_data.get("unresolved_count"),
                "duration_ms": run_data.get("duration_ms", 120),
                "created_at": "now()"
            }).execute()
            return True
        except Exception as e:
            logger.warning(f"Supabase eval run save notice: {e}")
            return False

# Global instance
supabase_service = SupabaseService()
