/**
 * Utility functions for the What's the Damage application
 */

/**
 * Show notification message
 * @param {string} message - The message to display
 * @param {string} type - The type of notification (success, danger, etc.)
 */
function showNotification(message, type) {
    // Create notification element
    var notification = document.createElement('div');
    notification.className = 'alert alert-' + type + ' alert-dismissible fade show';
    notification.role = 'alert';
    notification.innerHTML = message + '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';

    // Add to page
    var main = document.querySelector('main');
    if (main) {
        main.insertBefore(notification, main.firstChild);

        // Auto-dismiss after 5 seconds
        setTimeout(function() {
            notification.classList.remove('show');
            setTimeout(function() { notification.remove(); }, 150);
        }, 5000);
    }
}

/**
 * Update cell highlights based on statistical analysis results
 * @param {Object} highlights - Object containing highlight information
 */
function updateCellHighlights(highlights) {
    // Remove all current highlights from all tables
    var highlightElements = document.querySelectorAll('[class*="highlight-"]');
    for (var i = 0; i < highlightElements.length; i++) {
        var el = highlightElements[i];
        el.classList.remove('highlight-outlier', 'highlight-pareto', 'highlight-excluded');
    }

    // Apply new highlights - process each table separately
    var tables = document.querySelectorAll('table[data-datatable="true"]');
    for (var t = 0; t < tables.length; t++) {
        var table = tables[t];
        var thead = table.querySelector('thead');
        var tbody = table.querySelector('tbody');

        if (thead && tbody) {
            var headers = thead.querySelectorAll('th');
            var rows = tbody.querySelectorAll('tr');

            // Apply highlights for this specific table
            for (var key in highlights) {
                if (highlights.hasOwnProperty(key)) {
                    var highlightType = highlights[key];
                    var parts = key.split('_');
                    var column = parts[0];
                    var row = parts[1];

                    // Find the row by category in this table
                    for (var r = 0; r < rows.length; r++) {
                        var tr = rows[r];
                        var categoryCell = tr.querySelector('td:first-child');
                        if (categoryCell && categoryCell.textContent.trim() === row) {
                            // Find the column by month in this table
                            for (var c = 1; c < headers.length; c++) { // Skip first column (categories)
                                if (headers[c].textContent.trim() === column) {
                                    var cell = tr.querySelector('td:nth-child(' + (c + 1) + ')');
                                    if (cell) {
                                        cell.classList.add('highlight-' + highlightType);
                                    }
                                    break;
                                }
                            }
                            break;
                        }
                    }
                }
            }
        }
    }
}
