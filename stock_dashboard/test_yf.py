import yfinance as yf

try:
    print("Fetching AAPL with yf.download()...")
    data = yf.download("AAPL", period="1d", progress=False)
    if not data.empty:
        print("Data fetched successfully:")
        print(data)
        price = data['Close'].iloc[-1]
        print(f"Latest Close: {price}")
    else:
        print("Download returned empty DataFrame")
except Exception as e:
    print(f"Error: {e}")
