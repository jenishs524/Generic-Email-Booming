#!/usr/bin/env python3
"""
Test Gmail SMTP with port 465 (direct SSL)
"""
import smtplib
import ssl
import sys

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465  # Direct SSL instead of TLS
EMAIL = "example@gmail.com"
PASSWORD = "eiob efqo nvgj vgpr"

print(f"Testing Gmail SMTP on port 465 (direct SSL)...")
print(f"Server: {SMTP_SERVER}:{SMTP_PORT}")
print(f"Email: {EMAIL}")
print("-" * 60)

try:
    print("[1/3] Creating SSL connection...")
    context = ssl.create_default_context()
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    
    server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context, timeout=90)
    print("✅ SSL connection established")
    
    print("[2/3] Attempting login...")
    server.login(EMAIL, PASSWORD)
    print("✅ Login successful")
    
    print("[3/3] Verifying capabilities...")
    server.noop()
    print("✅ SMTP ready")
    
    print("-" * 60)
    print("✅ SUCCESS! Use port 465 with use_ssl=true")
    server.quit()
    sys.exit(0)
    
except smtplib.SMTPAuthenticationError as e:
    print(f"❌ AUTHENTICATION FAILED: {e}")
    print("\n⚠️  CREDENTIALS ARE INCORRECT!")
    print("\nVerify:")
    print("- Email is correct: example@gmail.com")
    print("- You're using an App-Specific Password (not your Gmail password)")
    print("- If 2FA is disabled, use: https://myaccount.google.com/apppasswords")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
