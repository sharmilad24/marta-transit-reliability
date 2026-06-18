import sqlite3
import pandas as pd

conn = sqlite3.connect("marta_data.db")

query = """
SELECT 
    r.route_long_name AS route,
    t.trip_id,
    st.departure_time,
    s.stop_name
FROM gtfs_stop_times st
JOIN gtfs_trips t ON st.trip_id = t.trip_id
JOIN gtfs_routes r ON t.route_id = r.route_id
JOIN gtfs_stops s ON st.stop_id = s.stop_id
WHERE s.stop_name LIKE '%Doraville%'
  AND r.route_long_name LIKE '%Gold%'
  AND st.departure_time >= '17:00:00'
  AND st.departure_time <= '19:00:00'
ORDER BY st.departure_time
LIMIT 20
"""

df = pd.read_sql_query(query, conn)
conn.close()
print(df.to_string())
