# 監視対象の銘柄リスト (Yahoo Financeのティッカーシンボル)
# 米国株: AAPL (Apple), MSFT (Microsoft), GOOGL (Google), AMZN (Amazon), TSLA (Tesla)
# 日本株: 7203.T (Toyota), 9984.T (SoftBank Group), 6758.T (Sony)
TICKERS = [
    "AAPL",
    "MSFT",
    "7203.T",
    "9997.T"
]

# データ取得間隔 (秒)
INTERVAL_SECONDS = 20

# データベースファイル名
DB_NAME = "stocks.db"

# 日本語企業名マッピング
# Yahoo Finance APIは英語名を返すため、ここで日本語名に変換します
# 新しい銘柄を追加する場合は、ここにもマッピングを追加してください
JAPANESE_NAMES = {
    "9997.T": "ベルーナ",
    "7012.T": "川崎重",
    "6941.T": "山一電機",
    "6471.T": "日本精工",
    "6269.T": "三井海洋",
    "6315.T": "ＴＯＷＡ",
    "5821.T": "平河ヒューテ",
    "6966.T": "三井ハイテク",
    "5802.T": "住友電工",
}
