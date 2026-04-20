import pytest

from abc import ABC, abstractmethod
from typing import Callable


class SchedulerBase(ABC):
    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def add_daily_job(self, func: Callable, minutes: int) -> None:
        raise NotImplementedError


# Concrete implementation for testing purposes
class TestScheduler(SchedulerBase):
    def __init__(self):
        self.started = False
        self.shutdown_called = False
        self.jobs = []

    def start(self) -> None:
        self.started = True

    def shutdown(self) -> None:
        self.shutdown_called = True

    def add_daily_job(self, func: Callable, minutes: int) -> None:
        if func is None:
            raise TypeError("func cannot be None")
        if not callable(func):
            raise TypeError("func must be callable")
        if not isinstance(minutes, int):
            raise TypeError("minutes must be an integer")
        if minutes < 0:
            raise ValueError("minutes cannot be negative")
        self.jobs.append((func, minutes))


# Test that abstract class cannot be instantiated
def test_cannot_instantiate_abstract_class():
    with pytest.raises(TypeError):
        SchedulerBase()


# Test normal expected inputs
def test_start_scheduler():
    scheduler = TestScheduler()
    scheduler.start()

    assert scheduler.started is True


def test_shutdown_scheduler():
    scheduler = TestScheduler()
    scheduler.shutdown()

    assert scheduler.shutdown_called is True


def test_add_daily_job_normal_input():
    scheduler = TestScheduler()
    dummy_func = lambda: None
    scheduler.add_daily_job(dummy_func, 60)

    assert len(scheduler.jobs) == 1
    assert scheduler.jobs[0] == (dummy_func, 60)


def test_start_then_shutdown():
    scheduler = TestScheduler()
    scheduler.start()
    scheduler.shutdown()

    assert scheduler.started is True
    assert scheduler.shutdown_called is True


def test_add_multiple_jobs():
    scheduler = TestScheduler()
    func1 = lambda: None
    func2 = lambda: None
    scheduler.add_daily_job(func1, 30)
    scheduler.add_daily_job(func2, 90)

    assert len(scheduler.jobs) == 2


# Edge cases
def test_add_daily_job_zero_minutes():
    scheduler = TestScheduler()
    dummy_func = lambda: None
    scheduler.add_daily_job(dummy_func, 0)

    assert len(scheduler.jobs) == 1
    assert scheduler.jobs[0][1] == 0


def test_add_daily_job_large_minutes():
    scheduler = TestScheduler()
    dummy_func = lambda: None
    scheduler.add_daily_job(dummy_func, 1440)  # 24 hours

    assert len(scheduler.jobs) == 1
    assert scheduler.jobs[0][1] == 1440


def test_shutdown_without_start():
    scheduler = TestScheduler()
    scheduler.shutdown()

    assert scheduler.shutdown_called is True


def test_start_multiple_times():
    scheduler = TestScheduler()
    scheduler.start()
    scheduler.start()

    assert scheduler.started is True


# Invalid inputs
def test_add_daily_job_negative_minutes():
    scheduler = TestScheduler()
    dummy_func = lambda: None

    with pytest.raises(ValueError):
        scheduler.add_daily_job(dummy_func, -1)


def test_add_daily_job_invalid_type_minutes():
    scheduler = TestScheduler()
    dummy_func = lambda: None

    with pytest.raises(TypeError):
        scheduler.add_daily_job(dummy_func, "60")


def test_add_daily_job_none_function():
    scheduler = TestScheduler()

    with pytest.raises(TypeError):
        scheduler.add_daily_job(None, 60)


def test_add_daily_job_float_minutes():
    scheduler = TestScheduler()
    dummy_func = lambda: None

    with pytest.raises(TypeError):
        scheduler.add_daily_job(dummy_func, 60.5)
