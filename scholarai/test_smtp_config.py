"""
Quick test to check if SMTP is configured correctly
"""

import mailer

print("\n🔍 Testing SMTP Configuration\n")
print("=" * 60)

config = mailer.get_smtp_config()

print(f"\nSMTP Server: {config['server']}")
print(f"SMTP Port: {config['port']}")
print(f"SMTP User: {config['user']}")
print(f"SMTP Password: {'*' * len(config['password']) if config['password'] else '(not set)'}")
print(f"SMTP From: {config['from']}")

print(f"\n{'✅' if mailer.is_smtp_configured() else '❌'} SMTP Configured: {mailer.is_smtp_configured()}")

if mailer.is_smtp_configured():
    print("\n✅ SMTP is properly configured!")
    print("\nTesting connection...")
    result = mailer.test_email_config()
    
    if result['success']:
        print(f"✅ {result['message']}")
        print(f"   Server: {result['smtp_server']}")
        print(f"   Port: {result['smtp_port']}")
        print(f"   User: {result['smtp_user']}")
    else:
        print(f"❌ {result['error']}")
        print(f"   Details: {result['details']}")
        if 'help' in result:
            print(f"   Help: {result['help']}")
else:
    print("\n❌ SMTP is NOT configured!")
    print("\nPlease set the following in your .env file:")
    print("  SMTP_SERVER=smtp.gmail.com")
    print("  SMTP_PORT=587")
    print("  SMTP_USER=your-email@gmail.com")
    print("  SMTP_PASSWORD=your-app-password")
    print("  SMTP_FROM=ScholarAI <your-email@gmail.com>")
    print("\nFor Gmail App Password: https://myaccount.google.com/apppasswords")

print("\n" + "=" * 60 + "\n")
