/**
 * Statistical Analysis JavaScript functionality
 * Handles statistical analysis controls, AJAX calls, and result visualization
 */

import { showNotification } from './utils';
import { postData } from './api';
import { AppError, StatisticalAnalysisRequest, StatisticalAnalysisResponse } from '../types';

/**
 * Initialize statistical analysis controls
 */
export function initStatisticalAnalysis(): void {
    const recalculateBtn = document.getElementById('recalculate-btn');
    const resetBtn = document.getElementById('reset-btn');

    // Only initialize if controls exist and haven't been initialized yet
    if (recalculateBtn && resetBtn && !recalculateBtn.dataset.initialized) {
        // Mark as initialized to prevent duplicate event listeners
        recalculateBtn.dataset.initialized = 'true';
        resetBtn.dataset.initialized = 'true';

        const spinner = recalculateBtn.querySelector('.spinner-border');

        // Recalculate button click handler
        recalculateBtn.addEventListener('click', function() {
            const algorithms = Array.prototype.slice.call(document.querySelectorAll('input[type="checkbox"][value]:checked'))
                .map(function(el: HTMLInputElement) { return el.value; });
            const directionInput = document.querySelector('input[name="direction"]:checked') as HTMLInputElement | null;
            const direction = (directionInput?.value ?? 'columns') as 'columns' | 'rows';

            const request: StatisticalAnalysisRequest = {
                result_id: (globalThis as any).resultId,
                algorithms: algorithms,
                direction: direction
            };

            // Show loading spinner
            if (spinner) spinner.classList.remove('d-none');
            const lastSpan = recalculateBtn.querySelector('span:last-child');
            if (lastSpan) lastSpan.textContent = 'Processing...';
            (recalculateBtn as HTMLButtonElement).disabled = true;
            (resetBtn as HTMLButtonElement).disabled = true;

            postData<StatisticalAnalysisResponse>('/recalculate-statistics', request)
                .then(function(data) {
                    if (data.status === 'success') {
                        // Update all cell highlights
                        updateCellHighlights(data.highlights);
                        showNotification('Statistics recalculated successfully!', 'success');
                    } else {
                        throw new AppError(data.error || 'Unknown error');
                    }
                })
                .catch(function(error: unknown) {
                    let appError: AppError;
                    if (error instanceof AppError) {
                        appError = error;
                    } else if (error instanceof Error) {
                        appError = new AppError(error.message);
                    } else {
                        appError = new AppError(String(error));
                    }
                    console.error('Error:', appError);
                    showNotification('Error recalculating statistics: ' + appError.message, 'danger');
                })
                .finally(function() {
                    // Hide loading spinner
                    if (spinner) spinner.classList.add('d-none');
                    const lastSpan = recalculateBtn.querySelector('span:last-child');
                    if (lastSpan) lastSpan.textContent = 'Recalculate';
                    (recalculateBtn as HTMLButtonElement).disabled = false;
                    (resetBtn as HTMLButtonElement).disabled = false;
                });
        });

        // Reset button click handler
        resetBtn.addEventListener('click', function() {
            // Reset checkboxes to default (both checked)
            const iqrCheckbox = document.getElementById('algorithm-iqr') as HTMLInputElement | null;
            const paretoCheckbox = document.getElementById('algorithm-pareto') as HTMLInputElement | null;
            if (iqrCheckbox) iqrCheckbox.checked = true;
            if (paretoCheckbox) paretoCheckbox.checked = true;

            // Reset radio buttons to default (columns checked)
            const columnsRadio = document.getElementById('direction-columns') as HTMLInputElement | null;
            if (columnsRadio) columnsRadio.checked = true;

            // Show loading spinner
            if (spinner) spinner.classList.remove('d-none');
            const lastSpan = recalculateBtn.querySelector('span:last-child');
            if (lastSpan) lastSpan.textContent = 'Restoring defaults...';
            (recalculateBtn as HTMLButtonElement).disabled = true;
            (resetBtn as HTMLButtonElement).disabled = true;

            // Trigger recalculation with default settings using default directions
            const resetRequest: StatisticalAnalysisRequest = {
                result_id: (globalThis as any).resultId,
                algorithms: ['iqr', 'pareto'],
                direction: 'columns',
                use_default_directions: true
            };

            postData<StatisticalAnalysisResponse>('/recalculate-statistics', resetRequest)
                .then(function(data) {
                    if (data.status === 'success') {
                        // Update all cell highlights
                        updateCellHighlights(data.highlights);
                        showNotification('Defaults restored successfully!', 'success');
                    } else {
                        throw new AppError(data.error || 'Unknown error');
                    }
                })
                .catch(function(error: unknown) {
                    let appError: AppError;
                    if (error instanceof AppError) {
                        appError = error;
                    } else {
                        const message = error instanceof Error ? error.message : String(error);
                        appError = new AppError(message);
                    }
                    console.error('Error:', appError);
                    showNotification('Error restoring defaults: ' + appError.message, 'danger');
                })
            .finally(function() {
                // Hide loading spinner
                if (spinner) spinner.classList.add('d-none');
                const lastSpan = recalculateBtn.querySelector('span:last-child');
                if (lastSpan) lastSpan.textContent = 'Recalculate';
                (recalculateBtn as HTMLButtonElement).disabled = false;
                (resetBtn as HTMLButtonElement).disabled = false;
            });
        });
    }
}

/**
 * Update cell highlights based on statistical analysis results
 * @param {Object} highlights - Object containing highlight information
 */
export function updateCellHighlights(highlights: Record<string, string>): void {
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
            const tbody = table.querySelector('tbody');
            if (!tbody) return;

            const rows = Array.from(tbody.querySelectorAll('tr'));

            rows.forEach(tr => {
                const cells = Array.from(tr.querySelectorAll('td'));
                if (cells.length === 0) return;

                // For tables with multiple columns (like results.html):
                // - First column is category/label
                // - Other columns are months/dates
                // Match when first cell equals row and any other cell equals column
                if (cells.length > 1) {
                    const firstCell = cells[0];
                    const firstCellText = firstCell?.textContent?.trim() || '';
                    const otherCells = cells.slice(1);

                    if (firstCellText === row) {
                        otherCells.forEach(cell => {
                            const cellText = cell?.textContent?.trim() || '';
                            if (cellText === column) {
                                cell.classList.add(`highlight-${highlightType}`);
                            }
                        });
                    }
                }
                // For tables with 2 columns (like drilldown views):
                // - First column is label
                // - Second column is value
                // Match when second cell equals row
                else if (cells.length === 2) {
                    const valueCell = cells[1];
                    if (valueCell) {
                        const valueCellText = valueCell.textContent?.trim() || '';
                        if (valueCellText === row) {
                            valueCell.classList.add(`highlight-${highlightType}`);
                        }
                    }
                }
            });
        });
    });
}
