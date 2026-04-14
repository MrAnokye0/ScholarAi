"""
Test password reset email functionality
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from mailer import send_password_reset, generate_6_digit_code

def main():
    print("Testing Password Reset Email...")
    
    # Generate a test code
    test_code = generate_6_digit_code()
    print(f"Generated reset code: {test_code}")
    
    # Send password reset email
    success = send_password_reset("anokyegyasiedward@gmail.com", test_code)
    
    if success:
        print("SUCCESS: Password reset email sent!")
        print("Check your inbox at anokyegyasiedward@gmail.com")
        print(f"The reset code in the email should be: {test_code}")
    else:
        print("FAILED: Could not send password reset email")
        print("Check the terminal output for detailed error messages")

if __name__ == "__main__":
    main()
