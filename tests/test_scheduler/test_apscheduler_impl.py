import pytest

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.scheduler.job_status import JobStatus, pipeline_job_status
from app.scheduler.apscheduler_impl import APSchedulerService
from app.utils.redis_lock import (
    acquire_lock,
    release_lock,
    PIPLEINE_LOCK_KEY,
    LOCK_TTL,
)


# JobStatus Tests
class TestJobStatus:
    def test_job_status_initialization(self):
        status = JobStatus()

        assert status.last_run is None
        assert status.last_duration is None
        assert status.last_error is None

    def test_job_status_update_last_run(self):
        status = JobStatus()
        status.last_run = datetime.now(timezone.utc)

        assert status.last_run is not None

    def test_job_status_update_last_duration(self):
        status = JobStatus()
        status.last_duration = 1.5

        assert status.last_duration == 1.5

    def test_job_status_update_last_error(self):
        status = JobStatus()
        status.last_error = "Test error"

        assert status.last_error == "Test error"

    def test_pipeline_job_status_is_singleton(self):
        status1 = pipeline_job_status
        status2 = pipeline_job_status

        assert status1 is status2


# Redis Lock Tests
class TestAcquireLock:
    @pytest.mark.asyncio
    async def test_acquire_lock_success(self):
        with patch("app.utils.redis_lock.redis_client") as mock_redis:
            mock_redis.set = AsyncMock(return_value=True)

            result = await acquire_lock()

            assert result is True

            mock_redis.set.assert_called_once_with(
                PIPLEINE_LOCK_KEY, "locked", nx=True, ex=LOCK_TTL
            )

    @pytest.mark.asyncio
    async def test_acquire_lock_failure_already_locked(self):
        with patch("app.utils.redis_lock.redis_client") as mock_redis:
            mock_redis.set = AsyncMock(return_value=False)

            result = await acquire_lock()

            assert result is False

            mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_acquire_lock_generates_unique_token(self):
        with patch("app.utils.redis_lock.redis_client") as mock_redis:
            mock_redis.set = AsyncMock(return_value=True)

            await acquire_lock()
            token1 = acquire_lock.__globals__["lock_token"]

            await acquire_lock()
            token2 = acquire_lock.__globals__["lock_token"]

            assert token1 != token2


class TestReleaseLock:
    @pytest.mark.asyncio
    async def test_release_lock_success(self):
        with patch("app.utils.redis_lock.redis_client") as mock_redis:
            mock_redis.delete = AsyncMock(return_value=1)

            await release_lock()

            mock_redis.delete.assert_called_once_with(PIPLEINE_LOCK_KEY)

    @pytest.mark.asyncio
    async def test_release_lock_no_lock_held(self):
        with patch("app.utils.redis_lock.redis_client") as mock_redis:
            mock_redis.delete = AsyncMock(return_value=0)

            await release_lock()

            mock_redis.delete.assert_called_once()


# APSchedulerService Tests
class TestAPSchedulerService:
    def test_scheduler_initialization(self):
        service = APSchedulerService()

        assert service.scheduler is not None

    def test_start_scheduler(self):
        service = APSchedulerService()
        with patch.object(service.scheduler, "start") as mock_start:
            service.start()
            mock_start.assert_called_once()

    def test_shutdown_scheduler(self):
        service = APSchedulerService()
        with patch.object(service.scheduler, "shutdown") as mock_shutdown:
            service.shutdown()
            mock_shutdown.assert_called_once()

    def test_add_daily_job(self):
        service = APSchedulerService()
        dummy_func = AsyncMock()

        with patch.object(service.scheduler, "add_job") as mock_add_job:
            service.add_daily_job(dummy_func, minutes=10)

            mock_add_job.assert_called_once()
            call_args = mock_add_job.call_args
            assert call_args[0][0] == service._run_with_lock
            assert call_args[1]["minutes"] == 10
            assert call_args[1]["args"] == [dummy_func]
            assert call_args[1]["id"] == "interval_pipeline_job"
            assert call_args[1]["replace_existing"] is True

    def test_add_daily_job_default_minutes(self):
        service = APSchedulerService()
        dummy_func = AsyncMock()

        with patch.object(service.scheduler, "add_job") as mock_add_job:
            service.add_daily_job(dummy_func)

            call_args = mock_add_job.call_args
            assert call_args[1]["minutes"] == 5

    @pytest.mark.asyncio
    async def test_run_with_lock_success(self):
        service = APSchedulerService()
        mock_func = AsyncMock()

        with patch(
            "app.scheduler.apscheduler_impl.acquire_lock", AsyncMock(return_value=True)
        ):
            with patch("app.scheduler.apscheduler_impl.release_lock", AsyncMock()):
                await service._run_with_lock(mock_func)

                mock_func.assert_called_once()
                assert pipeline_job_status.last_error is None
                assert pipeline_job_status.last_duration is not None
                assert pipeline_job_status.last_run is not None

    @pytest.mark.asyncio
    async def test_run_with_lock_already_locked(self):
        service = APSchedulerService()
        mock_func = AsyncMock()

        with patch(
            "app.scheduler.apscheduler_impl.acquire_lock", AsyncMock(return_value=False)
        ):
            with patch(
                "app.scheduler.apscheduler_impl.release_lock", AsyncMock()
            ) as mock_release:
                await service._run_with_lock(mock_func)

                mock_func.assert_not_called()
                mock_release.assert_not_called()

    @pytest.mark.asyncio
    async def test_run_with_lock_exception_handling(self):
        service = APSchedulerService()
        mock_func = AsyncMock(side_effect=Exception("Test error"))

        with patch(
            "app.scheduler.apscheduler_impl.acquire_lock", AsyncMock(return_value=True)
        ):
            with patch("app.scheduler.apscheduler_impl.release_lock", AsyncMock()):
                with pytest.raises(Exception, match="Test error"):
                    await service._run_with_lock(mock_func)

                assert pipeline_job_status.last_error == "Test error"
                assert pipeline_job_status.last_duration is not None

    @pytest.mark.asyncio
    async def test_run_with_lock_updates_status(self):
        service = APSchedulerService()
        mock_func = AsyncMock()

        before_run = datetime.now(timezone.utc)

        with patch(
            "app.scheduler.apscheduler_impl.acquire_lock", AsyncMock(return_value=True)
        ):
            with patch("app.scheduler.apscheduler_impl.release_lock", AsyncMock()):
                await service._run_with_lock(mock_func)

                assert pipeline_job_status.last_run >= before_run
                assert pipeline_job_status.last_duration > 0
                assert pipeline_job_status.last_error is None


# Integration Tests
class TestSchedulerIntegration:
    def test_full_scheduler_lifecycle(self):
        service = APSchedulerService()

        with patch.object(service.scheduler, "start"):
            with patch.object(service.scheduler, "shutdown"):
                service.start()
                service.add_daily_job(AsyncMock(), minutes=30)
                service.shutdown()

    @pytest.mark.asyncio
    async def test_lock_acquire_release_flow(self):
        with patch("app.utils.redis_lock.redis_client") as mock_redis:
            mock_redis.set = AsyncMock(return_value=True)
            mock_redis.delete = AsyncMock(return_value=1)

            acquired = await acquire_lock()
            assert acquired is True

            await release_lock()
            mock_redis.delete.assert_called()
