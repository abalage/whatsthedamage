/**
 * Utility functions for the What's the Damage application
 */

/**
 * Show notification message
 * @param {string} message - The message to display
 * @param {string} type - The type of notification (success, danger, etc.)
 */
export function showNotification(message: string, type: string): void {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.role = 'alert';
    notification.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>`;

    // Add to page
    const main = document.querySelector('main');
    if (main) {
        main.insertBefore(notification, main.firstChild);

        // Auto-dismiss after 5 seconds
        const AUTO_DISMISS_TIMEOUT = 5000 // ms
        const REMOVE_DELAY = 150 // ms
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => { notification.remove(); }, REMOVE_DELAY);
        }, AUTO_DISMISS_TIMEOUT); // 5 second auto-dismiss timeout
    }
}