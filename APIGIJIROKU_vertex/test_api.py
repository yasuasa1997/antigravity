import os
from dotenv import load_dotenv
import google.generativeai as genai
from mailer import send_transcription_email
import sys

def main():
    print("Loading .env file...")
    load_dotenv()
    
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print("❌ GEMINI_API_KEY is not set in .env")
        sys.exit(1)
        
    print(f"✅ Loaded GEMINI_API_KEY: {gemini_api_key[:5]}...{gemini_api_key[-5:]}")
    
    print("\n--- Testing Gemini API ---")
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content("こんにちは！返事は「テスト成功」とだけ返してください。")
        print(f"✅ Gemini API Test Success!")
        print(f"Reply: {response.text}")
    except Exception as e:
        print(f"❌ Gemini API Test Failed: {e}")
        
    print("\n--- Testing Gmail SMTP ---")
    to_email = os.getenv("SMTP_USERNAME")
    if not to_email:
        print("❌ SMTP_USERNAME is not set, cannot determine recipient.")
        sys.exit(1)
        
    print(f"Sending test email to: {to_email}")
    try:
        send_transcription_email(to_email, "これはGeminiとGmailの設定が正しく機能しているか確認するためのテストメールです。")
        print("✅ Gmail SMTP Test Success!")
    except Exception as e:
        print(f"❌ Gmail SMTP Test Failed: {e}")

if __name__ == "__main__":
    main()
