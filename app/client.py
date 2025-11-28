import httpx
import logging
from typing import List, Dict, Any

logger = logging.getLogger("uvicorn.error")

# Redirected URL for the external API
EXTERNAL_API_URL = "https://november7-730026606190.europe-west1.run.app/messages/"


async def fetch_data() -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            """
            Fetch and return data from the external API.
            """
            response = await client.get(EXTERNAL_API_URL)
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, list) else data["items"]
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        return []
