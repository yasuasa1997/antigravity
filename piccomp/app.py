import streamlit as st
from PIL import Image
import io
import zipfile

st.set_page_config(page_title="Image Resizer", page_icon="🖼️")

st.title("🖼️ 画像解像度リサイズアプリ")
st.write("複数の画像ファイルを一括でリサイズし、ZIPファイルとしてダウンロードできます。縦横比はそのまま維持されます。")

st.sidebar.header("設定")
resize_percentage = st.sidebar.slider(
    "解像度（縦横画像サイズ）変更率 (%)",
    min_value=1,
    max_value=200,
    value=50,
    step=1,
    help="画像の幅・高さを縮小・拡大します。100%で元のサイズ、50%で縦横それぞれ半分のサイズになります。"
)

quality_percentage = st.sidebar.slider(
    "画質（ファイルサイズ）維持率 (%)",
    min_value=1,
    max_value=100,
    value=80,
    step=1,
    help="JPEG保存時の画質を指定します（100が最高画質・最大サイズ。数値が小さいほどファイルサイズが軽くなります）。※PNG等一部フォーマットには適用されず最適化のみ行われます。"
)

uploaded_files = st.file_uploader(
    "画像を選択してください（複数選択可）", 
    type=["png", "jpg", "jpeg"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.write(f"**{len(uploaded_files)} 個**のファイルが選択されました。")
    
    # リサイズ実行ボタン
    if st.button("リサイズを実行"):
        with st.spinner("処理中..."):
            # メモリ上でZIPファイルを作成するためのバッファ
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                # プログレスバー
                progress_bar = st.progress(0)
                
                for i, uploaded_file in enumerate(uploaded_files):
                    try:
                        # 画像を開く
                        img = Image.open(uploaded_file)
                        
                        # 元のサイズを取得
                        original_width, original_height = img.size
                        
                        # 新しいサイズを計算
                        new_width = int(original_width * (resize_percentage / 100))
                        new_height = int(original_height * (resize_percentage / 100))
                        
                        # リサイズ
                        if hasattr(Image, 'Resampling'):
                            resample_method = Image.Resampling.LANCZOS
                        else:
                            resample_method = Image.LANCZOS
                            
                        # 最低でも1x1ピクセルは確保する
                        resized_img = img.resize((max(1, new_width), max(1, new_height)), resample_method)
                        
                        # 画像をバイトデータに書き出し
                        img_byte_arr = io.BytesIO()
                        
                        # オリジナルのフォーマットを取得 (PNG, JPEG 等) 
                        # アップロードされた画像ファイルによってはformatが取れない場合があるのでファイル名から推論
                        img_format = img.format if img.format else uploaded_file.name.split('.')[-1].upper()
                        if img_format == 'JPG':
                            img_format = 'JPEG'
                        
                        # JPEGの場合、RGBAモードをRGBに変換
                        if img_format == 'JPEG' and resized_img.mode in ('RGBA', 'P', 'LA'):
                            # 白背景でブレンドしてからRGBに変換すると透過部分がきれいになる
                            background = Image.new('RGB', resized_img.size, (255, 255, 255))
                            if resized_img.mode == 'RGBA':
                                background.paste(resized_img, mask=resized_img.split()[3]) # alpha channel
                            else:
                                background.paste(resized_img)
                            resized_img = background
                                
                        if img_format == 'JPEG':
                            resized_img.save(img_byte_arr, format=img_format, quality=quality_percentage)
                        elif img_format == 'PNG':
                            # PNGは可逆圧縮のためQuality指定ではなくOptimizeをかける
                            resized_img.save(img_byte_arr, format=img_format, optimize=True)
                        else:
                            resized_img.save(img_byte_arr, format=img_format)
                        img_byte_arr.seek(0)
                        
                        # ZIPに追加
                        # 元のファイル名にプレフィックスやサフィックスを付けて保存
                        original_name = uploaded_file.name
                        name_parts = original_name.rsplit('.', 1)
                        if len(name_parts) == 2:
                            new_name = f"{name_parts[0]}_resized_{resize_percentage}pct.{name_parts[1]}"
                        else:
                            new_name = f"{original_name}_resized_{resize_percentage}pct"
                            
                        zip_file.writestr(new_name, img_byte_arr.read())
                        
                    except Exception as e:
                        st.error(f"ファイル {uploaded_file.name} の処理中にエラーが発生しました: {e}")
                        
                    # プログレスバーを更新
                    progress_bar.progress((i + 1) / len(uploaded_files))
            
            # ZIPバッファのポインタを先頭に戻す
            zip_buffer.seek(0)
            
            st.success("処理が完了しました！以下のボタンからダウンロードできます。")
            
            # ダウンロードボタン
            st.download_button(
                label="📦 リサイズ完了画像をダウンロード (ZIP)",
                data=zip_buffer,
                file_name=f"resized_images_{resize_percentage}pct.zip",
                mime="application/zip"
            )
