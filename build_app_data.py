import sqlite3
import os

SOURCE = "marta_data.db"
TARGET = "app_data.db"

src = sqlite3.connect(f"file:{SOURCE}?mode=ro", uri=True, timeout=30)
dst = sqlite3.connect(TARGET)

print("Building trimmed app database...")

# Most tables stay full; trips and stop_times get filtered to RAIL only
table_queries = {
    "gtfs_routes": "SELECT * FROM gtfs_routes",
    "gtfs_stops": "SELECT * FROM gtfs_stops",
    "gtfs_calendar": "SELECT * FROM gtfs_calendar",
    "gtfs_trips": """
        SELECT * FROM gtfs_trips
        WHERE route_id IN (SELECT route_id FROM gtfs_routes WHERE route_type = 1)
    """,
    "gtfs_stop_times": """
        SELECT * FROM gtfs_stop_times
        WHERE trip_id IN (
            SELECT trip_id FROM gtfs_trips
            WHERE route_id IN (SELECT route_id FROM gtfs_routes WHERE route_type = 1)
        )
    """,
}

for table, query in table_queries.items():
    rows = src.execute(query).fetchall()
    cols = [d[0] for d in src.execute(f"SELECT * FROM {table} LIMIT 1").description]
    col_defs = ", ".join(f'"{c}"' for c in cols)
    placeholders = ", ".join("?" for _ in cols)

    dst.execute(f"DROP TABLE IF EXISTS {table}")
    dst.execute(f"CREATE TABLE {table} ({col_defs})")
    dst.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
    print(f"  Copied {len(rows):,} rows into {table}")

# Copy a sample of delay data (most recent 50k rows) so the clean view still works
print("  Copying delay data sample...")
delay_rows = src.execute(
    "SELECT * FROM train_arrivals ORDER BY id DESC LIMIT 50000"
).fetchall()
delay_cols = [d[0] for d in src.execute(
    "SELECT * FROM train_arrivals LIMIT 1").description]
col_defs = ", ".join(f'"{c}"' for c in delay_cols)
placeholders = ", ".join("?" for _ in delay_cols)
dst.execute("DROP TABLE IF EXISTS train_arrivals")
dst.execute(f"CREATE TABLE train_arrivals ({col_defs})")
dst.executemany(f"INSERT INTO train_arrivals VALUES ({placeholders})", delay_rows)
print(f"  Copied {len(delay_rows):,} delay records")

# Recreate the clean_arrivals view in the new database
dst.execute("""
CREATE VIEW IF NOT EXISTS clean_arrivals AS
SELECT line, station, direction, destination, train_id, delay_seconds,
    ROUND(delay_seconds / 60.0, 1) AS delay_minutes,
    CAST(strftime('%H', local_time) AS INTEGER) AS hour_of_day,
    CAST(strftime('%w', local_time) AS INTEGER) AS day_of_week,
    local_time, pulled_at
FROM (
    SELECT line, station, direction, destination, train_id, pulled_at,
        CAST(REPLACE(REPLACE(delay, 'T', ''), 'S', '') AS INTEGER) AS delay_seconds,
        datetime(replace(substr(pulled_at, 1, 19), 'T', ' '), '-4 hours') AS local_time
    FROM train_arrivals
    WHERE delay IS NOT NULL
)
""")

# Indexes for speed
dst.execute("CREATE INDEX IF NOT EXISTS idx_st_stop ON gtfs_stop_times(stop_id)")
dst.execute("CREATE INDEX IF NOT EXISTS idx_st_trip ON gtfs_stop_times(trip_id)")

dst.commit()
src.close()
dst.close()

size_mb = os.path.getsize(TARGET) / (1024 * 1024)
print(f"\nDone — app_data.db created ({size_mb:.1f} MB)")