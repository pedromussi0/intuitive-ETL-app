from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Annotated 
import asyncpg
from logging import getLogger

from ..services.search_service import search_operators_db
from ..models.operator import OperatorSearchResponse 
from ..database import get_db_pool

logger = getLogger(__name__)
router = APIRouter(
    prefix="/api/v1/operators", # Prefix for all routes in this router
    tags=["Operators"],         # Tag for Swagger UI grouping
)

# Define common query parameters
# Required query param 'q'
QueryDep = Annotated[str, Query(..., min_length=1, description="Text search term (e.g., operator name, CNPJ, city)")]
# Optional query param 'limit' 
LimitDep = Annotated[int, Query(ge=1, le=100, description="Number of results to return per page")]
# Optional query param 'offset' 
OffsetDep = Annotated[int, Query(ge=0, description="Number of results to skip for pagination")]
# DB Pool dependency
PoolDep = Annotated[asyncpg.Pool, Depends(get_db_pool)]

@router.get(
    "/search",
    response_model=OperatorSearchResponse,
    summary="Search Registered Operators",
    description="Performs a full-text search across Operator Name, Trading Name, CNPJ, and City. Returns relevant operators sorted by rank."
)
async def search_operators(
    q: QueryDep,
    pool: PoolDep,
    limit: LimitDep = 20,
    offset: OffsetDep = 0,
):
    """
    Searches for registered operators based on a query string.
    # ... (rest of docstring)
    """
    logger.info(f"Searching operators with query='{q}', limit={limit}, offset={offset}")
    try:
        total, results = await search_operators_db(pool, q, limit, offset)
        return OperatorSearchResponse(total_count=total, results=results)
    except RuntimeError as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during search.")
    except Exception as e:
        logger.exception(f"Unexpected error during search: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")