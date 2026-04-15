"""
Quick script to verify a user account
Run this on your live server to manually verify users who can't login
"""

import database as db
import sys

def main():
    if len(sys.argv) < 2:
        print("\n🎓 Quick User Verification Tool")
        print("\nUsage: python quick_verify_user.py <email>")
        print("\nExample: python quick_verify_user.py eedmund96@gmail.com\n")
        return
    
    email = sys.argv[1]
    
    # Check if user exists
    user = db.get_user_by_email(email)
    
    if not user:
        print(f"\n❌ User not found: {email}")
        print("\nMake sure the email is correct.\n")
        return
    
    print(f"\n📧 Found user: {user['username']} ({email})")
    print(f"Current status: {'✅ Verified' if user['is_verified'] else '❌ Not Verified'}")
    print(f"Tier: {user.get('tier', 'free')}")
    
    if user['is_verified']:
        print("\n✅ User is already verified!")
        print("\nIf they still can't login, the password might be wrong.")
        print("Try resetting their password with:")
        print(f"  python admin_tools.py reset {email} NewPassword123\n")
        return
    
    # Verify the user
    db.update_user_verification(user['username'], True)
    print(f"\n✅ SUCCESS! User {email} has been verified!")
    print("\nThey can now login with their password.\n")

if __name__ == "__main__":
    main()
