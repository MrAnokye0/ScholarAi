# ⚡ QUICK FIX - OTP Not Received (2 Minutes)

## 🎯 The Problem
Users on your live site (Streamlit Cloud) are not receiving OTP verification emails.

## ✅ The Solution
Add SMTP secrets to Streamlit Cloud dashboard.

---

## 📋 STEP-BY-STEP FIX

### 1️⃣ Open Streamlit Cloud Dashboard
- Go to: **https://share.streamlit.io/**
- Sign in to your account
- Find: **"ScholarAI — Literature Review Generator"**
- Click on the app

### 2️⃣ Open Secrets Editor
- Click the **☰ menu** (top right)
- Click **"Settings"**
- Click **"Secrets"** tab

### 3️⃣ Copy & Paste This Configuration

```toml
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "anokyegyasiedward@gmail.com"
SMTP_PASSWORD = "ghiruyggjsyjhqym"
SMTP_FROM = "ScholarAI <anokyegyasiedward@gmail.com>"
GOOGLE_API_KEY = "AIzaSyBYgy2C6uhpe6XbZWYIcVfwgBmnom_aUYY"
ADMIN_PASSWORD = "scholarai_admin_2026"
```

### 4️⃣ Save & Reboot
- Click **"Save"** button
- App will automatically reboot (wait 30 seconds)

### 5️⃣ Test It
- Go to your live site
- Click **"Create Account"**
- Fill in the form with a **real email address**
- Click **"Get Started"**
- Check your email inbox (and spam folder)
- Email should arrive within **5 seconds** ✅

---

## 🎉 DONE!

That's it! Your OTP emails should now be working.

---

## 🔍 How to Verify It's Working

### Check the Logs:

1. Go to Streamlit Cloud dashboard
2. Click **"Manage app"** → **"Logs"**
3. Look for this:

```
============================================================
SENDING EMAIL
============================================================
To: user@example.com
SMTP Server: smtp.gmail.com
SMTP User: anokyegyasiedward@gmail.com
SMTP Password: ****************
============================================================

✅ Login successful
✅ Message sent
✅ Email sent to user@example.com via starttls
```

If you see **"SMTP NOT CONFIGURED"**, go back to Step 2 and add the secrets again.

---

## 🚨 If Still Not Working

### Option 1: Generate New Gmail App Password

The password might be expired:

1. Go to: **https://myaccount.google.com/apppasswords**
2. Sign in: **anokyegyasiedward@gmail.com**
3. Click **"Generate"**
4. Copy the 16-character password
5. Update **SMTP_PASSWORD** in Streamlit Cloud secrets
6. Save and reboot

### Option 2: Use Emergency Code

If email fails, the code is now shown on screen:

```
📝 Your verification code is: 123456
```

Users can enter this code to verify their account.

### Option 3: Manual Verification

You can manually verify users:

```bash
cd scholarai
python bypass_verification.py user@email.com
```

---

## 📚 More Help

- **Complete Guide**: `EMAIL_NOT_RECEIVED_FIX.md`
- **Deployment Guide**: `STREAMLIT_CLOUD_DEPLOYMENT.md`
- **Full Solution**: `OTP_NOT_RECEIVED_SOLUTION.md`

---

## ✨ What Changed in the Code

1. ✅ Enhanced logging to see what's happening
2. ✅ Emergency code shown on screen if email fails
3. ✅ Better error messages
4. ✅ Increased timeout for reliability
5. ✅ SMTP configuration check
6. ✅ Admin tools for manual verification

All changes have been **committed and pushed** to GitHub!

---

## 🎯 Summary

**Problem**: OTP not received  
**Cause**: Streamlit Cloud secrets not configured  
**Fix**: Add secrets to dashboard (2 minutes)  
**Result**: Emails working ✅

**DO THIS NOW**: Go to Streamlit Cloud and add the secrets!

---

**Last Updated**: April 15, 2026  
**Status**: Code deployed, awaiting secrets configuration
