/**
 * Unit tests for useTransactionCorrections composable
 * @module test/composables/useTransactionCorrections
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { defineComponent, nextTick, type PropType } from 'vue';
import { createPinia, setActivePinia } from 'pinia';
import {
  useTransactionCorrections,
  isCategoryCorrected,
  isMerchantCorrected,
  isNoticeCorrected,
  isCorrected,
  merchantOf,
  correctedRowIds,
} from '../../src/composables/useTransactionCorrections';
import { updateTransaction, undoTransaction } from '../../src/js/api';
import { useFeedbackStore } from '../../src/stores/feedback';
import type { TransactionListItem, TransactionUpdatePayload } from '../../src/types/api';

vi.mock('vue3-gettext', (): Record<string, unknown> => ({
  useGettext: (): { $gettext: (key: string) => string } => ({
    $gettext: (key: string): string => key,
  }),
}));

vi.mock('../../src/js/api.js', () => ({
  updateTransaction: vi.fn(),
  undoTransaction: vi.fn(),
}));

const makeTransaction = (overrides: Partial<TransactionListItem> = {}): TransactionListItem => ({
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
  original_category_id: 'food',
  original_notice: null,
  confidence: null,
  created_at: null,
  updated_at: null,
  ...overrides,
});

const pristine = makeTransaction();
const corrected = makeTransaction({
  id: 2,
  category_id: 'housing',
  partner: 'Renamed Store',
  notice: 'birthday gift',
});

describe('corrected-state predicates', () => {
  it('marks a transaction corrected when a value differs from its original', () => {
    expect(isCategoryCorrected(corrected)).toBe(true);
    expect(isMerchantCorrected(corrected)).toBe(true);
    expect(isNoticeCorrected(corrected)).toBe(true);
    expect(isCorrected(corrected)).toBe(true);
  });

  it('marks a transaction uncorrected when applied values equal the originals', () => {
    expect(isCategoryCorrected(pristine)).toBe(false);
    expect(isMerchantCorrected(pristine)).toBe(false);
    expect(isNoticeCorrected(pristine)).toBe(false);
    expect(isCorrected(pristine)).toBe(false);
  });

  it('does not treat a null partner as a merchant correction', () => {
    const txn = makeTransaction({ original_partner: 'Store', partner: null });
    expect(isMerchantCorrected(txn)).toBe(false);
  });

  it('shows the applied merchant over the original', () => {
    expect(merchantOf(makeTransaction({ partner: 'Renamed Store' }))).toBe('Renamed Store');
    expect(merchantOf(pristine)).toBe('Store');
    expect(merchantOf(makeTransaction({ original_partner: '' }))).toBe('');
  });

  it('builds per-cell row ids for the highlight lookup', () => {
    expect(correctedRowIds(corrected)).toEqual({
      category_id: '2|category_id',
      merchant: '2|merchant',
      notice: '2|notice',
    });
  });
});

const Harness = defineComponent({
  props: {
    transactions: {
      type: Array as PropType<TransactionListItem[]>,
      required: true,
    },
  },
  setup(props) {
    const corrections = useTransactionCorrections(() => props.transactions);
    return { ...corrections };
  },
  template: '<div />',
});

describe('useTransactionCorrections', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setActivePinia(createPinia());
  });

  const mountHarness = (
    transactions: TransactionListItem[]
  ): ReturnType<typeof mount> => mount(Harness, {
    props: { transactions },
    global: { plugins: [createPinia()] },
  });

  it('persists a correction, replaces the row, and confirms the outcome', async () => {
    const updated = makeTransaction({ partner: 'Renamed Store' });
    vi.mocked(updateTransaction).mockResolvedValue(updated);
    const list = [pristine, makeTransaction({ id: 3 })];
    const wrapper = mountHarness(list);

    const vm = wrapper.vm as unknown as {
      saveCorrection: (id: number, payload: TransactionUpdatePayload) => Promise<void>;
    };
    await vm.saveCorrection(1, { partner: 'Renamed Store' });

    expect(updateTransaction).toHaveBeenCalledWith(1, { partner: 'Renamed Store' });
    expect(list[0]).toBe(updated);
    expect(useFeedbackStore().hasMessages).toBe(true);
  });

  it('undoes corrections and replaces the row', async () => {
    const restored = makeTransaction({ id: 2, category_id: 'food', partner: null, notice: null });
    vi.mocked(undoTransaction).mockResolvedValue(restored);
    const list = [corrected];
    const wrapper = mountHarness(list);

    const vm = wrapper.vm as unknown as {
      undoCorrection: (id: number) => Promise<void>;
    };
    await vm.undoCorrection(2);

    expect(undoTransaction).toHaveBeenCalledWith(2);
    expect(list[0]).toBe(restored);
  });

  it('rethrows save errors and keeps the row untouched', async () => {
    vi.mocked(updateTransaction).mockRejectedValue(new Error('Update failed'));
    const list = [pristine];
    const wrapper = mountHarness(list);

    const vm = wrapper.vm as unknown as {
      saveCorrection: (id: number, payload: TransactionUpdatePayload) => Promise<void>;
    };
    await expect(vm.saveCorrection(1, { notice: 'gift' })).rejects.toThrow('Update failed');

    expect(list[0]).toBe(pristine);
    expect(useFeedbackStore().hasErrors).toBe(false);
  });

  it('rethrows undo errors and keeps the row untouched', async () => {
    vi.mocked(undoTransaction).mockRejectedValue(new Error('Undo failed'));
    const list = [corrected];
    const wrapper = mountHarness(list);

    const vm = wrapper.vm as unknown as {
      undoCorrection: (id: number) => Promise<void>;
    };
    await expect(vm.undoCorrection(2)).rejects.toThrow('Undo failed');

    expect(list[0]).toBe(corrected);
  });

  it('keeps the row when the API returns an unknown transaction', async () => {
    vi.mocked(updateTransaction).mockResolvedValue(makeTransaction({ id: 99 }));
    const list = [pristine];
    const wrapper = mountHarness(list);

    const vm = wrapper.vm as unknown as {
      saveCorrection: (id: number, payload: TransactionUpdatePayload) => Promise<void>;
    };
    await vm.saveCorrection(1, { notice: 'gift' });

    expect(list).toHaveLength(1);
    expect(list[0]).toBe(pristine);
  });

  it('maps corrected cells to the corrected highlight type', async () => {
    const wrapper = mountHarness([pristine, corrected]);

    const vm = wrapper.vm as unknown as {
      correctedCellHighlights: Record<string, string[]>;
    };
    await nextTick();

    expect(vm.correctedCellHighlights['1|category_id']).toBeUndefined();
    expect(vm.correctedCellHighlights['2|category_id']).toEqual(['corrected']);
    expect(vm.correctedCellHighlights['2|merchant']).toEqual(['corrected']);
    expect(vm.correctedCellHighlights['2|notice']).toEqual(['corrected']);
  });
});
