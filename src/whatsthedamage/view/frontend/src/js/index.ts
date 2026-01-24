/**
 * Index page JavaScript functionality
 * Handles form clearing
 */

/**
 * Clear the uploaded file and reload the page
 */
export function clearForm(): void {
    fetch('/clear', { method: 'POST' })
        .then((response: Response) => {
            if (response.ok) {
                window.location.reload();
            }
        })
        .catch((error: Error) => {
            console.error('Error clearing form:', error);
            // Could add user notification here
        });
}

// Remove global pollution - functions are exported and imported where needed