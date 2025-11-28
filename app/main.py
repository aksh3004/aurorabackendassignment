import os
import logging
import redis
import time
import json
from fastapi import FastAPI, Query
from pydantic import BaseModel
from app.client import fetch_data
from typing import List, Any, Optional
from datetime import datetime
from app.models import SearchResponse

logger = logging.getLogger("uvicorn.error")
app = FastAPI(title="Search Engine")

CACHE_DURATION = 3600
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
MESSAGE_CACHE = "aurora:messages"

try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info("Connected to Redis at %s", REDIS_URL)
except Exception as e:
    logger.error("Failed to connect to Redis: %s", str(e))
    redis_client = None


async def get_cached_messages(force_refresh: bool = False):
    """
    Get cached messages or fetch new ones if cache is stale.
    """
    if not force_refresh and redis_client:
        try:
            cached = redis_client.get(MESSAGE_CACHE)
            if cached:
                logger.info("Loaded messages from Redis cache")
                return json.loads(cached)
        except Exception as e:
            logger.error("Error loading from Redis: %s", str(e))

    messages = await fetch_data()

    if redis_client and messages:
        try:
            redis_client.setex(MESSAGE_CACHE, CACHE_DURATION, json.dumps(messages))
            logger.info(f"Cached {len(messages)} messages in Redis")
        except Exception as e:
            logger.error("Error saving to Redis: %s", str(e))

    return messages


@app.on_event("startup")
async def startup_event():
    """
    Initialize cache on startup.
    """
    logger.info("Starting up and loading initial cache")
    await get_cached_messages(force_refresh=True)


@app.get("/search", response_model=SearchResponse)
async def search(
    query: str = Query("", description="Search query string"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
) -> SearchResponse:
    """
    Search for messages matching the query string.
    Returns the paginated search results.
    """
    messages = await get_cached_messages()

    query_lower = query.lower()
    start_time = time.time()

    # Lower case string matching
    results = [m for m in messages if query.lower() in json.dumps(m).lower()]
    # Pagination results
    total_result = len(results)
    start_size = (page - 1) * page_size
    end_size = start_size + page_size
    paginated_results = results[start_size:end_size]
    elapsed_ms = (time.time() - start_time) * 1000

    return SearchResponse(
        results=paginated_results,
        total=total_result,
        page=page,
        page_size=page_size,
        elapsed_ms=round(elapsed_ms, 3),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
