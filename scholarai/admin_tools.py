"""
Admin Tools for ScholarAI
Quick utilities to manage users on live server
"""

import database as db
import sys

def show_user_info(email_or_username: str):
    """Display user information"""
    user = db.debug_user_info(email_or_username)
    if user:
        print("\n=== User Information ===")
        print(f"ID: {user['id']}")
        print(f"Username: {user['username']}")
        print(f"Email: {user['email']}")
        print(f"Verified: {'Yes' if user['is_verified'] else 'No'}")
        print(f"Tier: {user['tier']}")
        print(f"Created: {user['created_at']}")
        print("========================\n")
    else:
        print(f"❌ User not found: {email_or_username}\n")

def verify_user(email_or_username: str):
    """Force verify a user account"""
    if db.force_verify_user(email_or_username):
        print(f"✅ User {email_or_username} has been verified!\n")
    else:
        print(f"❌ User not found: {email_or_username}\n")

def reset_user_password(email: str, new_password: str):
    """Reset a user's password"""
    user = db.get_user_by_email(email)
    if user:
        db.update_password(email, new_password)
        print(f"✅ Password updated for {email}\n")
        print(f"New password: {new_password}\n")
    else:
        print(f"❌ User not found: {email}\n")

def list_all_users():
    """List all users in the database"""
    import sqlite3
    conn = db.get_conn()
    cursor = conn.execute("""
        SELECT id, username, email, is_verified, tier, created_at 
        FROM users 
        ORDER BY created_at DESC
    """)
    users = cursor.fetchall()
    
    if users:
        print("\n=== All Users ===")
        print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Verified':<10} {'Tier':<10}")
        print("-" * 85)
        for user in users:
            verified = "Yes" if user[3] else "No"
            print(f"{user[0]:<5} {user[1]:<20} {user[2]:<30} {verified:<10} {user[4]:<10}")
        print(f"\nTotal users: {len(users)}\n")
    else:
        print("No users found.\n")
    
    conn.close()

if __name__ == "__main__":
    print("\n🎓 ScholarAI Admin Tools\n")
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python admin_tools.py list                          - List all users")
        print("  python admin_tools.py info <email/username>         - Show user info")
        print("  python admin_tools.py verify <email/username>       - Verify user account")
        print("  python admin_tools.py reset <email> <new_password>  - Reset password")
        print()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_all_users()
    elif command == "info" and len(sys.argv) >= 3:
        show_user_info(sys.argv[2])
    elif command == "verify" and len(sys.argv) >= 3:
        verify_user(sys.argv[2])
    elif command == "reset" and len(sys.argv) >= 4:
        reset_user_password(sys.argv[2], sys.argv[3])
    else:
        print("❌ Invalid command or missing arguments\n")
        sys.exit(1)
