/**
 * Unit tests for CategoryMonthsList page amount display formatting
 * @module test/pages/CategoryMonthsList
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { shallowMount, flushPromises, type VueWrapper } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { reactive } from 'vue';
import CategoryMonthsList from '../../src/pages/CategoryMonthsList.vue';
import { fetchAggregatedTransactions } from '../../src/js/api.js';
import type { AggregatedTransactionsResponse, TransactionListItem } from '../../src/types/api.js';

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
  fetchAggregatedTransactions: vi.fn(),
}));

const makeTransaction = (id: number, amount: number): TransactionListItem => ({
  id,
  user_id: 1,
  result_id: 'r1',
  date: '2026-01-15',
  transaction_type: 'debit',
  original_partner: 'Store',
  amount,
  currency: 'HUF',
  account: 'acc1',
  deduplication_hash: `hash-${id}`,
  category_id: 'grocery',
  partner: null,
  notice: null,
  original_category_id: null,
  original_notice: null,
  confidence: null,
  created_at: null,
  updated_at: null,
});

const makeResponse = (): AggregatedTransactionsResponse => ({
  result_id: 'r1',
  account: 'acc1',
  category_id: 'grocery',
  group_by: 'month',
  groups: {
    '2026-01': [makeTransaction(1, -10.5), makeTransaction(2, -20)],
  },
  highlights: {},
  total_count: 2,
});

describe('CategoryMonthsList.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockRoute.params = {
      accountId: 'acc1',
      categoryId: 'grocery',
    };
    mockRoute.query = {};
    setActivePinia(createPinia());
  });

  const mountPage = (): VueWrapper => shallowMount(CategoryMonthsList, { global: { plugins: [createPinia()] } });

  it('renders month totals without currency next to the numbers', async () => {
    vi.mocked(fetchAggregatedTransactions).mockResolvedValue(makeResponse());

    const wrapper = await mountPage();
    await flushPromises();

    const tableData = (wrapper.vm as unknown as {
      tableData: Array<{ total_display: string }>;
    }).tableData;

    expect(tableData).toHaveLength(1);
    expect(tableData[0].total_display).toBe('-30.50');
    expect(tableData[0].total_display).not.toContain('HUF');
  });

  it('keeps the currency only in the account data, not in the totals', async () => {
    vi.mocked(fetchAggregatedTransactions).mockResolvedValue(makeResponse());

    const wrapper = await mountPage();
    await flushPromises();

    const data = (wrapper.vm as unknown as {
      categoryMonthsData: AggregatedTransactionsResponse;
    }).categoryMonthsData;

    expect(data.account).toBe('acc1');
    expect(data.groups['2026-01'][0].currency).toBe('HUF');
    const tableData = (wrapper.vm as unknown as {
      tableData: Array<{ total_display: string }>;
    }).tableData;
    expect(tableData[0].total_display).toBe('-30.50');
  });

  it('passes the statistical settings to the fetch', async () => {
    vi.mocked(fetchAggregatedTransactions).mockResolvedValue(makeResponse());

    await mountPage();
    await flushPromises();

    expect(fetchAggregatedTransactions).toHaveBeenCalledWith(
      expect.objectContaining({
        algorithms: ['iqr', 'pareto'],
        direction: 'columns'
      })
    );
  });
});
