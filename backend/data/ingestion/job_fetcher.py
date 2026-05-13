import requests
from typing import List, Dict, Any
from backend.core.interfaces import IJobFetcher
from backend.config.settings import settings

class JSearchFetcher(IJobFetcher):
    def __init__(self, api_config=None):
        self.config = api_config or settings.api

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        all_jobs = []
        headers = {"x-rapidapi-key": self.config.key}
        
        for p in range(1, self.config.total_pages + 1):
            try:
                params = {
                    "query": self.config.query,
                    "page": p,
                    "num_pages": 1,
                    "country": self.config.country
                }
                res = requests.get(self.config.url, headers=headers, params=params, timeout=self.config.timeout)
                res.raise_for_status()
                batch = res.json().get('data', [])
                all_jobs.extend(batch)
            except Exception as e:
                print(f"Skipping page {p} due to error: {e}")
        return all_jobs
