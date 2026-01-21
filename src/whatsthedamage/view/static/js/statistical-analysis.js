/**
 * Statistical Analysis JavaScript functionality
 * Handles statistical analysis controls, AJAX calls, and result visualization
 */

document.addEventListener('DOMContentLoaded', function() {
    const recalculateBtn = document.getElementById('recalculate-btn');
    const resetBtn = document.getElementById('reset-btn');

    if (recalculateBtn && resetBtn) {
        const spinner = recalculateBtn.querySelector('.spinner-border');

        // Recalculate button click handler
        recalculateBtn.addEventListener('click', function() {
            const algorithms = Array.prototype.slice.call(document.querySelectorAll('input[type="checkbox"][value]:checked'))
                .map(function(el) { return el.value; });
            const direction = document.querySelector('input[name="direction"]:checked').value;

            // Show loading spinner
            spinner.classList.remove('d-none');
            recalculateBtn.querySelector('span:last-child').textContent = 'Processing...';
            recalculateBtn.disabled = true;
            resetBtn.disabled = true;

            fetch('/recalculate-statistics', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    result_id: globalThis.resultId,
                    algorithms: algorithms,
                    direction: direction
                })
            })
            .then(function(response) {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(function(data) {
                if (data.status === 'success') {
                    // Update all cell highlights
                    updateCellHighlights(data.highlights);
                    showNotification('Statistics recalculated successfully!', 'success');
                } else {
                    throw new Error(data.error || 'Unknown error');
                }
            })
            .catch(function(error) {
                console.error('Error:', error);
                showNotification('Error recalculating statistics: ' + error.message, 'danger');
            })
            .finally(function() {
                // Hide loading spinner
                spinner.classList.add('d-none');
                recalculateBtn.querySelector('span:last-child').textContent = 'Recalculate';
                recalculateBtn.disabled = false;
                resetBtn.disabled = false;
            });
        });

        // Reset button click handler
        resetBtn.addEventListener('click', function() {
            // Reset checkboxes to default (both checked)
            document.getElementById('algorithm-iqr').checked = true;
            document.getElementById('algorithm-pareto').checked = true;

            // Reset radio buttons to default (columns checked)
            document.getElementById('direction-columns').checked = true;

            // Trigger recalculation with default settings
            recalculateBtn.click();
        });
    }
});

/**
 * Update cell highlights based on statistical analysis results
 * @param {Object} highlights - Object containing highlight information
 */
function updateCellHighlights(highlights) {
    // Remove all current highlights from all tables
    const highlightElements = document.querySelectorAll('[class*="highlight-"]');
    for (const el of highlightElements) {
        el.classList.remove('highlight-outlier', 'highlight-pareto', 'highlight-excluded');
    }

    // Apply new highlights - process each table separately
    const tables = document.querySelectorAll('table[data-datatable="true"]');
    for (const table of tables) {
        const thead = table.querySelector('thead');
        const tbody = table.querySelector('tbody');

        if (thead && tbody) {
            const headers = thead.querySelectorAll('th');
            const rows = tbody.querySelectorAll('tr');

            // Apply highlights for this specific table
            for (const key in highlights) {
                if (Object.prototype.hasOwnProperty.call(highlights, key)) {
                    const highlightType = highlights[key];
                    const parts = key.split('_');
                    const column = parts[0];
                    const row = parts[1];

                    // Find the row by category in this table
                    for (const tr of rows) {
                        const categoryCell = tr.querySelector('td:first-child');
                        if (categoryCell && categoryCell.textContent.trim() === row) {
                            // Find the column by month in this table
                            for (let c = 1; c < headers.length; c++) { // Skip first column (categories)
                                if (headers[c].textContent.trim() === column) {
                                    const cell = tr.querySelector('td:nth-child(' + (c + 1) + ')');
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
