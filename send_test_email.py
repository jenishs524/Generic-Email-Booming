#!/usr/bin/env python3
"""
Safe test script - Send just 1 email to test delivery
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
import random
import json

def send_test_email(recipient):
    """Send a single test email with proper headers"""
    
    # Load config
    with open('email_boomer_config.json', 'r') as f:
        config = json.load(f)
    
    smtp_config = config['smtp']
    email_config = config['content']
    
    print(f"📧 Test Email Configuration")
    print(f"{'='*60}")
    print(f"From:      {smtp_config['username']}")
    print(f"To:        {recipient}")
    print(f"Server:    {smtp_config['server']}:{smtp_config['port']}")
    print(f"SSL:       {smtp_config['use_ssl']}")
    print(f"Subject:   {email_config['subject']}")
    print(f"{'='*60}\n")
    
    try:
        # Connect
        print("[1/4] Connecting to Gmail SMTP...")
        context = ssl.create_default_context()
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        if smtp_config['use_ssl']:
            server = smtplib.SMTP_SSL(
                smtp_config['server'],
                int(smtp_config['port']),
                context=context,
                timeout=90
            )
        else:
            server = smtplib.SMTP(
                smtp_config['server'],
                int(smtp_config['port']),
                timeout=90
            )
            if smtp_config['use_tls']:
                server.starttls(context=context)
        
        print("✅ Connected")
        
        # Login
        print("[2/4] Logging in...")
        server.login(smtp_config['username'], smtp_config['password'])
        print("✅ Logged in")
        
        # Build email with proper headers
        print("[3/4] Building email...")
        msg = MIMEMultipart('alternative')
        msg['From'] = smtp_config['from_email']
        msg['To'] = recipient
        msg['Subject'] = email_config['subject']
        
        # Proper headers
        msg['Message-ID'] = f"<test.{random.randint(100000, 999999)}@{smtp_config['from_email'].split('@')[1]}>"
        msg['Date'] = formatdate(localtime=True)
        msg['X-Mailer'] = 'Python-SMTP/3.0'
        msg['Reply-To'] = smtp_config['from_email']
        msg['Return-Path'] = smtp_config['from_email']
        msg['X-Priority'] = '3'
        msg['List-Unsubscribe'] = f"<mailto:{smtp_config['from_email']}?subject=Unsubscribe>"
        
        # Body
        body_text = email_config['body']
        msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
        
        print("✅ Email built with proper headers")
        
        # Send
        print("[4/4] Sending email...")
        server.send_message(msg)
        print("✅ Email sent successfully!\n")
        
        # Check if recipient received it
        print("📝 Next Steps:")
        print("1. Check if email arrived at: " + recipient)
        print("2. Check INBOX (not SPAM)")
        print("3. If in SPAM - Gmail spam filter is still blocking")
        print("4. If in INBOX - configuration is working!\n")
        
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ Login failed - Invalid credentials")
        print("   Generate new app-specific password: https://myaccount.google.com/apppasswords")
        return False
        
    except smtplib.SMTPRecipientsRefused as e:
        print(f"❌ Email BLOCKED by Gmail: {e}")
        print("   This is Gmail's spam filter rejecting the email")
        print("   Solutions:")
        print("   1. Reduce sending frequency (delay: 30+ seconds)")
        print("   2. Use multiple Gmail accounts (distribute load)")
        print("   3. Migrate to SendGrid/AWS SES for bulk sending")
        return False
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    import sys
    
    # Test email
    test_email = "example@gmail.com"  # Your test recipient
    
    print("\n🧪 Gmail Email Delivery Test\n")
    
    if len(sys.argv) > 1:
        test_email = sys.argv[1]
        print(f"Using recipient: {test_email}\n")
    
    success = send_test_email(test_email)
    sys.exit(0 if success else 1)
