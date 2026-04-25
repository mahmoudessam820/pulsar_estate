from datetime import datetime
from dataclasses import dataclass


@dataclass
class User:
    id: int
    email: str
    password_hash: str
    is_active: bool = True
    created_at: datetime = datetime.utcnow()
