import requests
import urllib3
import config

# Suppress InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_ticker_info(ticker_symbol):
    """
    Fetches ticker data (price and name) from Yahoo Finance.
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
                prev_close = meta.get('chartPreviousClose') or meta.get('previousClose')
                
                # Get name from config or API
                name = config.JAPANESE_NAMES.get(ticker_symbol.upper()) or config.JAPANESE_NAMES.get(ticker_symbol) or meta.get('shortName') or meta.get('longName') or ticker_symbol
                
                return {
                    'symbol': ticker_symbol,
                    'price': price,
                    'name': name,
                    'previousClose': prev_close
                }
            except (KeyError, IndexError, TypeError):
                pass
    except Exception as e:
        print(f"API Fetch error for {ticker_symbol}: {e}")
        
    return None

def search_tickers(query, max_results=10):
    """
    Search for tickers using Yahoo Finance search API.
    """
    if not query or not query.strip():
        return []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    url = "https://query2.finance.yahoo.com/v1/finance/search"
    params = {
        "q": query,
        "quotesCount": max_results,
        "newsCount": 0,
        "enableFuzzyQuery": "true"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, verify=False, timeout=10)
        if response.status_code == 200:
            data = response.json()
            quotes = data.get('quotes', [])
            results = []
            for q_res in quotes:
                if q_res.get('quoteType') not in ('EQUITY', 'ETF'):
                    continue
                
                symbol = q_res.get('symbol', '')
                name = (config.JAPANESE_NAMES.get(symbol.upper()) 
                        or config.JAPANESE_NAMES.get(symbol) 
                        or q_res.get('shortname') 
                        or q_res.get('longname') 
                        or symbol)
                
                results.append({
                    'symbol': symbol,
                    'name': name,
                    'exchange': q_res.get('exchDisp', q_res.get('exchange', ''))
                })
            return results
    except Exception as e:
        print(f"Search API error: {e}")
            
    return []
