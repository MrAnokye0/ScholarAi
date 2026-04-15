# OTP Verification Fix Guide

## Problem: OTP not working on live server

### What was fixed:

1. **Improved OTP validation** - Better code comparison with whitespace handling
2. **Development mode** - Shows OTP code on screen when SMTP not configured
3. **Bypass tools** - Scripts to manually verify users without OTP
4. **Debug tools** - Check what code is stored in database

## Solutions for Live Server

### Option 1: Bypass Verification (Quickest)

If users can't verify because they're not receiving emails:

```bash
cd scholarai
python bypass_verification.py user@example.com
```

This will verify the account immediately without needing the OTP code.

### Option 2: Check What Code is Stored

To see what verification code is in the database:

```bash
python check_verification_code.py user@example.com
```

This shows:
- The actual code stored
- Whether user is verified
- User details

### Option 3: Configure SMTP Properly

The real fix is to configure email sending. In your `.env` file on live server:

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=ScholarAI <your-email@gmail.com>
```

**For Gmail:**
1. Go to https://myaccount.google.com/apppasswords
2. Generate an App Password
3. Use that as `SMTP_PASSWORD`

### Option 4: Development Mode (Automatic)

If SMTP is not configured, the app now automatically shows the OTP code on screen!

This means:
- User signs up
- Instead of waiting for email, they see the code immediately
- They can copy and paste it to verify

## Testing on Live Server

### Test 1: Check if SMTP is configured
```bash
cd scholarai
python -c "import mailer; print('SMTP Configured:', mailer.is_smtp_configured())"
```

### Test 2: Create test account
1. Go to your live app
2. Create account with test email
3. If SMTP not configured, you'll see the code on screen
4. Enter the code to verify

### Test 3: Check database
```bash
python admin_tools.py list
```

Shows all users and their verification status.

## Common Issues & Solutions

### Issue 1: "Invalid code" error

**Cause**: Code doesn't match what's in database

**Solution**:
```bash
# Check what code is stored
python check_verification_code.py user@example.com

# If needed, bypass verification
python bypass_verification.py user@example.com
```

### Issue 2: Email not received

**Cause**: SMTP not configured or wrong credentials

**Solution**:
1. Check SMTP settings in `.env`
2. Test email: `python email_test_simple.py`
3. Or bypass: `python bypass_verification.py user@example.com`

### Issue 3: Code expired

**Cause**: User waited too long

**Solution**:
- User clicks "Resend Code" in app
- Or manually verify: `python bypass_verification.py user@example.com`

### Issue 4: User can't access verification page

**Cause**: Session lost or page refresh

**Solution**:
```bash
# Just verify them directly
python bypass_verification.py user@example.com
```

## For Streamlit Cloud

If you're on Streamlit Cloud and can't run scripts:

### Method 1: Use Streamlit Cloud Terminal
Some plans have terminal access in the dashboard.

### Method 2: Add Admin Page
Create a password-protected admin page in your app to verify users.

### Method 3: Development Mode
Since SMTP might not be configured, the app will show codes on screen automatically!

### Method 4: Database Access
1. Download database from Streamlit Cloud
2. Run scripts locally
3. Upload modified database

## Quick Commands Reference

| Task | Command |
|------|---------|
| Bypass verification | `python bypass_verification.py <email>` |
| Check stored code | `python check_verification_code.py <email>` |
| List all users | `python admin_tools.py list` |
| Check user status | `python check_login_issue.py <email>` |
| Force verify | `python quick_verify_user.py <email>` |

## What Happens Now

### With SMTP Configured:
1. User signs up
2. Receives email with 6-digit code
3. Enters code to verify
4. Account activated

### Without SMTP (Development Mode):
1. User signs up
2. **Code shown on screen immediately** 🎉
3. User copies and enters code
4. Account activated

## Testing the Fix

1. **Local test**:
   ```bash
   cd scholarai
   streamlit run app.py
   ```
   - Create account
   - You should see code on screen (if SMTP not configured)
   - Or receive email (if SMTP configured)

2. **Live test**:
   - Deploy to live server
   - Create test account
   - Check if code appears or email received
   - Verify account

## Prevention

1. **Always configure SMTP** before going live
2. **Test email sending** in development
3. **Keep backup admin access** to verify users manually
4. **Monitor verification rates** - if low, check SMTP

## Emergency Fix

If users are stuck and can't verify:

```bash
# SSH into live server
cd scholarai

# Verify all unverified users
python admin_tools.py list | grep "No" | awk '{print $3}' | while read email; do
    python bypass_verification.py "$email"
done
```

Or verify specific users:
```bash
python bypass_verification.py user1@example.com
python bypass_verification.py user2@example.com
```

## Summary

The OTP system now has multiple fallbacks:
1. ✅ Email delivery (if SMTP configured)
2. ✅ On-screen display (if SMTP not configured)
3. ✅ Manual bypass (admin tools)
4. ✅ Database inspection (debug tools)

Users should never be stuck unable to verify!
