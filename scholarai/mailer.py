import os
import smtplib
import secrets as _secrets
import time
import logging
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid
from dotenv import load_dotenv
from pathlib import Path

# Load .env from the same directory as this script
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)

# OTP expiry in seconds (10 minutes)
OTP_EXPIRY_SECONDS = 600

# SMTP Configuration helper
def get_smtp_config():
    """Dynamically reload settings from .env."""
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path, override=True)
    return {
        "server":   os.getenv("SMTP_SERVER", "smtp.gmail.com").strip(),
        "port":     int(os.getenv("SMTP_PORT", "587")),
        "user":     os.getenv("SMTP_USER", "").strip(),
        "password": os.getenv("SMTP_PASSWORD", "").strip(),
        "from":     os.getenv("SMTP_FROM", "").strip() or f"ScholarAI <{os.getenv('SMTP_USER', '')}>",
    }

def is_smtp_configured():
    config = get_smtp_config()
    return bool(config["user"] and config["password"])


def send_email(subject, recipient, body_html, max_retries=2):
    """
    Sends an HTML email using dynamic SMTP settings.
    Retries up to max_retries times on transient failures.
    Returns True on success, False on failure.
    """
    config = get_smtp_config()

    logger.info("Attempting to send email | to=%s subject=%s server=%s:%s user=%s",
                recipient, subject, config["server"], config["port"],
                config["user"] or "NOT SET")

    if not config["user"] or not config["password"]:
        logger.error("SMTP not configured — SMTP_USER or SMTP_PASSWORD missing in .env")
        print("❌ SMTP NOT CONFIGURED — set SMTP_USER and SMTP_PASSWORD in scholarai/.env")
        return False

    msg = MIMEMultipart("alternative")
    msg['From']       = config["from"]
    msg['To']         = recipient
    msg['Subject']    = subject
    msg['Date']       = formatdate(localtime=True)
    msg['Message-ID'] = make_msgid(domain="scholarai.app")
    msg['Reply-To']   = config["user"]
    # Headers that improve deliverability and reduce spam scoring
    msg['X-Mailer']          = "ScholarAI Mailer 1.0"
    msg['X-Priority']        = "1"
    msg['Precedence']        = "transactional"
    msg['Auto-Submitted']    = "auto-generated"
    # Plain-text fallback (many spam filters penalise HTML-only emails)
    plain = f"Your ScholarAI one-time code is in this email. If you cannot read HTML, your code was sent separately."
    msg.attach(MIMEText(plain, 'plain', 'utf-8'))
    msg.attach(MIMEText(body_html, 'html', 'utf-8'))

    last_error = None
    for attempt in range(1, max_retries + 2):   # attempts: 1, 2, 3
        try:
            port = config["port"]
            logger.info("SMTP attempt %d/%d — %s:%s",
                        attempt, max_retries + 1, config["server"], port)
            # Port 465 uses SSL directly; 587/25 use STARTTLS
            if port == 465:
                server = smtplib.SMTP_SSL(config["server"], port, timeout=20)
                server.ehlo()
            else:
                server = smtplib.SMTP(config["server"], port, timeout=20)
                server.ehlo()
                server.starttls()
                server.ehlo()
            server.login(config["user"], config["password"])
            refused = server.send_message(msg)
            server.quit()
            # send_message returns a dict of refused recipients — empty = all accepted
            if refused:
                logger.error("❌ Recipients refused by server: %s", refused)
                print(f"❌ Email refused for: {refused}")
                return False
            logger.info("✅ Email delivered to %s (attempt %d)", recipient, attempt)
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error("❌ SMTP auth failed: %s", e)
            print(f"❌ SMTP authentication failed. "
                  f"Generate a Gmail App Password at "
                  f"https://myaccount.google.com/apppasswords")
            return False

        except smtplib.SMTPRecipientsRefused as e:
            logger.error("❌ Recipient refused by SMTP server: %s — %s", recipient, e)
            print(f"❌ Recipient refused: {recipient} — {e}")
            return False

        except smtplib.SMTPSenderRefused as e:
            logger.error("❌ Sender refused: %s", e)
            print(f"❌ Sender address refused: {e}")
            return False

        except smtplib.SMTPDataError as e:
            logger.error("❌ SMTP data error (message rejected): %s", e)
            print(f"❌ Message rejected by server: {e}")
            return False

        except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected,
                ConnectionRefusedError, TimeoutError, OSError) as e:
            last_error = e
            logger.warning("⚠️  Transient SMTP error (attempt %d): %s — %s",
                           attempt, type(e).__name__, e)
            print(f"⚠️  SMTP transient error attempt {attempt}: {type(e).__name__}: {e}")
            if attempt <= max_retries:
                wait = 2 ** attempt
                logger.info("Retrying in %ds…", wait)
                time.sleep(wait)

        except Exception as e:
            last_error = e
            logger.error("❌ Unexpected SMTP error (attempt %d): %s — %s",
                         attempt, type(e).__name__, e)
            print(f"❌ Unexpected error attempt {attempt}: {type(e).__name__}: {e}")
            if attempt <= max_retries:
                time.sleep(2 ** attempt)

    logger.error("❌ All %d SMTP attempts failed for %s. Last error: %s",
                 max_retries + 1, recipient, last_error)
    return False

def send_verification_code(email, code):
    """Sends a 6-digit verification code to the user."""
    subject = f"Your ScholarAI code: {code}"
    plain_body = f"""Your ScholarAI sign-in code is: {code}

This code expires in 10 minutes.

If you did not request this, you can safely ignore this email.

— ScholarAI Team
"""
    html_body = f"""
    <div style="font-family:'Helvetica Neue',Arial,sans-serif;max-width:520px;margin:auto;background:#0B0F19;border-radius:16px;overflow:hidden;border:1px solid rgba(255,255,255,0.08)">
      <div style="background:linear-gradient(135deg,#4361EE,#7209B7);padding:32px;text-align:center">
        <h1 style="color:#fff;margin:0;font-size:1.6rem;font-weight:800;letter-spacing:-.02em">ScholarAI</h1>
        <p style="color:rgba(255,255,255,.8);margin:6px 0 0;font-size:.9rem">Your sign-in code</p>
      </div>
      <div style="padding:36px 32px;background:#0d1117">
        <p style="color:#E2E8F0;font-size:1rem;margin-bottom:8px">Hi there,</p>
        <p style="color:#94A3B8;font-size:.9rem;line-height:1.6;margin-bottom:28px">
          Use the code below to sign in to ScholarAI. It expires in <strong style="color:#E2E8F0">10 minutes</strong>.
        </p>
        <div style="background:rgba(67,97,238,.12);border:1px solid rgba(67,97,238,.3);border-radius:12px;padding:24px;text-align:center;margin-bottom:28px">
          <div style="font-size:2.4rem;font-weight:900;letter-spacing:.35em;color:#818cf8;font-family:monospace">{code}</div>
        </div>
        <p style="color:#475569;font-size:.8rem;text-align:center;line-height:1.6">
          If you didn't request this code, you can safely ignore this email.<br>
          This is an automated message — please do not reply.
        </p>
      </div>
      <div style="background:#0B0F19;padding:16px;text-align:center;border-top:1px solid rgba(255,255,255,.06)">
        <p style="color:#334155;font-size:.75rem;margin:0">ScholarAI · AI-Powered Literature Reviews</p>
      </div>
    </div>
    """
    # Build multipart message manually so both parts go through send_email
    config = get_smtp_config()
    from email.mime.multipart import MIMEMultipart as _MM
    from email.mime.text import MIMEText as _MT
    from email.utils import formatdate, make_msgid
    msg = _MM("alternative")
    msg['From']       = config["from"]
    msg['To']         = email
    msg['Subject']    = subject
    msg['Date']       = formatdate(localtime=True)
    msg['Message-ID'] = make_msgid(domain="scholarai.app")
    msg['Reply-To']   = config["user"]
    msg['X-Mailer']   = "ScholarAI Mailer 1.0"
    msg['Precedence'] = "transactional"
    msg.attach(_MT(plain_body, 'plain', 'utf-8'))
    msg.attach(_MT(html_body, 'html', 'utf-8'))

    if not config["user"] or not config["password"]:
        print("❌ SMTP not configured")
        return False

    for attempt in range(1, 4):
        try:
            port = config["port"]
            if port == 465:
                server = smtplib.SMTP_SSL(config["server"], port, timeout=20)
                server.ehlo()
            else:
                server = smtplib.SMTP(config["server"], port, timeout=20)
                server.ehlo()
                server.starttls()
                server.ehlo()
            server.login(config["user"], config["password"])
            refused = server.sendmail(config["user"], [email], msg.as_string())
            server.quit()
            if refused:
                print(f"❌ Recipient refused: {refused}")
                return False
            print(f"✅ OTP sent to {email}")
            return True
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ Auth failed: {e}")
            return False
        except smtplib.SMTPRecipientsRefused as e:
            print(f"❌ Recipient {email} refused: {e}")
            return False
        except Exception as e:
            print(f"⚠️  Attempt {attempt} failed: {type(e).__name__}: {e}")
            if attempt < 3:
                time.sleep(2 ** attempt)
    return False

def send_password_reset(email, code):
    """Sends a password reset code to the user."""
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
          Use the code below to reset your ScholarAI password. It expires in <strong style="color:#E2E8F0">15 minutes</strong>.
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
    return send_email(subject, email, html)

def generate_6_digit_code():
    """
    Generates a cryptographically secure 6-digit OTP as a zero-padded string.
    Uses secrets.randbelow instead of random.randint to avoid predictability.
    """
    return str(_secrets.randbelow(900000) + 100000)  # always 6 digits: 100000–999999


def is_otp_expired(issued_at_timestamp: float, expiry_seconds: int = OTP_EXPIRY_SECONDS) -> bool:
    """Returns True if the OTP is older than expiry_seconds."""
    return (time.time() - issued_at_timestamp) > expiry_seconds

def test_email_config():
    """Test email configuration and return detailed status."""
    config = get_smtp_config()

    if not config["user"] or not config["password"]:
        return {
            "success": False,
            "error": "SMTP credentials not configured",
            "details": (
                "Set SMTP_USER and SMTP_PASSWORD in scholarai/.env\n"
                "For Gmail: use your Gmail address as SMTP_USER and an App Password as SMTP_PASSWORD.\n"
                "Generate one at https://myaccount.google.com/apppasswords"
            ),
        }

    try:
        port = config["port"]
        if port == 465:
            server = smtplib.SMTP_SSL(config["server"], port, timeout=10)
            server.ehlo()
        else:
            server = smtplib.SMTP(config["server"], port, timeout=10)
            server.ehlo()
            server.starttls()
            server.ehlo()
        server.login(config["user"], config["password"])
        server.quit()
        return {
            "success": True,
            "message": "Email configuration is working",
            "smtp_server": config["server"],
            "smtp_port": config["port"],
            "smtp_user": config["user"],
        }
    except smtplib.SMTPAuthenticationError as e:
        return {
            "success": False,
            "error": "Authentication failed",
            "details": f"Invalid credentials or App Password required: {e}",
            "help": "Generate Gmail App Password: https://myaccount.google.com/apppasswords",
        }
    except smtplib.SMTPConnectError as e:
        return {
            "success": False,
            "error": "Connection failed",
            "details": f"Cannot connect to SMTP server: {e}",
            "help": "Check internet connection and SMTP_SERVER / SMTP_PORT settings",
        }
    except Exception as e:
        return {
            "success": False,
            "error": "Unexpected error",
            "details": f"{type(e).__name__}: {e}",
        }


def send_email_with_fallback(subject, recipient, body_html):
    """Send email — thin wrapper kept for compatibility."""
    if send_email(subject, recipient, body_html):
        return True, "Email sent successfully"
    return False, "Failed to send email. Check SMTP credentials in .env"
