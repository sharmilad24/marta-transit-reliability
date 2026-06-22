import sqlite3
import pandas as pd
import urllib.parse

import os
DB_FILE = "app_data.db" if os.path.exists("app_data.db") else "marta_data.db"


def get_db():
    """Open database in read-only mode so it never conflicts with the collector."""
    db_uri = "file:" + urllib.parse.quote(DB_FILE, safe="/:\\") + "?mode=ro"
    return sqlite3.connect(db_uri, uri=True, timeout=30)


def find_trips(from_station: str, to_station: str, after_time: str) -> pd.DataFrame:
    """
    Find direct trips from one station to another after a given time.
    Returns a DataFrame of options sorted by departure time.
    """
    conn = get_db()
    query = """
    SELECT
        r.route_long_name AS line,
        dep.trip_id,
        dep.departure_time AS depart,
        arr.arrival_time  AS arrive,
        dep_s.stop_name   AS from_stop,
        arr_s.stop_name   AS to_stop,
        ROUND(
            (CAST(SUBSTR(arr.arrival_time,1,2) AS INTEGER)*60 +
             CAST(SUBSTR(arr.arrival_time,4,2) AS INTEGER)) -
            (CAST(SUBSTR(dep.departure_time,1,2) AS INTEGER)*60 +
             CAST(SUBSTR(dep.departure_time,4,2) AS INTEGER))
        , 0) AS travel_min
    FROM gtfs_stop_times dep
    JOIN gtfs_stop_times arr ON dep.trip_id = arr.trip_id
        AND dep.stop_sequence < arr.stop_sequence
    JOIN gtfs_trips  t   ON dep.trip_id  = t.trip_id
    JOIN gtfs_routes r   ON t.route_id   = r.route_id
    JOIN gtfs_stops dep_s ON dep.stop_id = dep_s.stop_id
    JOIN gtfs_stops arr_s ON arr.stop_id = arr_s.stop_id
    WHERE dep_s.stop_name LIKE ?
      AND arr_s.stop_name LIKE ?
      AND dep.departure_time >= ?
    ORDER BY dep.departure_time
    LIMIT 4
    """
    df = pd.read_sql_query(
        query, conn,
        params=(f"%{from_station}%", f"%{to_station}%", after_time)
    )
    conn.close()
    return df


def plan_trip(from_station: str, to_station: str, leave_after: str):
    """Plan a trip and print the next few options."""
    print(f"\nFinding trips from {from_station} → {to_station} after {leave_after}\n")
    results = find_trips(from_station, to_station, leave_after)

    if results.empty:
        print("No direct trips found. You may need a transfer or rideshare.")
        return

    for _, row in results.iterrows():
        print(f"  Line:     {row['line']}")
        print(f"  Depart:   {row['depart']}")
        print(f"  Arrive:   {row['arrive']}")
        print(f"  Duration: {int(row['travel_min'])} minutes")
        print()

def find_trips_with_transfer(from_station, to_station, after_time, transfer="Five Points"):
    """
    Find a trip that may require one transfer at Five Points.
    Returns (legs_list, transfer_needed_bool).
    Each leg is a dict with line, depart, arrive, from_stop, to_stop, travel_min.
    """
    # First try a direct trip
    direct = find_trips(from_station, to_station, after_time)
    if not direct.empty:
        return [direct.iloc[0].to_dict()], False

    # No direct trip — route through Five Points
    leg1 = find_trips(from_station, transfer, after_time)
    if leg1.empty:
        return [], False  # can't even reach the transfer point

    first = leg1.iloc[0].to_dict()
    # Catch the next train from Five Points AFTER arriving there (+2 min buffer)
    arrive_time = first["arrive"]
    leg2 = find_trips(transfer, to_station, arrive_time)
    if leg2.empty:
        return [first], False  # got to Five Points but can't continue

    second = leg2.iloc[0].to_dict()
    return [first, second], True

if __name__ == "__main__":
    plan_trip("Doraville", "Airport", "17:00:00")
    plan_trip("Five Points", "Lindbergh", "08:00:00")