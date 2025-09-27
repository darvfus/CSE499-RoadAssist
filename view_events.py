# view_events.py
import argparse
import sqlite3
from storage import export_to_csv

DB_NAME = "driver_assistant.db"

def view_events(username=None, email=None, event_type=None, start_date=None, end_date=None, export=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
    if cursor.fetchone() is None:
        print("⚠️ No 'events' table found. Did you run init_db() yet?")
        conn.close()
        return

    # Build dynamic query with filters
    query = "SELECT * FROM events WHERE 1=1"
    params = []
    if username:
        query += " AND username=?"
        params.append(username)
    if email:
        query += " AND email=?"
        params.append(email)
    if event_type:
        query += " AND event_type=?"
        params.append(event_type)
    if start_date:
        query += " AND timestamp >= ?"
        params.append(start_date)
    if end_date:
        query += " AND timestamp <= ?"
        params.append(end_date)

    query += " ORDER BY timestamp DESC"
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("✅ No events logged with the given filters.")
        return

    # Print events
    print("📋 Logged Events:")
    print("-" * 100)
    for row in rows:
        print(f"ID: {row[0]}")
        print(f"Timestamp: {row[1]}")
        print(f"User: {row[2]} ({row[3]})")
        print(f"Event: {row[4]}")
        print(f"Heart Rate: {row[5]} BPM")
        print(f"Oxygen Level: {row[6]}%")
        print(f"Duration Closed: {row[7]} sec")
        print(f"EAR Value: {row[8]}")
        print(f"Email Status: {row[9]}")
        print(f"Alarm Status: {row[10]}")
        print("-" * 100)

    # 📊 Summary Report
    total_events = len(rows)
    avg_heart_rate = sum(r[5] for r in rows if r[5] is not None) / total_events
    avg_oxygen = sum(r[6] for r in rows if r[6] is not None) / total_events
    email_success = sum(1 for r in rows if r[9] == "Success")
    email_fail = sum(1 for r in rows if r[9] == "Failed")
    alarm_success = sum(1 for r in rows if r[10] == "Success")
    alarm_fail = sum(1 for r in rows if r[10] == "Failed")

    # 🔎 EAR Threshold Analysis
    EAR_THRESHOLD = 0.15
    critical_drowsy = sum(1 for r in rows if r[8] is not None and r[8] < EAR_THRESHOLD)

    print("\n📊 SUMMARY REPORT")
    print("=" * 100)
    print(f"Total Events: {total_events}")
    print(f"Average Heart Rate: {avg_heart_rate:.1f} BPM")
    print(f"Average Oxygen Level: {avg_oxygen:.1f}%")
    print(f"Email Sent: {email_success} ✅ | Failed: {email_fail} ❌")
    print(f"Alarm Played: {alarm_success} ✅ | Failed: {alarm_fail} ❌")
    print(f"Critical Drowsiness (EAR < {EAR_THRESHOLD}): {critical_drowsy} times ⚠️")
    print("=" * 100)

    # ✅ Optional CSV export
    if export:
        export_to_csv(export)
        print(f"💾 Events exported to {export}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="View logged drowsiness detection events.")
    parser.add_argument("--user", help="Filter by username")
    parser.add_argument("--email", help="Filter by email")
    parser.add_argument("--event", help="Filter by event type")
    parser.add_argument("--from", dest="start_date", help="Filter from date (YYYY-MM-DD)")
    parser.add_argument("--to", dest="end_date", help="Filter to date (YYYY-MM-DD)")
    parser.add_argument("--export", help="Export results to CSV")

    args = parser.parse_args()
    view_events(
        username=args.user,
        email=args.email,
        event_type=args.event,
        start_date=args.start_date,
        end_date=args.end_date,
        export=args.export
    )
