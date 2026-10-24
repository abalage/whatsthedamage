/**
 * Unit tests for the useTableHighlight composable
 * @module test/composables/useTableHighlight
 */

import { describe, it, expect } from 'vitest';
import { useTableHighlight } from '../../src/composables/useTableHighlight';

const row = {
  name: 'Groceries',
  total: 42,
  _rowIds: { total: 'row-1', name: 'row-2' }
};

describe('useTableHighlight', () => {
  it('returns no classes without a highlight map', () => {
    const { getCellHighlightClasses } = useTableHighlight(() => undefined);
    expect(getCellHighlightClasses(row, 'total')).toEqual([]);
  });

  it('returns no classes for rows without a _rowIds mapping', () => {
    const { getCellHighlightClasses } = useTableHighlight(() => ({ 'row-1': ['outlier'] }));
    expect(getCellHighlightClasses({ name: 'x' }, 'total')).toEqual([]);
  });

  it('resolves the CSS class of the cell row id', () => {
    const { getCellHighlightClasses } = useTableHighlight(() => ({ 'row-1': ['outlier'] }));
    expect(getCellHighlightClasses(row, 'total')).toEqual(['highlight-outlier']);
    expect(getCellHighlightClasses(row, 'name')).toEqual([]);
  });

  it('resolves multiple highlight types to the shared class', () => {
    const { getCellHighlightClasses } = useTableHighlight(() => ({
      'row-1': ['iqr', 'pareto']
    }));
    expect(getCellHighlightClasses(row, 'total')).toEqual(['highlight-multiple']);
  });
});
