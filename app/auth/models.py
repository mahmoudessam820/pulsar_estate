from typing import Optional
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
    created_at: Optional[datetime] = None
    subscription_id: Optional[str] = None
    subscription_status: str = "inactive"
    current_period_end: Optional[datetime] = None
    updated_at: Optional[datetime] = None
