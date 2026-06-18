import pandas as pd
import os

gtfs_path = "gtfs"

# Load the key files
routes = pd.read_csv(os.path.join(gtfs_path, "routes.txt"))
stops = pd.read_csv(os.path.join(gtfs_path, "stops.txt"))
stop_times = pd.read_csv(os.path.join(gtfs_path, "stop_times.txt"))
trips = pd.read_csv(os.path.join(gtfs_path, "trips.txt"))
calendar = pd.read_csv(os.path.join(gtfs_path, "calendar.txt"))

print("=== ROUTES ===")
print(f"{len(routes)} routes")
print(routes[["route_id", "route_short_name", "route_long_name"]].head(10))

print("\n=== STOPS ===")
print(f"{len(stops)} stops")
print(stops[["stop_id", "stop_name", "stop_lat", "stop_lon"]].head(10))

print("\n=== TRIPS ===")
print(f"{len(trips)} trips")
print(trips.head(5))

print("\n=== STOP TIMES (first 10) ===")
print(f"{len(stop_times)} stop time records")
print(stop_times.head(10))

print("\n=== SERVICE CALENDAR ===")
print(calendar.head())