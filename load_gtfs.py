import sqlite3
import pandas as pd
import os

gtfs_path = "gtfs"
DB_FILE = "marta_data.db"

conn = sqlite3.connect(DB_FILE)

print("Loading GTFS tables into SQLite...")

# Load each GTFS file as a table
tables = {
    "gtfs_routes": "routes.txt",
    "gtfs_stops": "stops.txt",
    "gtfs_trips": "trips.txt",
    "gtfs_stop_times": "stop_times.txt",
    "gtfs_calendar": "calendar.txt",
}

for table_name, filename in tables.items():
    filepath = os.path.join(gtfs_path, filename)
    df = pd.read_csv(filepath)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    print(f"  Loaded {len(df):,} rows into {table_name}")

# Add indexes so queries run fast
print("\nAdding indexes...")
conn.execute("CREATE INDEX IF NOT EXISTS idx_stop_times_stop ON gtfs_stop_times(stop_id)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_stop_times_trip ON gtfs_stop_times(trip_id)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_trips_route ON gtfs_trips(route_id)")
conn.commit()
conn.close()
print("Done — GTFS data is now queryable in marta_data.db")