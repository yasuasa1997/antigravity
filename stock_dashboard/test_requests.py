import requests
import json
import urllib3

# Suppress InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ticker = "AAPL"
url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1d"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

try:
    print(f"Fetching {url}...")
    response = requests.get(url, headers=headers, verify=False)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        # Parse the JSON to get the price
        try:
            meta = data['chart']['result'][0]['meta']
            price = meta['regularMarketPrice']
            print(f"Price: {price}")
        except (KeyError, IndexError) as e:
            print(f"Error parsing JSON: {e}")
            print(json.dumps(data, indent=2))
    else:
        print(f"Error: {response.text}")

except Exception as e:
    print(f"Exception: {e}")
