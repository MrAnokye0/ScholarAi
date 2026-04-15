"""
Check what verification code is stored for a user
Useful for debugging OTP issues on live server
"""

import database as db
import sys

def check_verification_code(email: str):
    print(f"\n🔍 Checking verification code for: {email}")
    print("=" * 60)
    
    user = db.get_user_by_email(email)
    
    if not user:
        print(f"\n❌ User not found: {email}\n")
        return
    
    print(f"\n✅ User found:")
    print(f"   Username: {user['username']}")
    print(f"   Email: {user['email']}")
    print(f"   Verified: {'Yes' if user['is_verified'] else 'No'}")
    
    code = user.get('verification_code', '')
    
    if code:
        print(f"\n📧 Verification Code: {code}")
        print(f"   Length: {len(code)} characters")
        print(f"   Type: {type(code)}")
        
        if user['is_verified']:
            print(f"\n⚠️  Note: User is already verified, code may be old")
        else:
            print(f"\n💡 User can verify with this code")
            print(f"   Or run: python quick_verify_user.py {email}")
    else:
        print(f"\n❌ No verification code found")
        print(f"\n💡 Generate a new code:")
        print(f"   1. User clicks 'Resend Code' in the app")
        print(f"   2. Or manually verify: python quick_verify_user.py {email}")
    
    print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n🔍 Verification Code Checker")
        print("\nUsage: python check_verification_code.py <email>")
        print("\nExample: python check_verification_code.py user@example.com\n")
        sys.exit(1)
    
    email = sys.argv[1]
    check_verification_code(email)
