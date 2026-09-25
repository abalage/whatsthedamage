/**
 * Unit tests for Categories page optional resultId handling
 * @module test/pages/Categories
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { shallowMount, flushPromises, type VueWrapper } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { reactive } from 'vue';
import Categories from '../../src/pages/Categories.vue';
import { fetchProcessingResultMetadata, fetchAllTransactions } from '../../src/js/api.js';
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
  beforeEach(() => {
    vi.clearAllMocks();
    mockRoute.params = {};
    mockRoute.query = {};
    setActivePinia(createPinia());
  });

  const mountPage = (): VueWrapper => shallowMount(Categories, { global: { plugins: [createPinia()] } });

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
});
