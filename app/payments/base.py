from abc import ABC, abstractmethod


class PaymentGatewayBase(ABC):
    @abstractmethod
    async def create_subscription(self, user_id: str, plan: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def cancel_subscription(self, subscription_id: str) -> dict:
        raise NotImplementedError
