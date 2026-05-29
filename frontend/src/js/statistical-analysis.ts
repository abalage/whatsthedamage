/**
 * Statistical Analysis JavaScript functionality
 * Handles statistical analysis controls, AJAX calls, and result visualization
 */

import { showNotification } from './utils';
import { postData, getApiUrl } from './api';
import { AppError, StatisticalAnalysisRequest, StatisticalAnalysisResponse } from '../types';
import { getCssClassesForHighlights } from '../config/highlight-config';

/**
 * Initialize statistical analysis controls
 */
export function initStatisticalAnalysis(): void {
    // Apply initial highlights if available
    const rawHighlights = (globalThis as Record<string, unknown>).highlights;
    if (rawHighlights) {
        // Parse the JSON string into an object if it's a string
        const parsedHighlights = typeof rawHighlights === 'string' ? JSON.parse(rawHighlights) : rawHighlights;
        updateCellHighlights(parsedHighlights as Record<string, string[]>);
    }

    const recalculateBtn = document.getElementById('recalculate-btn');
    const resetBtn = document.getElementById('reset-btn');

    // Only initialize if controls exist and haven't been initialized yet
    if (recalculateBtn && resetBtn && !recalculateBtn.dataset.initialized) {
        // Mark as initialized to prevent duplicate event listeners
        recalculateBtn.dataset.initialized = 'true';
        resetBtn.dataset.initialized = 'true';

        const spinner = recalculateBtn.querySelector('.spinner-border');

        // Recalculate button click handler
        recalculateBtn.addEventListener('click', () => {
            const algorithms = Array.prototype.slice.call(document.querySelectorAll('input[type="checkbox"][value]:checked'))
                .map((el: HTMLInputElement) => { return el.value; });
            const directionInput = document.querySelector('input[name="direction"]:checked') as HTMLInputElement | null;
            const direction = directionInput?.value === 'rows' ? 'rows' : 'columns';

            const request: StatisticalAnalysisRequest = {
                result_id: (globalThis as Record<string, unknown>).resultId as string,
                algorithms: algorithms,
                direction: direction
            };

            // Show loading spinner
            if (spinner) spinner.classList.remove('d-none');
            const lastSpan = recalculateBtn.querySelector('span:last-child');
            if (lastSpan) lastSpan.textContent = 'Processing...';
            (recalculateBtn as HTMLButtonElement).disabled = true;
            (resetBtn as HTMLButtonElement).disabled = true;

            postData<StatisticalAnalysisResponse>(getApiUrl('/recalculate-statistics'), request)
                .then((data) => {
                    if (data.status === 'success') {
                        // Update all cell highlights
                        updateCellHighlights(data.highlights);
                        showNotification('Statistics recalculated successfully!', 'success');
                    } else {
                        throw new AppError(data.error ?? 'Unknown error');
                    }
                })
                .catch((error: unknown) => {
                    let appError: AppError;
                    if (error instanceof AppError) {
                        appError = error;
                    } else if (error instanceof Error) {
                        appError = new AppError(error.message);
                    } else {
                        appError = new AppError(String(error));
                    }
                    showNotification('Error recalculating statistics: ' + appError.message, 'danger');
                })
                .finally(() => {
                    // Hide loading spinner
                    if (spinner) spinner.classList.add('d-none');
                    const lastSpan = recalculateBtn.querySelector('span:last-child');
                    if (lastSpan) lastSpan.textContent = 'Recalculate';
                    (recalculateBtn as HTMLButtonElement).disabled = false;
                    (resetBtn as HTMLButtonElement).disabled = false;
                });
        });

        // Reset button click handler
        resetBtn.addEventListener('click', () => {
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
                result_id: (globalThis as Record<string, unknown>).resultId as string,
                algorithms: ['iqr', 'pareto'],
                direction: 'columns',
                use_default_directions: true
            };

            postData<StatisticalAnalysisResponse>(getApiUrl('/recalculate-statistics'), resetRequest)
                .then((data) => {
                    if (data.status === 'success') {
                        // Update all cell highlights
                        updateCellHighlights(data.highlights);
                        showNotification('Defaults restored successfully!', 'success');
                    } else {
                        throw new AppError(data.error ?? 'Unknown error');
                    }
                })
                .catch((error: unknown) => {
                    let appError: AppError;
                    if (error instanceof AppError) {
                        appError = error;
                    } else {
                        const message = error instanceof Error ? error.message : String(error);
                        appError = new AppError(message);
                    }
                    showNotification('Error restoring defaults: ' + appError.message, 'danger');
                })
            .finally(() => {
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
 * Apply highlight classes to a cell based on highlight types
 * @param cell - DOM element to highlight
 * @param types - Array of highlight types
 */
function applyHighlightClasses(cell: HTMLElement, types: string[]): void {
    // Get CSS classes using the configuration
    const cssClasses = getCssClassesForHighlights(types);

    // Apply each CSS class to the cell
    cssClasses.forEach(cssClass => {
        cell.classList.add(cssClass);
    });
}

/**
 * Update cell highlights based on statistical analysis results
 * @param highlights - Object containing highlight information with row_id as key
 *                     Each value is an array of highlight types (e.g., ['outlier', 'pareto'])
 */
export function updateCellHighlights(highlights: Record<string, string[]>): void {
    // Remove all current highlights from all tables
    // Exclude legend badges by checking if element is inside a legend-display container
    const highlightElements = document.querySelectorAll('[class*="highlight-"]');
    highlightElements.forEach(el => {
        // Skip legend badges - they should keep their highlight classes
        if (el.closest('.legend-display')) {
            return;
        }
        // Remove all highlight classes from table cells
        Array.from(el.classList).forEach(cls => {
            if (cls.startsWith('highlight-')) {
                el.classList.remove(cls);
            }
        });
    });

    // Process each highlight entry using UUID-based addressing
    Object.entries(highlights).forEach(([rowId, highlightTypes]) => {
        // Find all cells with matching data-row-id attribute
        const cells = document.querySelectorAll(`[data-row-id="${rowId}"]`);
        cells.forEach(cell => {
            // highlightTypes is already an array from the template
            applyHighlightClasses(cell as HTMLElement, highlightTypes);
        });
    });
}
