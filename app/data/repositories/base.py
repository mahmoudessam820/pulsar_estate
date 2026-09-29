import uuid
from abc import ABC, abstractmethod
from datetime import datetime, time
from typing import Dict, Optional, List

from app.data.models.users import User
from app.data.models.api_keys import ApiKey
from app.data.models.insights import Insight
from app.data.models.pipeline_runs import PipelineRun
from app.data.models.usage_tracking import UsageTracking
from app.data.models.scheduled_queries import ScheduledQuery


class InsightRepositoryBase(ABC):
    """
    Abstract base class for insight repository operations.
    All insight-related data access methods should be implemented in subclasses.
    """

    @abstractmethod
    async def save(self, data: Dict[str, str], user_id: Optional[str] = None) -> Dict:
        """Save insight data to the repository."""
        raise NotImplementedError

    @abstractmethod
    async def load_latest(self) -> Optional[Insight]:
        """Load the latest insight data from the repository."""
        raise NotImplementedError

    @abstractmethod
    async def load_latest_for_user(self, user_id: uuid.UUID) -> Optional[Insight]:
        """Load the latest insight data for a specific user from the repository."""
        raise NotImplementedError


class UserRepositoryBase(ABC):
    """
    Abstract base class for user repository operations.
    All user-related data access methods should be implemented in subclasses.
    """

    @abstractmethod
    async def create(self, user: User) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_users(self) -> List[User]:
        raise NotImplementedError

    @abstractmethod
    async def update_user(self, user_id: str, user_data: dict) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update_role(self, user_id: str, role: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update_plan(self, user_id: str, plan: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        raise NotImplementedError

    @abstractmethod
    async def update_subscription(self, user_id: str, subscription_data: Dict) -> None:
        raise NotImplementedError


class UsageRepositoryBase(ABC):
    """
    Abstract base class for usage tracking repository operations.
    All usage-related data access methods should be implemented in subclasses.
    """

    @abstractmethod
    async def count_today(self, user_id: str, metric_type: str = "pipeline_run") -> int:
        """Count usage for today for a specific metric type."""
        raise NotImplementedError

    @abstractmethod
    async def increment(self, user_id: str, metric_type: str = "pipeline_run") -> None:
        """Increment usage count for today using UPSERT."""
        raise NotImplementedError

    @abstractmethod
    async def get_usage_history(
        self, user_id: str, metric_type: str, days: int = 30
    ) -> List[UsageTracking]:
        """Get usage history for the last N days."""
        raise NotImplementedError


class PipelineRunRepositoryBase(ABC):
    """
    Abstract base class for pipeline run repository operations.
    All pipeline run-related data access methods should be implemented in subclasses.
    """

    @abstractmethod
    async def create_run(self, user_id: Optional[str] = None) -> PipelineRun:
        """Create a new pipeline run record with status='pending'."""
        raise NotImplementedError

    @abstractmethod
    async def update_run_status(
        self,
        run_id: str,
        status: str,
        insight_id: Optional[str] = None,
        error: Optional[str] = None,
        duration_seconds: Optional[float] = None,
    ) -> None:
        """Update run status, optionally with insight_id, error, or duration."""
        raise NotImplementedError

    @abstractmethod
    async def get_run(self, run_id: str) -> Optional[PipelineRun]:
        """Get a specific pipeline run by ID."""
        raise NotImplementedError

    @abstractmethod
    async def get_recent_runs(self, limit: int = 20) -> List[PipelineRun]:
        """Get recent pipeline runs, ordered by started_at DESC."""
        raise NotImplementedError


class ScheduledQueryRepositoryBase(ABC):
    """
    Abstract base class for scheduled query repository operations.
    All scheduled query-related data access methods should be implemented in subclasses.
    """

    @abstractmethod
    async def create(
        self,
        user_id: str,
        query_text: str,
        execution_time: time,
        timezone: str = "UTC",
        next_run_at: datetime = None,
    ) -> ScheduledQuery:
        """Create a new scheduled query."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_user(self, user_id: str) -> List[ScheduledQuery]:
        """Get all scheduled queries for a user."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, query_id: str) -> List[ScheduledQuery]:
        """Get a specific scheduled query by ID."""
        raise NotImplementedError

    @abstractmethod
    async def get_due_queries(self) -> List[ScheduledQuery]:
        """Get all queries where next_run_at <= NOW() and is_active = true."""
        raise NotImplementedError

    @abstractmethod
    async def update_next_run(self, query_id: str, next_run_at: datetime) -> None:
        """Update the next_run_at timestamp after execution."""
        raise NotImplementedError

    @abstractmethod
    async def toggle_active(self, query_id: str, is_active: bool) -> None:
        """Pause or resume a scheduled query."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, query_id: str) -> None:
        """Delete a scheduled query."""
        raise NotImplementedError

    @abstractmethod
    async def count_active_by_user(self, user_id: str) -> int:
        """Count active scheduled queries for a user (for quota enforcement)."""
        raise NotImplementedError

    @abstractmethod
    async def mark_as_completed(self, query_id: str) -> None:
        """Marks a scheduled query as completed (is_active = False)."""
        raise NotImplementedError

    @abstractmethod
    async def push_back_next_run(self, query_id: str, hours: int = 24) -> None:
        """Handles execution failure by pushing the next_run_at time into the future."""
        raise NotImplementedError


class ApiKeyRepositoryBase(ABC):
    """
    Abstract base class for API key repository operations.
    All API key-related data access methods should be implemented in subclasses.
    """

    @abstractmethod
    async def create(
        self, user_id: str, name: str, hashed_key: str, prefix: str
    ) -> ApiKey:
        """Create a new API key."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, api_key_id: str) -> Optional[ApiKey]:
        """Get a specific API key by ID."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_user(self, user_id: str) -> List[ApiKey]:
        """Get all API keys for a user."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_hashed_key(self, hashed_key: str) -> Optional[ApiKey]:
        """Get an API key by its hashed value (for authentication)."""
        raise NotImplementedError

    @abstractmethod
    async def revoke(self, api_key_id: str) -> None:
        """Revoke an API key (set is_active = false)."""
        raise NotImplementedError

    @abstractmethod
    async def update_last_used(self, api_key_id: str) -> None:
        """Update the last_used_at timestamp."""
        raise NotImplementedError

    @abstractmethod
    async def count_active_by_user(self, user_id: str) -> int:
        """Count active API keys for a user (for quota enforcement)."""
        raise NotImplementedError
