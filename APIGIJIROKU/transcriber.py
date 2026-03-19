import google.generativeai as genai
import os
import time

def transcribe_audio(file_path: str) -> str:
    """
    音源ファイルをGoogle Gemini APIにアップロードし、話者分離付きの文字起こしを行う。
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEYが設定されていません。.envファイルの設定を確認してください。")
        
    genai.configure(api_key=api_key)

    print(f"Uploading file to Gemini: {file_path}")
    uploaded_file = genai.upload_file(path=file_path)
    
    # アップロード後の処理待ち
    while uploaded_file.state.name == "PROCESSING":
        print(".", end="", flush=True)
        time.sleep(2)
        uploaded_file = genai.get_file(uploaded_file.name)
        
    if uploaded_file.state.name == "FAILED":
        raise RuntimeError("Google Geminiへのファイルアップロード・処理が失敗しました。")

    print("\nFile successfully processed by Gemini. Starting transcription request...")
    
    # 複数人の声が含まれる場合の話者分離プロンプト
    prompt = (
        "この音声ファイルの「最初から最後まで」、一切省略せずに完全に文字起こししてください。"
        "要約や途中での打ち切りは絶対にしないでください。"
        "音声には複数の人が話している可能性があります。"
        "発言者ごとに分けて、改行を入れ、"
        "「発言者A: 〇〇」「発言者B: △△」のように誰が話したか明確に区別できるように出力してください。"
    )
    
    # Gemini 2.5 Flash等、利用可能な最新モデルを指定
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    # タイムアウト対策として、API呼び出し時のオプションだけでなく
    # GenerativeModelの呼び出し全体にわたるタイムアウトとして3600秒を設定します。
    # kwargs の timeout よりも強力な `request_options` で確実に上書きします。
    from google.api_core import retry
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    
    # セーフティフィルターによる意図しないブロック (finish_reason=2) を防ぐため、
    # 判定基準を「ブロックしない」に緩和します。
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
    
    # さらに長時間の通信無応答によるソケット切断を防ぐため stream=True を使用し、
    # 最大出力トークン数を上限付近まで引き上げて途中打ち切りを防ぐようにします。
    generation_config = genai.types.GenerationConfig(
        max_output_tokens=8192,
    )
    
    response = model.generate_content(
        [prompt, uploaded_file],
        stream=True,
        generation_config=generation_config,
        request_options={"timeout": 3600, "retry": retry.Retry(deadline=3600)},
        safety_settings=safety_settings
    )
    
    # ストリーミングされたチャンクを結合して最終的なテキストにする
    transcription = ""
    try:
        for chunk in response:
            try:
                if hasattr(chunk, "text") and chunk.text:
                    transcription += chunk.text
            except ValueError as ve:
                # ブロックの警告（FinishReason等）が原因で .text にアクセスできない場合
                print(f"Skipping chunk due to ValueError: {ve}")
                continue
            except Exception as e:
                print(f"Error accessing chunk text: {e}")
                continue
    except Exception as stream_e:
        print(f"Error during streaming response: {stream_e}")
        # もし途中で終わってしまっても、そこまでの文字起こし結果は保持させる
        pass

    if not transcription:
        # 万が一全くテキストが得られなかった場合のフォールバック（強制取得）
        transcription = response.text if hasattr(response, "text") else "文字起こし結果を取得できませんでした。"
    
    # ファイルを消去してクリーンアップ
    try:
        genai.delete_file(uploaded_file.name)
        print("Cleaned up file from Gemini.")
    except Exception as e:
        print(f"Warning: Failed to delete file {uploaded_file.name} from Gemini: {e}")

    return transcription
