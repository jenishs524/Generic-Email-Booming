# Gmail SMTP Setup Guide

## ❌ Problem
Your Gmail credentials are being rejected by the SMTP server. Connection closes immediately during login.

## ✅ Solution: Generate Gmail App Password

### Step 1: Enable 2-Factor Authentication (if not already enabled)
1. Go to: https://myaccount.google.com/security
2. Click "2-Step Verification" and follow the prompts
3. You should receive a verification code via phone/authenticator app

### Step 2: Generate App-Specific Password
1. Go to: https://myaccount.google.com/apppasswords
   - (Make sure you're signed in as: eexample@gmail.com)
2. Select:
   - App: **Mail**
   - Device: **Windows/Linux/Other (custom name)**
3. Click **Generate**
4. Gmail will show a 16-character password in this format: `xxxx xxxx xxxx xxxx`
5. **Copy this password** (including spaces)

### Step 3: Update Configuration
Replace the password in `/home/email_boomer_config.json`:

```json
{
    "smtp": {
        "server": "smtp.gmail.com",
        "port": 465,
        "use_ssl": true,
        "use_tls": false,
        "username": "example@gmail.com",
        "password": "YOUR_16_CHARACTER_APP_PASSWORD_HERE",
        "from_email": "example@gmail.com",
        "timeout": 90
    },
    ...
}
```

### Step 4: Test Connection
Run this command to verify it works:
```bash
cd "/home/"
python3 test_smtp_465.py 
```

## Alternative: If 2FA Cannot Be Enabled
If you cannot enable 2FA (e.g., work account):

1. Go to: https://myaccount.google.com/lesssecureapps
2. Toggle **"Allow less secure apps"** to ON
3. Use your actual Gmail password in the config
4. Update port to 587 and set:
   - `use_ssl`: false
   - `use_tls`: true

## Troubleshooting

**Still getting "Connection unexpectedly closed"?**
- ✓ Clear cache: `pip install --upgrade pip setuptools`
- ✓ Check if Gmail account is locked: https://accounts.google.com/signin/recovery
- ✓ Try a different Gmail account
- ✓ Check if your IP/location is being blocked by Gmail

## For Bulk Accounts (Email Bombing)
The app also supports multiple SMTP accounts in "bulk_accounts" format:
```
smtp.gmail.com:465:email1@gmail.com:password1:email1@gmail.com
smtp.gmail.com:465:email2@gmail.com:password2:email2@gmail.com
smtp.gmail.com:465:email3@gmail.com:password3:email3@gmail.com
```

Add this to your config.json under:
```json
"smtp": {
    "bulk_accounts": "server:port:user:pass:from_email\nserver:port:user:pass:from_email",
    "use_ssl": true,
    "use_tls": false,
    "timeout": 90,
    ...
}
```
