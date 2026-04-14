"""
Test script for email functionality
Run this to diagnose email sending issues
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from mailer import test_email_config, send_email_with_fallback, get_smtp_config

def main():
    print("ScholarAI Email Configuration Test")
    print("=" * 50)
    
    # Show current configuration
    config = get_smtp_config()
    print(f"📧 SMTP Configuration:")
    print(f"   Server: {config['server']}")
    print(f"   Port: {config['port']}")
    print(f"   Username: {config['user']}")
    print(f"   From: {config['from']}")
    print(f"   Password: {'✅ Set' if config['password'] else '❌ Not set'}")
    print()
    
    # Test configuration
    print("🧪 Testing SMTP Configuration...")
    test_result = test_email_config()
    
    if test_result["success"]:
        print(f"✅ SUCCESS: {test_result['message']}")
        print(f"   Server: {test_result['smtp_server']}:{test_result['smtp_port']}")
        print(f"   User: {test_result['smtp_user']}")
    else:
        print(f"❌ FAILED: {test_result['error']}")
        print(f"   Details: {test_result['details']}")
        if 'help' in test_result:
            print(f"   Help: {test_result['help']}")
        
        print("\n🔧 Common Solutions:")
        print("1. Enable 2-Step Verification on your Google Account")
        print("2. Generate an App Password: https://myaccount.google.com/apppasswords")
        print("3. Use the App Password instead of your regular password")
        print("4. Make sure 'Less secure app access' is enabled if needed")
        return
    
    print()
    
    # Send test email
    test_email_address = input("📧 Enter email address to send test email (or press Enter to skip): ").strip()
    
    if test_email_address:
        print(f"\n📤 Sending test email to {test_email_address}...")
        
        subject = "ScholarAI Email Test"
        body = """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #4361EE; padding: 20px; text-align: center; border-radius: 8px;">
                <h1 style="color: white; margin: 0;">🎓 ScholarAI</h1>
                <p style="color: white; margin: 5px 0 0;">Email Configuration Test</p>
            </div>
            <div style="background-color: white; padding: 30px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <p style="color: #333; font-size: 16px;">Hello,</p>
                <p style="color: #333; font-size: 16px;">
                    This is a test email from ScholarAI to verify that your email configuration is working correctly.
                </p>
                <p style="color: #666; font-size: 14px;">
                    If you received this email, your SMTP settings are properly configured and password reset emails will work.
                </p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #666; font-size: 14px;">
                    Best regards,<br>
                    The ScholarAI Team
                </p>
            </div>
        </div>
        """
        
        success, message = send_email_with_fallback(subject, test_email_address, body)
        
        if success:
            print(f"✅ Email sent successfully! {message}")
            print(f"   Check your inbox (and spam folder) at {test_email_address}")
        else:
            print(f"❌ Failed to send email: {message}")
            print("   Check the error message above and fix your configuration")
    else:
        print("⏭️  Skipping email test")
    
    print("\n📋 Next Steps:")
    print("1. If test passed: Your password reset emails should work now")
    print("2. If test failed: Fix the SMTP configuration in .env file")
    print("3. Restart your Streamlit app after making changes")
    print("4. Try password reset again")

if __name__ == "__main__":
    main()
