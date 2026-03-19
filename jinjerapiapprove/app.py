import streamlit as st
import pandas as pd
from jinjer_client import JinjerClient
from gpt_analyzer import GPTAnalyzer
from datetime import datetime
import time
import io

# ページ設定
st.set_page_config(
    page_title="Jinjer Workflow Analyzer",
    page_icon="🔍",
    layout="wide"
)

# スタイル
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007bff;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    st.title("🔍 ジンジャー ワークフロー自動分析")
    st.markdown("進行中の申請を自動取得し、AI（GPT-4o）が内容を判定・要約します。")

    # サイドバー設定
    st.sidebar.header("設定")
    my_id = st.sidebar.text_input("自分の社員番号 (フィルタ用)", value="", help="入力すると、自分が承認者のタスクのみを表示します")
    status_filter = st.sidebar.selectbox("取得するステータス", options=[("2", "進行中"), ("1", "承認完了")], format_func=lambda x: x[1])[0]
    max_count = st.sidebar.number_input("対象件数 (0で全件分析)", min_value=0, step=1, value=0, help="分析する最大件数を制限します。0の場合は全件取得します。")
    
    if st.button("分析を開始する"):
        try:
            jinjer = JinjerClient()
            gpt = GPTAnalyzer()
        except Exception as e:
            st.error(f"初期化エラー: {e}")
            return

        # 申請一覧を取得
        with st.spinner("申請一覧を取得中..."):
            all_requests = jinjer.get_workflow_requests(status=status_filter)
        
        if not all_requests:
            st.info("対象の申請は見つかりませんでした。")
            return

        # フィルタリング済みのリスト（後続の処理で自分宛のみに絞るため、全取得後の処理を念頭に置くが、
        # メモリ節約と速度向上のため、あらかじめ全件分析が必要か判定する）
        
        st.write(f"合計 {len(all_requests)} 件の申請が見つかりました。分析を開始します...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        analyzed_count = 0
        
        for i, req in enumerate(all_requests):
            # 対象件数に達した場合は終了
            if max_count > 0 and analyzed_count >= max_count:
                break

            request_id = req.get("id")
            category_id = req.get("_category_id")
            form_id = req.get("_form_id")
            title = req.get("title", "無題")
            requester = f"{req.get('requester', {}).get('last_name')} {req.get('requester', {}).get('first_name')}"
            requested_at = req.get("requested_at")
            request_url = req.get("request_url")

            status_text.text(f"分析中 ({analyzed_count+1}/{max_count if max_count > 0 else len(all_requests)}): {title}")

            # 詳細情報の取得
            details = jinjer.get_request_details(request_id, category_id, form_id)
            if not details:
                progress_bar.progress((i + 1) / len(all_requests))
                continue
                
            approval_histories = details.get("approval_histories", [])
            
            # 自分が現在の承認者かチェック
            if my_id:
                current_step = None
                for step in approval_histories:
                    app_date = step.get("approved_date")
                    if not app_date:
                        current_step = step
                        break
                
                if current_step:
                    approver_id = current_step.get("approver", {}).get("id")
                    if str(approver_id).strip() != str(my_id).strip():
                        progress_bar.progress((i + 1) / len(all_requests))
                        continue
            
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
            
            analyzed_count += 1
            progress_bar.progress((i + 1) / len(all_requests))
            time.sleep(0.5)

        status_text.text("分析完了！")
        progress_bar.progress(1.0)
        
        if not results:
            st.warning("分析対象となった申請、またはあなたの承認待ちタスクはありませんでした。")
            return

        # エクセル出力用にDataFrameを作成
        df = pd.DataFrame(results)
        
        st.subheader("分析結果一覧")
        
        st.dataframe(
            df,
            column_config={
                "判定": st.column_config.TextColumn("判定", width="small"),
                "件名": st.column_config.TextColumn("件名", width="medium"),
                "理由": st.column_config.TextColumn("理由", width="large"),
                "要約": st.column_config.TextColumn("要約", width="large"),
                "URL": st.column_config.LinkColumn("URL", display_text="開く", width="small"),
            },
            use_container_width=True,
            hide_index=True,
        )
        st.info("💡 テーブル内のセルにマウスを合わせると、全文がポップアップ表示されます（表示されない場合は下章の詳細をご確認ください）。")

        st.markdown("---")
        st.subheader("📋 分析詳細（全文確認用）")
        st.caption("各項目をクリックすると、AIの分析理由と要約の全文を確認できます。")

        for res in results:
            label = f"[{res['判定']}] {res['件名']} ({res['申請者']})"
            icon = "✅" if res['判定'] == "OK" else "⚠️" if res['判定'] == "要確認" else "🚨" if res['判定'] == "NG" else "ℹ️"
            
            with st.expander(f"{icon} {label}"):
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.markdown("**判定理由**")
                    st.info(res['理由'])
                with col2:
                    st.markdown("**申請要約**")
                    st.success(res['要約'])
                st.markdown(f"[ジンジャーでこの申請を開く]({res['URL']})")

        # エクセルダウンロード
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        xlsx_filename = f"workflow_analysis_{timestamp}.xlsx"
        
        output = io.BytesIO()
        try:
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="分析結果")
                workbook = writer.book
                worksheet = writer.sheets["分析結果"]
                # URLをハイパーリンク化
                for j, url in enumerate(df["URL"], start=2):
                    if pd.notna(url):
                        cell = worksheet.cell(row=j, column=8) # H列
                        cell.hyperlink = url
                        cell.style = "Hyperlink"
        except Exception as e:
            st.error(f"エクセル生成エラー: {e}")
            return
        
        st.sidebar.markdown("---")
        st.sidebar.download_button(
            label="Excel形式でダウンロード",
            data=output.getvalue(),
            file_name=xlsx_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if __name__ == "__main__":
    main()
