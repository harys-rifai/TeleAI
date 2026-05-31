// TeleAI Frontend Javascript Application

document.addEventListener('DOMContentLoaded', () => {
    // 1. Navigation Setup
    const menuItems = document.querySelectorAll('.sidebar-item');
    const panels = document.querySelectorAll('.tab-panel');
    const pageTitle = document.getElementById('page-title-text');
    
    const pageTitles = {
        'overview': 'Dashboard Overview',
        'accounts': 'Telegram Accounts',
        'messages': 'Chat History Logs',
        'scheduler': 'Message Scheduler',
        'ai': 'AI Assistant settings',
        'weather': 'Weather Automation Bot',
        'exports': 'Export Jobs & Reports'
    };

    menuItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const tab = item.getAttribute('data-tab');
            
            // Toggle active menu
            menuItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            
            // Toggle active panel
            panels.forEach(p => p.classList.remove('active'));
            document.getElementById(`panel-${tab}`).classList.add('active');
            
            // Update title
            pageTitle.textContent = pageTitles[tab] || 'TeleAI Dashboard';
            
            // Load tab specific data
            loadTabData(tab);
        });
    });

    // 2. Charts Initialization
    initCharts();

    // 3. Initial Load
    loadTabData('overview');
});

// CSRF Utility
function getHeaders() {
    const csrf = document.getElementById('csrf-token').value;
    return {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf
    };
}

// Toast Notifications Helper
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = 'toast';
    
    let icon = '<i class="fa-solid fa-circle-info" style="color: var(--neon-blue);"></i>';
    if (type === 'success') {
        icon = '<i class="fa-solid fa-circle-check" style="color: var(--neon-green);"></i>';
        toast.style.borderColor = 'var(--neon-green)';
    } else if (type === 'error') {
        icon = '<i class="fa-solid fa-circle-exclamation" style="color: var(--neon-red);"></i>';
        toast.style.borderColor = 'var(--neon-red)';
    } else if (type === 'warning') {
        icon = '<i class="fa-solid fa-triangle-exclamation" style="color: var(--neon-violet);"></i>';
        toast.style.borderColor = 'var(--neon-violet)';
    }

    toast.innerHTML = `${icon} <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease-out reverse';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Routing Tab Loads
function loadTabData(tab) {
    if (tab === 'overview') {
        loadOverviewStats();
        loadAnalyticsCharts();
    } else if (tab === 'accounts') {
        loadTelegramAccounts();
    } else if (tab === 'messages') {
        loadMessages();
    } else if (tab === 'scheduler') {
        loadSchedules();
        loadAccountsDropdown('schedule-account');
    } else if (tab === 'ai') {
        loadAIConfig();
    } else if (tab === 'weather') {
        loadWeatherLocations();
    } else if (tab === 'exports') {
        loadExportJobs();
    }
}

// Chart Variables
let volumeChart = null;
let distChart = null;

function initCharts() {
    const ctxVol = document.getElementById('chart-volume').getContext('2d');
    const ctxDist = document.getElementById('chart-distribution').getContext('2d');

    // Default configuration for Neon style charts
    volumeChart = new Chart(ctxVol, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [
                {
                    label: 'Outbound Messages',
                    borderColor: '#00f0ff',
                    backgroundColor: 'rgba(0, 240, 255, 0.05)',
                    borderWidth: 2,
                    tension: 0.4,
                    data: [0, 0, 0, 0, 0, 0, 0],
                    fill: true
                },
                {
                    label: 'Inbound Messages',
                    borderColor: '#d000ff',
                    backgroundColor: 'rgba(208, 0, 255, 0.05)',
                    borderWidth: 2,
                    tension: 0.4,
                    data: [0, 0, 0, 0, 0, 0, 0],
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#8d9bb0', font: { family: 'Outfit' } } }
            },
            scales: {
                x: { grid: { color: 'rgba(255,255,255,0.03)' }, ticks: { color: '#8d9bb0' } },
                y: { grid: { color: 'rgba(255,255,255,0.03)' }, ticks: { color: '#8d9bb0' } }
            }
        }
    });

    distChart = new Chart(ctxDist, {
        type: 'doughnut',
        data: {
            labels: ['Successful Sent', 'Failed Sent', 'Inbound'],
            datasets: [{
                data: [0, 0, 0],
                backgroundColor: ['#39ff14', '#ff3131', '#00f0ff'],
                borderColor: '#13141f',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#8d9bb0', font: { family: 'Outfit' } } }
            }
        }
    });
}

// ---------------------- OVERVIEW PANEL ----------------------

function loadOverviewStats() {
    fetch('/dashboard/api/stats/')
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const s = data.stats;
                document.getElementById('stat-accounts-active').textContent = `${s.accounts.active} / ${s.accounts.total}`;
                document.getElementById('stat-messages-sent').textContent = s.messages.sent;
                document.getElementById('stat-messages-received').textContent = s.messages.received;
                document.getElementById('stat-schedules-active').textContent = s.schedules.active;
            }
        });
}

function loadAnalyticsCharts() {
    fetch('/api/analytics/metrics/?days=7')
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const metrics = data.data;
                const daily = metrics.daily;
                
                if (daily.length > 0) {
                    const labels = daily.map(d => d.day);
                    const outbound = daily.map(d => d.outbound_count);
                    const inbound = daily.map(d => d.inbound_count);
                    
                    volumeChart.data.labels = labels;
                    volumeChart.data.datasets[0].data = outbound;
                    volumeChart.data.datasets[1].data = inbound;
                    volumeChart.update();
                }
                
                const sum = metrics.summary;
                distChart.data.datasets[0].data = [sum.success, sum.failed, metrics.daily.reduce((acc, curr) => acc + curr.inbound_count, 0)];
                distChart.update();
            }
        });
}

// ---------------------- ACCOUNTS PANEL ----------------------

function loadTelegramAccounts() {
    fetch('/api/telegram/accounts/')
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const accounts = data.accounts;
                const tbody = document.getElementById('accounts-table-body');
                tbody.innerHTML = '';
                
                if (accounts.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No accounts registered. Click connect to register.</td></tr>';
                    return;
                }
                
                accounts.forEach(acc => {
                    const statusText = acc.is_active ? 
                        '<span style="color: var(--neon-green);"><i class="fa-solid fa-circle-check"></i> Connected</span>' : 
                        '<span style="color: var(--text-muted);"><i class="fa-solid fa-circle"></i> Inactive</span>';
                        
                    const fileText = acc.has_session ? 
                        '<span style="color: var(--neon-blue); font-size: 0.8rem;"><i class="fa-solid fa-database"></i> Session Saved</span>' : 
                        '<span style="color: var(--neon-red); font-size: 0.8rem;"><i class="fa-solid fa-triangle-exclamation"></i> Unauthenticated</span>';
                        
                    const deleteBtn = `<button class="btn-sm btn-danger-neon" onclick="deleteAccount(${acc.id})"><i class="fa-solid fa-trash-can"></i> Delete</button>`;
                    
                    tbody.innerHTML += `
                        <tr>
                            <td><strong>${acc.user_email}</strong></td>
                            <td><code>${acc.phone_number}</code></td>
                            <td><code>${acc.api_id}</code></td>
                            <td>${statusText}</td>
                            <td>${fileText}</td>
                            <td>${deleteBtn}</td>
                        </tr>
                    `;
                });
            }
        });
}

function openConnectModal() {
    document.getElementById('connect-modal').style.display = 'flex';
    // Reset steps
    document.getElementById('auth-step-1').style.display = 'block';
    document.getElementById('auth-step-2').style.display = 'none';
    document.getElementById('auth-step-3').style.display = 'none';
}

function closeConnectModal() {
    document.getElementById('connect-modal').style.display = 'none';
}

function requestAuthCode() {
    const apiId = document.getElementById('auth-api-id').value;
    const apiHash = document.getElementById('auth-api-hash').value;
    const phone = document.getElementById('auth-phone').value;
    
    if (!apiId || !apiHash || !phone) {
        showToast('Please fill all fields', 'warning');
        return;
    }
    
    showToast('Connecting to Telegram, sending verification code...', 'info');
    
    fetch('/api/telegram/accounts/send-code/', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
            api_id: apiId,
            api_hash: apiHash,
            phone_number: phone
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            document.getElementById('auth-step-1').style.display = 'none';
            document.getElementById('auth-step-2').style.display = 'block';
        } else {
            showToast(data.error, 'error');
        }
    });
}

function verifyAuthCode() {
    const code = document.getElementById('auth-code').value;
    if (!code) {
        showToast('Enter the code received', 'warning');
        return;
    }
    
    fetch('/api/telegram/accounts/verify-code/', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ code: code })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            if (data.status === 'needs_2fa') {
                showToast(data.message, 'warning');
                document.getElementById('auth-step-2').style.display = 'none';
                document.getElementById('auth-step-3').style.display = 'block';
            } else {
                showToast(data.message, 'success');
                closeConnectModal();
                loadTelegramAccounts();
            }
        } else {
            showToast(data.error, 'error');
        }
    });
}

function verifyAuth2FA() {
    const password = document.getElementById('auth-password').value;
    if (!password) {
        showToast('Cloud password required', 'warning');
        return;
    }
    
    fetch('/api/telegram/accounts/verify-2fa/', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ password: password })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            closeConnectModal();
            loadTelegramAccounts();
        } else {
            showToast(data.error, 'error');
        }
    });
}

function deleteAccount(id) {
    if (!confirm('Are you sure you want to delete this credentials configuration?')) return;
    
    fetch(`/api/telegram/accounts/${id}/`, {
        method: 'DELETE',
        headers: getHeaders()
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            loadTelegramAccounts();
        } else {
            showToast(data.error, 'error');
        }
    });
}

// Helper: load active accounts to dropdown lists
function loadAccountsDropdown(selectId) {
    fetch('/api/telegram/accounts/')
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const accounts = data.accounts.filter(a => a.is_active);
                const select = document.getElementById(selectId);
                select.innerHTML = '';
                
                if (accounts.length === 0) {
                    select.innerHTML = '<option value="">No active accounts connected</option>';
                    return;
                }
                
                accounts.forEach(acc => {
                    select.innerHTML += `<option value="${acc.id}">${acc.phone_number}</option>`;
                });
            }
        });
}

// ---------------------- LOG MESSAGES PANEL ----------------------

function loadMessages() {
    const q = document.getElementById('messages-search').value;
    const direction = document.getElementById('messages-direction-filter').value;
    
    fetch(`/api/messages/logs/?q=${encodeURIComponent(q)}&direction=${direction}`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const logs = data.logs;
                const tbody = document.getElementById('messages-table-body');
                tbody.innerHTML = '';
                
                if (logs.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted);">No messages found matching search criteria.</td></tr>';
                    return;
                }
                
                logs.forEach(log => {
                    const directionBadge = log.direction === 'outbound' ? 
                        '<span style="color: var(--neon-blue);"><i class="fa-solid fa-arrow-right-from-bracket"></i> Outbound</span>' : 
                        '<span style="color: var(--neon-violet);"><i class="fa-solid fa-arrow-right-to-bracket"></i> Inbound</span>';
                        
                    const statusText = log.status === 'success' ? 
                        '<span style="color: var(--neon-green); font-size: 0.85rem;"><i class="fa-solid fa-check"></i> Success</span>' : 
                        '<span style="color: var(--neon-red); font-size: 0.85rem;"><i class="fa-solid fa-xmark"></i> Failed</span>';
                        
                    tbody.innerHTML += `
                        <tr>
                            <td><code>${log.sent_at}</code></td>
                            <td><code>${log.phone_number}</code></td>
                            <td>${directionBadge}</td>
                            <td><code>${log.chat_id}</code></td>
                            <td>${log.chat_title}</td>
                            <td style="max-width: 320px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${log.message_text.replace(/"/g, '&quot;')}">${log.message_text}</td>
                            <td>${statusText}</td>
                        </tr>
                    `;
                });
            }
        });
}

// ---------------------- MESSAGE SCHEDULER PANEL ----------------------

function toggleScheduleFields() {
    const type = document.getElementById('schedule-type').value;
    const intervalGroup = document.getElementById('schedule-interval-group');
    const cronGroup = document.getElementById('schedule-cron-group');
    
    intervalGroup.style.display = type === 'interval' ? 'block' : 'none';
    cronGroup.style.display = type === 'cron' ? 'block' : 'none';
}

function loadSchedules() {
    fetch('/api/scheduler/messages/')
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const schedules = data.schedules;
                const tbody = document.getElementById('schedules-table-body');
                tbody.innerHTML = '';
                
                if (schedules.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No message schedules set.</td></tr>';
                    return;
                }
                
                schedules.forEach(s => {
                    const statusBadge = s.status === 'active' ? 
                        '<span style="color: var(--neon-green);"><i class="fa-solid fa-spinner fa-spin"></i> Active</span>' : (
                            s.status === 'paused' ? '<span style="color: var(--text-muted);"><i class="fa-solid fa-pause"></i> Paused</span>' :
                            '<span style="color: var(--neon-blue);"><i class="fa-solid fa-check-double"></i> Finished</span>'
                        );
                        
                    const typeDisplay = s.schedule_type === 'cron' ? `Cron (<code>${s.cron_expression}</code>)` : (
                        s.schedule_type === 'interval' ? `Interval (${s.interval_seconds}s)` : 'Once'
                    );
                    
                    const actionBtnText = s.status === 'active' ? 'Pause' : 'Resume';
                    const actionBtnAction = s.status === 'active' ? 'pause' : 'resume';
                    
                    let actions = `
                        <button class="btn-sm btn-primary-neon" style="margin-right: 5px;" onclick="triggerSchedule(${s.id}, '${actionBtnAction}')">${actionBtnText}</button>
                        <button class="btn-sm btn-success-neon" style="margin-right: 5px;" onclick="triggerSchedule(${s.id}, 'trigger')">Run Now</button>
                        <button class="btn-sm btn-danger-neon" onclick="deleteSchedule(${s.id})"><i class="fa-solid fa-trash-can"></i></button>
                    `;
                    
                    if (s.status === 'completed') {
                        actions = `<button class="btn-sm btn-danger-neon" onclick="deleteSchedule(${s.id})"><i class="fa-solid fa-trash-can"></i></button>`;
                    }
                    
                    tbody.innerHTML += `
                        <tr>
                            <td><strong>${s.target_chat_id}</strong><br><small style="color: var(--text-muted);">${s.message_text.substring(0, 30)}...</small></td>
                            <td>${typeDisplay}</td>
                            <td><code>${s.next_run_at || 'N/A'}</code></td>
                            <td>${statusBadge}</td>
                            <td style="white-space: nowrap;">${actions}</td>
                        </tr>
                    `;
                });
            }
        });
}

function saveSchedule(e) {
    e.preventDefault();
    const account = document.getElementById('schedule-account').value;
    const target = document.getElementById('schedule-target').value;
    const text = document.getElementById('schedule-text').value;
    const type = document.getElementById('schedule-type').value;
    const interval = document.getElementById('schedule-interval').value;
    const cron = document.getElementById('schedule-cron').value;
    
    if (!account) {
        showToast('Please select a sender account', 'warning');
        return;
    }
    
    fetch('/api/scheduler/messages/', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
            telegram_account_id: account,
            target_chat_id: target,
            message_text: text,
            schedule_type: type,
            interval_seconds: interval,
            cron_expression: cron
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            document.getElementById('scheduler-form').reset();
            toggleScheduleFields();
            loadSchedules();
        } else {
            showToast(data.error, 'error');
        }
    });
}

function triggerSchedule(id, action) {
    fetch(`/api/scheduler/messages/${id}/`, {
        method: 'PUT',
        headers: getHeaders(),
        body: JSON.stringify({ action: action })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            loadSchedules();
        } else {
            showToast(data.error, 'error');
        }
    });
}

function deleteSchedule(id) {
    if (!confirm('Are you sure you want to delete this schedule?')) return;
    
    fetch(`/api/scheduler/messages/${id}/`, {
        method: 'DELETE',
        headers: getHeaders()
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            loadSchedules();
        } else {
            showToast(data.error, 'error');
        }
    });
}

// ---------------------- AI ASSISTANT PANEL ----------------------

function loadAIConfig() {
    fetch('/api/ai/configs/')
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const config = data.config;
                document.getElementById('ai-model').value = config.model_name;
                document.getElementById('ai-prompt').value = config.system_prompt;
                document.getElementById('ai-temp').value = config.temperature;
                document.getElementById('ai-temp-val').textContent = config.temperature;
                document.getElementById('ai-auto-reply').checked = config.is_auto_reply_enabled;
                document.getElementById('ai-base-url').value = config.api_base_url || '';
                
                // Show key placeholder if configured
                const keyInput = document.getElementById('ai-key');
                if (config.has_custom_key) {
                    keyInput.placeholder = '****************** (Saved)';
                } else {
                    keyInput.placeholder = 'sk-...';
                }
            }
        });
        
    // Range Slider update label
    document.getElementById('ai-temp').addEventListener('input', (e) => {
        document.getElementById('ai-temp-val').textContent = e.target.value;
    });
 }

function saveAIConfig(e) {
    e.preventDefault();
    const key = document.getElementById('ai-key').value;
    const model = document.getElementById('ai-model').value;
    const prompt = document.getElementById('ai-prompt').value;
    const temp = document.getElementById('ai-temp').value;
    const autoReply = document.getElementById('ai-auto-reply').checked;
    const baseUrl = document.getElementById('ai-base-url').value;
    
    fetch('/api/ai/configs/', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
            api_key: key,
            model_name: model,
            system_prompt: prompt,
            temperature: temp,
            is_auto_reply_enabled: autoReply,
            api_base_url: baseUrl
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            loadAIConfig();
        } else {
            showToast(data.error, 'error');
        }
    });
 }

function testAIPrompt() {
    const prompt = document.getElementById('ai-test-input').value;
    if (!prompt) {
        showToast('Type a prompt to test.', 'warning');
        return;
    }
    
    const output = document.getElementById('ai-test-output');
    output.textContent = 'Generating AI response, please wait...';
    
    fetch('/api/ai/test-prompt/', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ prompt: prompt })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            output.textContent = data.reply;
        } else {
            output.textContent = `Error: ${data.error}`;
        }
    });
}

// ---------------------- WEATHER PANEL ----------------------

function loadWeatherLocations() {
    fetch('/api/weather/locations/')
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const locations = data.locations;
                const tbody = document.getElementById('weather-table-body');
                tbody.innerHTML = '';
                
                if (locations.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No weather alerts configured.</td></tr>';
                    return;
                }
                
                locations.forEach(loc => {
                    const statusText = loc.is_active ? 
                        '<span style="color: var(--neon-green);"><i class="fa-solid fa-power-off"></i> Active</span>' : 
                        '<span style="color: var(--text-muted);"><i class="fa-solid fa-power-off"></i> Inactive</span>';
                        
                    const toggleBtnText = loc.is_active ? 'Deactivate' : 'Activate';
                    
                    tbody.innerHTML += `
                        <tr>
                            <td><strong>${loc.location_name}</strong><br><small style="color: var(--text-muted);">GPS: (${loc.latitude.toFixed(3)}, ${loc.longitude.toFixed(3)})</small></td>
                            <td><code>${loc.target_chat_id}</code></td>
                            <td><code>${loc.schedule_time}</code></td>
                            <td>${statusText}</td>
                            <td style="white-space: nowrap;">
                                <button class="btn-sm btn-primary-neon" style="margin-right: 5px;" onclick="toggleWeather(${loc.id})">${toggleBtnText}</button>
                                <button class="btn-sm btn-success-neon" style="margin-right: 5px;" onclick="getRealtimeWeather(${loc.id})">Realtime</button>
                                <button class="btn-sm btn-danger-neon" onclick="deleteWeather(${loc.id})"><i class="fa-solid fa-trash-can"></i></button>
                            </td>
                        </tr>
                    `;
                });
            }
        });
 }

function saveWeather(e) {
    e.preventDefault();
    const city = document.getElementById('weather-name').value;
    const chat = document.getElementById('weather-chat').value;
    const time = document.getElementById('weather-time').value;
    
    showToast('Resolving coordinates and saving weather bot...', 'info');
    
    fetch('/api/weather/locations/', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
            location_name: city,
            target_chat_id: chat,
            schedule_time: time
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            document.getElementById('weather-form').reset();
            loadWeatherLocations();
        } else {
            showToast(data.error, 'error');
        }
    });
}

function toggleWeather(id) {
    fetch(`/api/weather/locations/${id}/`, {
        method: 'PUT',
        headers: getHeaders(),
        body: JSON.stringify({ action: 'toggle' })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            loadWeatherLocations();
        } else {
            showToast(data.error, 'error');
        }
    });
}

function getRealtimeWeather(id) {
    fetch(`/api/weather/locations/${id}/`, {
        method: 'PUT',
        headers: getHeaders(),
        body: JSON.stringify({ action: 'realtime' })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
        } else {
            showToast(data.error, 'error');
        }
    });
}

function deleteWeather(id) {
    if (!confirm('Are you sure you want to delete this weather alert config?')) return;
    
    fetch(`/api/weather/locations/${id}/`, {
        method: 'DELETE',
        headers: getHeaders()
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            loadWeatherLocations();
        } else {
            showToast(data.error, 'error');
        }
    });
}

// ---------------------- EXPORTS PANEL ----------------------

function loadExportJobs() {
    fetch('/api/notifications/exports/')
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const jobs = data.jobs;
                const tbody = document.getElementById('exports-table-body');
                tbody.innerHTML = '';
                
                if (jobs.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No exports requested yet.</td></tr>';
                    return;
                }
                
                jobs.forEach(job => {
                    let statusBadge = '';
                    let action = '';
                    
                    if (job.status === 'completed') {
                        statusBadge = '<span style="color: var(--neon-green);"><i class="fa-solid fa-file-csv"></i> Completed</span>';
                        action = `<a href="${job.download_url}" class="btn-sm btn-success-neon" download style="text-decoration: none; display: inline-block;"><i class="fa-solid fa-cloud-arrow-down"></i> Download CSV</a>`;
                    } else if (job.status === 'processing') {
                        statusBadge = '<span style="color: var(--neon-violet);"><i class="fa-solid fa-cog fa-spin"></i> Processing</span>';
                    } else if (job.status === 'pending') {
                        statusBadge = '<span style="color: var(--text-muted);"><i class="fa-solid fa-clock"></i> Queued</span>';
                    } else {
                        statusBadge = '<span style="color: var(--neon-red);"><i class="fa-solid fa-circle-xmark"></i> Failed</span>';
                    }
                    
                    tbody.innerHTML += `
                        <tr>
                            <td><code>#${job.id}</code></td>
                            <td><strong>${job.export_type}</strong></td>
                            <td><code>${job.created_at}</code></td>
                            <td>${statusBadge}</td>
                            <td>${action}</td>
                        </tr>
                    `;
                });
            }
        });
}

function triggerExport() {
    showToast('Submitting message logs export request...', 'info');
    
    fetch('/api/notifications/exports/', {
        method: 'POST',
        headers: getHeaders()
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            loadExportJobs();
            // Poll for update in 3 seconds
            setTimeout(loadExportJobs, 3000);
        } else {
            showToast(data.error, 'error');
        }
    });
}
