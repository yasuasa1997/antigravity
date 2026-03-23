import requests
import urllib3
import time
import config
import pandas as pd
from datetime import datetime

# Suppress InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_ticker_data(ticker_symbol):
    """
    Fetches ticker data (price and name) from Yahoo Finance.
    Returns a dict with 'symbol', 'price', 'name' if successful, else None.
    Name is returned in Japanese if available in config.JAPANESE_NAMES.
    """
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker_symbol}?interval=1d&range=1d"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        if response.status_code == 200:
            data = response.json()
            try:
                meta = data['chart']['result'][0]['meta']
                price = meta.get('regularMarketPrice')
                previous_close = meta.get('chartPreviousClose') or meta.get('previousClose')
                
                # Get name: prefer Japanese name from config (case-insensitive), then API name
                name = config.JAPANESE_NAMES.get(ticker_symbol.upper()) or config.JAPANESE_NAMES.get(ticker_symbol) or meta.get('shortName') or meta.get('longName') or ticker_symbol
                
                return {
                    'symbol': ticker_symbol,
                    'price': price,
                    'name': name,
                    'previousClose': previous_close
                }
            except (KeyError, IndexError, TypeError) as e:
                print(f"Error parsing data for {ticker_symbol}: {e}")
        else:
            print(f"Error fetching {ticker_symbol}: Status {response.status_code}")
    except Exception as e:
        print(f"Exception fetching {ticker_symbol}: {e}")
        
    return None


def search_tickers(query, max_results=10):
    """
    Search for tickers by company name or symbol using Yahoo Finance search API.
    Supports Japanese, English, half-width, and full-width queries.
    Returns a list of dicts with 'symbol', 'name', 'exchange', 'type'.
    """
    if not query or not query.strip():
        return []
    
    # Try multiple variations if Japanese query returns 400
    queries_to_try = [query.strip()]
    
    # Simple mapping for common Japanese search terms if search fails
    # This is a fallback to improve UX for the "三井" example
    common_fallbacks = {
        "三井": "Mitsui",
        "トヨタ": "Toyota",
        "三菱": "Mitsubishi",
        "住友": "Sumitomo",
        "任天堂": "Nintendo",
        "ソニー": "Sony",
        "日立": "Hitachi",
        "東芝": "Toshiba",
        "パナソニック": "Panasonic",
        "ホンダ": "Honda",
        "マツダ": "Mazda",
        "日産": "Nissan",
        "キャノン": "Canon",
    }
    
    is_japanese = any(ord(c) > 0x7F for c in query)
    if is_japanese and query.strip() in common_fallbacks:
        queries_to_try.append(common_fallbacks[query.strip()])
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://finance.yahoo.co.jp/"
    }
    
    all_results = []
    seen_symbols = set()
    
    for q in queries_to_try:
        url = "https://query2.finance.yahoo.com/v1/finance/search"
        params = {
            "q": q,
            "quotesCount": max_results,
            "newsCount": 0,
            "enableFuzzyQuery": "false" if any(ord(c) > 0x7F for c in q) else "true"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, verify=False, timeout=10)
            if response.status_code == 200:
                data = response.json()
                quotes = data.get('quotes', [])
                for q_res in quotes:
                    quote_type = q_res.get('quoteType', '')
                    if quote_type not in ('EQUITY', 'ETF'):
                        continue
                    
                    symbol = q_res.get('symbol', '')
                    if symbol in seen_symbols:
                        continue
                    seen_symbols.add(symbol)
                    
                    name = (config.JAPANESE_NAMES.get(symbol.upper()) 
                            or config.JAPANESE_NAMES.get(symbol) 
                            or q_res.get('shortname') 
                            or q_res.get('longname') 
                            or symbol)
                    exchange = q_res.get('exchDisp', q_res.get('exchange', ''))
                    
                    all_results.append({
                        'symbol': symbol,
                        'name': name,
                        'exchange': exchange,
                        'type': quote_type,
                    })
                
                # If we got results for the first query, no need to try fallbacks
                if all_results:
                    break
            else:
                print(f"Search API error for '{q}': Status {response.status_code}")
        except Exception as e:
            print(f"Search exception for '{q}': {e}")
            
    return all_results


def get_historical_prices(ticker_symbol, interval='1d', period='1mo'):
    """
    Fetches historical price data from Yahoo Finance.
    Interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
    Period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    Returns a pandas DataFrame with 'timestamp' and 'price'.
    """
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker_symbol}?interval={interval}&range={period}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        if response.status_code == 200:
            data = response.json()
            result = data['chart']['result'][0]
            timestamps = result['timestamp']
            prices = result['indicators']['quote'][0]['close']
            
            df = pd.DataFrame({
                'timestamp': [datetime.fromtimestamp(t) for t in timestamps],
                'price': prices,
                'ticker': ticker_symbol
            })
            
            # Drop rows with None/NaN prices
            df = df.dropna(subset=['price'])
            return df
        else:
            print(f"Error fetching historical data for {ticker_symbol}: Status {response.status_code}")
    except Exception as e:
        print(f"Exception fetching historical data for {ticker_symbol}: {e}")
        
    return pd.DataFrame()
