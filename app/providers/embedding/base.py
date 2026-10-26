from typing import List
from abc import ABC, abstractmethod


class EmbeddingProviderBase(ABC):
    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generates a dense vector embedding for the given text."""
        raise NotImplementedError
