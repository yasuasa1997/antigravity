import sqlite3
import datetime
from config import DB_NAME

def create_connection():
    """Create a database connection to the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
    except Exception as e:
        print(e)
    return conn

def create_table():
    """Create the stock_prices table if it doesn't exist."""
    conn = create_connection()
    if conn is not None:
        try:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS stock_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ticker TEXT NOT NULL,
                    price REAL NOT NULL
                );
            """)
            conn.commit()
            print("Table 'stock_prices' checked/created.")
            create_ticker_table()
        except Exception as e:
            print(e)
        finally:
            conn.close()
    else:
        print("Error! cannot create the database connection.")

def insert_price(ticker, price):
    """Insert a new stock price record."""
    conn = create_connection()
    if conn is not None:
        try:
            c = conn.cursor()
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO stock_prices (timestamp, ticker, price) VALUES (?, ?, ?)", (timestamp, ticker, price))
            conn.commit()
            # print(f"Inserted {ticker}: {price} at {timestamp}")
        except Exception as e:
            print(e)
        finally:
            conn.close()

def get_data(ticker=None, limit=100):
    """Fetch data from the database."""
    conn = create_connection()
    rows = []
    if conn is not None:
        try:
            c = conn.cursor()
            if ticker:
                c.execute("SELECT timestamp, ticker, price FROM stock_prices WHERE ticker=? ORDER BY timestamp DESC LIMIT ?", (ticker, limit))
            else:
                c.execute("SELECT timestamp, ticker, price FROM stock_prices ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = c.fetchall()
        except Exception as e:
            print(e)
        finally:
            conn.close()
    return rows

def get_all_data_df():
    """Fetch all data as a pandas DataFrame."""
    import pandas as pd
    conn = create_connection()
    df = pd.DataFrame()
    if conn is not None:
        try:
            df = pd.read_sql_query("SELECT timestamp, ticker, price FROM stock_prices ORDER BY timestamp ASC", conn)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        except Exception as e:
            print(e)
        finally:
            conn.close()
    return df

def create_ticker_table():
    """Create the tickers table and seed with default if empty."""
    conn = create_connection()
    if conn is not None:
        try:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS tickers (
                    symbol TEXT PRIMARY KEY
                );
            """)
            
            # Check if empty, if so seed with default
            c.execute("SELECT count(*) FROM tickers")
            if c.fetchone()[0] == 0:
                default_tickers = ["9997.T"]
                for t in default_tickers:
                    c.execute("INSERT OR IGNORE INTO tickers (symbol) VALUES (?)", (t,))
                print(f"Seeded default tickers: {default_tickers}")
            
            conn.commit()
            print("Table 'tickers' checked/created.")
        except Exception as e:
            print(f"Error creating ticker table: {e}")
            
    # Check if 'name' column exists, if not add it (Migration)
    if conn is not None:
        try:
            c = conn.cursor()
            # Pragma table_info returns (cid, name, type, notnull, dflt_value, pk)
            c.execute("PRAGMA table_info(tickers)")
            columns = [info[1] for info in c.fetchall()]
            if 'name' not in columns:
                print("Migrating database: Adding 'name' column to tickers table...")
                c.execute("ALTER TABLE tickers ADD COLUMN name TEXT")
                conn.commit()
                print("Migration complete.")
        except Exception as e:
            print(f"Migration error: {e}")
        finally:
            conn.close()

def get_tickers():
    """Fetch all tracked tickers as a list of dicts {'symbol', 'name'}."""
    conn = create_connection()
    tickers = []
    if conn is not None:
        try:
            c = conn.cursor()
            c.execute("SELECT symbol, name FROM tickers")
            rows = c.fetchall()
            for row in rows:
                tickers.append({
                    'symbol': row[0],
                    'name': row[1] if row[1] else row[0] # Fallback to symbol if name is None
                })
        except Exception as e:
            print(e)
        finally:
            conn.close()
    return tickers

def add_ticker(symbol, name=None):
    """Add a new ticker with optional name."""
    conn = create_connection()
    if conn is not None:
        try:
            c = conn.cursor()
            # If name is provided, update it cleanly
            c.execute("INSERT OR REPLACE INTO tickers (symbol, name) VALUES (?, ?)", (symbol, name))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding ticker: {e}")
            return False
        finally:
            conn.close()
    return False

def remove_ticker(symbol):
    """Remove a ticker."""
    conn = create_connection()
    if conn is not None:
        try:
            c = conn.cursor()
            c.execute("DELETE FROM tickers WHERE symbol=?", (symbol,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error removing ticker: {e}")
            return False
        finally:
            conn.close()
    return False
