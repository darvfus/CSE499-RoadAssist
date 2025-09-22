# view_events.py
import sqlite3

DB_NAME = "driver_assistant.db"

def view_events():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
    if cursor.fetchone() is None:
        print("⚠️ No 'events' table found. Did you run init_db() yet?")
        conn.close()
        return

    cursor.execute("SELECT * FROM events ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("✅ No events logged yet.")
    else:
        print("📋 Logged Events:")
        print("-" * 80)
        for row in rows:
            print(f"ID: {row[0]}")
            print(f"User: {row[1]} ({row[2]})")
            print(f"Event: {row[3]}")
            print(f"Heart Rate: {row[4]} BPM")
            print(f"Oxygen Level: {row[5]}%")
            print(f"Timestamp: {row[6]}")
            print("-" * 80)

if __name__ == "__main__":
    view_events()
