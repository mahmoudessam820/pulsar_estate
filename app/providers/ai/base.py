from abc import ABC, abstractmethod
from typing import List, Dict


class AIProviderBase(ABC):
    @abstractmethod
    async def analyze(self, documents: List[Dict]) -> Dict:
        """Analyze a list of documents and return the analysis results."""
        raise NotImplementedError
