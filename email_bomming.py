import smtplib
import threading
import time
import json
import os
import queue
from tkinter import *
from tkinter import ttk, filedialog, messagebox, scrolledtext
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

# ----------------------------------------------------------------------
# Worker Thread for Sending Emails
# ----------------------------------------------------------------------
class SendWorker(threading.Thread):
    def __init__(self, task_queue, smtp_config, email_config, recipients, 
                 send_delay, log_callback, progress_callback, stop_event):
        super().__init__()
        self.task_queue = task_queue          # queue of (recipient_index, recipient_email)
        self.smtp_config = smtp_config
        self.email_config = email_config
        self.recipients = recipients
        self.send_delay = send_delay
        self.log_callback = log_callback
        self.progress_callback = progress_callback
        self.stop_event = stop_event
        self.daemon = True

    def run(self):
        while not self.stop_event.is_set():
            try:
                item = self.task_queue.get(timeout=0.5)
            except queue.Empty:
                break   # no more tasks

            if item is None:
                break

            idx, to_addr = item
            if not to_addr or not isinstance(to_addr, str):
                self.log_callback(f"❌ Skipping invalid recipient: {to_addr}")
                self.progress_callback(1, 0)   # one failed
                self.task_queue.task_done()
                continue

            success = self.send_single_email(to_addr)
            if success:
                self.progress_callback(1, 1)   # one sent
                self.log_callback(f"✅ Sent to {to_addr}")
            else:
                self.progress_callback(1, 0)   # one failed
                self.log_callback(f"❌ Failed to send to {to_addr}")

            self.task_queue.task_done()
            time.sleep(self.send_delay)

    def send_single_email(self, to_addr):
        """Send one email using current SMTP configuration."""
        try:
            # Build message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config['from_email']
            msg['To'] = to_addr
            msg['Subject'] = self.email_config['subject']

            # Body (HTML or plain)
            if self.email_config['is_html']:
                msg.attach(MIMEText(self.email_config['body'], 'html'))
            else:
                msg.attach(MIMEText(self.email_config['body'], 'plain'))

            # Attachments
            for file_path in self.email_config['attachments']:
                try:
                    with open(file_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition',
                                        f'attachment; filename="{os.path.basename(file_path)}"')
                        msg.attach(part)
                except Exception as e:
                    self.log_callback(f"⚠️ Attachment error {file_path}: {e}")

            # Connect and send
            if self.smtp_config['use_ssl']:
                server = smtplib.SMTP_SSL(self.smtp_config['server'], 
                                          self.smtp_config['port'], 
                                          timeout=self.smtp_config['timeout'])
            else:
                server = smtplib.SMTP(self.smtp_config['server'], 
                                      self.smtp_config['port'], 
                                      timeout=self.smtp_config['timeout'])
                if self.smtp_config['use_tls']:
                    server.starttls()

            if self.smtp_config['username'] and self.smtp_config['password']:
                server.login(self.smtp_config['username'], self.smtp_config['password'])

            server.send_message(msg)
            server.quit()
            return True

        except Exception as e:
            self.log_callback(f"SMTP error to {to_addr}: {str(e)}")
            return False

# ----------------------------------------------------------------------
# Main GUI Application
# ----------------------------------------------------------------------
class EmailBoomerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Email Booming Tool")
        self.root.geometry("950x700")
        self.root.resizable(True, True)

        # Data
        self.config_file = "email_boomer_config.json"
        self.stop_event = threading.Event()
        self.workers = []
        self.task_queue = queue.Queue()
        self.sent_count = 0
        self.fail_count = 0
        self.total_to_send = 0

        # Build GUI
        self.create_widgets()
        self.load_config()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # Notebook for tabs
        nb = ttk.Notebook(self.root)
        nb.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # Tab 1: SMTP Settings
        self.smtp_frame = Frame(nb)
        nb.add(self.smtp_frame, text="SMTP Settings")
        self.create_smtp_tab()

        # Tab 2: Email Content
        self.content_frame = Frame(nb)
        nb.add(self.content_frame, text="Email Content")
        self.create_content_tab()

        # Tab 3: Recipients
        self.recipients_frame = Frame(nb)
        nb.add(self.recipients_frame, text="Recipients")
        self.create_recipients_tab()

        # Tab 4: Booming Controls
        self.controls_frame = Frame(nb)
        nb.add(self.controls_frame, text="Booming Controls")
        self.create_controls_tab()

        # Log Frame
        log_frame = LabelFrame(self.root, text="Live Log", padx=5, pady=5)
        log_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, state='disabled', wrap=WORD)
        self.log_text.pack(fill=BOTH, expand=True)

        # Bottom buttons
        btn_frame = Frame(self.root)
        btn_frame.pack(fill=X, padx=5, pady=5)

        self.start_btn = Button(btn_frame, text="🚀 START BOOMING", command=self.start_booming,
                                bg="green", fg="white", font=('Arial', 10, 'bold'))
        self.start_btn.pack(side=LEFT, padx=5)

        self.stop_btn = Button(btn_frame, text="⏹️ STOP", command=self.stop_booming,
                               bg="red", fg="white", state=DISABLED)
        self.stop_btn.pack(side=LEFT, padx=5)

        Button(btn_frame, text="💾 Save Config", command=self.save_config).pack(side=LEFT, padx=5)
        Button(btn_frame, text="📂 Load Config", command=self.load_config).pack(side=LEFT, padx=5)

        # Progress bar
        self.progress_var = DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=X, padx=5, pady=5)

        self.status_label = Label(self.root, text="Idle", anchor=W)
        self.status_label.pack(fill=X, padx=5, pady=2)

    # ---------------------- SMTP Tab ----------------------
    def create_smtp_tab(self):
        frame = self.smtp_frame
        Label(frame, text="SMTP Server:").grid(row=0, column=0, sticky=E, padx=5, pady=5)
        self.smtp_server = Entry(frame, width=40)
        self.smtp_server.grid(row=0, column=1, padx=5, pady=5)

        Label(frame, text="Port:").grid(row=1, column=0, sticky=E, padx=5, pady=5)
        self.smtp_port = Entry(frame, width=10)
        self.smtp_port.grid(row=1, column=1, sticky=W, padx=5, pady=5)

        self.use_ssl = BooleanVar()
        Checkbutton(frame, text="Use SSL (Port 465)", variable=self.use_ssl).grid(row=2, column=1, sticky=W)

        self.use_tls = BooleanVar(value=True)
        Checkbutton(frame, text="Use STARTTLS (Port 587)", variable=self.use_tls).grid(row=3, column=1, sticky=W)

        Label(frame, text="Username:").grid(row=4, column=0, sticky=E, padx=5, pady=5)
        self.smtp_user = Entry(frame, width=40)
        self.smtp_user.grid(row=4, column=1, padx=5, pady=5)

        Label(frame, text="Password:").grid(row=5, column=0, sticky=E, padx=5, pady=5)
        self.smtp_pass = Entry(frame, width=40, show="*")
        self.smtp_pass.grid(row=5, column=1, padx=5, pady=5)

        Label(frame, text="From Email:").grid(row=6, column=0, sticky=E, padx=5, pady=5)
        self.from_email = Entry(frame, width=40)
        self.from_email.grid(row=6, column=1, padx=5, pady=5)

        Label(frame, text="Timeout (sec):").grid(row=7, column=0, sticky=E, padx=5, pady=5)
        self.smtp_timeout = Entry(frame, width=10)
        self.smtp_timeout.insert(0, "30")
        self.smtp_timeout.grid(row=7, column=1, sticky=W, padx=5, pady=5)

    # ---------------------- Content Tab ----------------------
    def create_content_tab(self):
        frame = self.content_frame
        Label(frame, text="Subject:").grid(row=0, column=0, sticky=E, padx=5, pady=5)
        self.subject_entry = Entry(frame, width=70)
        self.subject_entry.grid(row=0, column=1, padx=5, pady=5)

        self.is_html = BooleanVar()
        Checkbutton(frame, text="HTML Email", variable=self.is_html).grid(row=1, column=1, sticky=W)

        Label(frame, text="Body:").grid(row=2, column=0, sticky=NE, padx=5, pady=5)
        self.body_text = scrolledtext.ScrolledText(frame, width=80, height=12)
        self.body_text.grid(row=2, column=1, padx=5, pady=5)

        # Attachments
        Label(frame, text="Attachments:").grid(row=3, column=0, sticky=NE, padx=5, pady=5)
        self.attachments_listbox = Listbox(frame, height=4, width=60)
        self.attachments_listbox.grid(row=3, column=1, sticky=W, pady=5)

        btn_frame = Frame(frame)
        btn_frame.grid(row=4, column=1, sticky=W)
        Button(btn_frame, text="Add Attachment", command=self.add_attachment).pack(side=LEFT, padx=2)
        Button(btn_frame, text="Remove Selected", command=self.remove_attachment).pack(side=LEFT, padx=2)

    def add_attachment(self):
        files = filedialog.askopenfilenames(title="Select files to attach")
        for f in files:
            if f not in self.attachments_listbox.get(0, END):
                self.attachments_listbox.insert(END, f)

    def remove_attachment(self):
        sel = self.attachments_listbox.curselection()
        if sel:
            self.attachments_listbox.delete(sel[0])

    # ---------------------- Recipients Tab ----------------------
    def create_recipients_tab(self):
        frame = self.recipients_frame
        Label(frame, text="Recipient List (one email per line):").pack(anchor=W, padx=5, pady=2)
        self.recipients_text = scrolledtext.ScrolledText(frame, height=12, width=90)
        self.recipients_text.pack(fill=BOTH, expand=True, padx=5, pady=5)

        btn_frame = Frame(frame)
        btn_frame.pack(fill=X, padx=5, pady=5)
        Button(btn_frame, text="Load from File", command=self.load_recipients_file).pack(side=LEFT, padx=2)
        Button(btn_frame, text="Clear List", command=lambda: self.recipients_text.delete(1.0, END)).pack(side=LEFT)

    def load_recipients_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Text/CSV", "*.txt *.csv"), ("All files", "*.*")])
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.read().splitlines()
                # Clean and add only non-empty lines
                current = self.recipients_text.get(1.0, END).strip()
                new_recipients = []
                for line in lines:
                    line = line.strip()
                    if line and ',' in line:   # simple CSV: email, name (ignore name)
                        line = line.split(',')[0].strip()
                    if line and '@' in line:
                        new_recipients.append(line)
                if new_recipients:
                    if current:
                        self.recipients_text.insert(END, "\n" + "\n".join(new_recipients))
                    else:
                        self.recipients_text.insert(END, "\n".join(new_recipients))
                else:
                    messagebox.showwarning("Warning", "No valid email addresses found in file.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")

    # ---------------------- Booming Controls Tab ----------------------
    def create_controls_tab(self):
        frame = self.controls_frame
        Label(frame, text="Number of emails to send (0 = all):").grid(row=0, column=0, sticky=E, padx=5, pady=5)
        self.limit_send = Entry(frame, width=10)
        self.limit_send.insert(0, "0")
        self.limit_send.grid(row=0, column=1, sticky=W, padx=5, pady=5)

        Label(frame, text="Threads (workers):").grid(row=1, column=0, sticky=E, padx=5, pady=5)
        self.thread_count = Entry(frame, width=10)
        self.thread_count.insert(0, "3")
        self.thread_count.grid(row=1, column=1, sticky=W, padx=5, pady=5)

        Label(frame, text="Delay between emails (sec):").grid(row=2, column=0, sticky=E, padx=5, pady=5)
        self.send_delay = Entry(frame, width=10)
        self.send_delay.insert(0, "0.5")
        self.send_delay.grid(row=2, column=1, sticky=W, padx=5, pady=5)

        # Rotate "From" not implemented in this version, can be extended.
        Label(frame, text="Note: Too many threads or zero delay may trigger rate limiting.", 
              fg="orange").grid(row=3, column=0, columnspan=2, pady=10)

    # ---------------------- Logging & Progress ----------------------
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}\n"
        self.log_text.configure(state='normal')
        self.log_text.insert(END, formatted)
        self.log_text.see(END)
        self.log_text.configure(state='disabled')
        self.root.update_idletasks()

    def update_progress(self, sent_delta, fail_delta):
        self.sent_count += sent_delta
        self.fail_count += fail_delta
        total_processed = self.sent_count + self.fail_count
        if isinstance(self.total_to_send, int) and self.total_to_send > 0:
            percent = (total_processed / self.total_to_send) * 100
            self.progress_var.set(percent)
        self.status_label.config(text=f"Sent: {self.sent_count} | Failed: {self.fail_count} | Total: {self.total_to_send}")
        self.root.update_idletasks()

    def feed_queue_continuous(self, recipients):
        idx = 0
        while not self.stop_event.is_set():
            if self.task_queue.qsize() < 100:
                self.task_queue.put((idx, recipients[idx % len(recipients)]))
                idx += 1
            else:
                time.sleep(0.1)

    # ---------------------- Start / Stop ----------------------
    def get_recipient_list(self):
        raw = self.recipients_text.get(1.0, END).strip()
        if not raw:
            return []
        lines = raw.splitlines()
        recipients = [line.strip() for line in lines if line.strip() and '@' in line]
        return recipients

    def validate_config(self):
        # SMTP
        server = self.smtp_server.get().strip()
        port = self.smtp_port.get().strip()
        from_email = self.from_email.get().strip()
        if not server or not port or not from_email:
            messagebox.showerror("Error", "SMTP Server, Port and From Email are required.")
            return False
        try:
            int(port)
        except ValueError:
            messagebox.showerror("Error", "Port must be a number.")
            return False
        return True

    def start_booming(self):
        if not self.validate_config():
            return

        recipients = self.get_recipient_list()
        if not recipients:
            messagebox.showwarning("No recipients", "Please add at least one recipient email in the Recipients tab.")
            return

        # Limit 0 now means unlimited repeat
        try:
            limit = int(self.limit_send.get().strip())
        except:
            limit = 0

        self.repeat_unlimited = (limit == 0)
        if not self.repeat_unlimited and limit > 0:
            recipients = recipients[:limit]

        if not recipients:
            messagebox.showwarning("No recipients", "After applying limit, no recipients left.")
            return

        self.total_to_send = "Unlimited" if self.repeat_unlimited else len(recipients)
        self.sent_count = 0
        self.fail_count = 0
        self.progress_var.set(0)
        self.status_label.config(text=f"Sent: 0 | Failed: 0 | Total: {self.total_to_send}")

        # Build SMTP config dict
        try:
            smtp_cfg = {
                'server': self.smtp_server.get().strip(),
                'port': int(self.smtp_port.get().strip()),
                'use_ssl': self.use_ssl.get(),
                'use_tls': self.use_tls.get(),
                'username': self.smtp_user.get().strip(),
                'password': self.smtp_pass.get().strip(),
                'from_email': self.from_email.get().strip(),
                'timeout': int(self.smtp_timeout.get().strip())
            }
        except Exception as e:
            messagebox.showerror("Error", f"Invalid SMTP settings: {e}")
            return

        # Email content config
        email_cfg = {
            'subject': self.subject_entry.get().strip(),
            'body': self.body_text.get(1.0, END).strip(),
            'is_html': self.is_html.get(),
            'attachments': list(self.attachments_listbox.get(0, END))
        }
        if not email_cfg['subject']:
            messagebox.showwarning("Warning", "Subject is empty, proceed?")
        if not email_cfg['body']:
            messagebox.showwarning("Warning", "Body is empty, proceed?")

        # Threads & delay
        try:
            num_threads = max(1, int(self.thread_count.get().strip()))
            send_delay = float(self.send_delay.get().strip())
        except:
            num_threads = 3
            send_delay = 0.5

        # Fill task queue
        self.task_queue = queue.Queue()
        self.feed_done = False
        if self.repeat_unlimited:
            threading.Thread(target=self.feed_queue_continuous, args=(recipients,), daemon=True).start()
        else:
            for idx, rec in enumerate(recipients):
                self.task_queue.put((idx, rec))
            self.feed_done = True

        # Clear stop event and start workers
        self.stop_event.clear()
        self.workers = []
        for _ in range(num_threads):
            worker = SendWorker(
                task_queue=self.task_queue,
                smtp_config=smtp_cfg,
                email_config=email_cfg,
                recipients=recipients,
                send_delay=send_delay,
                log_callback=self.log,
                progress_callback=self.update_progress,
                stop_event=self.stop_event
            )
            worker.start()
            self.workers.append(worker)

        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitor_sending, daemon=True)
        self.monitor_thread.start()

        self.start_btn.config(state=DISABLED)
        self.stop_btn.config(state=NORMAL)
        self.log("🚀 Booming started. Sending emails...")

    def monitor_sending(self):
        # Wait for all tasks to be done OR stop event
        while not self.stop_event.is_set():
            if not self.repeat_unlimited and self.task_queue.empty():
                # Wait a moment for workers to finish their current email
                time.sleep(1)
                if self.task_queue.empty():
                    break
            else:
                time.sleep(0.5)

        # Ensure all workers finish gracefully
        self.stop_event.set()
        for w in self.workers:
            if w.is_alive():
                w.join(timeout=2)
        self.root.after(0, self.finish_booming)

    def finish_booming(self):
        self.start_btn.config(state=NORMAL)
        self.stop_btn.config(state=DISABLED)
        self.log("✅ Booming finished.")
        self.status_label.config(text=f"Final - Sent: {self.sent_count} | Failed: {self.fail_count} | Total: {self.total_to_send}")

    def stop_booming(self):
        self.stop_event.set()
        self.log("⚠️ Stopping booming... (please wait for current emails to finish)")
        self.start_btn.config(state=DISABLED)  # prevent restart until fully stopped
        self.stop_btn.config(state=DISABLED)

    # ---------------------- Config Save/Load ----------------------
    def save_config(self):
        config = {
            'smtp': {
                'server': self.smtp_server.get(),
                'port': self.smtp_port.get(),
                'use_ssl': self.use_ssl.get(),
                'use_tls': self.use_tls.get(),
                'username': self.smtp_user.get(),
                'password': self.smtp_pass.get(),
                'from_email': self.from_email.get(),
                'timeout': self.smtp_timeout.get()
            },
            'content': {
                'subject': self.subject_entry.get(),
                'body': self.body_text.get(1.0, END),
                'is_html': self.is_html.get(),
                'attachments': list(self.attachments_listbox.get(0, END))
            },
            'controls': {
                'limit': self.limit_send.get(),
                'threads': self.thread_count.get(),
                'delay': self.send_delay.get()
            },
            'recipients': self.recipients_text.get(1.0, END)
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            self.log("Configuration saved.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {e}")

    def load_config(self):
        if not os.path.exists(self.config_file):
            return
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            # SMTP
            smtp = config.get('smtp', {})
            self.smtp_server.delete(0, END); self.smtp_server.insert(0, smtp.get('server', ''))
            self.smtp_port.delete(0, END); self.smtp_port.insert(0, smtp.get('port', '587'))
            self.use_ssl.set(smtp.get('use_ssl', False))
            self.use_tls.set(smtp.get('use_tls', True))
            self.smtp_user.delete(0, END); self.smtp_user.insert(0, smtp.get('username', ''))
            self.smtp_pass.delete(0, END); self.smtp_pass.insert(0, smtp.get('password', ''))
            self.from_email.delete(0, END); self.from_email.insert(0, smtp.get('from_email', ''))
            self.smtp_timeout.delete(0, END); self.smtp_timeout.insert(0, smtp.get('timeout', '30'))

            # Content
            cnt = config.get('content', {})
            self.subject_entry.delete(0, END); self.subject_entry.insert(0, cnt.get('subject', ''))
            self.body_text.delete(1.0, END); self.body_text.insert(1.0, cnt.get('body', ''))
            self.is_html.set(cnt.get('is_html', False))
            self.attachments_listbox.delete(0, END)
            for att in cnt.get('attachments', []):
                if os.path.exists(att):
                    self.attachments_listbox.insert(END, att)

            # Controls
            ctrl = config.get('controls', {})
            self.limit_send.delete(0, END); self.limit_send.insert(0, ctrl.get('limit', '0'))
            self.thread_count.delete(0, END); self.thread_count.insert(0, ctrl.get('threads', '3'))
            self.send_delay.delete(0, END); self.send_delay.insert(0, ctrl.get('delay', '0.5'))

            # Recipients
            self.recipients_text.delete(1.0, END)
            self.recipients_text.insert(1.0, config.get('recipients', ''))
            self.log("Configuration loaded.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config: {e}")

    def on_closing(self):
        if self.workers and any(w.is_alive() for w in self.workers):
            if messagebox.askyesno("Confirm Exit", "Sending in progress. Stop and exit?"):
                self.stop_booming()
                self.root.destroy()
        else:
            self.root.destroy()


# ----------------------------------------------------------------------
if __name__ == "__main__":
    root = Tk()
    app = EmailBoomerApp(root)
    root.mainloop()