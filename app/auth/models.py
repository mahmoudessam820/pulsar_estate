from datetime import datetime
from dataclasses import dataclass


@dataclass
class User:
    id: str
    email: str
    password_hash: str
    role: str = "user"  # user | developer | admin
    plan: str = "free"  # free | pro | enterprise
    is_active: bool = True
    created_at: datetime = None
