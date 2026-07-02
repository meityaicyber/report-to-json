// DOM Elements
const uploadZone = document.getElementById('upload-zone');
const fileInput = document.getElementById('file-input');
const progressSection = document.getElementById('progress-section');
const consoleSection = document.getElementById('console-section');
const consoleLogs = document.getElementById('console-logs');
const resultsSection = document.getElementById('results-section');
const statusBannerContainer = document.getElementById('status-banner-container');
const engineHeartbeat = document.getElementById('engine-heartbeat');
const engineStatusText = document.getElementById('engine-status-text');

// Icons for stepper stages
const STAGE_ICONS = {
    security_gate: 'shield',
    table_extraction: 'table_chart',
    page_cleaning: 'cleaning_services',
    vlm_analysis: 'visibility',
    llm_structuring: 'account_tree'
};

const STAGE_LIST = ['security_gate', 'table_extraction', 'page_cleaning', 'vlm_analysis', 'llm_structuring'];

let currentTaskId = null;
let pollInterval = null;
let statusInterval = null;

// Initialize
setupUploadHandlers();
switchView('dashboard');

function setupUploadHandlers() {
    if (uploadZone) {
        uploadZone.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', handleFileSelect);

        // Drag & Drop
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('border-outline-variant');
            uploadZone.classList.add('border-secondary', 'bg-secondary/5');
        });

        uploadZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadZone.classList.add('border-outline-variant');
            uploadZone.classList.remove('border-secondary', 'bg-secondary/5');
        });

        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.add('border-outline-variant');
            uploadZone.classList.remove('border-secondary', 'bg-secondary/5');
            
            if (e.dataTransfer.files.length > 0) {
                uploadFile(e.dataTransfer.files[0]);
            }
        });
    }
}

function handleFileSelect(e) {
    if (fileInput.files.length > 0) {
        uploadFile(fileInput.files[0]);
    }
}

async function uploadFile(file) {
    resetUI();
    
    // Update heartbeat/UI status
    engineHeartbeat.className = 'w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse';
    engineStatusText.textContent = 'Uploading file...';
    
    const formData = new FormData();
    formData.append('file', file);

    try {
        appendLog(`[+] Uploading ${file.name} (${formatBytes(file.size)})...`);
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }
        
        const data = await response.json();
        appendLog(`[+] Upload complete. Saved to ${data.path}`);
        
        // Start processing
        startProcessing(data.path);
        
    } catch (err) {
        appendLog(`[-] Error: ${err.message}`);
        engineHeartbeat.className = 'w-2.5 h-2.5 rounded-full bg-rose-500';
        engineStatusText.textContent = 'Upload failed';
    }
}

async function startProcessing(filePath) {
    engineStatusText.textContent = 'Scanning file...';
    progressSection.classList.remove('hidden');
    consoleSection.classList.remove('hidden');
    
    try {
        const response = await fetch('/api/scan-and-process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                file_path: filePath,
                dry_run: false,
                no_vision: false
            })
        });
        
        if (!response.ok) {
            throw new Error(`Failed to initiate scan: ${response.statusText}`);
        }
        
        const data = await response.json();
        currentTaskId = data.task_id;
        
        // Start polling
        if (pollInterval) clearInterval(pollInterval);
        pollInterval = setInterval(pollTaskStatus, 800);
        
    } catch (err) {
        appendLog(`[-] Error starting pipeline: ${err.message}`);
        engineStatusText.textContent = 'Engine error';
    }
}

async function pollTaskStatus() {
    if (!currentTaskId) return;
    
    try {
        const response = await fetch(`/api/task/${currentTaskId}`);
        if (!response.ok) return;
        
        const task = await response.json();
        
        // Render new logs
        if (task.logs && task.logs.length > 0) {
            const currentLogCount = consoleLogs.childElementCount;
            for (let i = currentLogCount; i < task.logs.length; i++) {
                appendLog(task.logs[i]);
            }
        }
        
        // Update Stepper progress
        updateStepper(task.stage, task.status);
        
        // Update Heartbeat status
        if (task.status === 'scanning') {
            engineStatusText.textContent = 'Running security scan...';
        } else if (task.status === 'processing') {
            engineStatusText.textContent = 'Running VLM pipeline...';
        }
        
        // Check for terminal state
        if (task.status === 'completed') {
            clearInterval(pollInterval);
            pollInterval = null;
            engineHeartbeat.className = 'w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse';
            engineStatusText.textContent = 'Processing complete';
            
            showStatusBanner(task.verdict, task.filename, task.scan_result);
            renderResults(task);
            
        } else if (task.status === 'failed') {
            clearInterval(pollInterval);
            pollInterval = null;
            engineHeartbeat.className = 'w-2.5 h-2.5 rounded-full bg-rose-500';
            engineStatusText.textContent = 'Job failed';
            
            showStatusBanner(task.verdict || 'ERROR', task.filename, task.scan_result);
            document.getElementById('console-dot').className = 'w-2.5 h-2.5 rounded-full bg-rose-500';
            
            if (task.verdict === 'MALICIOUS') {
                renderMaliciousResults(task);
            }
        }
        
    } catch (err) {
        console.error('Error polling task status:', err);
    }
}

function updateStepper(activeStage, taskStatus) {
    const activeIdx = STAGE_LIST.indexOf(activeStage);
    
    STAGE_LIST.forEach((stage, idx) => {
        const stepDiv = document.getElementById(`step-${stage === 'security_gate' ? 'security' : stage === 'table_extraction' ? 'tables' : stage === 'page_cleaning' ? 'cleaning' : stage === 'vlm_analysis' ? 'vlm' : 'llm'}`);
        if (!stepDiv) return;
        
        const iconContainer = stepDiv.querySelector('div');
        const iconSpan = iconContainer.querySelector('span');
        const labelText = stepDiv.querySelector('p');
        
        // Clear old states
        iconContainer.className = 'w-10 h-10 rounded-full flex items-center justify-center mb-2 z-10';
        iconContainer.classList.remove('animate-pulse');
        labelText.className = 'text-label-caps font-label-caps';
        
        if (idx < activeIdx || (taskStatus === 'completed' && idx === activeIdx)) {
            // Completed Step
            iconContainer.classList.add('bg-emerald-500', 'text-white');
            iconSpan.textContent = 'check';
            labelText.classList.add('text-on-surface', 'font-bold');
            
            // Color connector line
            const line = document.getElementById(`line-${idx + 1}`);
            if (line) {
                line.className = 'hidden md:block h-0.5 flex-1 bg-emerald-500 -mt-10';
            }
            
        } else if (idx === activeIdx && taskStatus !== 'failed') {
            // Active Step
            iconContainer.classList.add('bg-secondary', 'text-white', 'animate-pulse');
            iconSpan.textContent = STAGE_ICONS[stage];
            labelText.classList.add('text-secondary', 'font-bold');
            
            // Color connector line
            const line = document.getElementById(`line-${idx}`);
            if (line) {
                line.className = 'hidden md:block h-0.5 flex-1 bg-secondary -mt-10';
            }
            
        } else {
            // Pending Step
            iconContainer.classList.add('bg-surface-container-high', 'text-on-surface-variant');
            iconSpan.textContent = STAGE_ICONS[stage];
            labelText.classList.add('text-on-surface-variant');
            
            // Color connector line
            const line = document.getElementById(`line-${idx}`);
            if (line) {
                line.className = 'hidden md:block h-0.5 flex-1 bg-surface-container-high -mt-10';
            }
        }
    });
}

function showStatusBanner(verdict, filename, scanResult) {
    statusBannerContainer.className = 'rounded-lg p-md flex items-center justify-between shadow-sm border mt-md';
    statusBannerContainer.innerHTML = '';
    
    let colorClasses = '';
    let verdictTitle = verdict;
    let icon = 'verified_user';
    let detailMsg = '';
    let trackingId = scanResult?.sha256 ? scanResult.sha256.substring(0, 10).toUpperCase() : 'UNKNOWN';

    if (verdict === 'CLEAN') {
        colorClasses = 'bg-emerald-50 border-emerald-200 text-emerald-900';
        detailMsg = `Document "${filename}" passed security check cleanly. Ready for structured processing.`;
    } else if (verdict === 'CLEAN_SANITIZED') {
        colorClasses = 'bg-amber-50 border-amber-200 text-amber-900';
        icon = 'cleaning_services';
        detailMsg = `Document "${filename}" contained active script components. A sanitized duplicate was created.`;
    } else if (verdict === 'MALICIOUS') {
        colorClasses = 'bg-rose-50 border-rose-200 text-rose-900';
        icon = 'gpp_bad';
        detailMsg = `BLOCKED: Active threat patterns or forbidden embedded content detected in "${filename}".`;
    } else {
        colorClasses = 'bg-rose-50 border-rose-200 text-rose-900';
        icon = 'report';
        detailMsg = `Scanner encountered error or inconclusive status for "${filename}".`;
    }
    
    statusBannerContainer.classList.add(...colorClasses.split(' '));
    statusBannerContainer.classList.remove('hidden');

    statusBannerContainer.innerHTML = `
        <div class="flex items-center gap-md">
            <div class="w-10 h-10 ${verdict === 'CLEAN' ? 'bg-emerald-500' : verdict === 'CLEAN_SANITIZED' ? 'bg-amber-500' : 'bg-rose-600'} rounded-full flex items-center justify-center">
                <span class="material-symbols-outlined text-white" style="font-variation-settings: 'FILL' 1;">${icon}</span>
            </div>
            <div>
                <h4 class="font-bold font-body-base">${verdictTitle}</h4>
                <p class="text-body-sm opacity-90">${detailMsg}</p>
            </div>
        </div>
        <div class="text-body-sm font-data-mono opacity-70">${trackingId}</div>
    `;
}

function renderResults(task) {
    resultsSection.classList.remove('hidden');
    
    // Overview Metrics
    document.getElementById('metric-time').textContent = task.elapsed || 'N/A';
    
    let tableCount = 0;
    let assetCount = 0;
    
    if (task.output && task.output._meta) {
        tableCount = task.output._meta.tables_extracted || 0;
        assetCount = task.output._meta.images_extracted || 0;
    }
    
    document.getElementById('metric-tables').textContent = tableCount;
    document.getElementById('metric-assets').textContent = assetCount;
    
    // Executive Summary
    const summaryText = document.getElementById('summary-text');
    if (task.output && task.output.sections && task.output.sections.executive_summary) {
        summaryText.innerHTML = formatJsonValue(task.output.sections.executive_summary);
    } else if (task.output && task.output.text_preview) {
        summaryText.innerHTML = `<strong>[DRY RUN PREVIEW]</strong><br><pre class="font-data-mono text-xs mt-2 overflow-x-auto">${task.output.text_preview}</pre>`;
    } else {
        summaryText.textContent = 'Structure was extracted but executive summary section is empty.';
    }

    // Findings Tab
    renderFindings(task);

    // Inspector Tab
    renderAssetInspector(task);

    // Raw JSON Tab
    document.getElementById('json-pre').textContent = JSON.stringify(task.output, null, 2);
    
    // Select first tab
    switchTab('overview');
}

function renderFindings(task) {
    const container = document.getElementById('findings-container');
    container.innerHTML = '';
    
    let findingsList = [];
    
    if (task.malicious_entities && task.malicious_entities.length > 0) {
        task.malicious_entities.forEach(entity => {
            findingsList.push({
                severity: entity.severity || 'SUSPICIOUS',
                title: entity.type || 'Anomaly',
                desc: entity.detail || 'Generic anomaly detected'
            });
        });
    }
    
    if (task.output && task.output.sections) {
        const obs = task.output.sections.detailed_observations || task.output.sections.findings || task.output.sections.vulnerabilities;
        if (Array.isArray(obs)) {
            obs.forEach(item => {
                findingsList.push({
                    severity: item.risk_rating || item.severity || 'INFO',
                    title: item.vulnerability_title || item.title || 'Observation',
                    desc: item.description || item.details || 'No detailed description.'
                });
            });
        }
    }
    
    if (findingsList.length === 0) {
        container.innerHTML = `
            <div class="col-span-full py-xl text-center text-on-surface-variant font-body-sm">
                No high-level vulnerabilities or anomalies detected.
            </div>
        `;
        return;
    }
    
    findingsList.forEach(finding => {
        const sev = finding.severity.toUpperCase();
        let bgClass = 'bg-blue-50 border-blue-200';
        let pillClass = 'bg-blue-600';
        let icon = 'info';
        
        if (sev === 'CRITICAL' || sev === 'HIGH' || sev === 'MALICIOUS') {
            bgClass = 'bg-rose-50 border-rose-200';
            pillClass = 'bg-rose-600';
            icon = 'report';
        } else if (sev === 'MEDIUM' || sev === 'DANGEROUS') {
            bgClass = 'bg-orange-50 border-orange-200';
            pillClass = 'bg-orange-500';
            icon = 'warning';
        } else if (sev === 'SUSPICIOUS' || sev === 'WARNING') {
            bgClass = 'bg-amber-50 border-amber-200';
            pillClass = 'bg-amber-500';
            icon = 'error';
        }
        
        const card = document.createElement('div');
        card.className = `${bgClass} border p-md rounded-xl flex flex-col justify-between`;
        card.innerHTML = `
            <div>
                <div class="flex justify-between items-start mb-md">
                    <span class="${pillClass} text-white px-2 py-1 rounded text-label-caps font-label-caps">${sev}</span>
                    <span class="material-symbols-outlined ${pillClass.replace('bg-', 'text-')}">${icon}</span>
                </div>
                <h5 class="font-bold text-on-surface mb-xs">${finding.title}</h5>
                <p class="text-body-sm text-on-surface-variant leading-relaxed">${finding.desc}</p>
            </div>
        `;
        container.appendChild(card);
    });
}

function renderAssetInspector(task) {
    const wrapper = document.getElementById('inspector-image-wrapper');
    const tableContainer = document.getElementById('inspector-table-container');
    
    let tableData = null;
    if (task.output && task.output.sections) {
        for (const [key, value] of Object.entries(task.output.sections)) {
            if (Array.isArray(value) && value.length > 0 && typeof value[0] === 'object') {
                tableData = value;
                break;
            }
        }
    }
    
    if (!tableData) {
        wrapper.innerHTML = `
            <div class="flex flex-col items-center justify-center p-xl text-on-surface-variant">
                <span class="material-symbols-outlined text-display-lg mb-sm">image_not_supported</span>
                <p class="text-body-sm">No extracted tables or visual placeholders to view</p>
            </div>
        `;
        tableContainer.innerHTML = `
            <div class="p-xl text-center text-on-surface-variant text-body-sm border border-dashed rounded-xl">
                No tabular JSON data mapped to inspector
            </div>
        `;
        return;
    }
    
    wrapper.innerHTML = `
        <div class="w-full h-full flex flex-col items-center justify-center bg-surface-container-low p-xl text-center border border-dashed border-outline rounded-xl">
            <span class="material-symbols-outlined text-display-lg text-secondary mb-sm animate-pulse">table_chart</span>
            <h5 class="font-bold text-on-surface mb-xs">Stitched Table Frame</h5>
            <p class="text-body-sm text-on-surface-variant max-w-sm">The Vision-Language model successfully stitched and parsed the table data visually.</p>
        </div>
    `;
    
    const headers = Object.keys(tableData[0]);
    let thead = `<thead class="bg-surface-container-low border-b border-outline-variant"><tr>`;
    headers.forEach(h => {
        thead += `<th class="px-md py-sm font-bold uppercase text-xs">${h.replace('_', ' ')}</th>`;
    });
    thead += `</tr></thead>`;
    
    let tbody = `<tbody class="divide-y divide-outline-variant">`;
    tableData.forEach(row => {
        tbody += `<tr class="hover:bg-surface-container-low transition-colors">`;
        headers.forEach(h => {
            const val = typeof row[h] === 'object' ? JSON.stringify(row[h]) : row[h];
            tbody += `<td class="px-md py-sm truncate max-w-[200px]" title="${val}">${val}</td>`;
        });
        tbody += `</tr>`;
    });
    tbody += `</tbody>`;
    
    tableContainer.innerHTML = `
        <table class="w-full text-left font-body-sm border-collapse">
            ${thead}
            ${tbody}
        </table>
    `;
}

function renderMaliciousResults(task) {
    resultsSection.classList.remove('hidden');
    
    document.getElementById('metric-time').textContent = task.elapsed || 'N/A';
    document.getElementById('metric-tables').textContent = 'BLOCKED';
    document.getElementById('metric-assets').textContent = 'BLOCKED';
    
    const summaryText = document.getElementById('summary-text');
    summaryText.innerHTML = `
        <div class="flex items-center gap-md text-rose-800 bg-rose-50 p-md rounded-xl border border-rose-200">
            <span class="material-symbols-outlined text-display-lg text-rose-600">block</span>
            <div>
                <h4 class="font-bold font-headline-md">Document Quarantined</h4>
                <p class="text-body-sm leading-relaxed mt-1">
                    This file failed critical malware screening policies. JavaScript extraction triggers or dangerous embedded elements were identified. The file has been quarantined and blocked from execution in downstream VLM processors.
                </p>
            </div>
        </div>
    `;
    
    renderFindings(task);
    
    const wrapper = document.getElementById('inspector-image-wrapper');
    const tableContainer = document.getElementById('inspector-table-container');
    wrapper.innerHTML = `
        <div class="flex flex-col items-center justify-center p-xl text-rose-600">
            <span class="material-symbols-outlined text-display-lg mb-sm">gpp_bad</span>
            <p class="text-body-sm font-bold">Inspection Blocked</p>
        </div>
    `;
    tableContainer.innerHTML = `
        <div class="p-xl text-center text-rose-600 text-body-sm border border-rose-200 bg-rose-50 rounded-xl">
            Asset generation aborted due to security violation
        </div>
    `;
    
    document.getElementById('json-pre').textContent = JSON.stringify(task.scan_result || {}, null, 2);
    switchTab('overview');
}

// Multi-View Navigation (Dashboard, History, System Status)
window.switchView = function(viewId) {
    // Hide all views
    document.querySelectorAll('.view-pane').forEach(pane => pane.classList.add('hidden'));
    // Show selected view
    document.getElementById('view-' + viewId).classList.remove('hidden');
    
    // Update nav links styles
    document.querySelectorAll('aside nav a').forEach(a => {
        a.classList.remove('text-secondary', 'bg-surface-container-high');
        a.classList.add('text-on-surface-variant');
    });
    
    const activeNav = document.getElementById('nav-' + viewId);
    if (activeNav) {
        activeNav.classList.add('text-secondary', 'bg-surface-container-high');
        activeNav.classList.remove('text-on-surface-variant');
    }
    
    // Reset/Load view data
    if (viewId === 'history') {
        loadHistoryData();
    } else if (viewId === 'status') {
        loadSystemStatusData();
        // Periodically refresh resource levels
        if (statusInterval) clearInterval(statusInterval);
        statusInterval = setInterval(loadSystemStatusData, 4000);
    } else {
        if (statusInterval) {
            clearInterval(statusInterval);
            statusInterval = null;
        }
    }
};

async function loadHistoryData() {
    const tableBody = document.getElementById('history-table-body');
    tableBody.innerHTML = `
        <tr>
            <td class="px-lg py-lg text-center text-on-surface-variant animate-pulse" colspan="5">
                Loading history records...
            </td>
        </tr>
    `;
    
    try {
        const response = await fetch('/api/history');
        if (!response.ok) throw new Error('Failed to load history data');
        
        const history = await response.json();
        if (history.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td class="px-lg py-lg text-center text-on-surface-variant" colspan="5">
                        No processing history found. Upload a report in the Dashboard to begin.
                    </td>
                </tr>
            `;
            return;
        }
        
        tableBody.innerHTML = '';
        history.forEach(item => {
            const tr = document.createElement('tr');
            tr.className = 'hover:bg-surface-container-low transition-colors';
            
            // Verdict badge
            let verdictPill = '<span class="bg-surface-container-high text-on-surface-variant px-2 py-0.5 rounded text-xs font-bold font-data-mono">UNKNOWN</span>';
            if (item.verdict === 'CLEAN') {
                verdictPill = '<span class="bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded text-xs font-bold font-data-mono">CLEAN</span>';
            } else if (item.verdict === 'CLEAN_SANITIZED') {
                verdictPill = '<span class="bg-amber-100 text-amber-800 px-2 py-0.5 rounded text-xs font-bold font-data-mono">SANITIZED</span>';
            } else if (item.verdict === 'MALICIOUS') {
                verdictPill = '<span class="bg-rose-100 text-rose-800 px-2 py-0.5 rounded text-xs font-bold font-data-mono">MALICIOUS</span>';
            }
            
            // Status indicator
            let statusText = `<span class="capitalize text-on-surface-variant">${item.status}</span>`;
            if (item.status === 'processing') {
                statusText = '<span class="text-secondary animate-pulse font-bold">Processing...</span>';
            } else if (item.status === 'scanning') {
                statusText = '<span class="text-amber-600 animate-pulse font-bold">Scanning...</span>';
            } else if (item.status === 'failed') {
                statusText = '<span class="text-rose-600 font-bold">Failed</span>';
            }
            
            // View action button
            let actionBtn = '--';
            if (item.status === 'completed') {
                const loadParam = item.output_file || item.filename;
                actionBtn = `
                    <button class="bg-primary text-white hover:bg-secondary px-sm py-1 rounded text-xs font-bold transition-all" onclick="loadHistoricalReport('${loadParam}')">
                        View Report
                    </button>
                `;
            }
            
            const dateStr = new Date(item.timestamp).toLocaleString();
            
            tr.innerHTML = `
                <td class="px-lg py-md font-bold text-primary">${item.filename}</td>
                <td class="px-lg py-md text-on-surface-variant text-sm">${dateStr}</td>
                <td class="px-lg py-md">${verdictPill}</td>
                <td class="px-lg py-md text-sm">${statusText}</td>
                <td class="px-lg py-md text-right">${actionBtn}</td>
            `;
            tableBody.appendChild(tr);
        });
        
    } catch (err) {
        tableBody.innerHTML = `
            <tr>
                <td class="px-lg py-lg text-center text-rose-600 font-bold" colspan="5">
                    Error loading records: ${err.message}
                </td>
            </tr>
        `;
    }
}

window.loadHistoricalReport = async function(filename) {
    try {
        const response = await fetch(`/api/history/load?filename=${encodeURIComponent(filename)}`);
        if (!response.ok) throw new Error('Failed to download historical report');
        
        const data = await response.json();
        
        // Construct task representation
        const mockTask = {
            filename: data.filename,
            elapsed: data.output?._meta?.elapsed_seconds ? `${Math.round(data.output._meta.elapsed_seconds)}s` : 'Completed',
            output: data.output,
            verdict: data.verdict,
            malicious_entities: data.output?._meta?.malicious_entities || []
        };
        
        showStatusBanner(mockTask.verdict, mockTask.filename, mockTask.output?._meta);
        renderResults(mockTask);
        switchView('dashboard');
        
    } catch (err) {
        alert('Error: ' + err.message);
    }
}

async function loadSystemStatusData() {
    const cpuBar = document.getElementById('status-cpu-bar');
    const cpuText = document.getElementById('status-cpu-text');
    const ramBar = document.getElementById('status-ram-bar');
    const ramText = document.getElementById('status-ram-text');
    const diskBar = document.getElementById('status-disk-bar');
    const diskText = document.getElementById('status-disk-text');
    const gpuState = document.getElementById('status-gpu-state');
    const gpuName = document.getElementById('status-gpu-name');
    
    const diagYara = document.getElementById('diagnostic-yara');
    const diagClamav = document.getElementById('diagnostic-clamav');
    const diagGs = document.getElementById('diagnostic-gs');
    const diagPython = document.getElementById('diagnostic-python');
    
    try {
        const response = await fetch('/api/system-status');
        if (!response.ok) throw new Error('Diagnostic query failed');
        
        const status = await response.json();
        
        // Update bars
        cpuBar.style.width = `${status.cpu_usage}%`;
        cpuText.textContent = `${status.cpu_usage}% Active`;
        
        ramBar.style.width = `${status.ram_usage}%`;
        ramText.textContent = `${status.ram_usage}% Used`;
        
        const diskUsedPct = Math.round(((status.disk_total_gb - status.disk_free_gb) / status.disk_total_gb) * 100);
        diskBar.style.width = `${diskUsedPct}%`;
        diskText.textContent = `${status.disk_free_gb} GB Free / ${status.disk_total_gb} GB`;
        
        // GPU
        if (status.gpu_available) {
            gpuState.textContent = 'ENABLED';
            gpuState.className = 'text-headline-md font-bold text-emerald-600 block';
            gpuName.textContent = status.gpu_name;
        } else {
            gpuState.textContent = 'DISABLED';
            gpuState.className = 'text-headline-md font-bold text-on-surface-variant block';
            gpuName.textContent = 'CPU Mode (VLM fallback)';
        }
        
        // Checklist
        diagYara.innerHTML = status.yara_scanner === 'Active' 
            ? '<span class="w-2.5 h-2.5 bg-emerald-500 rounded-full"></span>Active' 
            : '<span class="w-2.5 h-2.5 bg-rose-500 rounded-full"></span>Inactive';
        diagYara.className = `font-bold font-data-mono flex items-center gap-xs ${status.yara_scanner === 'Active' ? 'text-emerald-600' : 'text-rose-600'}`;
        
        diagClamav.innerHTML = status.clamav_scanner === 'Active' 
            ? '<span class="w-2.5 h-2.5 bg-emerald-500 rounded-full"></span>Active' 
            : '<span class="w-2.5 h-2.5 bg-outline rounded-full"></span>Inactive (Fallback)';
        diagClamav.className = `font-bold font-data-mono flex items-center gap-xs ${status.clamav_scanner === 'Active' ? 'text-emerald-600' : 'text-on-surface-variant'}`;
        
        diagGs.innerHTML = status.ghostscript === 'Active' 
            ? '<span class="w-2.5 h-2.5 bg-emerald-500 rounded-full"></span>Active' 
            : '<span class="w-2.5 h-2.5 bg-rose-500 rounded-full"></span>Inactive (No Strip)';
        diagGs.className = `font-bold font-data-mono flex items-center gap-xs ${status.ghostscript === 'Active' ? 'text-emerald-600' : 'text-rose-600'}`;
        
        diagPython.textContent = `Python ${status.python_version}`;
        
    } catch (err) {
        console.error('Diagnostic polling error:', err);
    }
}

// Helper: Append log to console
function appendLog(text) {
    const line = document.createElement('div');
    line.textContent = `[${new Date().toLocaleTimeString()}] ${text}`;
    consoleLogs.appendChild(line);
    consoleLogs.scrollTop = consoleLogs.scrollHeight;
}

// Helper: Format bytes
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// Helper: Format JSON value
function formatJsonValue(val) {
    if (typeof val === 'string') return val.replace(/\n/g, '<br>');
    if (typeof val === 'object') {
        let html = '<ul class="list-disc pl-md space-y-1">';
        for (const [k, v] of Object.entries(val)) {
            html += `<li><strong>${k.replace('_', ' ')}:</strong> ${typeof v === 'object' ? JSON.stringify(v) : v}</li>`;
        }
        html += '</ul>';
        return html;
    }
    return JSON.stringify(val);
}

// Reset UI state for new job
function resetUI() {
    statusBannerContainer.classList.add('hidden');
    progressSection.classList.add('hidden');
    consoleSection.classList.add('hidden');
    resultsSection.classList.add('hidden');
    consoleLogs.innerHTML = '';
    document.getElementById('console-dot').className = 'w-2.5 h-2.5 rounded-full bg-[#ffb4ab] animate-ping';
    
    // Reset stepper
    STAGE_LIST.forEach(stage => {
        const stepDiv = document.getElementById(`step-${stage === 'security_gate' ? 'security' : stage === 'table_extraction' ? 'tables' : stage === 'page_cleaning' ? 'cleaning' : stage === 'vlm_analysis' ? 'vlm' : 'llm'}`);
        if (!stepDiv) return;
        const iconContainer = stepDiv.querySelector('div');
        const iconSpan = iconContainer.querySelector('span');
        const labelText = stepDiv.querySelector('p');
        
        iconContainer.className = 'w-10 h-10 rounded-full bg-surface-container-high text-on-surface-variant flex items-center justify-center mb-2 z-10';
        iconSpan.textContent = STAGE_ICONS[stage];
        labelText.className = 'text-label-caps font-label-caps text-on-surface-variant';
    });
    
    for (let i = 1; i <= 4; i++) {
        const line = document.getElementById(`line-${i}`);
        if (line) {
            line.className = 'hidden md:block h-0.5 flex-1 bg-surface-container-high -mt-10';
        }
    }
}

// Copy JSON Clipboard
document.getElementById('copy-json-btn').addEventListener('click', () => {
    const jsonText = document.getElementById('json-pre').textContent;
    navigator.clipboard.writeText(jsonText).then(() => {
        const btnText = document.querySelector('#copy-json-btn span.text-body-sm');
        const oldText = btnText.textContent;
        btnText.textContent = 'Copied!';
        setTimeout(() => btnText.textContent = oldText, 1500);
    });
});

// Exposed global tab switcher
window.switchTab = function(tabId) {
    document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.add('hidden'));
    document.querySelectorAll('nav button').forEach(btn => {
        btn.classList.remove('text-secondary', 'border-b-2', 'border-secondary');
        btn.classList.add('text-on-surface-variant');
    });
    
    document.getElementById('content-' + tabId).classList.remove('hidden');
    const activeBtn = document.getElementById('tab-' + tabId);
    activeBtn.classList.add('text-secondary', 'border-b-2', 'border-secondary');
    activeBtn.classList.remove('text-on-surface-variant');
};
