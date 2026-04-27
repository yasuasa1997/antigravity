import os
import time
from dotenv import load_dotenv
from google.cloud import speech_v1p1beta1 as speech

# .env ファイルの読み込み
load_dotenv()

def transcribe_audio(gcs_uri, project_id=None, location=None):
    """
    Speech-to-Text V1 (v1p1beta1) を使用して音声を文字起こしする (Diarization対応)
    """
    client = speech.SpeechClient()

    # 高精度な最新長尺モデル (latest_long) を採用
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MP3,
        language_code="ja-JP",
        model="latest_long",
        enable_automatic_punctuation=True,
        enable_word_time_offsets=True,
        diarization_config=speech.SpeakerDiarizationConfig(
            enable_speaker_diarization=True,
            min_speaker_count=2, # 話者が分かれやすくするため
            max_speaker_count=10,
        ),
    )

    audio = speech.RecognitionAudio(uri=gcs_uri)

    print(f"Starting long running recognition (V1) for {gcs_uri}...")
    operation = client.long_running_recognize(config=config, audio=audio)
    
    # 完了を待機
    response = operation.result(timeout=3600)
    print("Recognition completed.")

    if not response.results:
        return "文字起こしの結果がありませんでした。"

    # 話者分離結果の構築 (複数仕様に堅牢に対応するロジック)
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
        # 句読点（スマートパンクチュエーション）が保持された transcript を使うため最も高品質
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
        last_result = response.results[-1]
        words_info = last_result.alternatives[0].words if hasattr(last_result.alternatives[0], 'words') else []
        
        if not words_info:
            # タグが完全に取得できなかった場合、結合したプレーンテキストをフォールバックとして返す
            return "\n\n".join([r.alternatives[0].transcript for r in response.results if hasattr(r, 'alternatives') and r.alternatives and r.alternatives[0].transcript.strip()])
             
        full_transcript = []
        current_speaker = None
        current_text = ""
        
        for w in words_info:
            spk = w.speaker_tag if hasattr(w, 'speaker_tag') else 0
            # 「また|マタ」などの読みが付属する場合があるので | でスプリットする
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
