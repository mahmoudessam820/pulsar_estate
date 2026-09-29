from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.scheduler.scheduled_query_service import ScheduledQueryService
from app.data.repositories.base import (
    InsightRepositoryBase,
    UserRepositoryBase,
    UsageRepositoryBase,
    PipelineRunRepositoryBase,
    ScheduledQueryRepositoryBase,
    ApiKeyRepositoryBase,
)
from app.data.repositories.insight_repo import PostgresInsightRepository
from app.data.repositories.user_repo import PostgresUserRepository
from app.data.repositories.usage_tracking_repo import PostgresUsageRepository
from app.data.repositories.pipeline_run_repo import PostgresPipelineRunRepository
from app.data.repositories.scheduled_query_repo import PostgresScheduledQueryRepository
from app.data.repositories.api_key_repo import PostgresApiKeyRepository

from app.auth.auth_service import AuthService
from app.auth.api_key_service import ApiKeyService

from app.monetization.usage import UsageService
from app.monetization.entitlements import EntitlementService


def get_insight_repository(db: AsyncSession = Depends(get_db)) -> InsightRepositoryBase:
    return PostgresInsightRepository(db)


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    repo = PostgresUserRepository(db)
    return AuthService(repo)


def get_api_key_service(db: AsyncSession = Depends(get_db)) -> ApiKeyService:
    repo = PostgresApiKeyRepository(db)
    return ApiKeyService(repo)


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepositoryBase:
    return PostgresUserRepository(db)


def get_usage_repository(db: AsyncSession = Depends(get_db)) -> UsageRepositoryBase:
    return PostgresUsageRepository(db)


def get_entitlement_service(db: AsyncSession = Depends(get_db)) -> EntitlementService:
    usage_repo = PostgresUsageRepository(db)
    usage_service = UsageService(usage_repo)
    scheduled_query_repo = PostgresScheduledQueryRepository(db)
    return EntitlementService(usage_service, scheduled_query_repo)


def get_scheduled_query_service(
    db: AsyncSession = Depends(get_db),
) -> ScheduledQueryService:
    repo = PostgresScheduledQueryRepository(db)
    return ScheduledQueryService(repo)


def get_usage_service(db: AsyncSession = Depends(get_db)) -> UsageService:
    repo = PostgresUsageRepository(db)
    return UsageService(repo)


def get_pipeline_run_repository(
    db: AsyncSession = Depends(get_db),
) -> PipelineRunRepositoryBase:
    return PostgresPipelineRunRepository(db)


def get_scheduled_query_repository(
    db: AsyncSession = Depends(get_db),
) -> ScheduledQueryRepositoryBase:
    return PostgresScheduledQueryRepository(db)


def get_api_key_repository(db: AsyncSession = Depends(get_db)) -> ApiKeyRepositoryBase:
    return PostgresApiKeyRepository(db)
