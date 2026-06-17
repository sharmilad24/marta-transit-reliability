import os
import time
import sqlite3
from datetime import datetime, timezone
from dotenv import load_dotenv
import requests

load_dotenv()
API_KEY = os.getenv("MARTA_API_KEY")

URL = (
    "https://developerservices.itsmarta.com:18096/itsmarta"
    "/railrealtimearrivals/developerservices/traindata"
    f"?apiKey={API_KEY}"
)

DB_FILE = "marta_data.db"
PULL_INTERVAL_SECONDS = 120  # pull every 2 minutes


def setup_database():
    """Create the database table once, if it doesn't already exist."""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS train_arrivals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pulled_at TEXT,
            train_id TEXT,
            line TEXT,
            direction TEXT,
            station TEXT,
            destination TEXT,
            next_arrival TEXT,
            waiting_seconds TEXT,
            waiting_time TEXT,
            event_time TEXT,
            delay TEXT,
            is_realtime TEXT,
            latitude TEXT,
            longitude TEXT
        )
    """)
    conn.commit()
    conn.close()


def fetch_and_store():
    """Pull one snapshot and save every train record with a timestamp."""
    pulled_at = datetime.now(timezone.utc).isoformat()
    response = requests.get(URL, timeout=30)
    trains = response.json()

    conn = sqlite3.connect(DB_FILE)
    for t in trains:
        conn.execute("""
            INSERT INTO train_arrivals (
                pulled_at, train_id, line, direction, station, destination,
                next_arrival, waiting_seconds, waiting_time, event_time,
                delay, is_realtime, latitude, longitude
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pulled_at, t.get("TRAIN_ID"), t.get("LINE"), t.get("DIRECTION"),
            t.get("STATION"), t.get("DESTINATION"), t.get("NEXT_ARR"),
            t.get("WAITING_SECONDS"), t.get("WAITING_TIME"), t.get("EVENT_TIME"),
            t.get("DELAY"), t.get("IS_REALTIME"), t.get("LATITUDE"), t.get("LONGITUDE"),
        ))
    conn.commit()
    conn.close()
    return len(trains)


def main():
    setup_database()
    print("Collector started. Leave this running. Press Ctrl+C to stop.")
    while True:
        try:
            count = fetch_and_store()
            now = datetime.now().strftime("%H:%M:%S")
            print(f"[{now}] Saved {count} records.")
        except Exception as e:
            print(f"Error during pull (will retry): {e}")
        time.sleep(PULL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()