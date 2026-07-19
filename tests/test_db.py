import pytest
import os
import sqlite3
from multicliswarm.db import init_db, save_session, get_session, DB_PATH

@pytest.fixture(autouse=True)
def setup_db():
    # Use an in-memory DB or temporary file for tests if needed.
    # For now, just clear the table to ensure isolation.
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions")
    conn.commit()
    conn.close()
    yield
    # Cleanup after test
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions")
    conn.commit()
    conn.close()

def test_save_and_get_session():
    session_id = "test-session-123"
    task = "Test Task"
    language = "python"
    specification = "# Spec"
    
    from multicliswarm.schemas import FileMap
    files_map = [FileMap(filepath="main.py", description="Test", is_test=False)]
    final_files = {"main.py": "print('hello')"}
    cost = 0.05
    
    save_session(session_id, task, language, specification, files_map, final_files, cost)
    
    session = get_session(session_id)
    assert session is not None
    assert session["session_id"] == session_id
    assert session["task"] == task
    assert session["language"] == language
    assert session["specification"] == specification
    assert session["final_files"]["main.py"] == "print('hello')"
    assert session["cost_usd"] == cost

def test_get_nonexistent_session():
    session = get_session("does-not-exist")
    assert session is None
