import smtplib
import threading
import time
import queue
import os
import ssl
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

import random
import re

class SendWorker(threading.Thread):
    def __init__(self, task_queue, smtp_configs, email_config, send_delay, log_queue, progress_queue, stop_event):
        super().__init__()
        self.task_queue = task_queue
        self.smtp_configs = smtp_configs # List of dicts
        self.email_config = email_config
        self.send_delay = send_delay
        self.log_queue = log_queue
        self.progress_queue = progress_queue
        self.stop_event = stop_event
        self.daemon = True
        
        self.current_smtp_idx = random.randint(0, len(self.smtp_configs) - 1)
        self.current_smtp_config = self.smtp_configs[self.current_smtp_idx]
        
        # Keep attachment paths and build fresh MIME parts per message.
        self.attachment_paths = []
        for file_path in self.email_config.get('attachments', []):
            if os.path.exists(file_path):
                self.attachment_paths.append(file_path)
            else:
                self.log_message(f"⚠️ Attachment file not found and will be skipped: {file_path}")

    def _rotate_smtp(self):
        self.current_smtp_idx = (self.current_smtp_idx + 1) % len(self.smtp_configs)
        self.current_smtp_config = self.smtp_configs[self.current_smtp_idx]
        self.log_message(f"🔄 Rotating to SMTP account: {self.current_smtp_config['username']}")

    def _build_message(self, to_addr):
        # Build message on the fly and attach fresh MIME parts for each send.
        outer = MIMEMultipart('mixed')
        alternative = MIMEMultipart('alternative')
        
        # Determine FROM address
        if self.current_smtp_config.get('randomize_from', False):
            # Use generated random email as FROM
            from_email = self._generate_random_email()
            self.log_message(f"   📤 Using random FROM: {from_email}")
        else:
            # Use real sender email
            from_email = self.current_smtp_config.get('from_email', self.current_smtp_config['username'])
        
        outer['From'] = from_email
        outer['To'] = to_addr
        
        # Spintax parser for subject and body
        subject = self._parse_spintax(self.email_config['subject'])
        body = self._parse_spintax(self.email_config['body'])
        
        outer['Subject'] = subject
        
        # Add proper headers to avoid spam detection
        timestamp = int(time.time())
        random_part = random.randint(100000, 999999)
        real_email = self.current_smtp_config.get('username', '')
        outer['Message-ID'] = f"<{random_part}.{timestamp}@{real_email.split('@')[-1] if '@' in real_email else 'gmail.com'}>"
        
        from email.utils import formatdate
        outer['Date'] = formatdate(localtime=True)
        outer['X-Mailer'] = 'Python-SMTP/3.0'
        outer['MIME-Version'] = '1.0'
        outer['Reply-To'] = real_email
        outer['Sender'] = real_email
        unsubscribe_link = f"mailto:{real_email}?subject=Unsubscribe"
        outer['List-Unsubscribe'] = f"<{unsubscribe_link}>"
        outer['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
        outer['Return-Path'] = real_email
        outer['X-Priority'] = '3'
        outer['X-MSMail-Priority'] = 'Normal'

        if self.email_config['is_html']:
            alternative.attach(MIMEText(body, 'html', 'utf-8'))
        else:
            alternative.attach(MIMEText(body, 'plain', 'utf-8'))

        outer.attach(alternative)

        for file_path in self.attachment_paths:
            try:
                with open(file_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition',
                                    f'attachment; filename="{os.path.basename(file_path)}"')
                    outer.attach(part)
            except Exception as e:
                self.log_message(f"⚠️ Attachment error {file_path}: {e}")

        return outer

    def _parse_spintax(self, text):
        # Example: {Hi|Hello|Hey} -> random choice
        pattern = re.compile(r'\{([^{}]*)\}')
        while pattern.search(text):
            text = pattern.sub(lambda m: random.choice(m.group(1).split('|')), text)
        return text

    def _generate_random_email(self):
        """Generate random FROM email that Gmail will accept"""
        import string
        
        # Generate random display name
        names = ["Support", "Admin", "Service", "Billing", "Update", "Alert", "Notice", 
                 "System", "Team", "Sales", "Help", "Info", "Marketing", "Manager", "Assist"]
        display_name = random.choice(names)
        
        # Add random suffix
        chars = string.ascii_lowercase + string.digits
        suffix = ''.join(random.choice(chars) for _ in range(4))
        display_name = f"{display_name}_{suffix}"
        
        # Get the authenticated domain (extract from real email)
        real_email = self.current_smtp_config.get('username', '')
        if '@' in real_email:
            domain = real_email.split('@')[1]
        else:
            domain = 'gmail.com'
        
        # Return formatted FROM with display name and real domain
        # This keeps the domain authentic but changes display name
        return f"{display_name} <{real_email}>"

    def run(self):
        server = None
        while not self.stop_event.is_set():
            try:
                item = self.task_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if item is None:
                break

            idx, to_addr = item
            if not to_addr or not isinstance(to_addr, str):
                self.log_message(f"❌ Skipping invalid recipient: {to_addr}")
                self.report_progress(failed=1)
                self.task_queue.task_done()
                continue

            # Ensure connection is alive
            if server is None:
                server = self.connect_smtp()
                if not server:
                    self.report_progress(failed=1)
                    self.task_queue.task_done()
                    time.sleep(self.send_delay)
                    continue

            success = self.send_single_email(server, to_addr)
            if success:
                self.report_progress(sent=1)
                self.log_message(f"✅ Sent to {to_addr} (via {self.current_smtp_config['username']})")
            else:
                self.report_progress(failed=1)
                self.log_message(f"❌ Failed to send to {to_addr} (via {self.current_smtp_config['username']})")
                # Connection might be dead or account banned, force reconnect and rotate
                try:
                    server.quit()
                except:
                    pass
                server = None
                self._rotate_smtp()

            self.task_queue.task_done()
            if self.send_delay > 0:
                time.sleep(self.send_delay)
                
        if server:
            try:
                server.quit()
            except:
                pass

    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put(f"[{timestamp}] {message}")

    def report_progress(self, sent=0, failed=0):
        self.progress_queue.put({'sent': sent, 'failed': failed})

    def connect_smtp(self):
        attempts = 0
        max_attempts = len(self.smtp_configs) * 2
        
        while attempts < max_attempts and not self.stop_event.is_set():
            try:
                server_addr = self.current_smtp_config.get('server', '').strip()
                timeout = int(self.current_smtp_config.get('timeout', 90))
                port = int(self.current_smtp_config['port'])
                username = self.current_smtp_config.get('username', '').strip()
                password = self.current_smtp_config.get('password', '').strip()
                use_ssl = self.current_smtp_config.get('use_ssl', False)
                use_tls = self.current_smtp_config.get('use_tls', True)
                
                # Create SSL context - compatible with Gmail
                context = ssl.create_default_context()
                context.check_hostname = True
                context.verify_mode = ssl.CERT_REQUIRED
                
                # Port selection logic
                if port == 465 or use_ssl:
                    # Direct SSL on port 465
                    self.log_message(f"🔗 Connecting to {server_addr}:{port} (direct SSL)...")
                    server = smtplib.SMTP_SSL(server_addr, port, 
                                              context=context, timeout=timeout)
                else:
                    # STARTTLS on port 587 (default for Gmail)
                    self.log_message(f"🔗 Connecting to {server_addr}:{port} (STARTTLS)...")
                    server = smtplib.SMTP(server_addr, port, timeout=timeout)
                server.ehlo()
                    
                if use_tls:
                    # Upgrade to TLS
                    server.starttls(context=context)
                    server.ehlo()
                
                # Login
                if username and password:
                    self.log_message(f"🔐 Authenticating as {username}...")
                    server.login(username, password)
                
                self.log_message(f"✅ Connected and authenticated")
                return server
                
            except smtplib.SMTPAuthenticationError as e:
                error_msg = str(e)
                self.log_message(f"❌ AUTH FAILED: {error_msg}")
                self.log_message(f"   ⚠️  Check credentials. Generate new app password: https://myaccount.google.com/apppasswords")
                self._rotate_smtp()
                attempts += 1
                time.sleep(2)
                
            except (ssl.SSLError, ssl.CertificateError) as e:
                error_msg = str(e)
                self.log_message(f"❌ SSL ERROR: {error_msg}")
                if "WRONG_VERSION_NUMBER" in error_msg:
                    self.log_message(f"   Trying port 587 with STARTTLS instead...")
                self._rotate_smtp()
                attempts += 1
                time.sleep(2)
                
            except smtplib.SMTPServerDisconnected as e:
                error_msg = str(e)
                self.log_message(f"❌ SERVER DISCONNECTED: {error_msg}")
                self._rotate_smtp()
                attempts += 1
                time.sleep(1)
                
            except (socket.timeout, OSError) as e:
                error_msg = str(e)
                self.log_message(f"❌ CONNECTION ERROR: {error_msg}")
                self._rotate_smtp()
                attempts += 1
                time.sleep(1)
                
            except Exception as e:
                error_msg = str(e)
                self.log_message(f"❌ ERROR: {type(e).__name__}: {error_msg}")
                self._rotate_smtp()
                attempts += 1
                time.sleep(1)
        
        self.log_message(f"❌ Failed to connect after {attempts} attempts")
        return None

    def send_single_email(self, server, to_addr):
        try:
            msg = self._build_message(to_addr)
            
            # Log what we're sending (for debugging spam issues)
            self.log_message(f"📤 Sending to {to_addr}")
            self.log_message(f"   From: {msg['From']}")
            self.log_message(f"   Subject: {msg['Subject'][:60]}")
            
            server.send_message(msg)
            return True
            
        except smtplib.SMTPServerDisconnected:
            self.log_message(f"❌ SMTP Disconnected: {to_addr}")
            return False
        except smtplib.SMTPRecipientsRefused as e:
            # Gmail rejected recipient - likely spam-flagged
            self.log_message(f"❌ BLOCKED: {to_addr} - {str(e)}")
            self.log_message(f"   ℹ️  Gmail rejected as spam. Reduce sending frequency.")
            return False
        except smtplib.SMTPException as e:
            error_msg = str(e)
            if "550" in error_msg or "blocked" in error_msg.lower():
                self.log_message(f"❌ BLOCKED: {to_addr}")
                self.log_message(f"   Reason: {error_msg}")
            else:
                self.log_message(f"❌ SMTP error to {to_addr}: {error_msg}")
            return False
        except Exception as e:
            self.log_message(f"❌ Error sending to {to_addr}: {str(e)}")
            return False

class EmailManager:
    def __init__(self):
        self.stop_event = threading.Event()
        self.workers = []
        self.task_queue = queue.Queue()
        self.log_queue = queue.Queue()
        self.progress_queue = queue.Queue()
        
        self.sent_count = 0
        self.fail_count = 0
        self.total_to_send = 0
        self.is_running = False

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put(f"[{timestamp}] {message}")

    def start_booming(self, config, recipients):
        if self.is_running:
            return False, "Already running"
        
        self.is_running = True
        self.sent_count = 0
        self.fail_count = 0
        
        # Empty queues
        while not self.log_queue.empty(): self.log_queue.get()
        while not self.progress_queue.empty(): self.progress_queue.get()
        while not self.task_queue.empty(): self.task_queue.get()
        
        self.stop_event.clear()
        self.feed_done = False

        limit = int(config.get('controls', {}).get('limit', 0))
        # limit 0 means infinite. Otherwise, limit is the total number of emails to send.
        if limit > 0:
            self.total_to_send = limit
        else:
            self.total_to_send = "Unlimited"

        num_threads = max(1, int(config.get('controls', {}).get('threads', 3)))
        send_delay = float(config.get('controls', {}).get('delay', 0.5))

        time_limit = float(config.get('controls', {}).get('time_limit', 0))
        auto_bomb = config.get('controls', {}).get('auto_bomb', False)
        schedule_time_str = config.get('controls', {}).get('schedule_time', None)

        if schedule_time_str:
            try:
                # Expected format: '2026-05-24T23:45'
                schedule_time = datetime.strptime(schedule_time_str, "%Y-%m-%dT%H:%M")
                now = datetime.now()
                if schedule_time > now:
                    wait_seconds = (schedule_time - now).total_seconds()
                    self.log(f"🕒 Boom scheduled for {schedule_time.strftime('%Y-%m-%d %H:%M:%S')}. Waiting {int(wait_seconds)} seconds...")
                    
                    def scheduled_start():
                        time.sleep(wait_seconds)
                        if self.is_running and not self.stop_event.is_set():
                            self._execute_boom(config, recipients, limit, time_limit, auto_bomb)
                    
                    threading.Thread(target=scheduled_start, daemon=True).start()
                    return True, "Scheduled"
            except Exception as e:
                self.log(f"⚠️ Schedule time parse error: {e}. Starting immediately.")

        # Start immediately if no valid future schedule
        self._execute_boom(config, recipients, limit, time_limit, auto_bomb)
        return True, "Started"

    def _execute_boom(self, config, recipients, limit, time_limit, auto_bomb):
        num_threads = max(1, int(config.get('controls', {}).get('threads', 3)))
        send_delay = float(config.get('controls', {}).get('delay', 0.5))

        # Start feeder thread
        threading.Thread(target=self.feed_queue, args=(recipients, limit, time_limit, auto_bomb), daemon=True).start()

        self.workers = []
        for _ in range(num_threads):
            worker = SendWorker(
                task_queue=self.task_queue,
                smtp_configs=config.get('parsed_smtps', []),
                email_config=config.get('content', {}),
                send_delay=send_delay,
                log_queue=self.log_queue,
                progress_queue=self.progress_queue,
                stop_event=self.stop_event
            )
            worker.start()
            self.workers.append(worker)

        # Monitor thread
        threading.Thread(target=self.monitor_sending, daemon=True).start()
        
        self.log("🚀 BOOM EXECUTED. SENDING PAYLOADS...")
        # initial progress
        self.progress_queue.put({'sent': 0, 'failed': 0})

    def generate_random_email(self):
        import random, string
        length = random.randint(6, 12)
        letters = string.ascii_lowercase + string.digits
        random_user = ''.join(random.choice(letters) for i in range(length))
        domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com', 'icloud.com']
        return f"{random_user}@{random.choice(domains)}"

    def feed_queue(self, recipients, limit, time_limit, auto_bomb):
        count = 0
        idx = 0
        num_recipients = len(recipients)
        start_time = time.time()
        
        while not self.stop_event.is_set():
            if limit > 0 and count >= limit:
                break
                
            if time_limit > 0 and (time.time() - start_time) >= time_limit:
                self.log_queue.put(f"[{datetime.now().strftime('%H:%M:%S')}] ⏱️ Time limit reached.")
                self.stop_event.set()
                break
            
            if self.task_queue.qsize() < 100:
                if auto_bomb:
                    rec = self.generate_random_email()
                else:
                    if num_recipients == 0:
                        break
                    rec = recipients[idx % num_recipients]
                
                self.task_queue.put((count, rec))
                count += 1
                idx += 1
            else:
                time.sleep(0.1)
                
        self.feed_done = True

    def monitor_sending(self):
        # Wait until feeder is done and queue is fully processed
        while not self.stop_event.is_set():
            if self.feed_done and self.task_queue.unfinished_tasks == 0:
                break
            time.sleep(0.5)

        self.stop_event.set()
        for w in self.workers:
            if w.is_alive():
                w.join(timeout=2)
        
        self.is_running = False
        self.log("✅ Booming finished.")
        self.progress_queue.put({'finished': True})

    def stop_booming(self):
        if not self.is_running:
            return
        self.stop_event.set()
        self.log("⚠️ Stopping booming... (please wait for current emails to finish)")
        
    def get_updates(self):
        logs = []
        while not self.log_queue.empty():
            logs.append(self.log_queue.get_nowait())
            
        sent_delta = 0
        failed_delta = 0
        finished = False
        
        while not self.progress_queue.empty():
            p = self.progress_queue.get_nowait()
            if 'finished' in p:
                finished = True
            else:
                sent_delta += p.get('sent', 0)
                failed_delta += p.get('failed', 0)
                
        self.sent_count += sent_delta
        self.fail_count += failed_delta
        
        return {
            'logs': logs,
            'progress': {
                'sent': self.sent_count,
                'failed': self.fail_count,
                'total': self.total_to_send,
                'is_running': self.is_running,
                'finished': finished
            }
        }
    
    def clear_logs(self):
        """Clear all logs from the queue"""
        while not self.log_queue.empty():
            try:
                self.log_queue.get_nowait()
            except:
                break
        self.log("🧹 Terminal cleared")
