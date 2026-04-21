# IIS 環境確認・セットアップ支援スクリプト

Write-Host "--- IIS for Streamlit Setup Check ---" -ForegroundColor Cyan

# 1. IIS 機能の確認 (WebSocketなど)
Write-Host "[1/2] Windows Server 機能を確認中..."
$features = Get-WindowsFeature -Name Web-Server, Web-WebSockets, Web-CGI
foreach ($f in $features) {
    if ($f.Installed) {
        Write-Host "  [OK] $($f.DisplayName) はインストール済みです。" -ForegroundColor Green
    } else {
        Write-Host "  [!!] $($f.DisplayName) が未インストールです。サーバーマネージャーから追加してください。" -ForegroundColor Yellow
    }
}

# 2. HttpPlatformHandler の確認
Write-Host "[2/2] HttpPlatformHandler モジュールを確認中..."
$modulePath = "$env:SystemRoot\System32\inetsrv\httpPlatformHandler.dll"
if (Test-Path $modulePath) {
    Write-Host "  [OK] HttpPlatformHandler はインストール済みです。" -ForegroundColor Green
} else {
    Write-Host "  [!!] HttpPlatformHandler が見つかりません。" -ForegroundColor Red
    Write-Host "  以下のURLよりダウンロードしてインストールしてください (IIS 向け)"
    Write-Host "  https://www.iis.net/downloads/microsoft/httpplatformhandler"
}

Write-Host "`n--- 設定のヒント ---"
Write-Host "1. IIS マネージャーで [新しいWebサイト] を作成してください。"
Write-Host "2. 物理パスにこのディレクトリ ($PWD) を指定してください。"
Write-Host "3. サイトの [バインド] でポート番号 (例: 80) を設定してください。"
Write-Host "4. サイトを選択し、[ハンドラー マッピング] に 'httpPlatformHandler' があることを確認してください。"
Write-Host "---"
