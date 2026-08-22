from fastapi import APIRouter, HTTPException, Query
from backend.app.api.investigations import investigations_cache

router = APIRouter(prefix="/api/claims", tags=["claims"])

@router.get("/{id}")
def get_claim_details(id: str, investigation_id: str = Query(...)):
    """
    GET /api/claims/{id} - Get detailed metadata for specific claim ID.
    """
    response = investigations_cache.get(investigation_id)
    if response is None:
        raise HTTPException(status_code=404, detail=f"Investigation '{investigation_id}' was not found.")

    for claim in response.trace_graph.claims:
        if (claim.claim_id or claim.id) == id:
            return claim.model_dump()

    raise HTTPException(status_code=404, detail=f"Claim '{id}' was not found in investigation '{investigation_id}'.")

@router.get("/{id}/provenance")
def get_claim_provenance(id: str, investigation_id: str = Query(...)):
    """
    GET /api/claims/{id}/provenance - Get full upstream provenance ancestor tree for claim ID.
    """
    response = investigations_cache.get(investigation_id)
    if response is None:
        raise HTTPException(status_code=404, detail=f"Investigation '{investigation_id}' was not found.")

    claims_map = {c.claim_id or c.id: c for c in response.trace_graph.claims}
    if id not in claims_map:
        raise HTTPException(status_code=404, detail=f"Claim '{id}' was not found in investigation '{investigation_id}'.")

    visited = set()
    queue = [id]
    while queue:
        curr = queue.pop(0)
        if curr in visited or curr not in claims_map:
            continue
        visited.add(curr)
        queue.extend(claims_map[curr].parent_claim_ids)

    return {
        "target_claim_id": id,
        "ancestor_claim_ids": list(visited),
        "total_ancestors": len(visited)
    }
