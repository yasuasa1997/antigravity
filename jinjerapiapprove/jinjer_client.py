import os
import requests
import urllib3
import json
import time
from typing import List, Dict, Any, Optional

# SSL証明書検証エラー（企業プロキシ等）への対策
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class JinjerClient:
    """
    ジンジャーAPIとの通信を担当するクライアントクラス
    """
    BASE_URL = "https://api.jinjer.biz"

    def __init__(self):
        # 環境変数から設定を読み込み（前後の空白や引用符を削除）
        def clean_env(key):
            val = os.getenv(key)
            if val:
                val = val.strip().strip('"').strip("'")
            return val

        self.api_key = clean_env("JINJER_API_KEY")
        self.api_secret = clean_env("JINJER_API_SECRET")
        self.company_code = clean_env("JINJER_COMPANY_CODE")
        self.api_token = clean_env("JINJER_API_TOKEN")
        self.my_employee_id = clean_env("JINJER_MY_EMPLOYEE_ID")

        if not self.company_code:
            raise ValueError("Environment variable JINJER_COMPANY_CODE is required.")
        
        # APIキー/シークレットがある場合は、トークンを再取得することを優先
        if self.api_key and self.api_secret:
            print("APIキーとシークレットを使用して新しいトークンを取得します...")
            self.api_token = self._fetch_token()
        elif not self.api_token:
            raise ValueError("Either (JINJER_API_KEY and JINJER_API_SECRET) or JINJER_API_TOKEN must be set.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "X-Company-Code": self.company_code
        }

    def _safe_get(self, url: str, params: Optional[Dict] = None, max_retries: int = 3) -> requests.Response:
        """
        Rate Limit (429) を考慮したGETリクエスト
        """
        for i in range(max_retries):
            response = requests.get(url, headers=self.headers, params=params, verify=False)
            if response.status_code == 429:
                wait_time = (i + 1) * 2 # 指数バックオフ的な待機
                print(f"  警告: Rate Limit (429) 到達。{wait_time}秒待機してリトライします ({i+1}/{max_retries})...")
                time.sleep(wait_time)
                continue
            return response
        return response

    def _fetch_token(self) -> str:
        """
        APIキーとシークレットキーを使用してアクセストークンを取得する。
        """
        headers = {
            "X-API-KEY": self.api_key,
            "X-SECRET-KEY": self.api_secret,
            "X-Company-Code": self.company_code,
            "Content-Type": "application/json"
        }
        response = requests.get(f"{self.BASE_URL}/v2/token", headers=headers, verify=False)
        if response.status_code == 200:
            token_data = response.json().get("data", {})
            token = token_data.get("access_token")
            if not token:
                raise Exception(f"Token not found in response: {response.text}")
            print(f"トークンの取得に成功しました。 (長さ: {len(token)})")
            return token
        else:
            # エラーの詳細を1行で表示
            msg = response.text.replace('\n', ' ')[:200]
            print(f"トークン取得失敗 (HTTP {response.status_code}): {msg}")
            
            # デバッグ情報
            print(f"環境変数確認: API_KEY(len={len(self.api_key or '')}), SECRET(len={len(self.api_secret or '')}), COMPANY(len={len(self.company_code or '')})")
            
            raise Exception(f"Auth Error {response.status_code}")

    def get_workflow_requests(self, status: str = "2") -> List[Dict[str, Any]]:
        """
        ワークフロー申請書の一覧を取得する。
        status: 1:承認完了, 2:進行中, 3:否認, 4:取下げ, 7:差し戻し (デフォルトは 2:進行中)
        """
        categories = self.get_request_forms()
        
        all_requests = []
        for category in categories:
            cat_id = category.get("id")
            cat_name = category.get("name") or "Unknown"
            forms = category.get("request_forms", [])
            
            # 勤怠(2)と経費(3)はワークフローAPIの対象外なのでスキップ
            if cat_id in ["2", "3"]:
                continue

            print(f"カテゴリを探査中: {cat_name} (ID: {cat_id}), フォーム数: {len(forms)}")
            
            for form in forms:
                form_id = form.get("id")
                form_name = form.get("name")
                params = {
                    "request-category-id": cat_id,
                    "request-form-id": form_id,
                    "status": status
                }
                
                # リクエスト。429対策として共通メソッドを使用
                response = self._safe_get(f"{self.BASE_URL}/v1/workflow-requests", params=params)
                
                if response.status_code == 200:
                    data = response.json().get("data", [])
                    if data:
                        print(f"  -> {form_name}: {len(data)}件の申請が見つかりました")
                        for item in data:
                            item["_category_id"] = cat_id
                            item["_form_id"] = form_id
                            item["_form_name"] = form_name
                        all_requests.extend(data)
                
                # 連続リクエストによる負荷軽減のため少し待機
                time.sleep(0.3)
        
        return all_requests

    def get_request_forms(self) -> List[Dict[str, Any]]:
        """
        申請区分と申請フォームの一覧を取得する。
        """
        response = self._safe_get(f"{self.BASE_URL}/v1/master/request-categories/request-forms")
        if response.status_code == 200:
            raw_data = response.json().get("data", [])
            # レスポンス構造の解析: data[0]["request_categories"] という構造になっている
            if raw_data and isinstance(raw_data, list) and "request_categories" in raw_data[0]:
                return raw_data[0]["request_categories"]
            return raw_data
        else:
            print(f"申請フォーム一覧取得失敗: ステータスコード={response.status_code}")
            raise Exception(f"Failed to fetch request forms: {response.text}")

    def get_request_details(self, request_id: str, category_id: str, form_id: str = None) -> Dict[str, Any]:
        """
        申請書の詳細情報を取得する。
        """
        # 標準的な申請フォームのマッピング (カテゴリ 1: 人事 の場合)
        endpoint_map = {
            "1": "onboardings",              # 入社申請
            "2": "affiliation-changes",      # 異動申請（主務）
            "3": "sub-affiliation-changes",  # 異動申請（兼務）
            "4": "offboardings",             # 退社申請
            "5": "dependent-changes",        # 扶養変更申請
            "6": "address-changes",          # 住所・通勤費変更申請
        }
        
        sub_path = "custom-requests"
        params = {}
        
        if str(category_id) == "1" and str(form_id) in endpoint_map:
            sub_path = endpoint_map[str(form_id)]
        else:
            # カスタム申請（およびカテゴリ1以外の標準外申請）の場合、カテゴリIDとフォームIDがクエリパラメータとして必須
            params = {
                "request-category-id": category_id,
                "request-form-id": form_id
            }
        
        response = self._safe_get(f"{self.BASE_URL}/v1/workflow-requests/{sub_path}/{request_id}", params=params)
        if response.status_code == 200:
            return response.json().get("data", {})
        else:
            # 頻出するエラーについては理由を表示
            print(f"  詳細取得失敗: {sub_path}/{request_id} (Status: {response.status_code})")
            return {}

if __name__ == "__main__":
    try:
        client = JinjerClient()
    except Exception as e:
        print(f"Error: {e}")
