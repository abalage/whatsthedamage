/**
 * Unit tests for Index page result selector
 * @module test/pages/Index
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises, type VueWrapper } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import Index from '../../src/pages/Index.vue';
import { useAuthStore } from '../../src/stores/auth.js';
import { fetchProcessingResults, fetchTransactionsByResult } from '../../src/js/api.js';
import type { ProcessingResultListItem } from '../../src/types/api.js';

const mockPush = vi.fn();

vi.mock('vue-router', (): Record<string, unknown> => ({
  useRouter: (): { push: typeof mockPush } => ({ push: mockPush }),
  RouterLink: { props: ['to'], template: '<a><slot /></a>' },
}));

vi.mock('vue3-gettext', (): Record<string, unknown> => ({
  useGettext: (): { $gettext: (key: string) => string } => ({
    $gettext: (key: string): string => key,
  }),
}));

vi.mock('../../src/js/api.js', () => ({
  fetchProcessingResults: vi.fn(),
  fetchTransactionsByResult: vi.fn(),
}));

const makeResult = (id: string, createdAt: string): ProcessingResultListItem => ({
  id,
  csv_profile_id: null,
  row_count: 10,
  processing_time: 1,
  ml_enabled: false,
  start_date: null,
  end_date: null,
  created_at: createdAt,
});

const emptyTransactionList = {
  transactions: [],
  total_count: 0,
  limit: 1,
  offset: 0,
};

describe('Index.vue result selector', () => {
  let pinia: ReturnType<typeof createPinia>;

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    pinia = createPinia();
    setActivePinia(pinia);
    const authStore = useAuthStore();
    authStore.user = {
      id: 1,
      username: 'testuser',
      is_active: true,
      opt_in_sharing: false,
    };
  });

  const mountPage = (): VueWrapper => mount(Index, { global: { plugins: [pinia] } });

  it('renders the result selector dropdown', async () => {
    vi.mocked(fetchProcessingResults).mockResolvedValue([makeResult('r1', '2026-01-01T00:00:00Z')]);
    vi.mocked(fetchTransactionsByResult).mockResolvedValue({ ...emptyTransactionList, total_count: 10 });

    const wrapper = await mountPage();
    await flushPromises();

    expect(wrapper.find('#result-selector').exists()).toBe(true);
  });

  it('offers "All Transactions" as the default option', async () => {
    vi.mocked(fetchProcessingResults).mockResolvedValue([makeResult('r1', '2026-01-01T00:00:00Z')]);
    vi.mocked(fetchTransactionsByResult).mockResolvedValue({ ...emptyTransactionList, total_count: 10 });

    const wrapper = await mountPage();
    await flushPromises();

    const select = wrapper.find('#result-selector');
    const allOption = select.findAll('option').find(option => option.text() === 'All Transactions');
    expect(allOption).toBeDefined();
    expect((select.element as HTMLSelectElement).value).toBe('');
  });

  it('populates the dropdown with results from the API', async () => {
    vi.mocked(fetchProcessingResults).mockResolvedValue([
      makeResult('r1', '2026-01-02T00:00:00Z'),
      makeResult('r2', '2026-01-01T00:00:00Z'),
    ]);
    vi.mocked(fetchTransactionsByResult).mockResolvedValue({ ...emptyTransactionList, total_count: 20 });

    const wrapper = await mountPage();
    await flushPromises();

    const options = wrapper.find('#result-selector').findAll('option');
    expect(options).toHaveLength(3);
    expect(options.some(option => option.text().includes('2026'))).toBe(true);
  });

  it('navigates to /results?resultId={id} when a result is selected and viewed', async () => {
    vi.mocked(fetchProcessingResults).mockResolvedValue([makeResult('r1', '2026-01-01T00:00:00Z')]);
    vi.mocked(fetchTransactionsByResult).mockResolvedValue({ ...emptyTransactionList, total_count: 10 });

    const wrapper = await mountPage();
    await flushPromises();

    await wrapper.find('#result-selector').setValue('r1');
    await wrapper.find('button').trigger('click');

    expect(mockPush).toHaveBeenCalledWith({ name: 'results', query: { resultId: 'r1' } });
    expect(localStorage.getItem('selectedResultId')).toBe('r1');
  });

  it('navigates to /results without a query for "All Transactions"', async () => {
    vi.mocked(fetchProcessingResults).mockResolvedValue([makeResult('r1', '2026-01-01T00:00:00Z')]);
    vi.mocked(fetchTransactionsByResult).mockResolvedValue({ ...emptyTransactionList, total_count: 10 });

    const wrapper = await mountPage();
    await flushPromises();

    await wrapper.find('#result-selector').setValue('r1');
    await wrapper.find('#result-selector').setValue('');
    await wrapper.find('button').trigger('click');

    expect(mockPush).toHaveBeenCalledWith({ name: 'results', query: {} });
    expect(localStorage.getItem('selectedResultId')).toBe(null);
  });

  it('restores a persisted selection from localStorage', async () => {
    localStorage.setItem('selectedResultId', 'r2');
    vi.mocked(fetchProcessingResults).mockResolvedValue([
      makeResult('r1', '2026-01-02T00:00:00Z'),
      makeResult('r2', '2026-01-01T00:00:00Z'),
    ]);
    vi.mocked(fetchTransactionsByResult).mockResolvedValue({ ...emptyTransactionList, total_count: 20 });

    const wrapper = await mountPage();
    await flushPromises();

    const select = wrapper.find('#result-selector');
    expect((select.element as HTMLSelectElement).value).toBe('r2');
  });

  it('resets the selection when the stored result no longer exists', async () => {
    localStorage.setItem('selectedResultId', 'missing');
    vi.mocked(fetchProcessingResults).mockResolvedValue([makeResult('r1', '2026-01-01T00:00:00Z')]);
    vi.mocked(fetchTransactionsByResult).mockResolvedValue({ ...emptyTransactionList, total_count: 10 });

    const wrapper = await mountPage();
    await flushPromises();

    const select = wrapper.find('#result-selector');
    expect((select.element as HTMLSelectElement).value).toBe('');
  });

  it('shows only the "All Transactions" option when no results exist but transactions do', async () => {
    vi.mocked(fetchProcessingResults).mockResolvedValue([]);
    vi.mocked(fetchTransactionsByResult).mockResolvedValue({ ...emptyTransactionList, total_count: 5 });

    const wrapper = await mountPage();
    await flushPromises();

    const options = wrapper.find('#result-selector').findAll('option');
    expect(options).toHaveLength(1);
    expect(options[0].text()).toBe('All Transactions');
  });

  it('shows the upload prompt when no results and no transactions exist', async () => {
    vi.mocked(fetchProcessingResults).mockResolvedValue([]);
    vi.mocked(fetchTransactionsByResult).mockResolvedValue(emptyTransactionList);

    const wrapper = await mountPage();
    await flushPromises();

    expect(wrapper.text()).toContain('You have no transactions yet.');
    expect(wrapper.find('#result-selector').exists()).toBe(false);
  });

  it('shows an error card with retry when loading fails', async () => {
    vi.mocked(fetchProcessingResults).mockRejectedValue(new Error('Network down'));
    vi.mocked(fetchTransactionsByResult).mockResolvedValue(emptyTransactionList);

    const wrapper = await mountPage();
    await flushPromises();

    expect(wrapper.text()).toContain('Failed to load your transactions');
    expect(wrapper.text()).toContain('Network down');
    expect(wrapper.text()).toContain('Try again');
    expect(wrapper.find('#result-selector').exists()).toBe(false);
    expect(wrapper.text()).not.toContain('You have no transactions yet.');
  });

  it('recovers with the selector after a successful retry', async () => {
    vi.mocked(fetchProcessingResults).mockRejectedValue(new Error('Network down'));
    vi.mocked(fetchTransactionsByResult).mockResolvedValue(emptyTransactionList);

    const wrapper = await mountPage();
    await flushPromises();

    vi.mocked(fetchProcessingResults).mockResolvedValue([makeResult('r1', '2026-01-01T00:00:00Z')]);
    vi.mocked(fetchTransactionsByResult).mockResolvedValue({ ...emptyTransactionList, total_count: 3 });
    await wrapper.find('button').trigger('click');
    await flushPromises();

    expect(wrapper.find('#result-selector').exists()).toBe(true);
  });
});
