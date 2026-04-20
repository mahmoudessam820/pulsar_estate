import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.scheduler.bootstrap import scheduler, start_scheduler, shutdown_scheduler
from app.scheduler.apscheduler_impl import APSchedulerService
from app.core.pipeline.pipeline_tasks import run_daily_pipeline


# Scheduler Instance Tests
class TestSchedulerInstance:
    def test_scheduler_is_singleton_instance(self):
        assert scheduler is not None
        assert isinstance(scheduler, APSchedulerService)

    def test_scheduler_instance_is_consistent(self):
        from app.scheduler.bootstrap import scheduler as scheduler2

        assert scheduler is scheduler2


# Start Scheduler Tests
class TestStartScheduler:
    @pytest.mark.asyncio
    async def test_start_scheduler_adds_job_and_starts(self):
        with patch.object(scheduler, "add_daily_job") as mock_add_job:
            with patch.object(scheduler, "start") as mock_start:
                await start_scheduler()

                mock_add_job.assert_called_once_with(run_daily_pipeline, minutes=5)
                mock_start.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_scheduler_with_custom_pipeline_function(self):
        custom_func = AsyncMock()

        with patch.object(scheduler, "add_daily_job") as mock_add_job:
            with patch.object(scheduler, "start") as mock_start:
                scheduler.add_daily_job(custom_func, minutes=10)
                await start_scheduler()

                assert mock_add_job.call_count >= 1

    @pytest.mark.asyncio
    async def test_start_scheduler_job_interval(self):
        with patch.object(scheduler, "add_daily_job") as mock_add_job:
            with patch.object(scheduler, "start"):
                await start_scheduler()

                call_args = mock_add_job.call_args
                assert call_args[1]["minutes"] == 5  # minutes=5


# Shutdown Scheduler Tests
class TestShutdownScheduler:
    @pytest.mark.asyncio
    async def test_shutdown_scheduler_calls_shutdown(self):
        with patch.object(scheduler, "shutdown") as mock_shutdown:
            await shutdown_scheduler()
            mock_shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_scheduler_multiple_times(self):
        with patch.object(scheduler, "shutdown") as mock_shutdown:
            await shutdown_scheduler()
            await shutdown_scheduler()

            assert mock_shutdown.call_count == 2


# Edge Cases
class TestEdgeCases:
    @pytest.mark.asyncio
    async def test_start_then_shutdown(self):
        with patch.object(scheduler, "add_daily_job"):
            with patch.object(scheduler, "start"):
                with patch.object(scheduler, "shutdown") as mock_shutdown:
                    await start_scheduler()
                    await shutdown_scheduler()

                    mock_shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_without_start(self):
        with patch.object(scheduler, "shutdown") as mock_shutdown:
            await shutdown_scheduler()
            mock_shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_scheduler_twice(self):
        with patch.object(scheduler, "add_daily_job") as mock_add_job:
            with patch.object(scheduler, "start") as mock_start:
                await start_scheduler()
                await start_scheduler()

                assert mock_add_job.call_count == 2
                assert mock_start.call_count == 2


# Invalid Inputs / Error Handling
class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_start_scheduler_with_failing_add_job(self):
        with patch.object(
            scheduler, "add_daily_job", side_effect=Exception("Job failed")
        ):
            with patch.object(scheduler, "start"):
                with pytest.raises(Exception, match="Job failed"):
                    await start_scheduler()

    @pytest.mark.asyncio
    async def test_start_scheduler_with_failing_start(self):
        with patch.object(scheduler, "add_daily_job"):
            with patch.object(
                scheduler, "start", side_effect=Exception("Start failed")
            ):
                with pytest.raises(Exception, match="Start failed"):
                    await start_scheduler()

    @pytest.mark.asyncio
    async def test_shutdown_scheduler_with_failing_shutdown(self):
        with patch.object(
            scheduler, "shutdown", side_effect=Exception("Shutdown failed")
        ):
            with pytest.raises(Exception, match="Shutdown failed"):
                await shutdown_scheduler()

    @pytest.mark.asyncio
    async def test_pipeline_function_is_passed_correctly(self):
        with patch.object(scheduler, "add_daily_job") as mock_add_job:
            with patch.object(scheduler, "start"):
                await start_scheduler()

                assert mock_add_job.call_args[0][0] == run_daily_pipeline


# Integration Tests
class TestSchedulerIntegration:
    @pytest.mark.asyncio
    async def test_full_lifecycle(self):
        with patch.object(scheduler, "add_daily_job") as mock_add_job:
            with patch.object(scheduler, "start") as mock_start:
                with patch.object(scheduler, "shutdown") as mock_shutdown:
                    await start_scheduler()
                    assert mock_add_job.called
                    assert mock_start.called

                    await shutdown_scheduler()
                    assert mock_shutdown.called

    @pytest.mark.asyncio
    async def test_scheduler_state_after_operations(self):
        with patch.object(scheduler, "add_daily_job"):
            with patch.object(scheduler, "start"):
                with patch.object(scheduler, "shutdown"):
                    await start_scheduler()
                    await shutdown_scheduler()

                    assert scheduler is not None
