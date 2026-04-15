import os
import smtplib
import random
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from pathlib import Path

# Load .env from the same directory as this script
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# SMTP Configuration helper
def get_smtp_config():
    """Dynamically reload settings from .env."""
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path, override=True)
    return {
        "server":   os.getenv("SMTP_SERVER", "smtp.gmail.com").strip(),
        "port":     int(os.getenv("SMTP_PORT", 587)),
        "user":     os.getenv("SMTP_USER", "").strip(),
        "password": os.getenv("SMTP_PASSWORD", "").strip(),
        "from":     os.getenv("SMTP_FROM", "").strip() or f"ScholarAI <{os.getenv('SMTP_USER', '')}>"
    }

def is_smtp_configured():
    config = get_smtp_config()
    return bool(config["user"] and config["password"])


def send_email(subject, recipient, body_html):
    """Sends an HTML email using dynamic SMTP settings."""
    config = get_smtp_config()
    
    if not config["user"] or not config["password"]:
        print(f"\n[MOCK EMAIL] To: {recipient}\nSubject: {subject}\n")
        return True

    msg = MIMEMultipart()
    msg['From'] = config["from"]
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body_html, 'html'))

    # Try STARTTLS (port 587) first, then SSL (port 465)
    for attempt in [("starttls", config["server"], config["port"]),
                    ("ssl",      config["server"], 465)]:
        method, host, port = attempt
        try:
            if method == "starttls":
                server = smtplib.SMTP(host, port, timeout=8)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(host, port, timeout=8)
            server.login(config["user"], config["password"])
            server.send_message(msg)
            server.quit()
            print(f"Email sent to {recipient} via {method}")
            return True
        except smtplib.SMTPAuthenticationError as e:
            print(f"Auth failed: {e}")
            return False  # No point retrying with wrong credentials
        except Exception as e:
            print(f"{method} attempt failed: {type(e).__name__}: {e}")
            continue

    print(f"All SMTP attempts failed for {recipient}")
    return False

def send_verification_code(email, code):
    """Sends a 6-digit verification code to the user (synchronous for Streamlit Cloud)."""
    subject = "ScholarAI — Verify Your Account"
    html = f"""
    <div style="font-family:'Helvetica Neue',Arial,sans-serif;max-width:520px;margin:auto;background:#0B0F19;border-radius:16px;overflow:hidden;border:1px solid rgba(255,255,255,0.08)">
      <div style="background:linear-gradient(135deg,#4361EE,#7209B7);padding:32px;text-align:center">
        <h1 style="color:#fff;margin:0;font-size:1.6rem;font-weight:800;letter-spacing:-.02em">🎓 ScholarAI</h1>
        <p style="color:rgba(255,255,255,.8);margin:6px 0 0;font-size:.9rem">Email Verification</p>
      </div>
      <div style="padding:36px 32px;background:#0d1117">
        <p style="color:#E2E8F0;font-size:1rem;margin-bottom:8px">Welcome to ScholarAI!</p>
        <p style="color:#94A3B8;font-size:.9rem;line-height:1.6;margin-bottom:28px">
          Use the code below to verify your account. It expires in 10 minutes.
        </p>
        <div style="background:rgba(67,97,238,.12);border:1px solid rgba(67,97,238,.3);border-radius:12px;padding:24px;text-align:center;margin-bottom:28px">
          <div style="font-size:2.2rem;font-weight:900;letter-spacing:.3em;color:#818cf8;font-family:monospace">{code}</div>
        </div>
        <p style="color:#475569;font-size:.8rem;text-align:center">If you didn't create an account, you can safely ignore this email.</p>
      </div>
      <div style="background:#0B0F19;padding:16px;text-align:center;border-top:1px solid rgba(255,255,255,.06)">
        <p style="color:#334155;font-size:.75rem;margin:0">© 2026 ScholarAI · AI-Powered Literature Reviews</p>
      </div>
    </div>
    """
    # Send synchronously for Streamlit Cloud compatibility
    return send_email(subject, email, html)

def send_password_reset(email, code):
    """Sends a password reset code to the user (synchronous for Streamlit Cloud)."""
    subject = "ScholarAI — Reset Your Password"
    html = f"""
    <div style="font-family:'Helvetica Neue',Arial,sans-serif;max-width:520px;margin:auto;background:#0B0F19;border-radius:16px;overflow:hidden;border:1px solid rgba(255,255,255,0.08)">
      <div style="background:linear-gradient(135deg,#4361EE,#7209B7);padding:32px;text-align:center">
        <h1 style="color:#fff;margin:0;font-size:1.6rem;font-weight:800;letter-spacing:-.02em">🎓 ScholarAI</h1>
        <p style="color:rgba(255,255,255,.8);margin:6px 0 0;font-size:.9rem">Password Reset Request</p>
      </div>
      <div style="padding:36px 32px;background:#0d1117">
        <p style="color:#E2E8F0;font-size:1rem;margin-bottom:8px">Hello,</p>
        <p style="color:#94A3B8;font-size:.9rem;line-height:1.6;margin-bottom:28px">
          Use the code below to reset your ScholarAI password. It expires in 15 minutes.
        </p>
        <div style="background:rgba(67,97,238,.12);border:1px solid rgba(67,97,238,.3);border-radius:12px;padding:24px;text-align:center;margin-bottom:28px">
          <div style="font-size:2.2rem;font-weight:900;letter-spacing:.3em;color:#818cf8;font-family:monospace">{code}</div>
        </div>
        <p style="color:#475569;font-size:.8rem;text-align:center">If you didn't request this, you can safely ignore this email.</p>
      </div>
      <div style="background:#0B0F19;padding:16px;text-align:center;border-top:1px solid rgba(255,255,255,.06)">
        <p style="color:#334155;font-size:.75rem;margin:0">© 2026 ScholarAI · AI-Powered Literature Reviews</p>
      </div>
    </div>
    """
    # Send synchronously for Streamlit Cloud compatibility
    return send_email(subject, email, html)

def generate_6_digit_code():
    """Generates a random 6-digit code as a string."""
    return str(random.randint(100000, 999999))

def test_email_config():
    """Test email configuration and return detailed status."""
    config = get_smtp_config()
    
    if not config["user"] or not config["password"]:
        return {
            "success": False,
            "error": "SMTP credentials not configured",
            "details": "Please set SMTP_USER and SMTP_PASSWORD in .env file"
        }
    
    try:
        # Test connection to SMTP server
        server = smtplib.SMTP(config["server"], config["port"], timeout=10)
        server.starttls()
        server.login(config["user"], config["password"])
        server.quit()
        
        return {
            "success": True,
            "message": "Email configuration is working",
            "smtp_server": config["server"],
            "smtp_port": config["port"],
            "smtp_user": config["user"]
        }
    except smtplib.SMTPAuthenticationError as e:
        return {
            "success": False,
            "error": "Authentication failed",
            "details": f"Invalid credentials or need App Password: {e}",
            "help": "Generate Gmail App Password: https://myaccount.google.com/apppasswords"
        }
    except smtplib.SMTPConnectError as e:
        return {
            "success": False,
            "error": "Connection failed",
            "details": f"Cannot connect to SMTP server: {e}",
            "help": "Check internet connection and SMTP server settings"
        }
    except Exception as e:
        return {
            "success": False,
            "error": "Unexpected error",
            "details": f"{type(e).__name__}: {e}"
        }

def send_email_with_fallback(subject, recipient, body_html):
    """Send email — thin wrapper kept for compatibility."""
    if send_email(subject, recipient, body_html):
        return True, "Email sent successfully"
    return False, "Failed to send email. Check SMTP credentials in .env"
