import os
import pandas as pd
from jinjer_client import JinjerClient
from gpt_analyzer import GPTAnalyzer
from datetime import datetime
import time
import json

def main():
    print("--- ジンジャー ワークフロー自動分析開始 ---")
    
    # クライアントの初期化
    try:
        jinjer = JinjerClient()
        gpt = GPTAnalyzer()
    except Exception as e:
        print(f"初期化エラー: {e}")
        return

    # 自分自身の社員番号
    my_id = jinjer.my_employee_id
    if not my_id:
        print("警告: JINJER_MY_EMPLOYEE_ID が設定されていません。承認者のフィルタリングを行いません。")

    # 進行中の申請一覧を取得
    print("申請一覧を取得中...")
    all_requests = jinjer.get_workflow_requests(status="2")  # 進行中
    print(f"合計 {len(all_requests)} 件の進行中の申請が見つかりました。")

    results = []

    for req in all_requests:
        request_id = req.get("id")
        category_id = req.get("_category_id")
        form_id = req.get("_form_id")
        title = req.get("title", "無題")
        requester = f"{req.get('requester', {}).get('last_name')} {req.get('requester', {}).get('first_name')}"
        requested_at = req.get("requested_at")
        request_url = req.get("request_url")

        # 詳細情報の取得
        details = jinjer.get_request_details(request_id, category_id, form_id)
        if not details:
            print(f"  警告: [{title}] の詳細を取得できませんでした。スキップします。")
            continue
            
        approval_histories = details.get("approval_histories", [])
        
        # 自分が現在の承認者かチェック
        if my_id:
            # 承認待ち（approved_date が空または None）の最初のステップを探す
            current_step = None
            for step in approval_histories:
                app_date = step.get("approved_date")
                if not app_date:  # None または "" の場合に「未承認」と判定
                    current_step = step
                    break
            
            if current_step:
                approver_id = current_step.get("approver", {}).get("id")
                if str(approver_id).strip() != str(my_id).strip():
                    # 自分が承認者でない場合はスキップ
                    continue
                else:
                    print(f"  -> あなたの承認待ちタスクが見つかりました: {title}")
            else:
                # 承認待ちが見つからない場合はスキップ
                continue
        
        print(f"分析中: {title} (申請者: {requester})...")
        
        # ChatGPTによる分析
        analysis = gpt.analyze_request(details)
        
        # 結果の集約
        results.append({
            "申請書No.": request_id,
            "件名": title,
            "申請者": requester,
            "申請日時": requested_at,
            "判定": analysis.get("judgment"),
            "理由": analysis.get("reason"),
            "要約": analysis.get("summary"),
            "URL": request_url
        })
        
        # Rate Limit対策とChatGPTの負荷分散のため少し待機
        time.sleep(1.0)

    if not results:
        print("分析対象の申請はありませんでした。")
        return

    # 結果を保存 (CSVとエクセル)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"workflow_analysis_{timestamp}.csv"
    xlsx_filename = f"workflow_analysis_{timestamp}.xlsx"

    df = pd.DataFrame(results)
    
    try:
        # CSV出力
        df.to_csv(csv_filename, index=False, encoding="utf-8-sig")
        
        # Excel出力 (リンクを等価的に扱うための後処理)
        with pd.ExcelWriter(xlsx_filename, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="分析結果")
            workbook = writer.book
            worksheet = writer.sheets["分析結果"]
            
            # URL列（G列または最終列）をハイパーリンクにする
            url_col_letter = "H" # 今回の列構成ではH列(8列目)がURLになる想定
            for i, url in enumerate(df["URL"], start=2): # start=2 はヘッダーの次から
                if pd.notna(url):
                    cell = worksheet[f"{url_col_letter}{i}"]
                    cell.hyperlink = url
                    cell.style = "Hyperlink"

        print(f"--- 完了 ---")
        print(f"結果を保存しました:\n - {csv_filename}\n - {xlsx_filename}")
    except Exception as e:
        print(f"ファイル保存エラー: {e}")

if __name__ == "__main__":
    main()
