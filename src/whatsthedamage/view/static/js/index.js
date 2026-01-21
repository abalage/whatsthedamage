/**
 * Index page JavaScript functionality
 * Handles form clearing
 */

function clearForm() {
    fetch('/clear', { method: 'POST' })
        .then(response => {
            if (response.ok) {
                globalThis.location.reload();
            }
        });
}
