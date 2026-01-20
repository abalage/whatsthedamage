/**
 * Statistical Analysis JavaScript functionality
 * Handles statistical analysis controls, AJAX calls, and result visualization
 */

document.addEventListener('DOMContentLoaded', function() {
    var recalculateBtn = document.getElementById('recalculate-btn');
    var resetBtn = document.getElementById('reset-btn');

    if (recalculateBtn && resetBtn) {
        var spinner = recalculateBtn.querySelector('.spinner-border');

        // Recalculate button click handler
        recalculateBtn.addEventListener('click', function() {
            var algorithms = Array.prototype.slice.call(document.querySelectorAll('input[type="checkbox"][value]:checked'))
                .map(function(el) { return el.value; });
            var direction = document.querySelector('input[name="direction"]:checked').value;

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
                    result_id: window.resultId,
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
