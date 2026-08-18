#!/usr/bin/env python3
"""
Diagnostic script to test Gmail SMTP connection
"""
import smtplib
import ssl
import sys

# Your Gmail credentials from config
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL = "example@gmail.com"
PASSWORD = "app password"  # App-specific password

print(f"Testing Gmail SMTP connection...")
print(f"Server: {SMTP_SERVER}:{SMTP_PORT}")
print(f"Email: {EMAIL}")
print(f"Password length: {len(PASSWORD)}")
print("-" * 60)

try:
    # Step 1: Create connection
    print("[1/4] Creating SMTP connection...")
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=90)
    print("✅ Connection established")
    
    # Step 2: Enable TLS
    print("[2/4] Enabling TLS...")
    context = ssl.create_default_context()
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    server.starttls(context=context)
    print("✅ TLS enabled")
    
    # Step 3: Login
    print("[3/4] Attempting login...")
    server.login(EMAIL, PASSWORD)
    print("✅ Login successful")
    
    # Step 4: Test send (don't actually send)
    print("[4/4] Verifying SMTP capabilities...")
    server.noop()
    print("✅ SMTP ready")
    
    print("-" * 60)
    print("✅ ALL TESTS PASSED - Your configuration is correct!")
    server.quit()
    sys.exit(0)
    
except smtplib.SMTPAuthenticationError as e:
    print(f"❌ AUTHENTICATION FAILED: {e}")
    print("\nPossible solutions:")
    print("1. Check if you're using an App-Specific Password (not your regular password)")
    print("2. Enable 2-Factor Authentication and generate a new App Password")
    print("3. Ensure 'Less secure app access' is enabled in Gmail settings")
    print("4. Check that the password is exactly correct (no extra spaces)")
    sys.exit(1)
    
except smtplib.SMTPException as e:
    print(f"❌ SMTP ERROR: {e}")
    print("\nThis is a Gmail server issue. Try:")
    print("1. Verify your internet connection")
    print("2. Check Gmail's status page for outages")
    print("3. Try port 465 with SSL instead of 587 with TLS")
    sys.exit(1)
    
except ssl.SSLError as e:
    print(f"❌ SSL/TLS ERROR: {e}")
    print("\nTry:")
    print("1. Disable SSL verification (for testing only):")
    print('   context.check_hostname = False')
    print('   context.verify_mode = ssl.CERT_NONE')
    sys.exit(1)
    
except TimeoutError as e:
    print(f"❌ CONNECTION TIMEOUT: {e}")
    print("\nCheck:")
    print("1. Your internet connection")
    print("2. Firewall settings")
    print("3. Gmail server status")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ UNEXPECTED ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
