import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx
import os
import tempfile
import threading
import time
from dotenv import load_dotenv

from transcriber import transcribe_audio
from mailer import send_transcription_email

def load_allowed_domains(file_path="allowed_domains.txt"):
    """許可されたドメインのリストをファイルから読み込む"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            # コメント行や空行を除外してリスト化
            domains = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        return domains
    except FileNotFoundError:
        # ファイルがない場合は制限なしとするかエラーにするか運用次第ですが、今回はエラーにします
        st.error("⚠️ allowed_domains.txt が見つかりません。システム管理者にお問い合わせください。")
        return []

# 環境変数の読み込み (.env)
load_dotenv()

st.set_page_config(
    page_title="音声文字起こし＆メール送信",
    page_icon="🎤",
    layout="centered"
)

def process_and_send(file_path: str, to_email: str, status_container):
    """バックグラウンドで実行される文字起こしとメール送信処理"""
    try:
        # 1. 文字起こし実行
        status_container.markdown("➡️ **[1/2] AIによる音声モデル解析と文字起こしを実行中...**\n\n(大容量ファイルの場合、数十分かかることがあります)")
        transcription = transcribe_audio(file_path)
        
        # 2. メール送信
        status_container.markdown("➡️ **[2/2] 文字起こし完了！メールを送信しています...**")
        send_transcription_email(to_email, transcription)
        
        status_container.success("✅ **すべての処理が正常に完了し、メールを送信しました！**")
        
    except Exception as e:
        status_container.error(f"❌ エラーが発生しました:\n\n{e}")
        print(f"Error occurred during processing: {e}")
    finally:
        # 3. 一時ファイルの削除
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted local temporary file: {file_path}")

def main():
    st.title("🎤 音声文字起こし＆メール送信システム")
    st.markdown("""
    音声ファイルをアップロードしてメールアドレスを入力すると、裏側でAI（Google Gemini）が話者を分離しながら文字起こしを行い、完了次第メールでお知らせします。
    """)
    st.divider()

    uploaded_file = st.file_uploader(
        "🎙️ 音声ファイルをアップロードしてください (mp3, wav, m4a等)", 
        type=["mp3", "wav", "m4a", "flac", "ogg", "mp4"]
    )
    
    email_address = st.text_input("📧 結果を受け取るメールアドレスを入力してください")

    if st.button("文字起こしを開始", type="primary"):
        if not uploaded_file:
            st.error("⚠️ 音声ファイルをアップロードしてください。")
            return
            
        if not email_address:
            st.error("⚠️ メールアドレスを入力してください。")
            return

        # ドメインのバリデーション処理
        allowed_domains = load_allowed_domains()
        if not allowed_domains:
            return # ドメインファイルの読み込みに失敗した場合は処理中断
            
        # 入力されたメールアドレスからドメイン部分（@以降）を抽出
        if "@" not in email_address:
            st.error("⚠️ 有効なメールアドレスを入力してください。")
            return
            
        domain_part = email_address.split("@")[-1]
        if domain_part not in allowed_domains:
            st.error(f"⚠️ 指定されたドメイン ({domain_part}) への送信は許可されていません。許可されたドメインを入力してください。")
            return

        st.success("✅ 受付を完了しました！処理が裏側で開始されました。")
        st.info(
            "処理には数十分かかる場合があります。この画面を閉じても処理は続行されます。\n"
        )
        
        # 進行状況を表示するための空コンテナを作成
        status_container = st.empty()

        with st.spinner("受付処理中..."):
            # ファイルを一時フォルダに保存 (バックグラウンドの別スレッドから参照するため)
            ext = os.path.splitext(uploaded_file.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name

            # StreamlitのUIをブロックしないように、別スレッドで処理を開始
            thread = threading.Thread(target=process_and_send, args=(tmp_file_path, email_address, status_container))
            # スレッド内でStreamlitウィジェットを操作するために現在のコンテキストを引き継ぐ
            add_script_run_ctx(thread)
            thread.start()

if __name__ == "__main__":
    main()
