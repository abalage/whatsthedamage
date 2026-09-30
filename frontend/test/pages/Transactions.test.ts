/**
 * Unit tests for Transactions page optional resultId handling
 * @module test/pages/Transactions
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { shallowMount, flushPromises, type VueWrapper } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { reactive } from 'vue';
import Transactions from '../../src/pages/Transactions.vue';
import VueDataTable from '../../src/components/data/VueDataTable.vue';
import EditableCategoryCell from '../../src/components/data/EditableCategoryCell.vue';
import EditableTextCell from '../../src/components/data/EditableTextCell.vue';
import { fetchProcessingResultMetadata, fetchAllTransactions, updateTransaction, fetchCategories } from '../../src/js/api.js';
import { useFeedbackStore } from '../../src/stores/feedback.js';
import type { ProcessingResultMetadata, TransactionListItem, CategoryDefinition } from '../../src/types/api.js';

interface ColumnLike {
  key: string;
  component?: unknown;
  componentProps?: (value: unknown, row?: Record<string, unknown>, index?: number) => Record<string, unknown>;
  filterOptions?: Array<{ value: string; label: string }>;
}

const tableProps = (wrapper: VueWrapper): Record<string, unknown> =>
  wrapper.findComponent(VueDataTable).props() as Record<string, unknown>;

const tableColumns = (wrapper: VueWrapper): ColumnLike[] =>
  tableProps(wrapper).columns as ColumnLike[];

const tableData = (wrapper: VueWrapper): Array<Record<string, unknown>> =>
  tableProps(wrapper).data as Array<Record<string, unknown>>;

const mockRoute = reactive<{ params: Record<string, unknown>; query: Record<string, unknown> }>({
  params: {},
  query: {},
});

vi.mock('vue-router', (): Record<string, unknown> => ({
  useRoute: () => mockRoute,
  RouterLink: { props: ['to'], template: '<a><slot /></a>' },
}));

vi.mock('vue3-gettext', (): Record<string, unknown> => ({
  useGettext: (): { $gettext: (key: string) => string } => ({
    $gettext: (key: string): string => key,
  }),
}));

vi.mock('../../src/js/api.js', () => ({
  fetchProcessingResultMetadata: vi.fn(),
  fetchAllTransactions: vi.fn(),
  updateTransaction: vi.fn(),
  fetchCategories: vi.fn(),
}));

const metadata: ProcessingResultMetadata = {
  result_id: 'r1',
  user_id: 1,
  csv_profile_id: null,
  row_count: 2,
  processing_time: 1,
  ml_enabled: false,
  start_date: '2026-01-01',
  end_date: '2026-01-31',
  created_at: '2026-01-01T00:00:00',
  transactions_url: '/api/v2/transactions?result_id=r1',
};

const transaction: TransactionListItem = {
  id: 1,
  user_id: 1,
  result_id: 'r1',
  date: '2026-01-15',
  transaction_type: 'debit',
  original_partner: 'Store',
  amount: -10.5,
  currency: 'EUR',
  account: 'acc1',
  deduplication_hash: 'hash',
  category_id: 'food',
  partner: null,
  notice: null,
  confidence: null,
  created_at: null,
  updated_at: null,
};

describe('Transactions.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockRoute.params = {};
    mockRoute.query = {};
    setActivePinia(createPinia());
    vi.mocked(fetchCategories).mockResolvedValue([]);
  });

  const mountPage = (): VueWrapper => shallowMount(Transactions, { global: { plugins: [createPinia()] } });

  it('renders without error when resultId is undefined', async () => {
    vi.mocked(fetchProcessingResultMetadata).mockResolvedValue(null);
    vi.mocked(fetchAllTransactions).mockResolvedValue({
      transactions: [transaction],
      total_count: 1,
      limit: 10000,
      offset: 0,
    });

    const wrapper = await mountPage();
    await flushPromises();

    expect(wrapper.text()).toContain('Transactions');
  });

  it('fetches all transactions without result_id when resultId is undefined', async () => {
    vi.mocked(fetchProcessingResultMetadata).mockResolvedValue(null);
    vi.mocked(fetchAllTransactions).mockResolvedValue({
      transactions: [transaction],
      total_count: 1,
      limit: 10000,
      offset: 0,
    });

    await mountPage();
    await flushPromises();

    expect(fetchAllTransactions).toHaveBeenCalledWith(undefined);
    expect(fetchProcessingResultMetadata).not.toHaveBeenCalled();
  });

  it('fetches filtered transactions and metadata when resultId is defined', async () => {
    mockRoute.query = { resultId: 'r1' };
    vi.mocked(fetchProcessingResultMetadata).mockResolvedValue(metadata);
    vi.mocked(fetchAllTransactions).mockResolvedValue({
      transactions: [transaction],
      total_count: 1,
      limit: 10000,
      offset: 0,
    });

    const wrapper = await mountPage();
    await flushPromises();

    expect(fetchProcessingResultMetadata).toHaveBeenCalledWith('r1');
    expect(fetchAllTransactions).toHaveBeenCalledWith('r1');
    expect(wrapper.text()).not.toContain('All Transactions');
  });

  it('shows the "All Transactions" hint when no resultId is given', async () => {
    vi.mocked(fetchProcessingResultMetadata).mockResolvedValue(null);
    vi.mocked(fetchAllTransactions).mockResolvedValue({
      transactions: [transaction],
      total_count: 1,
      limit: 10000,
      offset: 0,
    });

    const wrapper = await mountPage();
    await flushPromises();

    expect(wrapper.text()).toContain('(All Transactions)');
  });

  it('shows the empty state when no transactions are found', async () => {
    vi.mocked(fetchProcessingResultMetadata).mockResolvedValue(null);
    vi.mocked(fetchAllTransactions).mockResolvedValue({
      transactions: [],
      total_count: 0,
      limit: 10000,
      offset: 0,
    });

    const wrapper = await mountPage();
    await flushPromises();

    expect(wrapper.text()).toContain('No transactions found');
  });

  it('shows a truncation warning when total_count exceeds the fetched rows', async () => {
    vi.mocked(fetchProcessingResultMetadata).mockResolvedValue(null);
    vi.mocked(fetchAllTransactions).mockResolvedValue({
      transactions: [transaction],
      total_count: 500,
      limit: 10000,
      offset: 0,
    });

    const wrapper = await mountPage();
    await flushPromises();

    expect(wrapper.text()).toContain('Too many transactions to display');
    expect(wrapper.text()).toContain('1 / 500');
  });

  it('shows no truncation warning when all rows fit in the limit', async () => {
    vi.mocked(fetchProcessingResultMetadata).mockResolvedValue(null);
    vi.mocked(fetchAllTransactions).mockResolvedValue({
      transactions: [transaction],
      total_count: 1,
      limit: 10000,
      offset: 0,
    });

    const wrapper = await mountPage();
    await flushPromises();

    expect(wrapper.text()).not.toContain('Too many transactions to display');
  });

  it('shows the corrected partner over the original partner', async () => {
    vi.mocked(fetchProcessingResultMetadata).mockResolvedValue(null);
    vi.mocked(fetchAllTransactions).mockResolvedValue({
      transactions: [{ ...transaction, partner: 'Corrected Store' }],
      total_count: 1,
      limit: 10000,
      offset: 0,
    });

    const wrapper = await mountPage();
    await flushPromises();

    const rows = tableData(wrapper);
    expect(rows[0].merchant).toBe('Corrected Store');
  });
});

describe('Transactions.vue inline editing', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockRoute.params = {};
    mockRoute.query = {};
    setActivePinia(createPinia());
    vi.mocked(fetchCategories).mockResolvedValue([]);
  });

  const mountWithTransaction = async (
    txn: TransactionListItem
  ): Promise<VueWrapper> => {
    vi.mocked(fetchProcessingResultMetadata).mockResolvedValue(null);
    vi.mocked(fetchAllTransactions).mockResolvedValue({
      transactions: [txn],
      total_count: 1,
      limit: 10000,
      offset: 0,
    });
    const wrapper = shallowMount(Transactions, { global: { plugins: [createPinia()] } });
    await flushPromises();
    return wrapper;
  };

  const findColumn = (wrapper: VueWrapper, key: string): ColumnLike => {
    const column = tableColumns(wrapper).find(c => c.key === key);
    expect(column).toBeDefined();
    return column as ColumnLike;
  };

  it('renders merchant, category, and notice columns as editable cells', async () => {
    const wrapper = await mountWithTransaction(transaction);

    expect(findColumn(wrapper, 'merchant').component).toBe(EditableTextCell);
    expect(findColumn(wrapper, 'category_id').component).toBe(EditableCategoryCell);
    expect(findColumn(wrapper, 'notice').component).toBe(EditableTextCell);
  });

  it('prevents saving an empty merchant but allows an empty notice', async () => {
    const wrapper = await mountWithTransaction(transaction);
    const rows = tableData(wrapper);

    const merchantProps = findColumn(wrapper, 'merchant').componentProps?.(
      rows[0].merchant, rows[0]
    ) as { allowEmpty?: boolean };
    const noticeProps = findColumn(wrapper, 'notice').componentProps?.(
      rows[0].notice, rows[0]
    ) as { allowEmpty?: boolean };

    expect(merchantProps.allowEmpty).toBe(false);
    expect(noticeProps.allowEmpty).toBe(true);
  });

  it('persists a merchant correction and refreshes the row', async () => {
    const wrapper = await mountWithTransaction(transaction);
    const updated = { ...transaction, partner: 'Renamed Store' };
    vi.mocked(updateTransaction).mockResolvedValue(updated);

    const column = findColumn(wrapper, 'merchant');
    const rows = tableData(wrapper);
    const props = column.componentProps?.(rows[0].merchant, rows[0]) as { save: (v: string) => Promise<void> };
    await props.save('Renamed Store');

    expect(updateTransaction).toHaveBeenCalledWith(1, { partner: 'Renamed Store' });
    const refreshed = tableData(wrapper);
    expect(refreshed[0].merchant).toBe('Renamed Store');
    expect(useFeedbackStore().hasMessages).toBe(true);
  });

  it('persists a category correction', async () => {
    const wrapper = await mountWithTransaction(transaction);
    vi.mocked(updateTransaction).mockResolvedValue({ ...transaction, category_id: 'housing' });

    const column = findColumn(wrapper, 'category_id');
    const rows = tableData(wrapper);
    const props = column.componentProps?.(rows[0].category_id, rows[0]) as { save: (v: string | null) => Promise<void> };
    await props.save('housing');

    expect(updateTransaction).toHaveBeenCalledWith(1, { category_id: 'housing' });
  });

  it('persists a notice correction', async () => {
    const wrapper = await mountWithTransaction(transaction);
    vi.mocked(updateTransaction).mockResolvedValue({ ...transaction, notice: 'gift' });

    const column = findColumn(wrapper, 'notice');
    const rows = tableData(wrapper);
    const props = column.componentProps?.(rows[0].notice, rows[0]) as { save: (v: string) => Promise<void> };
    await props.save('gift');

    expect(updateTransaction).toHaveBeenCalledWith(1, { notice: 'gift' });
  });

  it('rejects failures so the cell can show the error inline', async () => {
    const wrapper = await mountWithTransaction(transaction);
    vi.mocked(updateTransaction).mockRejectedValue(new Error('Update failed'));

    const column = findColumn(wrapper, 'merchant');
    const rows = tableData(wrapper);
    const props = column.componentProps?.(rows[0].merchant, rows[0]) as { save: (v: string) => Promise<void> };

    await expect(props.save('Nope')).rejects.toThrow('Update failed');
    expect(useFeedbackStore().hasErrors).toBe(false);
  });
});

describe('Transactions.vue category filter', () => {
  const categoryDefinitions: CategoryDefinition[] = [
    { id: 'food', default_name: 'Food', patterns: [] },
    { id: 'housing', default_name: 'Housing', patterns: [] },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    mockRoute.params = {};
    mockRoute.query = {};
    setActivePinia(createPinia());
    vi.mocked(fetchCategories).mockResolvedValue(categoryDefinitions);
  });

  const mountWithCategories = async (): Promise<VueWrapper> => {
    vi.mocked(fetchProcessingResultMetadata).mockResolvedValue(null);
    vi.mocked(fetchAllTransactions).mockResolvedValue({
      transactions: [transaction],
      total_count: 1,
      limit: 10000,
      offset: 0,
    });
    const wrapper = shallowMount(Transactions, { global: { plugins: [createPinia()] } });
    await flushPromises();
    return wrapper;
  };

  it('loads categories on mount and offers their ids as filter values', async () => {
    const wrapper = await mountWithCategories();

    expect(fetchCategories).toHaveBeenCalled();
    const column = tableColumns(wrapper).find(c => c.key === 'category_id');
    const options = (column as ColumnLike).filterOptions ?? [];
    expect(options.map(option => option.value)).toEqual(['food', 'housing']);
  });

  it('labels filter options with the category display names', async () => {
    const wrapper = await mountWithCategories();

    const column = tableColumns(wrapper).find(c => c.key === 'category_id');
    const options = (column as ColumnLike).filterOptions ?? [];
    expect(options.find(option => option.value === 'food')?.label).toBe('Food');
    expect(options.find(option => option.value === 'housing')?.label).toBe('Housing');
  });

  it('offers no filter options before categories resolve', async () => {
    vi.mocked(fetchCategories).mockReturnValue(new Promise(() => undefined));
    vi.mocked(fetchProcessingResultMetadata).mockResolvedValue(null);
    vi.mocked(fetchAllTransactions).mockResolvedValue({
      transactions: [transaction],
      total_count: 1,
      limit: 10000,
      offset: 0,
    });

    const wrapper = shallowMount(Transactions, { global: { plugins: [createPinia()] } });
    await flushPromises();

    const column = tableColumns(wrapper).find(c => c.key === 'category_id');
    const options = (column as ColumnLike).filterOptions ?? [];
    expect(options).toEqual([]);
  });
});
