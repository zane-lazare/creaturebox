document.addEventListener('DOMContentLoaded', function() {
    // Dashboard button event handlers
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

    // Update dashboard status indicators based on initial data
    // This will run once at startup to set initial appearance
    function updateDashboardAppearance() {
        // Update dashboard UI based on system state
        api.get('/system/status')
            .then(data => {
                // Set button states based on current status
                if (data.power && data.power.lightsOn) {
                    btnToggleLights.innerHTML = '<i class="fas fa-lightbulb"></i> Lights On';
                } else {
                    btnToggleLights.innerHTML = '<i class="far fa-lightbulb"></i> Lights Off';
                }
            })
            .catch(error => {
                console.error('Error updating dashboard appearance:', error);
            });
    }

    // Initialize dashboard appearance
    updateDashboardAppearance();
});
