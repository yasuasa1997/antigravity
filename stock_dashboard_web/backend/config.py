# config.py
DB_NAME = "stocks.db"
INTERVAL_SECONDS = 15

# Default tickers to monitor
TICKERS = ["AAPL", "MSFT", "7203.T", "9997.T"]

# Mapping for Japanese company names (optional fallback)
JAPANESE_NAMES = {
    "AAPL": "アップル",
    "MSFT": "マイクロソフト",
    "GOOGL": "アルファベット",
    "TSLA": "テスラ",
    "NVDA": "エヌビディア",
    "7203.T": "トヨタ自動車",
    "9984.T": "ソフトバンクグループ",
    "6758.T": "ソニーグループ",
    "9997.T": "ベルーナ",
    "8031.T": "三井物産",
    "8001.T": "伊藤忠商事",
}
