import os
import json
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from email_sender import EmailManager
from models import db, Campaign

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-advanced-key-for-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload

CONFIG_FILE = 'email_boomer_config.json'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)
email_manager = EmailManager()

@app.before_request
def create_tables():
    app.before_request_funcs[None].remove(create_tables)
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            try:
                config = json.load(f)
                return jsonify(config)
            except:
                pass
    return jsonify({})

@app.route('/api/config', methods=['POST'])
def save_config():
    config = request.json
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)
    return jsonify({"status": "success"})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({"filepath": os.path.abspath(filepath), "filename": filename})

@app.route('/api/start', methods=['POST'])
def start_booming():
    data = request.json
    config = data.get('config', {})
    recipients_raw = data.get('recipients', '')
    
    if not recipients_raw:
        return jsonify({"error": "No recipients"}), 400
        
    recipients = [r.strip() for r in recipients_raw.splitlines() if r.strip() and '@' in r]
    if not recipients:
        return jsonify({"error": "No valid email addresses found"}), 400

    bulk_smtp_raw = config.get('smtp', {}).get('bulk_accounts', '').strip()
    if not bulk_smtp_raw:
        return jsonify({"error": "Bulk SMTP Accounts are required. Please check your SMTP Settings tab."}), 400

    parsed_smtps = []
    for line in bulk_smtp_raw.splitlines():
        line = line.strip()
        if not line: continue
        parts = line.split(':')
        if len(parts) >= 5:
            # server:port:user:password:from_email
            parsed_smtps.append({
                'server': parts[0].strip(),
                'port': parts[1].strip(),
                'username': parts[2].strip(),
                'password': parts[3].strip(),
                'from_email': ':'.join(parts[4:]).strip(), # Support colons in from_email (e.g. 'Name <email>')
                'use_ssl': config.get('smtp', {}).get('use_ssl', False),
                'use_tls': config.get('smtp', {}).get('use_tls', True),
                'timeout': config.get('smtp', {}).get('timeout', 30),
                'randomize_from': config.get('smtp', {}).get('randomize_from', False),
                'random_from_domain': config.get('smtp', {}).get('random_from_domain', '')
            })

    if not parsed_smtps:
        return jsonify({"error": "No valid SMTP accounts parsed. Ensure format is server:port:user:password:from_email"}), 400

    # Inject parsed smtps into config for manager
    config['parsed_smtps'] = parsed_smtps

    attachments = config.get('content', {}).get('attachments', [])
    valid_attachments = [a for a in attachments if os.path.exists(a)]
    if 'content' not in config:
        config['content'] = {}
    config['content']['attachments'] = valid_attachments

    success, msg = email_manager.start_booming(config, recipients)
    if success:
        # Create campaign record
        subject = config.get('content', {}).get('subject', 'No Subject')
        campaign = Campaign(subject=subject)
        db.session.add(campaign)
        db.session.commit()
        return jsonify({"status": "started"})
    else:
        return jsonify({"error": msg}), 400

@app.route('/api/stop', methods=['POST'])
def stop_booming():
    email_manager.stop_booming()
    return jsonify({"status": "stopping"})

@app.route('/api/clear-logs', methods=['POST'])
def clear_logs():
    """Clear terminal logs"""
    email_manager.clear_logs()
    return jsonify({"status": "logs cleared"})

@app.route('/api/status', methods=['GET'])
def get_status():
    updates = email_manager.get_updates()
    return jsonify(updates)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000, host='0.0.0.0')
