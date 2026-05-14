import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional
from shared.core.interfaces import IDataRepository
from shared.config.settings import settings

class SQLiteRepository(IDataRepository):
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.database.name

    def initialize(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY, 
                title TEXT, 
                company TEXT, 
                posted_at DATETIME, 
                experience_level TEXT, 
                raw_ref TEXT)''')
            c.execute('CREATE TABLE IF NOT EXISTS skills (skill_id INTEGER PRIMARY KEY AUTOINCREMENT, skill_name TEXT UNIQUE)')
            c.execute('CREATE TABLE IF NOT EXISTS job_skills (job_id TEXT, skill_id INTEGER, UNIQUE(job_id, skill_id))')
            conn.commit()

    def save_jobs(self, jobs: List[Dict[str, Any]]):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            for entry in jobs:
                c.execute("INSERT OR IGNORE INTO jobs VALUES (?, ?, ?, ?, ?, ?)", 
                          (entry['source_id'], entry['title'], entry['company'], 
                           entry['date'], entry['experience'], entry['raw_ref']))
                for skill in entry['skills']:
                    c.execute("INSERT OR IGNORE INTO skills (skill_name) VALUES (?)", (skill,))
                    c.execute("SELECT skill_id FROM skills WHERE skill_name = ?", (skill,))
                    res = c.fetchone()
                    if res:
                        s_id = res[0]
                        c.execute("INSERT OR IGNORE INTO job_skills VALUES (?, ?)", (entry['source_id'], s_id))
            conn.commit()

    def get_all_jobs(self) -> pd.DataFrame:
        conn = sqlite3.connect(self.db_path)
        query = """
        SELECT j.job_id, j.title, j.company, GROUP_CONCAT(s.skill_name, ' ') as skill_set
        FROM jobs j
        LEFT JOIN job_skills js ON j.job_id = js.job_id
        LEFT JOIN skills s ON js.skill_id = s.skill_id
        GROUP BY j.job_id
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def get_job_details(self, job_ids: List[str]) -> pd.DataFrame:
        conn = sqlite3.connect(self.db_path)
        placeholders = ','.join(['?'] * len(job_ids))
        query = f"SELECT * FROM jobs WHERE job_id IN ({placeholders})"
        df = pd.read_sql_query(query, conn, params=job_ids)
        conn.close()
        return df

    def get_trend_data(self) -> pd.DataFrame:
        conn = sqlite3.connect(self.db_path)
        query = """
        SELECT 
            j.posted_at,
            s.skill_name
        FROM jobs j
        JOIN job_skills js ON j.job_id = js.job_id
        JOIN skills s ON js.skill_id = s.skill_id
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        df['posted_at'] = pd.to_datetime(df['posted_at'])
        return df
