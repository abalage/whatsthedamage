/**
 * Index page JavaScript functionality
 * Handles form clearing
 */

/**
 * Clear the uploaded file and reload the page
 */
export function clearForm() {
    fetch('/clear', { method: 'POST' })
        .then(response => {
            if (response.ok) {
                globalThis.location.reload();
            }
        });
}

// Auto-initialize if DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        // Make function available globally for template usage
        globalThis.clearForm = clearForm;
    });
} else {
    globalThis.clearForm = clearForm;
}
