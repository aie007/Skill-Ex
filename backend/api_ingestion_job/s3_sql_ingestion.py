import json
import requests
import re
import os
import yaml
import sqlite3
import boto3
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class ConfigLoader:
    """Loads configuration from YAML and environment variables."""
    @staticmethod
    def load():
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
        # Inject secrets from .env
        config['api']['key'] = os.getenv("RAPIDAPI_KEY")
        config['aws']['key_id'] = os.getenv("AWS_ACCESS_KEY_ID")
        config['aws']['secret'] = os.getenv("AWS_SECRET_ACCESS_KEY")
        return config

class JobFetcher:
    """Handles all interactions with the JSearch API."""
    def __init__(self, config):
        self.config = config['api']

    def fetch_all_pages(self):
        all_jobs = []
        headers = {"x-rapidapi-key": self.config['key']}
        
        for p in range(1, self.config['total_pages'] + 1):
            try:
                params = {
                    "query": self.config['query'],
                    "page": p,
                    "num_pages": 1,
                    "country": self.config['country']
                }
                res = requests.get(self.config['url'], headers=headers, params=params, timeout=self.config['timeout'])
                res.raise_for_status()
                batch = res.json().get('data', [])
                all_jobs.extend(batch)
                print(f"Successfully fetched page {p}/{self.config['total_pages']}")
            except Exception as e:
                print(f"Skipping page {p} due to error: {e}")
        return all_jobs

class SkillExtractor:
    """Processes text using optimized Regex matching."""
    def __init__(self, skill_list):
        self.skill_list = skill_list
        # Escape symbols like C++ and join with word boundaries
        pattern_string = r'\b(' + '|'.join(map(re.escape, skill_list)) + r')\b'
        self.pattern = re.compile(pattern_string, re.IGNORECASE)

    def extract(self, text):
        if not text: return []
        matches = self.pattern.findall(text)
        # Normalize casing based on the original YAML list
        return list(set(next((s for s in self.skill_list if s.lower() == m.lower()), m) for m in matches))

class StorageProvider:
    """Handles all cloud storage (S3) operations."""
    def __init__(self, config):
        self.aws_cfg = config['aws']
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=self.aws_cfg['key_id'],
            aws_secret_access_key=self.aws_cfg['secret']
        )

    def upload_json(self, bucket, key, data):
        self.s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(data, indent=2))

    def backup_database(self, bucket, db_name):
        with open(db_name, 'rb') as f:
            self.s3.put_object(Bucket=bucket, Key=f"db_backups/{db_name}", Body=f)


class ExperienceExtractor:
    """Responsibility: Identify seniority level and years of experience."""
    def __init__(self, levels_config):
        self.levels = levels_config
        # Pattern to find years of experience (e.g., "5+ years", "3-5 years")
        self.years_pattern = re.compile(r'(\d+)\s*(?:\+|-|\sto\s)?\s*\d*\s*years?', re.IGNORECASE)

    def extract(self, title, description):
        # 1. Check title for explicit seniority keywords
        for level, pattern in self.levels.items():
            if re.search(pattern, title, re.IGNORECASE):
                return level.capitalize()

        # 2. Check description for years of experience
        match = self.years_pattern.search(description)
        if match:
            years = int(match.group(1))
            if years < 2: return "Junior"
            if 2 <= years <= 5: return "Mid"
            return "Senior"
        
        return "Not Specified"

class DatabaseRepo:
    """Handles local persistence in SQLite (Updated for experience)."""
    def __init__(self, db_name):
        self.db_name = db_name

    def initialize(self):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            # Added experience column to jobs table
            c.execute('''CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY, 
                title TEXT, 
                company TEXT, 
                posted_at DATETIME, 
                experience_level TEXT, 
                raw_ref TEXT)''')
            c.execute('CREATE TABLE IF NOT EXISTS skills (skill_id INTEGER PRIMARY KEY AUTOINCREMENT, skill_name TEXT UNIQUE)')
            c.execute('CREATE TABLE IF NOT EXISTS job_skills (job_id TEXT, skill_id INTEGER, UNIQUE(job_id, skill_id))')

    def save_results(self, processed_list):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            for entry in processed_list:
                # Updated INSERT to include experience_level
                c.execute("INSERT OR IGNORE INTO jobs VALUES (?, ?, ?, ?, ?, ?)", 
                          (entry['source_id'], entry['title'], entry['company'], 
                           entry['date'], entry['experience'], entry['raw_ref']))
                for skill in entry['skills']:
                    c.execute("INSERT OR IGNORE INTO skills (skill_name) VALUES (?)", (skill,))
                    c.execute("SELECT skill_id FROM skills WHERE skill_name = ?", (skill,))
                    s_id = c.fetchone()[0]
                    c.execute("INSERT OR IGNORE INTO job_skills VALUES (?, ?)", (entry['source_id'], s_id))

class Orchestrator:
    """The 'Main' controller (Updated to include Experience Extraction)."""
    def __init__(self):
        self.config = ConfigLoader.load()
        self.fetcher = JobFetcher(self.config)
        self.extractor = SkillExtractor(self.config['skills'])
        self.exp_extractor = ExperienceExtractor(self.config.get('experience_levels', {})) # New
        self.storage = StorageProvider(self.config)
        self.db = DatabaseRepo(self.config['database']['name'])

    def run(self):
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
        self.db.initialize()

        raw_jobs = self.fetcher.fetch_all_pages()
        if not raw_jobs: return

        raw_key = f"raw/jobs_{timestamp}.json"
        self.storage.upload_json(self.config['aws']['raw_bucket'], raw_key, {"data": raw_jobs})

        processed = []
        for job in raw_jobs:
            desc = job.get("job_description", "")
            title = job.get("job_title", "")
            
            # Extract both Skills and Experience
            skills = self.extractor.extract(desc)
            exp_level = self.exp_extractor.extract(title, desc) # New logic
            
            processed.append({
                "title": title,
                "company": job.get("employer_name"),
                "skills": skills,
                "experience": exp_level, # New field
                "date": job.get("job_posted_at_datetime_utc"),
                "source_id": job.get("job_id"),
                "raw_ref": raw_key
            })

        self.storage.upload_json(self.config['aws']['processed_bucket'], f"processed/jobs_{timestamp}.json", processed)
        self.db.save_results(processed)
        self.storage.backup_database(self.config['aws']['processed_bucket'], self.config['database']['name'])
        
        print(f"Pipeline finished. Experience levels tagged.")

# ... (main block stays the same)
if __name__ == "__main__":
    Orchestrator().run()