// Perf Profiler Dashboard — real-time metrics visualization via REST/WebSocket.

'use strict';

/**
 * Fetch profile data from REST API and render flame graph canvas.
 */
async function fetchProfilesAndRender() {
    const response = await fetch('/api/profiles');
    const profilesData = await response.json();
    renderFlameGraph(profilesData);
}

/**
 * Render flame graph canvas from profile data.
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

    ctx.fillStyle = '#4f46e5';
    let yPosition = 380;

    for (const profile of sortedProfiles) {
        const width = (profile.cpu_time / totalCPU) * canvas.width;
        ctx.fillRect(10, yPosition - 20, width, 20);
        ctx.fillStyle = '#1a1a2e';
        ctx.fillText(profile.function_name, 15, yPosition - 10);
        yPosition -= 25;
    }
}

/**
 * Fetch hot path data from REST API and render table.
 */
async function fetchHotPathsAndRender() {
    const response = await fetch('/api/hot_paths');
    const hotPathsData = await response.json();
    renderHotPathsTable(hotPathsData);
}

/**
 * Render hot paths table from detected data.
 * @param {Array} hotPaths - List of detected hot path entries.
 */
function renderHotPathsTable(hotPaths) {
    const tbody = document.getElementById('hot-paths-body');

    if (!hotPaths || hotPaths.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4">No hot paths detected</td></tr>';
        return;
    }

    const sortedHotPaths = [...hotPaths].sort((a, b) => b.percentage_of_total - a.percentage_of_total);

    let html = '';
    for (const hp of sortedHotPaths) {
        html += `<tr><td>${hp.function_name}</td><td>${hp.avg_cpu_time}s</td><td>${hp.call_count}</td><td>${hp.percentage_of_total}%</td></tr>`;
    }

    tbody.innerHTML = html;
}

/**
 * Fetch memory snapshot data from REST API and render chart.
 */
async function fetchMemorySnapshotsAndRender() {
    const response = await fetch('/api/memory_snapshots');
    const memoryData = await response.json();
    renderMemoryChart(memoryData);
}

/**
 * Render memory trend canvas from snapshot data.
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

    const sortedSnapshots = [...snapshots].sort((a, b) => a.timestamp - b.timestamp);

    ctx.strokeStyle = '#4f46e5';
    ctx.lineWidth = 2;
    ctx.beginPath();

    let firstPoint = true;
    for (const snapshot of sortedSnapshots) {
        const x = ((snapshot.timestamp % 3600) / 3600 * canvas.width);
        const y = (snapshot.current_bytes / Math.max(1, snapshot.peak_bytes)) * canvas.height;

        if (firstPoint) {
            ctx.moveTo(x, y);
            firstPoint = false;
        } else {
            ctx.lineTo(x, y);
        }
    }

    ctx.stroke();
}

/**
 * Connect to WebSocket for real-time metric streaming.
 */
function connectWebSocket() {
    const wsUrl = 'ws://localhost:8000/ws/metrics';
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
            document.getElementById('status-indicator').textContent = 'Disconnected';
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
 * Update live metrics display panel.
 * @param {Object} data - Current metric values dictionary.
 */
function updateMetricsDisplay(data) {
    const display = document.getElementById('metrics-display');

    const cpuSpan = `<span>CPU: ${data.cpu_time || 0}s</span>`;
    const memorySpan = `<span>Memory: ${data.memory_bytes || 0} bytes</span>`;

    display.innerHTML = `${cpuSpan}${memorySpan}`;
}

// Initialize dashboard on load.
document.addEventListener('DOMContentLoaded', () => {
    connectWebSocket();
    fetchProfilesAndRender();
    fetchHotPathsAndRender();
    fetchMemorySnapshotsAndRender();
});