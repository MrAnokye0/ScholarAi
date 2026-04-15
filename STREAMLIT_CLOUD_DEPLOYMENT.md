# 🚀 Streamlit Cloud Deployment Checklist

## Critical: Email Configuration for Live Site

Your OTP emails are not being received because **Streamlit Cloud requires secrets to be configured in the dashboard**, not just in the `.env` file.

---

## ⚠️ IMMEDIATE ACTION REQUIRED

### Step 1: Add Secrets to Streamlit Cloud

1. **Go to your app dashboard**:
   - Visit: https://share.streamlit.io/
   - Find your app: "ScholarAI — Literature Review Generator"
   - Click on the app

2. **Open Secrets Editor**:
   - Click the hamburger menu (☰) in the top right
   - Click "Settings"
   - Click the "Secrets" tab

3. **Add these secrets** (copy and paste):

```toml
# AI Configuration
GOOGLE_API_KEY = "AIzaSyBYgy2C6uhpe6XbZWYIcVfwgBmnom_aUYY"

# CRITICAL: SMTP Configuration for Email Sending
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "anokyegyasiedward@gmail.com"
SMTP_PASSWORD = "ghiruyggjsyjhqym"
SMTP_FROM = "ScholarAI <anokyegyasiedward@gmail.com>"

# Admin
ADMIN_PASSWORD = "scholarai_admin_2026"
```

4. **Save and Reboot**:
   - Click "Save" button
   - App will automatically reboot
   - Wait 30 seconds for reboot to complete

---

## 🧪 Step 2: Test Email Sending

### Test on Live Site:

1. **Open your live app**:
   - Go to your Streamlit Cloud URL
   - Click "Create Account"

2. **Create a test account**:
   - Username: `testuser123`
   - Email: YOUR_REAL_EMAIL@gmail.com
   - Password: `test1234`
   - Click "Get Started"

3. **Check for success**:
   - You should see: "✅ Verification code sent to your@email.com"
   - Check your email inbox (and spam folder)
   - Email should arrive within 5-10 seconds

4. **If email not received**:
   - Look for emergency code on screen: "📝 Your verification code is: 123456"
   - Use this code to verify
   - Check logs (see below)

---

## 📊 Step 3: Check Logs

### View Streamlit Cloud Logs:

1. Go to app dashboard
2. Click "Manage app"
3. Click "Logs" tab
4. Look for email sending messages

### What to Look For:

**✅ SUCCESS** - You should see:
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

**❌ FAILURE** - If you see:
```
❌ SMTP NOT CONFIGURED - User: , Password: NOT SET
```
**Fix**: Secrets not added correctly. Go back to Step 1.

**❌ AUTH FAILURE** - If you see:
```
❌ Auth failed: (535, b'5.7.8 Username and Password not accepted')
```
**Fix**: Gmail App Password expired. Generate new one (see below).

---

## 🔑 Step 4: Generate New Gmail App Password (If Needed)

If authentication fails, the Gmail App Password might be expired:

1. **Go to Google Account**:
   - Visit: https://myaccount.google.com/apppasswords
   - Sign in with: anokyegyasiedward@gmail.com

2. **Generate New App Password**:
   - Select app: "Mail"
   - Select device: "Streamlit Cloud"
   - Click "Generate"
   - Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

3. **Update Streamlit Cloud Secrets**:
   - Go back to Secrets editor
   - Update `SMTP_PASSWORD` with new password (remove spaces)
   - Save and reboot

4. **Test Again**:
   - Try creating a new account
   - Email should now be sent

---

## 🔍 Troubleshooting

### Issue 1: Secrets Not Loading

**Symptoms**:
- Logs show "SMTP NOT CONFIGURED"
- Environment variables are empty

**Solution**:
1. Double-check secrets are saved in dashboard
2. Ensure no typos in secret names (case-sensitive)
3. Reboot app manually:
   - Settings → Reboot app
4. Clear browser cache and reload

### Issue 2: Gmail Blocking

**Symptoms**:
- Auth fails even with correct password
- "Less secure app" error

**Solution**:
1. Check Gmail security settings
2. Enable 2-factor authentication
3. Generate new App Password
4. Check for security alerts in Gmail

### Issue 3: Emails Going to Spam

**Symptoms**:
- Email sent successfully in logs
- User doesn't see email in inbox

**Solution**:
1. Check spam folder
2. Add sender to safe list
3. Mark as "Not Spam"
4. Future emails will go to inbox

### Issue 4: Timeout Errors

**Symptoms**:
- Connection timeout
- No response from SMTP server

**Solution**:
1. Check Streamlit Cloud status: https://status.streamlit.io/
2. Wait a few minutes and try again
3. Timeout increased to 15 seconds (already done)
4. Contact Streamlit support if persists

---

## ✅ Verification Checklist

After deployment, verify these work:

- [ ] Secrets added to Streamlit Cloud dashboard
- [ ] App rebooted successfully
- [ ] Logs show SMTP configuration loaded
- [ ] Test signup sends email
- [ ] Email received in inbox (or spam)
- [ ] Verification code works
- [ ] Resend code works
- [ ] Password reset sends email
- [ ] Login with verified account works
- [ ] Remember me persists across sessions

---

## 🎯 Expected Behavior

### Signup Flow:
1. User fills signup form
2. Clicks "Get Started"
3. Sees spinner: "Sending verification code... This may take a few seconds."
4. Sees success: "✅ Verification code sent to user@email.com"
5. Sees info: "📧 Check your inbox (and spam folder)"
6. Redirected to verification screen
7. Email arrives within 5-10 seconds
8. User enters 6-digit code
9. Account verified ✅

### If Email Fails:
1. User sees: "⚠️ Email sending failed. Check the logs for details."
2. User sees: "📝 Your verification code is: 123456"
3. User can still verify with emergency code
4. User can click "Resend Code" on verification screen

---

## 📧 Email Delivery Times

- **Local Development**: 1-2 seconds
- **Streamlit Cloud**: 2-5 seconds
- **Gmail Spam Filter**: Up to 30 seconds
- **Gmail Queue**: Up to 2 minutes (rare)

If email not received after 2 minutes:
1. Check spam folder
2. Use emergency code shown on screen
3. Click "Resend Code"
4. Contact admin for manual verification

---

## 🚨 Emergency User Verification

If a user can't receive emails, admin can manually verify:

### Option 1: Get User's Code
```bash
cd scholarai
python get_user_code.py user@email.com
```
Give the code to the user.

### Option 2: Bypass Verification
```bash
cd scholarai
python bypass_verification.py user@email.com
```
User can now login without verification.

### Option 3: Admin Tools
```bash
cd scholarai
python admin_tools.py
# Choose option 2: Verify user
```

---

## 📊 Monitoring

### Check Email Sending Status:

**Daily**:
- Check Streamlit Cloud logs for errors
- Monitor user signups
- Check for failed email attempts

**Weekly**:
- Review Gmail sending limits (500/day)
- Check for spam complaints
- Verify App Password still valid

**Monthly**:
- Review email deliverability
- Check for blocked users
- Update SMTP credentials if needed

---

## 🎉 Success Indicators

You'll know everything is working when:

1. ✅ Secrets loaded in Streamlit Cloud
2. ✅ Logs show successful SMTP connection
3. ✅ Test signup sends email
4. ✅ Email received in inbox
5. ✅ Verification code works
6. ✅ No errors in logs
7. ✅ Users can complete signup flow
8. ✅ Resend functionality works

---

## 📞 Support

If issues persist:

1. **Check this guide**: `EMAIL_NOT_RECEIVED_FIX.md`
2. **Run diagnosis**: `python diagnose_email.py`
3. **Check logs**: Streamlit Cloud dashboard
4. **Test locally**: `streamlit run app.py`
5. **Contact support**: support@streamlit.io

---

## 🔄 Deployment Steps Summary

1. ✅ Add secrets to Streamlit Cloud dashboard
2. ✅ Reboot app
3. ✅ Check logs for SMTP configuration
4. ✅ Test signup with real email
5. ✅ Verify email received
6. ✅ Test resend functionality
7. ✅ Test password reset
8. ✅ Monitor logs for errors

---

**CRITICAL**: The most common issue is **forgetting to add secrets to Streamlit Cloud dashboard**. The `.env` file is NOT used on Streamlit Cloud!

**Next Step**: Go to your Streamlit Cloud dashboard NOW and add the secrets from Step 1.

---

**Last Updated**: April 15, 2026  
**Status**: Ready for deployment  
**Action Required**: Add secrets to Streamlit Cloud dashboard
