# MARTA Transit Reliability Dashboard

An end-to-end data pipeline that collects live MARTA rail data,
models delay patterns with SQL, predicts delays with machine learning,
and visualizes findings in an interactive Power BI dashboard.

> **Unofficial project — not affiliated with or endorsed by MARTA.**

## Live Dashboard
[View the interactive dashboard here](https://app.powerbi.com/reportEmbed?reportId=ca39a18a-96e0-4ff6-843b-8f7e14186be0&autoAuth=true&ctid=a7499e28-6a7f-48d9-8b14-d3e690989660)

## Key Findings
- BLUE line averages ~2 min delay; GOLD is most reliable
- Indian Creek, Kensington, and Avondale are the most delayed stations
- Late evening (hour 20–22) has the worst delays system-wide
- ML model predicts delays within ~78 seconds (20% better than baseline)

## Stack
Python · SQLite · SQL · Scikit-learn · Power BI · Git

## Pipeline
Live MARTA API → collector.py (every 2 min) → SQLite →
clean_arrivals SQL view → Random Forest model → Power BI dashboard

## Project Structure
- `collector.py` — scheduled data ingestion from MARTA Rail API
- `clean_data.sql` — SQL cleaning view (delay parsing, time extraction)
- `train_model.py` — ML model training and evaluation
- `export_csv.py` — exports clean data for Power BI
