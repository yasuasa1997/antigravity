FROM python:3.11-slim

# 作業ディレクトリの設定
WORKDIR /app

# 依存パッケージのインストール
# 先に requirements.txt をコピーしてキャッシュを活かします
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのすべてのファイルをコピー
COPY . .

ENV PORT=8080
EXPOSE $PORT

# ログなどの時間を日本時間に合わせる
ENV TZ="Asia/Tokyo"

# Streamlitの起動コマンド
# Cloud Runでは外部からアクセスできるよう --server.address=0.0.0.0 を指定します
CMD sh -c "streamlit run app.py --server.port=${PORT} --server.address=0.0.0.0"
