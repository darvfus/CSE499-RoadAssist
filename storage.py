import sqlite3
from datetime import datetime

DB_NAME = "driver_assistant.db"


def init_db():
    """Initialize the SQLite database with extended fields."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            event_type TEXT NOT NULL,
            heart_rate INTEGER,
            oxygen_level INTEGER,
            duration_closed REAL,
            ear_value REAL,
            email_status TEXT,
            alarm_status TEXT
        )
    """)

    # ✅ Optimization: add index for faster queries by timestamp
    c.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_username ON events(username)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_email ON events(email)")

    conn.commit()
    conn.close()


def log_event(username, email, event_type,
              heart_rate=None, oxygen_level=None,
              duration_closed=None, ear_value=None,
              email_status=None, alarm_status=None):
    """
    Insert a new event into the database.
    Includes vital signs, EAR, and statuses.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        INSERT INTO events (
            timestamp, username, email, event_type,
            heart_rate, oxygen_level, duration_closed, ear_value,
            email_status, alarm_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        username,
        email,
        event_type,
        heart_rate,
        oxygen_level,
        duration_closed,
        ear_value,
        email_status,
        alarm_status
    ))

    conn.commit()
    conn.close()
    print(f"[DB] Event logged: {event_type} for {username}")


def fetch_all_events():
    """Retrieve all events (for testing or export)."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM events ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()
    return rows


def fetch_events_by_user(username=None, email=None):
    """Retrieve events filtered by username or email."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    if username:
        c.execute("SELECT * FROM events WHERE username=? ORDER BY timestamp DESC", (username,))
    elif email:
        c.execute("SELECT * FROM events WHERE email=? ORDER BY timestamp DESC", (email,))
    else:
        conn.close()
        return []

    rows = c.fetchall()
    conn.close()
    return rows


def export_to_csv(filename="events_export.csv"):
    """Export all events to CSV for analysis."""
    import csv
    events = fetch_all_events()

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "ID", "Timestamp", "Username", "Email", "Event Type",
            "Heart Rate", "Oxygen Level", "Duration Closed", "EAR Value",
            "Email Status", "Alarm Status"
        ])
        writer.writerows(events)

    print(f"[DB] Events exported to {filename}")
