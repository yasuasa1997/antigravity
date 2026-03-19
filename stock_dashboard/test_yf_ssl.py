import yfinance as yf
import requests

session = requests.Session()
session.verify = False

try:
    print("Fetching AAPL with SSL verify=False...")
    # Attempt to pass session to Ticker (supported in newer yfinance)
    ticker = yf.Ticker("AAPL", session=session)
    
    # Try getting history
    hist = ticker.history(period="1d")
    
    if not hist.empty:
        print("Data fetched successfully:")
        print(hist.tail())
        price = hist['Close'].iloc[-1]
        print(f"Latest Close: {price}")
    else:
        print("History empty")

except Exception as e:
    print(f"Error: {e}")
