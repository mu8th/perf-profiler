// Perf Profiler Dashboard, real-time metrics visualization via REST/WebSocket.

'use strict';

// Escape values before they reach innerHTML. Function names come from
// whatever code was instrumented, so treat them as text, not markup.
function esc(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

/**
 * Fetch profile data from the REST API and render the flame graph canvas.
 */
async function fetchProfilesAndRender() {
    const response = await fetch('/api/profiles');
    if (!response.ok) return;
    const profilesData = await response.json();
    renderFlameGraph(profilesData);
}

/**
 * Render flame graph bars from profile data, widest (most CPU) on top.
 * @param {Array} profiles - List of function call profiles with CPU time values.
 */
function renderFlameGraph(profiles) {
    const canvas = document.getElementById('flame-graph');
    const ctx = canvas.getContext('2d');

    if (!profiles || profiles.length === 0) {
        ctx.fillStyle = '#6b7280';
        ctx.fillText('No data available', 10, 30);
        return;
    }

    const totalCPU = profiles.reduce((sum, p) => sum + p.cpu_time, 0);
    const sortedProfiles = [...profiles].sort((a, b) => b.cpu_time - a.cpu_time);

    let yPosition = 40;
    for (const profile of sortedProfiles) {
        const width = Math.max(2, (profile.cpu_time / totalCPU) * canvas.width);
        ctx.fillStyle = '#4f46e5';
        ctx.fillRect(10, yPosition, width, 20);
        ctx.fillStyle = '#e5e7eb';
        ctx.fillText(profile.function_name, 15, yPosition + 14);
        yPosition += 28;
    }
}

/**
 * Fetch hot path data from the REST API and render the table.
 */
async function fetchHotPathsAndRender() {
    const response = await fetch('/api/hot_paths');
    if (!response.ok) return;
    const hotPathsData = await response.json();
    renderHotPathsTable(hotPathsData);
}

/**
 * Render the hot paths table, most expensive function first.
 * @param {Array} hotPaths - List of detected hot path entries.
 */
function renderHotPathsTable(hotPaths) {
    const tbody = document.getElementById('hot-paths-body');

    if (!hotPaths || hotPaths.length === 0) {
        tbody.innerHTML = '<tr class="row-empty"><td colspan="4">No hot paths detected.</td></tr>';
        return;
    }

    const sortedHotPaths = [...hotPaths].sort((a, b) => b.percentage_of_total - a.percentage_of_total);

    let html = '';
    for (const hp of sortedHotPaths) {
        html += `<tr><td>${esc(hp.function_name)}</td><td>${hp.avg_cpu_time}s</td><td>${esc(hp.call_count)}</td><td>${hp.percentage_of_total}%</td></tr>`;
    }

    tbody.innerHTML = html;
}

/**
 * Fetch memory snapshot data from the REST API and render the trend chart.
 */
async function fetchMemorySnapshotsAndRender() {
    const response = await fetch('/api/memory_snapshots');
    if (!response.ok) return;
    const memoryData = await response.json();
    renderMemoryChart(memoryData);
}

/**
 * Render the memory trend line from snapshot data.
 * Points are spaced evenly along the x axis; y is scaled against the largest
 * current allocation in the series so growth and drops stay visible.
 * @param {Array} snapshots - List of memory allocation snapshots with timestamps.
 */
function renderMemoryChart(snapshots) {
    const canvas = document.getElementById('memory-chart');
    const ctx = canvas.getContext('2d');

    if (!snapshots || snapshots.length === 0) {
        ctx.fillStyle = '#6b7280';
        ctx.fillText('No data available', 10, 30);
        return;
    }

    const sortedSnapshots = [...snapshots].sort((a, b) => String(a.timestamp).localeCompare(String(b.timestamp)));
    const maxBytes = Math.max(...sortedSnapshots.map(s => s.current_bytes), 1);
    const stepX = snapshots.length > 1 ? (canvas.width - 20) / (snapshots.length - 1) : 0;

    ctx.strokeStyle = '#4f46e5';
    ctx.lineWidth = 2;
    ctx.beginPath();

    sortedSnapshots.forEach((snapshot, i) => {
        const x = 10 + i * stepX;
        const y = canvas.height - (snapshot.current_bytes / maxBytes) * (canvas.height - 20);
        if (i === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });

    ctx.stroke();
}

/**
 * Connect to the WebSocket for real-time metric streaming.
 */
function connectWebSocket() {
    // Derive the socket URL from the page origin so the dashboard works
    // whatever host and port the server is bound to.
    const protocol = location.protocol === 'https:' ? 'wss://' : 'ws://';
    const wsUrl = `${protocol}${location.host}/ws/metrics`;
    let websocket;

    try {
        websocket = new WebSocket(wsUrl);

        websocket.onopen = () => {
            document.getElementById('status-indicator').textContent = 'Connected';
        };

        websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            updateMetricsDisplay(data);
        };

        websocket.onerror = () => {
            document.getElementById('status-indicator').textContent = 'Error';
        };

        websocket.onclose = () => {
            document.getElementById('status-indicator').textContent = 'Disconnected';
        };
    } catch (error) {
        console.error('WebSocket connection failed:', error);
        document.getElementById('status-indicator').textContent = 'Error';
    }
}

/**
 * Update the live metrics display panel. The "CPU: Xs" and "Memory: Y bytes"
 * format is parsed by the presentation layer in index.html, so keep it stable.
 * @param {Object} data - Current metric values dictionary.
 */
function updateMetricsDisplay(data) {
    const display = document.getElementById('metrics-display');

    const cpuSpan = `<span>CPU: ${esc(data.cpu_time || 0)}s</span>`;
    const memorySpan = `<span>Memory: ${esc(data.memory_bytes || 0)} bytes</span>`;

    display.innerHTML = `${cpuSpan}${memorySpan}`;
}

// Initialize dashboard on load.
document.addEventListener('DOMContentLoaded', () => {
    connectWebSocket();
    fetchProfilesAndRender();
    fetchHotPathsAndRender();
    fetchMemorySnapshotsAndRender();
});
