# IIS HttpPlatformHandler から呼び出される Streamlit 起動用スクリプト

$env:PYTHONPATH = ".;" + $env:PYTHONPATH

# IIS から割り当てられたポート番号を取得
$port = $env:HTTP_PLATFORM_PORT
if (-not $port) { $port = "8501" }

# Streamlit を実行
# --server.port: IIS が待機しているポートを指定
# --server.headless: GUI ブラウザを自動起動しない設定
# --server.baseUrlPath: 必要に応じてパスプレフィックスを指定可能
streamlit run app.py `
    --server.port $port `
    --server.headless true `
    --server.enableCORS false `
    --server.enableXsrfProtection false `
    --server.maxUploadSize 200
