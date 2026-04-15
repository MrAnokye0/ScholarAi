# 🔧 EMAIL NOT RECEIVED - TROUBLESHOOTING GUIDE

## Problem
Users are not receiving OTP verification emails after signup.

---

## ✅ IMMEDIATE FIXES APPLIED

### 1. Enhanced Logging
Added detailed logging to `mailer.py` to show:
- SMTP configuration status
- Connection attempts
- Authentication results
- Send status

### 2. Better Error Messages
Updated `app.py` signup flow to:
- Show verification code on screen if email fails
- Display clear error messages
- Provide emergency code access
- Guide users to check spam folder

### 3. Increased Timeouts
Changed SMTP timeout from 8 seconds to 15 seconds for better reliability on Streamlit Cloud.

### 4. SMTP Configuration Check
Added check to verify SMTP is configured before attempting to send.

---

## 🔍 DIAGNOSIS STEPS

### Step 1: Run Email Diagnosis Script
```bash
cd scholarai
python diagnose_email.py
```

This will:
1. Check environment variables
2. Test SMTP connection
3. Send a test email
4. Show detailed error messages

### Step 2: Check Streamlit Cloud Secrets

**CRITICAL**: On Streamlit Cloud, environment variables must be set in **Secrets**, not `.env` file!

1. Go to: https://share.streamlit.io/
2. Click on your app
3. Settings → Secrets
4. Add these secrets:

```toml
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "anokyegyasiedward@gmail.com"
SMTP_PASSWORD = "ghiruyggjsyjhqym"
SMTP_FROM = "ScholarAI <anokyegyasiedward@gmail.com>"
```

5. Click "Save"
6. Reboot app

### Step 3: Verify Gmail App Password

The Gmail App Password might have expired or been revoked.

1. Go to: https://myaccount.google.com/apppasswords
2. Sign in with: anokyegyasiedward@gmail.com
3. Generate a new App Password:
   - App: "Mail"
   - Device: "Streamlit Cloud"
4. Copy the 16-character password (no spaces)
5. Update in Streamlit Cloud Secrets
6. Reboot app

### Step 4: Check Gmail Account Status

1. Sign in to Gmail: anokyegyasiedward@gmail.com
2. Check for security alerts
3. Verify "Less secure app access" is not blocking
4. Check "Recent security activity"
5. Ensure account is not suspended

---

## 🚨 COMMON ISSUES & SOLUTIONS

### Issue 1: "SMTP NOT CONFIGURED"
**Cause**: Environment variables not loaded on Streamlit Cloud  
**Solution**: Add secrets to Streamlit Cloud dashboard (see Step 2 above)

### Issue 2: "Authentication Failed"
**Cause**: Invalid or expired Gmail App Password  
**Solution**: Generate new App Password (see Step 3 above)

### Issue 3: "Connection Timeout"
**Cause**: Streamlit Cloud firewall or network issue  
**Solution**: 
- Increased timeout to 15 seconds (already done)
- Try SSL port 465 as fallback (already implemented)
- Contact Streamlit Cloud support if persists

### Issue 4: "Email in Spam Folder"
**Cause**: Gmail spam filter  
**Solution**: 
- Check spam folder
- Add sender to safe list
- Use custom domain (future enhancement)

### Issue 5: "Email Delayed"
**Cause**: Gmail rate limiting or queue  
**Solution**: 
- Wait 2-3 minutes
- Click "Resend Code"
- Use emergency code shown on screen

---

## 🔧 EMERGENCY WORKAROUNDS

### Option 1: Use Emergency Code
When signup fails to send email, the code is now displayed on screen:
```
📝 Your verification code is: 123456
```
User can enter this code on the verification screen.

### Option 2: Manual Verification
Admin can manually verify users:
```bash
cd scholarai
python bypass_verification.py user@email.com
```

### Option 3: Check Database for Code
```bash
cd scholarai
python check_verification_code.py user@email.com
```

### Option 4: Admin Tools
```bash
cd scholarai
python admin_tools.py
# Choose option 2: Verify user
```

---

## 📊 TESTING CHECKLIST

### Local Testing
- [ ] Run `python diagnose_email.py`
- [ ] Verify SMTP connection succeeds
- [ ] Receive test email
- [ ] Check spam folder
- [ ] Try signup with real email
- [ ] Verify OTP received

### Streamlit Cloud Testing
- [ ] Add secrets to dashboard
- [ ] Reboot app
- [ ] Check app logs for SMTP messages
- [ ] Try signup with test email
- [ ] Check if email received
- [ ] Verify emergency code shown if fails
- [ ] Test resend functionality

---

## 📝 STREAMLIT CLOUD CONFIGURATION

### Required Secrets
Go to: App Dashboard → Settings → Secrets

```toml
# AI APIs
GOOGLE_API_KEY = "AIzaSyBYgy2C6uhpe6XbZWYIcVfwgBmnom_aUYY"

# SMTP (CRITICAL - MUST BE SET!)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "anokyegyasiedward@gmail.com"
SMTP_PASSWORD = "ghiruyggjsyjhqym"
SMTP_FROM = "ScholarAI <anokyegyasiedward@gmail.com>"
```

### How to Add Secrets
1. Open your app on Streamlit Cloud
2. Click the hamburger menu (☰)
3. Click "Settings"
4. Click "Secrets" tab
5. Paste the secrets above
6. Click "Save"
7. App will automatically reboot

### Verify Secrets Are Loaded
Check the app logs for:
```
SMTP Server: smtp.gmail.com
SMTP Port: 587
SMTP User: anokyegyasiedward@gmail.com
SMTP Password: ****************
```

If you see "NOT SET", secrets are not loaded correctly.

---

## 🔍 DEBUGGING ON STREAMLIT CLOUD

### View Logs
1. Go to app dashboard
2. Click "Manage app"
3. Click "Logs" tab
4. Look for email sending messages:
   ```
   ============================================================
   SENDING EMAIL
   ============================================================
   To: user@example.com
   Subject: ScholarAI — Verify Your Account
   SMTP Server: smtp.gmail.com
   SMTP Port: 587
   SMTP User: anokyegyasiedward@gmail.com
   SMTP Password: ****************
   ============================================================
   
   Attempting starttls connection to smtp.gmail.com:587...
   Connected via SMTP, starting TLS...
   TLS started successfully
   Logging in as anokyegyasiedward@gmail.com...
   ✅ Login successful
   Sending message...
   ✅ Message sent
   ✅ Email sent to user@example.com via starttls
   ```

### Common Log Errors

**Error**: `SMTP NOT CONFIGURED - User: , Password: NOT SET`
**Fix**: Add secrets to Streamlit Cloud dashboard

**Error**: `Auth failed: (535, b'5.7.8 Username and Password not accepted')`
**Fix**: Generate new Gmail App Password

**Error**: `Connection timeout`
**Fix**: Check Streamlit Cloud network status, try again later

**Error**: `[Errno 111] Connection refused`
**Fix**: Gmail SMTP might be blocked, contact Streamlit support

---

## 🎯 RECOMMENDED SOLUTION

### For Immediate Fix:
1. **Add secrets to Streamlit Cloud** (most likely cause)
2. **Generate new Gmail App Password** (if auth fails)
3. **Show emergency code on screen** (already implemented)

### For Long-term Solution:
1. Use a dedicated email service (SendGrid, Mailgun, AWS SES)
2. Implement email queue with retry logic
3. Add email delivery tracking
4. Set up monitoring and alerts
5. Use custom domain for better deliverability

---

## 📧 ALTERNATIVE EMAIL SERVICES

If Gmail continues to have issues, consider:

### SendGrid (Recommended)
- Free tier: 100 emails/day
- Better deliverability
- Detailed analytics
- Easy setup

```python
# Install: pip install sendgrid
import sendgrid
from sendgrid.helpers.mail import Mail

sg = sendgrid.SendGridAPIClient(api_key=os.getenv('SENDGRID_API_KEY'))
message = Mail(
    from_email='noreply@scholarai.com',
    to_emails=recipient,
    subject=subject,
    html_content=body_html
)
response = sg.send(message)
```

### Mailgun
- Free tier: 5,000 emails/month
- Good for transactional emails
- Simple API

### AWS SES
- Very cheap ($0.10 per 1,000 emails)
- Highly reliable
- Requires AWS account

---

## ✅ VERIFICATION

After applying fixes, verify:

1. **Signup Flow**:
   - Create new account
   - See "Sending verification code..." spinner
   - See success message OR emergency code
   - Check email inbox (and spam)
   - Receive email within 5 seconds

2. **Resend Flow**:
   - Click "Resend Code"
   - See spinner
   - Receive new email
   - Cooldown timer works

3. **Error Handling**:
   - If email fails, emergency code shown
   - Clear error messages displayed
   - User can still verify account

---

## 📞 SUPPORT

If issues persist after trying all solutions:

1. **Check Streamlit Cloud Status**: https://status.streamlit.io/
2. **Contact Streamlit Support**: support@streamlit.io
3. **Check Gmail Status**: https://www.google.com/appsstatus
4. **Use Manual Verification**: `python bypass_verification.py user@email.com`

---

## 🎉 SUCCESS INDICATORS

You'll know it's working when:
- ✅ Logs show "Email sent to user@example.com via starttls"
- ✅ User receives email within 5 seconds
- ✅ No error messages in logs
- ✅ Success message shown in app
- ✅ User can verify account with OTP

---

**Last Updated**: April 15, 2026  
**Status**: Enhanced logging and error handling applied  
**Next Step**: Add secrets to Streamlit Cloud dashboard
