from abc import ABC, abstractmethod
from typing import Dict

class BaseIngestor(ABC):
    """Abstract base class for content ingestion."""

    @abstractmethod
    def fetch_content(self, identifier: str) -> Dict:
        """Fetch content based on identifier."""
        pass

    @abstractmethod
    def parse_content(self, raw_content: Dict) -> Dict:
        """Parse raw content into structured format."""
        pass

    def ingest(self, identifier: str) -> Dict:
        """Complete ingestion pipeline."""
        raw_content = self.fetch_content(identifier)
        return self.parse_content(raw_content)
