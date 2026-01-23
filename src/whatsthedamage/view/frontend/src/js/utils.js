/**
 * Utility functions for the What's the Damage application
 */

/**
 * Show notification message
 * @param {string} message - The message to display
 * @param {string} type - The type of notification (success, danger, etc.)
 */
export function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'alert alert-' + type + ' alert-dismissible fade show';
    notification.role = 'alert';
    notification.innerHTML = message + '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';

    // Add to page
    const main = document.querySelector('main');
    if (main) {
        main.insertBefore(notification, main.firstChild);

        // Auto-dismiss after 5 seconds
        setTimeout(function() {
            notification.classList.remove('show');
            setTimeout(function() { notification.remove(); }, 150);
        }, 5000);
    }
}
