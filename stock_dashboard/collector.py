import time
import requests
import urllib3
import config
import database
import stock_api
from datetime import datetime

# Suppress InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def main():
    print("Starting stock data collector (Direct API Mode Data Driven)...")
    print(f"Interval: {config.INTERVAL_SECONDS} seconds")

    # Initialize database
    database.create_table()
    database.create_ticker_table() # Ensure migration runs

    while True:
        try:
            start_time = time.time()
            print(f"\n--- Fetching data at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
            
            # Get current tickers from DB
            # Returns list of dicts: [{'symbol': 'AAPL', 'name': 'Apple Inc.'}, ...]
            tickers = database.get_tickers()
            if not tickers:
                print("No tickers found in database.")
            
            for ticker_info in tickers:
                symbol = ticker_info['symbol']
                # Use stock_api to get data
                data = stock_api.get_ticker_data(symbol)
                
                if data and data['price']:
                    database.insert_price(symbol, data['price'])
                    print(f"{symbol} ({data['name']}): {data['price']:.2f}")
                    
                    # Update name in DB if missing or changed (optional, but good for keeping sync)
                    if data['name'] != ticker_info['name']:
                         database.add_ticker(symbol, data['name'])
                else:
                    print(f"Failed to fetch {symbol}")

            # Calculate sleep time to maintain interval
            elapsed = time.time() - start_time
            sleep_time = max(0, config.INTERVAL_SECONDS - elapsed)
            print(f"Sleeping for {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\nCollector stopped by user.")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(config.INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
