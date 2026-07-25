from fastapi import APIRouter
 
from api.cache import ping_redis
from api.index_store import store
from api.schemas import HealthResponse
 
router = APIRouter(prefix="/health", tags=["Health"])


@router.get("" , response_model=HealthResponse)
async def health_check() -> HealthResponse:
    redis_ok = await ping_redis()
    return HealthResponse(
        status = "ok" if redis_ok else "degraded" , 
        redis = "connected" if redis_ok else "unavailable" , 
        index_loaded = store.is_ready , 
        num_chunks = len(store.chunks)
    )