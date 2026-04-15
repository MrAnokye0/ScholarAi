"""
Bypass verification for testing on live server
This will verify the user account without needing the OTP code
"""

import database as db
import sys

def bypass_verification(email: str):
    print(f"\n🔓 Bypassing verification for: {email}")
    print("=" * 60)
    
    user = db.get_user_by_email(email)
    
    if not user:
        print(f"\n❌ User not found: {email}")
        print(f"\nMake sure the user has created an account first.\n")
        return
    
    if user['is_verified']:
        print(f"\n✅ User is already verified!")
        print(f"\nIf they still can't login, check password with:")
        print(f"  python check_login_issue.py {email}\n")
        return
    
    print(f"\n📧 User: {user['username']}")
    print(f"   Email: {user['email']}")
    print(f"   Current status: Not verified")
    
    # Verify the user
    db.update_user_verification(user['username'], True)
    
    print(f"\n✅ SUCCESS! User {email} has been verified!")
    print(f"\nThey can now login with their password.")
    print(f"No OTP code needed.\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n🔓 Verification Bypass Tool")
        print("\nThis tool verifies a user account without needing the OTP code.")
        print("Useful when OTP emails aren't being delivered on live server.")
        print("\nUsage: python bypass_verification.py <email>")
        print("\nExample: python bypass_verification.py user@example.com\n")
        sys.exit(1)
    
    email = sys.argv[1]
    
    # Confirm action
    print(f"\n⚠️  You are about to verify: {email}")
    confirm = input("Continue? (yes/no): ").strip().lower()
    
    if confirm in ['yes', 'y']:
        bypass_verification(email)
    else:
        print("\n❌ Cancelled.\n")
