import sqlite3
import json
import os
from typing import Dict, Any, Optional

DB_PATH = os.path.expanduser("~/.multicliswarm.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            task TEXT,
            language TEXT,
            specification TEXT,
            files_map TEXT,
            final_files TEXT,
            cost_usd REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_session(session_id: str, task: str, language: str, specification: str, files_map: list, final_files: dict, cost: float):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO sessions 
        (session_id, task, language, specification, files_map, final_files, cost_usd)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        session_id, 
        task, 
        language, 
        specification, 
        json.dumps([fm.dict() for fm in files_map]), 
        json.dumps(final_files), 
        cost
    ))
    conn.commit()
    conn.close()

def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
        
    return {
        "session_id": row[0],
        "task": row[1],
        "language": row[2],
        "specification": row[3],
        "files_map": json.loads(row[4]),
        "final_files": json.loads(row[5]),
        "cost_usd": row[6],
        "timestamp": row[7]
    }
