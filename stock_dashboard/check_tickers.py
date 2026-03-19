import sqlite3
import pandas as pd
from config import DB_NAME
import database

try:
    # Ensure table exists (this should trigger creation and seeding)
    database.create_ticker_table()
    
    conn = sqlite3.connect(DB_NAME)
    
    # Check tickers table
    print("--- Tickers Table ---")
    df = pd.read_sql_query("SELECT * FROM tickers", conn)
    print(df)
    
    conn.close()

except Exception as e:
    print(f"Error checking database: {e}")
