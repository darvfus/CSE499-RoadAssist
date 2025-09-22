# storage.py
import sqlite3
from datetime import datetime

DB_NAME = "events.db"

def init_db():
    """Create database and events table if not exists."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            user_email TEXT NOT NULL,
            event_type TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            heart_rate INTEGER,
            oxygenation INTEGER
        )
    """)
    conn.commit()
    conn.close()

def log_event(user_name, user_email, event_type, heart_rate=None, oxygenation=None):
    """Insert a new event log into the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO events (user_name, user_email, event_type, timestamp, heart_rate, oxygenation)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_name, user_email, event_type, datetime.now().isoformat(), heart_rate, oxygenation))
    conn.commit()
    conn.close()

def sync_events_to_cloud():
    """
    Placeholder for syncing events with a cloud database or API.
    Right now, it just prints unsynced events.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()
    conn.close()

    print("Syncing events to cloud (placeholder)...")
    for event in events:
        print(event)
