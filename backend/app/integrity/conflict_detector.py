import re
from typing import List, Tuple
from backend.app.schemas import Claim, GraphEdge, VerificationStatus

class ConflictDetector:
    """
    Detects conflicting claims between sources (e.g. Source A says Market growth = 12%, Source B says Market growth = 7%).
    Creates CONTRADICTS edges between conflicting claims.
    """
    def detect_conflicts(self, claims: List[Claim]) -> Tuple[List[GraphEdge], List[str]]:
        edges: List[GraphEdge] = []
        conflicting_messages: List[str] = []

        # Compare claim pairs for numerical or factual contradictions
        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                c1 = claims[i]
                c2 = claims[j]

                # Check if from different sources
                s1 = c1.source_id or (c1.source_refs[0].source_id if c1.source_refs else None)
                s2 = c2.source_id or (c2.source_refs[0].source_id if c2.source_refs else None)

                if s1 and s2 and s1 != s2:
                    # Detect conflicting numeric figures or key assertions
                    nums1 = re.findall(r'\b\d+(?:\.\d+)?%?\b', c1.text)
                    nums2 = re.findall(r'\b\d+(?:\.\d+)?%?\b', c2.text)

                    if nums1 and nums2 and nums1 != nums2 and any(w in c1.text.lower() for w in ['growth', 'market', 'revenue', 'profit', 'cagr']):
                        cid1 = c1.claim_id or c1.id
                        cid2 = c2.claim_id or c2.id
                        edges.append(GraphEdge(source=cid1, target=cid2, edge_type="CONTRADICTS"))
                        c1.verification_status = VerificationStatus.CONFLICTING
                        c2.verification_status = VerificationStatus.CONFLICTING
                        msg = f"🟠 CONFLICTING EVIDENCE: Claim {cid1} asserts {nums1[0]} whereas Claim {cid2} asserts {nums2[0]}."
                        c1.reason = msg
                        c2.reason = msg
                        conflicting_messages.append(msg)

        return edges, conflicting_messages
