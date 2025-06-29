from ingestion.base_ingestor import BaseIngestor
import requests
from utils.logger import logger

class MSDocsIngestor(BaseIngestor):
    def fetch_content(self, doc_url: str) -> Dict:
        try:
            response = requests.get(doc_url, timeout=10)
            response.raise_for_status()
            return {"html": response.text}
        except requests.RequestException as e:
            logger.error(f"Failed to fetch MS Docs content: {e}")
            raise ContentFetchError(f"MS Docs fetch failed: {e}")

    def parse_content(self, raw_content: Dict) -> Dict:
        # Implement parsing logic specific to MS Docs HTML structure
        pass
