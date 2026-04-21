import smtplib
from email.message import EmailMessage
import os

def send_transcription_email(to_email: str, transcription_text: str):
    """
    文字起こし結果を指定のメールアドレスに送信する
    """
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")

    # メール内容の設定（本文は固定メッセージのみ）
    msg = EmailMessage()
    msg.set_content("文字起こしが完了しました。\n添付のテキストファイルをご確認ください。\n\n※このメールは自動送信です。")
    msg['Subject'] = "【自動送信】音声ファイルの文字起こし結果"
    
    # 差出人の表示名をわかりやすく設定 (オプション)
    if smtp_username:
        msg['From'] = f"AI文字起こしシステム <{smtp_username}>"
    else:
         msg['From'] = "no-reply@example.com"
         
    msg['To'] = to_email

    # 文字起こし結果をテキストファイルとして添付
    # メモリ上でbytesデータとして扱って添付します
    transcription_bytes = transcription_text.encode('utf-8')
    msg.add_attachment(transcription_bytes, maintype='text', subtype='plain', filename='transcription_result.txt')

    try:
        # SMTP_SSL (ポート465等の場合)
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                if smtp_username and smtp_password:
                    server.login(smtp_username, smtp_password)
                server.send_message(msg)
        # ちなみに587などはSTARTTLSを使うのが一般的
        else:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                if smtp_username and smtp_password:
                    server.login(smtp_username, smtp_password)
                server.send_message(msg)
        print(f"Email successfully sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}. Error: {e}")
        raise e
