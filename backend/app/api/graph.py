from fastapi import APIRouter, HTTPException
from backend.app.api.investigations import investigations_cache

router = APIRouter(prefix="/api/graph", tags=["graph"])

@router.get("/{id}")
def get_graph_by_id(id: str):
    """
    GET /api/graph/{id} - Get complete React Flow DAG schema.
    """
    if id in investigations_cache:
        return investigations_cache[id].trace_graph.model_dump()

    raise HTTPException(status_code=404, detail=f"Investigation '{id}' was not found.")
