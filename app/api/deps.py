from app.data.repositories.base import (
    InsightRepositoryBase,
    InsightsHistoryRepositoryBase,
)
from app.data.repositories.insight_repo import JSONInsightRepository
from app.data.repositories.insights_history_repo import InsightsHistoryRepository
from app.data.repositories.user_repo import JSONUserRepository
from app.auth.auth_service import AuthService
from app.data.repositories.usage_repo import JSONUsageRepository
from app.monetization.usage import UsageService
from app.monetization.entitlements import EntitlementService


def get_insight_repository() -> InsightRepositoryBase:
    return JSONInsightRepository()


def get_insights_history_repository() -> InsightsHistoryRepositoryBase:
    return InsightsHistoryRepository()


def get_auth_service() -> AuthService:
    repo = JSONUserRepository()
    return AuthService(repo)


def get_user_repository() -> JSONUserRepository:
    return JSONUserRepository()


def get_entitlement_service() -> EntitlementService:
    usage_repo = JSONUsageRepository()
    usage_service = UsageService(usage_repo)
    return EntitlementService(usage_service)
