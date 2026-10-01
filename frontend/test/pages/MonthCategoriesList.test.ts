/**
 * Unit tests for MonthCategoriesList page amount display formatting
 * @module test/pages/MonthCategoriesList
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { shallowMount, flushPromises, type VueWrapper } from '@vue/test-utils';
import { createPinia, setActivePinia, type Pinia } from 'pinia';
import { reactive } from 'vue';
import MonthCategoriesList from '../../src/pages/MonthCategoriesList.vue';
import { fetchMonthCategories } from '../../src/js/api.js';
import { useStatisticalStore } from '../../src/stores/statistical.js';
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
  fetchMonthCategories: vi.fn(),
}));

const makeTransaction = (id: number, amount: number, categoryId: string): TransactionListItem => ({
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
  category_id: categoryId,
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
  month: '2026-01',
  group_by: 'category',
  groups: {
    grocery: [makeTransaction(1, -10.5, 'grocery'), makeTransaction(2, -20, 'grocery')],
  },
  highlights: {},
  total_count: 2,
});

describe('MonthCategoriesList.vue', () => {
  let pinia: Pinia;

  beforeEach(() => {
    vi.clearAllMocks();
    mockRoute.params = {
      accountId: 'acc1',
      monthId: '2026-01',
    };
    mockRoute.query = {};
    pinia = createPinia();
    setActivePinia(pinia);
  });

  const mountPage = (): VueWrapper => shallowMount(MonthCategoriesList, { global: { plugins: [pinia] } });

  it('renders category totals without currency next to the numbers', async () => {
    vi.mocked(fetchMonthCategories).mockResolvedValue(makeResponse());

    const wrapper = await mountPage();
    await flushPromises();

    const tableData = (wrapper.vm as unknown as {
      tableData: Array<{ total_display: string }>;
    }).tableData;

    expect(tableData).toHaveLength(1);
    expect(tableData[0].total_display).toBe('-30.50');
    expect(tableData[0].total_display).not.toContain('HUF');
  });

  it('keeps the currency only in the account header, not in the totals', async () => {
    vi.mocked(fetchMonthCategories).mockResolvedValue(makeResponse());

    const wrapper = await mountPage();
    await flushPromises();

    const accountCurrency = (wrapper.vm as unknown as {
      accountCurrency: string | null;
    }).accountCurrency;

    expect(accountCurrency).toBe('HUF');
    const tableData = (wrapper.vm as unknown as {
      tableData: Array<{ total_display: string }>;
    }).tableData;
    expect(tableData[0].total_display).toBe('-30.50');
  });

  it('stores highlights from the aggregate response', async () => {
    const response = makeResponse();
    response.highlights = { grocery: ['pareto'] };
    vi.mocked(fetchMonthCategories).mockResolvedValue(response);

    await mountPage();
    await flushPromises();

    const store = useStatisticalStore();
    expect(store.highlights).toEqual({ grocery: ['pareto'] });
  });

  it('passes the statistical settings to the fetch', async () => {
    vi.mocked(fetchMonthCategories).mockResolvedValue(makeResponse());

    await mountPage();
    await flushPromises();

    expect(fetchMonthCategories).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({
        algorithms: ['iqr', 'pareto'],
        direction: 'columns'
      })
    );
  });
});
