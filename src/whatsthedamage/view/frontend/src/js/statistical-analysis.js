/**
 * Statistical Analysis JavaScript functionality
 * Handles statistical analysis controls, AJAX calls, and result visualization
 */

import { showNotification } from './utils';

/**
 * Initialize statistical analysis controls
 */
export function initStatisticalAnalysis() {
    const recalculateBtn = document.getElementById('recalculate-btn');
    const resetBtn = document.getElementById('reset-btn');

        if (recalculateBtn && resetBtn) {
            // Mark as initialized for testing purposes
            recalculateBtn.setAttribute('data-initialized', 'true');
            resetBtn.setAttribute('data-initialized', 'true');
            
            const spinner = recalculateBtn.querySelector('.spinner-border');

            // Recalculate button click handler
            recalculateBtn.addEventListener('click', function() {
                const algorithms = Array.prototype.slice.call(document.querySelectorAll('input[type="checkbox"][value]:checked'))
                    .map(function(el) { return el.value; });
                const directionInput = document.querySelector('input[name="direction"]:checked');
                const direction = directionInput ? directionInput.value : 'columns';

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
                const iqrCheckbox = document.getElementById('algorithm-iqr');
                const paretoCheckbox = document.getElementById('algorithm-pareto');
                if (iqrCheckbox) iqrCheckbox.checked = true;
                if (paretoCheckbox) paretoCheckbox.checked = true;

                // Reset radio buttons to default (columns checked)
                const columnsRadio = document.getElementById('direction-columns');
                if (columnsRadio) columnsRadio.checked = true;

                // Trigger recalculation with default settings
            recalculateBtn.click();
        });
    }
}

/**
 * Update cell highlights based on statistical analysis results
 * @param {Object} highlights - Object containing highlight information
 */
export function updateCellHighlights(highlights) {
    // Remove all current highlights from all tables
    const highlightElements = document.querySelectorAll('[class*="highlight-"]');
    highlightElements.forEach(el => {
        el.classList.remove('highlight-outlier', 'highlight-pareto', 'highlight-excluded');
    });

    // Process each highlight entry
    Object.entries(highlights).forEach(([key, highlightType]) => {
        const [column, row] = key.split('_');
        if (!column || !row) return;

        // Find and update matching cells in all tables
        document.querySelectorAll('table[data-datatable="true"]').forEach(table => {
            const thead = table.querySelector('thead');
            const tbody = table.querySelector('tbody');
            if (!thead || !tbody) return;

            const headers = Array.from(thead.querySelectorAll('th'));
            const rows = Array.from(tbody.querySelectorAll('tr'));

            // Find matching row
            const matchingRow = rows.find(tr => {
                const categoryCell = tr.querySelector('td:first-child');
                return categoryCell && categoryCell.textContent.trim() === row;
            });

            if (matchingRow) {
                // Find matching column
                headers.slice(1).forEach((header, index) => {
                    if (header.textContent.trim() === column) {
                        const cell = matchingRow.querySelector(`td:nth-child(${index + 2})`);
                        if (cell) {
                            cell.classList.add(`highlight-${highlightType}`);
                        }
                    }
                });
            }
        });
    });
}
