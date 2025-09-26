import sqlite3
import json
from datetime import datetime

DATABASE_NAME = "reports.db"

def setup_database():
    """Initializes the database and creates the reports table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            report_data TEXT NOT NULL,
            timestamp DATETIME NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_report(user_id: str, report_data: dict):
    """Saves a new report for a given user_id."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reports (user_id, report_data, timestamp) VALUES (?, ?, ?)",
        (user_id, json.dumps(report_data), datetime.now())
    )
    conn.commit()
    conn.close()

def get_latest_report(user_id: str) -> dict | None:
    """Retrieves the most recent report for a given user_id."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT report_data FROM reports WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return None