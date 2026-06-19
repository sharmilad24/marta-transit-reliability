import sqlite3
import pandas as pd
import urllib.parse
from functools import lru_cache
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

DB_FILE = "marta_data.db"

geolocator = Nominatim(user_agent="marta-trip-planner")


def get_db():
    """Open database in read-only mode so it never conflicts with the collector."""
    db_uri = "file:" + urllib.parse.quote(DB_FILE, safe="/:\\") + "?mode=ro"
    return sqlite3.connect(db_uri, uri=True, timeout=30)


@lru_cache(maxsize=256)
def address_to_coords(address: str):
    """
    Convert an address to (lat, lon). Returns None if not found.
    Cached so the same address is only looked up online once.
    """
    try:
        # Try the address exactly as typed first — respects real city names
        location = geolocator.geocode(address, timeout=10, country_codes="us")
        if location:
            return (location.latitude, location.longitude)

        # Only if that fails, assume it's a local Atlanta address and retry
        location = geolocator.geocode(f"{address}, Atlanta, GA",
                                      timeout=10, country_codes="us")
        if location:
            return (location.latitude, location.longitude)

        return None
    except Exception:
        return None


def nearest_station(lat: float, lon: float):
    """
    Find the nearest MARTA rail station to a GPS coordinate.
    Returns a dict with station name, coords, and distance in miles.
    """
    conn = get_db()
    stations = pd.read_sql_query("""
        SELECT DISTINCT s.stop_name, s.stop_lat, s.stop_lon
        FROM gtfs_stops s
        WHERE s.stop_name LIKE '%STATION%'
          AND s.stop_lat IS NOT NULL
          AND s.stop_lon IS NOT NULL
          AND s.stop_id IN (
              SELECT DISTINCT st.stop_id
              FROM gtfs_stop_times st
              JOIN gtfs_trips t ON st.trip_id = t.trip_id
              JOIN gtfs_routes r ON t.route_id = r.route_id
              WHERE r.route_type = 1
          )
    """, conn)
    conn.close()

    user_point = (lat, lon)
    stations["distance_miles"] = stations.apply(
        lambda row: geodesic(user_point, (row["stop_lat"], row["stop_lon"])).miles,
        axis=1
    )
    closest = stations.loc[stations["distance_miles"].idxmin()]
    return {
        "name": closest["stop_name"],
        "lat": closest["stop_lat"],
        "lon": closest["stop_lon"],
        "distance_miles": round(closest["distance_miles"], 2),
    }


def address_to_nearest_station(address: str):
    """
    Full pipeline: address string → nearest MARTA rail station.
    Returns (station_info_dict, error_string).
    """
    coords = address_to_coords(address)
    if coords is None:
        return None, f"Couldn't find '{address}' — try adding a city or zip code."

    station = nearest_station(coords[0], coords[1])
    return station, None


if __name__ == "__main__":
    test_addresses = [
        "Hartsfield-Jackson Atlanta Airport",
        "Stone Mountain Park, GA",
        "Athens, GA",
    ]
    for addr in test_addresses:
        print(f"Looking up: {addr}")
        coords = address_to_coords(addr)
        print(f"  Coordinates: {coords}")
        station, err = address_to_nearest_station(addr)
        if err:
            print(f"  {err}")
        else:
            print(f"  Nearest: {station['name']} ({station['distance_miles']} mi)")
        print()