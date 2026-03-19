"""Fix: Update all ticker names in DB to Japanese using config.JAPANESE_NAMES (case-insensitive)"""
import database
import config
import stock_api

# Show current state
tickers = database.get_tickers()
print("=== Before ===")
for t in tickers:
    print(f"  {t['symbol']}: {t['name']}")

# Update each ticker with Japanese name
print("\n=== Updating ===")
for t in tickers:
    symbol = t['symbol']
    old_name = t['name']
    
    # Case-insensitive lookup in JAPANESE_NAMES
    new_name = config.JAPANESE_NAMES.get(symbol.upper()) or config.JAPANESE_NAMES.get(symbol)
    
    if new_name and new_name != old_name:
        database.add_ticker(symbol, new_name)
        print(f"  {symbol}: {old_name} -> {new_name}")
    elif not new_name:
        # Not in config, try API (will use JAPANESE_NAMES internally via stock_api)
        data = stock_api.get_ticker_data(symbol)
        if data and data['name'] != old_name:
            database.add_ticker(symbol, data['name'])
            print(f"  {symbol}: {old_name} -> {data['name']}")
        else:
            print(f"  {symbol}: (not in mapping, keeping) {old_name}")
    else:
        print(f"  {symbol}: (already Japanese) {old_name}")

# Show result
tickers = database.get_tickers()
print("\n=== After ===")
for t in tickers:
    print(f"  {t['symbol']}: {t['name']}")
