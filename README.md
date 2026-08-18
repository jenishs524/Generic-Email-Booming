# Generic-Email-Booming

# Email Testing & SMTP Automation

A Flask-based web application for **authorized SMTP and email-delivery testing**.

> **Important:** Use this project only with email accounts and recipient addresses that you own or have explicit permission to test. Do not use it to send unsolicited bulk email, overwhelm mailboxes, bypass provider limits, or evade spam/abuse controls.

---

## 📌 Project Overview

This project provides a web interface for testing email delivery through SMTP.

It supports:

* SMTP configuration
* TLS/SSL SMTP connections
* Email subject and body configuration
* Plain-text and HTML email
* Email attachments
* Recipient management
* Sending progress and live logs
* Start/stop controls
* Configuration saving/loading
* SQLite campaign records
* Docker deployment
* SMTP connection testing
* Test scripts for troubleshooting

### Technology Stack

| Component              | Technology            |
| ---------------------- | --------------------- |
| Backend                | Python                |
| Web Framework          | Flask                 |
| Database               | SQLite                |
| ORM                    | Flask-SQLAlchemy      |
| Authentication library | Flask-Login           |
| WSGI Server            | Gunicorn              |
| Email                  | Python `smtplib`      |
| Frontend               | HTML, CSS, JavaScript |
| Containerization       | Docker                |

---

# 📁 Project Structure

```text
Email Booming/
│
├── app.py
├── email_sender.py
├── email_bomming.py
├── models.py
│
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
│
├── email_boomer_config.json
│
├── send_test_email.py
├── test_credentials.py
├── test_random_emails.py
├── test_smtp.py
├── test_smtp_465.py
│
├── templates/
│   └── index.html
│
├── static/
│   ├── app.js
│   ├── style.css
│   └── hacker_bg.png
│
├── uploads/
│
├── instance/
│   └── database.db
│
├── GMAIL_SETUP.md
├── GMAIL_SPAM_SOLUTIONS.md
├── RANDOM_EMAIL_SETUP.md
├── TROUBLESHOOTING.md
└── FIXES_APPLIED.md
```

---

# ⚙️ How the Application Works

The general workflow is:

```text
                    ┌──────────────────┐
                    │      User        │
                    │ Web Browser      │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   Flask Web App  │
                    │     app.py       │
                    └────────┬─────────┘
                             │
                 ┌───────────┴───────────┐
                 ▼                       ▼
        ┌─────────────────┐      ┌─────────────────┐
        │ Configuration   │      │   Recipients    │
        │ SMTP / Content  │      │ Email Addresses │
        └────────┬────────┘      └────────┬────────┘
                 │                        │
                 └────────────┬───────────┘
                              ▼
                    ┌──────────────────┐
                    │  Email Manager   │
                    │ email_sender.py  │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   SMTP Server    │
                    │ TLS / SSL        │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Authorized Test  │
                    │ Recipient        │
                    └──────────────────┘
```

---

# 🔧 Requirements

Before running the project, install:

### Required

* Python 3.10+
* pip
* Git (optional)
* A test SMTP account
* An email address that you are authorized to test

### Optional

* Docker
* Docker Compose

---

# 🐍 Installation on Kali Linux / Linux

## 1. Extract the project

```bash
unzip "Email Booming.zip"
cd "Email Booming"
```

Check the files:

```bash
ls
```

You should see:

```text
app.py
requirements.txt
email_sender.py
templates
static
Dockerfile
docker-compose.yml
```

---

## 2. Check Python

```bash
python3 --version
```

Check pip:

```bash
python3 -m pip --version
```

If Python is missing:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv unzip -y
```

---

# 🧪 3. Create a Virtual Environment

Recommended:

```bash
python3 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

You should see something similar to:

```text
(venv) user@kali:~/Email\ Booming$
```

---

# 📦 4. Install Python Dependencies

Run:

```bash
pip install -r requirements.txt
```

The project requires:

```text
Flask==3.1.3
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Werkzeug==3.1.8
gunicorn==26.0.0
```

Verify Flask:

```bash
python3 -c "import flask; print(flask.__version__)"
```

---

# 📧 SMTP Configuration

The application uses SMTP to communicate with an email provider.

Typical SMTP settings are:

```text
SMTP Server: smtp.example.com
SMTP Port: 587
Security: STARTTLS
Username: your-test-account
Password: your-test-account-password
```

For an SMTP provider that supports implicit TLS, the common configuration is:

```text
Port: 465
SSL: Enabled
```

Do not put a normal account password into a project unless the provider explicitly supports it. Use the provider's recommended authentication mechanism, such as an app-specific password where applicable.

---

# 🔐 Protect Your Credentials

Never commit real SMTP passwords to GitHub.

For example, do **not** publish:

```text
username: myemail@example.com
password: my-real-password
```

Also do not publish:

```text
email_boomer_config.json
```

if it contains real credentials.

Add sensitive files to `.gitignore`:

```text
venv/
__pycache__/
*.pyc
instance/
uploads/
email_boomer_config.json
.env
```

If credentials were accidentally uploaded to GitHub, immediately revoke/rotate them.

---

# ▶️ Running the Application

With the virtual environment activated:

```bash
python3 app.py
```

The application listens on:

```text
http://127.0.0.1:5000
```

Open your browser and visit:

```text
http://127.0.0.1:5000
```

---

# 🖥️ Application Interface

The interface contains several sections.

## 1. SMTP Settings

Used to configure the authorized test SMTP server.

Typical information includes:

```text
SMTP Server
Port
SSL/TLS
Username
Password
From Email
Timeout
```

---

## 2. Email Content

You can configure:

```text
Subject
Body
HTML / Plain Text
Attachments
```

For example:

```text
Subject:
SMTP Security Test

Body:
This is an authorized email-delivery test.
```

---

## 3. Recipients

Enter **only authorized test addresses**.

Example:

```text
test-account-1@example.com
test-account-2@example.com
```

You can also load recipient data from a file supported by the application.

---

## 4. Controls

The application includes controls for managing a test run, including:

```text
Start
Stop
Delay
Limit
Threads
```

For a safe lab, use a small recipient set and a conservative delay.

---

# 📎 Attachments

The application supports attachments.

The interface can add files to the email before sending.

Example:

```text
test-report.pdf
sample.txt
test-image.png
```

Only attach files that you are authorized to send.

---

# 🗄️ Database

The project uses SQLite.

The database is stored under:

```text
instance/database.db
```

Flask-SQLAlchemy is used to manage database operations.

Campaign information can be recorded by the application.

---

# 🌐 API Workflow

The Flask backend exposes endpoints used by the frontend.

### Get configuration

```text
GET /api/config
```

### Save configuration

```text
POST /api/config
```

### Upload attachment

```text
POST /api/upload
```

### Start a test run

```text
POST /api/start
```

### Stop a test run

```text
POST /api/stop
```

### Clear logs

```text
POST /api/clear-logs
```

### Check status

```text
GET /api/status
```

The frontend communicates with these endpoints through JavaScript.

---

# 🔄 Complete Application Workflow

```text
1. Start Flask
       │
       ▼
2. Open Web Dashboard
       │
       ▼
3. Configure Authorized SMTP Account
       │
       ▼
4. Configure Email Subject/Body
       │
       ▼
5. Add Authorized Test Recipient
       │
       ▼
6. Add Optional Test Attachment
       │
       ▼
7. Save Configuration
       │
       ▼
8. Start Test
       │
       ▼
9. Flask Receives Request
       │
       ▼
10. Email Manager Processes Test
       │
       ▼
11. SMTP Connection
       │
       ▼
12. TLS/SSL Authentication
       │
       ▼
13. Construct MIME Email
       │
       ▼
14. Send to Authorized Recipient
       │
       ▼
15. Record Success/Failure
       │
       ▼
16. Display Logs and Status
       │
       ▼
17. Stop Test
```

---

# 🐳 Docker Installation

Docker provides another way to run the application without manually installing the Python dependencies.

Check Docker:

```bash
docker --version
```

Check Docker Compose:

```bash
docker compose version
```

If Docker is not installed on Kali:

```bash
sudo apt update
sudo apt install docker.io docker-compose-plugin -y
```

Start Docker:

```bash
sudo systemctl enable --now docker
```

---

# 🏗️ Build the Docker Container

From the project directory:

```bash
docker compose build
```

Then start:

```bash
docker compose up
```

The application uses:

```text
Port 5000
```

Open:

```text
http://127.0.0.1:5000
```

To run in the background:

```bash
docker compose up -d
```

Check containers:

```bash
docker ps
```

View logs:

```bash
docker compose logs
```

Stop:

```bash
docker compose down
```

---

# 🧪 Testing

The repository contains several testing scripts.

Examples include:

```text
test_credentials.py
test_random_emails.py
test_smtp.py
test_smtp_465.py
send_test_email.py
```

Use these only against SMTP accounts and recipients you control.

For example, inspect a test script before running it:

```bash
cat test_smtp.py
```

Then execute an appropriate authorized test:

```bash
python3 test_smtp.py
```

---

# 🛠️ Troubleshooting

## Flask does not start

Check:

```bash
python3 --version
```

Then:

```bash
pip install -r requirements.txt
```

---

## Port 5000 is already being used

Check:

```bash
sudo ss -ltnp | grep :5000
```

Stop the process that is legitimately using the port, or change the application's port.

---

## SMTP Authentication Failure

Check:

```text
SMTP server
SMTP port
TLS/SSL configuration
Username
Authentication method
```

Do not repeatedly attempt authentication against an account you do not control.

---

## TLS/SSL Error

Port and encryption mode must match the SMTP provider.

Common patterns are:

```text
587 → STARTTLS
465 → SMTP over SSL
```

Always follow your provider's current SMTP documentation.

---

## Attachment Not Found

Check the file path:

```bash
ls -lh uploads/
```

Make sure the application has permission to read the file.

---

# 🔒 Security Recommendations

Before using this project beyond a local laboratory:

* Use authentication for the web dashboard.
* Do not expose port 5000 directly to the Internet.
* Store SMTP credentials outside source code.
* Use environment variables or a secrets manager.
* Add CSRF protection.
* Validate uploaded files.
* Restrict attachment size and type.
* Keep detailed audit logs.
* Use authorization checks for every sending operation.
* Add recipient allowlists for laboratory use.
* Add strict rate limits.
* Never use the application to bypass provider anti-abuse controls.
* Never use it for unsolicited bulk email.

---

# 🧪 Recommended Cybersecurity Lab Setup

For safe testing, create a controlled environment:

```text
┌────────────────────────────┐
│ Kali Linux / Test Machine  │
│                            │
│ Flask Email Test App       │
└─────────────┬──────────────┘
              │
              │ SMTP
              ▼
┌────────────────────────────┐
│ Test SMTP Account          │
└─────────────┬──────────────┘
              │
              ▼
┌────────────────────────────┐
│ Your Test Mailbox          │
│                            │
│ Observe:                   │
│ • Delivery                 │
│ • Headers                  │
│ • TLS                      │
│ • Authentication           │
│ • Attachments              │
└────────────────────────────┘
```

This lets you study email infrastructure without targeting other people's mailboxes.

---

# 📚 Useful Project Files

### `app.py`

Main Flask application.

Responsible for:

* Web routes
* API endpoints
* Configuration
* File uploads
* Database initialization
* Starting/stopping email operations

### `email_sender.py`

Contains SMTP/email-sending functionality.

Responsible for:

* SMTP connection
* TLS/SSL
* MIME message construction
* Attachments
* Sending
* Logging
* Progress reporting

### `models.py`

Contains database models.

### `templates/index.html`

Main web interface.

### `static/app.js`

Frontend JavaScript.

### `static/style.css`

Frontend styling.

### `requirements.txt`

Python dependency list.

### `Dockerfile`

Defines the application container.

### `docker-compose.yml`

Defines how the application is started with Docker Compose.

---

# 🚀 Quick Start

```bash
unzip "Email Booming.zip"

cd "Email Booming"

python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt

python3 app.py
```

Then open:

```text
http://127.0.0.1:5000
```

Configure an **authorized test SMTP account**, use a **test recipient you control**, and perform a small delivery test.

---

# 🎯 Project Purpose

This project can be used as a cybersecurity/DevOps learning project to understand:

* SMTP
* TLS
* Email authentication
* MIME messages
* Flask APIs
* Frontend/backend communication
* SQLite
* File uploads
* Docker
* Python threading
* Logging
* Email delivery troubleshooting

It should be operated only within an authorized testing environment.

---

# ⚠️ Disclaimer

The author/user is responsible for ensuring that this software is used legally and ethically.

Do not use this project to:

* send unsolicited emails;
* flood or overwhelm mailboxes;
* harass recipients;
* bypass anti-spam systems;
* evade provider restrictions;
* impersonate another sender;
* distribute malicious attachments;
* access or use SMTP accounts without authorization.

Use controlled accounts, controlled recipients, and controlled test environments.
