#!/usr/bin/env python3
"""
Interactive Gmail credentials tester
Helps diagnose and fix SMTP authentication issues
"""
import smtplib
import ssl
import sys
import getpass

def test_credentials(email, password, port=465):
    """Test Gmail SMTP credentials"""
    print(f"\n{'='*60}")
    print(f"Testing: {email} on port {port}")
    print(f"{'='*60}\n")
    
    try:
        context = ssl.create_default_context()
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        if port == 465:
            print("[1/3] Connecting with direct SSL (port 465)...")
            server = smtplib.SMTP_SSL("smtp.gmail.com", port, context=context, timeout=90)
        else:
            print("[1/3] Connecting with STARTTLS (port 587)...")
            server = smtplib.SMTP("smtp.gmail.com", port, timeout=90)
            server.starttls(context=context)
        
        print("✅ Connection successful")
        
        print(f"[2/3] Attempting login with {email}...")
        server.login(email, password)
        print("✅ Login successful")
        
        print("[3/3] Testing SMTP capabilities...")
        server.noop()
        print("✅ SMTP ready")
        
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ AUTHENTICATION FAILED")
        print(f"   Error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ CONNECTION FAILED")
        print(f"   Error: {type(e).__name__}: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("Gmail SMTP Credentials Tester")
    print("="*60)
    
    email = input("\n📧 Enter Gmail address (e.g., your@gmail.com): ").strip()
    if not email or '@' not in email:
        print("❌ Invalid email address")
        return
    
    print("\n🔑 Enter App-Specific Password (16 characters with spaces)")
    print("   Get it from: https://myaccount.google.com/apppasswords")
    password = getpass.getpass("   Password: ")
    
    if len(password.replace(' ', '')) < 15:
        print("⚠️  Warning: Password seems too short (should be ~16 chars without spaces)")
    
    # Test both ports
    success_465 = test_credentials(email, password, 465)
    success_587 = test_credentials(email, password, 587)
    
    print(f"\n{'='*60}")
    print("Summary:")
    print(f"  Port 465 (SSL):      {'✅ WORKS' if success_465 else '❌ FAILED'}")
    print(f"  Port 587 (STARTTLS): {'✅ WORKS' if success_587 else '❌ FAILED'}")
    print(f"{'='*60}\n")
    
    if success_465 or success_587:
        working_port = 465 if success_465 else 587
        print(f"✅ SUCCESS! Use port {working_port}\n")
        
        print("Update your config file with:")
        print(f"  'port': {working_port},")
        print(f"  'use_ssl': {'true' if working_port == 465 else 'false'},")
        print(f"  'use_tls': {'false' if working_port == 465 else 'true'},")
        print(f"  'username': '{email}',")
        print(f"  'password': '{password}',\n")
        
        # Optionally save to config
        save = input("💾 Save to config file? (y/n): ").strip().lower()
        if save == 'y':
            import json
            config_file = 'email_boomer_config.json'
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                config['smtp']['port'] = working_port
                config['smtp']['use_ssl'] = working_port == 465
                config['smtp']['use_tls'] = working_port == 587
                config['smtp']['username'] = email
                config['smtp']['password'] = password
                
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=4)
                print(f"✅ Saved to {config_file}")
            except Exception as e:
                print(f"❌ Failed to save: {e}")
    else:
        print("❌ FAILED - Credentials not accepted\n")
        print("Try these solutions:")
        print("1. Generate a NEW App-Specific Password:")
        print("   https://myaccount.google.com/apppasswords")
        print("2. Make sure 2FA is enabled: https://myaccount.google.com/security")
        print("3. Check if your account is locked:")
        print("   https://accounts.google.com/signin/recovery")
        print("4. If it still fails, try a different Gmail account\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        sys.exit(0)
