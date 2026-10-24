/**
 * Unit tests for the useTableFiltering composable
 * @module test/composables/useTableFiltering
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useTableFiltering } from '../../src/composables/useTableFiltering';
import type { Column } from '../../src/types/column';

const columns: Column[] = [
  { key: 'name', title: 'Name' },
  {
    key: 'type',
    title: 'Type',
    filterOptions: [
      { value: 'debit', label: 'Debit' },
      { value: 'credit', label: 'Credit' }
    ]
  },
  { key: 'secret', title: 'Secret', searchable: false }
];

const rows = [
  { name: 'Coffee Shop', type: 'debit', secret: 'hidden-a' },
  { name: 'Salary', type: 'credit', secret: 'hidden-b' }
];

describe('useTableFiltering', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('returns the data unchanged without filters', () => {
    const { filterData } = useTableFiltering(() => columns);
    expect(filterData(rows)).toEqual(rows);
  });

  it('filters by case-insensitive substring on text columns', () => {
    const { setColumnFilter, filterData } = useTableFiltering(() => columns);
    setColumnFilter('name', 'coffee');
    expect(filterData(rows).map(row => row.name)).toEqual(['Coffee Shop']);
  });

  it('matches fixed-choice filters exactly', () => {
    const { setColumnFilter, filterData } = useTableFiltering(() => columns);
    setColumnFilter('type', 'debit');
    expect(filterData(rows).map(row => row.name)).toEqual(['Coffee Shop']);
  });

  it('applies the global search across searchable columns only', () => {
    const { search, filterData } = useTableFiltering(() => columns);
    search('hidden-a');
    expect(filterData(rows)).toEqual([]);
    search('salary');
    expect(filterData(rows).map(row => row.name)).toEqual(['Salary']);
  });

  it('debounces handleSearch and reports changes', () => {
    const onFiltersChanged = vi.fn();
    const { handleSearch, searchQuery, filterData } = useTableFiltering(() => columns, { onFiltersChanged });

    handleSearch('coffee');
    expect(searchQuery.value).toBe('');
    vi.advanceTimersByTime(299);
    expect(searchQuery.value).toBe('');
    vi.advanceTimersByTime(1);
    expect(searchQuery.value).toBe('coffee');
    expect(onFiltersChanged).toHaveBeenCalledTimes(1);
    expect(filterData(rows).map(row => row.name)).toEqual(['Coffee Shop']);
  });

  it('only the latest debounced search applies', () => {
    const { handleSearch, searchQuery } = useTableFiltering(() => columns);
    handleSearch('coffee');
    handleSearch('salary');
    vi.advanceTimersByTime(300);
    expect(searchQuery.value).toBe('salary');
  });

  it('clears a single filter and all filters', () => {
    const { setColumnFilter, clearColumnFilter, columnFilters, clearColumnFilters } = useTableFiltering(() => columns);
    setColumnFilter('name', 'coffee');
    setColumnFilter('type', 'debit');
    clearColumnFilter('name');
    expect(columnFilters.value).toEqual({ type: 'debit' });
    clearColumnFilters();
    expect(columnFilters.value).toEqual({});
  });

  it('clearSearch and setColumnFilter report changes', () => {
    const onFiltersChanged = vi.fn();
    const { search, clearSearch, setColumnFilter } = useTableFiltering(() => columns, { onFiltersChanged });

    search('coffee');
    setColumnFilter('type', 'debit');
    clearSearch();
    expect(onFiltersChanged).toHaveBeenCalledTimes(3);
  });
});
