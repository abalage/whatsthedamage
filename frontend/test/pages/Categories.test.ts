/**
 * Unit tests for Categories page optional resultId handling
 * @module test/pages/Categories
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { shallowMount, flushPromises, type VueWrapper } from '@vue/test-utils';
import { createPinia, setActivePinia, type Pinia } from 'pinia';
import { reactive } from 'vue';
import Categories from '../../src/pages/Categories.vue';
import { fetchProcessingResultMetadata, fetchAllTransactions, recalculateStatistics } from '../../src/js/api.js';
import { useStatisticalStore } from '../../src/stores/statistical.js';
import type { ProcessingResultMetadata, TransactionListItem } from '../../src/types/api.js';

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
  recalculateStatistics: vi.fn(),
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
  transaction_start_date: '2026-01-01',
  transaction_end_date: '2026-01-31',
  created_at: '2026-01-01T00:00:00',
  transactions_url: '/api/v2/transactions?result_id=r1',
};

const makeTransaction = (id: number): TransactionListItem => ({
  id,
  user_id: 1,
  result_id: 'r1',
  date: '2026-01-15',
  transaction_type: 'debit',
  original_partner: 'Store',
  amount: -10.5,
  currency: 'EUR',
  account: 'acc1',
  deduplication_hash: `hash-${id}`,
  category_id: 'food',
  partner: null,
  notice: null,
  confidence: null,
  created_at: null,
  updated_at: null,
});

describe('Categories.vue', () => {
  let pinia: Pinia;

  beforeEach(() => {
    vi.clearAllMocks();
    mockRoute.params = {};
    mockRoute.query = {};
    pinia = createPinia();
    setActivePinia(pinia);
  });

  const mountPage = (): VueWrapper => shallowMount(Categories, { global: { plugins: [pinia] } });

  it('renders without error when resultId is undefined', async () => {
    vi.mocked(fetchProcessingResultMetadata).mockResolvedValue(null);
    vi.mocked(fetchAllTransactions).mockResolvedValue({
      transactions: [makeTransaction(1)],
      total_count: 1,
      limit: 10000,
      offset: 0,
    });

    const wrapper = await mountPage();
    await flushPromises();

    expect(wrapper.text()).toContain('Categories');
  });

  it('fetches all transactions without result_id when resultId is undefined', async () => {
    vi.mocked(fetchProcessingResultMetadata).mockResolvedValue(null);
    vi.mocked(fetchAllTransactions).mockResolvedValue({
      transactions: [makeTransaction(1)],
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
      transactions: [makeTransaction(1), makeTransaction(2)],
      total_count: 2,
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
      transactions: [makeTransaction(1)],
      total_count: 1,
      limit: 10000,
      offset: 0,
    });

    const wrapper = await mountPage();
    await flushPromises();

    expect(wrapper.text()).toContain('(All Transactions)');
  });

  it('groups transactions with an empty account under the unknown account', async () => {
    vi.mocked(fetchProcessingResultMetadata).mockResolvedValue(null);
    const withoutAccount = { ...makeTransaction(2), account: '' };
    vi.mocked(fetchAllTransactions).mockResolvedValue({
      transactions: [makeTransaction(1), withoutAccount],
      total_count: 2,
      limit: 10000,
      offset: 0,
    });

    const wrapper = await mountPage();
    await flushPromises();

    // The fallback keeps the route param non-empty so vue-router can
    // resolve the drilldown links of the account tables
    expect(wrapper.text()).toContain('Account: acc1');
    expect(wrapper.text()).toContain('Account: unknown');
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
      transactions: [makeTransaction(1)],
      total_count: 500,
      limit: 10000,
      offset: 0,
    });

    const wrapper = await mountPage();
    await flushPromises();

    expect(wrapper.text()).toContain('Too many transactions to display');
    expect(wrapper.text()).toContain('1 / 500');
  });

  it('renders popover amounts without currency next to the numbers', async () => {
    vi.mocked(fetchProcessingResultMetadata).mockResolvedValue(null);
    vi.mocked(fetchAllTransactions).mockResolvedValue({
      transactions: [makeTransaction(1)],
      total_count: 1,
      limit: 10000,
      offset: 0,
    });

    const wrapper = await mountPage();
    await flushPromises();

    const vm = wrapper.vm as unknown as {
      buildTableColumns: (account: { id: string }) => Array<{
        key: string;
        componentProps: (value: unknown, row?: Record<string, unknown>) => Record<string, unknown>;
      }>;
      buildTableData: (account: { id: string }) => Record<string, unknown>[];
    };
    const account = { id: 'acc1' };
    const columns = vm.buildTableColumns(account);
    const rows = vm.buildTableData(account);

    const monthColumn = columns.find(column => column.key === 'month-2026-01');
    if (!monthColumn) {
      throw new Error('Expected the month column to be defined');
    }

    const props = monthColumn.componentProps(rows[0]['month-2026-01'], rows[0]);
    expect(props.popoverContent).toContain('-10.50');
    expect(props.popoverContent).not.toContain('EUR');
  });

  it('recalculates statistics and stores highlights after loading transactions', async () => {
    vi.mocked(fetchProcessingResultMetadata).mockResolvedValue(null);
    vi.mocked(fetchAllTransactions).mockResolvedValue({
      transactions: [makeTransaction(1)],
      total_count: 1,
      limit: 10000,
      offset: 0,
    });
    vi.mocked(recalculateStatistics).mockResolvedValue({
      status: 'success',
      result_id: null,
      highlights: { 'acc1|2026-01|food': ['pareto'] },
      algorithms: ['iqr', 'pareto'],
      direction: 'columns',
    });

    await mountPage();
    await flushPromises();

    expect(recalculateStatistics).toHaveBeenCalledWith(
      undefined,
      ['iqr', 'pareto'],
      'columns'
    );
    const store = useStatisticalStore();
    expect(store.highlights).toEqual({ 'acc1|2026-01|food': ['pareto'] });
  });

  it('skips highlight loading when there are no transactions', async () => {
    vi.mocked(fetchProcessingResultMetadata).mockResolvedValue(null);
    vi.mocked(fetchAllTransactions).mockResolvedValue({
      transactions: [],
      total_count: 0,
      limit: 10000,
      offset: 0,
    });

    await mountPage();
    await flushPromises();

    expect(recalculateStatistics).not.toHaveBeenCalled();
  });

  it('builds cell IDs for each month column of a row', async () => {
    vi.mocked(fetchProcessingResultMetadata).mockResolvedValue(null);
    vi.mocked(fetchAllTransactions).mockResolvedValue({
      transactions: [makeTransaction(1)],
      total_count: 1,
      limit: 10000,
      offset: 0,
    });

    const wrapper = await mountPage();
    await flushPromises();

    const vm = wrapper.vm as unknown as {
      buildTableData: (account: { id: string }) => Record<string, unknown>[];
    };
    const rows = vm.buildTableData({ id: 'acc1' });
    const rowIds = rows[0]._rowIds as Record<string, string>;
    expect(rowIds['month-2026-01']).toBe('acc1|2026-01|food');
  });
});
