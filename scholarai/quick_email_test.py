"""
Quick email test to send to the user's email address
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from mailer import send_email_with_fallback

def main():
    print("Sending test email to anokyegyasiedward@gmail.com...")
    
    subject = "ScholarAI Password Reset Test"
    body = """
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #4361EE; padding: 20px; text-align: center; border-radius: 8px;">
            <h1 style="color: white; margin: 0;">ScholarAI</h1>
            <p style="color: white; margin: 5px 0 0;">Password Reset Test</p>
        </div>
        <div style="background-color: white; padding: 30px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <p style="color: #333; font-size: 16px;">Hello,</p>
            <p style="color: #333; font-size: 16px;">
                This is a test email to verify that the password reset functionality is working correctly.
            </p>
            <p style="color: #666; font-size: 14px;">
                If you received this email, the password reset feature should now work properly.
            </p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #666; font-size: 14px;">
                Best regards,<br>
                The ScholarAI Team
            </p>
        </div>
    </div>
    """
    
    success, message = send_email_with_fallback(subject, "anokyegyasiedward@gmail.com", body)
    
    if success:
        print(f"SUCCESS: Email sent! {message}")
        print("Check your inbox at anokyegyasiedward@gmail.com")
    else:
        print(f"FAILED: {message}")

if __name__ == "__main__":
    main()
