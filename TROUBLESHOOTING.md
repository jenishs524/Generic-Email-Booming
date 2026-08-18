# 🔧 Email Bombing - Troubleshooting Guide

## ❌ Current Issue: "Connection unexpectedly closed"

Your Gmail password **`eiob efqo nvgj vgpr`** is **invalid or expired** and is being rejected by Gmail's SMTP server.

---

## ✅ SOLUTION: Get a New Gmail App-Specific Password

### Why the Current Password Doesn't Work:
- It may have expired (Gmail app passwords expire after a period)
- It could be invalid or incorrectly formatted
- Your Gmail account might have security restrictions
- The password may be for a different email account

### Step-by-Step Fix:

#### 1️⃣ Generate a New App-Specific Password

**Go to:** https://myaccount.google.com/apppasswords

Make sure you're signed in as: **example@gmail.com**

If you don't see "App passwords" option:
- ✅ Enable 2-Factor Authentication first: https://myaccount.google.com/security
- Then return to the app passwords page

#### 2️⃣ Create App Password

1. Click the dropdown and select:
   - **Select app:** Mail
   - **Select device:** Windows Computer (or Other - Linux/Server)

2. Click **"Generate"**

3. Gmail will display a **16-character password** in this format:
   ```
   xxxx xxxx xxxx xxxx
   ```

4. **Copy it** (including the spaces)

#### 3️⃣ Test Your New Password

Run the interactive tester:
```bash
cd "/home"
python3 test_credentials.py
```

When prompted:
- Enter your email: `example@gmail.com`
- Paste your new app password

#### 4️⃣ If Test Passes ✅

The script will show you what to update in the config file.

#### 5️⃣ Run Email Campaign

```bash
python3 app.py
# OR run from web UI at http://localhost:5000
```

---

## 🆘 Still Failing After Steps Above?

### Option A: Check Gmail Security Settings
1. Go to: https://accounts.google.com/signin/recovery
2. Verify your account isn't locked
3. Complete any security verification

### Option B: Enable "Less Secure Apps"
(Only use if Option A doesn't work)

1. Go to: https://myaccount.google.com/lesssecureapps
2. Toggle to **"Allow less secure apps"**
3. Use your **actual Gmail password** (not app password) in config
4. In `email_boomer_config.json`:
   ```json
   "port": 587,
   "use_ssl": false,
   "use_tls": true
   ```

### Option C: Try a Different Gmail Account
If the account has persistent issues:
1. Create a new Gmail account
2. Generate app password for the new account
3. Test with new credentials

---

## 📋 Recommended Configuration

For **Gmail port 465 (Most Reliable)**:
```json
{
    "smtp": {
        "server": "smtp.gmail.com",
        "port": 465,
        "use_ssl": true,
        "use_tls": false,
        "username": "your-email@gmail.com",
        "password": "your-16-char-app-password",
        "from_email": "your-email@gmail.com",
        "timeout": 90
    },
    "content": {
        "subject": "Your Subject",
        "body": "Your Body",
        "is_html": true,
        "attachments": []
    },
    "controls": {
        "limit": 10,
        "threads": 2,
        "delay": 2
    },
    "recipients": "recipient@example.com"
}
```

For **Port 587 (STARTTLS)**:
```json
{
    "smtp": {
        "port": 587,
        "use_ssl": false,
        "use_tls": true,
        ...
    }
}
```

---

## 🧪 Testing Tools Available

```bash
# Test connection with your credentials
python3 test_credentials.py

# Quick port 465 test
python3 test_smtp_465.py

# Quick port 587 test  
python3 test_smtp.py
```

---

## 📝 Summary

| Issue | Solution |
|-------|----------|
| "Connection unexpectedly closed" | Generate new app password at myaccount.google.com/apppasswords |
| "Authentication failed" | Verify app password is correct (16 chars with spaces) |
| "Timeout" | Increase timeout to 90+ seconds (already configured) |
| Account locked | Check https://accounts.google.com/signin/recovery |
| Can't find app passwords | Enable 2FA first at https://myaccount.google.com/security |

---

## ⚠️ Important Security Notes

- ✅ Never commit passwords to version control
- ✅ App passwords are safer than using your main Gmail password
- ✅ Each app password is device-specific
- ✅ You can delete old app passwords anytime
- ✅ Gmail logs all app password usage for security

---

## Need More Help?

- Gmail App Passwords Guide: https://support.google.com/accounts/answer/185833
- Gmail Security: https://myaccount.google.com/security
- Python SMTP: https://docs.python.org/3/library/smtplib.html
