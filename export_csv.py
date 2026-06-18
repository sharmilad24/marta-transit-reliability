import sqlite3
import pandas as pd

conn = sqlite3.connect("marta_data.db")
df = pd.read_sql_query("SELECT * FROM clean_arrivals", conn)
conn.close()

df.to_csv("clean_arrivals.csv", index=False)
print(f"Exported {len(df):,} rows to clean_arrivals.csv")