import sqlite3
import json
import os
from typing import Dict, Any, Optional, List
from .config import settings

def init_db():
    conn = sqlite3.connect(settings.DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            task TEXT,
            language TEXT,
            status TEXT DEFAULT 'idle',
            specification TEXT,
            files_map TEXT,
            final_files TEXT,
            cost_usd REAL DEFAULT 0.0,
            metadata TEXT,
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

def save_session(session_id: str, task: str, language: str, status: str = "completed", 
                 specification: str = "", files_map: list = None, final_files: dict = None, 
                 cost: float = 0.0, meta: dict = None):
    init_db()
    conn = sqlite3.connect(settings.DB_PATH)
    cursor = conn.cursor()
    
    files_map_json = json.dumps([fm.model_dump() for fm in files_map]) if files_map else "[]"
    final_files_json = json.dumps(final_files) if final_files else "{}"
    meta_json = json.dumps(meta) if meta else "{}"
    
    cursor.execute('''
        INSERT OR REPLACE INTO sessions 
        (session_id, task, language, status, specification, files_map, final_files, cost_usd, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (session_id, task, language, status, specification, files_map_json, final_files_json, cost, meta_json))
    conn.commit()
    conn.close()

def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    init_db()
    conn = sqlite3.connect(settings.DB_PATH)
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
        "status": row[3],
        "specification": row[4],
        "files_map": json.loads(row[5]),
        "final_files": json.loads(row[6]),
        "cost_usd": row[7],
        "metadata": json.loads(row[8]),
        "timestamp": row[9]
    }

def create_snapshot(session_id: str, label: str, specification: str, final_files: dict):
    import uuid
    init_db()
    snapshot_id = str(uuid.uuid4())
    conn = sqlite3.connect(settings.DB_PATH)
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
    conn = sqlite3.connect(settings.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT snapshot_id, label, timestamp FROM snapshots WHERE session_id = ? ORDER BY timestamp DESC", (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "label": r[1], "date": r[2]} for r in rows]

def load_snapshot(snapshot_id: str) -> Optional[Dict[str, Any]]:
    init_db()
    conn = sqlite3.connect(settings.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT specification, final_files FROM snapshots WHERE snapshot_id = ?", (snapshot_id,))
    row = cursor.fetchone()
    conn.close()
    if not row: return None
    return {"specification": row[0], "final_files": json.loads(row[1])}
