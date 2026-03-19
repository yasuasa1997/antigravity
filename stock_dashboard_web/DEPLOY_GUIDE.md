# さくらのレンタルサーバ デプロイ手順書

`miichans-w.sakuraweb.com` に株価ダッシュボードを公開するための全手順です。

## 1. ファイルの準備

以下のフォルダ内のファイルをすべてサーバーの公開ディレクトリ（通常は `~/www/`）にアップロードしてください。

**対象フォルダ**: `c:\Users\0000004032\...\stock_dashboard_web\deploy\www\`

### 配置後の構成
```
~/www/
├── assets/            (CSS/JS群)
├── index.html         (メイン画面)
├── index.cgi          (API実行用プログラム)
├── .htaccess          (ルーティング設定)
├── main.py            (バックエンド本体)
├── api_utils.py       (API連携)
├── db_manager.py      (DB操作)
├── config.py          (設定)
└── cron_collector.py  (株価収集用)
```

## 2. 実行権限の設定

FTPツールまたはSSHで、以下のファイルのパーミッションを **755** に変更してください。

- `index.cgi`
- `cron_collector.py`

## 3. ライブラリのセットアップ

SSHでサーバーにログインし、以下のコマンドで必要なライブラリをインストールします。

```bash
pip install --user fastapi a2wsgi requests urllib3 pandas plotly
```

## 4. 自動更新の設定 (Cron)

さくらのコントロールパネルの「スケジュールジョブ」または `crontab -e` で、株価を自動取得するジョブを追加します。

**設定例 (15分おきに取得する場合)**:
`*/15 * * * * /usr/local/bin/python3 ~/www/cron_collector.py >> ~/www/collector.log 2>&1`

---

以上の設定で、`http://miichans-w.sakuraweb.com/` から世界中のどこからでもダッシュボードを見ることができるようになります。
