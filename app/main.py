import os
from fastapi import FastAPI, Query
from pydantic import BaseModel
from app.client import fetch_data
from typing import List, Any, Optional
from datetime import datetime
import logging
import asyncio
import redis
from app.models import Message, SearchResponse

logger = logging.getLogger("uvicorn.error")
app = FastAPI(title="Search Engine")

CACHE_DURATION = 3600
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info("Connected to Redis at %s", REDIS_URL)
except Exception as e:
    logger.error("Failed to connect to Redis: %s", str(e))
    redis_client = None


_message_cache = "aurora:messages"
    

async def get_cached_messages(force_refresh: bool = False):
    """
    Get cached messages or fetch new ones if cache is stale.
    """
    global _message_cache
    now = datetime.utcnow().timestamp()

    if not force_refresh and redis_client:
        try:
            cached = redis_client.get(_message_cache)
            if cached:
                logger.info("Loaded messages from Redis cache")
                return json.loads(cached)
        except Exception as e:
            logger.error("Error loading from Redis: %s", str(e))
    
    messages = await fetch_data()
    if redis_client and messages:
        try:
            redis_client.setex(_message_cache, CACHE_DURATION, json.dumps(messages))
        except Exception as e:
            logger.error("Error saving to Redis: %s", str(e))
                  
    return messages


@app.on_event("startup")
async def startup_event():
    """
    Initialize cache on startup.
    """
    logger.info("Starting up and loading initial cache")
    await get_cached_messages()


@app.get("/search", response_model=SearchResponse)
async def search(
    query: str = Query("", description="Search query string"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
 ) -> SearchResponse:
    """
    Search for messages matching the query string.
    Returns the paginated search results.
    """
    messages = await get_cached_messages()
    query_lower = query.lower()
    
    results = [
        m for m in messages 
        if query_lower in str(m.get("content", "")).lower() or 
            query_lower in str(m.get("id", "")).lower()
    ]
    
    # Pagination results
    total_result = len(results)
    start_size = (page - 1) * page_size
    end_size = start_size + page_size
    paginated_results = results[start_size:end_size]
    
    return SearchResponse(
        results=paginated_results,
        total=total_result,
        page=page,
        page_size=page_size
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
