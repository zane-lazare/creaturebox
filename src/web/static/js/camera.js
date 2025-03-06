document.addEventListener('DOMContentLoaded', function() {
    // Camera settings elements
    const imageFormat = document.getElementById('image-format');
    const exposureTime = document.getElementById('exposure-time');
    const exposureTimeValue = document.getElementById('exposure-time-value');
    const analogGain = document.getElementById('analog-gain');
    const analogGainValue = document.getElementById('analog-gain-value');
    const lensPosition = document.getElementById('lens-position');
    const lensPositionValue = document.getElementById('lens-position-value');
    
    // HDR settings elements
    const hdrToggle = document.getElementById('hdr-toggle');
    const hdrPhotos = document.getElementById('hdr-photos');
    const hdrWidth = document.getElementById('hdr-width');
    const hdrSettings = document.querySelectorAll('.hdr-setting');
    
    // Camera action buttons
    const btnStreamStart = document.getElementById('btn-stream-start');
    const btnCalibrate = document.getElementById('btn-calibrate');
    const btnCapture = document.getElementById('btn-capture');
    const btnSaveSettings = document.getElementById('btn-save-settings');
    
    // Camera stream element
    const cameraStream = document.getElementById('camera-stream');
    const cameraOverlay = document.querySelector('.camera-overlay');
    
    // Initialize camera settings from server
    function loadCameraSettings() {
        api.get('/camera/settings')
            .then(settings => {
                // Update image format
                if (imageFormat && settings.ImageFileType) {
                    imageFormat.value = settings.ImageFileType;
                }
                
                // Update exposure time
                if (exposureTime && settings.ExposureTime) {
                    const expValue = parseInt(settings.ExposureTime);
                    exposureTime.value = expValue;
                    exposureTimeValue.textContent = expValue;
                }
                
                // Update analog gain
                if (analogGain && settings.AnalogueGain) {
                    const gainValue = parseFloat(settings.AnalogueGain);
                    analogGain.value = gainValue;
                    analogGainValue.textContent = gainValue.toFixed(1);
                }
                
                // Update lens position
                if (lensPosition && settings.LensPosition) {
                    const posValue = parseFloat(settings.LensPosition);
                    lensPosition.value = posValue;
                    lensPositionValue.textContent = posValue.toFixed(1);
                }
                
                // Update HDR settings
                if (hdrToggle && settings.HDR) {
                    const hdrValue = parseInt(settings.HDR);
                    hdrToggle.checked = hdrValue >= 3;
                    toggleHDRSettings(hdrValue >= 3);
                    
                    if (hdrValue >= 3) {
                        hdrPhotos.value = hdrValue;
                    }
                }
                
                if (hdrWidth && settings.HDR_width) {
                    hdrWidth.value = settings.HDR_width;
                }
                
                // Update other camera settings
                if (settings.AutoCalibration) {
                    document.getElementById('auto-calibration').checked = settings.AutoCalibration === '1';
                }
                
                if (settings.VerticalFlip) {
                    document.getElementById('vertical-flip').checked = settings.VerticalFlip === '1';
                }
                
                if (settings.AwbMode) {
                    document.getElementById('awb-mode').value = settings.AwbMode;
                }
                
                if (settings.AfMode) {
                    document.getElementById('focus-mode').value = settings.AfMode;
                }
            })
            .catch(error => {
                showMessage('Error loading camera settings: ' + error.message, 'error');
            });
    }
    
    // Toggle HDR settings visibility
    function toggleHDRSettings(enabled) {
        hdrSettings.forEach(setting => {
            setting.style.display = enabled ? 'flex' : 'none';
        });
    }
    
    // Update range input display values
    if (exposureTime) {
        exposureTime.addEventListener('input', function() {
            exposureTimeValue.textContent = this.value;
        });
    }
    
    if (analogGain) {
        analogGain.addEventListener('input', function() {
            analogGainValue.textContent = parseFloat(this.value).toFixed(1);
        });
    }
    
    if (lensPosition) {
        lensPosition.addEventListener('input', function() {
            lensPositionValue.textContent = parseFloat(this.value).toFixed(1);
        });
    }
    
    // Toggle HDR settings visibility
    if (hdrToggle) {
        hdrToggle.addEventListener('change', function() {
            toggleHDRSettings(this.checked);
        });
    }
    
    // Start camera stream
    if (btnStreamStart) {
        btnStreamStart.addEventListener('click', function() {
            cameraOverlay.style.display = 'none';
            cameraStream.src = '/api/camera/stream';
            
            // Add stop stream button
            const stopButton = document.createElement('button');
            stopButton.className = 'btn danger camera-stop-btn';
            stopButton.innerHTML = '<i class="fas fa-stop"></i> Stop Stream';
            stopButton.style.position = 'absolute';
            stopButton.style.bottom = '10px';
            stopButton.style.right = '10px';
            
            stopButton.addEventListener('click', function() {
                cameraStream.src = 'img/camera-placeholder.jpg';
                this.remove();
                cameraOverlay.style.display = 'flex';
            });
            
            document.querySelector('.camera-feed').appendChild(stopButton);
        });
    }
    
    // Camera calibration
    if (btnCalibrate) {
        btnCalibrate.addEventListener('click', function() {
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Calibrating...';
            
            api.post('/camera/calibrate')
                .then(response => {
                    showMessage('Camera calibrated successfully!');
                    // Reload camera settings to get the new calibrated values
                    loadCameraSettings();
                })
                .catch(error => {
                    showMessage('Error calibrating camera: ' + error.message, 'error');
                })
                .finally(() => {
                    this.disabled = false;
                    this.innerHTML = '<i class="fas fa-sync"></i> Calibrate';
                });
        });
    }
    
    // Capture photo
    if (btnCapture) {
        btnCapture.addEventListener('click', function() {
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Capturing...';
            
            api.post('/camera/capture')
                .then(response => {
                    showMessage('Photo captured successfully!');
                })
                .catch(error => {
                    showMessage('Error capturing photo: ' + error.message, 'error');
                })
                .finally(() => {
                    this.disabled = false;
                    this.innerHTML = '<i class="fas fa-camera"></i> Capture';
                });
        });
    }
    
    // Save camera settings
    if (btnSaveSettings) {
        btnSaveSettings.addEventListener('click', function() {
            const settings = {
                ImageFileType: imageFormat ? imageFormat.value : '0',
                ExposureTime: exposureTime ? exposureTime.value : '500',
                AnalogueGain: analogGain ? analogGain.value : '1.5',
                LensPosition: lensPosition ? lensPosition.value : '6.0',
                HDR: hdrToggle && hdrToggle.checked ? hdrPhotos.value : '0',
                HDR_width: hdrWidth ? hdrWidth.value : '7000',
                AutoCalibration: document.getElementById('auto-calibration') ? 
                    (document.getElementById('auto-calibration').checked ? '1' : '0') : '0',
                AutoCalibrationPeriod: document.getElementById('cal-period') ? 
                    document.getElementById('cal-period').value : '600',
                VerticalFlip: document.getElementById('vertical-flip') ? 
                    (document.getElementById('vertical-flip').checked ? '1' : '0') : '0',
                AwbMode: document.getElementById('awb-mode') ? 
                    document.getElementById('awb-mode').value : '0',
                AfMode: document.getElementById('focus-mode') ? 
                    document.getElementById('focus-mode').value : '0'
            };
            
            api.post('/camera/settings', settings)
                .then(response => {
                    showMessage('Camera settings saved successfully!');
                })
                .catch(error => {
                    showMessage('Error saving camera settings: ' + error.message, 'error');
                });
        });
    }
    
    // Initialize camera settings on load
    loadCameraSettings();
    
    // Initialize HDR settings visibility
    if (hdrToggle) {
        toggleHDRSettings(hdrToggle.checked);
    }
});
