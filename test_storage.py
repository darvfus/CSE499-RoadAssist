from storage import init_db, log_event, fetch_all_events, fetch_events_by_user, export_to_csv

def run_tests():
    print("\n[TEST] Initializing DB...")
    init_db()

    print("\n[TEST] Logging dummy events...")
    log_event(
        username="Alex",
        email="alex@example.com",
        event_type="Drowsiness Detected",
        heart_rate=72,
        oxygen_level=98,
        duration_closed=2.1,
        ear_value=0.18,
        email_status="sent",
        alarm_status="triggered"
    )

    log_event(
        username="John",
        email="john@example.com",
        event_type="Normal Driving",
        heart_rate=80,
        oxygen_level=99,
        duration_closed=0.5,
        ear_value=0.30,
        email_status="not_sent",
        alarm_status="off"
    )

    print("\n[TEST] Fetching all events...")
    all_events = fetch_all_events()
    for e in all_events:
        print(e)

    print("\n[TEST] Fetching events by username=Alex...")
    alex_events = fetch_events_by_user(username="Alex")
    for e in alex_events:
        print(e)

    print("\n[TEST] Fetching events by email=john@example.com...")
    john_events = fetch_events_by_user(email="john@example.com")
    for e in john_events:
        print(e)

    print("\n[TEST] Exporting events to CSV...")
    export_to_csv("test_events.csv")
    print("[TEST] Done! Check test_events.csv for exported data.\n")


if __name__ == "__main__":
    run_tests()
    