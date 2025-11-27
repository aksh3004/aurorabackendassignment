from pydantic import BaseModel
from typing import List, Any, Optional

class Message(BaseModel):
    """Message model"""
    content: str
    id: Any
    text: Optional[str] = None
    timestamp: Optional[str] = None

class SearchResponse(BaseModel):
    """Search response model"""
    results: List[Message]
    total: int
    page: int
    page_size: int