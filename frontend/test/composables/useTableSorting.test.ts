/**
 * Unit tests for the useTableSorting composable
 * @module test/composables/useTableSorting
 */

import { describe, it, expect, vi } from 'vitest';
import { useTableSorting, compareValues } from '../../src/composables/useTableSorting';
import type { Column } from '../../src/types/column';

const columns: Column[] = [
  { key: 'name', title: 'Name' },
  { key: 'amount', title: 'Amount' },
  { key: 'locked', title: 'Locked', sortable: false }
];

const rows = [
  { name: 'banana', amount: 3 },
  { name: 'apple', amount: 1 },
  { name: 'cherry', amount: 2 }
];

describe('useTableSorting', () => {
  it('leaves data unsorted and returns no ARIA value initially', () => {
    const { sortColumn, sortDirection, ariaSortValue, sortData } = useTableSorting(() => columns);
    expect(sortColumn.value).toBeNull();
    expect(sortDirection.value).toBe('asc');
    expect(ariaSortValue.value).toBeUndefined();
    expect(sortData(rows)).toEqual(rows);
  });

  it('sorts ascending and descending on repeated handleSort calls', () => {
    const { handleSort, sortData, ariaSortValue } = useTableSorting(() => columns);

    handleSort('name');
    expect(sortData(rows).map(row => row.name)).toEqual(['apple', 'banana', 'cherry']);
    expect(ariaSortValue.value).toBe('ascending');

    handleSort('name');
    expect(sortData(rows).map(row => row.name)).toEqual(['cherry', 'banana', 'apple']);
    expect(ariaSortValue.value).toBe('descending');
  });

  it('ignores clicks on non-sortable columns', () => {
    const { handleSort, sortColumn } = useTableSorting(() => columns);
    handleSort('locked');
    expect(sortColumn.value).toBeNull();
  });

  it('sorts numbers numerically', () => {
    const { handleSort, sortData } = useTableSorting(() => columns);
    handleSort('amount');
    expect(sortData(rows).map(row => row.amount)).toEqual([1, 2, 3]);
  });

  it('calls onSortChange when the sort state changes', () => {
    const onSortChange = vi.fn();
    const { handleSort, sortBy } = useTableSorting(() => columns, { onSortChange });

    handleSort('name');
    sortBy('amount', 'desc');
    expect(onSortChange).toHaveBeenCalledTimes(2);
  });

  it('sortBy sets the state directly', () => {
    const { sortBy, sortColumn, sortDirection, sortData } = useTableSorting(() => columns);
    sortBy('amount', 'desc');
    expect(sortColumn.value).toBe('amount');
    expect(sortDirection.value).toBe('desc');
    expect(sortData(rows).map(row => row.amount)).toEqual([3, 2, 1]);
  });

  it('does not mutate the input array', () => {
    const { handleSort, sortData } = useTableSorting(() => columns);
    handleSort('name');
    const sorted = sortData(rows);
    expect(rows[0].name).toBe('banana');
    expect(sorted).not.toBe(rows);
  });
});

describe('compareValues', () => {
  it('orders null before values and compares numbers and strings', () => {
    expect(compareValues(null, 1)).toBe(-1);
    expect(compareValues(1, null)).toBe(1);
    expect(compareValues(null, null)).toBe(0);
    expect(compareValues(2, 10)).toBeLessThan(0);
    expect(compareValues('a', 'b')).toBeLessThan(0);
  });

  it('compares dates by time', () => {
    expect(compareValues(new Date(2026, 0, 2), new Date(2026, 0, 1))).toBeGreaterThan(0);
    expect(compareValues(new Date(2026, 0, 1), 'text')).toBe(-1);
  });
});
