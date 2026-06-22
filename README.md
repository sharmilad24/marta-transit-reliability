# 🚇 MARTA Transit Reliability & Trip Planner

An end-to-end data project that collects live MARTA rail data, predicts delays
with machine learning, and powers two products: an interactive **trip planner
web app** and a **Power BI reliability dashboard** — both built on the same
data pipeline.

> **Unofficial project — not affiliated with or endorsed by MARTA.**

## 🔗 Live Links
- **Trip Planner App:** [https://marta-trip-planner.streamlit.app/]
- **Power BI Dashboard:** [https://app.powerbi.com/links/_HWksyzxs5?ctid=a7499e28-6a7f-48d9-8b14-d3e690989660&pbi_source=linkShare]

## What it does
**Trip Planner** — type any two addresses; it geocodes them, finds the nearest
rail stations, routes your trip (handling transfers at Five Points), predicts
delays on each leg with an ML model, and flags when you'll need a car for the
first or last mile.

**Reliability Dashboard** — visualizes delay patterns across MARTA: a line × hour
heatmap, worst stations, and on-time performance, all from collected real-time data.

## Key Findings
- BLUE line averages ~2 min delay; GOLD is most reliable
- Indian Creek, Kensington, and Avondale are the most delayed stations
- Late evening (hours 20–22) has the worst delays system-wide
- ML model predicts delays within ~78 seconds — 20% better than baseline

## Tech Stack
**Python · SQL · SQLite · Scikit-learn · Streamlit · Power BI · GTFS · Git**

## How it works
Live MARTA Rail API

│  (collector.py — pulls every 2 min)

▼

SQLite database  ──►  clean_arrivals SQL view  ──►  Random Forest delay model

│                                                        │

├──────────────►  Power BI Dashboard                     │

│                                                        ▼

└──────────────►  Streamlit Trip Planner  ◄──────  delay predictions

(GTFS routing + geocoding + transfers)

## Project Structure
| File | Purpose |
|------|---------|
| `collector.py` | Scheduled ingestion from the MARTA Rail API |
| `clean_data.sql` | SQL cleaning view (delay parsing, time features) |
| `train_model.py` | ML model training & evaluation |
| `router.py` | GTFS-based trip routing with transfer handling |
| `geocoder.py` | Address → coordinates → nearest rail station |
| `app.py` | Streamlit trip planner web app |
| `build_app_data.py` | Builds the trimmed database for deployment |

## Running Locally
```bash
pip install -r requirements.txt
streamlit run app.py
```