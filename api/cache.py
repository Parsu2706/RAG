import hashlib
import json
import logging
import os 
from typing import Any , Optional

import redis.asyncio as aioredis
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

REDIS_URL : str = os.getenv("REDIS_URL" , "redis://localhost:6379/0")
QUERY_TTL : int = int(os.getenv("QUERY_CACHE_TTL" , 3600)) #1 hours
INDEX_TTL = int(os.getenv("INDEX_CACHE_TTL", "86400"))

_redis_client : Optional[aioredis.Redis] = None

async def get_redis() -> Optional[aioredis.Redis]: 
    global _redis_client
    if _redis_client is None: 
        try: 
            _redis_client = aioredis.from_url(REDIS_URL , encoding = "utf-8" , 
                                            decode_responses = True , socket_connect_timeout = 2 , 
                                            socket_timeout = 2)
            await _redis_client.ping()
            logger.info("Redis connected : %s" , REDIS_URL)
        except Exception as e: 
            logger.warning("Redis Unavailable - caching disabled. Reason: %s" , e)
            _redis_client = None
    return _redis_client

async def close_redis() -> None: 
    global _redis_client 
    if _redis_client: 
        await _redis_client.aclose()
        _redis_client = None
        logger.info("Redis Connection Closed.")

async def ping_redis() -> bool: 
    client = await get_redis()
    if client is None: 
        return False
    try : 
        return await client.ping()

    except Exception: 
        return False
    
def _query_cache_key(query : str , mode : str , top_k : int) -> str: 
    raw = f"{query.strip().lower()}|{mode}|{top_k}"
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"query:{digest}"

async def get_cached_query(query : str , mode : str , top_k : int) -> Optional[dict[str ,Any]] : 
    client = await get_redis()
    if client is None: 
        return None
    key = _query_cache_key(query , mode  ,top_k)
    try: 
        raw = await client.get(key)
        if raw : 
            logger.debug("Cache HIT key=%s" , key)
            return json.loads(raw)
        logger.debug("Cache MISS key=%s" , key)
    except Exception as e : 
        logger.warning("Cache read error: %s" , e)

async def set_cached_query(query : str , mode:str , top_k : int , response_dict : dict[str , Any]) -> None :
    client = await get_redis()
    if client is None: 
        return None
    key = _query_cache_key(query , mode , top_k)
    try: 
        await client.setex(key , QUERY_TTL , json.dumps(response_dict))
        logger.debug("Cache SET key=%s ttl=%ds" , key , QUERY_TTL)
    except Exception as e : 
        logger.warning("cache write error :" , e)
    
async def invalidate_query_cache()-> int: 
    client  = await get_redis()
    if client  is None : 
        return 0 
    try : 
        key = await client.keys("query:*")
        if key: 
            deleted = await client.delete(*key)
            logger.info("Invalidated %d query cache entries" , deleted)
            return deleted
    except Exception as e : 
        logger.warning("cache invalidation error: %s" , e)
    return 0 


