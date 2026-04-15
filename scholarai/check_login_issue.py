"""
Diagnostic script to check why login is failing
Run this with the email that's having login issues
"""

import database as db
import sys

def check_login_issue(email_or_username: str, password: str = None):
    print("\n🔍 Checking login issue for:", email_or_username)
    print("=" * 60)
    
    # Check if user exists by email
    user_by_email = db.get_user_by_email(email_or_username)
    
    # Check if user exists by username
    user_info = db.debug_user_info(email_or_username)
    
    if not user_by_email and not user_info:
        print("\n❌ ISSUE FOUND: User does not exist")
        print(f"   Email/Username '{email_or_username}' not found in database")
        print("\n💡 SOLUTION:")
        print("   - User needs to create an account")
        print("   - Or check if they used a different email\n")
        return
    
    user = user_by_email or user_info
    
    print(f"\n✅ User found in database")
    print(f"   Username: {user['username']}")
    print(f"   Email: {user['email']}")
    print(f"   Account created: {user.get('created_at', 'Unknown')}")
    
    # Check verification status
    if not user.get('is_verified'):
        print(f"\n❌ ISSUE FOUND: Account not verified")
        print(f"   User needs to verify their email")
        print("\n💡 SOLUTION:")
        print(f"   Run: python quick_verify_user.py {user['email']}")
        print(f"   Or: python admin_tools.py verify {user['email']}\n")
        return
    
    print(f"\n✅ Account is verified")
    
    # Check tier
    print(f"   Tier: {user.get('tier', 'free')}")
    
    # If password provided, test it
    if password:
        print(f"\n🔐 Testing password...")
        test_user = db.verify_user(email_or_username, password)
        if test_user:
            print(f"✅ Password is correct!")
            print(f"\n🎉 Login should work! If it doesn't, try:")
            print(f"   1. Clear browser cache")
            print(f"   2. Try incognito/private mode")
            print(f"   3. Check if SMTP is configured for password reset\n")
        else:
            print(f"❌ Password is incorrect")
            print(f"\n💡 SOLUTION:")
            print(f"   Reset password with:")
            print(f"   python admin_tools.py reset {user['email']} NewPassword123\n")
    else:
        print(f"\n💡 To test password, run:")
        print(f"   python check_login_issue.py {email_or_username} <password>\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n🔍 Login Issue Diagnostic Tool")
        print("\nUsage:")
        print("  python check_login_issue.py <email>")
        print("  python check_login_issue.py <email> <password>")
        print("\nExamples:")
        print("  python check_login_issue.py eedmund96@gmail.com")
        print("  python check_login_issue.py eedmund96@gmail.com mypassword123\n")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2] if len(sys.argv) > 2 else None
    
    check_login_issue(email, password)
