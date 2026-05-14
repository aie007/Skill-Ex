from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd

class IDataRepository(ABC):
    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def save_jobs(self, jobs: List[Dict[str, Any]]):
        pass

    @abstractmethod
    def get_all_jobs(self) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_job_details(self, job_ids: List[str]) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_trend_data(self) -> pd.DataFrame:
        pass

class IJobFetcher(ABC):
    @abstractmethod
    def fetch_jobs(self) -> List[Dict[str, Any]]:
        pass

class ISkillExtractor(ABC):
    @abstractmethod
    def extract(self, text: str) -> List[str]:
        pass

class IRecommender(ABC):
    @abstractmethod
    def train(self):
        pass

    @abstractmethod
    def recommend(self, user_skills: str, top_n: int = 5) -> tuple[List[Dict[str, Any]], List[str]]:
        pass

class ITrendEngine(ABC):
    @abstractmethod
    def get_timeseries_trends(self, df: pd.DataFrame, freq: str = 'D') -> pd.DataFrame:
        pass

    @abstractmethod
    def calculate_momentum(self, trend_df: pd.DataFrame, window: int = 3) -> pd.Series:
        pass
