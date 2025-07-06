//      <h1>🌻 Sunflower Photo Log</h1>
// wrap it all to wait for DOM to load
document.addEventListener("DOMContentLoaded", function() {
    // Show upload button when file is selected
    document.getElementById('file-input').addEventListener('change', function(e) {
        const uploadButton = document.getElementById('upload-button');
        if (e.target.files.length > 0) {
            uploadButton.style.display = 'inline-block';
            uploadButton.textContent = `🌻 Confirm Upload (${e.target.files.length} photos)`;
        } else {
            uploadButton.style.display = 'none';
        }
    });
    // Auto-hide flash messages after 5 seconds
    setTimeout(function() {
        const flashMessages = document.querySelectorAll('.flash');
        flashMessages.forEach(function(message) {
            message.style.opacity = '0';
            setTimeout(function() {
                message.style.display = 'none';
            }, 300);
        });
    }, 5000);
    // Modal functionality for photo click
    const modal = document.getElementById("photo-modal");
    const modalImg = document.getElementById("modal-image");
    const modalClose = document.querySelector(".modal-close");

    document.querySelectorAll(".photo-item img").forEach(img => {
    img.addEventListener("click", function(){
        modal.style.display = "block";
        modalImg.src = this.src;
    });
    });

    modalClose.addEventListener("click", function(){
    modal.style.display = "none";
    });

    // close modal if clicked outside the image
    modal.addEventListener("click", function(e){
    if (e.target === modal) {
        modal.style.display = "none";
    }
    });
});