from typing import Dict, Any, List
from abc import ABC, abstractmethod

class BaseEcosystemConnector(ABC):
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Verifies API connection to the external partner platform."""
        pass

    @abstractmethod
    async def map_record_to_schema(self, raw_record: Dict[str, Any], schema_type: str) -> Dict[str, Any]:
        """Translates third-party payload into standard DecentralID credential claims."""
        pass

    @abstractmethod
    async def process_sync_batch(self, records: List[Dict[str, Any]], schema_type: str) -> Dict[str, Any]:
        """Validates, deduplicates, and stages ingestion records."""
        pass
