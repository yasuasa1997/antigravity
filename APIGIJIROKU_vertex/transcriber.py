import os
import time
import tempfile
from dotenv import load_dotenv
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import storage

# .env ファイルの読み込み
load_dotenv()

def get_sample_rate(audio_file_path):
    """
    pydubを使用して音声ファイルの正確なサンプリングレートを取得します
    """
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(audio_file_path)
        return audio.frame_rate
    except Exception as e:
        print(f"pydubでのサンプルレート取得に失敗しました: {e}")
        return 44100 # デフォルト値

def transcribe_audio(gcs_uri, project_id=None, location=None):
    """
    Speech-to-Text V1 (v1p1beta1) を使用して音声を文字起こしする (Diarization対応・サンプリングレート自動取得)
    """
    client = speech.SpeechClient()
    storage_client = storage.Client()

    # GCSから一時的にファイルをダウンロードしてサンプリングレートを解析
    try:
        parts = gcs_uri.replace("gs://", "").split("/", 1)
        bucket_name = parts[0]
        blob_name = parts[1]
        
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            temp_file_path = temp_file.name
            print(f"Downloading {gcs_uri} to {temp_file_path} for sample rate detection...")
            blob.download_to_filename(temp_file_path)

        sample_rate = get_sample_rate(temp_file_path)
        print(f"Detected exact sample rate: {sample_rate} Hz")
        
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            
    except Exception as e:
        print(f"サンプリングレートの自動検出でエラーが発生しました。デフォルトの44100Hzを使用します: {e}")
        sample_rate = 44100

    # 認識設定
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MP3,
        sample_rate_hertz=sample_rate, # これが話者分離機能を確実に動作させるための最重要パラメータ
        language_code="ja-JP",
        model="latest_long",
        enable_automatic_punctuation=True,
        enable_word_time_offsets=True,
        diarization_config=speech.SpeakerDiarizationConfig(
            enable_speaker_diarization=True,
            min_speaker_count=1, # 指定により1人に設定
            max_speaker_count=10, # 指定により10人に設定
        ),
    )

    audio = speech.RecognitionAudio(uri=gcs_uri)

    print(f"Starting long running recognition (V1) at {sample_rate}Hz for {gcs_uri}...")
    operation = client.long_running_recognize(config=config, audio=audio)
    
    # 完了を待機
    response = operation.result(timeout=3600)
    print("Recognition completed.")

    if not response.results:
        return "文字起こしの結果がありませんでした。"

    # 話者分離結果の構築 (B案：時系列順かつ句読点を維持する堅牢なロジック)
    valid_results = []
    has_meaningful_tags = False
    
    # 1. 各リザルトからプレーンテキストと話者タグを回収
    for result in response.results:
        alt = result.alternatives[0]
        transcript = alt.transcript.strip()
        
        # 集約用リザルト（transcriptが空）の場合はスキップ
        if not transcript:
            continue
            
        speaker = 0
        if hasattr(alt, 'words') and alt.words:
            tags = [w.speaker_tag for w in alt.words if hasattr(w, 'speaker_tag') and w.speaker_tag > 0]
            if tags:
                has_meaningful_tags = True
                speaker = max(set(tags), key=tags.count)
                
        valid_results.append((speaker, transcript))
        
    if has_meaningful_tags and valid_results:
        # 新仕様：各セグメントに正しくタグ情報が付与されている場合
        # 句読点が保持された transcript を使うため最も高品質
        full_transcript = []
        prev_spk = valid_results[0][0]
        curr_text = valid_results[0][1]
        
        for spk, text in valid_results[1:]:
            if spk == prev_spk:
                curr_text += " " + text
            else:
                full_transcript.append(f"話者 {prev_spk}: {curr_text}")
                prev_spk = spk
                curr_text = text
                
        full_transcript.append(f"話者 {prev_spk}: {curr_text}")
        return "\n\n".join(full_transcript)
        
    else:
        # 旧仕様：最後のリザルトにのみ、すべての単語配列が集約されている場合
        # Zenn記事の抽出ロジックに類似するフォールバック（時系列に出力）
        last_result = response.results[-1]
        words_info = last_result.alternatives[0].words if hasattr(last_result.alternatives[0], 'words') else []
        
        if not words_info:
            return "\n\n".join([r.alternatives[0].transcript for r in response.results if hasattr(r, 'alternatives') and r.alternatives and r.alternatives[0].transcript.strip()])
             
        full_transcript = []
        current_speaker = None
        current_text = ""
        
        for w in words_info:
            spk = w.speaker_tag if hasattr(w, 'speaker_tag') else 0
            clean_word = w.word.split('|')[0]
            
            if current_speaker is None:
                current_speaker = spk
                current_text = clean_word
            elif spk != current_speaker:
                full_transcript.append(f"話者 {current_speaker}: {current_text}")
                current_speaker = spk
                current_text = clean_word
            else:
                current_text += clean_word
                
        if current_text:
            full_transcript.append(f"話者 {current_speaker}: {current_text}")
            
        return "\n\n".join(full_transcript)
