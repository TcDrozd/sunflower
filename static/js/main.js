// main.js - centralized theme, modal, upload preview, photo modal, and lazy loader utilities

document.addEventListener("DOMContentLoaded", () => {
  // ===== theme logic =====
  const applyTheme = (theme) => {
    document.documentElement.classList.remove('sun-theme', 'lunar-theme');
    if (theme === 'sun') document.documentElement.classList.add('sun-theme');
    if (theme === 'lunar') document.documentElement.classList.add('lunar-theme');
    localStorage.setItem('theme', theme);
    document.getElementById('sunBtn')?.classList.toggle('active', theme === 'sun');
    document.getElementById('lunarBtn')?.classList.toggle('active', theme === 'lunar');
  };

  document.getElementById('sunBtn')?.addEventListener('click', () => applyTheme('sun'));
  document.getElementById('lunarBtn')?.addEventListener('click', () => applyTheme('lunar'));
  applyTheme(localStorage.getItem('theme') || 'sun');

  // ===== modal utilities =====
  window.showModal = function(modalId) {
    const m = document.getElementById(modalId);
    if (m) m.style.display = 'block';
  };
  window.hideModal = function(modalId) {
    const m = document.getElementById(modalId);
    if (m) m.style.display = 'none';
  };
  window.addEventListener('click', (event) => {
    document.querySelectorAll('.modal').forEach(modal => {
      if (event.target === modal) {
        modal.style.display = 'none';
      }
    });
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal').forEach(m => { m.style.display = 'none'; });
    }
  });

  // ===== upload preview & confirm flow =====
  let selectedFiles = [];
  const photoInput = document.getElementById('photoInput');
  if (photoInput) {
    photoInput.addEventListener('change', function(e) {
      selectedFiles = Array.from(e.target.files);
      if (selectedFiles.length > 0) {
        showUploadPreview();
      }
    });
  }

  function showUploadPreview() {
    const preview = document.getElementById('filePreview');
    if (!preview) return;
    preview.innerHTML = '<h3>Selected Photos:</h3>';
    selectedFiles.forEach((file) => {
      const fileDiv = document.createElement('div');
      fileDiv.className = 'file-preview';
      fileDiv.innerHTML = `
        <div class="file-info">
          <strong>📷 ${file.name}</strong> (${(file.size / 1024 / 1024).toFixed(2)} MB)
        </div>
        <div style="font-size: 0.9rem; color: #666;">
          Type: ${file.type} | Last modified: ${new Date(file.lastModified).toLocaleDateString()}
        </div>
      `;
      preview.appendChild(fileDiv);
    });
    showModal('uploadModal');
  }

  window.confirmUpload = function() {
    if (!selectedFiles || selectedFiles.length === 0) return;
    const uploadLoading = document.getElementById('uploadLoading');
    const confirmUploadBtn = document.getElementById('confirmUploadBtn');
    const successMessage = document.getElementById('successMessage');
    const errorMessage = document.getElementById('errorMessage');

    if (uploadLoading) uploadLoading.style.display = 'block';
    if (confirmUploadBtn) confirmUploadBtn.style.display = 'none';
    if (successMessage) successMessage.style.display = 'none';
    if (errorMessage) errorMessage.style.display = 'none';

    const formData = new FormData();
    selectedFiles.forEach(file => {
      formData.append('photos', file);
    });

    fetch('/upload', { method: 'POST', body: formData })
        .then(async response => {
            if (!response.ok) {
            const text = await response.text();
            throw new Error(`Upload failed: ${response.status} ${text}`);
            }
            try {
            return await response.json();
            } catch (e) {
            throw new Error('Invalid JSON from server: ' + e.message);
            }
        })
        .then(data => {
            if (uploadLoading) uploadLoading.style.display = 'none';
            if (data.success) {
            if (successMessage) {
                successMessage.innerHTML = data.message || 'Uploaded successfully.';
                successMessage.style.display = 'block';
            }
            setTimeout(() => { window.location.reload(); }, 1500);
            } else {
            if (errorMessage) {
                errorMessage.innerHTML = data.error || 'Upload failed';
                errorMessage.style.display = 'block';
            }
            if (confirmUploadBtn) confirmUploadBtn.style.display = 'inline-block';
            }
        })
        .catch(error => {
            if (uploadLoading) uploadLoading.style.display = 'none';
            if (errorMessage) {
            errorMessage.innerHTML = 'Network error: ' + error.message;
            errorMessage.style.display = 'block';
            }
            if (confirmUploadBtn) confirmUploadBtn.style.display = 'inline-block';
        });
  };

// ===== photo detail modal loader =====
window.showPhotoModal = function(photoId) {
  fetch(`/photo/${photoId}`, { cache: 'no-cache' })
    .then(res => res.json())
    .then(photo => {
      const baseName = photo.filename;
      const imgSrc = `/static/uploads/${baseName}`;

      const modalTitleEl = document.getElementById('photoModalTitle');
      if (modalTitleEl) {
        modalTitleEl.textContent = photo.date_taken
          ? `Photo from ${photo.date_taken}`
          : `Photo: ${photo.original_filename || baseName || 'Untitled'}`;
      }

      let cameraInfo = '';
      if (photo.camera_info && Object.keys(photo.camera_info).length > 0) {
        cameraInfo = '<div class="exif-info"><h3>📷 Camera Information</h3><div class="exif-grid">';
        const labels = {
          make: 'Camera Make',
          model: 'Camera Model',
          lens: 'Lens',
          focal_length: 'Focal Length',
          aperture: 'Aperture',
          iso: 'ISO',
          shutter_speed: 'Shutter Speed'
        };
        for (const [key, val] of Object.entries(photo.camera_info)) {
          if (val) {
            const label = labels[key] || key.replace('_', ' ').toUpperCase();
            cameraInfo += `
              <div class="exif-item">
                <span class="exif-label">${label}:</span>
                <span class="exif-value">${val}</span>
              </div>`;
          }
        }
        cameraInfo += '</div></div>';
      }

      const bodyEl = document.getElementById('photoModalBody');
      if (bodyEl) {
        bodyEl.innerHTML = `
          <img src="${imgSrc}" alt="Sunflower photo" class="modal-image">
          <div style="margin-bottom: 1rem;">
            <h3>${photo.original_filename || baseName}</h3>
            <p><strong>📅 Date Taken:</strong> ${photo.date_taken || 'Unknown'}${photo.time_taken ? ' at ' + photo.time_taken : ''}</p>
            <p><strong>📤 Uploaded:</strong> ${photo.upload_date ? new Date(photo.upload_date).toLocaleDateString() : 'Unknown'}</p>
          </div>
          ${cameraInfo}
          <button id="deletePhotoBtn" class="btn danger" style="margin-top: 1rem;">🗑️ Delete Photo</button>
        `;
      }

      const deleteBtn = document.getElementById('deletePhotoBtn');
      if (deleteBtn && photo.id != null) {
        deleteBtn.onclick = () => {
          if (confirm('Are you sure you want to delete this photo?')) {
            fetch(`/delete/${photo.id}`, { method: 'DELETE' })
              .then(res => res.json())
              .then(data => {
                if (data.success) {
                  hideModal('photoModal');
                  window.location.reload();
                } else {
                  alert(data.error || 'Failed to delete photo.');
                }
              })
              .catch(() => alert('An error occurred while deleting the photo.'));
          }
        };
      }

      showModal('photoModal');
    })
    .catch(error => {
      console.error('Error loading photo details:', error);
      const bodyEl = document.getElementById('photoModalBody');
      if (bodyEl) {
        bodyEl.innerHTML = '<p>Error loading photo details.</p>';
      }
      showModal('photoModal');
    });
};

  // ===== lazy loader =====
  const lazyImages = Array.from(document.querySelectorAll('img.lazy'));
  if ('IntersectionObserver' in window && lazyImages.length) {
    const observer = new IntersectionObserver((entries, obs) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          const highRes = img.dataset.src;
          if (highRes) {
            const temp = new Image();
            temp.src = highRes;
            temp.onload = () => {
              img.src = highRes;
              img.classList.remove('lazy');
              img.classList.add('loaded');
            };
          }
          obs.unobserve(img);
        }
      });
    }, { rootMargin: '100px', threshold: 0.1 });
    lazyImages.forEach(img => observer.observe(img));
  } else {
    // fallback: upgrade all after short delay
    setTimeout(() => {
      lazyImages.forEach(img => {
        const highRes = img.dataset.src;
        if (highRes) {
          img.src = highRes;
          img.classList.remove('lazy');
          img.classList.add('loaded');
        }
      });
    }, 500);
  }
});