import vertexai
from vertexai.generative_models import GenerativeModel, Part, HarmCategory, HarmBlockThreshold
from google.cloud import storage
import os
import uuid
import mimetypes

def transcribe_audio(file_path: str) -> str:
    """
    音源ファイルをGCS経由で Google Cloud Vertex AI に渡し、話者分離付きの文字起こしを行う。
    """
    project_id = os.getenv("GCP_PROJECT_ID")
    location = os.getenv("GCP_LOCATION")
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    
    if not project_id or not location or not bucket_name:
        raise ValueError("GCP_PROJECT_ID, GCP_LOCATION, GCS_BUCKET_NAME のいずれかが設定されていません。.envファイルの設定を確認してください。")

    # Vertex AI の初期化
    vertexai.init(project=project_id, location=location)
    
    # Storage クライアントの初期化とファイルアップロード
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)
    
    # 衝突を避けるために一意のファイル名を生成
    blob_name = f"audio_{uuid.uuid4().hex}_{os.path.basename(file_path)}"
    blob = bucket.blob(blob_name)
    
    print(f"Uploading file to GCS bucket '{bucket_name}' as '{blob_name}': {file_path}")
    blob.upload_from_filename(file_path, timeout=600)
    
    gcs_uri = f"gs://{bucket_name}/{blob_name}"
    print(f"File successfully uploaded to GCS. URI: {gcs_uri}")

    try:
        # Vertex AI Gemini モデルによる処理の開始
        print("Starting transcription request with Vertex AI...")
        
        # 音声のMIMEタイプを推定 (Part.from_uri には mime_type が必要です)
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            if file_path.lower().endswith('.m4a'):
                mime_type = "audio/m4a"
            elif file_path.lower().endswith('.mp4'):
                mime_type = "video/mp4"
            else:
                mime_type = "audio/mpeg"

        audio_part = Part.from_uri(uri=gcs_uri, mime_type=mime_type)
        
        prompt = (
            "この音声ファイルの「最初から最後まで」、一切省略せずに完全に文字起こししてください。"
            "要約や途中での打ち切りは絶対にしないでください。"
            "音声には複数の人が話している可能性があります。"
            "発言者ごとに分けて、改行を入れ、"
            "「発言者A: 〇〇」「発言者B: △△」のように誰が話したか明確に区別できるように出力してください。"
        )
        
        model = GenerativeModel("gemini-2.5-flash")
        
        # セーフティフィルターの設定
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        generation_config = {
            "max_output_tokens": 8192,
        }
        
        response = model.generate_content(
            [audio_part, prompt],
            stream=True,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        transcription = ""
        for chunk in response:
            try:
                if chunk.text:
                    transcription += chunk.text
            except ValueError as ve:
                print(f"Skipping chunk due to ValueError: {ve}")
            except Exception as e:
                print(f"Error accessing chunk text: {e}")
                
        if not transcription:
            transcription = "文字起こし結果を取得できませんでした。"
            
    finally:
        # GCSから一時ファイルを削除してクリーンアップ
        try:
            blob.delete()
            print(f"Cleaned up file from GCS: {gcs_uri}")
        except Exception as e:
            print(f"Warning: Failed to delete file {gcs_uri} from GCS: {e}")

    return transcription
