"""
Quick script to get a user's verification code
Usage: python get_user_code.py email@example.com
"""
import sys
import database as db

if len(sys.argv) < 2:
    print("Usage: python get_user_code.py email@example.com")
    sys.exit(1)

email = sys.argv[1].strip()

print(f"\n{'='*60}")
print(f"GETTING VERIFICATION CODE FOR: {email}")
print(f"{'='*60}\n")

user = db.get_user_by_email(email)

if not user:
    print(f"❌ No user found with email: {email}")
    sys.exit(1)

print(f"✅ User found!")
print(f"\nUsername: {user['username']}")
print(f"Email: {user['email']}")
print(f"Verified: {'✅ Yes' if user['is_verified'] else '❌ No'}")
print(f"Tier: {user.get('tier', 'free')}")
print(f"\n{'='*60}")
print(f"VERIFICATION CODE: {user.get('verification_code', 'NOT SET')}")
print(f"{'='*60}\n")

if user['is_verified']:
    print("ℹ️  User is already verified. No code needed.")
else:
    print(f"📝 Give this code to the user to verify their account.")
    print(f"   Or run: python bypass_verification.py {email}")

print()
