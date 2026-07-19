import sqlite3
import json
import os
from typing import Dict, Any, Optional, List

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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS snapshots (
            snapshot_id TEXT PRIMARY KEY,
            session_id TEXT,
            label TEXT,
            specification TEXT,
            final_files TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(session_id) REFERENCES sessions(session_id)
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
        json.dumps([fm.model_dump() for fm in files_map]), 
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

def create_snapshot(session_id: str, label: str, specification: str, final_files: dict):
    import uuid
    init_db()
    snapshot_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO snapshots (snapshot_id, session_id, label, specification, final_files)
        VALUES (?, ?, ?, ?, ?)
    ''', (snapshot_id, session_id, label, specification, json.dumps(final_files)))
    conn.commit()
    conn.close()
    return snapshot_id

def list_snapshots(session_id: str) -> List[Dict[str, Any]]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT snapshot_id, label, timestamp FROM snapshots WHERE session_id = ? ORDER BY timestamp DESC", (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "label": r[1], "date": r[2]} for r in rows]

def load_snapshot(snapshot_id: str) -> Optional[Dict[str, Any]]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT specification, final_files FROM snapshots WHERE snapshot_id = ?", (snapshot_id,))
    row = cursor.fetchone()
    conn.close()
    if not row: return None
    return {"specification": row[0], "final_files": json.loads(row[1])}
