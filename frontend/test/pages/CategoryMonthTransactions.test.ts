/**
 * Unit tests for CategoryMonthTransactions page
 * @module test/pages/CategoryMonthTransactions
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { shallowMount, flushPromises, type VueWrapper, type DOMWrapper } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { reactive } from 'vue';
import CategoryMonthTransactions from '../../src/pages/CategoryMonthTransactions.vue';
import VueDataTable from '../../src/components/data/VueDataTable.vue';
import EditableCategoryCell from '../../src/components/data/EditableCategoryCell.vue';
import EditableTextCell from '../../src/components/data/EditableTextCell.vue';
import UndoCorrectionCell from '../../src/components/data/UndoCorrectionCell.vue';
import { fetchCategoryMonthTransactions, fetchCategories, updateTransaction, undoTransaction } from '../../src/js/api.js';
import { useFeedbackStore } from '../../src/stores/feedback.js';
import type { TransactionListItem, TransactionListResponse, CategoryDefinition } from '../../src/types/api.js';

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
  fetchCategoryMonthTransactions: vi.fn(),
  fetchCategories: vi.fn(),
  updateTransaction: vi.fn(),
  undoTransaction: vi.fn(),
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

const makeResponse = (transactions?: TransactionListItem[]): TransactionListResponse => ({
  transactions: transactions ?? [makeTransaction(1, -10.5), makeTransaction(2, -20)],
  total_count: 2,
  limit: 10000,
  offset: 0,
});

describe('CategoryMonthTransactions.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockRoute.params = {
      accountId: 'acc1',
      categoryId: 'grocery',
      monthId: '2026-01',
    };
    mockRoute.query = {};
    setActivePinia(createPinia());
    vi.mocked(fetchCategories).mockResolvedValue([]);
  });

  const mountPage = (): VueWrapper => shallowMount(CategoryMonthTransactions, { global: { plugins: [createPinia()] } });

  it('renders transaction amounts without currency next to the numbers', async () => {
    vi.mocked(fetchCategoryMonthTransactions).mockResolvedValue(makeResponse());

    const wrapper = await mountPage();
    await flushPromises();

    const rows = tableData(wrapper);

    expect(rows).toHaveLength(2);
    expect(rows[0].amount_display).toBe('-10.50');
    expect(rows[1].amount_display).toBe('-20.00');
    expect(rows[0].amount_display).not.toContain('HUF');
  });

  it('keeps the currency only in the account header, not in the amounts', async () => {
    vi.mocked(fetchCategoryMonthTransactions).mockResolvedValue(makeResponse());

    const wrapper = await mountPage();
    await flushPromises();

    const accountCurrency = (wrapper.vm as unknown as {
      accountCurrency: string | null;
    }).accountCurrency;

    expect(accountCurrency).toBe('HUF');
    const rows = tableData(wrapper);
    expect(rows[0].amount_display).toBe('-10.50');
  });

  it('shows the corrected partner over the original partner', async () => {
    vi.mocked(fetchCategoryMonthTransactions).mockResolvedValue(
      makeResponse([{ ...makeTransaction(1, -10.5), partner: 'Renamed Store' }])
    );

    const wrapper = await mountPage();
    await flushPromises();

    const rows = tableData(wrapper);
    expect(rows[0].merchant).toBe('Renamed Store');
  });
});

describe('CategoryMonthTransactions.vue inline editing', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockRoute.params = {
      accountId: 'acc1',
      categoryId: 'grocery',
      monthId: '2026-01',
    };
    mockRoute.query = {};
    setActivePinia(createPinia());
    vi.mocked(fetchCategories).mockResolvedValue([]);
  });

  const mountWithResponse = async (
    response: TransactionListResponse
  ): Promise<VueWrapper> => {
    vi.mocked(fetchCategoryMonthTransactions).mockResolvedValue(response);
    const wrapper = shallowMount(CategoryMonthTransactions, { global: { plugins: [createPinia()] } });
    await flushPromises();
    return wrapper;
  };

  const findColumn = (wrapper: VueWrapper, key: string): ColumnLike => {
    const column = tableColumns(wrapper).find(c => c.key === key);
    expect(column).toBeDefined();
    return column as ColumnLike;
  };

  it('renders category, merchant, and notice columns as editable cells', async () => {
    const wrapper = await mountWithResponse(makeResponse());

    expect(findColumn(wrapper, 'category_id').component).toBe(EditableCategoryCell);
    expect(findColumn(wrapper, 'merchant').component).toBe(EditableTextCell);
    expect(findColumn(wrapper, 'notice').component).toBe(EditableTextCell);
  });

  it('renders the notice value from the transaction', async () => {
    const txn = { ...makeTransaction(1, -10.5), notice: 'gift' };
    const wrapper = await mountWithResponse(makeResponse([txn]));

    const rows = tableData(wrapper);
    expect(rows[0].notice).toBe('gift');
  });

  it('prevents saving an empty merchant but allows an empty notice', async () => {
    const wrapper = await mountWithResponse(makeResponse());
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
    const wrapper = await mountWithResponse(makeResponse([makeTransaction(1, -10.5)]));
    vi.mocked(updateTransaction).mockResolvedValue({ ...makeTransaction(1, -10.5), partner: 'Renamed Store' });

    const column = findColumn(wrapper, 'merchant');
    const rows = tableData(wrapper);
    const props = column.componentProps?.(rows[0].merchant, rows[0]) as { save: (v: string, applyToFuture?: boolean) => Promise<void> };
    await props.save('Renamed Store', false);

    expect(updateTransaction).toHaveBeenCalledWith(1, { partner: 'Renamed Store', apply_to_future: false });
    const refreshed = tableData(wrapper);
    expect(refreshed[0].merchant).toBe('Renamed Store');
    expect(useFeedbackStore().hasMessages).toBe(true);
  });

  it('persists a category correction with the apply-to-future flag', async () => {
    const wrapper = await mountWithResponse(makeResponse([makeTransaction(1, -10.5)]));
    vi.mocked(updateTransaction).mockResolvedValue({ ...makeTransaction(1, -10.5), category_id: 'housing' });

    const column = findColumn(wrapper, 'category_id');
    const rows = tableData(wrapper);
    const props = column.componentProps?.(rows[0].category_id, rows[0]) as { save: (v: string | null, applyToFuture?: boolean) => Promise<void> };
    await props.save('housing', true);

    expect(updateTransaction).toHaveBeenCalledWith(1, { category_id: 'housing', apply_to_future: true });
  });

  it('persists a notice correction without the apply-to-future flag', async () => {
    const wrapper = await mountWithResponse(makeResponse([makeTransaction(1, -10.5)]));
    vi.mocked(updateTransaction).mockResolvedValue({ ...makeTransaction(1, -10.5), notice: 'gift' });

    const column = findColumn(wrapper, 'notice');
    const rows = tableData(wrapper);
    const props = column.componentProps?.(rows[0].notice, rows[0]) as { save: (v: string) => Promise<void> };
    await props.save('gift');

    expect(updateTransaction).toHaveBeenCalledWith(1, { notice: 'gift' });
  });

  it('rejects failures so the cell can show the error inline', async () => {
    const wrapper = await mountWithResponse(makeResponse([makeTransaction(1, -10.5)]));
    vi.mocked(updateTransaction).mockRejectedValue(new Error('Update failed'));

    const column = findColumn(wrapper, 'merchant');
    const rows = tableData(wrapper);
    const props = column.componentProps?.(rows[0].merchant, rows[0]) as { save: (v: string) => Promise<void> };

    await expect(props.save('Nope')).rejects.toThrow('Update failed');
    expect(useFeedbackStore().hasErrors).toBe(false);
  });
});

describe('CategoryMonthTransactions.vue corrections review', () => {
  /** Transaction without corrections: applied values equal the originals */
  const pristineTransaction: TransactionListItem = {
    ...makeTransaction(1, -10.5),
    category_id: 'grocery',
    original_category_id: 'grocery',
    notice: null,
    original_notice: null,
    partner: null,
  };

  /** Transaction with merchant, category, and notice corrected */
  const correctedTransaction: TransactionListItem = {
    ...makeTransaction(2, -20),
    category_id: 'housing',
    original_category_id: 'grocery',
    partner: 'Renamed Store',
    notice: 'birthday gift',
    original_notice: null,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockRoute.params = {
      accountId: 'acc1',
      categoryId: 'grocery',
      monthId: '2026-01',
    };
    mockRoute.query = {};
    setActivePinia(createPinia());
    vi.mocked(fetchCategories).mockResolvedValue([]);
  });

  const mountWithTransactions = async (
    transactions: TransactionListItem[]
  ): Promise<VueWrapper> => {
    vi.mocked(fetchCategoryMonthTransactions).mockResolvedValue({
      transactions,
      total_count: transactions.length,
      limit: 10000,
      offset: 0,
    });
    const wrapper = shallowMount(CategoryMonthTransactions, { global: { plugins: [createPinia()] } });
    await flushPromises();
    return wrapper;
  };

  it('marks rows as corrected when any value differs from its original', async () => {
    const wrapper = await mountWithTransactions([pristineTransaction, correctedTransaction]);

    const rows = tableData(wrapper);
    expect(rows[0].corrected).toBe(false);
    expect(rows[1].corrected).toBe(true);
  });

  it('maps corrected cells to the corrected highlight type', async () => {
    const wrapper = await mountWithTransactions([pristineTransaction, correctedTransaction]);

    const highlights = tableProps(wrapper)
      .cellHighlightsByRowId as Record<string, string[]>;
    expect(highlights['1|category_id']).toBeUndefined();
    expect(highlights['1|merchant']).toBeUndefined();
    expect(highlights['1|notice']).toBeUndefined();
    expect(highlights['2|category_id']).toEqual(['corrected']);
    expect(highlights['2|merchant']).toEqual(['corrected']);
    expect(highlights['2|notice']).toEqual(['corrected']);
  });

  it('carries per-cell row ids for the highlight lookup', async () => {
    const wrapper = await mountWithTransactions([correctedTransaction]);

    const rowIds = tableData(wrapper)[0]._rowIds as Record<string, string>;
    expect(rowIds).toEqual({
      category_id: '2|category_id',
      merchant: '2|merchant',
      notice: '2|notice',
    });
  });

  it('hides the undo column by default', async () => {
    const wrapper = await mountWithTransactions([correctedTransaction]);

    const keys = tableColumns(wrapper).map(column => column.key);
    expect(keys).not.toContain('undo');
  });
});

describe('CategoryMonthTransactions.vue toolbar toggles', () => {
  /** Transaction without corrections: applied values equal the originals */
  const pristineTransaction: TransactionListItem = {
    ...makeTransaction(1, -10.5),
    category_id: 'grocery',
    original_category_id: 'grocery',
    notice: null,
    original_notice: null,
    partner: null,
  };

  /** Transaction with merchant, category, and notice corrected */
  const correctedTransaction: TransactionListItem = {
    ...makeTransaction(2, -20),
    category_id: 'housing',
    original_category_id: 'grocery',
    partner: 'Renamed Store',
    notice: 'birthday gift',
    original_notice: null,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockRoute.params = {
      accountId: 'acc1',
      categoryId: 'grocery',
      monthId: '2026-01',
    };
    mockRoute.query = {};
    setActivePinia(createPinia());
    vi.mocked(fetchCategories).mockResolvedValue([]);
  });

  // The toolbar buttons render inside VueDataTable's filter-actions slot,
  // so the table itself must not be stubbed for these tests
  const mountWithTable = async (
    transactions: TransactionListItem[]
  ): Promise<VueWrapper> => {
    vi.mocked(fetchCategoryMonthTransactions).mockResolvedValue({
      transactions,
      total_count: transactions.length,
      limit: 10000,
      offset: 0,
    });
    const wrapper = shallowMount(CategoryMonthTransactions, {
      global: {
        plugins: [createPinia()],
        stubs: { VueDataTable: false },
      },
    });
    await flushPromises();
    return wrapper;
  };

  // Toggle buttons in toolbar order: Corrected, Edit
  const findToggleButtons = (wrapper: VueWrapper): DOMWrapper<Element>[] =>
    wrapper.findAll('button[aria-pressed]');

  it('renders the toggle buttons next to the clear button', async () => {
    const wrapper = await mountWithTable([correctedTransaction]);

    const toggles = findToggleButtons(wrapper);
    expect(toggles).toHaveLength(2);
    expect(toggles.map(t => t.text())).toEqual(['Corrected', 'Edit']);
  });

  it('filters the table to corrected transactions when the Corrected toggle is on', async () => {
    const wrapper = await mountWithTable([pristineTransaction, correctedTransaction]);

    await findToggleButtons(wrapper)[0].trigger('click');
    await flushPromises();

    const rows = tableData(wrapper);
    expect(rows).toHaveLength(1);
    expect(rows[0].transaction_id).toBe(2);
    expect(findToggleButtons(wrapper)[0].attributes('aria-pressed')).toBe('true');
  });

  it('adds the undo column with per-row undo callbacks when the Edit toggle is on', async () => {
    const wrapper = await mountWithTable([pristineTransaction, correctedTransaction]);
    const restored: TransactionListItem = {
      ...correctedTransaction,
      category_id: 'grocery',
      partner: null,
      notice: null,
    };
    vi.mocked(undoTransaction).mockResolvedValue(restored);

    await findToggleButtons(wrapper)[1].trigger('click');
    await flushPromises();

    const column = tableColumns(wrapper).find(c => c.key === 'undo');
    expect(column).toBeDefined();
    expect((column as ColumnLike).component).toBe(UndoCorrectionCell);

    const rows = tableData(wrapper);
    const pristineProps = (column as ColumnLike).componentProps?.(
      undefined, rows[0]
    ) as { corrected: boolean; undo: () => Promise<void> };
    const correctedProps = (column as ColumnLike).componentProps?.(
      undefined, rows[1]
    ) as { corrected: boolean; undo: () => Promise<void> };
    expect(pristineProps.corrected).toBe(false);
    expect(correctedProps.corrected).toBe(true);

    await correctedProps.undo();
    expect(undoTransaction).toHaveBeenCalledWith(2);
    expect(tableData(wrapper)[1].corrected).toBe(false);
    expect(useFeedbackStore().hasMessages).toBe(true);
  });

  it('rejects undo failures so the undo cell can show the error inline', async () => {
    const wrapper = await mountWithTable([correctedTransaction]);
    vi.mocked(undoTransaction).mockRejectedValue(new Error('Undo failed'));

    await findToggleButtons(wrapper)[1].trigger('click');
    await flushPromises();

    const column = tableColumns(wrapper).find(c => c.key === 'undo');
    const rows = tableData(wrapper);
    const props = (column as ColumnLike).componentProps?.(
      undefined, rows[0]
    ) as { undo: () => Promise<void> };

    await expect(props.undo()).rejects.toThrow('Undo failed');
    expect(tableData(wrapper)[0].corrected).toBe(true);
    expect(useFeedbackStore().hasErrors).toBe(false);
  });

  it('resets the corrected toggle when the filters are cleared', async () => {
    const wrapper = await mountWithTable([pristineTransaction, correctedTransaction]);

    await findToggleButtons(wrapper)[0].trigger('click');
    await flushPromises();
    expect(tableData(wrapper)).toHaveLength(1);

    const clearButton = wrapper
      .findAll('button')
      .find(button => button.text() === 'Clear all filters');
    await clearButton?.trigger('click');
    await flushPromises();

    expect(findToggleButtons(wrapper)[0].attributes('aria-pressed')).toBe('false');
    expect(tableData(wrapper)).toHaveLength(2);
  });

  it('loads categories on mount for the category filter and editor', async () => {
    const categoryDefinitions: CategoryDefinition[] = [
      { id: 'grocery', default_name: 'Grocery', patterns: [] },
      { id: 'housing', default_name: 'Housing', patterns: [] },
    ];
    vi.mocked(fetchCategories).mockResolvedValue(categoryDefinitions);

    const wrapper = await mountWithTable([correctedTransaction]);

    expect(fetchCategories).toHaveBeenCalled();
    const column = tableColumns(wrapper).find(c => c.key === 'category_id');
    const options = (column as ColumnLike).filterOptions ?? [];
    expect(options.map(option => option.value)).toEqual(['grocery', 'housing']);
  });
});
