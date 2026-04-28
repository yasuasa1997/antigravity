import os
import time
import tempfile
import uuid
from pydub import AudioSegment
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.cloud import storage

# .env ファイルの読み込み
load_dotenv()

def transcribe_audio(gcs_uri, project_id=None, location=None):
    """
    音声を30分チャンクに分割し、Gemini 1.5 Proを用いて高精度に話者分離と文字起こしを行う
    """
    storage_client = storage.Client()

    # GCS URIの解析
    parts = gcs_uri.replace("gs://", "").split("/", 1)
    bucket_name = parts[0]
    blob_name = parts[1]
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    print(f"Downloading {gcs_uri} for chunking...")
    
    # 元の音声ファイルを一時ダウンロード
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
        temp_file_path = temp_file.name
        blob.download_to_filename(temp_file_path)

    # pydubで音声を分割 (30分 = 30 * 60 * 1000 ms)
    # チャンクサイズはメモリとGeminiの最適コンテキスト長を考慮
    print("Splitting audio into chunks...")
    try:
        audio = AudioSegment.from_file(temp_file_path)
    except Exception as e:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return f"音声ファイルの読み込みに失敗しました（ffmpegが正しくインストールされていないか、非対応フォーマットです）。エラー: {e}"

    chunk_length_ms = 15 * 60 * 1000
    total_ms = len(audio)
    
    chunks = []
    for i in range(0, total_ms, chunk_length_ms):
        chunks.append(audio[i:i+chunk_length_ms])

    print(f"Total chunks created: {len(chunks)} ({total_ms / 60000:.2f} minutes total)")
    
    # ローカルの元一時ファイルはもう不要なので削除
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)

    # Gemini クライアントの初期化
    # Vertex AIを利用 (Workload Identity または 環境変数から自動認証)
    pid = project_id or os.getenv("GCP_PROJECT_ID")
    # 完全固定でリージョンを指定し、環境変数レベルでも強制する
    loc = "asia-northeast1"
    os.environ["GOOGLE_CLOUD_REGION"] = loc
    os.environ["GOOGLE_CLOUD_LOCATION"] = loc
    
    try:
        if not pid:
            try:
                import google.auth
                _, pid = google.auth.default()
            except Exception:
                pass

        if pid:
            print(f"Initializing Gemini Client with Vertex AI (project={pid}, location={loc})")
            client = genai.Client(vertexai=True, project=pid, location=loc)
        elif os.getenv("GEMINI_API_KEY"):
            print("Initializing Gemini Client with API Key")
            client = genai.Client()
        else:
            print(f"Initializing Gemini Client with default credentials (location={loc})")
            client = genai.Client(vertexai=True, location=loc)
    except Exception as e:
        print(f"GenAI Client Init fallback directly to Client(): {e}")
        client = genai.Client(vertexai=True, location=loc)

    prompt = """
あなたはプロの議事録作成および音声の文字起こしオペレーターです。
提供された音声データから、誰が何を話したかを正確に書き起こしてください。
以下の条件を厳守してください：
1. 会話の時系列順に発言を記述すること。
2. 必ず「話者A: 」「話者B: 」のように発言者を特定し、話者が交代するたびに改行して記載すること。(A, B, Cなどアルファベットで区別)
3. 句読点のない読みにくいテキストではなく、自然で読みやすい句読点を補った日本語で記述すること。
4. 【重要】無音区間や背景音のみで誰も話していない場合は「[無音]」とだけ出力し、絶対にテキストを捏造（ハルシネーション）しないこと。
5. 【重要】「はい。」や「あー」などの同じ相槌を異常な回数繰り返すエラー（ループ）を絶対に起こさないこと。会話の内容が存在しない場合は省略して構いません。
6. Markdownの過剰な装飾（太字など）は避け、シンプルなテキストベースで出力すること。
"""

    full_transcript = []
    
    # チャンクごとに処理
    for idx, chunk in enumerate(chunks):
        print(f"Processing chunk {idx + 1} / {len(chunks)}")
        
        # 1. チャンクをローカルに一時保存
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as chunk_temp_file:
            chunk_local_path = chunk_temp_file.name
            chunk.export(chunk_local_path, format="mp3")
            
        # 2. チャンクをGCSにアップロード (Gemini API はURIを受け取るため)
        chunk_blob_name = f"chunks/{uuid.uuid4()}_chunk_{idx}.mp3"
        chunk_blob = bucket.blob(chunk_blob_name)
        chunk_blob.upload_from_filename(chunk_local_path)
        chunk_gcs_uri = f"gs://{bucket_name}/{chunk_blob_name}"
        
        print(f"Chunk uploaded to: {chunk_gcs_uri}. Sending to Gemini 2.5 Flash...")
        
        # 3. Geminiにリクエスト
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    types.Part.from_uri(file_uri=chunk_gcs_uri, mime_type="audio/mp3"),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    temperature=0.1,
                )
            )
            # パートごとに区切りを入れて結合
            result_text = response.text.strip() if response.text else "[音声が認識されなかったか、テキストが生成されませんでした]"
            full_transcript.append(f"【パート {idx + 1}】（おおよそ {idx*15}分 〜 {(idx+1)*15}分 の区間）\n{result_text}")
            print(f"Chunk {idx + 1} processing complete.")
            
        except Exception as e:
            print(f"Error processing chunk {idx + 1}: {e}")
            full_transcript.append(f"【パート {idx + 1}】\n[文字起こし失敗: Gemini APIでエラーが発生しました - {e}]")
            
        # 4. クリーンアップ (ローカルとGCS)
        if os.path.exists(chunk_local_path):
            os.remove(chunk_local_path)
            
        try:
            chunk_blob.delete()
            print(f"Deleted temporary chunk from GCS: {chunk_blob_name}")
        except Exception as e:
            print(f"Failed to delete {chunk_gcs_uri} from GCS: {e}")
            
    # 全てのチャンクを結合して返す
    final_text = "\n\n---\n\n".join(full_transcript)
    return final_text
