"""
Email Diagnosis Script - Test SMTP and send test email
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

print("=" * 60)
print("SCHOLARAI EMAIL DIAGNOSIS")
print("=" * 60)

# Check environment variables
print("\n1. CHECKING ENVIRONMENT VARIABLES:")
print("-" * 60)
smtp_server = os.getenv("SMTP_SERVER", "")
smtp_port = os.getenv("SMTP_PORT", "")
smtp_user = os.getenv("SMTP_USER", "")
smtp_password = os.getenv("SMTP_PASSWORD", "")
smtp_from = os.getenv("SMTP_FROM", "")

print(f"SMTP_SERVER: {smtp_server if smtp_server else '❌ NOT SET'}")
print(f"SMTP_PORT: {smtp_port if smtp_port else '❌ NOT SET'}")
print(f"SMTP_USER: {smtp_user if smtp_user else '❌ NOT SET'}")
print(f"SMTP_PASSWORD: {'*' * len(smtp_password) if smtp_password else '❌ NOT SET'}")
print(f"SMTP_FROM: {smtp_from if smtp_from else '❌ NOT SET'}")

if not all([smtp_server, smtp_port, smtp_user, smtp_password]):
    print("\n❌ ERROR: SMTP credentials not fully configured!")
    sys.exit(1)

print("\n✅ All SMTP environment variables are set")

# Test SMTP connection
print("\n2. TESTING SMTP CONNECTION:")
print("-" * 60)

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    print(f"Connecting to {smtp_server}:{smtp_port}...")
    server = smtplib.SMTP(smtp_server, int(smtp_port), timeout=10)
    print("✅ Connected to SMTP server")
    
    print("Starting TLS...")
    server.starttls()
    print("✅ TLS started")
    
    print(f"Logging in as {smtp_user}...")
    server.login(smtp_user, smtp_password)
    print("✅ Login successful")
    
    server.quit()
    print("✅ SMTP connection test PASSED")
    
except smtplib.SMTPAuthenticationError as e:
    print(f"❌ AUTHENTICATION FAILED: {e}")
    print("\n🔧 FIX: Generate a new Gmail App Password:")
    print("   https://myaccount.google.com/apppasswords")
    sys.exit(1)
except Exception as e:
    print(f"❌ CONNECTION FAILED: {type(e).__name__}: {e}")
    sys.exit(1)

# Send test email
print("\n3. SENDING TEST EMAIL:")
print("-" * 60)

test_email = input("Enter email address to send test OTP to: ").strip()
if not test_email or "@" not in test_email:
    print("❌ Invalid email address")
    sys.exit(1)

test_code = "123456"

msg = MIMEMultipart()
msg['From'] = smtp_from
msg['To'] = test_email
msg['Subject'] = "ScholarAI — Test Verification Code"

html = f"""
<div style="font-family:'Helvetica Neue',Arial,sans-serif;max-width:520px;margin:auto;background:#0B0F19;border-radius:16px;overflow:hidden;border:1px solid rgba(255,255,255,0.08)">
  <div style="background:linear-gradient(135deg,#4361EE,#7209B7);padding:32px;text-align:center">
    <h1 style="color:#fff;margin:0;font-size:1.6rem;font-weight:800;letter-spacing:-.02em">🎓 ScholarAI</h1>
    <p style="color:rgba(255,255,255,.8);margin:6px 0 0;font-size:.9rem">Email Test</p>
  </div>
  <div style="padding:36px 32px;background:#0d1117">
    <p style="color:#E2E8F0;font-size:1rem;margin-bottom:8px">This is a test email!</p>
    <p style="color:#94A3B8;font-size:.9rem;line-height:1.6;margin-bottom:28px">
      If you receive this, your SMTP configuration is working correctly.
    </p>
    <div style="background:rgba(67,97,238,.12);border:1px solid rgba(67,97,238,.3);border-radius:12px;padding:24px;text-align:center;margin-bottom:28px">
      <div style="font-size:2.2rem;font-weight:900;letter-spacing:.3em;color:#818cf8;font-family:monospace">{test_code}</div>
    </div>
    <p style="color:#475569;font-size:.8rem;text-align:center">This is a test verification code.</p>
  </div>
  <div style="background:#0B0F19;padding:16px;text-align:center;border-top:1px solid rgba(255,255,255,.06)">
    <p style="color:#334155;font-size:.75rem;margin:0">© 2026 ScholarAI · AI-Powered Literature Reviews</p>
  </div>
</div>
"""

msg.attach(MIMEText(html, 'html'))

try:
    print(f"Sending test email to {test_email}...")
    server = smtplib.SMTP(smtp_server, int(smtp_port), timeout=10)
    server.starttls()
    server.login(smtp_user, smtp_password)
    server.send_message(msg)
    server.quit()
    
    print("✅ TEST EMAIL SENT SUCCESSFULLY!")
    print(f"\n📧 Check {test_email} inbox (and spam folder)")
    print(f"🔢 Test code: {test_code}")
    
except Exception as e:
    print(f"❌ FAILED TO SEND EMAIL: {type(e).__name__}: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)
