/**
 * Tests for highlight configuration
 */
import { describe, it, expect } from 'vitest';
import {
    DEFAULT_HIGHLIGHT_CONFIG,
    getCssClassForHighlight,
    getCssClassesForHighlights,
    HighlightConfig
} from '../src/config/highlight-config';

describe('Highlight Configuration', () => {
    it('should export default configuration', () => {
        expect(DEFAULT_HIGHLIGHT_CONFIG).toBeDefined();
        expect(DEFAULT_HIGHLIGHT_CONFIG.highlightTypes).toBeDefined();
        expect(DEFAULT_HIGHLIGHT_CONFIG.multipleHighlightClass).toBe('highlight-multiple');
    });

    it('should have default mappings for known highlight types', () => {
        expect(DEFAULT_HIGHLIGHT_CONFIG.highlightTypes['outlier']).toBe('highlight-outlier');
        expect(DEFAULT_HIGHLIGHT_CONFIG.highlightTypes['pareto']).toBe('highlight-pareto');
        expect(DEFAULT_HIGHLIGHT_CONFIG.highlightTypes['excluded']).toBe('highlight-excluded');
    });

    it('should return empty string for unknown highlight type', () => {
        const result = getCssClassForHighlight('unknown-type');
        expect(result).toBe('');
    });

    it('should return correct CSS class for known highlight type', () => {
        expect(getCssClassForHighlight('outlier')).toBe('highlight-outlier');
        expect(getCssClassForHighlight('pareto')).toBe('highlight-pareto');
        expect(getCssClassForHighlight('excluded')).toBe('highlight-excluded');
    });

    it('should use custom configuration when provided', () => {
        const customConfig: HighlightConfig = {
            highlightTypes: {
                outlier: 'custom-outlier',
                pareto: 'custom-pareto',
            },
            multipleHighlightClass: 'custom-multiple',
        };

        expect(getCssClassForHighlight('outlier', customConfig)).toBe('custom-outlier');
        expect(getCssClassForHighlight('pareto', customConfig)).toBe('custom-pareto');
    });

    it('should return single CSS class for single highlight', () => {
        const result = getCssClassesForHighlights(['outlier']);
        expect(result).toEqual(['highlight-outlier']);
    });

    it('should return multiple CSS classes for multiple highlights', () => {
        const result = getCssClassesForHighlights(['outlier', 'pareto']);
        expect(result).toEqual(['highlight-outlier', 'highlight-pareto', 'highlight-multiple']);
    });

    it('should handle excluded highlight separately', () => {
        const result = getCssClassesForHighlights(['outlier', 'excluded']);
        expect(result).toEqual(['highlight-outlier', 'highlight-excluded']);
    });

    it('should handle multiple highlights with excluded', () => {
        const result = getCssClassesForHighlights(['outlier', 'pareto', 'excluded']);
        expect(result).toEqual(['highlight-outlier', 'highlight-pareto', 'highlight-multiple', 'highlight-excluded']);
    });

    it('should return empty array for empty input', () => {
        const result = getCssClassesForHighlights([]);
        expect(result).toEqual([]);
    });

    it('should filter out unknown highlights', () => {
        const result = getCssClassesForHighlights(['unknown1', 'unknown2']);
        expect(result).toEqual([]);
    });

    it('should handle mixed known and unknown highlights', () => {
        const result = getCssClassesForHighlights(['outlier', 'unknown', 'pareto']);
        expect(result).toEqual(['highlight-outlier', 'highlight-pareto', 'highlight-multiple']);
    });
});