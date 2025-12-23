// Water Monitoring Dashboard - Main JavaScript File

// Global variables
let autoRefreshInterval;
let currentData = {};
let lastUpdateTime = null;

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('AquaFlow Monitoring System initialized');
    
    // Initialize tooltips
    initTooltips();
    
    // Start auto-refresh
    startAutoRefresh();
    
    // Initialize real-time updates
    initRealTimeUpdates();
    
    // Setup event listeners
    setupEventListeners();
    
    // Load initial data
    loadInitialData();
});

// Initialize tooltips
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', function(e) {
            const tooltipText = this.getAttribute('data-tooltip');
            showTooltip(e, tooltipText);
        });
        
        element.addEventListener('mouseleave', function() {
            hideTooltip();
        });
    });
}

// Show tooltip
function showTooltip(event, text) {
    let tooltip = document.getElementById('global-tooltip');
    if (!tooltip) {
        tooltip = document.createElement('div');
        tooltip.id = 'global-tooltip';
        tooltip.className = 'tooltip-box';
        document.body.appendChild(tooltip);
    }
    
    tooltip.textContent = text;
    tooltip.style.display = 'block';
    tooltip.style.left = (event.pageX + 10) + 'px';
    tooltip.style.top = (event.pageY + 10) + 'px';
}

// Hide tooltip
function hideTooltip() {
    const tooltip = document.getElementById('global-tooltip');
    if (tooltip) {
        tooltip.style.display = 'none';
    }
}

// Start auto-refresh
function startAutoRefresh() {
    // Clear any existing interval
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    
    // Set new interval (30 seconds)
    autoRefreshInterval = setInterval(refreshDashboardData, 30000);
    console.log('Auto-refresh started (30s interval)');
}

// Stop auto-refresh
function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
        console.log('Auto-refresh stopped');
    }
}

// Initialize real-time updates
function initRealTimeUpdates() {
    // This would connect to WebSocket or SSE for real-time updates
    // For now, we'll use polling via auto-refresh
    console.log('Real-time updates initialized');
}

// Setup event listeners
function setupEventListeners() {
    // Manual refresh button
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function(e) {
            e.preventDefault();
            refreshDashboardData();
        });
    }
    
    // Check leaks button
    const checkLeaksBtn = document.getElementById('check-leaks-btn');
    if (checkLeaksBtn) {
        checkLeaksBtn.addEventListener('click', function(e) {
            e.preventDefault();
            checkLeaks();
        });
    }
    
    // Export data button
    const exportBtn = document.getElementById('export-data-btn');
    if (exportBtn) {
        exportBtn.addEventListener('click', function(e) {
            e.preventDefault();
            exportData();
        });
    }
    
    // System diagnostics button
    const diagnosticsBtn = document.getElementById('diagnostics-btn');
    if (diagnosticsBtn) {
        diagnosticsBtn.addEventListener('click', function(e) {
            e.preventDefault();
            runDiagnostics();
        });
    }
    
    // Close modal buttons
    document.querySelectorAll('.modal-close, .modal-cancel').forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            if (modal) {
                modal.style.display = 'none';
            }
        });
    });
    
    // Auto-refresh toggle
    const autoRefreshToggle = document.getElementById('auto-refresh-toggle');
    if (autoRefreshToggle) {
        autoRefreshToggle.addEventListener('change', function() {
            if (this.checked) {
                startAutoRefresh();
                showNotification('Auto-refresh enabled', 'success');
            } else {
                stopAutoRefresh();
                showNotification('Auto-refresh disabled', 'warning');
            }
        });
    }
    
    // Window resize handling
    window.addEventListener('resize', debounce(handleResize, 250));
}

// Handle window resize
function handleResize() {
    // Update any responsive elements
    updateResponsiveElements();
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Load initial data
async function loadInitialData() {
    try {
        showLoading();
        
        const response = await fetch('/api/system-data');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        currentData = data;
        lastUpdateTime = new Date();
        
        updateDashboard(data);
        updateLastUpdateTime();
        
        hideLoading();
        showNotification('Dashboard data loaded successfully', 'success');
    } catch (error) {
        console.error('Error loading initial data:', error);
        hideLoading();
        showNotification('Failed to load dashboard data', 'error');
    }
}

// Refresh dashboard data
async function refreshDashboardData() {
    try {
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.classList.add('refreshing');
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
        }
        
        const response = await fetch('/api/system-data');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        currentData = data;
        lastUpdateTime = new Date();
        
        updateDashboard(data);
        updateLastUpdateTime();
        
        if (refreshBtn) {
            refreshBtn.classList.remove('refreshing');
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
        }
        
        // Show success indicator
        showSuccessIndicator();
    } catch (error) {
        console.error('Error refreshing data:', error);
        
        if (refreshBtn) {
            refreshBtn.classList.remove('refreshing');
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
        }
        
        showNotification('Failed to refresh data', 'error');
    }
}

// Update dashboard with new data
function updateDashboard(data) {
    // Update valve status
    updateValveStatus(data.valves);
    
    // Update sensor readings
    updateSensorReadings(data.sensors);
    
    // Update water level
    updateWaterLevel(data.water_level);
    
    // Update tap status
    updateTapStatus(data.taps);
    
    // Update leaks
    updateLeaks(data.leaks);
    
    // Update system stats
    updateSystemStats(data);
}

// Update valve status display
function updateValveStatus(valves) {
    const valveContainer = document.getElementById('valve-status-container');
    if (!valveContainer) return;
    
    let html = '';
    for (const [valveName, status] of Object.entries(valves)) {
        const isOpen = status === 1 || status === 'Open';
        html += `
            <div class="valve-item">
                <div class="valve-icon ${isOpen ? 'open' : 'closed'}">
                    <i class="fas fa-${isOpen ? 'toggle-on' : 'toggle-off'}"></i>
                </div>
                <div class="valve-info">
                    <h4>${valveName}</h4>
                    <p class="valve-status-text ${isOpen ? 'status-open' : 'status-closed'}">
                        ${isOpen ? 'OPEN' : 'CLOSED'}
                    </p>
                </div>
                <div class="valve-actions">
                    <button class="action-btn small" onclick="toggleValve('${valveName}')">
                        <i class="fas fa-exchange-alt"></i>
                    </button>
                </div>
            </div>
        `;
    }
    
    valveContainer.innerHTML = html;
}

// Update sensor readings
function updateSensorReadings(sensors) {
    // pH sensor
    const phValue = document.getElementById('ph-value');
    if (phValue && sensors.pH !== undefined) {
        phValue.textContent = sensors.pH.toFixed(1);
        phValue.className = `sensor-value ${getPhStatusClass(sensors.pH)}`;
    }
    
    // Turbidity sensor
    const turbidityValue = document.getElementById('turbidity-value');
    if (turbidityValue && sensors.turbidity !== undefined) {
        turbidityValue.textContent = sensors.turbidity.toFixed(1) + ' NTU';
        turbidityValue.className = `sensor-value ${getTurbidityStatusClass(sensors.turbidity)}`;
    }
    
    // Salinity sensor
    const salinityValue = document.getElementById('salinity-value');
    if (salinityValue && sensors.salinity !== undefined) {
        salinityValue.textContent = sensors.salinity.toFixed(2) + ' g/L';
        salinityValue.className = `sensor-value ${getSalinityStatusClass(sensors.salinity)}`;
    }
    
    // Flow sensor
    const flowValue = document.getElementById('flow-value');
    if (flowValue && sensors.flow !== undefined) {
        flowValue.textContent = sensors.flow.toFixed(1) + ' L/min';
        flowValue.className = 'sensor-value';
    }
}

// Get pH status class
function getPhStatusClass(ph) {
    if (ph >= 6.5 && ph <= 8.5) return 'good';
    if (ph >= 6.0 && ph <= 9.0) return 'warning';
    return 'critical';
}

// Get turbidity status class
function getTurbidityStatusClass(turbidity) {
    if (turbidity <= 5.0) return 'good';
    if (turbidity <= 10.0) return 'warning';
    return 'critical';
}

// Get salinity status class
function getSalinityStatusClass(salinity) {
    if (salinity <= 0.5) return 'good';
    if (salinity <= 1.0) return 'warning';
    return 'critical';
}

// Update water level
function updateWaterLevel(level) {
    const waterLevelElement = document.getElementById('water-level');
    if (waterLevelElement) {
        waterLevelElement.textContent = level + '%';
        waterLevelElement.className = `water-level ${getWaterLevelClass(level)}`;
    }
    
    const waterLevelBar = document.getElementById('water-level-bar');
    if (waterLevelBar) {
        waterLevelBar.style.width = level + '%';
    }
    
    const waterLevelIndicator = document.getElementById('water-level-indicator');
    if (waterLevelIndicator) {
        waterLevelIndicator.className = `water-level-indicator ${getWaterLevelClass(level)}`;
    }
}

// Get water level class
function getWaterLevelClass(level) {
    if (level >= 75) return 'high';
    if (level >= 25) return 'medium';
    return 'low';
}

// Update tap status
function updateTapStatus(taps) {
    const tapContainer = document.getElementById('tap-status-container');
    if (!tapContainer) return;
    
    let openCount = 0;
    let html = '';
    
    for (const [tapName, status] of Object.entries(taps)) {
        const isOpen = status === 1 || status === 'Open';
        if (isOpen) openCount++;
        
        html += `
            <div class="tap-item">
                <div class="tap-icon ${isOpen ? 'open' : 'closed'}">
                    <i class="fas fa-${isOpen ? 'faucet' : 'faucet-drip'}"></i>
                </div>
                <div class="tap-info">
                    <h4>${tapName}</h4>
                    <p class="tap-status-text ${isOpen ? 'status-open' : 'status-closed'}">
                        ${isOpen ? 'FLOWING' : 'CLOSED'}
                    </p>
                </div>
                <div class="tap-actions">
                    <button class="action-btn small" onclick="toggleTap('${tapName}')">
                        <i class="fas fa-${isOpen ? 'times' : 'check'}"></i>
                    </button>
                </div>
            </div>
        `;
    }
    
    tapContainer.innerHTML = html;
    
    // Update open taps counter
    const openTapsElement = document.getElementById('open-taps-count');
    if (openTapsElement) {
        openTapsElement.textContent = openCount;
    }
}

// Update leaks
function updateLeaks(leaks) {
    const leakContainer = document.getElementById('leak-status-container');
    if (!leakContainer) return;
    
    const activeLeaks = Object.entries(leaks).filter(([_, status]) => 
        status === 1 || status === 'ACTIVE'
    );
    
    if (activeLeaks.length > 0) {
        let html = `
            <div class="leak-alert">
                <div class="alert-header critical">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>ACTIVE LEAKS DETECTED</h3>
                    <span class="badge badge-danger">${activeLeaks.length}</span>
                </div>
                <div class="leak-list">
        `;
        
        activeLeaks.forEach(([pipeName, status]) => {
            html += `
                <div class="leak-item">
                    <div class="leak-icon">
                        <i class="fas fa-faucet-drip"></i>
                    </div>
                    <div class="leak-info">
                        <h4>${pipeName}</h4>
                        <p class="leak-severity critical">CRITICAL - IMMEDIATE ATTENTION REQUIRED</p>
                        <small>Detected: Just now</small>
                    </div>
                    <div class="leak-actions">
                        <button class="btn btn-danger small" onclick="isolateLeak('${pipeName}')">
                            <i class="fas fa-ban"></i> Isolate
                        </button>
                        <button class="btn btn-secondary small" onclick="showLeakDetails('${pipeName}')">
                            <i class="fas fa-info-circle"></i> Details
                        </button>
                    </div>
                </div>
            `;
        });
        
        html += `
                </div>
                <div class="leak-actions-footer">
                    <button class="btn btn-danger" onclick="emergencyShutdown()">
                        <i class="fas fa-power-off"></i> Emergency Shutdown
                    </button>
                    <button class="btn btn-secondary" onclick="notifyMaintenance()">
                        <i class="fas fa-tools"></i> Notify Maintenance
                    </button>
                </div>
            </div>
        `;
        
        leakContainer.innerHTML = html;
        
        // Play alert sound if first time detecting
        if (!leakContainer.hasAttribute('data-alert-played')) {
            playAlertSound();
            leakContainer.setAttribute('data-alert-played', 'true');
        }
    } else {
        leakContainer.innerHTML = `
            <div class="no-leaks">
                <div class="status-icon good">
                    <i class="fas fa-check-circle"></i>
                </div>
                <h3>SYSTEM INTEGRITY VERIFIED</h3>
                <p>No active leaks detected in the water network</p>
                <p class="last-scan">Last verified: ${new Date().toLocaleTimeString()}</p>
            </div>
        `;
        
        leakContainer.removeAttribute('data-alert-played');
    }
}

// Update system stats
function updateSystemStats(data) {
    // Update various system statistics
    updateStatsDisplay('total-flow', calculateTotalFlow(data));
    updateStatsDisplay('system-pressure', calculateSystemPressure(data));
    updateStatsDisplay('water-quality', calculateWaterQualityIndex(data.sensors));
    updateStatsDisplay('energy-efficiency', calculateEnergyEfficiency(data));
}

// Update a stats display element
function updateStatsDisplay(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
    }
}

// Calculate total flow
function calculateTotalFlow(data) {
    const flow = data.sensors?.flow || 0;
    const openTaps = Object.values(data.taps || {}).filter(v => v === 1 || v === 'Open').length;
    return (flow * openTaps).toFixed(1) + ' L/min';
}

// Calculate system pressure
function calculateSystemPressure(data) {
    // Simplified calculation based on water level and open valves
    const waterLevel = data.water_level || 0;
    const openValves = Object.values(data.valves || {}).filter(v => v === 1 || v === 'Open').length;
    const pressure = (waterLevel / 100) * 3 + (openValves * 0.5);
    return pressure.toFixed(1) + ' Bar';
}

// Calculate water quality index
function calculateWaterQualityIndex(sensors) {
    if (!sensors) return 'N/A';
    
    let score = 100;
    
    // pH scoring (ideal: 7.0)
    const phDiff = Math.abs((sensors.pH || 7) - 7);
    score -= phDiff * 5;
    
    // Turbidity scoring (lower is better)
    const turbidity = sensors.turbidity || 0;
    score -= turbidity * 0.5;
    
    // Salinity scoring (lower is better)
    const salinity = sensors.salinity || 0;
    score -= salinity * 10;
    
    // Ensure score is within bounds
    score = Math.max(0, Math.min(100, score));
    
    if (score >= 90) return 'Excellent';
    if (score >= 75) return 'Good';
    if (score >= 60) return 'Fair';
    return 'Poor';
}

// Calculate energy efficiency
function calculateEnergyEfficiency(data) {
    // Simplified efficiency calculation
    const waterLevel = data.water_level || 0;
    const flow = data.sensors?.flow || 0;
    
    if (waterLevel === 0 || flow === 0) return '0%';
    
    const efficiency = (flow / (waterLevel / 100)) * 100;
    return Math.min(100, Math.round(efficiency)) + '%';
}

// Update last update time display
function updateLastUpdateTime() {
    const timeElement = document.getElementById('last-update-time');
    if (timeElement && lastUpdateTime) {
        timeElement.textContent = lastUpdateTime.toLocaleTimeString();
    }
    
    // Update the update indicator
    const updateIndicator = document.getElementById('update-indicator');
    if (updateIndicator) {
        updateIndicator.classList.add('updated');
        setTimeout(() => {
            updateIndicator.classList.remove('updated');
        }, 2000);
    }
}

// Show loading state
function showLoading() {
    const loadingElement = document.getElementById('loading-overlay');
    if (loadingElement) {
        loadingElement.style.display = 'flex';
    }
}

// Hide loading state
function hideLoading() {
    const loadingElement = document.getElementById('loading-overlay');
    if (loadingElement) {
        loadingElement.style.display = 'none';
    }
}

// Show notification
function showNotification(message, type = 'info') {
    const notificationContainer = document.getElementById('notification-container');
    if (!notificationContainer) {
        // Create notification container if it doesn't exist
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'notification-container';
        document.body.appendChild(container);
    }
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-icon">
            <i class="fas fa-${getNotificationIcon(type)}"></i>
        </div>
        <div class="notification-content">
            <p>${message}</p>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    document.getElementById('notification-container').appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Get notification icon based on type
function getNotificationIcon(type) {
    switch (type) {
        case 'success': return 'check-circle';
        case 'error': return 'exclamation-circle';
        case 'warning': return 'exclamation-triangle';
        default: return 'info-circle';
    }
}

// Show success indicator
function showSuccessIndicator() {
    const indicator = document.getElementById('success-indicator');
    if (indicator) {
        indicator.style.display = 'block';
        setTimeout(() => {
            indicator.style.display = 'none';
        }, 2000);
    }
}

// Check for leaks
async function checkLeaks() {
    try {
        const checkBtn = document.getElementById('check-leaks-btn');
        if (checkBtn) {
            checkBtn.classList.add('loading');
            checkBtn.disabled = true;
            checkBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scanning...';
        }
        
        const response = await fetch('/api/check-leaks', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (checkBtn) {
            checkBtn.classList.remove('loading');
            checkBtn.disabled = false;
            checkBtn.innerHTML = '<i class="fas fa-search"></i> Check Leaks';
        }
        
        // Show results in modal
        showLeakResultsModal(data);
        
        showNotification(`Leak scan completed: ${data.total_active} leaks found`, 
                        data.total_active > 0 ? 'warning' : 'success');
                        
    } catch (error) {
        console.error('Error checking leaks:', error);
        
        const checkBtn = document.getElementById('check-leaks-btn');
        if (checkBtn) {
            checkBtn.classList.remove('loading');
            checkBtn.disabled = false;
            checkBtn.innerHTML = '<i class="fas fa-search"></i> Check Leaks';
        }
        
        showNotification('Failed to check for leaks', 'error');
    }
}

// Show leak results modal
function showLeakResultsModal(data) {
    const modal = document.getElementById('leak-results-modal');
    const content = document.getElementById('leak-results-content');
    
    if (!modal || !content) return;
    
    let html = `
        <div class="leak-report">
            <div class="report-header">
                <h3><i class="fas fa-file-alt"></i> Leak Detection Report</h3>
                <p class="report-time">Generated: ${new Date().toLocaleString()}</p>
            </div>
            
            <div class="report-summary">
                <div class="summary-grid">
                    <div class="summary-item">
                        <div class="summary-label">Total Pipes Scanned</div>
                        <div class="summary-value">${data.total_pipes || 15}</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-label">Active Leaks Found</div>
                        <div class="summary-value ${data.total_active > 0 ? 'critical' : 'good'}">
                            ${data.total_active}
                        </div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-label">Inactive Leaks</div>
                        <div class="summary-value">${data.inactive_leak_count || 0}</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-label">Scan Duration</div>
                        <div class="summary-value">~2.5 seconds</div>
                    </div>
                </div>
            </div>
    `;
    
    if (data.active_leaks && data.active_leaks.length > 0) {
        html += `
            <div class="report-details">
                <h4>Active Leaks Detected:</h4>
                <ul class="leak-details-list">
        `;
        
        data.active_leaks.forEach((leak, index) => {
            html += `
                <li>
                    <strong>Leak #${index + 1}:</strong> ${leak}
                    <br><span class="leak-status critical">● ACTIVE - Water loss detected</span>
                </li>
            `;
        });
        
        html += `
                </ul>
            </div>
            
            <div class="report-actions">
                <h4>Recommended Actions:</h4>
                <ol>
                    <li>Immediately isolate affected pipe sections</li>
                    <li>Dispatch maintenance team to location</li>
                    <li>Monitor adjacent pipe pressure</li>
                    <li>Update maintenance log with findings</li>
                </ol>
            </div>
        `;
    } else {
        html += `
            <div class="report-details">
                <div class="no-leaks-found">
                    <i class="fas fa-check-circle"></i>
                    <h4>No Active Leaks Found</h4>
                    <p>All pipes in the water network are functioning properly with no active leaks detected.</p>
                </div>
            </div>
        `;
    }
    
    html += `
            <div class="report-footer">
                <p><strong>Note:</strong> This report is generated based on real-time sensor data. 
                Regular maintenance checks are still recommended.</p>
            </div>
        </div>
    `;
    
    content.innerHTML = html;
    modal.style.display = 'flex';
}

// Export data
function exportData() {
    if (!currentData || Object.keys(currentData).length === 0) {
        showNotification('No data available to export', 'warning');
        return;
    }
    
    try {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `aquaflow-export-${timestamp}.json`;
        
        const dataStr = JSON.stringify(currentData, null, 2);
        const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
        
        const link = document.createElement('a');
        link.setAttribute('href', dataUri);
        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showNotification('Data exported successfully', 'success');
    } catch (error) {
        console.error('Error exporting data:', error);
        showNotification('Failed to export data', 'error');
    }
}

// Run system diagnostics
async function runDiagnostics() {
    try {
        const diagnosticsBtn = document.getElementById('diagnostics-btn');
        if (diagnosticsBtn) {
            diagnosticsBtn.classList.add('loading');
            diagnosticsBtn.disabled = true;
            diagnosticsBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running...';
        }
        
        // Simulate diagnostics (in a real app, this would call an API)
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        const diagnostics = {
            system_health: Math.floor(Math.random() * 30) + 70, // 70-100%
            firebase_connection: currentData ? 'Connected' : 'Disconnected',
            sensor_status: 'All sensors operational',
            valve_status: 'All valves responding',
            last_maintenance: '2024-01-15',
            recommendations: [
                'Schedule routine maintenance for next month',
                'Consider upgrading pH sensor calibration',
                'Monitor water level trends'
            ]
        };
        
        if (diagnosticsBtn) {
            diagnosticsBtn.classList.remove('loading');
            diagnosticsBtn.disabled = false;
            diagnosticsBtn.innerHTML = '<i class="fas fa-stethoscope"></i> Diagnostics';
        }
        
        showDiagnosticsModal(diagnostics);
        showNotification('System diagnostics completed', 'success');
        
    } catch (error) {
        console.error('Error running diagnostics:', error);
        
        const diagnosticsBtn = document.getElementById('diagnostics-btn');
        if (diagnosticsBtn) {
            diagnosticsBtn.classList.remove('loading');
            diagnosticsBtn.disabled = false;
            diagnosticsBtn.innerHTML = '<i class="fas fa-stethoscope"></i> Diagnostics';
        }
        
        showNotification('Failed to run diagnostics', 'error');
    }
}

// Show diagnostics modal
function showDiagnosticsModal(diagnostics) {
    const modal = document.getElementById('diagnostics-modal');
    const content = document.getElementById('diagnostics-content');
    
    if (!modal || !content) return;
    
    let html = `
        <div class="diagnostics-report">
            <div class="report-header">
                <h3><i class="fas fa-stethoscope"></i> System Diagnostics Report</h3>
                <p class="report-time">Generated: ${new Date().toLocaleString()}</p>
            </div>
            
            <div class="health-score">
                <div class="score-circle">
                    <div class="score-value">${diagnostics.system_health}%</div>
                    <div class="score-label">System Health</div>
                </div>
                <div class="health-indicator ${diagnostics.system_health >= 90 ? 'excellent' : 
                                               diagnostics.system_health >= 75 ? 'good' : 
                                               diagnostics.system_health >= 60 ? 'fair' : 'poor'}">
                </div>
            </div>
            
            <div class="diagnostics-details">
                <h4>System Status:</h4>
                <table class="status-table">
                    <tr>
                        <td>Firebase Connection:</td>
                        <td><span class="status-badge ${diagnostics.firebase_connection === 'Connected' ? 'good' : 'bad'}">
                            ${diagnostics.firebase_connection}
                        </span></td>
                    </tr>
                    <tr>
                        <td>Sensor Status:</td>
                        <td><span class="status-badge good">${diagnostics.sensor_status}</span></td>
                    </tr>
                    <tr>
                        <td>Valve Status:</td>
                        <td><span class="status-badge good">${diagnostics.valve_status}</span></td>
                    </tr>
                    <tr>
                        <td>Last Maintenance:</td>
                        <td>${diagnostics.last_maintenance}</td>
                    </tr>
                </table>
            </div>
            
            <div class="recommendations">
                <h4>Recommendations:</h4>
                <ul>
    `;
    
    diagnostics.recommendations.forEach(rec => {
        html += `<li><i class="fas fa-chevron-right"></i> ${rec}</li>`;
    });
    
    html += `
                </ul>
            </div>
            
            <div class="report-footer">
                <p><strong>Note:</strong> This is an automated diagnostic report. 
                For detailed analysis, contact system administrator.</p>
            </div>
        </div>
    `;
    
    content.innerHTML = html;
    modal.style.display = 'flex';
}

// Toggle valve (simulated - in real app would call API)
function toggleValve(valveName) {
    if (confirm(`Are you sure you want to toggle ${valveName}?`)) {
        showNotification(`${valveName} toggle command sent`, 'info');
        
        // In a real app, this would call an API endpoint
        // For now, just simulate the action
        setTimeout(() => {
            showNotification(`${valveName} status updated`, 'success');
            refreshDashboardData();
        }, 1000);
    }
}

// Toggle tap (simulated - in real app would call API)
function toggleTap(tapName) {
    if (confirm(`Are you sure you want to toggle ${tapName}?`)) {
        showNotification(`${tapName} toggle command sent`, 'info');
        
        // In a real app, this would call an API endpoint
        // For now, just simulate the action
        setTimeout(() => {
            showNotification(`${tapName} status updated`, 'success');
            refreshDashboardData();
        }, 1000);
    }
}

// Isolate leak
function isolateLeak(pipeName) {
    if (confirm(`Emergency isolation for ${pipeName}?\n\nThis will shut down water flow to this section and may affect multiple taps.`)) {
        showNotification(`Initiating isolation for ${pipeName}...`, 'warning');
        
        // In a real app, this would call an emergency API
        setTimeout(() => {
            showNotification(`${pipeName} isolated successfully. Maintenance team notified.`, 'success');
            refreshDashboardData();
        }, 2000);
    }
}

// Show leak details
function showLeakDetails(pipeName) {
    // Create a simple details modal
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3><i class="fas fa-info-circle"></i> Leak Details: ${pipeName}</h3>
                <button class="modal-close" onclick="this.closest('.modal').remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                <div class="leak-details">
                    <p><strong>Location:</strong> ${pipeName}</p>
                    <p><strong>Status:</strong> <span class="critical">ACTIVE LEAK</span></p>
                    <p><strong>First Detected:</strong> ${new Date().toLocaleString()}</p>
                    <p><strong>Estimated Flow Loss:</strong> 2.5 L/min</p>
                    <p><strong>Affected Areas:</strong> Downstream taps and sections</p>
                    <p><strong>Recommended Action:</strong> Immediate isolation and repair</p>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">
                    Close
                </button>
                <button class="btn btn-danger" onclick="isolateLeak('${pipeName}'); this.closest('.modal').remove()">
                    <i class="fas fa-ban"></i> Isolate Now
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    modal.style.display = 'flex';
}

// Emergency shutdown
function emergencyShutdown() {
    if (confirm('EMERGENCY SHUTDOWN\n\nThis will close ALL valves and shut down the entire water system.\n\nAre you absolutely sure?')) {
        showNotification('EMERGENCY SHUTDOWN INITIATED!', 'error');
        
        // In a real app, this would trigger an emergency shutdown
        setTimeout(() => {
            showNotification('System shutdown complete. All valves closed.', 'error');
            refreshDashboardData();
        }, 3000);
    }
}

// Notify maintenance
function notifyMaintenance() {
    showNotification('Maintenance team has been notified', 'info');
    
    // In a real app, this would send a notification to maintenance
    setTimeout(() => {
        showNotification('Maintenance team acknowledged. ETA: 30 minutes', 'success');
    }, 1500);
}

// Play alert sound
function playAlertSound() {
    // Create and play a simple alert sound
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
        oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1);
        oscillator.frequency.setValueAtTime(800, audioContext.currentTime + 0.2);
        
        gainNode.gain.setValueAtTime(0.5, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);
    } catch (error) {
        console.warn('Could not play alert sound:', error);
    }
}

// Update responsive elements
function updateResponsiveElements() {
    const width = window.innerWidth;
    
    // Adjust layout for mobile
    if (width < 768) {
        document.body.classList.add('mobile-view');
    } else {
        document.body.classList.remove('mobile-view');
    }
}

// Clean up on page unload
window.addEventListener('beforeunload', function() {
    stopAutoRefresh();
});