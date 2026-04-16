from abc import ABC, abstractmethod


class SchedulerBase(ABC):
    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def add_daily_job(self, func, minutes: int) -> None:
        raise NotImplementedError
