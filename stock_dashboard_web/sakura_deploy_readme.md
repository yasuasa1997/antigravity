# Sakura Internet Deployment Instructions

`miichans-w.sakuraweb.com` にデプロイするための手順です。

## 1. ファイルのアップロード

`deploy/www` フォルダ内のすべてのファイルを、サーバの公開ディレクトリ（例: `~/www/`）にアップロードしてください。

### 配置後のディレクトリ構成 (例)
```
~/www/
├── index.html         (Frontend)
├── assets/            (Frontend assets)
├── index.cgi          (API Bridge)
├── .htaccess          (Routing)
├── main.py            (FastAPI logic)
├── api_utils.py
├── db_manager.py
├── config.py
└── cron_collector.py  (Background worker)
```

## 2. パーミッションの設定

FTPツールやSSHを使用して、以下のファイルの実行権限を `755` に設定してください。

- `index.cgi`
- `cron_collector.py`

## 3. ライブラリのインストール

SSHでサーバにログインし、必要なライブラリをインストールしてください。
(※さくらの共有サーバでは `pip install --user` を使用するか、仮想環境を作成してください)

```bash
pip install --user fastapi a2wsgi requests urllib3 pandas plotly
```

## 4. Cron の設定

サーバのコンパイルパネル、または `crontab -e` で、定期的に株価を取得するように設定します。
(例: 15分おきに実行)

```cron
*/15 * * * * /usr/local/bin/python3 ~/www/cron_collector.py >> ~/www/collector.log 2>&1
```

これで、ブラウザから `http://miichans-w.sakuraweb.com/` にアクセスすればダッシュボードが利用可能になります。
