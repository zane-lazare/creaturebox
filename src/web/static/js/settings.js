document.addEventListener('DOMContentLoaded', function() {
    // Schedule form elements
    const scheduleForm = document.getElementById('schedule-form');
    const weekdayCheckboxes = document.querySelectorAll('input[name="weekday"]');
    const utcOffset = document.getElementById('utc-offset');
    const runtime = document.getElementById('runtime');
    const onlyFlash = document.getElementById('only-flash');
    
    // Network form elements
    const networkForm = document.getElementById('network-form');
    const wifiSsidInput = document.getElementById('wifi-ssid-input');
    const wifiPassword = document.getElementById('wifi-password');
    
    // Camera settings form elements
    const cameraSettingsForm = document.getElementById('camera-settings-form');
    
    // Power settings form elements
    const powerSettingsForm = document.getElementById('power-settings-form');
    const powerOffOnHalt = document.getElementById('power-off-on-halt');
    const wakeOnGpio = document.getElementById('wake-on-gpio');
    
    // Load schedule settings
    function loadScheduleSettings() {
        api.get('/schedule/settings')
            .then(settings => {
                // Update weekday checkboxes
                if (settings.weekday) {
                    const days = settings.weekday.split(';');
                    weekdayCheckboxes.forEach(checkbox => {
                        checkbox.checked = days.includes(checkbox.value);
                    });
                }
                
                // Update hours grid
                if (settings.hour) {
                    const hours = settings.hour.split(';');
                    const hourBoxes = document.querySelectorAll('.hour-box');
                    hourBoxes.forEach(box => {
                        const hour = box.getAttribute('data-hour');
                        box.classList.toggle('selected', hours.includes(hour));
                    });
                }
                
                // Update other settings
                if (settings.utc_off) {
                    utcOffset.value = settings.utc_off;
                }
                
                if (settings.runtime) {
                    runtime.value = settings.runtime;
                }
                
                if (settings.onlyflash) {
                    onlyFlash.value = settings.onlyflash;
                }
            })
            .catch(error => {
                showMessage('Error loading schedule settings: ' + error.message, 'error');
            });
    }
    
    // Load network settings
    function loadNetworkSettings() {
        api.get('/network/status')
            .then(status => {
                document.getElementById('wifi-status').textContent = status.connected ? 'Connected' : 'Disconnected';
                document.getElementById('wifi-ssid').textContent = status.ssid || 'None';
                document.getElementById('wifi-ip').textContent = status.ip || 'Not available';
                document.getElementById('wifi-signal').textContent = status.connected ? 
                    `${status.signalStrength}%` : 'N/A';
            })
            .catch(error => {
                console.error('Error loading network status:', error);
            });
    }
    
    // Load power settings
    function loadPowerSettings() {
        api.get('/system/power')
            .then(settings => {
                document.getElementById('pi-model').textContent = `Raspberry Pi ${settings.piModel || 'Unknown'}`;
                document.getElementById('power-manager').textContent = settings.powerManager || 'Unknown';
                
                if (powerOffOnHalt) {
                    powerOffOnHalt.checked = settings.POWER_OFF_ON_HALT === '1';
                }
                
                if (wakeOnGpio) {
                    wakeOnGpio.checked = settings.WAKE_ON_GPIO === '1';
                }
            })
            .catch(error => {
                console.error('Error loading power settings:', error);
            });
    }
    
    // Save schedule settings
    if (scheduleForm) {
        scheduleForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get selected weekdays
            const selectedDays = [];
            weekdayCheckboxes.forEach(checkbox => {
                if (checkbox.checked) {
                    selectedDays.push(checkbox.value);
                }
            });
            
            // Get selected hours
            const selectedHours = [];
            const hourBoxes = document.querySelectorAll('.hour-box.selected');
            hourBoxes.forEach(box => {
                selectedHours.push(box.getAttribute('data-hour'));
            });
            
            // Build settings object
            const settings = {
                weekday: selectedDays.join(';'),
                hour: selectedHours.join(';'),
                utc_off: utcOffset.value,
                runtime: runtime.value,
                onlyflash: onlyFlash.value
            };
            
            // Submit settings
            api.post('/schedule/settings', settings)
                .then(response => {
                    showMessage('Schedule settings saved successfully!');
                })
                .catch(error => {
                    showMessage('Error saving schedule settings: ' + error.message, 'error');
                });
        });
    }
    
    // Add new WiFi network
    if (networkForm) {
        networkForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (!wifiSsidInput.value || !wifiPassword.value) {
                showMessage('Please enter both SSID and password', 'error');
                return;
            }
            
            const networkData = {
                ssid: wifiSsidInput.value,
                wifipass: wifiPassword.value
            };
            
            api.post('/network/add', networkData)
                .then(response => {
                    showMessage('WiFi network added successfully! Connection attempt in progress...');
                    // Clear form
                    wifiSsidInput.value = '';
                    wifiPassword.value = '';
                    
                    // Reload network status after a delay
                    setTimeout(loadNetworkSettings, 10000);
                })
                .catch(error => {
                    showMessage('Error adding WiFi network: ' + error.message, 'error');
                });
        });
    }
    
    // Save camera settings
    if (cameraSettingsForm) {
        cameraSettingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const settings = {};
            
            for (const [key, value] of formData.entries()) {
                settings[key] = value;
            }
            
            api.post('/camera/settings', settings)
                .then(response => {
                    showMessage('Camera settings saved successfully!');
                })
                .catch(error => {
                    showMessage('Error saving camera settings: ' + error.message, 'error');
                });
        });
    }
    
    // Save power settings
    if (powerSettingsForm) {
        powerSettingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const settings = {
                POWER_OFF_ON_HALT: powerOffOnHalt.checked ? '1' : '0',
                WAKE_ON_GPIO: wakeOnGpio.checked ? '1' : '0'
            };
            
            api.post('/system/power', settings)
                .then(response => {
                    showMessage('Power settings saved successfully!');
                })
                .catch(error => {
                    showMessage('Error saving power settings: ' + error.message, 'error');
                });
        });
    }
    
    // Initialize settings data
    loadScheduleSettings();
    loadNetworkSettings();
    loadPowerSettings();
});
