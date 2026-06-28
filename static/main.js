document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const navItems = document.querySelectorAll('.nav-item');
    const tabContents = document.querySelectorAll('.tab-content');
    const pageTitle = document.getElementById('page-title');
    
    const extractForm = document.getElementById('extract-form');
    const channelUrlInput = document.getElementById('channel-url');
    const videoLimitInput = document.getElementById('video-limit');
    const languageCodesInput = document.getElementById('language-codes');
    const btnSubmit = document.getElementById('btn-submit');
    
    const jobStatusBadge = document.getElementById('job-status-badge');
    const progressText = document.getElementById('progress-text');
    const progressPercent = document.getElementById('progress-percent');
    const progressBarFill = document.getElementById('progress-bar-fill');
    const metricTotal = document.getElementById('metric-total');
    const metricSuccess = document.getElementById('metric-success');
    const metricUnavailable = document.getElementById('metric-unavailable');
    const logConsole = document.getElementById('log-console');
    
    const channelsList = document.getElementById('channels-list');
    const btnRefreshVault = document.getElementById('btn-refresh-vault');
    const vaultSearch = document.getElementById('vault-search');
    
    const modal = document.getElementById('transcript-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalSubtitle = document.getElementById('modal-subtitle');
    const modalContent = document.getElementById('modal-content');
    const modalClose = document.getElementById('modal-close');
    const modalCopy = document.getElementById('modal-copy');

    let currentSocket = null;
    let cachedChannels = [];

    // Navigation Tabs
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const tab = item.getAttribute('data-tab');
            navItems.forEach(i => i.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            item.classList.add('active');
            document.getElementById(`tab-${tab}`).classList.add('active');
            pageTitle.textContent = tab === 'extractor' ? 'Channel Transcript Extractor' : 'Downloads Vault';

            if (tab === 'explorer') {
                loadVaultDownloads();
            }
        });
    });

    // Form Submission
    extractForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const channelUrl = channelUrlInput.value.trim();
        if (!channelUrl) return;

        const selectedFormats = Array.from(document.querySelectorAll('input[name="format"]:checked'))
            .map(cb => cb.value);
            
        if (selectedFormats.length === 0) {
            alert('Please select at least one export format.');
            return;
        }

        const limitVal = videoLimitInput.value ? parseInt(videoLimitInput.value) : None;
        const languages = languageCodesInput.value.split(',').map(s => s.trim()).filter(Boolean);

        // Reset UI Console
        resetConsole();
        setJobStatus('running', 'Processing');
        btnSubmit.disabled = true;
        btnSubmit.innerHTML = `<span class="status-dot online"></span> Initializing Extraction...`;

        try {
            const res = await fetch('/api/extract', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    channel_url: channelUrl,
                    formats: selectedFormats,
                    languages: languages,
                    limit: limitVal
                })
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Failed to initialize job');
            }

            const data = await res.json();
            connectWebSocket(data.job_id);

        } catch (err) {
            appendLog(`Error: ${err.message}`, 'warn');
            setJobStatus('idle', 'Error');
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><polyline points="8 17 12 21 16 17"></polyline><line x1="12" y1="12" x2="12" y2="21"></line><path d="M20.88 18.09A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.29"></path></svg> Extract Transcripts & Metadata`;
        }
    });

    function connectWebSocket(jobId) {
        if (currentSocket) {
            currentSocket.close();
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/progress/${jobId}`;
        currentSocket = new WebSocket(wsUrl);

        currentSocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleProgressEvent(data);
        };

        currentSocket.onerror = (err) => {
            appendLog('WebSocket connection error', 'warn');
        };

        currentSocket.onclose = () => {
            // Socket closed
        };
    }

    function handleProgressEvent(data) {
        if (data.type === 'status') {
            progressText.textContent = data.message;
            appendLog(data.message, 'info');
        } else if (data.type === 'progress') {
            const pct = data.percentage || 0;
            progressBarFill.style.width = `${pct}%`;
            progressPercent.textContent = `${pct}%`;
            progressText.textContent = `Processing (${data.current}/${data.total}): ${data.video_title}`;
            metricTotal.textContent = data.total;
            
            appendLog(`[${data.current}/${data.total}] ${data.video_title}`, 'info');
        } else if (data.type === 'complete') {
            const res = data.result;
            progressBarFill.style.width = '100%';
            progressPercent.textContent = '100%';
            progressText.textContent = `Completed extraction for ${res.channel_title}`;
            
            metricTotal.textContent = res.total;
            metricSuccess.textContent = res.success;
            metricUnavailable.textContent = res.unavailable;
            
            setJobStatus('completed', 'Completed');
            appendLog(`✅ Finished! ${res.success} transcripts saved into vault.`, 'success');
            
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><polyline points="8 17 12 21 16 17"></polyline><line x1="12" y1="12" x2="12" y2="21"></line><path d="M20.88 18.09A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.29"></path></svg> Extract Transcripts & Metadata`;
            
            // Auto refresh explorer
            loadVaultDownloads();
        } else if (data.type === 'error') {
            appendLog(`❌ Error: ${data.message}`, 'warn');
            setJobStatus('idle', 'Failed');
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = `Extract Transcripts & Metadata`;
        }
    }

    function resetConsole() {
        progressBarFill.style.width = '0%';
        progressPercent.textContent = '0%';
        progressText.textContent = 'Starting job...';
        metricTotal.textContent = '0';
        metricSuccess.textContent = '0';
        metricUnavailable.textContent = '0';
        logConsole.innerHTML = '';
    }

    function setJobStatus(statusClass, label) {
        jobStatusBadge.className = `status-pill ${statusClass}`;
        jobStatusBadge.textContent = label;
    }

    function appendLog(msg, type = 'info') {
        const line = document.createElement('div');
        line.className = `log-line ${type}`;
        line.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
        logConsole.appendChild(line);
        logConsole.scrollTop = logConsole.scrollHeight;
    }

    // Vault Downloads Explorer
    btnRefreshVault.addEventListener('click', loadVaultDownloads);

    vaultSearch.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        const filtered = cachedChannels.filter(c => 
            c.channel_title.toLowerCase().includes(query) ||
            c.folder_name.toLowerCase().includes(query)
        );
        renderChannels(filtered);
    });

    async function loadVaultDownloads() {
        try {
            const res = await fetch('/api/downloads');
            const data = await res.json();
            cachedChannels = data.channels || [];
            renderChannels(cachedChannels);
        } catch (err) {
            channelsList.innerHTML = `<p class="subtitle">Failed to load downloads vault.</p>`;
        }
    }

    function renderChannels(channels) {
        channelsList.innerHTML = '';
        if (channels.length === 0) {
            channelsList.innerHTML = `<div class="card glass-panel" style="grid-column: 1/-1; text-align:center; padding: 3rem;"><p class="subtitle">No channels extracted yet. Use the Extractor tab to download YouTube transcripts.</p></div>`;
            return;
        }

        channels.forEach(ch => {
            const card = document.createElement('div');
            card.className = 'channel-card';

            const filesListHtml = ch.transcript_files.slice(0, 10).map(f => 
                `<button class="file-item-btn" onclick="openFileViewer('${ch.folder_name}', '${f}')">
                    <span>📄 ${f}</span>
                    <small>View</small>
                </button>`
            ).join('');

            card.innerHTML = `
                <div class="channel-info">
                    <h4>${ch.channel_title}</h4>
                    <div class="channel-stats">
                        <span>📊 ${ch.total_transcripts} Transcripts Saved</span>
                    </div>
                    <div class="file-list-preview">
                        ${filesListHtml || '<span style="color:var(--text-dim)">No transcript files</span>'}
                    </div>
                </div>
                <div style="display:flex; gap:0.5rem; margin-top:1rem;">
                    <a href="/api/export-zip/${encodeURIComponent(ch.folder_name)}" class="btn btn-secondary btn-block" style="text-decoration:none;">
                        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                        Export ZIP
                    </a>
                </div>
            `;
            channelsList.appendChild(card);
        });
    }

    // Modal Viewer
    window.openFileViewer = async (channelFolder, filename) => {
        try {
            const res = await fetch(`/api/download-file?channel=${encodeURIComponent(channelFolder)}&file_type=transcript&filename=${encodeURIComponent(filename)}`);
            if (!res.ok) throw new Error('Could not fetch file');
            const text = await res.text();

            modalTitle.textContent = filename;
            modalSubtitle.textContent = channelFolder;
            modalContent.textContent = text;
            modal.classList.add('active');
        } catch (err) {
            alert('Failed to load file content.');
        }
    };

    modalClose.addEventListener('click', () => modal.classList.remove('active'));
    modal.addEventListener('click', (e) => { if (e.target === modal) modal.classList.remove('active'); });

    modalCopy.addEventListener('click', () => {
        navigator.clipboard.writeText(modalContent.textContent);
        modalCopy.textContent = 'Copied!';
        setTimeout(() => modalCopy.textContent = 'Copy Content', 2000);
    });

    // Initial load
    loadVaultDownloads();
});
