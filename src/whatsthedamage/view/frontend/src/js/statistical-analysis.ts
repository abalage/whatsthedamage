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
 * @param {Object} highlights - Object containing highlight information with row_id as key
 */
export function updateCellHighlights(highlights: Record<string, string>): void {
    // Remove all current highlights from all tables
    const highlightElements = document.querySelectorAll('[class*="highlight-"]');
    highlightElements.forEach(el => {
        el.classList.remove('highlight-outlier', 'highlight-pareto', 'highlight-excluded');
    });

    // Process each highlight entry using UUID-based addressing
    Object.entries(highlights).forEach(([rowId, highlightType]) => {
        // Find all cells with matching data-row-id attribute
        const cells = document.querySelectorAll(`[data-row-id="${rowId}"]`);
        cells.forEach(cell => {
            cell.classList.add(`highlight-${highlightType}`);
        });
    });
}
