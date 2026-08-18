#!/usr/bin/env python3
"""
Test script - Send emails with random FROM addresses
Tests that random email generation is working
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
import random
import json
import string

def generate_random_email(real_email):
    """Generate random FROM email that Gmail will accept"""
    names = ["Support", "Admin", "Service", "Billing", "Update", "Alert", "Notice", 
             "System", "Team", "Sales", "Help", "Info", "Marketing", "Manager", "Assist"]
    display_name = random.choice(names)
    
    # Add random suffix
    chars = string.ascii_lowercase + string.digits
    suffix = ''.join(random.choice(chars) for _ in range(4))
    display_name = f"{display_name}_{suffix}"
    
    # Get the authenticated domain
    if '@' in real_email:
        domain = real_email.split('@')[1]
    else:
        domain = 'gmail.com'
    
    # Return formatted FROM with display name and real domain
    return f"{display_name} <{real_email}>"


def send_random_emails_test(recipient, num_emails=3):
    """Send test emails with random FROM addresses"""
    
    # Load config
    with open('email_boomer_config.json', 'r') as f:
        config = json.load(f)
    
    smtp_config = config['smtp']
    email_config = config['content']
    
    print(f"📧 Random Email Test")
    print(f"{'='*60}")
    print(f"Target: {recipient}")
    print(f"Real Email: {smtp_config['username']}")
    print(f"Randomize FROM: {smtp_config.get('randomize_from', False)}")
    print(f"Emails to Send: {num_emails}")
    print(f"{'='*60}\n")
    
    try:
        # Connect
        print("[1/4] Connecting to Gmail SMTP...")
        context = ssl.create_default_context()
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        server = smtplib.SMTP(
            smtp_config['server'],
            int(smtp_config['port']),
            timeout=90
        )
        server.starttls(context=context)
        print("✅ Connected\n")
        
        # Login
        print("[2/4] Logging in...")
        server.login(smtp_config['username'], smtp_config['password'])
        print("✅ Logged in\n")
        
        # Send multiple emails with random FROM
        print("[3/4] Sending emails with random FROM addresses...\n")
        
        for i in range(num_emails):
            # Build email
            msg = MIMEMultipart('alternative')
            
            # Generate random FROM
            if smtp_config.get('randomize_from', False):
                from_email = generate_random_email(smtp_config['username'])
            else:
                from_email = smtp_config['from_email']
            
            msg['From'] = from_email
            msg['To'] = recipient
            msg['Subject'] = email_config['subject']
            msg['Date'] = formatdate(localtime=True)
            msg['Sender'] = smtp_config['username']  # IMPORTANT for authentication
            msg['Reply-To'] = smtp_config['username']
            msg['Return-Path'] = smtp_config['username']
            msg['X-Mailer'] = 'Python-SMTP/3.0'
            
            # Body
            msg.attach(MIMEText(email_config['body'], 'plain', 'utf-8'))
            
            # Send
            print(f"Email {i+1}:")
            print(f"  FROM: {from_email}")
            print(f"  TO: {recipient}")
            print(f"  Subject: {msg['Subject']}")
            print(f"  Sender (Auth): {msg['Sender']}")
            
            server.send_message(msg)
            print(f"  ✅ Sent\n")
        
        print("[4/4] All emails sent!")
        print(f"{'='*60}\n")
        print("📝 Check target email:")
        print(f"1. Go to: {recipient}")
        print(f"2. Check INBOX (not SPAM)")
        print(f"3. You should see {num_emails} emails with different FROM display names")
        print(f"4. All should be from: {smtp_config['username']}\n")
        
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Login failed - Invalid credentials")
        print(f"   Generate new app-specific password: https://myaccount.google.com/apppasswords")
        return False
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    import sys
    
    # Get recipient from command line or use default
    recipient = sys.argv[1] if len(sys.argv) > 1 else "example@gmail.com"
    num_emails = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    
    print(f"\n🧪 Testing Random Email Generation\n")
    success = send_random_emails_test(recipient, num_emails)
    
    sys.exit(0 if success else 1)
