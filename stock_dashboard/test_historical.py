import stock_api
import pandas as pd

def test_intervals():
    ticker = "7203.T" # Toyota
    intervals = [
        ("5分", "5m", "1d"),
        ("1時間", "1h", "5d"),
        ("1日", "1d", "1mo"),
        ("1週間", "1wk", "6mo")
    ]
    
    for label, interval, period in intervals:
        print(f"Testing {label} (interval={interval}, period={period})...")
        df = stock_api.get_historical_prices(ticker, interval, period)
        if not df.empty:
            print(f"Success: {len(df)} rows fetched. First timestamp: {df['timestamp'].iloc[0]}")
        else:
            print(f"Failed to fetch data for {label}")

if __name__ == "__main__":
    test_intervals()
