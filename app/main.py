import os
from fastapi import FastAPI, Query
from pydantic import BaseModel
from app.client import fetch_data
from typing import List, Any, Optional
from datetime import datetime
import logging
import asyncio
from app.models import Message, SearchResponse

logger = logging.getLogger("uvicorn.error")
app = FastAPI(title="Search Engine")

CACHE_DURATION = 3600

_message_cache = None
_cache_timestamp = None


async def get_cached_messages():
    """
    Get cached messages or fetch new ones if cache is stale.
    """
    global _message_cache, _cache_timestamp
    now = datetime.utcnow().timestamp()

    if (
        _message_cache
        and _cache_timestamp
        and (now - _cache_timestamp) < CACHE_DURATION
    ):
        return _message_cache

    messages = await fetch_data()
    _message_cache = messages
    _cache_timestamp = now

    return messages


async def background_refresh_cache():
    while True:
        await asyncio.sleep(CACHE_DURATION)
        try:
            messages = await fetch_data()
            logger.info("Cache refreshed with %d messages", len(messages))
        except Exception as e:
            logger.error("Failed to refresh cache: %s", str(e))


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
    end_size = start + page_size
    paginated_results = results[start_size:end_size]
    
    return SearchResponse(
        results=paginated_results,
        total=total_result,
        page=page,
        page_size=page_size
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
