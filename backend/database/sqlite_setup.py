import sqlite3

def init_db(db_path="job_market.db"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # 1. Create Jobs table
    c.execute('''CREATE TABLE IF NOT EXISTS jobs (
        job_id TEXT PRIMARY KEY,
        title TEXT,
        company TEXT,
        posted_at DATETIME,
        raw_ref TEXT
    )''')

    # 2. Create Skills table
    c.execute('''CREATE TABLE IF NOT EXISTS skills (
        skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
        skill_name TEXT UNIQUE
    )''')

    # 3. Create Bridge table for trends
    c.execute('''CREATE TABLE IF NOT EXISTS job_skills (
        job_id TEXT,
        skill_id INTEGER,
        FOREIGN KEY(job_id) REFERENCES jobs(job_id),
        FOREIGN KEY(skill_id) REFERENCES skills(skill_id),
        UNIQUE(job_id, skill_id)
    )''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

init_db()