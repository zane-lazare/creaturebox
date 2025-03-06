document.addEventListener('DOMContentLoaded', function() {
    // Gallery elements
    const dateSelect = document.getElementById('date-select');
    const galleryContainer = document.querySelector('.gallery-container');
    const photoModal = document.querySelector('.photo-modal');
    const modalImage = document.getElementById('modal-image');
    const modalTitle = document.getElementById('modal-title');
    const modalDate = document.getElementById('modal-date');
    const modalTime = document.getElementById('modal-time');
    const modalExposure = document.getElementById('modal-exposure');
    const modalFocus = document.getElementById('modal-focus');
    const btnPrev = document.getElementById('btn-prev');
    const btnNext = document.getElementById('btn-next');
    const btnDownload = document.getElementById('btn-download');
    const btnDelete = document.getElementById('btn-delete');
    
    // Store gallery data
    let galleryDates = [];
    let galleryPhotos = [];
    let currentPhotoIndex = -1;
    
    // Load available dates
    function loadGalleryDates() {
        api.get('/gallery/dates')
            .then(dates => {
                galleryDates = dates;
                
                // Clear date select options except 'All Dates'
                while (dateSelect.options.length > 1) {
                    dateSelect.remove(1);
                }
                
                // Add date options
                dates.forEach(date => {
                    const option = document.createElement('option');
                    option.value = date;
                    option.textContent = formatDateString(date);
                    dateSelect.appendChild(option);
                });
                
                // Load photos
                loadGalleryPhotos();
            })
            .catch(error => {
                console.error('Error loading gallery dates:', error);
                showMessage('Error loading gallery dates', 'error');
            });
    }
    
    // Load photos for the selected date
    function loadGalleryPhotos() {
        const date = dateSelect.value;
        const url = date === 'all' ? '/gallery/photos' : `/gallery/photos?date=${date}`;
        
        // Show loading message
        galleryContainer.innerHTML = '<div class="gallery-message">Loading photos...</div>';
        
        api.get(url)
            .then(photos => {
                galleryPhotos = photos;
                
                if (photos.length === 0) {
                    galleryContainer.innerHTML = '<div class="gallery-message">No photos found</div>';
                    return;
                }
                
                // Clear gallery container
                galleryContainer.innerHTML = '';
                
                // Add photos to gallery
                photos.forEach((photo, index) => {
                    const photoItem = document.createElement('div');
                    photoItem.className = 'photo-item';
                    photoItem.setAttribute('data-index', index);
                    
                    // Create image element
                    const img = document.createElement('img');
                    img.src = photo.thumbnailUrl;
                    img.alt = photo.filename;
                    
                    // Create info elements for list view
                    const photoInfo = document.createElement('div');
                    photoInfo.className = 'photo-info';
                    
                    const photoName = document.createElement('strong');
                    photoName.textContent = photo.filename;
                    
                    const photoDate = document.createElement('span');
                    photoDate.textContent = `${formatDateString(photo.date)} ${photo.time}`;
                    
                    photoInfo.appendChild(photoName);
                    photoInfo.appendChild(document.createElement('br'));
                    photoInfo.appendChild(photoDate);
                    
                    // Add click event to open modal
                    photoItem.addEventListener('click', function() {
                        openPhotoModal(index);
                    });
                    
                    // Add elements to photo item
                    photoItem.appendChild(img);
                    photoItem.appendChild(photoInfo);
                    
                    // Add photo item to gallery
                    galleryContainer.appendChild(photoItem);
                });
            })
            .catch(error => {
                console.error('Error loading gallery photos:', error);
                galleryContainer.innerHTML = '<div class="gallery-message">Error loading photos</div>';
                showMessage('Error loading gallery photos', 'error');
            });
    }
    
    // Open photo modal
    function openPhotoModal(index) {
        const photo = galleryPhotos[index];
        
        if (!photo) {
            return;
        }
        
        currentPhotoIndex = index;
        
        // Update modal content
        modalImage.src = photo.url;
        modalTitle.textContent = photo.filename;
        modalDate.textContent = formatDateString(photo.date);
        modalTime.textContent = photo.time;
        modalExposure.textContent = photo.exposure || 'Unknown';
        modalFocus.textContent = photo.focus || 'Unknown';
        
        // Show modal
        photoModal.style.display = 'block';
        
        // Update prev/next buttons state
        updateNavigationButtons();
    }
    
    // Close photo modal
    function closePhotoModal() {
        photoModal.style.display = 'none';
        modalImage.src = '';  // Clear image to stop loading
    }
    
    // Navigate to previous photo
    function navigateToPrevPhoto() {
        if (currentPhotoIndex > 0) {
            openPhotoModal(currentPhotoIndex - 1);
        }
    }
    
    // Navigate to next photo
    function navigateToNextPhoto() {
        if (currentPhotoIndex < galleryPhotos.length - 1) {
            openPhotoModal(currentPhotoIndex + 1);
        }
    }
    
    // Update navigation buttons state
    function updateNavigationButtons() {
        btnPrev.disabled = currentPhotoIndex <= 0;
        btnNext.disabled = currentPhotoIndex >= galleryPhotos.length - 1;
    }
    
    // Download current photo
    function downloadCurrentPhoto() {
        if (currentPhotoIndex >= 0 && currentPhotoIndex < galleryPhotos.length) {
            const photo = galleryPhotos[currentPhotoIndex];
            const downloadLink = document.createElement('a');
            downloadLink.href = `${photo.url}?download=1`;
            downloadLink.download = photo.filename;
            downloadLink.click();
        }
    }
    
    // Delete current photo
    function deleteCurrentPhoto() {
        if (currentPhotoIndex >= 0 && currentPhotoIndex < galleryPhotos.length) {
            const photo = galleryPhotos[currentPhotoIndex];
            
            if (confirm(`Are you sure you want to delete "${photo.filename}"?`)) {
                api.delete(`/gallery/photos/${encodeURIComponent(photo.filename)}`)
                    .then(response => {
                        showMessage('Photo deleted successfully');
                        closePhotoModal();
                        loadGalleryPhotos(); // Reload photos
                    })
                    .catch(error => {
                        showMessage('Error deleting photo: ' + error.message, 'error');
                    });
            }
        }
    }
    
    // Format date string from YYYY-MM-DD to readable format
    function formatDateString(dateStr) {
        if (!dateStr || !dateStr.includes('-')) {
            return dateStr;
        }
        
        const parts = dateStr.split('-');
        if (parts.length !== 3) {
            return dateStr;
        }
        
        const year = parts[0];
        const month = parts[1];
        const day = parts[2];
        
        const date = new Date(year, month - 1, day);
        return date.toLocaleDateString();
    }
    
    // Event listeners
    if (dateSelect) {
        dateSelect.addEventListener('change', loadGalleryPhotos);
    }
    
    if (btnPrev) {
        btnPrev.addEventListener('click', navigateToPrevPhoto);
    }
    
    if (btnNext) {
        btnNext.addEventListener('click', navigateToNextPhoto);
    }
    
    if (btnDownload) {
        btnDownload.addEventListener('click', downloadCurrentPhoto);
    }
    
    if (btnDelete) {
        btnDelete.addEventListener('click', deleteCurrentPhoto);
    }
    
    // Close modal when clicking the X button
    const closeModalButton = photoModal.querySelector('.close-modal');
    if (closeModalButton) {
        closeModalButton.addEventListener('click', closePhotoModal);
    }
    
    // Close modal when clicking outside the content
    photoModal.addEventListener('click', function(e) {
        if (e.target === photoModal) {
            closePhotoModal();
        }
    });
    
    // Keyboard navigation
    document.addEventListener('keydown', function(e) {
        if (photoModal.style.display === 'block') {
            if (e.key === 'ArrowLeft') {
                navigateToPrevPhoto();
            } else if (e.key === 'ArrowRight') {
                navigateToNextPhoto();
            } else if (e.key === 'Escape') {
                closePhotoModal();
            }
        }
    });
    
    // Initialize gallery
    loadGalleryDates();
});
