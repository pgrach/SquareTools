// Script for the flash welcome message when a new member created:
 
window.onload = function() {
    const flashMessage = document.getElementById("flash-message");
    if (flashMessage) {
        flashMessage.style.display = "block";
        setTimeout(function() {
            flashMessage.style.display = "none";
        }, 5000);  // Hide after 5 seconds
    }
};