# app/api/schemas/__init__.py
from .admin import (
    RunPipelineRequest,
    PipelineRunResponse,
    UpgradeRoleRequest,
    DowngradeRoleRequest,
    DowngradeRoleResponse,
    RoleUpdateResponse,
    UpgradePlanRequest,
    PlanUpdateResponse,
    DowngradePlanRequest,
    DowngradePlanResponse,
    AdminErrorResponse,
)
from .auth import RegisterRequest, loginRequest, AuthResponse, UserPublic
from .insights import InsightResponse
from .insights_history import InsightsHistory, InsightsHistoryItem
from .insight_topic import (
    InsightTopicResponse,
    TopicVersion,
    TopicItem,
    ConfidenceMetrics,
)
from .pipeline import PipelineRunRequest
from .scheduler_status import SchedulerStatusResponse

__all__ = [
    # Admin Schemas
    "RunPipelineRequest",
    "PipelineRunResponse",
    "UpgradeRoleRequest",
    "DowngradeRoleRequest",
    "DowngradeRoleResponse",
    "RoleUpdateResponse",
    "UpgradePlanRequest",
    "PlanUpdateResponse",
    "DowngradePlanRequest",
    "DowngradePlanResponse",
    "AdminErrorResponse",
    # Auth Schemas
    "RegisterRequest",
    "loginRequest",
    "AuthResponse",
    "UserPublic",
    # Insight Schemas
    "InsightResponse",
    # Insight Topic Schemas
    "InsightTopicResponse",
    "TopicVersion",
    "TopicItem",
    "ConfidenceMetrics",
    # Insights History Schemas
    "InsightsHistory",
    "InsightsHistoryItem",
    # Pipeline Schemas
    "PipelineRunRequest",
    # Scheduler Status Schemas
    "SchedulerStatusResponse",
]
