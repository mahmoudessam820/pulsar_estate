import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# Request
class ApiKeyCreateRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="A friendly name for this API key (e.g., 'Production App')",
    )


# Response
class ApiKeyCreateResponse(BaseModel):
    id: uuid.UUID
    name: str
    prefix: str
    raw_key: str = Field(
        ..., description="The raw API key. Save this now, it will not be shown again."
    )


class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    prefix: str
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
