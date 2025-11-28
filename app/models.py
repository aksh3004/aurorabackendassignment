from pydantic import BaseModel
from typing import List, Any, Optional


class Message(BaseModel):
    """
    Message model
    """

    id: Any
    user_id: Optional[Any] = None
    user_name: Optional[str] = None
    message: Optional[str] = None
    timestamp: Optional[str] = None


class SearchResponse(BaseModel):
    """
    Search response model
    """

    results: List[Message]
    total: int
    page: int
    page_size: int
    elapsed_ms: Optional[float] = None
