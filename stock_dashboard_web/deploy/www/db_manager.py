import sqlite3
import datetime
import os
from config import DB_NAME

def create_connection():
    """Create a database connection to the SQLite database."""
    conn = None
    try:
        # DB_NAME is usually just "stocks.db"
        # We ensure it's created in the same directory as this file
        db_path = os.path.join(os.path.dirname(__file__), DB_NAME)
        conn = sqlite3.connect(db_path, check_same_thread=False)
    except Exception as e:
        print(f"Connection error: {e}")
    return conn

def create_tables():
    """Create the stock_prices and tickers tables."""
    conn = create_connection()
    if conn is not None:
        try:
            c = conn.cursor()
            # Table for price history
            c.execute("""
                CREATE TABLE IF NOT EXISTS stock_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ticker TEXT NOT NULL,
                    price REAL NOT NULL
                );
            """)
            
            # Table for monitored tickers
            c.execute("""
                CREATE TABLE IF NOT EXISTS tickers (
                    symbol TEXT PRIMARY KEY,
                    name TEXT
                );
            """)
            
            conn.commit()
            print("Tables checked/created.")
        except Exception as e:
            print(f"Table creation error: {e}")
        finally:
            conn.close()

def insert_price(ticker, price):
    """Insert a new stock price record."""
    conn = create_connection()
    if conn is not None:
        try:
            c = conn.cursor()
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO stock_prices (timestamp, ticker, price) VALUES (?, ?, ?)", (timestamp, ticker, price))
            conn.commit()
        except Exception as e:
            print(f"Insert price error: {e}")
        finally:
            conn.close()

def get_latest_prices():
    """Fetch the latest price for each tracked ticker."""
    conn = create_connection()
    results = []
    if conn is not None:
        try:
            c = conn.cursor()
            # Select latest price per ticker
            c.execute("""
                SELECT t.symbol, t.name, p.price, p.timestamp
                FROM tickers t
                LEFT JOIN (
                    SELECT ticker, price, timestamp
                    FROM stock_prices
                    WHERE (ticker, timestamp) IN (
                        SELECT ticker, MAX(timestamp)
                        FROM stock_prices
                        GROUP BY ticker
                    )
                ) p ON t.symbol = p.ticker
            """)
            rows = c.fetchall()
            for row in rows:
                results.append({
                    'symbol': row[0],
                    'name': row[1] or row[0],
                    'price': row[2],
                    'timestamp': row[3]
                })
        except Exception as e:
            print(f"Fetch latest prices error: {e}")
        finally:
            conn.close()
    return results

def get_history(ticker, limit=100):
    """Fetch price history for a specific ticker."""
    conn = create_connection()
    rows = []
    if conn is not None:
        try:
            c = conn.cursor()
            c.execute("SELECT timestamp, price FROM stock_prices WHERE ticker=? ORDER BY timestamp ASC LIMIT ?", (ticker, limit))
            rows = [{'timestamp': r[0], 'price': r[1]} for r in c.fetchall()]
        except Exception as e:
            print(f"Fetch history error: {e}")
        finally:
            conn.close()
    return rows

def get_tickers():
    """Fetch all tracked tickers."""
    conn = create_connection()
    tickers = []
    if conn is not None:
        try:
            c = conn.cursor()
            c.execute("SELECT symbol, name FROM tickers")
            rows = c.fetchall()
            for row in rows:
                tickers.append({'symbol': row[0], 'name': row[1]})
        except Exception as e:
            print(f"Fetch tickers error: {e}")
        finally:
            conn.close()
    return tickers

def add_ticker(symbol, name=None):
    """Add a new ticker."""
    conn = create_connection()
    if conn is not None:
        try:
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO tickers (symbol, name) VALUES (?, ?)", (symbol, name))
            conn.commit()
            return True
        except Exception as e:
            print(f"Add ticker error: {e}")
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
            c.execute("DELETE FROM stock_prices WHERE ticker=?", (symbol,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Remove ticker error: {e}")
            return False
        finally:
            conn.close()
    return False

# Initialize tables on import
create_tables()
