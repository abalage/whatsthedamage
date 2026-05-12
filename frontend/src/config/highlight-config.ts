/**
 * Highlight Configuration
 *
 * This configuration file defines the mapping between semantic highlight types
 * (returned from backend statistical analysis) and their corresponding CSS classes.
 * This allows the presentation layer to control styling independently of the
 * business logic in the service layer.
 */

export interface HighlightConfig {
    /**
     * Mapping of semantic highlight types to CSS class names
     */
    highlightTypes: Record<string, string>;

    /**
     * CSS class to apply when multiple highlights are present
     */
    multipleHighlightClass: string;
}

/**
 * Default highlight configuration
 */
export const DEFAULT_HIGHLIGHT_CONFIG: HighlightConfig = {
    highlightTypes: {
        outlier: 'highlight-outlier',
        iqr: 'highlight-outlier',
        pareto: 'highlight-pareto',
        excluded: 'highlight-excluded',
    },
    multipleHighlightClass: 'highlight-multiple',
};

/**
 * Get CSS class for a semantic highlight type
 * @param highlightType - Semantic highlight type (e.g., 'outlier', 'pareto')
 * @param config - Highlight configuration (defaults to DEFAULT_HIGHLIGHT_CONFIG)
 * @returns CSS class name or empty string if not found
 */
export function getCssClassForHighlight(
    highlightType: string,
    config: HighlightConfig = DEFAULT_HIGHLIGHT_CONFIG
): string {
    const cssClass = config.highlightTypes[highlightType];
    if (!cssClass) {
        // Log warning for unknown highlight types to help debugging
        console.warn(`Unknown highlight type: "${highlightType}". This may prevent highlight-multiple from being applied correctly.`);
    }
    return cssClass ?? '';
}

/**
 * Get CSS classes for an array of highlight types
 * @param highlightTypes - Array of semantic highlight types
 * @param config - Highlight configuration (defaults to DEFAULT_HIGHLIGHT_CONFIG)
 * @returns Array of CSS class names
 */
export function getCssClassesForHighlights(
    highlightTypes: string[],
    config: HighlightConfig = DEFAULT_HIGHLIGHT_CONFIG
): string[] {
    const cssClasses: string[] = [];

    // If 'excluded' is present, it takes precedence - only apply highlight-excluded
    if (highlightTypes.includes('excluded')) {
        const excludedClass = getCssClassForHighlight('excluded', config);
        if (excludedClass) {
            cssClasses.push(excludedClass);
        }
        return cssClasses;
    }

    // Filter out 'excluded' (already handled above)
    const algoHighlights = highlightTypes.filter(t => t !== 'excluded');

    // Convert algorithm highlights to CSS classes
    const validAlgoHighlights: string[] = [];
    algoHighlights.forEach(hType => {
        const cssClass = getCssClassForHighlight(hType, config);
        if (cssClass) {
            validAlgoHighlights.push(hType);
        }
    });

    // Add multiple highlight class if multiple valid algorithm highlights
    // When multiple algorithms mark the same cell, only apply highlight-multiple
    const MIN_HIGHLIGHTS_FOR_MULTIPLE = 1
    if (validAlgoHighlights.length > MIN_HIGHLIGHTS_FOR_MULTIPLE) {
        cssClasses.push(config.multipleHighlightClass);
    } else {
        // For single algorithm, add its individual class
        algoHighlights.forEach(hType => {
            const cssClass = getCssClassForHighlight(hType, config);
            if (cssClass) {
                cssClasses.push(cssClass);
            }
        });
    }

    return cssClasses;
}
