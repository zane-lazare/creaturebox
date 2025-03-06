document.addEventListener('DOMContentLoaded', function() {
    // Log elements
    const logType = document.getElementById('log-type');
    const logContent = document.getElementById('log-content');
    const btnRefreshLog = document.getElementById('btn-refresh-log');
    const btnDownloadLog = document.getElementById('btn-download-log');
    
    // Current log type
    let currentLogType = 'system';
    
    // Load log content
    function loadLogContent(type) {
        currentLogType = type || currentLogType;
        
        // Show loading message
        logContent.textContent = 'Loading log content...';
        
        api.get(`/logs/${currentLogType}`)
            .then(response => {
                logContent.textContent = response.content || 'No log content available';
                
                // Scroll to the bottom of the log
                logContent.scrollTop = logContent.scrollHeight;
            })
            .catch(error => {
                logContent.textContent = `Error loading log: ${error.message}`;
                showMessage('Error loading log content', 'error');
            });
    }
    
    // Download log file
    function downloadLog() {
        window.location.href = `/api/logs/${currentLogType}/download`;
    }
    
    // Event listeners
    if (logType) {
        logType.addEventListener('change', function() {
            loadLogContent(this.value);
        });
    }
    
    if (btnRefreshLog) {
        btnRefreshLog.addEventListener('click', function() {
            loadLogContent();
        });
    }
    
    if (btnDownloadLog) {
        btnDownloadLog.addEventListener('click', downloadLog);
    }
    
    // Initialize log content
    if (logType && logType.value) {
        currentLogType = logType.value;
    }
    
    loadLogContent();
});
