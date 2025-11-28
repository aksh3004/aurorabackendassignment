import httpx
from typing import List, Dict, Any

EXTERNAL_API_URL = "https://november7-730026606190.europe-west1.run.app/messages/"

async def fetch_data() -> List[Dict[str, Any]]:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(EXTERNAL_API_URL)
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, list) else data.get("messages", [])
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []
