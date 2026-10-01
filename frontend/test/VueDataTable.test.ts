/**
 * Unit tests for VueDataTable select-based column filters
 * @module test/VueDataTable
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, type VueWrapper } from '@vue/test-utils';
import VueDataTable from '../src/components/data/VueDataTable.vue';

/** Minimal column shape used to mount the table (see Column in VueDataTable.vue) */
interface FilterColumn {
  key: string;
  title: string;
  filterOptions?: Array<{ value: string; label: string }>;
}

vi.mock('vue3-gettext', (): Record<string, unknown> => ({
  useGettext: (): { $gettext: (key: string) => string } => ({
    $gettext: (key: string): string => key,
  }),
}));

interface Row {
  category: string;
  merchant: string;
}

const rows: Row[] = [
  { category: 'grocery', merchant: 'Store A' },
  { category: 'housing', merchant: 'Store B' },
];

const columns: FilterColumn[] = [
  {
    key: 'category',
    title: 'Category',
    filterOptions: [
      { value: 'grocery', label: 'Grocery' },
      { value: 'housing', label: 'Housing' },
    ],
  },
  { key: 'merchant', title: 'Merchant' },
];

const mountTable = (): VueWrapper =>
  mount(VueDataTable, {
    props: {
      id: 'filter-test-table',
      data: rows,
      columns,
      showColumnFilters: true,
      showSearch: false,
      showExport: false,
      showPagination: false,
    },
  });

/** setColumnFilter is exposed via defineExpose, invisible to wrapper.vm typing */
const setFilter = (wrapper: VueWrapper, key: string, value: string): void => {
  (wrapper.vm as unknown as { setColumnFilter: (key: string, value: string) => void })
    .setColumnFilter(key, value);
};

describe('VueDataTable column filters', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders a select for a column with filterOptions and a text input otherwise', () => {
    const wrapper = mountTable();

    const selects = wrapper.findAll('thead select');
    const inputs = wrapper.findAll('thead input');

    expect(selects).toHaveLength(1);
    expect(inputs).toHaveLength(1);
    expect(inputs[0].attributes('type')).toBe('text');
  });

  it('offers an "All" option plus the translated filter options', () => {
    const wrapper = mountTable();

    const options = wrapper.findAll('thead select option');
    const labels = options.map(option => option.text());

    expect(labels).toEqual(['All', 'Grocery', 'Housing']);
    expect((options[0].element as HTMLOptionElement).value).toBe('');
  });

  it('filters rows by exact match when an option is selected', async () => {
    const wrapper = mountTable();

    await wrapper.find('thead select').setValue('housing');

    expect(wrapper.findAll('tbody tr')).toHaveLength(1);
    expect(wrapper.text()).toContain('Store B');
    expect(wrapper.text()).not.toContain('Store A');
  });

  it('shows all rows again when the "All" option is selected', async () => {
    const wrapper = mountTable();

    await wrapper.find('thead select').setValue('housing');
    await wrapper.find('thead select').setValue('');

    expect(wrapper.findAll('tbody tr')).toHaveLength(2);
  });

  it('does not substring-match on fixed-choice filter values', async () => {
    const wrapper = mountTable();

    setFilter(wrapper, 'category', 'hous');
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('No data available');
  });

  it('keeps case-insensitive substring matching for text filters', async () => {
    const wrapper = mountTable();

    setFilter(wrapper, 'merchant', 'store');
    await wrapper.vm.$nextTick();

    expect(wrapper.findAll('tbody tr')).toHaveLength(2);
  });
});

describe('VueDataTable filter toolbar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows the clear button even when no filter is active', () => {
    const wrapper = mountTable();

    expect(wrapper.text()).toContain('Clear all filters');
  });

  it('clears active filters and emits cleared-filters on click', async () => {
    const wrapper = mountTable();
    setFilter(wrapper, 'category', 'housing');
    await wrapper.vm.$nextTick();
    expect(wrapper.findAll('tbody tr')).toHaveLength(1);

    const clearButton = wrapper
      .findAll('button')
      .find(button => button.text() === 'Clear all filters');
    await clearButton?.trigger('click');
    await wrapper.vm.$nextTick();

    expect(wrapper.findAll('tbody tr')).toHaveLength(2);
    expect(wrapper.emitted('cleared-filters')).toHaveLength(1);
  });

  it('renders page-provided buttons in the filter-actions slot', () => {
    const wrapper = mount(VueDataTable, {
      props: {
        id: 'slot-test-table',
        data: rows,
        columns,
        showColumnFilters: true,
        showSearch: false,
        showExport: false,
        showPagination: false,
      },
      slots: {
        'filter-actions': '<button type="button" class="test-toggle">Toggle</button>',
      },
    });

    const toggle = wrapper.find('button.test-toggle');
    expect(toggle.exists()).toBe(true);
    expect(toggle.text()).toBe('Toggle');
  });
});
