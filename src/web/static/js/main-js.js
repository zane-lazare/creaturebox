document.addEventListener('DOMContentLoaded', function() {
    // Navigation handling
    const navLinks = document.querySelectorAll('nav a');
    const pages = document.querySelectorAll('.page');

    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Get the page id from data attribute
            const targetPageId = this.getAttribute('data-page');
            
            // Remove active class from all nav links
            navLinks.forEach(link => link.classList.remove('active'));
            
            // Add active class to clicked link
            this.classList.add('active');
            
            // Hide all pages
            pages.forEach(page => page.classList.remove('active'));
            
            // Show target page
            document.getElementById(targetPageId).classList.add('active');
        });
    });

    // Tab navigation
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');
            
            // Remove active class from all tab buttons
            tabButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Hide all tab contents
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Show target tab content
            document.getElementById(targetTab).classList.add('active');
        });
    });

    // Gallery view toggle
    const viewGrid = document.getElementById('view-grid');
    const viewList = document.getElementById('view-list');
    const galleryContainer = document.querySelector('.gallery-container');

    if (viewGrid && viewList) {
        viewGrid.addEventListener('click', function() {
            viewGrid.classList.add('active');
            viewList.classList.remove('active');
            galleryContainer.classList.add('grid-view');
            galleryContainer.classList.remove('list-view');
        });

        viewList.addEventListener('click', function() {
            viewList.classList.add('active');
            viewGrid.classList.remove('active');
            galleryContainer.classList.add('list-view');
            galleryContainer.classList.remove('grid-view');
        });
    }

    // Modal handling
    const modals = document.querySelectorAll('.modal');
    const closeButtons = document.querySelectorAll('.close-modal');
    const aboutLink = document.getElementById('about-link');
    const helpLink = document.getElementById('help-link');
    const aboutModal = document.getElementById('about-modal');
    const helpModal = document.getElementById('help-modal');

    // Close modals when clicking the X button
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            modal.style.display = 'none';
        });
    });

    // Close modals when clicking outside content
    modals.forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.style.display = 'none';
            }
        });
    });

    // Open about modal
    if (aboutLink) {
        aboutLink.addEventListener('click', function(e) {
            e.preventDefault();
            aboutModal.style.display = 'block';
        });
    }

    // Open help modal
    if (helpLink) {
        helpLink.addEventListener('click', function(e) {
            e.preventDefault();
            helpModal.style.display = 'block';
        });
    }

    // Create hours grid
    const hoursGrid = document.querySelector('.hours-grid');
    if (hoursGrid) {
        for (let i = 0; i < 24; i++) {
            const hourBox = document.createElement('div');
            hourBox.className = 'hour-box';
            hourBox.setAttribute('data-hour', i);
            hourBox.textContent = i < 10 ? `0${i}:00` : `${i}:00`;
            
            hourBox.addEventListener('click', function() {
                this.classList.toggle('selected');
            });
            
            hoursGrid.appendChild(hourBox);
        }
    }

    // API utilities
    window.api = {
        baseUrl: '/api',

        /**
         * Makes an API request
         * @param {string} endpoint - API endpoint
         * @param {Object} options - Fetch options
         * @returns {Promise} - Fetch promise
         */
        request: async function(endpoint, options = {}) {
            const url = `${this.baseUrl}${endpoint}`;
            
            const defaultOptions = {
                headers: {
                    'Content-Type': 'application/json'
                }
            };
            
            const fetchOptions = { ...defaultOptions, ...options };
            
            try {
                const response = await fetch(url, fetchOptions);
                
                if (!response.ok) {
                    throw new Error(`API error: ${response.status}`);
                }
                
                // Check if response is JSON
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    return await response.json();
                }
                
                return await response.text();
            } catch (error) {
                console.error('API request failed:', error);
                throw error;
            }
        },

        /**
         * Makes a GET request
         * @param {string} endpoint - API endpoint
         * @returns {Promise} - Fetch promise
         */
        get: function(endpoint) {
            return this.request(endpoint, { method: 'GET' });
        },

        /**
         * Makes a POST request with JSON data
         * @param {string} endpoint - API endpoint
         * @param {Object} data - Data to send
         * @returns {Promise} - Fetch promise
         */
        post: function(endpoint, data) {
            return this.request(endpoint, {
                method: 'POST',
                body: JSON.stringify(data)
            });
        },

        /**
         * Makes a DELETE request
         * @param {string} endpoint - API endpoint
         * @returns {Promise} - Fetch promise
         */
        delete: function(endpoint) {
            return this.request(endpoint, { method: 'DELETE' });
        }
    };

    // Dashboard functionality
    const loadDashboardData = () => {
        api.get('/system/status')
            .then(data => {
                // Update system info
                document.getElementById('device-name').textContent = data.system.deviceName;
                document.getElementById('uptime').textContent = formatDuration(data.system.uptime);
                document.getElementById('cpu-temp').textContent = `${data.system.cpuTemp}°C`;
                document.getElementById('cpu-usage').textContent = `${data.system.cpuUsage}%`;
                document.getElementById('memory-usage').textContent = `${data.system.memoryUsage}%`;
                
                // Update power info
                document.getElementById('power-source').textContent = data.power.source;
                document.getElementById('battery-level').style.width = `${data.power.batteryLevel}%`;
                document.getElementById('battery-percentage').textContent = `${data.power.batteryLevel}%`;
                document.getElementById('power-current').textContent = `${data.power.current} mA`;
                document.getElementById('power-voltage').textContent = `${data.power.voltage} V`;
                
                // Update storage info
                const internalPercentage = (data.storage.internalUsed / data.storage.internalTotal) * 100;
                document.getElementById('storage-internal').style.width = `${internalPercentage}%`;
                document.getElementById('storage-internal-text').textContent = 
                    `${internalPercentage.toFixed(1)}% (${formatBytes(data.storage.internalUsed)} / ${formatBytes(data.storage.internalTotal)})`;
                
                document.getElementById('photos-count').textContent = 
                    `${data.storage.photosCount} photos (${formatBytes(data.storage.photosSize)})`;
                
                if (data.storage.externalConnected) {
                    const externalPercentage = (data.storage.externalUsed / data.storage.externalTotal) * 100;
                    document.getElementById('storage-external').style.width = `${externalPercentage}%`;
                    document.getElementById('storage-external-text').textContent = 
                        `${externalPercentage.toFixed(1)}% (${formatBytes(data.storage.externalUsed)} / ${formatBytes(data.storage.externalTotal)})`;
                } else {
                    document.getElementById('storage-external').style.width = '0%';
                    document.getElementById('storage-external-text').textContent = 'Not connected';
                }
                
                // Update schedule info
                document.getElementById('current-mode').textContent = data.schedule.mode;
                document.getElementById('next-wake').textContent = formatDateTime(data.schedule.nextWake);
                document.getElementById('last-photo').textContent = formatDateTime(data.schedule.lastPhoto);
                document.getElementById('runtime').textContent = `${data.schedule.runtime} minutes`;
                
                // Update system status
                const statusIndicator = document.querySelector('.status-indicator');
                statusIndicator.className = 'status-indicator';
                statusIndicator.classList.add(data.system.status.toLowerCase());
                document.querySelector('.status-indicator .text').textContent = data.system.status;
            })
            .catch(error => {
                console.error('Error loading dashboard data:', error);
            });
    };

    // Format timestamp to readable date/time
    function formatDateTime(timestamp) {
        if (!timestamp) return 'Never';
        
        const date = new Date(timestamp * 1000);
        return date.toLocaleString();
    }

    // Format time duration
    function formatDuration(seconds) {
        if (!seconds || seconds <= 0) return '0s';
        
        const days = Math.floor(seconds / 86400);
        seconds %= 86400;
        const hours = Math.floor(seconds / 3600);
        seconds %= 3600;
        const minutes = Math.floor(seconds / 60);
        seconds %= 60;
        
        let result = '';
        if (days > 0) result += `${days}d `;
        if (hours > 0) result += `${hours}h `;
        if (minutes > 0) result += `${minutes}m `;
        if (seconds > 0) result += `${seconds}s`;
        
        return result.trim();
    }

    // Format bytes to human-readable size
    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }

    // Handle dashboard button clicks
    const btnTakePhoto = document.getElementById('btn-take-photo');
    if (btnTakePhoto) {
        btnTakePhoto.addEventListener('click', function() {
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Taking photo...';
            
            api.post('/camera/capture')
                .then(response => {
                    showMessage('Photo captured successfully!');
                    // Refresh dashboard data
                    loadDashboardData();
                })
                .catch(error => {
                    showMessage('Error taking photo: ' + error.message, 'error');
                })
                .finally(() => {
                    this.disabled = false;
                    this.innerHTML = '<i class="fas fa-camera"></i> Take Photo';
                });
        });
    }
    
    const btnToggleLights = document.getElementById('btn-toggle-lights');
    if (btnToggleLights) {
        btnToggleLights.addEventListener('click', function() {
            this.disabled = true;
            
            api.post('/system/toggle-lights')
                .then(response => {
                    // Update button text based on response
                    if (response.lightsOn) {
                        this.innerHTML = '<i class="fas fa-lightbulb"></i> Lights On';
                        showMessage('Lights turned on');
                    } else {
                        this.innerHTML = '<i class="far fa-lightbulb"></i> Lights Off';
                        showMessage('Lights turned off');
                    }
                })
                .catch(error => {
                    showMessage('Error toggling lights: ' + error.message, 'error');
                })
                .finally(() => {
                    this.disabled = false;
                });
        });
    }
    
    const btnReboot = document.getElementById('btn-reboot');
    if (btnReboot) {
        btnReboot.addEventListener('click', function() {
            if (confirm('Are you sure you want to reboot the system?')) {
                this.disabled = true;
                this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Rebooting...';
                
                api.post('/system/reboot')
                    .then(() => {
                        showMessage('System is rebooting. The page will refresh in 60 seconds.', 'warning', 60000);
                        // Set timeout to refresh the page after 60 seconds
                        setTimeout(() => {
                            window.location.reload();
                        }, 60000);
                    })
                    .catch(error => {
                        showMessage('Error rebooting system: ' + error.message, 'error');
                        this.disabled = false;
                        this.innerHTML = '<i class="fas fa-sync"></i> Reboot';
                    });
            }
        });
    }
    
    const btnShutdown = document.getElementById('btn-shutdown');
    if (btnShutdown) {
        btnShutdown.addEventListener('click', function() {
            if (confirm('Are you sure you want to shut down the system?')) {
                this.disabled = true;
                this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Shutting down...';
                
                api.post('/system/shutdown')
                    .then(() => {
                        showMessage('System is shutting down. This page will no longer be accessible.', 'warning');
                    })
                    .catch(error => {
                        showMessage('Error shutting down system: ' + error.message, 'error');
                        this.disabled = false;
                        this.innerHTML = '<i class="fas fa-power-off"></i> Shutdown';
                    });
            }
        });
    }

    // Function to show status messages
    function showMessage(message, type = 'success', duration = 5000) {
        // Check if message container exists, if not create it
        let messageContainer = document.querySelector('.message-container');
        if (!messageContainer) {
            messageContainer = document.createElement('div');
            messageContainer.className = 'message-container';
            document.querySelector('main').prepend(messageContainer);
            
            // Add styles for the message container
            const style = document.createElement('style');
            style.textContent = `
                .message-container {
                    position: sticky;
                    top: 0;
                    left: 0;
                    right: 0;
                    z-index: 1000;
                }
                .message {
                    padding: 0.75rem;
                    margin-bottom: 1rem;
                    border-radius: var(--border-radius);
                    color: white;
                    animation: slideDown 0.3s ease-out;
                }
                .message.success {
                    background-color: var(--success-color);
                }
                .message.error {
                    background-color: var(--danger-color);
                }
                .message.warning {
                    background-color: var(--warning-color);
                }
                @keyframes slideDown {
                    from { transform: translateY(-100%); }
                    to { transform: translateY(0); }
                }
            `;
            document.head.appendChild(style);
        }
        
        // Create message element
        const messageElement = document.createElement('div');
        messageElement.className = `message ${type}`;
        messageElement.textContent = message;
        
        // Add to container
        messageContainer.appendChild(messageElement);
        
        // Remove after duration
        setTimeout(() => {
            messageElement.remove();
        }, duration);
    }

    // Load dashboard data on page load
    loadDashboardData();
    
    // Refresh dashboard data every 10 seconds
    setInterval(loadDashboardData, 10000);