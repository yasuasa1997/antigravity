import db_manager
import api_utils
import time

def run_collection():
    print(f"Starting price collection at {time.ctime()}")
    try:
        tickers = db_manager.get_tickers()
        for t in tickers:
            info = api_utils.get_ticker_info(t['symbol'])
            if info and info['price']:
                db_manager.insert_price(t['symbol'], info['price'])
                print(f"Updated {t['symbol']}: {info['price']}")
            else:
                print(f"Skipped {t['symbol']} (no data)")
    except Exception as e:
        print(f"Collection error: {e}")
    print("Collection finished.")

if __name__ == "__main__":
    run_collection()
