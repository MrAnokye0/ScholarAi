# Login Issues Troubleshooting Guide

## Problem: "Invalid login credentials" on live server but works locally

### Possible Causes:
1. **User account not verified** - User created account but didn't verify email
2. **Different database** - Live server has different database than local
3. **Password hash mismatch** - Old users might have different password hashes

### Solutions:

## Option 1: Use Admin Tools (Recommended)

SSH into your live server and run these commands:

```bash
cd scholarai
python admin_tools.py list
```

This will show all users and their verification status.

### To verify a user manually:
```bash
python admin_tools.py verify user@example.com
```

### To check user info:
```bash
python admin_tools.py info user@example.com
```

### To reset a user's password:
```bash
python admin_tools.py reset user@example.com newpassword123
```

## Option 2: Direct Database Access

If you have access to the SQLite database on the live server:

```bash
cd scholarai/data
sqlite3 scholarai.db

-- Check user status
SELECT username, email, is_verified, tier FROM users;

-- Manually verify a user
UPDATE users SET is_verified = 1 WHERE email = 'user@example.com';

-- Check password hash
SELECT username, email, password_hash FROM users WHERE email = 'user@example.com';
```

## Option 3: Have User Re-register

If the user can't login:
1. Ask them to try "Forgot Password?" to reset their password
2. Or have them create a new account with a different email
3. Use admin tools to verify their account immediately

## Testing on Live Server

1. Create a test account on live server
2. Check if verification email is sent (check SMTP settings in .env)
3. If email not sent, manually verify using admin tools
4. Try logging in

## Common Issues:

### Email not being sent
- Check `.env` file has correct SMTP settings:
  ```
  SMTP_SERVER=smtp.gmail.com
  SMTP_PORT=587
  SMTP_USER=your-email@gmail.com
  SMTP_PASSWORD=your-app-password
  SMTP_FROM=ScholarAI <your-email@gmail.com>
  ```
- For Gmail, you need an App Password: https://myaccount.google.com/apppasswords

### Database file permissions
```bash
chmod 664 scholarai/data/scholarai.db
```

### Check logs on Streamlit Cloud
- Go to your Streamlit Cloud dashboard
- Check the logs for any error messages
- Look for SMTP errors or database errors

## Quick Fix for Existing Users

If you have users who can't login on live server:

```bash
# SSH into live server
cd scholarai

# List all users
python admin_tools.py list

# Verify all unverified users
python admin_tools.py verify user1@example.com
python admin_tools.py verify user2@example.com

# Or reset their passwords
python admin_tools.py reset user@example.com TempPassword123
```

Then tell users to:
1. Login with the temporary password
2. Change their password in settings

## Prevention

To prevent this in the future:
1. Ensure SMTP is properly configured before deploying
2. Test email sending on live server
3. Consider adding email verification bypass for testing
4. Keep local and live databases in sync during development
