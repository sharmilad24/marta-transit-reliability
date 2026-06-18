import sqlite3
import pandas as pd
from datetime import datetime

DB_FILE = "marta_data.db"

def find_trips(from_station: str, to_station: str, after_time: str) -> pd.DataFrame:
    """
    Find direct trips from one station to another after a given time.
    Returns a DataFrame of options sorted by departure time.
    """
    conn = sqlite3.connect(DB_FILE)

    query = """
    SELECT
        r.route_long_name AS line,
        dep.trip_id,
        dep.departure_time AS depart_from_origin,
        arr.arrival_time AS arrive_at_destination,
        dep_stop.stop_name AS from_stop,
        arr_stop.stop_name AS to_stop,
        -- How long the trip takes in minutes
        ROUND(
            (CAST(SUBSTR(arr.arrival_time, 1, 2) AS INTEGER) * 60 +
             CAST(SUBSTR(arr.arrival_time, 4, 2) AS INTEGER)) -
            (CAST(SUBSTR(dep.departure_time, 1, 2) AS INTEGER) * 60 +
             CAST(SUBSTR(dep.departure_time, 4, 2) AS INTEGER)),
            0
        ) AS travel_minutes
    FROM gtfs_stop_times dep
    JOIN gtfs_stop_times arr
        ON dep.trip_id = arr.trip_id
        AND dep.stop_sequence < arr.stop_sequence
    JOIN gtfs_trips t ON dep.trip_id = t.trip_id
    JOIN gtfs_routes r ON t.route_id = r.route_id
    JOIN gtfs_stops dep_stop ON dep.stop_id = dep_stop.stop_id
    JOIN gtfs_stops arr_stop ON arr.stop_id = arr_stop.stop_id
    WHERE dep_stop.stop_name LIKE ?
      AND arr_stop.stop_name LIKE ?
      AND dep.departure_time >= ?
    ORDER BY dep.departure_time
    LIMIT 5
    """

    params = (f"%{from_station}%", f"%{to_station}%", after_time)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def plan_trip(from_station: str, to_station: str, leave_after: str):
    """Plan a trip and print the next few options."""
    print(f"\nFinding trips from {from_station} → {to_station} after {leave_after}\n")
    results = find_trips(from_station, to_station, leave_after)

    if results.empty:
        print("No direct trips found. You may need a transfer, or MARTA")
        print("may not serve this route directly.")
        return

    for _, row in results.iterrows():
        print(f"  Line:      {row['line']}")
        print(f"  Depart:    {row['depart_from_origin']}")
        print(f"  Arrive:    {row['arrive_at_destination']}")
        print(f"  Duration:  {int(row['travel_minutes'])} minutes")
        print()


if __name__ == "__main__":
    # Test it with a real trip
    plan_trip("Doraville", "Airport", "17:00:00")
    plan_trip("Five Points", "Lindbergh", "08:00:00")