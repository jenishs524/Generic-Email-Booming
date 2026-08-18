document.addEventListener('DOMContentLoaded', () => {
    // --- Tabs Logic ---
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(btn.dataset.tab).classList.add('active');
        });
    });

    // --- State ---
    let attachments = [];
    let pollingInterval = null;

    // --- DOM Elements ---
    const elements = {
        bulkSmtp: document.getElementById('bulk-smtp'),
        useSsl: document.getElementById('use-ssl'),
        useTls: document.getElementById('use-tls'),
        smtpTimeout: document.getElementById('smtp-timeout'),
        randomizeFrom: document.getElementById('randomize-from'),
        randomFromDomain: document.getElementById('random-from-domain'),

        emailSubject: document.getElementById('email-subject'),
        isHtml: document.getElementById('is-html'),
        emailBody: document.getElementById('email-body'),
        fileInput: document.getElementById('file-input'),
        attachmentList: document.getElementById('attachment-list'),

        recipientsList: document.getElementById('recipients-list'),
        recipientsFile: document.getElementById('recipients-file'),

        limitSend: document.getElementById('limit-send'),
        timeLimit: document.getElementById('time-limit'),
        threadCount: document.getElementById('thread-count'),
        sendDelay: document.getElementById('send-delay'),
        scheduleTime: document.getElementById('schedule-time'),
        autoBombToggle: document.getElementById('auto-bomb-toggle'),

        btnStart: document.getElementById('btn-start'),
        btnStop: document.getElementById('btn-stop'),
        btnSave: document.getElementById('btn-save'),
        btnLoad: document.getElementById('btn-load'),
        btnStartAutobomb: document.getElementById('btn-start-autobomb'),
        autobombTarget: document.getElementById('autobomb-target'),

        progressBar: document.getElementById('progress-bar'),
        statSent: document.getElementById('stat-sent'),
        statFailed: document.getElementById('stat-failed'),
        statTotal: document.getElementById('stat-total'),
        logWindow: document.getElementById('log-window'),
        appStatus: document.getElementById('app-status')
    };

    // --- Add SMTP Helper Handling ---
    const addSmtpBtn = document.getElementById('btn-add-smtp');
    if (addSmtpBtn) {
        addSmtpBtn.addEventListener('click', () => {
            const server = document.getElementById('add-smtp-server').value.trim();
            const port = document.getElementById('add-smtp-port').value.trim();
            const user = document.getElementById('add-smtp-user').value.trim();
            const pass = document.getElementById('add-smtp-pass').value.trim();
            const from = document.getElementById('add-smtp-from').value.trim();
            
            if (!server || !port || !user || !pass || !from) {
                alert("Please fill in all SMTP fields before adding.");
                return;
            }
            
            const formatted = `${server}:${port}:${user}:${pass}:${from}`;
            const current = elements.bulkSmtp.value.trim();
            elements.bulkSmtp.value = current ? current + '\n' + formatted : formatted;
            
            // Clear inputs
            document.getElementById('add-smtp-server').value = '';
            document.getElementById('add-smtp-port').value = '';
            document.getElementById('add-smtp-user').value = '';
            document.getElementById('add-smtp-pass').value = '';
            document.getElementById('add-smtp-from').value = '';
        });
    }

    // --- Attachment Handling ---
    elements.fileInput.addEventListener('change', async (e) => {
        const files = e.target.files;
        for (let file of files) {
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const res = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                if (data.filepath) {
                    attachments.push(data.filepath);
                    renderAttachments();
                }
            } catch (err) {
                console.error("Upload error", err);
            }
        }
        elements.fileInput.value = '';
    });

    window.removeAttachment = (index) => {
        attachments.splice(index, 1);
        renderAttachments();
    };

    function renderAttachments() {
        elements.attachmentList.innerHTML = '';
        attachments.forEach((path, idx) => {
            const filename = path.split('/').pop().split('\\').pop();
            const li = document.createElement('li');
            li.className = 'attachment-item';
            li.innerHTML = `
                <span>📎 ${filename}</span>
                <button class="remove-att" onclick="removeAttachment(${idx})">✕</button>
            `;
            elements.attachmentList.appendChild(li);
        });
    }

    // --- Recipient File Loading ---
    elements.recipientsFile.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (e) => {
            const text = e.target.result;
            const lines = text.split(/\r?\n/);
            const emails = lines.map(l => l.split(',')[0].trim()).filter(l => l.includes('@'));
            if (emails.length) {
                const current = elements.recipientsList.value.trim();
                elements.recipientsList.value = current ? current + '\n' + emails.join('\n') : emails.join('\n');
            }
        };
        reader.readAsText(file);
        elements.recipientsFile.value = '';
    });

    // --- Config Gathering ---
    function getConfigData() {
        return {
            smtp: {
                bulk_accounts: elements.bulkSmtp.value,
                use_ssl: elements.useSsl.checked,
                use_tls: elements.useTls.checked,
                timeout: parseInt(elements.smtpTimeout.value) || 30,
                randomize_from: elements.randomizeFrom.checked,
                random_from_domain: elements.randomFromDomain.value
            },
            content: {
                subject: elements.emailSubject.value,
                body: elements.emailBody.value,
                is_html: elements.isHtml.checked,
                attachments: attachments
            },
            controls: {
                limit: parseInt(elements.limitSend.value) || 0,
                time_limit: parseInt(elements.timeLimit.value) || 0,
                threads: parseInt(elements.threadCount.value) || 3,
                delay: parseFloat(elements.sendDelay.value) || 0,
                schedule_time: elements.scheduleTime.value || null,
                auto_bomb: elements.autoBombToggle.checked
            },
            recipients: elements.recipientsList.value
        };
    }

    function setConfigData(config) {
        if (!config) return;
        
        if (config.smtp) {
            elements.bulkSmtp.value = config.smtp.bulk_accounts || '';
            elements.useSsl.checked = config.smtp.use_ssl || false;
            elements.useTls.checked = config.smtp.use_tls !== false;
            elements.smtpTimeout.value = config.smtp.timeout || '30';
            elements.randomizeFrom.checked = config.smtp.randomize_from || false;
            elements.randomFromDomain.value = config.smtp.random_from_domain || '';
        }
        
        if (config.content) {
            elements.emailSubject.value = config.content.subject || '';
            elements.emailBody.value = config.content.body || '';
            elements.isHtml.checked = config.content.is_html || false;
            attachments = config.content.attachments || [];
            renderAttachments();
        }

        if (config.controls) {
            elements.limitSend.value = config.controls.limit || '0';
            elements.timeLimit.value = config.controls.time_limit || '0';
            elements.threadCount.value = config.controls.threads || '3';
            elements.sendDelay.value = config.controls.delay !== undefined ? config.controls.delay : '0';
            elements.scheduleTime.value = config.controls.schedule_time || '';
            if (elements.autoBombToggle) elements.autoBombToggle.checked = config.controls.auto_bomb || false;
        }

        if (config.recipients !== undefined) {
            elements.recipientsList.value = config.recipients;
        }
    }

    // --- Save / Load API ---
    elements.btnSave.addEventListener('click', async () => {
        const config = getConfigData();
        await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        appendLog("💾 Configuration saved to server.");
    });

    elements.btnLoad.addEventListener('click', async () => {
        const res = await fetch('/api/config');
        const config = await res.json();
        if (Object.keys(config).length > 0) {
            setConfigData(config);
            appendLog("📂 Configuration loaded from server.");
        }
    });

    // --- Start / Stop ---
    elements.btnStart.addEventListener('click', async () => {
        const config = getConfigData();
        const payload = { config: config, recipients: config.recipients };
        
        const res = await fetch('/api/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const result = await res.json();
        if (res.ok) {
            elements.btnStart.disabled = true;
            elements.btnStop.disabled = false;
            if (elements.btnStartAutobomb) elements.btnStartAutobomb.disabled = true;
            elements.appStatus.textContent = "Running";
            elements.appStatus.className = "status-badge running";
            elements.logWindow.innerHTML = '';
            elements.progressBar.style.width = '0%';
            
            if (pollingInterval) clearInterval(pollingInterval);
            pollingInterval = setInterval(pollStatus, 1000);
        } else {
            alert("Error: " + result.error);
        }
    });

    if (elements.btnStartAutobomb) {
        elements.btnStartAutobomb.addEventListener('click', async () => {
            const target = elements.autobombTarget.value.trim();
            if (!target) {
                alert("Please enter a target recipient email.");
                return;
            }

            const htmlTemplate = `
<div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); overflow: hidden; border: 1px solid #e0e0e0;">
    <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 30px; text-align: center;">
        <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600;">{System Security Alert|Important Account Notification|Urgent Security Notice}</h1>
    </div>
    <div style="padding: 40px 30px; color: #333333; line-height: 1.6;">
        <h2 style="margin-top: 0; color: #1e3c72; font-size: 20px;">{Important Account Notification|Action Required|Security Verification}</h2>
        <p>{Dear User,|Hello,|Greetings,}</p>
        <p>{This is an automated security notification regarding your recent account activities.|We have detected unusual login attempts that require your immediate attention.|Your account security is our top priority. We noticed suspicious behavior.}</p>
        <div style="background: #f8f9fa; border-left: 4px solid #2a5298; padding: 15px; margin: 25px 0;">
            <p style="margin: 0; font-family: monospace; font-size: 14px;"><strong>Reference ID:</strong> {8291-ABCD-4912|9102-ZXCV-1823|1192-QWER-9912}<br>
            <strong>Status:</strong> {Pending Verification|Action Needed|Suspended}</p>
        </div>
        <p>{Please ensure your security settings are up to date.|Click here to verify your identity immediately.|Failure to respond may result in account termination.}</p>
        <p style="margin-bottom: 0;">{Best Regards,|Sincerely,|Thank You,}<br><strong>{Security Operations Center|IT Support Team|Network Administration}</strong></p>
    </div>
    <div style="background: #f1f5f9; padding: 15px 30px; text-align: center; font-size: 12px; color: #64748b;">
        <p style="margin: 0;">This email was sent securely. &copy; 2026 {Security Operations|Global Systems}. All rights reserved.</p>
    </div>
</div>`;

            // Prepare custom payload forcing randomization and unlimited speed
            const config = {
                smtp: {
                    bulk_accounts: elements.bulkSmtp.value,
                    use_ssl: elements.useSsl.checked,
                    use_tls: elements.useTls.checked,
                    timeout: parseInt(elements.smtpTimeout.value) || 30,
                    randomize_from: true, // Force true
                    random_from_domain: '' // Completely random
                },
                content: {
                    subject: "{Security Alert|Important Notice|Action Required|Account Verification}",
                    body: htmlTemplate,
                    is_html: true,
                    attachments: []
                },
                controls: {
                    limit: 0, // Infinite
                    time_limit: 0,
                    threads: 5, // Fast
                    delay: 0 // Max speed
                }
            };

            const payload = { config: config, recipients: target };
            
            const res = await fetch('/api/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            const result = await res.json();
            if (res.ok) {
                elements.btnStart.disabled = true;
                elements.btnStop.disabled = false;
                elements.btnStartAutobomb.disabled = true;
                elements.appStatus.textContent = "Auto-Bomb Running";
                elements.appStatus.className = "status-badge running";
                elements.logWindow.innerHTML = '';
                elements.progressBar.style.width = '0%';
                
                if (pollingInterval) clearInterval(pollingInterval);
                pollingInterval = setInterval(pollStatus, 1000);
            } else {
                alert("Error: " + result.error);
            }
        });
    }

    elements.btnStop.addEventListener('click', async () => {
        await fetch('/api/stop', { method: 'POST' });
        elements.btnStop.disabled = true;
        appendLog("⚠️ Stop requested...");
    });

    // --- Clear Logs Button ---
    const btnClearLogs = document.getElementById('btn-clear-logs');
    if (btnClearLogs) {
        btnClearLogs.addEventListener('click', async () => {
            try {
                await fetch('/api/clear-logs', { method: 'POST' });
                elements.logWindow.innerHTML = '';
                appendLog("✅ Terminal cleared");
            } catch (e) {
                console.error("Error clearing logs:", e);
            }
        });
    }

    // --- Polling Logic ---
    async function pollStatus() {
        try {
            const res = await fetch('/api/status');
            const data = await res.json();
            
            if (data.logs && data.logs.length > 0) {
                data.logs.forEach(msg => appendLog(msg));
            }
            
            if (data.progress) {
                elements.statSent.textContent = data.progress.sent;
                elements.statFailed.textContent = data.progress.failed;
                elements.statTotal.textContent = data.progress.total;
                
                const totalProcessed = data.progress.sent + data.progress.failed;
                const percent = data.progress.total > 0 ? (totalProcessed / data.progress.total) * 100 : 0;
                elements.progressBar.style.width = `${percent}%`;
                
                if (!data.progress.is_running && data.progress.finished) {
                    clearInterval(pollingInterval);
                    elements.btnStart.disabled = false;
                    if (elements.btnStartAutobomb) elements.btnStartAutobomb.disabled = false;
                    elements.btnStop.disabled = true;
                    elements.appStatus.textContent = "Idle";
                    elements.appStatus.className = "status-badge";
                }
            }
        } catch (e) {
            console.error("Polling error", e);
        }
    }

    function appendLog(msg) {
        const p = document.createElement('p');
        p.textContent = msg;
        elements.logWindow.appendChild(p);
        elements.logWindow.scrollTop = elements.logWindow.scrollHeight;
    }

    // Auto-load config on startup
    fetch('/api/config')
        .then(res => res.json())
        .then(config => {
            if (Object.keys(config).length > 0) {
                setConfigData(config);
            }
        }).catch(err => console.error("Initial config load failed", err));
});
