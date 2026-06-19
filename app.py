import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
import joblib
from datetime import time
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

DB_FILE = "marta_data.db"
WALK_LIMIT_MILES = 1.5
TRANSFER = "Five Points"

st.set_page_config(page_title="MARTA Trip Planner", page_icon="🚇",
                   layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0A1628; color: #E8EDF5; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 720px; }
.hero { text-align: center; padding: 2rem 0 1.5rem 0; border-bottom: 1px solid #1E3A5F; margin-bottom: 1.5rem; }
.hero h1 { font-family: 'Space Grotesk', sans-serif; font-size: 2.2rem; font-weight: 700; color: #FFF; margin: 0 0 0.4rem 0; letter-spacing: -0.02em; }
.hero p { color: #7A9CC0; font-size: 1rem; margin: 0; }
.hero .accent { color: #00B4D8; }
.section-label { font-family: 'Space Grotesk', sans-serif; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: #00B4D8; margin: 1.2rem 0 0.5rem 0; }
.leg-title { font-family: 'Space Grotesk', sans-serif; font-size: 0.95rem; font-weight: 600; color: #FFF; margin: 1.4rem 0 0.6rem 0; }
.trip-card { background: #122040; border-radius: 10px; padding: 1.1rem 1.1rem 1.1rem 0; margin-bottom: 0.9rem; display: flex; border: 1px solid #1E3A5F; overflow: hidden; }
.line-stripe { width: 5px; border-radius: 10px 0 0 10px; margin-right: 1.1rem; flex-shrink: 0; }
.stripe-GOLD { background: #FFB703; } .stripe-RED { background: #EF5350; }
.stripe-BLUE { background: #00B4D8; } .stripe-GREEN { background: #4CAF50; }
.trip-line { font-family: 'Space Grotesk', sans-serif; font-size: 0.72rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: #7A9CC0; margin-bottom: 0.3rem; }
.trip-times { font-family: 'Space Grotesk', sans-serif; font-size: 1.35rem; font-weight: 700; color: #FFF; margin-bottom: 0.2rem; }
.trip-duration { font-size: 0.85rem; color: #7A9CC0; }
.delay-badge { display: inline-block; background: #2A1A00; border: 1px solid #FFB703; color: #FFB703; font-size: 0.72rem; font-weight: 600; padding: 0.12rem 0.5rem; border-radius: 4px; margin-left: 0.5rem; }
.delay-ok { color: #4CAF50; font-size: 0.72rem; font-weight: 600; margin-left: 0.5rem; }
.transfer-note { background: #0D2233; border-left: 3px solid #00B4D8; color: #8FD4E8; font-size: 0.82rem; padding: 0.5rem 1rem; border-radius: 4px; margin: 0.3rem 0 0.9rem 0; }
.notice { border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 0.9rem; font-size: 0.9rem; }
.car-notice { background: #1A1200; border: 1px solid #FFB703; color: #FFB703; }
.walk-notice { background: #0D2233; border: 1px solid #1E3A5F; color: #8FD4E8; font-size: 0.82rem; padding: 0.6rem 1rem; border-radius: 8px; margin-bottom: 0.5rem; }
.stButton button { background: #00B4D8 !important; color: #0A1628 !important; font-family: 'Space Grotesk', sans-serif !important; font-weight: 600 !important; border: none !important; border-radius: 8px !important; padding: 0.55rem 1.2rem !important; width: 100% !important; }
.stButton button:hover { background: #0096B4 !important; }
.stTextInput input { background-color: #0A1628 !important; border: 1px solid #2A4A70 !important; color: #E8EDF5 !important; border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

geolocator = Nominatim(user_agent="marta-trip-planner")

def get_db():
    uri = "file:" + urllib.parse.quote(DB_FILE, safe="/:\\") + "?mode=ro"
    return sqlite3.connect(uri, uri=True, timeout=30)

@st.cache_resource
def load_model():
    try: return joblib.load("delay_model.pkl")
    except Exception: return None

@st.cache_data
def rail_stations():
    conn = get_db()
    df = pd.read_sql_query("""
        SELECT DISTINCT s.stop_name, s.stop_lat, s.stop_lon FROM gtfs_stops s
        WHERE s.stop_name LIKE '%STATION%' AND s.stop_lat IS NOT NULL
          AND s.stop_id IN (SELECT DISTINCT st.stop_id FROM gtfs_stop_times st
              JOIN gtfs_trips t ON st.trip_id=t.trip_id
              JOIN gtfs_routes r ON t.route_id=r.route_id WHERE r.route_type=1)
    """, conn)
    conn.close()
    return df

def geocode(address):
    try:
        loc = geolocator.geocode(address, timeout=10, country_codes="us")
        if loc: return (loc.latitude, loc.longitude)
        loc = geolocator.geocode(f"{address}, Atlanta, GA", timeout=10, country_codes="us")
        if loc: return (loc.latitude, loc.longitude)
    except Exception: return None
    return None

def nearest_station(lat, lon, stations):
    s = stations.copy()
    s["dist"] = s.apply(lambda r: geodesic((lat,lon),(r["stop_lat"],r["stop_lon"])).miles, axis=1)
    c = s.loc[s["dist"].idxmin()]
    return c["stop_name"], round(c["dist"], 2)

def find_trips(from_station, to_station, after_time):
    conn = get_db()
    q = """
    SELECT r.route_long_name AS line, dep.departure_time AS depart, arr.arrival_time AS arrive,
           dep_s.stop_name AS from_stop, arr_s.stop_name AS to_stop,
           ROUND((CAST(SUBSTR(arr.arrival_time,1,2) AS INT)*60+CAST(SUBSTR(arr.arrival_time,4,2) AS INT))
                -(CAST(SUBSTR(dep.departure_time,1,2) AS INT)*60+CAST(SUBSTR(dep.departure_time,4,2) AS INT)),0) AS travel_min
    FROM gtfs_stop_times dep
    JOIN gtfs_stop_times arr ON dep.trip_id=arr.trip_id AND dep.stop_sequence<arr.stop_sequence
    JOIN gtfs_trips t ON dep.trip_id=t.trip_id JOIN gtfs_routes r ON t.route_id=r.route_id
    JOIN gtfs_stops dep_s ON dep.stop_id=dep_s.stop_id JOIN gtfs_stops arr_s ON arr.stop_id=arr_s.stop_id
    WHERE dep_s.stop_name LIKE ? AND arr_s.stop_name LIKE ? AND dep.departure_time >= ?
    ORDER BY dep.departure_time LIMIT 1
    """
    df = pd.read_sql_query(q, conn, params=(f"%{from_station}%", f"%{to_station}%", after_time))
    conn.close()
    return df

def route_leg(from_station, to_station, after_time):
    """Use the proven router logic from router.py."""
    from router import find_trips_with_transfer
    legs, transfer = find_trips_with_transfer(from_station, to_station, after_time)
    return legs, transfer

def line_color(name):
    n = str(name).upper()
    for c in ["GOLD","RED","BLUE","GREEN"]:
        if c in n: return c
    return "BLUE"

def predict_delay(model, line, station, hour, dow):
    if model is None: return None
    try:
        s = pd.DataFrame([{"hour_of_day":hour,"day_of_week":dow,
            f"line_{line}":1,f"station_{station}":1,"direction_N":1}])
        for col in model.feature_names_in_:
            if col not in s.columns: s[col] = 0
        s = s[model.feature_names_in_]
        return round(model.predict(s)[0]/60, 1)
    except Exception: return None

def render_train(row, model, hour, dow):
    lc = line_color(row["line"])
    d = predict_delay(model, lc, str(row["from_stop"]), hour, dow)
    if d is not None and d > 1: badge = f'<span class="delay-badge">~{d} min delay likely</span>'
    elif d is not None: badge = '<span class="delay-ok">✓ On time expected</span>'
    else: badge = ""
    st.markdown(f"""<div class="trip-card"><div class="line-stripe stripe-{lc}"></div>
        <div><div class="trip-line">{row['line']}</div>
        <div class="trip-times">{row['depart'][:5]} → {row['arrive'][:5]} {badge}</div>
        <div class="trip-duration">{int(row['travel_min'])} min · {row['from_stop'].title()} → {row['to_stop'].title()}</div>
        </div></div>""", unsafe_allow_html=True)

# ── UI ──
st.markdown("""<div class="hero"><h1>🚇 MARTA <span class="accent">Trip Planner</span></h1>
<p>Type any address · Real schedules · Predicted delays</p></div>""", unsafe_allow_html=True)

model = load_model()
stations = rail_stations()

if "waypoints" not in st.session_state:
    st.session_state.waypoints = ["", ""]  # start, end

st.markdown('<div class="section-label">Your Trip</div>', unsafe_allow_html=True)
for i in range(len(st.session_state.waypoints)):
    if i == 0: label = "Starting address"
    elif i == len(st.session_state.waypoints)-1: label = "Destination address"
    else: label = f"Stop {i}"
    st.session_state.waypoints[i] = st.text_input(
        label, value=st.session_state.waypoints[i], key=f"wp_{i}",
        placeholder="e.g. Georgia State University")

ca, cb = st.columns(2)
with ca:
    if st.button("＋ Add a stop"):
        st.session_state.waypoints.insert(len(st.session_state.waypoints)-1, "")
        st.rerun()
with cb:
    if len(st.session_state.waypoints) > 2:
        if st.button("✕ Remove last stop"):
            st.session_state.waypoints.pop(len(st.session_state.waypoints)-2)
            st.rerun()

c1, c2 = st.columns(2)
with c1: leave = st.time_input("Leave after", value=time(8,0))
with c2: day = st.selectbox("Day", ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])
dow = {"Sunday":0,"Monday":1,"Tuesday":2,"Wednesday":3,"Thursday":4,"Friday":5,"Saturday":6}[day]
after = leave.strftime("%H:%M:%S")
hour = leave.hour

if st.button("Plan my trip →"):
    wps = [w.strip() for w in st.session_state.waypoints]
    if any(not w for w in wps):
        st.warning("Please fill in every address field.")
    else:
        coords = []
        ok = True
        with st.spinner("Finding your route..."):
            for w in wps:
                c = geocode(w)
                if not c:
                    st.error(f"Couldn't find '{w}'. Try adding a city or zip code.")
                    ok = False; break
                coords.append(c)
        if ok:
            current_time = after
            # For each consecutive pair of waypoints, route a segment
            for seg in range(len(coords)-1):
                from_st, from_dist = nearest_station(*coords[seg], stations)
                to_st, to_dist = nearest_station(*coords[seg+1], stations)
                st.markdown(f'<div class="leg-title">Segment {seg+1}: {wps[seg].title()} → {wps[seg+1].title()}</div>', unsafe_allow_html=True)

                if from_dist > WALK_LIMIT_MILES:
                    st.markdown(f"""<div class="notice car-notice">🚗 <strong>Drive to start</strong><br>
                    {from_dist} miles to nearest rail station (<strong>{from_st.title()}</strong>). Drive or rideshare there.</div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="walk-notice">🚶 Walk {from_dist} mi to <strong>{from_st.title()}</strong></div>', unsafe_allow_html=True)

                trains, transfer = route_leg(from_st, to_st, current_time)
                if not trains:
                    st.markdown(f"""<div class="notice car-notice">No MARTA rail route found for this segment after {current_time[:5]}.</div>""", unsafe_allow_html=True)
                else:
                    for idx, tr in enumerate(trains):
                        if idx == 1 and transfer:
                            st.markdown(f'<div class="transfer-note">🔄 Transfer at {TRANSFER} Station</div>', unsafe_allow_html=True)
                        render_train(tr, model, hour, dow)
                    current_time = trains[-1]["arrive"]  # next segment leaves after this arrives

                if to_dist > WALK_LIMIT_MILES:
                    st.markdown(f"""<div class="notice car-notice">🚗 <strong>Drive from finish</strong><br>
                    {to_dist} miles from <strong>{to_st.title()}</strong> to your destination.</div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="walk-notice">🚶 Walk {to_dist} mi from <strong>{to_st.title()}</strong></div>', unsafe_allow_html=True)

st.markdown("""<div style="text-align:center; color:#3A5A7A; font-size:0.75rem; margin-top:3rem;
padding-top:1rem; border-top:1px solid #1E3A5F;">Unofficial project · Not affiliated with MARTA<br>
Real GTFS schedule data · ML-predicted delays</div>""", unsafe_allow_html=True)