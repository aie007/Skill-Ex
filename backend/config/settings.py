import os
import yaml
from typing import List, Dict, Any, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class APISettings(BaseSettings):
    url: str = "https://jsearch.p.rapidapi.com/search"
    query: str = "software developer in India"
    total_pages: int = 30
    timeout: int = 50
    country: str = "in"
    key: Optional[str] = Field(None, alias="RAPIDAPI_KEY")

class AWSSettings(BaseSettings):
    key_id: Optional[str] = Field(None, alias="AWS_ACCESS_KEY_ID")
    secret: Optional[str] = Field(None, alias="AWS_SECRET_ACCESS_KEY")
    raw_bucket: str = "amzn-s3-raw-bucket-skillex"
    processed_bucket: str = "amzn-s3-processed-bucket-skillex"

class DatabaseSettings(BaseSettings):
    name: str = "job_market.db"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    api: APISettings = APISettings()
    aws: AWSSettings = AWSSettings()
    database: DatabaseSettings = DatabaseSettings()
    experience_levels: Dict[str, str] = {
        "senior": "Senior|Lead|Principal|Staff|Architect",
        "mid": "Mid|Intermediate|Experienced",
        "junior": "Junior|Entry|Associate|Graduate|Intern"
    }
    skills: List[str] = []

    @classmethod
    def load_config(cls, yaml_path: str = "backend/config/config.yaml") -> "Settings":
        if os.path.exists(yaml_path):
            with open(yaml_path, "r") as f:
                yaml_data = yaml.safe_load(f)
        else:
            yaml_data = {}

        # Merge YAML data into settings
        settings = cls(**yaml_data)
        return settings

# Singleton instance
settings = Settings.load_config()
