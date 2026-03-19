import os
from openai import OpenAI
import json
import httpx

class GPTAnalyzer:
    """
    OpenAI APIを使用して申請内容を分析するクラス
    """
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL") # 任意でエンドポイントを変更可能にする
        
        if not self.api_key:
            raise ValueError("Environment variable OPENAI_API_KEY is required.")
        
        # 診断ログの出力
        print(f"--- OpenAI API 診断 ---")
        print(f" - API Key 長さ: {len(self.api_key)}")
        print(f" - API Key 接頭辞: {self.api_key[:7]}...")
        if not self.api_key.startswith("sk-"):
            print(" 【警告】APIキーが 'sk-' で始まっていません。OpenAIの有効なキーではない可能性があります。")
        
        if self.base_url:
            print(f" - Base URL: {self.base_url}")
        
        # 企業環境等でのSSL証明書エラー回避のため verify=False を設定
        http_client = httpx.Client(verify=False)
        self.client = OpenAI(
            api_key=self.api_key, 
            base_url=self.base_url, # None の場合はデフォルトの https://api.openai.com/v1 が使用される
            http_client=http_client
        )

    def analyze_request(self, request_data: dict) -> dict:
        """
        申請データをChatGPTに投げて判定結果を得る
        """
        # 申請データを文字列化（重要な項目を抽出してプロンプトに含める）
        request_summary = json.dumps(request_data, ensure_ascii=False, indent=2)
        
        prompt = f"""
あなたは企業の人事承認アドバイザーです。
以下のワークフロー申請内容を確認し、問題がないか「判定」を行ってください。

【申請内容】
{request_summary}

【出力フォーマット】
以下のJSON形式のみで回答してください：
{{
  "judgment": "OK" または "要確認" または "NG",
  "reason": "詳細な理由（100文字以内）",
  "summary": "申請内容の簡潔な要約"
}}
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたは正確で客観的な人事アドバイザーです。"},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" }
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            print(f"ChatGPT Analysis Error: {e}")
            return {
                "judgment": "エラー",
                "reason": str(e),
                "summary": "分析に失敗しました"
            }
