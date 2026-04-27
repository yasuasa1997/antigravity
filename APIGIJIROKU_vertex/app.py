import streamlit as st
import os
import time
import uuid
import datetime
import google.auth
import google.auth.transport.requests
import requests
from dotenv import load_dotenv
from google.cloud import storage

from transcriber import transcribe_audio
from mailer import send_transcription_email

# 環境変数の読み込み (.env)
load_dotenv()

def load_allowed_domains(file_path="allowed_domains.txt"):
    """許可されたドメインのリストをファイルから読み込む"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            domains = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        return domains
    except FileNotFoundError:
        st.error("⚠️ allowed_domains.txt が見つかりません。")
        return []

def generate_upload_session_url(blob_name):
    """GCSのレジュマブルアップロードセッションURLを生成する"""
    storage_client = storage.Client()
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    # 動的にオリジン（アクセス元URL）を取得するように変更
    try:
        # Streamlit 1.34+ の st.context.headers を使用
        origin = st.context.headers.get("origin")
        if not origin:
            # Originヘッダーがない場合、Hostヘッダーから組み立てる
            host = st.context.headers.get("host")
            if host:
                if "localhost" in host or "127.0.0.1" in host:
                    origin = f"http://{host}"
                else:
                    origin = f"https://{host}"
    except Exception:
        origin = None
        
    # フォールバック（以前のハードコードされたもの）
    if not origin:
        origin = "https://apigijiroku-run-service-jvlukp7iqq-an.a.run.app"
    
    # 署名付きURL（Signed URL）の代わりに、レジュマブルアップロードセッションを使用します。
    # GCSはここで指定されたoriginからのアクセスのみを許可します。
    session_url = blob.create_resumable_upload_session(
        content_type="application/octet-stream",
        origin=origin
    )
    return session_url

st.set_page_config(
    page_title="音声文字起こし＆メール送信 (Serverless)",
    page_icon="🎤",
    layout="centered"
)

def process_gcs_file(gcs_uri: str, to_email: str, status_container):
    """GCS上のファイルを処理してメール送信する"""
    try:
        start_time = time.time()
        start_time_str = time.strftime('%H:%M', time.localtime(start_time))
        
        status_container.info(f"🕒 **処理開始**: {start_time_str}\n\n➡️ **[1/2] AIによる音声解析を実行中...**\n(Cloud Run環境を維持するため、ストレージ直接連携で処理しています)")
        
        # 1. 文字起こし実行 (GCS URIを直接渡す)
        transcription = transcribe_audio(gcs_uri=gcs_uri)
        
        # 2. メール送信
        status_container.info(f"🕒 **処理開始**: {start_time_str}\n\n➡️ **[2/2] 完了！メールを送信しています...**")
        send_transcription_email(to_email, transcription)
        
        end_time_str = time.strftime('%H:%M', time.localtime(time.time()))
        status_container.success(f"✅ **正常に完了しました！**\n(完了時間: {end_time_str})")
        
    except Exception as e:
        status_container.error(f"❌ エラーが発生しました: {e}")

def get_query_param(key, default=None):
    """バージョン互換性を考慮してクエリパラメータを取得する"""
    try:
        if hasattr(st, "query_params"):
            val = st.query_params.get(key, default)
            return val
    except Exception:
        pass
    
    try:
        params = st.experimental_get_query_params()
        if key in params:
            return params[key][0]
    except Exception:
        pass
    
    return default

def main():
    # クエリパラメータからアップロード済みの情報を取得
    uploaded_gcs_uri = get_query_param("gcs_uri")
    target_email = get_query_param("email")

    # バージョン表示
    st.markdown('<div style="text-align: right; color: gray; font-size: 0.8em;">v3.3.0</div>', unsafe_allow_html=True)
    
    st.title("🎤 音声文字起こし＆メール送信")
    st.divider()

    if uploaded_gcs_uri and target_email:
        # アップロード完了後の処理画面
        st.success(f"✅ アップロード完了: {os.path.basename(uploaded_gcs_uri)}")
        if st.button("もう一度最初から"):
            st.query_params.clear()
            st.rerun()
            
        status_container = st.empty()
        process_gcs_file(uploaded_gcs_uri, target_email, status_container)
        return

    # 入力画面
    email_address = st.text_input("📧 結果を受け取るメールアドレス", value=st.session_state.get("email", ""))
    st.session_state["email"] = email_address

    # ドメインチェック
    allowed_domains = load_allowed_domains()
    is_email_valid = False
    if email_address:
        if "@" in email_address:
            domain_part = email_address.split("@")[-1]
            if domain_part in allowed_domains:
                is_email_valid = True
            else:
                st.warning(f"⚠️ {domain_part} は許可されていないドメインです。")
        else:
            st.warning("⚠️ 有効なメールアドレスを入力してください。")
    
    if is_email_valid:
        if "blob_name" not in st.session_state:
            st.session_state["blob_name"] = f"direct_upload_{uuid.uuid4().hex}.mp3"
        
        blob_name = st.session_state["blob_name"]
        upload_url = generate_upload_session_url(blob_name)
        gcs_uri = f"gs://{os.getenv('GCS_BUCKET_NAME')}/{blob_name}"

        st.info("👇 1. ファイルを選択してアップロード（最大200MB）")
        
        cache_buster = int(time.time())
        upload_html = f"""
        <div style="text-align: center; font-family: sans-serif; border: 2px dashed #ccc; padding: 20px; border-radius: 10px;">
            <input type="file" id="file-uploader" accept="audio/*" style="display: none;">
            <label for="file-uploader" id="label" style="cursor: pointer; background: #007bff; color: white; padding: 10px 20px; border-radius: 5px; font-weight: bold;">
                ファイルを選択してアップロード開始
            </label>
            <div id="progress-container" style="margin-top: 20px; display: none;">
                <div style="width: 100%; background-color: #f3f3f3; border-radius: 10px; height: 20px; box-shadow: inset 0 1px 3px rgba(0,0,0,0.2);">
                    <div id="progress-bar" style="width: 0%; height: 100%; background-color: #28a745; border-radius: 10px; transition: width 0.3s ease-in-out;"></div>
                </div>
                <div id="progress-text" style="margin-top: 10px; font-weight: bold; color: #555;">0%</div>
            </div>
        </div>

        <script>
        console.log("Upload Component loaded (v3.3.0)");
        const fileUploader = document.getElementById('file-uploader');
        const progressContainer = document.getElementById('progress-container');
        const progressBar = document.getElementById('progress-bar');
        const progressText = document.getElementById('progress-text');
        const label = document.getElementById('label');

        fileUploader.addEventListener('change', (event) => {{
            const file = event.target.files[0];
            if (!file) return;
            
            if (file.size > 200 * 1024 * 1024) {{
                alert("200MBを超えるファイルはアップロードできません。");
                return;
            }}

            label.style.display = 'none';
            progressContainer.style.display = 'block';
            progressText.innerText = '📤 アップロード中... (0%)';

            const xhr = new XMLHttpRequest();
            xhr.open('PUT', '{upload_url}', true);
            xhr.setRequestHeader('Content-Type', 'application/octet-stream');

            xhr.upload.onprogress = (e) => {{
                if (e.lengthComputable) {{
                    const percent = Math.round((e.loaded / e.total) * 100);
                    progressBar.style.width = percent + '%';
                    progressText.innerText = '📤 アップロード中... (' + percent + '%)';
                }}
            }};

            xhr.onload = () => {{
                if (xhr.status === 200 || xhr.status === 201) {{
                    progressText.innerHTML = '<p style="color: #28a745; font-size: 1.1em; margin: 10px 0;">✅ アップロード完了！<br><br><b>【重要】</b> 下にある赤色の「文字起こしを開始する」ボタンをクリックしてください。</p>';
                }} else {{
                    progressText.innerText = '❌ アップロード失敗 (Status: ' + xhr.status + ')';
                    label.style.display = 'inline-block';
                }}
            }};

            xhr.onerror = () => {{
                progressText.innerText = '❌ エラーが発生しました';
                label.style.display = 'inline-block';
            }};

            xhr.send(file);
        }});
        </script>
        """
        st.components.v1.html(upload_html, height=180)

        st.write("") 
        st.info("👇 2. アップロード完了後にクリックしてください")
        
        if st.button("🚀 文字起こしを開始する", use_container_width=True, type="primary", key="start_transcription_btn"):
            storage_client = storage.Client()
            bucket = storage_client.bucket(os.getenv("GCS_BUCKET_NAME"))
            if bucket.blob(blob_name).exists():
                status_container = st.empty()
                process_gcs_file(gcs_uri, email_address, status_container)
                if "blob_name" in st.session_state:
                    del st.session_state["blob_name"]
            else:
                st.error("⚠️ まだアップロードが完了していないか、ファイルが見つかりません。アップロード完了メッセージが出るまでお待ちください。")

if __name__ == "__main__":
    main()
