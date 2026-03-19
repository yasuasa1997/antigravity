from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import db_manager
import api_utils
import config
import time
import threading

app = FastAPI(title="Stock Dashboard API")

# CORS setup for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Background worker for price updates
def update_prices_worker():
    while True:
        try:
            tickers = db_manager.get_tickers()
            for t in tickers:
                info = api_utils.get_ticker_info(t['symbol'])
                if info and info['price']:
                    db_manager.insert_price(t['symbol'], info['price'])
            time.sleep(config.INTERVAL_SECONDS)
        except Exception as e:
            print(f"Worker error: {e}")
            time.sleep(10)

# Start worker in a separate thread
@app.on_event("startup")
async def startup_event():
    thread = threading.Thread(target=update_prices_worker, daemon=True)
    thread.start()

@app.get("/api/stocks")
async def get_stocks():
    """Get latest prices for all monitored stocks."""
    return db_manager.get_latest_prices()

@app.get("/api/stocks/{symbol}/history")
async def get_stock_history(symbol: str):
    """Get price history for a specific stock."""
    return db_manager.get_history(symbol)

@app.get("/api/search")
async def search_stocks(q: str):
    """Search for stocks by name or ticker."""
    return api_utils.search_tickers(q)

@app.post("/api/stocks")
async def add_stock(symbol: str):
    """Add a new stock to monitor."""
    info = api_utils.get_ticker_info(symbol)
    if not info:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    if db_manager.add_ticker(symbol, info['name']):
        if info['price']:
            db_manager.insert_price(symbol, info['price'])
        return {"status": "success", "data": info}
    else:
        raise HTTPException(status_code=500, detail="Failed to add stock")

@app.delete("/api/stocks/{symbol}")
async def remove_stock(symbol: str):
    """Remove a stock from monitor."""
    if db_manager.remove_ticker(symbol):
        return {"status": "success"}
    else:
        raise HTTPException(status_code=500, detail="Failed to remove stock")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
