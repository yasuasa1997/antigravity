import sqlite3
import pandas as pd
from config import DB_NAME

try:
    conn = sqlite3.connect(DB_NAME)
    
    # Check table existence
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stock_prices';")
    table_exists = cursor.fetchone()
    
    if table_exists:
        print("Table 'stock_prices' exists.")
        
        # Check row count
        cursor.execute("SELECT count(*) FROM stock_prices;")
        count = cursor.fetchone()[0]
        print(f"Total rows: {count}")
        
        # Show recent data
        if count > 0:
            df = pd.read_sql_query("SELECT * FROM stock_prices ORDER BY timestamp DESC LIMIT 5", conn)
            print("\nRecent Data:")
            print(df)
        else:
            print("Table is empty.")
    else:
        print("Table 'stock_prices' does NOT exist.")

    conn.close()

except Exception as e:
    print(f"Error checking database: {e}")
