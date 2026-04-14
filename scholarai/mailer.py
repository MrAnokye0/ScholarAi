import os
import smtplib
import random
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

# SMTP Configuration helper
def get_smtp_config():
    """Dynamically reload settings from .env."""
    load_dotenv(override=True)
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
    """Sends a 6-digit verification code to the user (non-blocking)."""
    subject = "Verify Your ScholarAI Account"
    html = f"""
    <div style="font-family: sans-serif; max-width: 500px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
        <h2 style="color: #4361EE; text-align: center;">Welcome to ScholarAI!</h2>
        <p>Thank you for signing up. Please use the following 6-digit code to verify your account:</p>
        <div style="background: #f4f7fe; padding: 20px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 5px; color: #4361EE; border-radius: 8px;">
            {code}
        </div>
        <p style="font-size: 12px; color: #666; margin-top: 20px;">If you did not create an account, please ignore this email.</p>
    </div>
    """
    threading.Thread(target=send_email, args=(subject, email, html), daemon=True).start()
    return True

def send_password_reset(email, code):
    """Sends a password reset code to the user (non-blocking)."""
    subject = "Reset Your ScholarAI Password"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #4361EE; padding: 20px; text-align: center; border-radius: 8px;">
            <h1 style="color: white; margin: 0;">ScholarAI</h1>
            <p style="color: white; margin: 5px 0 0;">Password Reset Request</p>
        </div>
        <div style="background-color: white; padding: 30px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <p style="color: #333; font-size: 16px;">Hello,</p>
            <p style="color: #333; font-size: 16px;">Use the following code to reset your ScholarAI password:</p>
            <div style="background: #f4f7fe; padding: 20px; text-align: center; font-size: 28px; font-weight: bold; letter-spacing: 8px; color: #4361EE; border-radius: 8px; margin: 20px 0;">
                {code}
            </div>
            <p style="color: #666; font-size: 14px;">This code expires in 15 minutes. If you didn't request this, ignore this email.</p>
            <p style="color: #666; font-size: 14px;">Best regards,<br>The ScholarAI Team</p>
        </div>
    </div>
    """
    threading.Thread(target=send_email, args=(subject, email, html), daemon=True).start()
    return True

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
