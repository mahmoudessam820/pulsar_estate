from typing import Optional

from pydantic import BaseModel


class CrawledDocument(BaseModel):
    url: str
    title: Optional[str]
    content: Optional[str]
    published_at: Optional[str]
    author: Optional[str]
    error: Optional[str] = None
