import os
import sys
from jinjer_client import JinjerClient

def debug():
    try:
        jinjer = JinjerClient()
        print("--- 申請フォーム一覧取得テスト ---")
        forms = jinjer.get_request_forms()
        print(f"取得したフォーム数: {len(forms)}")
        
        categories = {}
        for form in forms:
            cat_id = form.get("request_category_id")
            cat_name = form.get("request_category_name")
            form_id = form.get("id")
            form_name = form.get("name")
            
            if cat_id not in categories:
                categories[cat_id] = {"name": cat_name, "forms": []}
            categories[cat_id]["forms"].append({"id": form_id, "name": form_name})
            
        for cat_id, data in categories.items():
            print(f"カテゴリーID: {cat_id} ({data['name']})")
            for f in data["forms"]:
                print(f"  - フォームID: {f['id']} ({f['name']})")
                
    except Exception as e:
        print(f"\n[DEBUG ERROR] 実行中にエラーが発生しました:")
        print(f"型: {type(e).__name__}")
        print(f"メッセージ: {e}")
        # スタックトレースは不要（メッセージに詳細が含まれるように jinjer_client.py を修正済み）

if __name__ == "__main__":
    debug()
